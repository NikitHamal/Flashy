"""
Gemini Service Module

This module provides the main service for Flashy Coding Agent interactions
with various LLM providers (Gemini, DeepInfra, Qwen, Gradient).

Enhanced Features:
- Multi-provider support
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
from .image_service import get_image_service, ImageResult, ImageType
from .providers import get_provider_service, BaseProvider


class GeminiService:
    """
    Production-grade service for Multi-Provider powered coding agent.

    Handles:
    - Client initialization and session management
    - Agent loop with tool execution
    - Response streaming with thought separation
    - Interruption and cancellation support
    - Persistent session storage
    """

    def __init__(self):
        self.gemini_client: Optional[GeminiClient] = None
        self.config = load_config()
        self.sessions: Dict[str, Any] = {} # For Gemini chat objects mainly
        self.provider_sessions: Dict[str, List[Dict[str,str]]] = {} # For other providers history
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

    def get_active_provider(self) -> str:
        """Get the currently configured active provider."""
        self.config = load_config() # Reload config
        return self.config.get("active_provider", "gemini")

    async def get_gemini_client(self) -> GeminiClient:
        """Get or initialize Gemini client."""
        if self.gemini_client is None:
            self.config = load_config()

            self.gemini_client = GeminiClient(
                self.config["Secure_1PSID"],
                self.config["Secure_1PSIDTS"],
                proxy=None
            )

            # Inject additional cookies if present
            if self.config.get("Secure_1PSIDCC"):
                self.gemini_client.cookies["__Secure-1PSIDCC"] = self.config["Secure_1PSIDCC"]

            await self.gemini_client.init(
                timeout=600,
                auto_close=False,
                close_delay=300,
                auto_refresh=True
            )

        return self.gemini_client

    def get_agent(self, session_id: str) -> CodingAgent:
        """Get or create a coding agent for a session."""
        if session_id not in self.agents:
            self.agents[session_id] = CodingAgent(
                workspace_path=self.workspace_path,
                session_id=session_id
            )
        return self.agents[session_id]

    async def get_gemini_chat_session(self, session_id: str, history: Any = None):
        """Get or create a Gemini chat session object."""
        client = await self.get_gemini_client()

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
        chat, # Can be Gemini Chat or Provider Instance
        message: str,
        files: List[str] = None,
        max_retries: int = 3,
        timeout: int = 120,
        provider: str = "gemini",
        session_id: str = None
    ):
        """Send message with retry logic and timeout."""
        last_error = None

        if provider == "gemini":
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
        
        else:
             # Logic for other providers (they stream, so we accumulate info)
            return None # Providers use generate_stream, this method is legacy for Gemini structure

    async def generate_response(
        self,
        text: str,
        session_id: str = None,
        files: List[str] = None,
        history: Any = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate response from configured provider with full agent loop.
        """
        provider_name = self.get_active_provider()
        agent = self.get_agent(session_id) if session_id else None
        
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
                
                # Append file content if provided (for providers that don't support file upload API)
                if files and provider_name != "gemini":
                    # For non-Gemini providers, read file content and append to prompt
                    # This is a simplification; optimal way is to use context management tool
                    # But for "UploadFile", we usually want them in context immediately.
                    full_prompt += "\n\nAttached Files Content:\n"
                    for fpath in files:
                        try:
                            import chardet
                            with open(fpath, "rb") as f:
                                b_content = f.read(20000) # Limit size
                                encoding = chardet.detect(b_content)['encoding'] or 'utf-8'
                                decoded = b_content.decode(encoding, errors='ignore')
                                full_prompt += f"\n--- {fpath} ---\n{decoded}\n"
                        except Exception as e:
                            full_prompt += f"\n--- {fpath} ---\n[Error reading file: {e}]\n"
            else:
                 full_prompt = text

            # --- Provider specific setup ---
            chat_session = None
            response_generator = None
            
            if provider_name == "gemini":
                chat_session = await self.get_gemini_chat_session(session_id, history=history)
            else:
                # Load provider history
                if session_id not in self.provider_sessions:
                    self.provider_sessions[session_id] = []
                # Append user message to history
                self.provider_sessions[session_id].append({"role": "user", "content": full_prompt})
            
            # --- Agent Loop ---
            if agent and self.workspace_path:
                max_iterations = 20
                iteration = 0

                current_prompt = full_prompt
                
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
                    
                    # --- Generation Step ---
                    response_text = ""
                    api_thoughts = ""
                    
                    if provider_name == "gemini":
                        if iteration == 0:
                            # Initial user request
                             gemini_resp = await self._send_with_retry(chat_session, current_prompt, files=files if iteration == 0 else None)
                        else:
                            # Feedback loop
                             gemini_resp = await self._send_with_retry(chat_session, current_prompt)
                        
                        response_text = gemini_resp.text or ""
                        api_thoughts = getattr(gemini_resp, 'thoughts', None) or ""
                        
                        # Yield any images found in gemini response
                        if hasattr(gemini_resp, 'images') and gemini_resp.images:
                             for img in gemini_resp.images:
                                img_url = getattr(img, 'url', '')
                                if img_url and img_url not in images:
                                    images.append(img_url)
                                    # Track
                                    img_type = "generated" if "generated" in type(img).__name__.lower() else "web"
                                    image_service = get_image_service(self.workspace_path)
                                    image_service.generated_images.append(ImageResult(
                                            url=img_url,
                                            image_type=ImageType.GENERATED if img_type == "generated" else ImageType.WEB,
                                            title=getattr(img, 'title', None),
                                            alt=getattr(img, 'alt', None)
                                     ))
                    else:
                        # --- Other Providers ---
                        provider_service_inst = get_provider_service(provider_name)
                        if not provider_service_inst:
                            yield {"error": f"Provider '{provider_name}' implementation not found.", "is_final": True}
                            return
                            
                        # Prepare kwargs
                        kwargs = {
                            "proxy": self.config.get("proxy")
                        }
                        
                        # Generate
                        # Note: provider_sessions already has the history up to the last user prompt
                        # If this is iteration > 0, we need to append the tool result as a user message
                        if iteration > 0:
                             self.provider_sessions[session_id].append({"role": "user", "content": current_prompt})
                             
                        accumulated_text = ""
                        accumulated_thought = ""
                        
                        async for chunk in provider_service_inst.generate_stream(
                            self.provider_sessions[session_id], 
                            self.config.get("model", ""), 
                            **kwargs
                        ):
                             if "error" in chunk:
                                 yield {"error": chunk["error"]}
                                 message_parts.append({"type": "error", "content": chunk["error"]})
                             
                             if "thought" in chunk:
                                 accumulated_thought += chunk["thought"]
                                 yield {"thought": chunk["thought"]}
                                 # We'll merge these later or track them
                                 
                             if "text" in chunk:
                                 accumulated_text += chunk["text"]
                                 yield {"text": chunk["text"]} # Stream raw text
                                 
                        response_text = accumulated_text
                        api_thoughts = accumulated_thought
                        
                        # Append assistant response to history
                        self.provider_sessions[session_id].append({"role": "assistant", "content": response_text})
                    
                    # --- Processing Response ---
                    embedded_thinking, clean_response = self._separate_thinking(response_text)
                    
                    # Combine thoughts
                    all_thoughts = ""
                    if api_thoughts:
                         all_thoughts = api_thoughts
                    if embedded_thinking:
                        all_thoughts = f"{all_thoughts}\n\n{embedded_thinking}".strip() if all_thoughts else embedded_thinking
                    
                    if all_thoughts:
                        if provider_name == "gemini":
                            yield {"thought": all_thoughts}
                        message_parts.append({"type": "thought", "content": all_thoughts})
                    
                    # Parse tool call from clean response
                    tool_call = agent.parse_tool_call(clean_response)
                    
                    if not tool_call:
                        # No tool call - final response
                        if provider_name == "gemini":
                             # Gemini yields text after complete generation, others yielded during stream
                             final_text = self._clean_response_text(clean_response)
                             if final_text:
                                yield {"text": final_text, "images": images, "is_final": True}
                                message_parts.append({"type": "text", "content": final_text})
                             elif images:
                                 yield {"text": "", "images": images, "is_final": True}
                             else:
                                 yield {"text": "[Agent completed]", "is_final": True}
                        else:
                             # For streaming providers, we assume text was already yielded. 
                             # We just send is_final. But we should save the full text
                             message_parts.append({"type": "text", "content": clean_response})
                             yield {"images": images, "is_final": True}
                        break
                    
                    # Handle text before tool call (For Gemini mostly)
                    if provider_name == "gemini":
                        display_text = self._clean_response_text(
                            clean_response,
                            tool_call.get("raw_match")
                        )
                        if display_text:
                            yield {"text": display_text + "\n"}
                            message_parts.append({"type": "text", "content": display_text})
                    else:
                        if clean_response:
                            message_parts.append({"type": "text", "content": clean_response})
                    
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
                        elif tool_call["name"] == "generate_image":
                             # Special handling for image generation
                            prompt = tool_call["args"].get("prompt", "")
                            save_to_project = tool_call["args"].get("save_to_project", False)
                            filename = tool_call["args"].get("filename")
                            
                            if provider_name == "gemini":
                                # Send a direct image generation request to Gemini
                                image_prompt = f"Generate an image: {prompt}. Use your image generation capabilities to create this image now."
                                image_response = await self._send_with_retry(chat_session, image_prompt)
                                
                                # Check if images were generated
                                if hasattr(image_response, 'images') and image_response.images:
                                    generated_urls = []
                                    for img in image_response.images:
                                        img_url = getattr(img, 'url', '')
                                        if img_url:
                                            generated_urls.append(img_url)
                                            images.append(img_url)
                                            # Track
                                            img_type = "generated" if "generated" in type(img).__name__.lower() else "web"
                                            image_service = get_image_service(self.workspace_path)
                                            image_service.generated_images.append(ImageResult(
                                                url=img_url,
                                                image_type=ImageType.GENERATED if img_type == "generated" else ImageType.WEB,
                                                title=getattr(img, 'title', None),
                                                alt=getattr(img, 'alt', None)
                                            ))
                                            
                                            # Save to project if requested
                                            if save_to_project and self.workspace_path:
                                                success, save_path = await image_service.save_image_from_url(
                                                    img_url, filename
                                                )
                                                if success:
                                                    tool_result = f"Image generated and saved to: {save_path}"
                                                else:
                                                    tool_result = f"Image generated but failed to save: {save_path}"
                                            else:
                                                tool_result = f"Image generated successfully. URL: {img_url[:50]}..."
                                    
                                    # Yield generated images
                                    yield {"images": generated_urls}
                                    tool_status = ToolCallStatus.SUCCESS
                                    
                                    # Use image response as next response (skip iteration increment step logic? No, just replace response)
                                    # For loop logic, we just continue
                                else:
                                    tool_result = "Image generation requested but no images were returned. This may be due to content policy or availability restrictions."
                                    tool_status = ToolCallStatus.ERROR
                            else:
                                tool_result = "Image generation only supported on Gemini provider currently."
                                tool_status = ToolCallStatus.ERROR
                        
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
                        
                        # Prepare prompt for next iteration
                        current_prompt = tool_result
                        iteration += 1
                        
                    except asyncio.CancelledError:
                        yield {"text": "\n\n*Agent interrupted by user.*", "is_final": True}
                        break
                    except Exception as e:
                        error_msg = f"Error executing '{tool_call['name']}': {str(e)}"
                        yield {"tool_result": error_msg}
                        message_parts.append({"type": "tool_result", "content": error_msg})
                        
                        current_prompt = error_msg
                        iteration += 1
                
                 # Check iteration limit
                if iteration >= max_iterations:
                    yield {
                        "text": "\n\n*Agent reached maximum iterations. Task may be incomplete.*",
                        "is_final": True
                    }

            else:
                 # Simple response (no workspace/agent)
                 # provider specific
                 if provider_name == "gemini":
                     gemini_resp = await self._send_with_retry(chat_session, full_prompt, files=files)
                     response_text = gemini_resp.text or ""
                     api_thoughts = getattr(gemini_resp, 'thoughts', None) or ""
                     
                     embedded_thinking, clean_text = self._separate_thinking(response_text)
                     clean_text = self.response_filter.filter(clean_text)
                     
                     all_thoughts = api_thoughts
                     if embedded_thinking:
                         all_thoughts = f"{all_thoughts}\n\n{embedded_thinking}".strip() if all_thoughts else embedded_thinking
                         
                     if all_thoughts:
                         yield {"thought": all_thoughts}
                         message_parts.append({"type": "thought", "content": all_thoughts})
                     
                     # Check images
                     if hasattr(gemini_resp, 'images') and gemini_resp.images:
                         for img in gemini_resp.images:
                            img_url = getattr(img, 'url', '')
                            if img_url:
                                images.append(img_url)
                     
                     yield {"text": clean_text, "images": images, "is_final": True}
                     message_parts.append({"type": "text", "content": clean_text})
                 else:
                    provider_service_inst = get_provider_service(provider_name)
                    if not provider_service_inst:
                         yield {"error": f"Provider '{provider_name}' implementation not found.", "is_final": True}
                         return
                    
                    # Prepare message list
                    messages = [{"role": "user", "content": full_prompt}]
                    
                    # Prepare kwargs
                    kwargs = {
                        "proxy": self.config.get("proxy")
                    }

                    accumulated_text = ""
                    accumulated_thought = ""
                    async for chunk in provider_service_inst.generate_stream(messages, self.config.get("model", ""), **kwargs):
                        if "error" in chunk:
                            yield {"error": chunk["error"]}
                        if "thought" in chunk:
                            accumulated_thought += chunk["thought"]
                            yield {"thought": chunk["thought"]}
                        if "text" in chunk:
                            accumulated_text += chunk["text"]
                            yield {"text": chunk["text"]}
                    
                    if accumulated_thought:
                        message_parts.append({"type": "thought", "content": accumulated_thought})
                    message_parts.append({"type": "text", "content": accumulated_text})
                    yield {"images": images, "is_final": True}

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
                    
                    # Save session metadata for persistence is tricky with multi-provider
                    # But we can save whatever we have

                except Exception as e:
                    print(f"[GeminiService] Failed to save message: {e}")

    async def run_delegated_task(self, task: str, context: str = "") -> str:
        """Run a delegated task in a temporary sub-agent session."""
        try:
             # Basic implementation - use same provider
            provider_name = self.get_active_provider()
            temp_agent = CodingAgent(self.workspace_path)
            
            prompt = f"""{temp_agent.get_system_prompt()}

## Delegated Task
Context from parent agent: {context}

Task: {task}

Execute this task autonomously and provide a complete summary of what you accomplished."""

            response_text = ""
            
            if provider_name == "gemini":
                client = await self.get_gemini_client()
                model_name = self.config.get("model", "G_2_5_FLASH")
                model = getattr(Model, model_name, Model.G_2_5_FLASH)
                chat = client.start_chat(model=model)
                response = await asyncio.wait_for(chat.send_message(prompt), timeout=120)
                response_text = response.text or ""
            else:
                 # Minimal support for others in delegation
                return "Delegation currently optimized for Gemini provider."

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
                
                if provider_name == "gemini":
                    response = await asyncio.wait_for(chat.send_message(tool_result), timeout=120)
                    response_text = response.text or ""
                else:
                    break

            return f"**Sub-agent Result:**\n{response_text}"

        except asyncio.TimeoutError:
            return "Error: Delegated task timed out"
        except Exception as e:
            return f"Error in delegated task: {str(e)}"

    async def reset(self):
        """Reset the service (clear all sessions and agents)."""
        self.gemini_client = None
        self.sessions = {}
        self.provider_sessions = {}
        self.agents = {}
        self.interrupted_sessions.clear()
        self.active_tasks.clear()
