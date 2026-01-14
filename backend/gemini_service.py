import asyncio
from gemini_webapi import GeminiClient
from gemini_webapi.constants import Model
from .config import load_config
from .agent import Agent
from .prompts import SYSTEM_PROMPT

class GeminiService:
    def __init__(self):
        self.client = None
        self.config = load_config()
        self.sessions = {}
        self.agents = {}  # Agent instances per session
        self.workspace_path = None
    
    def set_workspace(self, path: str) -> str:
        """Set workspace for all new agent sessions."""
        import os
        if os.path.isdir(path):
            self.workspace_path = os.path.abspath(path)
            # Update all existing agents
            for agent in self.agents.values():
                agent.set_workspace(self.workspace_path)
            return f"Workspace set to: {self.workspace_path}"
        return f"Error: '{path}' is not a valid directory."
    
    def get_workspace(self) -> str:
        """Get current workspace path."""
        return self.workspace_path or ""
    
    async def get_client(self):
        if self.client is None:
            self.config = load_config()
            self.client = GeminiClient(
                self.config["Secure_1PSID"], 
                self.config["Secure_1PSIDTS"], 
                proxy=None
            )
            await self.client.init(timeout=30, auto_close=False, close_delay=300, auto_refresh=True)
        return self.client

    def get_agent(self, session_id: str) -> Agent:
        """Get or create an agent for a session."""
        if session_id not in self.agents:
            self.agents[session_id] = Agent(self.workspace_path)
        return self.agents[session_id]

    async def get_session(self, session_id, history=None):
        client = await self.get_client()
        if session_id not in self.sessions:
            model_name = self.config.get("model", "G_2_5_FLASH")
            model = getattr(Model, model_name, Model.G_2_5_FLASH)
            chat = client.start_chat(model=model)
            self.sessions[session_id] = chat
        return self.sessions[session_id]

    async def generate_response(self, text, session_id=None, files=None, history=None):
        client = await self.get_client()
        agent = self.get_agent(session_id) if session_id else None
        
        # Build prompt with system context if we have a workspace
        if agent and self.workspace_path:
            system_context = agent.get_system_prompt()
            full_prompt = f"{system_context}\n\nUser: {text}"
        else:
            full_prompt = text
        
        if session_id:
            chat = await self.get_session(session_id, history=history)
            response = await chat.send_message(full_prompt, files=files)
        else:
            model_name = self.config.get("model", "G_2_5_FLASH")
            model = getattr(Model, model_name, Model.G_2_5_FLASH)
            response = await client.generate_content(full_prompt, model=model, files=files)
        
        response_text = response.text or ""
        
        # Extract images if any
        images = [img.url for img in response.images] if hasattr(response, 'images') and response.images else []
        
        # Process agent response for tool calls
        if agent and self.workspace_path:
            max_iterations = 10
            iteration = 0
            
            while iteration < max_iterations:
                tool_call = agent.parse_tool_call(response_text)
                
                if not tool_call:
                    # No more tool calls, yield final text chunk
                    yield {"text": response_text, "images": images, "is_final": True}
                    break
                
                # Yield the text BEFORE the tool call (if any) and the tool call itself
                display_text = response_text.replace(tool_call["raw_match"], "").strip()
                if display_text:
                    yield {"text": display_text + "\n"}
                
                yield {"tool_call": {"name": tool_call["name"], "args": tool_call["args"]}}
                
                # Execute tool
                try:
                    if tool_call["name"] == "delegate_task":
                        task = tool_call["args"].get("task")
                        context = tool_call["args"].get("context", "")
                        tool_result = await self.run_delegated_task(task, context)
                    else:
                        tool_result = agent.execute_tool(tool_call["name"], tool_call["args"])
                    
                    yield {"tool_result": tool_result}
                    
                    # Feed result back to Gemini
                    response = await chat.send_message(tool_result)
                    response_text = response.text or ""
                    images = [img.url for img in response.images] if hasattr(response, 'images') and response.images else []
                    iteration += 1
                except Exception as e:
                    error_msg = f"Error executing tool '{tool_call['name']}': {str(e)}"
                    yield {"tool_result": error_msg}
                    # Feed error back to Gemini so it can try to correct it
                    response = await chat.send_message(error_msg)
                    response_text = response.text or ""
                    images = [img.url for img in response.images] if hasattr(response, 'images') and response.images else []
                    iteration += 1
        else:
            # Simple response, yield at once (native streaming not supported by this webapi wrapper yet easily)
            yield {"text": response_text, "images": images, "is_final": True}


    async def run_delegated_task(self, task, context="") -> str:
        """Run a task in a separate, temporary session and return the final result."""
        try:
            client = await self.get_client()
            model_name = self.config.get("model", "G_2_5_FLASH")
            model = getattr(Model, model_name, Model.G_2_5_FLASH)
            
            # Create a temporary agent
            temp_agent = Agent(self.workspace_path)
            chat = client.start_chat(model=model)
            
            prompt = f"{temp_agent.get_system_prompt()}\n\nCONTEXT FROM MAIN AGENT: {context}\n\nTASK: {task}\n\nExecute this task autonomously and provide a final summary of what you did."
            
            response = await chat.send_message(prompt)
            response_text = response.text or ""
            
            # Run the agent loop for the sub-agent
            max_iterations = 5
            for _ in range(max_iterations):
                tool_call = temp_agent.parse_tool_call(response_text)
                if not tool_call:
                    break
                
                tool_result = temp_agent.execute_tool(tool_call["name"], tool_call["args"])
                response = await chat.send_message(tool_result)
                response_text = response.text or ""
            
            return f"Sub-agent completion result:\n{response_text}"
        except Exception as e:
            return f"Error in delegated task: {str(e)}"

    async def reset(self):
        self.client = None
        self.sessions = {}
        self.agents = {}
