import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator

from ..config import load_config
from ..coding_agent import CodingAgent
from ..response_filter import ResponseFilter, ThoughtFilter
from ..storage import async_save_chat_message
from ..image_service import get_image_service, ImageResult, ImageType
from ..providers import get_provider_service
from .gemini import get_gemini_chat_session, get_gemini_client, send_with_retry
from .helpers import clean_response_text, separate_thinking
from .support import generate_simple_response, handle_image_generation, run_delegated_task


class LLMService:
    def __init__(self):
        self.gemini_client = None
        self.config = load_config()
        self.sessions: Dict[str, Any] = {}
        self.provider_sessions: Dict[str, List[Dict[str, str]]] = {}
        self.qwen_conversations: Dict[str, Any] = {}
        self.agents: Dict[str, CodingAgent] = {}
        self.interrupted_sessions: set = set()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.workspace_path: Optional[str] = None
        self.workspace_id: Optional[str] = None
        self.response_filter = ResponseFilter(aggressive=False)
        self.thought_filter = ThoughtFilter()

    def set_workspace(self, path: str, workspace_id: str = None) -> str:
        import os

        if os.path.isdir(path):
            self.workspace_path = os.path.abspath(path)
            self.workspace_id = workspace_id
            for agent in self.agents.values():
                agent.set_workspace(self.workspace_path)
            return f"Workspace set to: {self.workspace_path}"
        return f"Error: '{path}' is not a valid directory."

    def get_workspace(self) -> str:
        return self.workspace_path or ""

    def get_active_provider(self) -> str:
        self.config = load_config()
        return self.config.get("active_provider", "gemini")

    async def get_gemini_client(self):
        return await get_gemini_client(self)

    def get_agent(self, session_id: str) -> CodingAgent:
        if session_id not in self.agents:
            self.agents[session_id] = CodingAgent(
                workspace_path=self.workspace_path,
                session_id=session_id,
            )
            from ..agents import agent_registry

            agent_registry.register_session(session_id, self.agents[session_id])
        return self.agents[session_id]

    async def get_gemini_chat_session(self, session_id: str, history=None, fresh: bool = False):
        return await get_gemini_chat_session(self, session_id, history=history, fresh=fresh)

    def interrupt_session(self, session_id: str):
        self.interrupted_sessions.add(session_id)
        if session_id in self.active_tasks:
            task = self.active_tasks[session_id]
            if task and not task.done():
                task.cancel()

    def _is_interrupted(self, session_id: str) -> bool:
        return session_id in self.interrupted_sessions

    async def _send_with_retry(self, *args, **kwargs):
        return await send_with_retry(self, *args, **kwargs)

    async def generate_response(
        self,
        text: str,
        session_id: str = None,
        files: List[str] = None,
        history: Any = None,
        chat_type: str = "t2t",
        thinking_enabled: bool = True,
        thinking_mode: str = "Auto",
    ) -> AsyncGenerator[Dict[str, Any], None]:
        provider_name = self.get_active_provider()
        agent = self.get_agent(session_id) if session_id else None
        message_parts: List[Dict[str, Any]] = []
        images: List[str] = []

        try:
            if session_id in self.interrupted_sessions:
                self.interrupted_sessions.remove(session_id)
            if agent:
                agent.reset_context()

            if agent and self.workspace_path:
                system_context = agent.get_system_prompt()
                full_prompt = (
                    f"{system_context}\n\n## User Request\n{text}\n\n"
                    "Execute this task using the appropriate tools."
                )
                if files and provider_name != "gemini":
                    full_prompt += "\n\nAttached Files Content:\n"
                    for file_path in files:
                        try:
                            import chardet

                            with open(file_path, "rb") as handle:
                                raw = handle.read(20000)
                                encoding = chardet.detect(raw)["encoding"] or "utf-8"
                                full_prompt += (
                                    f"\n--- {file_path} ---\n"
                                    f"{raw.decode(encoding, errors='ignore')}\n"
                                )
                        except Exception as exc:
                            full_prompt += f"\n--- {file_path} ---\n[Error reading file: {exc}]\n"
            else:
                full_prompt = text

            chat_session = None
            if provider_name == "gemini":
                chat_session = await self.get_gemini_chat_session(session_id, history=history)
            else:
                if session_id not in self.provider_sessions:
                    self.provider_sessions[session_id] = []
                self.provider_sessions[session_id].append({"role": "user", "content": full_prompt})

            if agent and self.workspace_path:
                max_iterations = 20
                iteration = 0
                current_prompt = full_prompt

                while iteration < max_iterations:
                    if self._is_interrupted(session_id):
                        yield {"text": "\n\n*Agent interrupted by user.*", "is_final": True}
                        break

                    if not agent.increment_iteration():
                        yield {"text": "\n\n*Agent reached maximum iterations. Task may be incomplete.*", "is_final": True}
                        break

                    from ..agents import agent_registry
                    agent_registry.update_session(session_id)

                    response_text = ""
                    api_thoughts = ""

                    if provider_name == "gemini":
                        gemini_resp = await self._send_with_retry(
                            chat_session,
                            current_prompt,
                            files=files if iteration == 0 else None,
                            session_id=session_id,
                        )
                        response_text = gemini_resp.text or ""
                        api_thoughts = getattr(gemini_resp, "thoughts", None) or ""

                        if hasattr(gemini_resp, "images") and gemini_resp.images:
                            image_service = get_image_service(self.workspace_path)
                            for image in gemini_resp.images:
                                image_url = getattr(image, "url", "")
                                if image_url and image_url not in images:
                                    images.append(image_url)
                                    image_service.generated_images.append(
                                        ImageResult(
                                            url=image_url,
                                            image_type=ImageType.GENERATED if "generated" in type(image).__name__.lower() else ImageType.WEB,
                                            title=getattr(image, "title", None),
                                            alt=getattr(image, "alt", None),
                                        )
                                    )
                    else:
                        provider_svc = get_provider_service(provider_name)
                        if not provider_svc:
                            yield {"error": f"Provider '{provider_name}' not found.", "is_final": True}
                            return

                        if iteration > 0:
                            self.provider_sessions[session_id].append({"role": "user", "content": current_prompt})

                        accumulated_text = ""
                        accumulated_thought = ""
                        in_think_block = False

                        async for chunk in provider_svc.generate_stream(
                            self.provider_sessions[session_id],
                            self.config.get("model", ""),
                            proxy=self.config.get("proxy"),
                            chat_type=chat_type,
                            thinking_enabled=thinking_enabled,
                            thinking_mode=thinking_mode,
                            files=files,
                            conversation=self.qwen_conversations.get(session_id) if provider_name == "qwen" else None,
                        ):
                            if "conversation" in chunk:
                                self.qwen_conversations[session_id] = chunk["conversation"]
                                continue
                            if "error" in chunk:
                                yield {"error": chunk["error"]}
                                message_parts.append({"type": "error", "content": chunk["error"]})
                                continue
                            if "thought" in chunk:
                                accumulated_thought += chunk["thought"]
                                yield {"thought": chunk["thought"]}
                            if "text" in chunk:
                                token = chunk["text"]
                                accumulated_text += token
                                if "<think>" in token:
                                    in_think_block = True
                                    before, after = token.split("<think>", 1)
                                    if before:
                                        yield {"text": before}
                                    if after:
                                        accumulated_thought += after
                                        yield {"thought": after}
                                    continue
                                if "</think>" in token:
                                    in_think_block = False
                                    before, after = token.split("</think>", 1)
                                    if before:
                                        accumulated_thought += before
                                        yield {"thought": before}
                                    if after:
                                        yield {"text": after}
                                    continue
                                if in_think_block:
                                    accumulated_thought += token
                                    yield {"thought": token}
                                else:
                                    yield {"text": token}

                        response_text = accumulated_text
                        api_thoughts = accumulated_thought
                        self.provider_sessions[session_id].append({"role": "assistant", "content": response_text})

                    if provider_name == "gemini":
                        embedded_thinking, clean_response = separate_thinking(self, response_text)
                        all_thoughts = api_thoughts
                        if embedded_thinking:
                            all_thoughts = f"{all_thoughts}\n\n{embedded_thinking}".strip() if all_thoughts else embedded_thinking
                        if all_thoughts:
                            yield {"thought": all_thoughts}
                            message_parts.append({"type": "thought", "content": all_thoughts})
                    else:
                        clean_response = response_text
                        if api_thoughts:
                            message_parts.append({"type": "thought", "content": api_thoughts})

                    tool_call = agent.parse_tool_call(clean_response)
                    if not tool_call:
                        final_text = clean_response_text(self, clean_response)
                        if provider_name == "gemini":
                            if final_text:
                                yield {"text": final_text, "images": images, "is_final": True}
                                message_parts.append({"type": "text", "content": final_text})
                            elif images:
                                yield {"text": "", "images": images, "is_final": True}
                            else:
                                yield {"text": "[Agent completed]", "is_final": True}
                        else:
                            if final_text:
                                message_parts.append({"type": "text", "content": final_text})
                            yield {"images": images, "is_final": True}
                        break

                    display_text = clean_response_text(self, clean_response, tool_call.get("raw_match"))
                    if display_text:
                        if provider_name == "gemini":
                            yield {"text": display_text + "\n"}
                        message_parts.append({"type": "text", "content": display_text})

                    yield {"tool_call": {"name": tool_call["name"], "args": tool_call["args"]}}
                    message_parts.append(
                        {"type": "tool_call", "content": {"name": tool_call["name"], "args": tool_call["args"]}}
                    )

                    if self._is_interrupted(session_id):
                        yield {"text": "\n\n*Agent interrupted by user.*", "is_final": True}
                        break

                    try:
                        if tool_call["name"] == "delegate_task":
                            tool_result = await run_delegated_task(
                                self,
                                tool_call["args"].get("task", ""),
                                tool_call["args"].get("context", ""),
                            )
                        elif tool_call["name"] == "generate_image":
                            tool_result = await handle_image_generation(
                                self,
                                tool_call["args"],
                                provider_name,
                                chat_session,
                                session_id,
                            )
                            image_service = get_image_service(self.workspace_path)
                            for image in image_service.generated_images:
                                if image.url and image.url not in images:
                                    images.append(image.url)
                                    yield {"images": [image.url]}
                        else:
                            tool_result, _ = await agent.execute_tool(tool_call["name"], tool_call["args"])

                        yield {"tool_result": tool_result}
                        message_parts.append({"type": "tool_result", "content": tool_result})

                        if self._is_interrupted(session_id):
                            yield {"text": "\n\n*Agent interrupted by user.*", "is_final": True}
                            break

                        current_prompt = tool_result
                        iteration += 1
                    except asyncio.CancelledError:
                        yield {"text": "\n\n*Agent interrupted by user.*", "is_final": True}
                        break
                    except Exception as exc:
                        error_msg = f"Error executing '{tool_call['name']}': {str(exc)}"
                        yield {"tool_result": error_msg, "is_final": True}
                        message_parts.append({"type": "tool_result", "content": error_msg})
                        current_prompt = error_msg
                        iteration += 1

                if iteration >= max_iterations and not self._is_interrupted(session_id):
                    yield {"text": "\n\n*Agent reached maximum iterations.*", "is_final": True}
            else:
                async for chunk in generate_simple_response(
                    self,
                    full_prompt,
                    provider_name,
                    chat_session,
                    files,
                    session_id,
                    message_parts,
                    images,
                    history,
                ):
                    yield chunk
        except asyncio.CancelledError:
            yield {"text": "\n\n*Interrupted.*", "is_final": True}
            message_parts.append({"type": "text", "content": "*Interrupted*"})
        except Exception as exc:
            import traceback

            traceback.print_exc()
            error_msg = f"Error ({type(exc).__name__}): {str(exc)}"
            error_str = str(exc).lower()
            if "invalid response" in error_str or "403" in error_str or "failed to generate" in error_str:
                error_msg += "\n\n**Hint:** Your Gemini cookies (Secure-1PSID) might be invalid or expired."
            yield {"error": error_msg, "is_final": True}
            message_parts.append({"type": "error", "content": error_msg})
            return
        finally:
            if session_id in self.interrupted_sessions:
                self.interrupted_sessions.remove(session_id)
            if session_id and message_parts:
                try:
                    await async_save_chat_message(
                        session_id,
                        "ai",
                        parts=message_parts,
                        images=images,
                        workspace_id=self.workspace_id,
                    )
                except Exception as exc:
                    print(f"[LLMService] Failed to save message: {exc}")

    async def _generate_simple_response(self, *args, **kwargs):
        async for chunk in generate_simple_response(self, *args, **kwargs):
            yield chunk

    async def _handle_image_generation(self, *args, **kwargs) -> str:
        return await handle_image_generation(self, *args, **kwargs)

    async def run_delegated_task(self, task: str, context: str = "") -> str:
        return await run_delegated_task(self, task, context)

    async def reset(self):
        self.gemini_client = None
        self.sessions = {}
        self.provider_sessions = {}
        self.qwen_conversations = {}
        self.agents = {}
        self.interrupted_sessions.clear()
        self.active_tasks.clear()
