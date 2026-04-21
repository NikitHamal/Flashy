from __future__ import annotations

import json
import re
import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..config import load_config
from ..server import ProviderGateway, ProviderRequest

logger = logging.getLogger("flashy.computer_use.planner")

SYSTEM_PROMPT = """You are Flashy Computer Use, an autonomous desktop operator.
You control the local computer by selecting ONE tool call at a time.

Operating rules:
- When you complete a task, call finish_run immediately. DO NOT repeat successful actions.
- Use deterministic actions: open_application, type_text (paste=true), press_keys.
- After type_text succeeds, call finish_run - the text is already pasted.
- Do not call more than one tool in a single turn.
- For opening apps: use simple names like "notepad", "chrome", "explorer".
- For typing: use type_text with paste=true for reliability.
- When the user's request is done, call finish_run with a summary.""".strip()


TOOL_DEFS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Launch or focus a desktop application by executable or app name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Application name such as notepad, chrome, vscode, explorer, terminal."},
                },
                "required": ["app_name"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Open a URL in the default browser or a named browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "preferred_browser": {"type": "string"},
                },
                "required": ["url"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move_cursor",
            "description": "Move the mouse cursor to a screen coordinate.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "duration": {"type": "number"},
                },
                "required": ["x", "y"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "Click on a screen coordinate.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "button": {"type": "string", "enum": ["left", "right", "middle"]},
                    "clicks": {"type": "integer", "minimum": 1, "maximum": 4},
                },
                "required": ["x", "y"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "drag",
            "description": "Drag from one point to another.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_x": {"type": "integer"},
                    "start_y": {"type": "integer"},
                    "end_x": {"type": "integer"},
                    "end_y": {"type": "integer"},
                    "duration": {"type": "number"},
                },
                "required": ["start_x", "start_y", "end_x", "end_y"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "scroll",
            "description": "Scroll vertically. Positive scrolls up, negative scrolls down.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "integer"},
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                },
                "required": ["amount"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "press_keys",
            "description": "Press one key or a hotkey chord in order, for example ['ctrl','l'] or ['enter'].",
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "maxItems": 5,
                    },
                },
                "required": ["keys"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type or paste text into the focused field. Use paste=true for multi-word text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "paste": {"type": "boolean"},
                },
                "required": ["text"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "wait",
            "description": "Wait for the UI to update or an app to launch.",
            "parameters": {
                "type": "object",
                "properties": {
                    "seconds": {"type": "number", "minimum": 0.1, "maximum": 30},
                },
                "required": ["seconds"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish_run",
            "description": "Mark the task complete and provide a user-facing summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                },
                "required": ["summary"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fail_run",
            "description": "Stop because the task cannot continue safely or successfully.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string"},
                },
                "required": ["reason"],
                "additionalProperties": False,
            },
        },
    },
]

TOOL_CALL_RE = re.compile(
    r'<ActionTool>\s*(\{.*?\})\s*</ActionTool>',
    re.DOTALL,
)

FALLBACK_SYSTEM_SUFFIX = """

When you need to take an action, respond with ONLY this XML block (no other text before it):
<ActionTool>{"name": "TOOL_NAME", "arguments": {JSON_ARGS}}</ActionTool>

Available tools:
"""

LLM_TIMEOUT_SECONDS = 120


@dataclass(slots=True)
class PlannerDecision:
    name: str
    arguments: Dict[str, Any]
    reasoning: str = ""
    raw_text: str = ""


def _parse_tool_call_from_text(text: str) -> Optional[Dict[str, Any]]:
    for m in TOOL_CALL_RE.finditer(text):
        json_str = m.group(1).strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        elif json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()
        try:
            payload = json.loads(json_str)
            return {"name": payload.get("name", ""), "arguments": payload.get("arguments", {})}
        except (json.JSONDecodeError, KeyError):
            continue

    patterns = [
        (r'```json\s*(\{[^`]*?"name"[^`]*?\})\s*```', re.DOTALL),
        (r'\{"name"\s*:\s*"(\w+)"\s*,\s*"arguments"\s*:\s*(\{[^}]*\})\}', 0),
    ]
    for pattern, flags in patterns:
        for m2 in re.finditer(pattern, flags):
            try:
                if flags:
                    data = json.loads(m2.group(1))
                else:
                    name = m2.group(1)
                    args = json.loads(m2.group(2))
                    data = {"name": name, "arguments": args}
                return data
            except (json.JSONDecodeError, KeyError):
                continue

    return None


