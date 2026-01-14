import re
import json
from typing import Optional
from .tools import Tools
from .prompts import SYSTEM_PROMPT, TOOL_RESULT_TEMPLATE

class Agent:
    """Manages the agent loop: Think -> Act -> Observe."""
    
    def __init__(self, workspace_path: str = None):
        self.tools = Tools(workspace_path)
        self.conversation_history = []
        self.max_iterations = 10  # Safety limit
    
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
        """Parse a tool call from the model's output (Robust & Fast)."""
        if not text:
            return None

        # 1. Primary: Standard Markdown Blocks
        if '```json' in text:
            blocks = text.split('```json')
            for block in blocks[1:]:
                content = block.split('```')[0].strip()
                try:
                    data = json.loads(content)
                    if self._is_valid_tool_data(data):
                        return self._format_tool_match(data, f"```json{content}```")
                except: continue

        # 2. Secondary: Aggressive Bracket Matching (Non-Recursive)
        # Find all '{' indices
        start_indices = [i for i, char in enumerate(text) if char == '{']
        
        # Try to find matching '}' for each '{', starting from the largest possible blocks
        for start_idx in start_indices:
            # We look for the last '}' that could possibly close this JSON
            end_idx = text.rfind('}', start_idx)
            while end_idx != -1 and end_idx > start_idx:
                potential_json = text[start_idx:end_idx+1]
                try:
                    # Quick check if it looks like our tool before expensive parse
                    if '"action"' in potential_json or '"tool"' in potential_json or '"name"' in potential_json:
                        data = json.loads(potential_json)
                        if self._is_valid_tool_data(data):
                            return self._format_tool_match(data, potential_json)
                except:
                    pass
                # Try the next '}' coming backwards
                end_idx = text.rfind('}', start_idx, end_idx)

        return None

    def _is_valid_tool_data(self, data: dict) -> bool:
        """Verify if a JSON object is a valid tool call."""
        if not isinstance(data, dict): return False
        action = data.get("action") or data.get("tool") or data.get("name")
        return bool(action)

    def _format_tool_match(self, data: dict, raw: str) -> dict:
        """Format the parsed data into a standard tool call object."""
        return {
            "name": data.get("action") or data.get("tool") or data.get("name"),
            "args": data.get("args") or data.get("arguments") or {},
            "raw_match": raw
        }
    
    def execute_tool(self, tool_name: str, args: dict) -> str:
        """Execute a tool and return formatted result."""
        if tool_name == "delegate_task":
            return self.delegate_task(**args)
        result = self.tools.execute(tool_name, **args)
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
