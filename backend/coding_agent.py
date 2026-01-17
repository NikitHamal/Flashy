"""
Enhanced Coding Agent Module

This module provides the production-grade agent logic for the Flashy Coding Agent.
Features:
- Robust tool call parsing with multiple format support
- Enhanced error handling with recovery strategies
- Context management for large codebases
- Structured thought processing
- Tool execution with validation and retry logic
"""

import re
import json
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .tools import Tools
from .coding_prompts import (
    get_system_prompt,
    get_tool_result_template,
    get_error_recovery_hint,
    build_workspace_context,
    TOOL_SCHEMAS
)


class ToolCallStatus(Enum):
    """Status of a tool call execution."""
    SUCCESS = "success"
    ERROR = "error"
    RETRY = "retry"
    SKIP = "skip"


@dataclass
class ToolExecution:
    """Represents a tool execution with its result."""
    tool_name: str
    args: Dict[str, Any]
    result: str
    status: ToolCallStatus
    retry_count: int = 0
    error_hint: Optional[str] = None


@dataclass
class AgentContext:
    """Maintains agent context across iterations."""
    workspace_path: str
    session_id: str
    iteration_count: int = 0
    max_iterations: int = 20
    tool_history: List[ToolExecution] = field(default_factory=list)
    file_cache: Dict[str, str] = field(default_factory=dict)
    recent_errors: List[str] = field(default_factory=list)

    def add_tool_execution(self, execution: ToolExecution):
        """Track tool execution."""
        self.tool_history.append(execution)
        if execution.status == ToolCallStatus.ERROR:
            self.recent_errors.append(f"{execution.tool_name}: {execution.result[:200]}")
            # Keep only last 5 errors
            self.recent_errors = self.recent_errors[-5:]

    def get_tool_summary(self) -> str:
        """Get summary of recent tool executions."""
        if not self.tool_history:
            return "No tools executed yet."

        recent = self.tool_history[-5:]
        lines = ["Recent tool executions:"]
        for exec in recent:
            status_icon = "✓" if exec.status == ToolCallStatus.SUCCESS else "✗"
            lines.append(f"  {status_icon} {exec.tool_name}")
        return "\n".join(lines)