class ComputerUsePlanner:
    def __init__(self) -> None:
        self.gateway = ProviderGateway()

    def _resolve_provider_model(self, provider: Optional[str], model: Optional[str]) -> tuple[str, str]:
        config = load_config()
        return (
            provider or config.get("computer_use_provider") or config.get("active_provider") or "airforce",
            model or config.get("computer_use_model") or config.get("model") or "",
        )

    def _build_tool_suffix(self) -> str:
        lines = [FALLBACK_SYSTEM_SUFFIX]
        for t in TOOL_DEFS:
            fn = t.get("function", t)
            name = fn.get("name", "unknown")
            desc = fn.get("description", "")
            params = fn.get("parameters", {})
            lines.append(f"- **{name}**: {desc}")
            if params.get("properties"):
                for pname, pinfo in params["properties"].items():
                    req = "required" if pname in params.get("required", []) else "optional"
                    pdesc = pinfo.get("description", "")
                    ptype = pinfo.get("type", "any")
                    lines.append(f"  - {pname} ({ptype}, {req}): {pdesc}")
        lines.append("")
        return "\n".join(lines)

    async def next_action(
        self,
        *,
        provider: Optional[str],
        model: Optional[str],
        vision_capable: bool = True,
        task: str,
        session_context: str,
        observations: List[Dict[str, Any]],
        tool_messages: List[Dict[str, Any]],
    ) -> PlannerDecision:
        resolved_provider, resolved_model = self._resolve_provider_model(provider, model)
        latest = observations[-1]
        
        cursor_x = latest.get('cursor_x', 0)
        cursor_y = latest.get('cursor_y', 0)
        
        observation_text = (
            f"Task: {task}\n"
            f"Screen: {latest['width']}x{latest['height']} pixels\n"
            f"Platform: {latest['platform']}\n"
            f"Mouse cursor at: ({cursor_x}, {cursor_y})\n"
            f"Session history:\n{session_context or '(none)'}\n"
        )
        
        if vision_capable:
            observation_text += "IMPORTANT: You see the screenshot above. Use coordinates visible in the screen to interact.\n"
        
        if vision_capable:
            user_content: List[Dict[str, Any]] = [
                {"type": "text", "text": observation_text},
                {"type": "image_url", "image_url": {"url": latest["screenshot_data_url"]}},
            ]
        else:
            user_content = [
                {"type": "text", "text": observation_text + "\n\nIMPORTANT: You CANNOT see the screen. After successfully completing an action, call finish_run IMMEDIATELY. Do NOT repeat actions that already succeeded. For example: once Notepad is open and text is typed, call finish_run - do NOT open Notepad again."}
            ]

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *tool_messages,
            {"role": "user", "content": user_content},
        ]

        try:
            return await asyncio.wait_for(
                self._try_with_tools(resolved_provider, resolved_model, messages, tool_messages),
                timeout=LLM_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            raise RuntimeError(f"LLM call timed out after {LLM_TIMEOUT_SECONDS}s. Try a different model or provider.")
        except Exception as exc:
            logger.warning(f"[ComputerUse] Tool-call request failed ({exc}), falling back to text parsing")
            try:
                return await asyncio.wait_for(
                    self._try_without_tools(resolved_provider, resolved_model, messages, tool_messages),
                    timeout=LLM_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                raise RuntimeError(f"LLM fallback also timed out after {LLM_TIMEOUT_SECONDS}s.")
            except Exception as fallback_exc:
                raise RuntimeError(f"Both tool-call and fallback failed. Tool error: {exc}. Fallback error: {fallback_exc}")

    async def _try_with_tools(
        self,
        provider: str,
        model: str,
        messages: List[Dict[str, Any]],
        tool_messages: List[Dict[str, Any]],
    ) -> PlannerDecision:
        request = ProviderRequest(
            provider=provider,
            model=model,
            messages=messages,
            tools=TOOL_DEFS,
            tool_choice="auto",
            pass_through=True,
            thinking_enabled=True,
            thinking_mode="Auto",
        )
        completion = await self.gateway.complete(request)
        if completion.tool_calls:
            call = completion.tool_calls[0]
            arguments = call.get("arguments", {})
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments or "{}")
                except json.JSONDecodeError:
                    arguments = {}
            return PlannerDecision(
                name=call["name"],
                arguments=arguments,
                reasoning=completion.thoughts,
                raw_text=completion.text,
            )
        text = completion.text.strip()
        if text:
            parsed = _parse_tool_call_from_text(text)
            if parsed:
                return PlannerDecision(
                    name=parsed["name"],
                    arguments=parsed.get("arguments", {}),
                    reasoning=completion.thoughts,
                    raw_text=completion.text,
                )
        raise RuntimeError(completion.text.strip() or "Model returned no tool call and no parseable action.")

    async def _try_without_tools(
        self,
        provider: str,
        model: str,
        messages: List[Dict[str, Any]],
        tool_messages: List[Dict[str, Any]],
    ) -> PlannerDecision:
        tool_suffix = self._build_tool_suffix()
        text_messages: List[Dict[str, Any]] = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content")
            if isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        parts.append(item.get("text", ""))
                content = "\n".join(parts)
            if role == "system":
                content = (content or "") + tool_suffix
            elif role == "tool":
                name = msg.get("name", "")
                content = f'<tool_result name="{name}">\n{content}\n</tool_result>'
            elif role == "assistant":
                tool_calls = msg.get("tool_calls")
                if tool_calls:
                    for tc in tool_calls:
                        fn = tc.get("function", {})
                        tc_name = fn.get("name", "unknown")
                        tc_args = fn.get("arguments", "{}")
                        tc_json = json.dumps({"name": tc_name, "arguments": json.loads(tc_args) if isinstance(tc_args, str) else tc_args})
                        content = '<ActionTool>' + tc_json + '</ActionTool>'
            if content:
                text_messages.append({"role": role, "content": content})

        request = ProviderRequest(
            provider=provider,
            model=model,
            messages=text_messages,
            pass_through=False,
            thinking_enabled=True,
            thinking_mode="Auto",
        )
        completion = await self.gateway.complete(request)
        text = completion.text.strip()
        if not text:
            raise RuntimeError("Model returned empty response in fallback mode.")
        parsed = _parse_tool_call_from_text(text)
        if parsed:
            return PlannerDecision(
                name=parsed["name"],
                arguments=parsed.get("arguments", {}),
                reasoning=completion.thoughts,
                raw_text=completion.text,
            )
        raise RuntimeError(f"Could not parse a tool call from model response: {text[:300]}")