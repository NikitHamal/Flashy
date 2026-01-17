"""
Design Agent Module

This module provides the agent logic for parsing design tool calls
from Gemini responses and executing them on the canvas.
"""

import re
import json
from typing import Optional, Dict, Any, List
from .design_tools import DesignTools
from .design_prompts import DESIGN_SYSTEM_PROMPT, DESIGN_TOOL_RESULT_TEMPLATE


class DesignAgent:
    """
    Manages the design agent loop: Understand -> Design -> Review.
    Parses tool calls from AI responses and executes design operations.
    """

    def __init__(self, canvas_width: int = 1200, canvas_height: int = 800):
        self.tools = DesignTools(canvas_width=canvas_width, canvas_height=canvas_height)
        self.conversation_history: List[Dict[str, Any]] = []
        self.max_iterations = 25  # Higher limit for complex designs
        self.session_id: Optional[str] = None

    def get_system_prompt(self) -> str:
        """Get the system prompt with current canvas info."""
        return DESIGN_SYSTEM_PROMPT.format(
            canvas_width=self.tools.canvas.width,
            canvas_height=self.tools.canvas.height,
            object_count=len(self.tools.canvas.objects)
        )

    def get_canvas_state(self) -> Dict[str, Any]:
        """Get current canvas state as dictionary."""
        return self.tools.canvas.to_dict()

    def set_canvas_state(self, state: Dict[str, Any]) -> str:
        """Set canvas state from dictionary."""
        return self.tools.load_state(state)

    def parse_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse a design tool call from the model's output.

        Recognizes:
        1. ```json code blocks with action key
        2. Inline JSON objects with action key
        """
        if not text:
            return None

        # Get list of valid tool names
        valid_tools = {t['name'] for t in self.tools.get_available_tools()}

        # 1. Primary: Markdown Code Blocks
        if '```json' in text:
            blocks = text.split('```json')
            for block in blocks[1:]:
                if '```' not in block:
                    continue
                content = block.split('```')[0].strip()
                try:
                    data = json.loads(content)
                    result = self._validate_tool_call(data, valid_tools)
                    if result:
                        result["raw_match"] = f"```json\n{content}\n```"
                        return result
                except json.JSONDecodeError:
                    continue

        # 2. Secondary: Inline JSON with "action" key
        action_pattern = r'\{\s*"action"\s*:\s*"([^"]+)"'
        matches = list(re.finditer(action_pattern, text))

        for match in matches:
            tool_name = match.group(1)
            if tool_name not in valid_tools:
                continue

            # Find complete JSON object
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

    def _validate_tool_call(
        self, data: Dict[str, Any], valid_tools: set
    ) -> Optional[Dict[str, Any]]:
        """Validate that parsed JSON is a valid design tool call."""
        if not isinstance(data, dict):
            return None

        tool_name = data.get("action") or data.get("tool") or data.get("name")
        if not tool_name or tool_name not in valid_tools:
            return None

        args = data.get("args") or data.get("arguments") or {}

        return {
            "name": tool_name,
            "args": args
        }

    async def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Execute a design tool and return formatted result."""
        result = await self.tools.execute(tool_name, **args)
        return DESIGN_TOOL_RESULT_TEMPLATE.format(
            tool_name=tool_name,
            output=result
        )

    def format_for_streaming(
        self, text: str, tool_call: Dict = None,
        tool_result: str = None, canvas_update: bool = False
    ) -> Dict[str, Any]:
        """Format response for streaming to frontend."""
        response = {
            "text": text,
            "tool_call": tool_call,
            "tool_result": tool_result,
            "is_complete": tool_call is None
        }

        if canvas_update:
            response["canvas_state"] = self.get_canvas_state()

        return response

    def get_object_summary(self) -> str:
        """Get a brief summary of objects on canvas for context."""
        objects = self.tools.canvas.objects
        if not objects:
            return "The canvas is currently empty."

        summary_parts = []
        type_counts = {}

        for obj in objects:
            type_name = obj.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        for type_name, count in type_counts.items():
            summary_parts.append(f"{count} {type_name}{'s' if count > 1 else ''}")

        return f"Canvas contains: {', '.join(summary_parts)}"

    def process_multiple_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """
        Process multiple tool calls from a single response.
        Returns list of tool call objects.
        """
        tool_calls = []
        valid_tools = {t['name'] for t in self.tools.get_available_tools()}

        # Find all ```json blocks
        if '```json' in text:
            blocks = text.split('```json')
            for block in blocks[1:]:
                if '```' not in block:
                    continue
                content = block.split('```')[0].strip()
                try:
                    data = json.loads(content)
                    result = self._validate_tool_call(data, valid_tools)
                    if result:
                        result["raw_match"] = f"```json\n{content}\n```"
                        tool_calls.append(result)
                except json.JSONDecodeError:
                    continue

        return tool_calls

    async def execute_multiple_tools(
        self, tool_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute multiple tool calls and return results."""
        results = []
        for tool_call in tool_calls:
            result = await self.execute_tool(tool_call["name"], tool_call["args"])
            results.append({
                "tool_call": tool_call,
                "result": result
            })
        return results

    def clean_response_text(self, text: str, raw_matches: List[str] = None) -> str:
        """Clean response text by removing tool call JSON."""
        if not text:
            return ""

        cleaned = text

        # Remove specific matches
        if raw_matches:
            for match in raw_matches:
                cleaned = cleaned.replace(match, "")

        # Remove any remaining ```json blocks that look like tool calls
        json_block_pattern = r'```json\s*\{[^`]*?"(?:action|tool|name)"\s*:[^`]*?\}\s*```'
        cleaned = re.sub(json_block_pattern, '', cleaned, flags=re.DOTALL)

        return cleaned.strip()

    def separate_thinking(self, text: str) -> tuple:
        """
        Separate thinking/reasoning from actual response text.
        Returns (thinking_content, clean_text)
        """
        if not text:
            return None, ""

        thinking_content = None
        clean_text = text

        # Pattern: <think>...</think>
        think_pattern = r'<think>(.*?)</think>'
        matches = re.findall(think_pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            thinking_content = '\n'.join(matches)
            clean_text = re.sub(
                think_pattern, '', clean_text,
                flags=re.DOTALL | re.IGNORECASE
            ).strip()

        # Pattern: [Thinking]...[/Thinking]
        bracket_pattern = r'\[Thinking\](.*?)\[/Thinking\]'
        bracket_matches = re.findall(
            bracket_pattern, clean_text,
            re.DOTALL | re.IGNORECASE
        )
        if bracket_matches:
            if thinking_content:
                thinking_content += '\n' + '\n'.join(bracket_matches)
            else:
                thinking_content = '\n'.join(bracket_matches)
            clean_text = re.sub(
                bracket_pattern, '', clean_text,
                flags=re.DOTALL | re.IGNORECASE
            ).strip()

        return thinking_content, clean_text
