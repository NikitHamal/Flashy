"""
Gemini Service Module

This module provides the main service for Flashy Coding Agent interactions
with various LLM providers (Gemini, DeepInfra, Qwen).

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
from .storage import save_chat_message, async_save_chat_message, save_chat_metadata, get_chat_metadata
from .image_service import get_image_service, ImageResult, ImageType
from .providers import get_provider_service, BaseProvider


class LLMService:
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
        """Get or initialize Gemini client with explicit user cookies."""
        if not hasattr(self, "_init_lock"):
            self._init_lock = asyncio.Lock()

        async with self._init_lock:
            if self.gemini_client is None:
                # Force reload config to get latest user settings
                self.config = load_config()
                
                psid = self.config.get("Secure_1PSID", "").strip()
                psidts = self.config.get("Secure_1PSIDTS", "").strip()
                
                if not psid:
                    print("[LLMService] Warning: __Secure-1PSID is missing in config.")

                print(f"[LLMService] Initializing GeminiClient with explicit cookies (PSID: {psid[:10]}...)")
                
                # Create client with EXPLICIT cookies only
                self.gemini_client = GeminiClient(
                    psid,
                    psidts,
                    proxy=None
                )

                try:
                    await self.gemini_client.init(
                        timeout=30,
                        auto_close=False,
                        close_delay=300,
                        auto_refresh=False
                    )
                    print("[LLMService] Gemini client initialized successfully.")
                except Exception as e:
                    print(f"[LLMService] Failed to initialize client: {e}")
                    self.gemini_client = None # Reset so next call tries again
                    raise
                
            return self.gemini_client

    def get_agent(self, session_id: str) -> CodingAgent:
        """Get or create a coding agent for a session."""
        if session_id not in self.agents:
            self.agents[session_id] = CodingAgent(
                workspace_path=self.workspace_path,
                session_id=session_id
            )
            # Register in global registry for transparency/activity UI
            from .agents import agent_registry
            agent_registry.register_session(session_id, self.agents[session_id])
            
        return self.agents[session_id]

    async def get_gemini_chat_session(self, session_id: str, history: Any = None, fresh: bool = False):
        """Get or create a Gemini chat session object."""
        client = await self.get_gemini_client()

        if session_id not in self.sessions or fresh:
            model_name = self.config.get("model", "G_2_5_FLASH")
            model = self._resolve_gemini_model(model_name)

            # Try to restore from saved metadata if not forcing a fresh session
            saved_meta = get_chat_metadata(session_id) if not fresh else None
            if saved_meta:
                chat = client.start_chat(
                    model=model,
                    cid=saved_meta.get('cid'),
                    rid=saved_meta.get('rid'),
                    rcid=saved_meta.get('rcid')
                )
                print(f"[LLMService] Restored session {session_id}")
            else:
                chat = client.start_chat(model=model)
                if fresh:
                    print(f"[LLMService] Started fresh session for {session_id}")

            self.sessions[session_id] = chat

        return self.sessions[session_id]

    def interrupt_session(self, session_id: str):
        """Interrupt a running session."""
        self.interrupted_sessions.add(session_id)

        if session_id in self.active_tasks:
            task = self.active_tasks[session_id]
            if task and not task.done():
                task.cancel()
                print(f"[LLMService] Cancelled task for session {session_id}")

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

    def _default_gemini_model(self) -> Model:
        """Select a safe default Gemini model across gemini_webapi versions."""
        for attr in (
            "G_3_0_FLASH",
            "G_3_0_FLASH_THINKING",
            "G_3_1_PRO",
            "G_3_0_PRO",
            "G_2_5_FLASH",
            "G_2_5_PRO",
        ):
            if hasattr(Model, attr):
                return getattr(Model, attr)
        # Fall back to the first available model (or UNSPECIFIED if present)
        if hasattr(Model, "UNSPECIFIED"):
            return getattr(Model, "UNSPECIFIED")
        return next(iter(Model))

    def _resolve_gemini_model(self, model_name: Any) -> Model:
        """Resolve a configured model name to a gemini_webapi Model enum."""
        if isinstance(model_name, Model):
            return model_name

        # Allow custom model dicts when supported by the library
        if isinstance(model_name, dict):
            if hasattr(Model, "from_dict"):
                try:
                    return Model.from_dict(model_name)
                except Exception:
                    pass
            return self._default_gemini_model()

        if not model_name:
            return self._default_gemini_model()

        if isinstance(model_name, str):
            # Direct enum lookup (e.g., "G_3_0_FLASH")
            if hasattr(Model, model_name):
                return getattr(Model, model_name)

            # Legacy enum aliases
            legacy_enum_aliases = {
                "G_2_5_FLASH": ["G_3_0_FLASH", "G_3_0_FLASH_THINKING", "G_2_5_FLASH"],
                "G_2_0_FLASH": ["G_3_0_FLASH", "G_3_0_FLASH_THINKING", "G_2_0_FLASH"],
                "G_2_5_PRO": ["G_3_1_PRO", "G_3_0_PRO", "G_2_5_PRO"],
                "G_2_0_PRO": ["G_3_1_PRO", "G_3_0_PRO", "G_2_0_PRO"],
            }
            if model_name in legacy_enum_aliases:
                for attr in legacy_enum_aliases[model_name]:
                    if hasattr(Model, attr):
                        return getattr(Model, attr)

            # Legacy model name strings
            legacy_name_aliases = {
                "gemini-2.5-flash": "gemini-3.0-flash",
                "gemini-2.5-pro": "gemini-3.0-pro",
                "gemini-1.5-flash": "gemini-3.0-flash",
                "gemini-1.5-pro": "gemini-3.0-pro",
            }
            candidate_names = [model_name]
            if model_name in legacy_name_aliases:
                candidate_names.insert(0, legacy_name_aliases[model_name])

            if hasattr(Model, "from_name"):
                for name in candidate_names:
                    try:
                        return Model.from_name(name)
                    except Exception:
                        continue

        return self._default_gemini_model()

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
        timeout: int = 120,
        provider: str = "gemini",
        session_id: str = None
    ):
        """Send message to Gemini with retry logic and timeout."""
        last_error = None

        if provider != "gemini":
            raise RuntimeError("_send_with_retry is Gemini-only; use generate_stream for other providers")

        current_chat = chat

        for attempt in range(max_retries):
            try:
                if files:
                    response = await asyncio.wait_for(
                        current_chat.send_message(message, files=files),
                        timeout=timeout
                    )
                else:
                    response = await asyncio.wait_for(
                        current_chat.send_message(message),
                        timeout=timeout
                    )

                if session_id and current_chat != chat:
                    self.sessions[session_id] = current_chat

                return response

            except asyncio.CancelledError:
                raise

            except asyncio.TimeoutError:
                last_error = f"Request timed out after {timeout}s"
                print(f"[LLMService] Attempt {attempt + 1}/{max_retries}: {last_error}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

            except Exception as e:
                last_error = str(e)
                error_str = str(e).lower()
                print(f"[LLMService] Attempt {attempt + 1}/{max_retries} Failed: {error_str}")

                if "invalid response" in error_str or "failed to generate" in error_str:
                    if session_id and attempt < max_retries - 1:
                        print(f"[LLMService] Detected dead session {session_id}. Recovering with fresh chat...")
                        try:
                            current_chat = await self.get_gemini_chat_session(session_id, fresh=True)
                            self.sessions[session_id] = current_chat
                            if len(message) > 50:
                                message = f"[System: Connection lost. Resuming task.]\n\n{message}"
                        except Exception as rec_e:
                            print(f"[LLMService] Recovery failed: {rec_e}")

                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
                        continue

                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
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
        Generate response from configured provider with full multi-turn agent loop.

        Works uniformly for ALL providers (Gemini, Qwen, DeepInfra).
        Each iteration: generate -> parse tool call -> execute -> feed result back.
        """
        provider_name = self.get_active_provider()
        agent = self.get_agent(session_id) if session_id else None

        message_parts: List[Dict[str, Any]] = []
        images: List[str] = []

        try:
            if session_id in self.interrupted_sessions:
                self.interrupted_sessions.remove(session_id)

            if agent:
                agent.reset_context()

            # Build prompt
            if agent and self.workspace_path:
                system_context = agent.get_system_prompt()
                full_prompt = f"{system_context}\n\n## User Request\n{text}\n\nExecute this task using the appropriate tools."

                if files and provider_name != 'gemini':
                    full_prompt += "\n\nAttached Files Content:\n"
                    for fpath in files:
                        try:
                            import chardet
                            with open(fpath, 'rb') as f:
                                raw = f.read(20000)
                                enc = chardet.detect(raw)['encoding'] or 'utf-8'
                                full_prompt += f"\n--- {fpath} ---\n{raw.decode(enc, errors='ignore')}\n"
                        except Exception as e:
                            full_prompt += f"\n--- {fpath} ---\n[Error reading file: {e}]\n"
            else:
                full_prompt = text

            # Provider setup
            chat_session = None
            if provider_name == 'gemini':
                chat_session = await self.get_gemini_chat_session(session_id, history=history)
            else:
                if session_id not in self.provider_sessions:
                    self.provider_sessions[session_id] = []
                self.provider_sessions[session_id].append({'role': 'user', 'content': full_prompt})

            # --- Agent Loop with multi-turn tool execution ---
            if agent and self.workspace_path:
                max_iterations = 20
                iteration = 0
                current_prompt = full_prompt

                while iteration < max_iterations:
                    if self._is_interrupted(session_id):
                        yield {'text': '\n\n*Agent interrupted by user.*', 'is_final': True}
                        break

                    if not agent.increment_iteration():
                        yield {'text': '\n\n*Agent reached maximum iterations. Task may be incomplete.*', 'is_final': True}
                        break

                    from .agents import agent_registry
                    agent_registry.update_session(session_id)

                    # Generation
                    response_text = ''
                    api_thoughts = ''

                    if provider_name == 'gemini':
                        gemini_resp = await self._send_with_retry(
                            chat_session, current_prompt,
                            files=files if iteration == 0 else None,
                            session_id=session_id
                        )
                        response_text = gemini_resp.text or ''
                        api_thoughts = getattr(gemini_resp, 'thoughts', None) or ''

                        if hasattr(gemini_resp, 'images') and gemini_resp.images:
                            for img in gemini_resp.images:
                                img_url = getattr(img, 'url', '')
                                if img_url and img_url not in images:
                                    images.append(img_url)
                                    img_type = 'generated' if 'generated' in type(img).__name__.lower() else 'web'
                                    image_service = get_image_service(self.workspace_path)
                                    image_service.generated_images.append(ImageResult(
                                        url=img_url,
                                        image_type=ImageType.GENERATED if img_type == 'generated' else ImageType.WEB,
                                        title=getattr(img, 'title', None),
                                        alt=getattr(img, 'alt', None)
                                    ))
                    else:
                        provider_svc = get_provider_service(provider_name)
                        if not provider_svc:
                            yield {'error': f"Provider '{provider_name}' not found.", 'is_final': True}
                            return

                        if iteration > 0:
                            self.provider_sessions[session_id].append({'role': 'user', 'content': current_prompt})

                        accumulated_text = ''
                        accumulated_thought = ''
                        in_think_block = False

                        async for chunk in provider_svc.generate_stream(
                            self.provider_sessions[session_id],
                            self.config.get('model', ''),
                            proxy=self.config.get('proxy')
                        ):
                            if 'error' in chunk:
                                yield {'error': chunk['error']}
                                message_parts.append({'type': 'error', 'content': chunk['error']})
                                continue
                            if 'thought' in chunk:
                                accumulated_thought += chunk['thought']
                                yield {'thought': chunk['thought']}
                            if 'text' in chunk:
                                t = chunk['text']
                                accumulated_text += t
                                if '<think>' in t:
                                    in_think_block = True
                                    parts = t.split('<think>', 1)
                                    if parts[0]: yield {'text': parts[0]}
                                    if parts[1]:
                                        accumulated_thought += parts[1]
                                        yield {'thought': parts[1]}
                                    continue
                                if '</think>' in t:
                                    in_think_block = False
                                    parts = t.split('</think>', 1)
                                    if parts[0]:
                                        accumulated_thought += parts[0]
                                        yield {'thought': parts[0]}
                                    if parts[1]: yield {'text': parts[1]}
                                    continue
                                if in_think_block:
                                    accumulated_thought += t
                                    yield {'thought': t}
                                else:
                                    yield {'text': t}

                        response_text = accumulated_text
                        api_thoughts = accumulated_thought
                        self.provider_sessions[session_id].append({'role': 'assistant', 'content': response_text})

                    # Process response
                    # For non-Gemini providers, thinking was already streamed live in the provider loop above.
                    # We skip re-extraction and re-yielding to avoid duplication.
                    if provider_name == 'gemini':
                        embedded_thinking, clean_response = self._separate_thinking(response_text)
                        all_thoughts = api_thoughts
                        if embedded_thinking:
                            all_thoughts = f'{all_thoughts}\n\n{embedded_thinking}'.strip() if all_thoughts else embedded_thinking
                        if all_thoughts:
                            yield {'thought': all_thoughts}
                            message_parts.append({'type': 'thought', 'content': all_thoughts})
                    else:
                        # Thinking already streamed live — just track it for message saving
                        clean_response = response_text
                        if api_thoughts:
                            message_parts.append({'type': 'thought', 'content': api_thoughts})

                    tool_call = agent.parse_tool_call(clean_response)

                    if not tool_call:
                        # Final response
                        if provider_name == 'gemini':
                            final_text = self._clean_response_text(clean_response)
                            if final_text:
                                yield {'text': final_text, 'images': images, 'is_final': True}
                                message_parts.append({'type': 'text', 'content': final_text})
                            elif images:
                                yield {'text': '', 'images': images, 'is_final': True}
                            else:
                                yield {'text': '[Agent completed]', 'is_final': True}
                        else:
                            message_parts.append({'type': 'text', 'content': clean_response})
                            yield {'images': images, 'is_final': True}
                        break

                    # Text before tool call
                    if provider_name == 'gemini':
                        display_text = self._clean_response_text(clean_response, tool_call.get('raw_match'))
                        if display_text:
                            yield {'text': display_text + '\n'}
                            message_parts.append({'type': 'text', 'content': display_text})
                    else:
                        if clean_response.strip():
                            message_parts.append({'type': 'text', 'content': clean_response})

                    yield {'tool_call': {'name': tool_call['name'], 'args': tool_call['args']}}
                    message_parts.append({
                        'type': 'tool_call',
                        'content': {'name': tool_call['name'], 'args': tool_call['args']}
                    })

                    if self._is_interrupted(session_id):
                        yield {'text': '\n\n*Agent interrupted by user.*', 'is_final': True}
                        break

                    # Execute tool
                    try:
                        if tool_call['name'] == 'delegate_task':
                            tool_result = await self.run_delegated_task(
                                tool_call['args'].get('task', ''),
                                tool_call['args'].get('context', '')
                            )
                        elif tool_call['name'] == 'generate_image':
                            tool_result = await self._handle_image_generation(
                                tool_call['args'], provider_name, chat_session, session_id
                            )
                            img_svc = get_image_service(self.workspace_path)
                            for img_obj in img_svc.generated_images:
                                if img_obj.url and img_obj.url not in images:
                                    images.append(img_obj.url)
                                    yield {'images': [img_obj.url]}
                        else:
                            tool_result, _ = await agent.execute_tool(
                                tool_call['name'], tool_call['args']
                            )

                        yield {'tool_result': tool_result}
                        message_parts.append({'type': 'tool_result', 'content': tool_result})

                        if self._is_interrupted(session_id):
                            yield {'text': '\n\n*Agent interrupted by user.*', 'is_final': True}
                            break

                        current_prompt = tool_result
                        iteration += 1

                    except asyncio.CancelledError:
                        yield {'text': '\n\n*Agent interrupted by user.*', 'is_final': True}
                        break
                    except Exception as e:
                        error_msg = f"Error executing '{tool_call['name']}': {str(e)}"
                        yield {'tool_result': error_msg}
                        message_parts.append({'type': 'tool_result', 'content': error_msg})
                        current_prompt = error_msg
                        iteration += 1

                if iteration >= max_iterations and not self._is_interrupted(session_id):
                    yield {'text': '\n\n*Agent reached maximum iterations.*', 'is_final': True}

            else:
                # Simple response (no workspace/agent)
                async for chunk in self._generate_simple_response(
                    full_prompt, provider_name, chat_session, files,
                    session_id, message_parts, images, history
                ):
                    yield chunk

        except asyncio.CancelledError:
            yield {'text': '\n\n*Interrupted.*', 'is_final': True}
            message_parts.append({'type': 'text', 'content': '*Interrupted*'})

        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = f'Error ({type(e).__name__}): {str(e)}'
            error_str = str(e).lower()
            if 'invalid response' in error_str or '403' in error_str or 'failed to generate' in error_str:
                error_msg += '\n\n**Hint:** Your Gemini cookies (Secure-1PSID) might be invalid or expired.'
            yield {'error': error_msg, 'is_final': True}
            message_parts.append({'type': 'error', 'content': error_msg})
            return

        finally:
            if session_id in self.interrupted_sessions:
                self.interrupted_sessions.remove(session_id)
            if session_id and message_parts:
                try:
                    await async_save_chat_message(
                        session_id, 'ai', parts=message_parts,
                        images=images, workspace_id=self.workspace_id
                    )
                except Exception as e:
                    print(f'[LLMService] Failed to save message: {e}')

    async def _generate_simple_response(
        self, full_prompt: str, provider_name: str, chat_session,
        files, session_id, message_parts: list, images: list, history
    ):
        """Generate a response without the agent loop (no workspace set)."""
        if provider_name == 'gemini':
            gemini_resp = await self._send_with_retry(chat_session, full_prompt, files=files, session_id=session_id)
            response_text = gemini_resp.text or ''
            api_thoughts = getattr(gemini_resp, 'thoughts', None) or ''
            embedded_thinking, clean_text = self._separate_thinking(response_text)
            clean_text = self.response_filter.filter(clean_text)

            all_thoughts = api_thoughts
            if embedded_thinking:
                all_thoughts = f'{all_thoughts}\n\n{embedded_thinking}'.strip() if all_thoughts else embedded_thinking
            if all_thoughts:
                yield {'thought': all_thoughts}
                message_parts.append({'type': 'thought', 'content': all_thoughts})

            if hasattr(gemini_resp, 'images') and gemini_resp.images:
                for img in gemini_resp.images:
                    img_url = getattr(img, 'url', '')
                    if img_url:
                        images.append(img_url)

            yield {'text': clean_text, 'images': images, 'is_final': True}
            message_parts.append({'type': 'text', 'content': clean_text})
        else:
            provider_svc = get_provider_service(provider_name)
            if not provider_svc:
                yield {'error': f"Provider '{provider_name}' not found.", 'is_final': True}
                return

            messages = [{'role': 'user', 'content': full_prompt}]
            accumulated_text = ''
            accumulated_thought = ''

            async for chunk in provider_svc.generate_stream(
                messages, self.config.get('model', ''),
                proxy=self.config.get('proxy')
            ):
                if 'error' in chunk:
                    yield {'error': chunk['error']}
                if 'thought' in chunk:
                    accumulated_thought += chunk['thought']
                    yield {'thought': chunk['thought']}
                if 'text' in chunk:
                    accumulated_text += chunk['text']
                    yield {'text': chunk['text']}

            if accumulated_thought:
                message_parts.append({'type': 'thought', 'content': accumulated_thought})
            message_parts.append({'type': 'text', 'content': accumulated_text})
            yield {'images': images, 'is_final': True}

    async def _handle_image_generation(
        self, args: dict, provider_name: str, chat_session, session_id: str
    ) -> str:
        """Handle image generation tool call."""
        prompt = args.get('prompt', '')
        save_to_project = args.get('save_to_project', False)
        filename = args.get('filename')

        if provider_name != 'gemini':
            return 'Image generation only supported on Gemini provider.'

        image_prompt = f'Generate an image: {prompt}. Use your image generation capabilities.'
        try:
            image_response = await self._send_with_retry(chat_session, image_prompt, session_id=session_id)
        except Exception as e:
            return f'Image generation failed: {str(e)}'

        if not hasattr(image_response, 'images') or not image_response.images:
            return 'Image generation requested but no images returned.'

        results = []
        for img in image_response.images:
            img_url = getattr(img, 'url', '')
            if not img_url:
                continue

            img_type = 'generated' if 'generated' in type(img).__name__.lower() else 'web'
            img_svc = get_image_service(self.workspace_path)
            img_result = ImageResult(
                url=img_url,
                image_type=ImageType.GENERATED if img_type == 'generated' else ImageType.WEB,
                title=getattr(img, 'title', None),
                alt=getattr(img, 'alt', None)
            )
            img_svc.generated_images.append(img_result)

            if save_to_project and self.workspace_path:
                success, save_path = await img_svc.save_image_from_url(img_url, filename)
                if success:
                    img_result.local_path = save_path
                    img_result.saved = True
                    results.append(f'Image generated and saved to: {save_path}')
                else:
                    results.append(f'Image generated but failed to save: {save_path}')
            else:
                results.append(f'Image generated: {img_url[:60]}...')

        return '\n'.join(results) if results else 'Image generation completed with no results.'


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
                model = self._resolve_gemini_model(model_name)
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
