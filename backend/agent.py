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
        """Get the system prompt with current workspace."""
        return SYSTEM_PROMPT.format(workspace_path=self.tools.workspace_path)
    
    def parse_tool_call(self, text: str) -> Optional[dict]:
        """Parse a tool call from the model's output (Primary: JSON block)."""
        # 1. Look for JSON code blocks
        json_block_pattern = r'```json\s*(.*?)\s*```'
        json_matches = re.finditer(json_block_pattern, text, re.DOTALL)
        
        for match in json_matches:
            try:
                content = match.group(1).strip()
                data = json.loads(content)
                action = data.get("action") or data.get("tool") or data.get("name")
                args = data.get("args") or data.get("arguments") or {}
                
                if action:
                    return {"name": action, "args": args, "raw_match": match.group(0)}
            except Exception:
                continue

        # 2. Look for raw JSON objects (if no code block)
        raw_json_pattern = r'(\{\s*"(action|tool|name)"\s*:\s*".*?"\s*,\s*"(args|arguments)"\s*:\s*\{.*?\s*\}\s*\})'
        raw_matches = re.finditer(raw_json_pattern, text, re.DOTALL)
        for match in raw_matches:
            try:
                data = json.loads(match.group(0))
                action = data.get("action") or data.get("tool") or data.get("name")
                args = data.get("args") or data.get("arguments") or {}
                if action:
                    return {"name": action, "args": args, "raw_match": match.group(0)}
            except Exception:
                continue

        # 3. Last resort XML fallback
        xml_match = re.search(r'<tool_call>(.*?)</tool_call>', text, re.DOTALL)
        if xml_match:
            try:
                tc_content = xml_match.group(1)
                name_match = re.search(r'<name>\s*(.*?)\s*</name>', tc_content, re.DOTALL)
                tool_name = name_match.group(1).strip() if name_match else None
                args_match = re.search(r'<(args|arguments)>\s*(.*?)\s*</(args|arguments)>', tc_content, re.DOTALL)
                args_str = args_match.group(2).strip() if args_match else "{}"
                if tool_name:
                    return {"name": tool_name, "args": json.loads(args_str), "raw_match": xml_match.group(0)}
            except: pass

        return None
    
    def execute_tool(self, tool_name: str, args: dict) -> str:
        """Execute a tool and return formatted result."""
        result = self.tools.execute(tool_name, **args)
        return TOOL_RESULT_TEMPLATE.format(tool_name=tool_name, output=result)
    
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
        return "\n".join([f"- `{t['name']}`: {t['description']}" for t in tools])
