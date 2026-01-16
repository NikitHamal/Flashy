import re
import json
from typing import Optional
from .tools import Tools
from .prompts import SYSTEM_PROMPT, TOOL_RESULT_TEMPLATE

class Agent:
    """Manages the agent loop: Think -> Act -> Observe."""
    
    def __init__(self, workspace_path: str = None, session_id: str = None):
        self.tools = Tools(workspace_path, session_id=session_id)
        self.conversation_history = []
        self.max_iterations = 10  # Safety limit
        self.session_id = session_id
    
    def set_workspace(self, path: str) -> str:
        """Set the agent's workspace."""
        return self.tools.set_workspace(path)
    
    def get_system_prompt(self) -> str:
        """Get the system prompt with current workspace and plan if available."""
        prompt = SYSTEM_PROMPT.format(workspace_path=self.tools.workspace_path)
        
        # Check for plan.md
        plan_content = self.tools.read_file("plan.md")
        if "Content of plan.md" in plan_content:
            prompt += f"\n\n## Current Plan (plan.md)\n{plan_content}"
            
        return prompt
    
    def parse_tool_call(self, text: str) -> Optional[dict]:
        """
        Parse a tool call from the model's output.
        
        IMPORTANT: This is designed to be strict to avoid false positives.
        Only recognizes tool calls that:
        1. Are in valid JSON format
        2. Have a recognized tool name from our tool list
        3. Prefer ```json code blocks over inline JSON
        """
        if not text:
            return None

        # Get list of valid tool names for validation
        valid_tools = {t['name'] for t in self.tools.get_available_tools()}
        valid_tools.add("delegate_task")  # Special tool not in the standard list

        # 1. Primary: Standard Markdown Code Blocks (most reliable)
        if '```json' in text:
            blocks = text.split('```json')
            for block in blocks[1:]:
                if '```' not in block:
                    continue
                content = block.split('```')[0].strip()
                try:
                    data = json.loads(content)
                    result = self._validate_and_format_tool(data, valid_tools, f"```json\n{content}\n```")
                    if result:
                        return result
                except json.JSONDecodeError:
                    continue

        # 2. Secondary: Look for JSON objects with "action" key
        # Use a more targeted approach - find { followed by "action"
        action_pattern = r'\{\s*"action"\s*:\s*"([^"]+)"'
        matches = list(re.finditer(action_pattern, text))
        
        for match in matches:
            tool_name = match.group(1)
            # Quick validation - is this a known tool?
            if tool_name not in valid_tools:
                continue
            
            # Find the complete JSON object
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
                    result = self._validate_and_format_tool(data, valid_tools, potential_json)
                    if result:
                        return result
                except json.JSONDecodeError:
                    continue

        return None

    def _validate_and_format_tool(self, data: dict, valid_tools: set, raw: str) -> Optional[dict]:
        """
        Validate that parsed JSON is actually a valid tool call.
        Returns formatted tool call dict or None if invalid.
        """
        if not isinstance(data, dict):
            return None
        
        # Extract tool name (support multiple key names)
        tool_name = data.get("action") or data.get("tool") or data.get("name")
        
        if not tool_name or tool_name not in valid_tools:
            return None
        
        # Extract arguments
        args = data.get("args") or data.get("arguments") or {}
        
        return {
            "name": tool_name,
            "args": args,
            "raw_match": raw
        }

    def _is_valid_tool_data(self, data: dict) -> bool:
        """Legacy validation - kept for compatibility."""
        if not isinstance(data, dict):
            return False
        action = data.get("action") or data.get("tool") or data.get("name")
        return bool(action)

    def _format_tool_match(self, data: dict, raw: str) -> dict:
        """Legacy formatting - kept for compatibility."""
        return {
            "name": data.get("action") or data.get("tool") or data.get("name"),
            "args": data.get("args") or data.get("arguments") or {},
            "raw_match": raw
        }
    
    async def execute_tool(self, tool_name: str, args: dict) -> str:
        """Execute a tool and return formatted result."""
        if tool_name == "delegate_task":
            return await self.delegate_task(**args)
        result = await self.tools.execute(tool_name, **args)
        return TOOL_RESULT_TEMPLATE.format(tool_name=tool_name, output=result)
    
    def delegate_task(self, task: str, context: Optional[str] = None) -> str:
        """Spawn a sub-agent to perform a specific task."""
        # This is a bit tricky since it needs to be async or wait for result
        # For simplicity in this local version, we'll run it synchronously 
        # but in reality we might want a separate process or thread.
        print(f"Delegating task: {task}")
        # To avoid infinite recursion, we could limit depth
        # For now, let's just run a one-off completion with Gemini
        # We need access to GeminiService here, but Agent shouldn't depend on it directly
        # Let's instead return a message that the system should handle delegation
        return f"SYSTEM: Delegation requested for task: '{task}'. Context: {context}. Please process this sub-task."
    
    def format_for_streaming(self, text: str, tool_call: dict = None, tool_result: str = None) -> dict:
        """Format response for streaming to frontend."""
        return {
            "text": text,
            "tool_call": tool_call,
            "tool_result": tool_result,
            "is_complete": tool_call is None  # If no tool call, agent is done
        }
    
    async def process_response(self, model_response: str) -> dict:
        """Process model response, execute tools if needed, return structured output."""
        tool_call = self.parse_tool_call(model_response)
        
        if tool_call:
            # Remove the tool call XML from displayed text
            display_text = model_response.replace(tool_call["raw_match"], "").strip()
            
            # Execute the tool
            tool_result = self.execute_tool(tool_call["name"], tool_call["args"])
            
            return {
                "display_text": display_text,
                "tool_call": {
                    "name": tool_call["name"],
                    "args": tool_call["args"]
                },
                "tool_result": tool_result,
                "needs_continuation": True
            }
        else:
            return {
                "display_text": model_response,
                "tool_call": None,
                "tool_result": None,
                "needs_continuation": False
            }
    
    def get_tool_descriptions(self) -> str:
        """Get formatted tool descriptions for the prompt."""
        tools = self.tools.get_available_tools()
        descriptions = [f"- `{t['name']}`: {t['description']}" for t in tools]
        descriptions.append("- `delegate_task`: Delegate a complex sub-task to a specialized sub-agent. Args: task (str), context (str, optional)")
        return "\n".join(descriptions)
