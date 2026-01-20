"""
Design Agent Module (SVG-based)

This module provides the agent logic for parsing SVG design tool calls
from Gemini responses and executing them on the canvas.

The design agent now works with direct SVG generation and manipulation,
providing a more flexible and standards-compliant approach to design.
"""

import re
import json
from typing import Optional, Dict, Any, List
from .svg_tools import SVGTools
from .design_prompts import get_svg_system_prompt, SVG_TOOL_RESULT_TEMPLATE


class DesignAgent:
    """
    Manages the SVG-based design agent loop.
    Parses tool calls from AI responses and executes SVG operations.
    
    The agent now works with native SVG:
    - AI generates SVG code directly
    - Tools manipulate SVG content
    - Frontend renders and makes SVG interactive
    """

    def __init__(self, canvas_width: int = 1200, canvas_height: int = 800):
        self.tools = SVGTools(width=canvas_width, height=canvas_height)
        self.conversation_history: List[Dict[str, Any]] = []
        self.max_iterations = 30
        self.session_id: Optional[str] = None

    def get_system_prompt(self) -> str:
        """Get the system prompt with current canvas info."""
        return get_svg_system_prompt(
            canvas_width=self.tools.canvas.width,
            canvas_height=self.tools.canvas.height,
            element_count=len(self.tools.canvas.elements)
        )

    def get_canvas_state(self) -> Dict[str, Any]:
        """Get current SVG canvas state as dictionary."""
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
        3. ```svg blocks for direct SVG generation
        """
        if not text:
            return None

        # Get list of valid tool names
        valid_tools = {t['name'] for t in self.tools.get_available_tools()}

        # Check for SVG code blocks first
        if '```svg' in text:
            svg_pattern = r'```svg\s*(.*?)```'
            svg_match = re.search(svg_pattern, text, re.DOTALL)
            if svg_match:
                svg_content = svg_match.group(1).strip()
                return {
                    "name": "set_svg",
                    "args": {"svg": svg_content},
                    "raw_match": svg_match.group(0)
                }

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
        return result

    def format_tool_result(self, tool_name: str, result: str) -> str:
        """Format tool result for sending back to Gemini."""
        return SVG_TOOL_RESULT_TEMPLATE.format(
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

    def get_element_summary(self) -> str:
        """Get a brief summary of elements on canvas for context."""
        elements = self.tools.canvas.elements
        if not elements:
            return "The canvas is currently empty."

        summary_parts = []
        type_counts = {}

        for elem in elements:
            tag = elem.get("tag", "unknown")
            type_counts[tag] = type_counts.get(tag, 0) + 1

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

        # Also find SVG blocks
        if '```svg' in text:
            svg_pattern = r'```svg\s*(.*?)```'
            for match in re.finditer(svg_pattern, text, re.DOTALL):
                svg_content = match.group(1).strip()
                tool_calls.append({
                    "name": "set_svg",
                    "args": {"svg": svg_content},
                    "raw_match": match.group(0)
                })

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
        """Clean response text by removing tool call JSON and SVG blocks."""
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

        # Remove any ```svg blocks
        svg_block_pattern = r'```svg\s*.*?```'
        cleaned = re.sub(svg_block_pattern, '', cleaned, flags=re.DOTALL)

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

    def get_svg(self) -> str:
        """Get the current SVG content."""
        return self.tools.get_svg()

    def update_canvas_size(self, width: int, height: int):
        """Update canvas dimensions."""
        self.tools.set_canvas_size(width, height)
