"""
Astro Service

Manages Flashy Astro agent sessions and streaming responses.
"""

import asyncio
import re
from typing import Dict, Any, List, Optional, AsyncGenerator

from gemini_webapi import GeminiClient
from gemini_webapi.constants import Model

from .config import load_config
from .astro_agent import AstroAgent
from .response_filter import ResponseFilter, ThoughtFilter


class AstroService:
    """Streaming service for Vedic astrology agent."""

    def __init__(self):
        self.client: Optional[GeminiClient] = None
        self.config = load_config()
        self.sessions: Dict[str, Any] = {}
        self.agents: Dict[str, AstroAgent] = {}
        self.interrupted_sessions: set = set()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.response_filter = ResponseFilter(aggressive=False)
        self.thought_filter = ThoughtFilter()

    async def get_client(self) -> GeminiClient:
        if self.client is None:
            self.config = load_config()
            self.client = GeminiClient(
                self.config["Secure_1PSID"],
                self.config["Secure_1PSIDTS"],
                proxy=None
            )
            if self.config.get("Secure_1PSIDCC"):
                self.client.cookies["__Secure-1PSIDCC"] = self.config["Secure_1PSIDCC"]
            await self.client.init(
                timeout=600,
                auto_close=False,
                close_delay=300,
                auto_refresh=True
            )
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
        task = self.active_tasks.get(session_id)
        if task and not task.done():
            task.cancel()

    def _is_interrupted(self, session_id: str) -> bool:
        return session_id in self.interrupted_sessions

    def _clean_response_text(self, text: str, tool_call_raw: str = None) -> str:
        if not text:
            return ""
        cleaned = text
        if tool_call_raw:
            cleaned = cleaned.replace(tool_call_raw, "").strip()
        json_block_pattern = r'```json\\s*\\{[^`]*?"(?:action|tool|name)"\\s*:[^`]*?\\}\\s*```'
        cleaned = re.sub(json_block_pattern, "", cleaned, flags=re.DOTALL).strip()
        cleaned = self.response_filter.filter(cleaned)
        return cleaned

    def _separate_thinking(self, text: str) -> tuple:
        if not text:
            return None, ""
        return self.thought_filter.extract_thoughts(text)

    def _build_kundali_context(
        self,
        kundalis: List[Dict[str, Any]],
        active_id: Optional[str]
    ) -> str:
        if not kundalis:
            return "No kundalis are stored yet."
        lines = [f"Stored kundalis: {len(kundalis)}"]
        for k in kundalis[:12]:
            active = " (active)" if k.get("id") == active_id else ""
            lines.append(
                f"- {k.get('id')}: {k.get('name')} | {k.get('birthDate')} {k.get('birthTime')} | "
                f"{k.get('birthPlace')} | {k.get('gender')}{active}"
            )
            if k.get("chart") and k.get("chart").get("summary"):
                lines.append(f"  Chart Summary: {k['chart']['summary']}")
        return "\n".join(lines)

    async def _send_with_retry(self, chat, message: str, max_retries: int = 3, timeout: int = 120):
        last_error = None
        for attempt in range(max_retries):
            try:
                return await asyncio.wait_for(chat.send_message(message), timeout=timeout)
            except asyncio.CancelledError:
                raise
            except asyncio.TimeoutError:
                last_error = f"Request timed out after {timeout}s"
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
        raise Exception(f"Failed after {max_retries} attempts: {last_error}")

    async def generate_response(
        self,
        message: str,
        session_id: str,
        kundalis: List[Dict[str, Any]],
        active_kundali_id: Optional[str]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        client = await self.get_client()
        agent = self.get_agent(session_id)
        chat = await self.get_session(session_id)

        try:
            if session_id in self.interrupted_sessions:
                self.interrupted_sessions.remove(session_id)

            context = self._build_kundali_context(kundalis, active_kundali_id)
            prompt = (
                f"{agent.get_system_prompt()}\n\n"
                f"## Current Kundali Context\n{context}\n\n"
                f"## User Request\n{message}"
            )

            response = await self._send_with_retry(chat, prompt)

            iteration = 0
            while iteration < agent.max_iterations:
                if self._is_interrupted(session_id):
                    yield {"text": "\n\n*Astro agent interrupted.*", "is_final": True}
                    break

                response_text = response.text or ""
                embedded_thinking, clean_response = self._separate_thinking(response_text)
                if embedded_thinking:
                    yield {"thought": embedded_thinking}

                tool_call = agent.parse_tool_call(clean_response)
                if not tool_call:
                    final_text = self._clean_response_text(clean_response)
                    if final_text:
                        yield {"text": final_text, "is_final": True}
                    else:
                        yield {"text": "[Astro agent completed]", "is_final": True}
                    break

                display_text = self._clean_response_text(clean_response, tool_call.get("raw_match"))
                if display_text:
                    yield {"text": display_text + "\n"}

                yield {"tool_call": {"name": tool_call["name"], "args": tool_call["args"]}}

                try:
                    tool_result, kundalis, active_kundali_id = agent.execute_tool(
                        tool_call["name"],
                        kundalis,
                        active_kundali_id,
                        tool_call["args"]
                    )
                except Exception as exc:
                    yield {"text": f"\n\nTool error: {exc}", "is_final": True}
                    break

                yield {
                    "tool_result": tool_result,
                    "kundali_updates": {
                        "kundalis": kundalis,
                        "active_id": active_kundali_id
                    }
                }

                follow_up = (
                    f"{tool_result}\n\n"
                    f"## Updated Kundali Context\n{self._build_kundali_context(kundalis, active_kundali_id)}\n\n"
                    "Continue."
                )
                response = await self._send_with_retry(chat, follow_up)
                iteration += 1
        except Exception as e:
            yield {"text": f"\n\n**Astro Error:** {str(e)}", "is_final": True}
