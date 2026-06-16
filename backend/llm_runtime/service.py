import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator

from ..config import load_config
from ..coding_agent import CodingAgent
from ..prompts import SYSTEM_PROMPT as LEGACY_SYSTEM_PROMPT
from ..response_filter import ResponseFilter, ThoughtFilter
from ..storage import async_save_chat_message
from ..providers import get_provider_service
from .helpers import clean_response_text, separate_thinking
from .support import generate_simple_response, run_delegated_task
from ..models import get_context_window, estimate_tokens, should_compact, perform_compaction


class LLMService:
    def __init__(self):
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
        self._qwen_usage_stats: Dict[str, Dict[str, int]] = {}
        self.session_usage: Dict[str, Dict[str, int]] = {}

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
        return self.config.get("active_provider", "qwen")

    def get_agent(self, session_id: str) -> CodingAgent:
        if session_id not in self.agents:
            self.agents[session_id] = CodingAgent(
                workspace_path=self.workspace_path,
                session_id=session_id,
            )
            from ..agents import agent_registry

            agent_registry.register_session(session_id, self.agents[session_id])
        return self.agents[session_id]

    def interrupt_session(self, session_id: str):
        self.interrupted_sessions.add(session_id)
        if session_id in self.active_tasks:
            task = self.active_tasks[session_id]
            if task and not task.done():
                task.cancel()

    def _is_interrupted(self, session_id: str) -> bool:
        return session_id in self.interrupted_sessions

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

            if agent and self.workspace_path:
                system_context = (
                    LEGACY_SYSTEM_PROMPT.replace("{workspace_path}", agent.tools.workspace_path or "[Not Set]")
                    if provider_name == "qwen"
                    else agent.get_system_prompt()
                )
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
            if session_id not in self.provider_sessions:
                self.provider_sessions[session_id] = []
            self.provider_sessions[session_id].append({"role": "user", "content": full_prompt})

            # Init usage tracking for this session
            model_name = self.config.get("model", "")
            self.session_usage[session_id] = {
                "input_tokens": estimate_tokens(full_prompt),
                "output_tokens": 0,
                "provider": provider_name,
                "model": model_name,
            }

            if agent and self.workspace_path:
                max_iterations = 500
                iteration = 0

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

                    provider_svc = get_provider_service(provider_name)
                    if not provider_svc:
                        yield {"error": f"Provider '{provider_name}' not found.", "is_final": True}
                        return

                    # Re-estimate token usage from current messages
                    messages = self.provider_sessions.get(session_id, [])
                    total_est = sum(estimate_tokens(m.get("content", "")) for m in messages)
                    s_usage = self.session_usage.get(session_id)
                    if s_usage:
                        s_usage["input_tokens"] = total_est
                    context_window = get_context_window(
                        s_usage.get("provider", provider_name) if s_usage else provider_name,
                        s_usage.get("model", "") if s_usage else "",
                    )

                    # Check whether to compact before this provider call
                    if should_compact(total_est, context_window):
                        was = perform_compaction(
                            session_id, self.provider_sessions,
                            self.session_usage, context_window,
                            provider_name, s_usage.get("model", "") if s_usage else "",
                        )
                        if was:
                            yield {"text": "\n*[Context compacted — continuing...]*\n"}

                    accumulated_text = ""
                    accumulated_thought = ""
                    in_think_block = False

                    provider_kwargs = {
                        "proxy": self.config.get("proxy"),
                        "chat_type": chat_type,
                        "thinking_enabled": thinking_enabled,
                        "thinking_mode": thinking_mode,
                        "files": files,
                        "conversation": self.qwen_conversations.get(session_id) if provider_name == "qwen" else None,
                    }
                    if provider_name == "grok":
                        provider_kwargs["proxy"] = self.config.get("grok_proxy") or provider_kwargs["proxy"]
                    elif provider_name == "deepseek":
                        provider_kwargs["token"] = self.config.get("deepseek_token", "")
                    elif provider_name == "kimi":
                        provider_kwargs["token"] = self.config.get("kimi_token", "")
                    elif provider_name == "zai":
                        provider_kwargs["token"] = self.config.get("zai_token", "")
                    elif provider_name == "glm":
                        provider_kwargs["token"] = self.config.get("glm_refresh_token", "")
                    elif provider_name == "chat2api":
                        provider_kwargs["base_url"] = self.config.get("chat2api_base_url", "http://127.0.0.1:8080")
                        provider_kwargs["api_key"] = self.config.get("chat2api_api_key", "")
                    elif provider_name == "lmarena":
                        provider_kwargs["lmarena_cookies"] = self.config.get("lmarena_cookies", "")

                    async for chunk in provider_svc.generate_stream(
                        self.provider_sessions[session_id],
                        self.config.get("model", ""),
                        **provider_kwargs
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
                        if "usage" in chunk:
                            self._qwen_usage_stats[session_id] = chunk["usage"]
                            usage_data = chunk["usage"]
                            # Update tracked usage from provider
                            pu = self.session_usage.get(session_id, {})
                            if usage_data:
                                pu["input_tokens"] = usage_data.get("prompt_tokens", usage_data.get("input_tokens", pu.get("input_tokens", 0)))
                                pu["output_tokens"] = usage_data.get("completion_tokens", usage_data.get("output_tokens", pu.get("output_tokens", 0)))
                            yield {"usage": chunk["usage"]}
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

                    clean_response = response_text
                    if api_thoughts:
                        message_parts.append({"type": "thought", "content": api_thoughts})

                    tool_call = agent.parse_tool_call(clean_response)
                    if not tool_call:
                        self.provider_sessions[session_id].append({"role": "assistant", "content": response_text})
                        final_text = clean_response_text(self, clean_response)
                        if final_text:
                            yield {"text": final_text, "images": images, "is_final": True}
                            message_parts.append({"type": "text", "content": final_text})
                        elif images:
                            yield {"text": "", "images": images, "is_final": True}
                        else:
                            yield {"text": "", "is_final": True}
                        break

                    display_text = clean_response_text(self, clean_response, tool_call.get("raw_match"))
                    if display_text:
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
                        else:
                            tool_result, _ = await agent.execute_tool(tool_call["name"], tool_call["args"])

                        yield {"tool_result": tool_result}
                        message_parts.append({"type": "tool_result", "content": tool_result})

                        if self._is_interrupted(session_id):
                            yield {"text": "\n\n*Agent interrupted by user.*", "is_final": True}
                            break

                        self.provider_sessions[session_id].append({"role": "assistant", "content": response_text})
                        self.provider_sessions[session_id].append({"role": "tool", "content": tool_result})
                        iteration += 1
                    except asyncio.CancelledError:
                        yield {"text": "\n\n*Agent interrupted by user.*", "is_final": True}
                        break
                    except Exception as exc:
                        error_msg = f"Error executing '{tool_call['name']}': {str(exc)}"
                        yield {"tool_result": error_msg}
                        message_parts.append({"type": "tool_result", "content": error_msg})
                        if self._is_interrupted(session_id):
                            yield {"text": "\n\n*Agent interrupted by user.*", "is_final": True}
                            break
                        self.provider_sessions[session_id].append({"role": "assistant", "content": response_text})
                        self.provider_sessions[session_id].append({"role": "tool", "content": error_msg})
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
                    chat_type=chat_type,
                    thinking_enabled=thinking_enabled,
                    thinking_mode=thinking_mode,
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
            provider_name = self.get_active_provider()
            if "invalid response" in error_str or "403" in error_str or "failed to generate" in error_str:
                if provider_name == "qwen":
                    error_msg += "\n\n**Hint:** Qwen may have triggered a WAF/captcha challenge. Try again in a moment."
                else:
                    error_msg += f"\n\n**Hint:** The {provider_name} provider may be temporarily unavailable."
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
