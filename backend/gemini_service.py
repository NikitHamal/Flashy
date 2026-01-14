import asyncio
import re
from gemini_webapi import GeminiClient
from gemini_webapi.constants import Model
from .config import load_config
from .agent import Agent
from .prompts import SYSTEM_PROMPT
from .storage import save_chat_message


class GeminiService:
    """
    Service for interacting with Google Gemini via the gemini-webapi library.
    Handles the agent loop, tool execution, and response streaming.
    """

    def __init__(self):
        self.client = None
        self.config = load_config()
        self.sessions = {}
        self.agents = {}  # Agent instances per session
        self.interrupted_sessions = set()  # Track interrupted sessions
        self.workspace_path = None
        self.workspace_id = None  # Track the UUID

    def set_workspace(self, path: str, workspace_id: str = None) -> str:
        """Set workspace for all new agent sessions."""
        import os

        if os.path.isdir(path):
            self.workspace_path = os.path.abspath(path)
            self.workspace_id = workspace_id
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
            await self.client.init(timeout=600, auto_close=False, close_delay=300, auto_refresh=True)
        return self.client

    def get_agent(self, session_id: str) -> Agent:
        """Get or create an agent for a session."""
        if session_id not in self.agents:
            self.agents[session_id] = Agent(self.workspace_path, session_id=session_id)
        return self.agents[session_id]

    async def get_session(self, session_id, history=None):
        client = await self.get_client()
        if session_id not in self.sessions:
            model_name = self.config.get("model", "G_2_5_FLASH")
            model = getattr(Model, model_name, Model.G_2_5_FLASH)
            chat = client.start_chat(model=model)
            self.sessions[session_id] = chat
        return self.sessions[session_id]

    def interrupt_session(self, session_id: str):
        """Interrupt a running session."""
        self.interrupted_sessions.add(session_id)

    def _clean_response_text(self, text: str, tool_call_raw: str = None) -> str:
        """
        Clean the response text by removing raw JSON tool calls.
        This prevents displaying raw JSON blocks to the user.
        """
        if not text:
            return ""
        
        cleaned = text
        
        # Remove the specific tool call match if provided
        if tool_call_raw:
            cleaned = cleaned.replace(tool_call_raw, "").strip()
        
        # Also remove any orphaned ```json blocks that might be tool calls
        # Pattern: ```json followed by { ... "action" or "tool" ... } followed by ```
        json_block_pattern = r'```json\s*\{[^`]*?"(?:action|tool|name)"\s*:[^`]*?\}\s*```'
        cleaned = re.sub(json_block_pattern, '', cleaned, flags=re.DOTALL).strip()
        
        # Remove standalone JSON objects that look like tool calls (without code blocks)
        # Be careful not to remove legitimate JSON in explanations
        standalone_json_pattern = r'(?<![`\w])\{\s*"(?:action|tool)"\s*:\s*"[^"]+"\s*,\s*"args"\s*:\s*\{[^}]*\}\s*\}(?![`\w])'
        cleaned = re.sub(standalone_json_pattern, '', cleaned).strip()
        
        return cleaned

    async def generate_response(self, text, session_id=None, files=None, history=None):
        """
        Generate a response from Gemini, handling the agent loop with tool calls.
        
        Key behaviors:
        1. Thoughts are yielded on EVERY iteration (not just the first)
        2. Tool calls are ONLY parsed from response.text, NEVER from thoughts
        3. Raw JSON is cleaned from displayed text
        """
        client = await self.get_client()
        agent = self.get_agent(session_id) if session_id else None

        # Track message parts for saving
        message_parts = []
        images = []

        try:
            # Clear any previous interruption for this session
            if session_id in self.interrupted_sessions:
                self.interrupted_sessions.remove(session_id)

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

            # Process agent response for tool calls
            if agent and self.workspace_path:
                max_iterations = 15
                iteration = 0

                while iteration < max_iterations:
                    # Check for interruption
                    if session_id in self.interrupted_sessions:
                        interruption_msg = "\n\n*Agent interrupted by user.*"
                        yield {"text": interruption_msg, "is_final": True}
                        message_parts.append({"type": "text", "content": interruption_msg})
                        break

                    # Extract response components
                    response_text = response.text or ""
                    
                    # Get thoughts - available on EVERY response, not just first
                    thoughts = getattr(response, 'thoughts', None) or ""
                    
                    # Get images
                    if hasattr(response, 'images') and response.images:
                        for img in response.images:
                            if img.url not in images:
                                images.append(img.url)

                    # 1. ALWAYS yield thoughts if present (on every iteration)
                    if thoughts:
                        yield {"thought": thoughts}
                        message_parts.append({"type": "thought", "content": thoughts})

                    # 2. Parse tool call ONLY from response.text (NOT from thoughts)
                    tool_call = agent.parse_tool_call(response_text)

                    if not tool_call:
                        # No tool call found - this is the final answer
                        clean_text = self._clean_response_text(response_text)
                        
                        if clean_text:
                            yield {"text": clean_text, "images": images, "is_final": True}
                            message_parts.append({"type": "text", "content": clean_text})
                        elif images:
                            yield {"text": "", "images": images, "is_final": True}
                        else:
                            # Edge case: empty response
                            yield {"text": "[Agent completed without output]", "is_final": True}
                        break

                    # 3. Handle text BEFORE the tool call (explanation text)
                    display_text = self._clean_response_text(response_text, tool_call["raw_match"])
                    if display_text:
                        yield {"text": display_text + "\n"}
                        message_parts.append({"type": "text", "content": display_text})

                    # 4. Yield the tool call for UI display
                    yield {"tool_call": {"name": tool_call["name"], "args": tool_call["args"]}}
                    message_parts.append({
                        "type": "tool_call", 
                        "content": {"name": tool_call["name"], "args": tool_call["args"]}
                    })

                    # 5. Execute the tool
                    try:
                        if tool_call["name"] == "delegate_task":
                            task = tool_call["args"].get("task")
                            context = tool_call["args"].get("context", "")
                            tool_result = await self.run_delegated_task(task, context)
                        else:
                            tool_result = await agent.execute_tool(tool_call["name"], tool_call["args"])

                        yield {"tool_result": tool_result}
                        message_parts.append({"type": "tool_result", "content": tool_result})

                        # Feed result back to Gemini for next iteration
                        response = await chat.send_message(tool_result)
                        iteration += 1

                    except Exception as e:
                        error_msg = f"Error executing tool '{tool_call['name']}': {str(e)}"
                        yield {"tool_result": error_msg}
                        message_parts.append({"type": "tool_result", "content": error_msg})

                        # Feed error back to Gemini
                        response = await chat.send_message(error_msg)
                        iteration += 1

                # Check if we hit the iteration limit
                if iteration >= max_iterations:
                    limit_msg = "\n\n*Agent reached maximum iterations. Stopping to prevent infinite loop.*"
                    yield {"text": limit_msg, "is_final": True}
                    message_parts.append({"type": "text", "content": limit_msg})

            else:
                # Simple response (no workspace/agent)
                response_text = response.text or ""
                if hasattr(response, 'images') and response.images:
                    for img in response.images:
                        if img.url not in images:
                            images.append(img.url)
                
                yield {"text": response_text, "images": images, "is_final": True}
                message_parts.append({"type": "text", "content": response_text})

        finally:
            # Save AI message with all parts in sequence, even if interrupted
            if session_id and message_parts:
                try:
                    # Ensure we have the latest workspace_id if it was updated during the session
                    save_chat_message(
                        session_id, 
                        "ai", 
                        parts=message_parts, 
                        images=images, 
                        workspace_id=self.workspace_id
                    )
                    print(f"[GeminiService] Saved AI message for session {session_id} ({len(message_parts)} parts)")
                except Exception as e:
                    print(f"[GeminiService] Failed to save AI message: {e}")



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
        """Reset the client and all sessions."""
        self.client = None
        self.sessions = {}
        self.agents = {}
