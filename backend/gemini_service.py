"""
Gemini Service Module

This module provides the main service for Flashy Coding Agent interactions
with Google Gemini via the gemini-webapi library.

Enhanced Features:
- Production-grade agent loop with robust error handling
- Response filtering for clean output
- Session management with interruption support
- Thought extraction and structured streaming
- Tool execution with retry logic
"""

import asyncio
import re
from typing import Dict, Any, List, Optional, AsyncGenerator

from gemini_webapi import GeminiClient
from gemini_webapi.constants import Model

from .config import load_config
from .coding_agent import CodingAgent, ToolCallStatus
from .coding_prompts import get_system_prompt, get_tool_result_template
from .response_filter import ResponseFilter, ThoughtFilter
from .storage import save_chat_message, save_chat_metadata, get_chat_metadata


class GeminiService:
    """
    Production-grade service for Gemini-powered coding agent.

    Handles:
    - Client initialization and session management
    - Agent loop with tool execution
    - Response streaming with thought separation
    - Interruption and cancellation support
    - Persistent session storage
    """

    def __init__(self):
        self.client: Optional[GeminiClient] = None
        self.config = load_config()
        self.sessions: Dict[str, Any] = {}
        self.agents: Dict[str, CodingAgent] = {}
        self.interrupted_sessions: set = set()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.workspace_path: Optional[str] = None
        self.workspace_id: Optional[str] = None

        # Initialize filters
        self.response_filter = ResponseFilter(aggressive=False)
        self.thought_filter = ThoughtFilter()

    def set_workspace(self, path: str, workspace_id: str = None) -> str:
        """Set workspace for all agent sessions."""
        import os

        if os.path.isdir(path):
            self.workspace_path = os.path.abspath(path)
            self.workspace_id = workspace_id

            # Update existing agents
            for agent in self.agents.values():
                agent.set_workspace(self.workspace_path)

            return f"Workspace set to: {self.workspace_path}"
        return f"Error: '{path}' is not a valid directory."

    def get_workspace(self) -> str:
        """Get current workspace path."""
        return self.workspace_path or ""

    async def get_client(self) -> GeminiClient:
        """Get or initialize Gemini client."""
        if self.client is None:
            self.config = load_config()

            self.client = GeminiClient(
                self.config["Secure_1PSID"],
                self.config["Secure_1PSIDTS"],
                proxy=None
            )

            # Inject additional cookies if present
            if self.config.get("Secure_1PSIDCC"):
                self.client.cookies["__Secure-1PSIDCC"] = self.config["Secure_1PSIDCC"]

            await self.client.init(
                timeout=600,
                auto_close=False,
                close_delay=300,
                auto_refresh=True
            )

        return self.client

    def get_agent(self, session_id: str) -> CodingAgent:
        """Get or create a coding agent for a session."""
        if session_id not in self.agents:
            self.agents[session_id] = CodingAgent(
                workspace_path=self.workspace_path,
                session_id=session_id
            )
        return self.agents[session_id]

    async def get_session(self, session_id: str, history: Any = None):
        """Get or create a Gemini chat session."""
        client = await self.get_client()

        if session_id not in self.sessions:
            model_name = self.config.get("model", "G_2_5_FLASH")
            model = getattr(Model, model_name, Model.G_2_5_FLASH)

            # Try to restore from saved metadata
            saved_meta = get_chat_metadata(session_id)
            if saved_meta:
                chat = client.start_chat(
                    model=model,
                    cid=saved_meta.get('cid'),
                    rid=saved_meta.get('rid'),
                    rcid=saved_meta.get('rcid')
                )
                print(f"[GeminiService] Restored session {session_id}")
            else:
                chat = client.start_chat(model=model)

            self.sessions[session_id] = chat

        return self.sessions[session_id]

    def interrupt_session(self, session_id: str):
        """Interrupt a running session."""
        self.interrupted_sessions.add(session_id)

        if session_id in self.active_tasks:
            task = self.active_tasks[session_id]
            if task and not task.done():
                task.cancel()
                print(f"[GeminiService] Cancelled task for session {session_id}")

    def _is_interrupted(self, session_id: str) -> bool:
        """Check if session is interrupted."""
        return session_id in self.interrupted_sessions

    def _clean_response_text(self, text: str, tool_call_raw: str = None) -> str:
        """Clean response text by removing JSON tool calls and artifacts."""
        if not text:
            return ""

        cleaned = text

        # Remove specific tool call match
        if tool_call_raw:
            cleaned = cleaned.replace(tool_call_raw, "").strip()

        # Remove orphaned JSON blocks that look like tool calls
        json_block_pattern = r'```json\s*\{[^`]*?"(?:action|tool|name)"\s*:[^`]*?\}\s*```'
        cleaned = re.sub(json_block_pattern, '', cleaned, flags=re.DOTALL).strip()

        # Remove standalone tool-call JSON
        standalone_pattern = r'(?<![`\w])\{\s*"(?:action|tool)"\s*:\s*"[^"]+"\s*,\s*"args"\s*:\s*\{[^}]*\}\s*\}(?![`\w])'
        cleaned = re.sub(standalone_pattern, '', cleaned).strip()

        # Apply response filter (removes YouTube links, etc.)
        cleaned = self.response_filter.filter(cleaned)

        return cleaned

    def _separate_thinking(self, text: str) -> tuple:
        """Separate thinking from response using enhanced filter."""
        if not text:
            return None, ""
        return self.thought_filter.extract_thoughts(text)

    async def _send_with_retry(
        self,
        chat,
        message: str,
        files: List[str] = None,
        max_retries: int = 3,
        timeout: int = 120
    ):
        """Send message with retry logic and timeout."""
        last_error = None

        for attempt in range(max_retries):
            try:
                if files:
                    response = await asyncio.wait_for(
                        chat.send_message(message, files=files),
                        timeout=timeout
                    )
                else:
                    response = await asyncio.wait_for(
                        chat.send_message(message),
                        timeout=timeout
                    )
                return response

            except asyncio.CancelledError:
                raise

            except asyncio.TimeoutError:
                last_error = f"Request timed out after {timeout}s"
                print(f"[GeminiService] Attempt {attempt + 1}/{max_retries}: {last_error}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

            except Exception as e:
                last_error = str(e)
                print(f"[GeminiService] Attempt {attempt + 1}/{max_retries}: {last_error}")

                error_str = str(e).lower()
                if "invalid response" in error_str or "failed to generate" in error_str:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                raise

        raise Exception(f"Failed after {max_retries} attempts: {last_error}")

    async def generate_response(
        self,
        text: str,
        session_id: str = None,
        files: List[str] = None,
        history: Any = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate response from Gemini with full agent loop.

        Yields dictionaries with:
        - thought: AI thinking content
        - text: Response text for display
        - tool_call: Tool being called {name, args}
        - tool_result: Tool execution result
        - images: Generated image URLs
        - is_final: Whether this is the final response
        """
        client = await self.get_client()
        agent = self.get_agent(session_id) if session_id else None
        chat = None

        # Track message parts for saving
        message_parts: List[Dict[str, Any]] = []
        images: List[str] = []

        try:
            # Clear previous interruption
            if session_id in self.interrupted_sessions:
                self.interrupted_sessions.remove(session_id)

            # Reset agent context for new conversation turn
            if agent:
                agent.reset_context()

            # Build prompt with system context
            if agent and self.workspace_path:
                system_context = agent.get_system_prompt()
                full_prompt = f"{system_context}\n\n## User Request\n{text}\n\nExecute this task using the appropriate tools."
            else:
                full_prompt = text

            # Get or create session
            if session_id:
                chat = await self.get_session(session_id, history=history)
                response = await self._send_with_retry(chat, full_prompt, files=files)
            else:
                model_name = self.config.get("model", "G_2_5_FLASH")
                model = getattr(Model, model_name, Model.G_2_5_FLASH)
                response = await asyncio.wait_for(
                    client.generate_content(full_prompt, model=model, files=files),
                    timeout=120
                )

            # Agent loop
            if agent and self.workspace_path:
                max_iterations = 20
                iteration = 0

                while iteration < max_iterations:
                    # Check for interruption
                    if self._is_interrupted(session_id):
                        yield {"text": "\n\n*Agent interrupted by user.*", "is_final": True}
                        break

                    # Increment agent iteration
                    if not agent.increment_iteration():
                        yield {
                            "text": "\n\n*Agent reached maximum iterations.*",
                            "is_final": True
                        }
                        break

                    # Extract response components
                    response_text = response.text or ""

                    # Get thoughts from API and embedded in text
                    api_thoughts = getattr(response, 'thoughts', None) or ""
                    embedded_thinking, clean_response = self._separate_thinking(response_text)

                    # Combine thoughts
                    all_thoughts = ""
                    if api_thoughts:
                        all_thoughts = api_thoughts
                    if embedded_thinking:
                        all_thoughts = f"{all_thoughts}\n\n{embedded_thinking}".strip() if all_thoughts else embedded_thinking

                    # Get images
                    if hasattr(response, 'images') and response.images:
                        for img in response.images:
                            if img.url not in images:
                                images.append(img.url)

                    # Yield thoughts
                    if all_thoughts:
                        yield {"thought": all_thoughts}
                        message_parts.append({"type": "thought", "content": all_thoughts})

                    # Parse tool call from clean response
                    tool_call = agent.parse_tool_call(clean_response)

                    if not tool_call:
                        # No tool call - final response
                        final_text = self._clean_response_text(clean_response)

                        if final_text:
                            yield {"text": final_text, "images": images, "is_final": True}
                            message_parts.append({"type": "text", "content": final_text})
                        elif images:
                            yield {"text": "", "images": images, "is_final": True}
                        else:
                            yield {"text": "[Agent completed]", "is_final": True}
                        break

                    # Handle text before tool call
                    display_text = self._clean_response_text(
                        clean_response,
                        tool_call.get("raw_match")
                    )
                    if display_text:
                        yield {"text": display_text + "\n"}
                        message_parts.append({"type": "text", "content": display_text})

                    # Yield tool call
                    yield {
                        "tool_call": {
                            "name": tool_call["name"],
                            "args": tool_call["args"]
                        }
                    }
                    message_parts.append({
                        "type": "tool_call",
                        "content": {
                            "name": tool_call["name"],
                            "args": tool_call["args"]
                        }
                    })

                    # Check interruption before tool execution
                    if self._is_interrupted(session_id):
                        yield {"text": "\n\n*Agent interrupted by user.*", "is_final": True}
                        break

                    # Execute tool
                    try:
                        if tool_call["name"] == "delegate_task":
                            task = tool_call["args"].get("task", "")
                            context = tool_call["args"].get("context", "")
                            tool_result = await self.run_delegated_task(task, context)
                            tool_status = ToolCallStatus.SUCCESS
                        else:
                            tool_result, tool_status = await agent.execute_tool(
                                tool_call["name"],
                                tool_call["args"]
                            )

                        yield {"tool_result": tool_result}
                        message_parts.append({"type": "tool_result", "content": tool_result})

                        # Check interruption before next API call
                        if self._is_interrupted(session_id):
                            yield {"text": "\n\n*Agent interrupted by user.*", "is_final": True}
                            break

                        # Feed result back to Gemini
                        response = await self._send_with_retry(chat, tool_result)
                        iteration += 1

                    except asyncio.CancelledError:
                        yield {"text": "\n\n*Agent interrupted by user.*", "is_final": True}
                        break

                    except Exception as e:
                        error_msg = f"Error executing '{tool_call['name']}': {str(e)}"
                        yield {"tool_result": error_msg}
                        message_parts.append({"type": "tool_result", "content": error_msg})

                        if self._is_interrupted(session_id):
                            yield {"text": "\n\n*Agent interrupted by user.*", "is_final": True}
                            break

                        # Feed error back to Gemini for recovery
                        response = await self._send_with_retry(chat, error_msg)
                        iteration += 1

                # Check iteration limit
                if iteration >= max_iterations:
                    yield {
                        "text": "\n\n*Agent reached maximum iterations. Task may be incomplete.*",
                        "is_final": True
                    }

            else:
                # Simple response (no workspace/agent)
                response_text = response.text or ""
                embedded_thinking, clean_text = self._separate_thinking(response_text)
                api_thoughts = getattr(response, 'thoughts', None) or ""

                all_thoughts = ""
                if api_thoughts:
                    all_thoughts = api_thoughts
                if embedded_thinking:
                    all_thoughts = f"{all_thoughts}\n\n{embedded_thinking}".strip() if all_thoughts else embedded_thinking

                if all_thoughts:
                    yield {"thought": all_thoughts}
                    message_parts.append({"type": "thought", "content": all_thoughts})

                if hasattr(response, 'images') and response.images:
                    for img in response.images:
                        if img.url not in images:
                            images.append(img.url)

                # Apply response filter
                clean_text = self.response_filter.filter(clean_text)

                yield {"text": clean_text, "images": images, "is_final": True}
                message_parts.append({"type": "text", "content": clean_text})

        except asyncio.CancelledError:
            yield {"text": "\n\n*Agent interrupted by user.*", "is_final": True}
            message_parts.append({"type": "text", "content": "*Interrupted*"})

        except Exception as e:

            import traceback
            traceback.print_exc()
            error_msg = f"Error ({type(e).__name__}): {str(e)}"
            yield {"error": error_msg, "is_final": True}
            message_parts.append({"type": "error", "content": error_msg})
            raise

        finally:
            # Clean up interrupted state
            if session_id in self.interrupted_sessions:
                self.interrupted_sessions.remove(session_id)

            # Save AI message
            if session_id and message_parts:
                try:
                    save_chat_message(
                        session_id,
                        "ai",
                        parts=message_parts,
                        images=images,
                        workspace_id=self.workspace_id
                    )

                    # Save session metadata for persistence
                    if chat:
                        save_chat_metadata(session_id, {
                            "cid": chat.cid,
                            "rid": chat.rid,
                            "rcid": chat.rcid
                        })

                except Exception as e:
                    print(f"[GeminiService] Failed to save message: {e}")

    async def run_delegated_task(self, task: str, context: str = "") -> str:
        """Run a delegated task in a temporary sub-agent session."""
        try:
            client = await self.get_client()
            model_name = self.config.get("model", "G_2_5_FLASH")
            model = getattr(Model, model_name, Model.G_2_5_FLASH)

            # Create temporary agent
            temp_agent = CodingAgent(self.workspace_path)
            chat = client.start_chat(model=model)

            prompt = f"""{temp_agent.get_system_prompt()}

## Delegated Task
Context from parent agent: {context}

Task: {task}

Execute this task autonomously and provide a complete summary of what you accomplished."""

            response = await asyncio.wait_for(
                chat.send_message(prompt),
                timeout=120
            )
            response_text = response.text or ""

            # Run sub-agent loop
            max_iterations = 8
            for _ in range(max_iterations):
                tool_call = temp_agent.parse_tool_call(response_text)
                if not tool_call:
                    break

                tool_result, _ = await temp_agent.execute_tool(
                    tool_call["name"],
                    tool_call["args"]
                )

                response = await asyncio.wait_for(
                    chat.send_message(tool_result),
                    timeout=120
                )
                response_text = response.text or ""

            return f"**Sub-agent Result:**\n{response_text}"

        except asyncio.TimeoutError:
            return "Error: Delegated task timed out"
        except Exception as e:
            return f"Error in delegated task: {str(e)}"

    async def reset(self):
        """Reset the service (clear all sessions and agents)."""
        self.client = None
        self.sessions = {}
        self.agents = {}
        self.interrupted_sessions.clear()
        self.active_tasks.clear()