class CodingAgent:
    """
    Production-grade coding agent with enhanced capabilities.

    Features:
    - Robust tool call parsing
    - Error recovery with hints
    - Context-aware execution
    - Structured output for streaming
    """

    def __init__(self, workspace_path: str = None, session_id: str = None):
        self.tools = Tools(workspace_path, session_id=session_id)
        self.conversation_history: List[Dict[str, Any]] = []
        self.session_id = session_id

        # Agent context
        self.context = AgentContext(
            workspace_path=workspace_path or "",
            session_id=session_id or "",
            max_iterations=20
        )

        # Tool call parsing patterns (ordered by priority)
        self._json_block_pattern = re.compile(
            r'```json\s*(\{[\s\S]*?\})\s*```',
            re.MULTILINE
        )
        self._inline_action_pattern = re.compile(
            r'\{\s*"action"\s*:\s*"([^"]+)"'
        )

    def set_workspace(self, path: str) -> str:
        """Set the agent's workspace."""
        result = self.tools.set_workspace(path)
        self.context.workspace_path = path
        return result

    def get_system_prompt(self) -> str:
        """Get the system prompt with current workspace context."""
        # Build context from recent activity
        workspace_context = ""

        # Add tool execution summary if we have history
        if self.context.tool_history:
            workspace_context = self.context.get_tool_summary()

        # Add error context if we've had recent errors
        if self.context.recent_errors:
            workspace_context += "\n\n### Recent Errors (address these):\n"
            for err in self.context.recent_errors[-3:]:
                workspace_context += f"- {err}\n"

        return get_system_prompt(
            workspace_path=self.tools.workspace_path,
            workspace_context=workspace_context
        )

    def parse_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse a tool call from model output with enhanced robustness.

        Supports multiple formats:
        1. ```json code blocks (preferred)
        2. Inline JSON with "action" key
        3. Fallback patterns for edge cases

        Returns dict with: name, args, raw_match
        """
        if not text:
            return None

        # Get valid tool names
        valid_tools = {t['name'] for t in self.tools.get_available_tools()}
        valid_tools.add("delegate_task")

        # Strategy 1: JSON code blocks (most reliable)
        json_blocks = self._json_block_pattern.findall(text)
        for block in json_blocks:
            result = self._try_parse_json(block, valid_tools)
            if result:
                # Find the full match for raw_match
                full_match = f"```json\n{block}\n```"
                if full_match not in text:
                    full_match = f"```json{block}```"
                result["raw_match"] = full_match
                return result

        # Strategy 2: Find inline JSON with action key
        for match in self._inline_action_pattern.finditer(text):
            tool_name = match.group(1)
            if tool_name not in valid_tools:
                continue

            # Extract complete JSON object
            json_str = self._extract_json_object(text, match.start())
            if json_str:
                result = self._try_parse_json(json_str, valid_tools)
                if result:
                    result["raw_match"] = json_str
                    return result

        # Strategy 3: Look for tool-like patterns without proper JSON
        # This handles edge cases where the model outputs malformed JSON
        for tool_name in valid_tools:
            pattern = rf'{tool_name}\s*\(\s*([^)]*)\s*\)'
            match = re.search(pattern, text)
            if match:
                # Try to parse function-call style
                args_str = match.group(1)
                args = self._parse_function_args(args_str)
                if args is not None:
                    return {
                        "name": tool_name,
                        "args": args,
                        "raw_match": match.group(0)
                    }

        return None

    def _try_parse_json(self, json_str: str, valid_tools: set) -> Optional[Dict[str, Any]]:
        """Try to parse JSON and validate as tool call."""
        try:
            # Clean up common issues
            json_str = json_str.strip()
            # Handle trailing commas (common LLM mistake)
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)

            data = json.loads(json_str)

            if not isinstance(data, dict):
                return None

            # Extract tool name (support multiple key formats)
            tool_name = (
                data.get("action") or
                data.get("tool") or
                data.get("name") or
                data.get("function")
            )

            if not tool_name or tool_name not in valid_tools:
                return None

            # Extract args
            args = (
                data.get("args") or
                data.get("arguments") or
                data.get("parameters") or
                data.get("params") or
                {}
            )

            # Validate args is a dict
            if not isinstance(args, dict):
                args = {}

            return {
                "name": tool_name,
                "args": args
            }

        except json.JSONDecodeError:
            return None

    def _extract_json_object(self, text: str, start_idx: int) -> Optional[str]:
        """Extract a complete JSON object starting at start_idx."""
        brace_count = 0
        in_string = False
        escape_next = False
        end_idx = start_idx

        for i, char in enumerate(text[start_idx:], start=start_idx):
            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break

        if brace_count == 0 and end_idx > start_idx:
            return text[start_idx:end_idx]
        return None

    def _parse_function_args(self, args_str: str) -> Optional[Dict[str, Any]]:
        """Parse function-call style arguments."""
        if not args_str.strip():
            return {}

        try:
            # Try to parse as key=value pairs
            args = {}
            # Simple pattern: key=value or key="value"
            for match in re.finditer(r'(\w+)\s*=\s*(["\']?)([^,"\']*)(["\']?)', args_str):
                key = match.group(1)
                value = match.group(3)
                args[key] = value
            return args if args else None
        except Exception:
            return None

    async def execute_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        retry_on_error: bool = True
    ) -> Tuple[str, ToolCallStatus]:
        """
        Execute a tool with enhanced error handling.

        Returns tuple of (result_string, status).
        """
        max_retries = 2 if retry_on_error else 0
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                # Handle delegation specially
                if tool_name == "delegate_task":
                    result = self._handle_delegation(args)
                    status = ToolCallStatus.SUCCESS
                else:
                    result = await self.tools.execute(tool_name, **args)
                    status = self._determine_status(result)

                # Track execution
                execution = ToolExecution(
                    tool_name=tool_name,
                    args=args,
                    result=result,
                    status=status,
                    retry_count=attempt
                )
                self.context.add_tool_execution(execution)

                # Format result
                formatted = get_tool_result_template(
                    tool_name=tool_name,
                    output=result,
                    success=(status == ToolCallStatus.SUCCESS)
                )

                # Add recovery hint if error
                if status == ToolCallStatus.ERROR:
                    hint = get_error_recovery_hint(result)
                    formatted += f"\n{hint}"

                return formatted, status

            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue

        # All retries failed
        error_result = f"Error executing '{tool_name}' after {max_retries + 1} attempts: {last_error}"
        hint = get_error_recovery_hint(last_error)

        execution = ToolExecution(
            tool_name=tool_name,
            args=args,
            result=error_result,
            status=ToolCallStatus.ERROR,
            retry_count=max_retries,
            error_hint=hint
        )
        self.context.add_tool_execution(execution)

        return get_tool_result_template(
            tool_name=tool_name,
            output=f"{error_result}\n{hint}",
            success=False
        ), ToolCallStatus.ERROR

    def _determine_status(self, result: str) -> ToolCallStatus:
        """Determine if a tool execution was successful."""
        result_lower = result.lower()

        # Check for error indicators
        error_patterns = [
            "error:",
            "error ",
            "failed",
            "not found",
            "permission denied",
            "invalid",
            "exception",
            "traceback"
        ]

        for pattern in error_patterns:
            if pattern in result_lower:
                return ToolCallStatus.ERROR

        return ToolCallStatus.SUCCESS

    def _handle_delegation(self, args: Dict[str, Any]) -> str:
        """Handle task delegation request."""
        task = args.get("task", "")
        context = args.get("context", "")

        return f"""SYSTEM: Delegation requested.
Task: {task}
Context: {context}

The main agent loop will handle this delegation by spawning a sub-agent."""

    def format_for_streaming(
        self,
        text: str = None,
        tool_call: Dict = None,
        tool_result: str = None,
        thought: str = None,
        is_final: bool = False
    ) -> Dict[str, Any]:
        """Format response for streaming to frontend."""
        response = {}

        if thought:
            response["thought"] = thought
        if text:
            response["text"] = text
        if tool_call:
            response["tool_call"] = {
                "name": tool_call.get("name"),
                "args": tool_call.get("args", {})
            }
        if tool_result:
            response["tool_result"] = tool_result
        if is_final:
            response["is_final"] = True

        return response

    def clean_response_text(self, text: str, raw_matches: List[str] = None) -> str:
        """Clean response text by removing tool call JSON and artifacts."""
        if not text:
            return ""

        cleaned = text

        # Remove specific matches
        if raw_matches:
            for match in raw_matches:
                cleaned = cleaned.replace(match, "")

        # Remove orphaned JSON blocks that look like tool calls
        json_block_pattern = r'```json\s*\{[^`]*?"(?:action|tool|name)"\s*:[^`]*?\}\s*```'
        cleaned = re.sub(json_block_pattern, '', cleaned, flags=re.DOTALL)

        # Remove standalone JSON objects that look like tool calls
        standalone_pattern = r'(?<![`\w])\{\s*"(?:action|tool)"\s*:\s*"[^"]+"\s*,\s*"args"\s*:\s*\{[^}]*\}\s*\}(?![`\w])'
        cleaned = re.sub(standalone_pattern, '', cleaned)

        # Remove Google content URLs (Gemini API artifact)
        google_pattern = r'https?://googleusercontent\.com/youtube_content/\d+'
        cleaned = re.sub(google_pattern, '', cleaned)

        # Clean up excessive whitespace
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

        return cleaned.strip()

    def separate_thinking(self, text: str) -> Tuple[Optional[str], str]:
        """
        Separate thinking/reasoning from response text.

        Returns (thinking_content, clean_text)
        """
        if not text:
            return None, ""

        thinking_parts = []
        clean_text = text

        # Pattern 1: <think>...</think>
        think_matches = re.findall(r'<think>(.*?)</think>', text, re.DOTALL | re.IGNORECASE)
        if think_matches:
            thinking_parts.extend(think_matches)
            clean_text = re.sub(r'<think>.*?</think>', '', clean_text, flags=re.DOTALL | re.IGNORECASE)

        # Pattern 2: [Thinking]...[/Thinking]
        bracket_matches = re.findall(r'\[Thinking\](.*?)\[/Thinking\]', clean_text, re.DOTALL | re.IGNORECASE)
        if bracket_matches:
            thinking_parts.extend(bracket_matches)
            clean_text = re.sub(r'\[Thinking\].*?\[/Thinking\]', '', clean_text, flags=re.DOTALL | re.IGNORECASE)

        # Pattern 3: **Thinking:** ... (up to next section or double newline)
        thinking_header = re.findall(r'\*\*Thinking:\*\*\s*(.*?)(?=\*\*[A-Z]|\n\n|$)', clean_text, re.DOTALL)
        if thinking_header:
            thinking_parts.extend(thinking_header)
            clean_text = re.sub(r'\*\*Thinking:\*\*\s*.*?(?=\*\*[A-Z]|\n\n|$)', '', clean_text, flags=re.DOTALL)

        thinking_content = '\n\n'.join(thinking_parts).strip() if thinking_parts else None
        return thinking_content, clean_text.strip()

    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of agent context for debugging."""
        return {
            "workspace": self.context.workspace_path,
            "session_id": self.context.session_id,
            "iterations": self.context.iteration_count,
            "tools_executed": len(self.context.tool_history),
            "recent_errors": self.context.recent_errors,
            "file_cache_size": len(self.context.file_cache)
        }

    def increment_iteration(self) -> bool:
        """Increment iteration counter and check limit."""
        self.context.iteration_count += 1
        return self.context.iteration_count < self.context.max_iterations

    def reset_context(self):
        """Reset agent context for new conversation."""
        self.context = AgentContext(
            workspace_path=self.context.workspace_path,
            session_id=self.context.session_id
        )

    def get_tool_descriptions(self) -> str:
        """Get formatted tool descriptions for prompts."""
        tools = self.tools.get_available_tools()
        descriptions = []

        for t in tools:
            schema = TOOL_SCHEMAS.get(t['name'])
            if schema:
                # Use schema description if available
                descriptions.append(f"- `{t['name']}`: {schema['description']}")
            else:
                descriptions.append(f"- `{t['name']}`: {t['description']}")

        descriptions.append("- `delegate_task`: Delegate a complex sub-task to a specialized sub-agent. Args: task (str), context (str, optional)")

        return "\n".join(descriptions)

    async def process_response(self, model_response: str) -> Dict[str, Any]:
        """
        Process model response, execute tools if needed.

        Returns structured output with:
        - display_text: Text to show user
        - tool_call: Parsed tool call (if any)
        - tool_result: Result of tool execution
        - needs_continuation: Whether agent loop should continue
        - thought: Extracted thinking content
        """
        # Separate thinking from response
        thinking, clean_response = self.separate_thinking(model_response)

        # Parse tool call from clean response
        tool_call = self.parse_tool_call(clean_response)

        result = {
            "thought": thinking,
            "needs_continuation": False
        }

        if tool_call:
            # Clean display text (remove tool call JSON)
            display_text = self.clean_response_text(clean_response, [tool_call.get("raw_match", "")])

            # Execute the tool
            tool_result, status = await self.execute_tool(
                tool_call["name"],
                tool_call["args"]
            )

            result.update({
                "display_text": display_text,
                "tool_call": {
                    "name": tool_call["name"],
                    "args": tool_call["args"]
                },
                "tool_result": tool_result,
                "tool_status": status.value,
                "needs_continuation": True
            })
        else:
            # No tool call - final response
            result.update({
                "display_text": self.clean_response_text(clean_response),
                "tool_call": None,
                "tool_result": None,
                "needs_continuation": False
            })

        return result
