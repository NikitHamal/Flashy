"""
Design Service Module

This module provides the main service for the Flashy Design Agent.
It manages sessions, coordinates with Gemini API, and handles
the design generation loop with screenshot feedback.

Enhanced Features:
- Precise positioning with smart layout engine
- Response filtering for clean agentic behavior
- Canvas state synchronization
- Screenshot-based feedback loops
"""

import asyncio
import re
import base64
import tempfile
import os
from typing import Dict, Any, List, Optional, AsyncGenerator
from gemini_webapi import GeminiClient
from gemini_webapi.constants import Model

from .config import load_config
from .design_agent import DesignAgent
from .design_prompts import get_system_prompt, get_review_prompt, DESIGN_TOOL_RESULT_TEMPLATE
from .response_filter import ResponseFilter, ThoughtFilter


class DesignService:
    """
    Service for design agent interactions with Gemini.
    Handles session management, streaming responses, and
    canvas screenshot feedback loops.
    """

    def __init__(self):
        self.client = None
        self.config = load_config()
        self.sessions: Dict[str, Any] = {}  # Gemini chat sessions
        self.agents: Dict[str, DesignAgent] = {}  # Design agents per session
        self.interrupted_sessions: set = set()
        self.active_tasks: Dict[str, asyncio.Task] = {}

        # Initialize filters
        self.response_filter = ResponseFilter(aggressive=False)
        self.thought_filter = ThoughtFilter()

    async def get_client(self):
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

    def get_agent(
        self, session_id: str,
        canvas_width: int = 1200, canvas_height: int = 800
    ) -> DesignAgent:
        """Get or create a design agent for a session."""
        if session_id not in self.agents:
            self.agents[session_id] = DesignAgent(
                canvas_width=canvas_width,
                canvas_height=canvas_height
            )
            self.agents[session_id].session_id = session_id
        return self.agents[session_id]

    async def get_session(self, session_id: str):
        """Get or create a Gemini chat session."""
        client = await self.get_client()

        if session_id not in self.sessions:
            model_name = self.config.get("model", "G_2_5_FLASH")
            model = getattr(Model, model_name, Model.G_2_5_FLASH)
            chat = client.start_chat(model=model)
            self.sessions[session_id] = chat

        return self.sessions[session_id]

    def interrupt_session(self, session_id: str):
        """Interrupt a running design session."""
        self.interrupted_sessions.add(session_id)
        if session_id in self.active_tasks:
            task = self.active_tasks[session_id]
            if task and not task.done():
                task.cancel()
                print(f"[DesignService] Cancelled task for session {session_id}")

    def _is_interrupted(self, session_id: str) -> bool:
        """Check if session is interrupted."""
        return session_id in self.interrupted_sessions

    def _clean_response_text(self, text: str, tool_call_raw: str = None) -> str:
        """Clean response text by removing tool call JSON and unwanted content."""
        if not text:
            return ""

        cleaned = text

        if tool_call_raw:
            cleaned = cleaned.replace(tool_call_raw, "").strip()

        # Remove orphaned JSON blocks
        json_block_pattern = r'```json\s*\{[^`]*?"(?:action|tool|name)"\s*:[^`]*?\}\s*```'
        cleaned = re.sub(json_block_pattern, '', cleaned, flags=re.DOTALL).strip()

        # Apply response filter to remove YouTube links and tutorial text
        cleaned = self.response_filter.filter(cleaned)

        return cleaned

    def _separate_thinking(self, text: str) -> tuple:
        """Separate thinking from response text using enhanced filter."""
        if not text:
            return None, ""

        return self.thought_filter.extract_thoughts(text)

    async def _send_with_retry(
        self, chat, message, files=None,
        max_retries: int = 3, timeout: int = 120
    ):
        """Send message with retry logic."""
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
                print(f"[DesignService] Attempt {attempt + 1}/{max_retries}: {last_error}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
            except Exception as e:
                last_error = str(e)
                print(f"[DesignService] Attempt {attempt + 1}/{max_retries}: {last_error}")
                error_str = str(e).lower()
                if "invalid response" in error_str or "failed to generate" in error_str:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                raise

        raise Exception(f"Failed after {max_retries} attempts: {last_error}")

    def _build_object_context(self, agent: DesignAgent) -> str:
        """Build a context string describing current canvas objects for the AI."""
        state = agent.get_canvas_state()
        objects = state.get("objects", [])

        if not objects:
            return "Canvas is empty."

        context_lines = [f"Canvas has {len(objects)} objects:"]
        for obj in objects[:20]:  # Limit to prevent huge prompts
            obj_type = obj.get("type", "unknown")
            obj_id = obj.get("id", "?")
            x = obj.get("left", 0)
            y = obj.get("top", 0)
            width = obj.get("width", 0)
            height = obj.get("height", 0)

            if obj_type in ("i-text", "text", "textbox"):
                text_preview = (obj.get("text", "")[:30] + "...") if len(obj.get("text", "")) > 30 else obj.get("text", "")
                context_lines.append(f"  - Text '{text_preview}' (id: {obj_id}) at ({x}, {y})")
            elif obj_type == "circle":
                r = obj.get("radius", 0)
                context_lines.append(f"  - Circle (id: {obj_id}) at ({x}, {y}), radius={r}")
            else:
                context_lines.append(f"  - {obj_type.capitalize()} (id: {obj_id}) at ({x}, {y}), size {width}x{height}")

        return "\n".join(context_lines)

    async def generate_design(
        self,
        prompt: str,
        session_id: str,
        canvas_state: Optional[Dict[str, Any]] = None,
        screenshot_base64: Optional[str] = None,
        files: Optional[List[str]] = None,
        images: Optional[List[Dict[str, str]]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate design based on user prompt.
        Handles the agent loop with tool calls and canvas updates.

        Yields dictionaries with:
        - thought: AI thinking content
        - text: Response text
        - tool_call: Tool being called
        - tool_result: Tool execution result
        - canvas_state: Updated canvas state
        - canvas_action: Frontend action to execute
        - is_final: Whether this is the final response
        """
        client = await self.get_client()
        agent = self.get_agent(session_id)
        chat = await self.get_session(session_id)

        # Track parts for session history
        message_parts = []
        temp_files: List[str] = []

        try:
            # Clear previous interruption
            if session_id in self.interrupted_sessions:
                self.interrupted_sessions.remove(session_id)

            # Load canvas state if provided
            if canvas_state:
                agent.tools.load_state(canvas_state)

            # Get canvas dimensions
            state = agent.get_canvas_state()
            canvas_width = state.get("width", 1200)
            canvas_height = state.get("height", 800)
            object_count = len(state.get("objects", []))

            # Build full prompt with enhanced system context
            system_context = get_system_prompt(
                canvas_width=canvas_width,
                canvas_height=canvas_height,
                object_count=object_count
            )

            # Build object context
            object_context = self._build_object_context(agent)

            full_prompt = f"""{system_context}

## Current Objects on Canvas
{object_context}

## User Request
{prompt}

Execute the design now. Calculate precise positions and use tool calls."""

            # Handle screenshot feedback
            file_paths = files or []
            if screenshot_base64:
                screenshot_bytes = self._decode_data_url(screenshot_base64)
                if screenshot_bytes:
                    temp_dir = tempfile.mkdtemp(prefix="flashy_design_")
                    screenshot_path = os.path.join(temp_dir, "canvas_screenshot.png")
                    with open(screenshot_path, "wb") as f:
                        f.write(screenshot_bytes)
                    file_paths.append(screenshot_path)
                    temp_files.append(screenshot_path)
                    full_prompt += "\n\n[Screenshot of current canvas attached for visual reference]"

            # Handle uploaded reference images
            if images:
                for index, image in enumerate(images):
                    data_url = image.get("data")
                    if not data_url:
                        continue
                    image_bytes = self._decode_data_url(data_url)
                    if not image_bytes:
                        continue
                    temp_dir = tempfile.mkdtemp(prefix="flashy_design_upload_")
                    filename = image.get("name") or f"upload_{index}.png"
                    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
                    file_path = os.path.join(temp_dir, safe_name)
                    with open(file_path, "wb") as f:
                        f.write(image_bytes)
                    file_paths.append(file_path)
                    temp_files.append(file_path)
                if images:
                    full_prompt += "\n\n[Reference images attached for design inspiration]"

            # Send initial request
            response = await self._send_with_retry(
                chat, full_prompt,
                files=file_paths if file_paths else None
            )

            # Process agent loop
            max_iterations = 30  # Increased for complex designs
            iteration = 0

            while iteration < max_iterations:
                # Check for interruption
                if self._is_interrupted(session_id):
                    yield {
                        "text": "*Design interrupted.*",
                        "is_final": True,
                        "canvas_state": agent.get_canvas_state()
                    }
                    break

                response_text = response.text or ""

                # Extract thoughts using enhanced filter
                api_thoughts = getattr(response, 'thoughts', None) or ""
                embedded_thinking, clean_response = self._separate_thinking(response_text)

                all_thoughts = ""
                if api_thoughts:
                    all_thoughts = api_thoughts
                if embedded_thinking:
                    if all_thoughts:
                        all_thoughts += "\n\n" + embedded_thinking
                    else:
                        all_thoughts = embedded_thinking

                # Yield thoughts
                if all_thoughts:
                    yield {"thought": all_thoughts}
                    message_parts.append({"type": "thought", "content": all_thoughts})

                # Parse tool call
                tool_call = agent.parse_tool_call(clean_response)

                if not tool_call:
                    # No tool call - final response
                    final_text = self._clean_response_text(clean_response)
                    if final_text:
                        yield {
                            "text": final_text,
                            "is_final": True,
                            "canvas_state": agent.get_canvas_state()
                        }
                        message_parts.append({"type": "text", "content": final_text})
                    else:
                        yield {
                            "text": "",
                            "is_final": True,
                            "canvas_state": agent.get_canvas_state()
                        }
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
                    yield {
                        "text": "*Design interrupted.*",
                        "is_final": True,
                        "canvas_state": agent.get_canvas_state()
                    }
                    break

                # Execute tool
                try:
                    tool_result = await agent.execute_tool(
                        tool_call["name"],
                        tool_call["args"]
                    )

                    # Build canvas action for frontend
                    canvas_action = None
                    if not str(tool_result).lower().startswith("error"):
                        canvas_action = self._build_canvas_action(
                            tool_call["name"],
                            tool_call.get("args") or {},
                            tool_result
                        )

                    payload = {
                        "tool_result": tool_result,
                        "canvas_state": agent.get_canvas_state()
                    }
                    if canvas_action:
                        payload["canvas_action"] = canvas_action

                    yield payload
                    message_parts.append({"type": "tool_result", "content": tool_result})

                    # Check interruption before next API call
                    if self._is_interrupted(session_id):
                        yield {
                            "text": "*Design interrupted.*",
                            "is_final": True,
                            "canvas_state": agent.get_canvas_state()
                        }
                        break

                    # Build concise result for Gemini
                    result_prompt = DESIGN_TOOL_RESULT_TEMPLATE.format(
                        tool_name=tool_call["name"],
                        output=tool_result
                    )

                    # Feed result back to Gemini
                    response = await self._send_with_retry(chat, result_prompt)
                    iteration += 1

                except asyncio.CancelledError:
                    yield {
                        "text": "*Design interrupted.*",
                        "is_final": True,
                        "canvas_state": agent.get_canvas_state()
                    }
                    break
                except Exception as e:
                    error_msg = f"Error executing '{tool_call['name']}': {str(e)}"
                    yield {"tool_result": error_msg}
                    message_parts.append({"type": "tool_result", "content": error_msg})

                    if self._is_interrupted(session_id):
                        yield {
                            "text": "*Design interrupted.*",
                            "is_final": True,
                            "canvas_state": agent.get_canvas_state()
                        }
                        break

                    # Feed error back to Gemini
                    response = await self._send_with_retry(chat, error_msg)
                    iteration += 1

            # Check iteration limit
            if iteration >= max_iterations:
                yield {
                    "text": "*Design agent reached maximum iterations. Design may be incomplete.*",
                    "is_final": True,
                    "canvas_state": agent.get_canvas_state()
                }

        except asyncio.CancelledError:
            yield {
                "text": "*Design interrupted.*",
                "is_final": True,
                "canvas_state": agent.get_canvas_state()
            }
        except Exception as e:
            yield {
                "error": str(e),
                "is_final": True,
                "canvas_state": agent.get_canvas_state()
            }
        finally:
            # Clean up
            if session_id in self.interrupted_sessions:
                self.interrupted_sessions.remove(session_id)

            # Clean up temp files
            for path in temp_files:
                try:
                    os.unlink(path)
                    dir_path = os.path.dirname(path)
                    if dir_path and "flashy_design_" in dir_path:
                        os.rmdir(dir_path)
                except Exception:
                    pass

    async def send_screenshot_for_review(
        self,
        session_id: str,
        screenshot_base64: str,
        additional_feedback: str = ""
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Send canvas screenshot to AI for review and iteration.
        This allows the AI to see its work and make improvements.
        """
        agent = self.get_agent(session_id)
        state = agent.get_canvas_state()
        canvas_width = state.get("width", 1200)
        canvas_height = state.get("height", 800)
        object_count = len(state.get("objects", []))

        # Use the enhanced review prompt
        prompt = get_review_prompt(
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            object_count=object_count,
            feedback=additional_feedback
        )

        async for chunk in self.generate_design(
            prompt=prompt,
            session_id=session_id,
            screenshot_base64=screenshot_base64
        ):
            yield chunk

    def _decode_data_url(self, data_url: str) -> Optional[bytes]:
        """Decode base64 content from a data URL or raw base64."""
        if not data_url:
            return None
        try:
            if "," in data_url:
                data_url = data_url.split(",", 1)[1]
            return base64.b64decode(data_url)
        except Exception:
            return None

    def _extract_id_from_result(self, tool_result: str) -> Optional[str]:
        """Extract object IDs from tool results when possible."""
        if not tool_result:
            return None
        id_match = re.search(r"ID:\s*([a-zA-Z0-9_-]+)", tool_result)
        if id_match:
            return id_match.group(1)
        group_match = re.search(r"Created group '([^']+)'", tool_result)
        if group_match:
            return group_match.group(1)
        duplicate_match = re.search(r"Duplicated '[^']+' as '([^']+)'", tool_result)
        if duplicate_match:
            return duplicate_match.group(1)
        return None

    def _build_canvas_action(
        self, tool_name: str, args: Dict[str, Any], tool_result: str
    ) -> Optional[Dict[str, Any]]:
        """Build canvas action payload for frontend execution."""
        non_canvas_tools = {
            "list_objects",
            "get_object_properties",
            "get_canvas_state",
            "select_object"
        }
        if tool_name in non_canvas_tools:
            return None

        action_args = dict(args or {})
        new_id = self._extract_id_from_result(tool_result)

        if new_id and tool_name.startswith("add_") and "id" not in action_args:
            action_args["id"] = new_id
        if tool_name == "group_objects" and new_id:
            action_args["group_id"] = new_id
        if tool_name == "duplicate_object" and new_id:
            action_args["new_id"] = new_id

        return {
            "tool": tool_name,
            "args": action_args,
            "result": tool_result
        }

    def get_canvas_state(self, session_id: str) -> Dict[str, Any]:
        """Get current canvas state for a session."""
        agent = self.agents.get(session_id)
        if agent:
            return agent.get_canvas_state()
        return {"width": 1200, "height": 800, "background": "#FFFFFF", "objects": []}

    def set_canvas_state(self, session_id: str, state: Dict[str, Any]) -> str:
        """Set canvas state for a session."""
        agent = self.get_agent(session_id)
        return agent.set_canvas_state(state)

    def execute_local_tool(
        self, session_id: str,
        tool_name: str, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a design tool locally without AI involvement.
        Used for manual canvas operations from the frontend.
        """
        agent = self.get_agent(session_id)

        # Execute synchronously for local operations
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                agent.tools.execute(tool_name, **args)
            )
        finally:
            loop.close()

        return {
            "result": result,
            "canvas_state": agent.get_canvas_state()
        }

    async def reset(self):
        """Reset the service."""
        self.client = None
        self.sessions = {}
        self.agents = {}
