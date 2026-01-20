"""
Astro Agent

Parses tool calls and executes astro tools.
"""

import json
import re
from typing import Any, Dict, List, Optional

from .astro_tools import AstroTools
from .astro_prompts import ASTRO_SYSTEM_PROMPT, ASTRO_TOOL_RESULT_TEMPLATE


class AstroAgent:
    def __init__(self):
        self.tools = AstroTools()
        self.conversation_history: List[Dict[str, Any]] = []
        self.max_iterations = 20

    def get_system_prompt(self) -> str:
        return ASTRO_SYSTEM_PROMPT.format(tool_descriptions=self.get_tool_descriptions())

    def get_tool_descriptions(self) -> str:
        tools = self.tools.get_available_tools()
        return "\n".join([f"- `{t['name']}`: {t['description']}" for t in tools])

    def parse_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None

        valid_tools = {t["name"] for t in self.tools.get_available_tools()}

        if "```json" in text:
            blocks = text.split("```json")
            for block in blocks[1:]:
                if "```" not in block:
                    continue
                content = block.split("```")[0].strip()
                try:
                    data = json.loads(content)
                    result = self._validate_tool_call(data, valid_tools)
                    if result:
                        result["raw_match"] = f"```json\n{content}\n```"
                        return result
                except json.JSONDecodeError:
                    continue

        action_pattern = r'\{\s*"action"\s*:\s*"([^"]+)"'
        matches = list(re.finditer(action_pattern, text))
        for match in matches:
            tool_name = match.group(1)
            if tool_name not in valid_tools:
                continue
            start_idx = match.start()
            brace_count = 0
            end_idx = start_idx
            for i, char in enumerate(text[start_idx:], start=start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            if end_idx > start_idx:
                potential_json = text[start_idx:end_idx]
                try:
                    data = json.loads(potential_json)
                    result = self._validate_tool_call(data, valid_tools)
                    if result:
                        result["raw_match"] = potential_json
                        return result
                except json.JSONDecodeError:
                    continue

        return None

    def _validate_tool_call(self, data: Dict[str, Any], valid_tools: set) -> Optional[Dict[str, Any]]:
        if not isinstance(data, dict):
            return None
        tool_name = data.get("action") or data.get("tool") or data.get("name")
        if not tool_name or tool_name not in valid_tools:
            return None
        args = data.get("args") or data.get("arguments") or {}
        return {"name": tool_name, "args": args}

    async def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        result = await self.tools.execute(tool_name, **(args or {}))
        return ASTRO_TOOL_RESULT_TEMPLATE.format(tool_name=tool_name, output=result)
