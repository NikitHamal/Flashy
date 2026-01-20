"""
Astro Service

Streaming service for the Flashy Astro agent.
"""

import asyncio
import json
import re
from typing import Any, AsyncGenerator, Dict, List, Optional

from gemini_webapi import GeminiClient
from gemini_webapi.constants import Model

from .astro_agent import AstroAgent
from .config import load_config
from .response_filter import ResponseFilter, ThoughtFilter


class AstroService:
    def __init__(self):
        self.client: Optional[GeminiClient] = None
        self.config = load_config()
        self.sessions: Dict[str, Any] = {}
        self.agents: Dict[str, AstroAgent] = {}
        self.interrupted_sessions: set = set()
        self.response_filter = ResponseFilter(aggressive=False)
        self.thought_filter = ThoughtFilter()

    async def get_client(self):
        if self.client is None:
            self.config = load_config()
            self.client = GeminiClient(
                self.config["Secure_1PSID"],
                self.config["Secure_1PSIDTS"],
                proxy=None
            )
            if self.config.get("Secure_1PSIDCC"):
                self.client.cookies["__Secure-1PSIDCC"] = self.config["Secure_1PSIDCC"]
            await self.client.init(timeout=600, auto_close=False, close_delay=300, auto_refresh=True)
        return self.client

    def get_agent(self, session_id: str) -> AstroAgent:
        if session_id not in self.agents:
            self.agents[session_id] = AstroAgent()
        return self.agents[session_id]

    async def get_session(self, session_id: str):
        client = await self.get_client()
        if session_id not in self.sessions:
            model_name = self.config.get("model", "G_2_5_FLASH")
            model = getattr(Model, model_name, Model.G_2_5_FLASH)
            self.sessions[session_id] = client.start_chat(model=model)
        return self.sessions[session_id]

    def interrupt_session(self, session_id: str):
        self.interrupted_sessions.add(session_id)

    def _is_interrupted(self, session_id: str) -> bool:
        return session_id in self.interrupted_sessions

    def _clean_response_text(self, text: str, tool_call_raw: str = None) -> str:
        if not text:
            return ""
        cleaned = text
        if tool_call_raw:
            cleaned = cleaned.replace(tool_call_raw, "").strip()
        json_block_pattern = r'```json\s*\{[^`]*?"(?:action|tool|name)"\s*:[^`]*?\}\s*```'
        cleaned = re.sub(json_block_pattern, '', cleaned, flags=re.DOTALL).strip()
        return self.response_filter.filter(cleaned)

    async def _send_with_retry(self, chat, message: str, timeout: int = 120):
        return await asyncio.wait_for(chat.send_message(message), timeout=timeout)

    def _build_kundali_summary(self, agent: AstroAgent) -> str:
        kundalis = agent.tools.get_state()
        if not kundalis:
            return "No kundalis stored yet."
        lines = [f"{len(kundalis)} kundalis stored:"]
        for kundali in kundalis[:20]:
            profile = kundali.get("profile", {})
            lines.append(f"- {profile.get('name', 'Unnamed')} (id: {kundali.get('id')})")
        return "\n".join(lines)

    async def generate_response(
        self,
        prompt: str,
        session_id: str,
        kundalis_state: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        client = await self.get_client()
        agent = self.get_agent(session_id)
        chat = await self.get_session(session_id)

        if kundalis_state is not None:
            agent.tools.set_state(kundalis_state)

        system_prompt = agent.get_system_prompt()
        kundali_context = self._build_kundali_summary(agent)

        full_prompt = f"""{system_prompt}

## Current Kundalis
{kundali_context}

## User Request
{prompt}

Use tools when you need to store or retrieve kundali data."""

        response = await self._send_with_retry(chat, full_prompt)
        iteration = 0
        max_iterations = agent.max_iterations

        while iteration < max_iterations:
            if self._is_interrupted(session_id):
                yield {"text": "*Astro session interrupted.*", "is_final": True}
                break

            response_text = response.text or ""
            api_thoughts = getattr(response, "thoughts", None) or ""
            embedded_thinking, clean_response = self.thought_filter.extract_thoughts(response_text)

            all_thoughts = ""
            if api_thoughts:
                all_thoughts = api_thoughts
            if embedded_thinking:
                all_thoughts = f"{all_thoughts}\n\n{embedded_thinking}".strip() if all_thoughts else embedded_thinking

            if all_thoughts:
                yield {"thought": all_thoughts}

            tool_call = agent.parse_tool_call(clean_response)
            if not tool_call:
                final_text = self._clean_response_text(clean_response)
                yield {"text": final_text, "kundalis_state": agent.tools.get_state(), "is_final": True}
                break

            display_text = self._clean_response_text(clean_response, tool_call.get("raw_match"))
            if display_text:
                yield {"text": display_text + "\n"}

            yield {"tool_call": {"name": tool_call["name"], "args": tool_call["args"]}}

            if self._is_interrupted(session_id):
                yield {"text": "*Astro session interrupted.*", "is_final": True}
                break

            tool_result = await agent.execute_tool(tool_call["name"], tool_call["args"])
            yield {
                "tool_result": tool_result,
                "kundalis_state": agent.tools.get_state()
            }

            if self._is_interrupted(session_id):
                yield {"text": "*Astro session interrupted.*", "is_final": True}
                break

            response = await self._send_with_retry(chat, tool_result)
            iteration += 1

        if iteration >= max_iterations:
            yield {"text": "*Astro agent reached max iterations.*", "is_final": True}

    def get_kundalis_state(self, session_id: str) -> List[Dict[str, Any]]:
        agent = self.agents.get(session_id)
        return agent.tools.get_state() if agent else []

    def set_kundalis_state(self, session_id: str, kundalis: List[Dict[str, Any]]):
        agent = self.get_agent(session_id)
        agent.tools.set_state(kundalis)
        return {"message": "Kundalis synced", "count": len(kundalis)}
