"""
Astro Agent

Handles tool parsing and execution for Flashy Astro.
"""

import json
import re
from typing import Dict, Any, Optional, List, Tuple

from .astro_tools import AstroTools
from .astro_prompts import ASTRO_SYSTEM_PROMPT, ASTRO_TOOL_RESULT_TEMPLATE


class AstroAgent:
    """Astro agent logic with tool parsing."""

    def __init__(self):
        self.tools = AstroTools()
        self.max_iterations = 12

    def get_system_prompt(self) -> str:
        return ASTRO_SYSTEM_PROMPT

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
            for i, ch in enumerate(text[start_idx:], start=start_idx):
                if ch == "{":
                    brace_count += 1
                elif ch == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            if end_idx > start_idx:
                potential = text[start_idx:end_idx]
                try:
                    data = json.loads(potential)
                    result = self._validate_tool_call(data, valid_tools)
                    if result:
                        result["raw_match"] = potential
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

    def execute_tool(
        self,
        tool_name: str,
        kundalis: List[Dict[str, Any]],
        active_id: Optional[str],
        args: Dict[str, Any]
    ) -> Tuple[str, List[Dict[str, Any]], Optional[str]]:
        result, updated, new_active = self.tools.execute(
            tool_name, kundalis, active_id, **args
        )
        return (
            ASTRO_TOOL_RESULT_TEMPLATE.format(tool_name=tool_name, output=result),
            updated,
            new_active
        )
