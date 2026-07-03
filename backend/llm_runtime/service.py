import asyncio
import json
import logging
import random
import time
import uuid
from typing import Dict, Any, List, Optional, AsyncGenerator

import aiohttp

from ..config import load_config
from ..coding_agent import CodingAgent
from ..prompts import SYSTEM_PROMPT as LEGACY_SYSTEM_PROMPT
from ..response_filter import ResponseFilter, ThoughtFilter
from ..storage import async_save_chat_message
from ..providers import get_provider_service
from ..providers.base import ProviderType
from .helpers import clean_response_text, separate_thinking
from .support import generate_simple_response, run_delegated_task
from ..models import get_context_window, get_max_output, estimate_tokens, should_compact, perform_compaction

logger = logging.getLogger("flashy.service")


_TRANSIENT_EXCEPTIONS = (
    asyncio.TimeoutError,
    aiohttp.ClientConnectionError,
    aiohttp.ClientOSError,
    aiohttp.ServerDisconnectedError,
    aiohttp.ServerTimeoutError,
    ConnectionError,
    OSError,
)


def _is_transient(exc: BaseException) -> bool:
    if isinstance(exc, _TRANSIENT_EXCEPTIONS):
        return True
    msg = str(exc).lower()
    needles = (
        "connection aborted",
        "connection reset",
        "connection refused",
        "remote disconnected",
        "timed out",
        "timeout",
        "temporary failure",
        "network is unreachable",
        "winerror 1236",
        "winerror 10054",
        "winerror 10053",
    )
    return any(n in msg for n in needles)


def _build_text_tool_instruction(tools: List[Dict[str, Any]]) -> str:
    lines = [
        "You have access to the following tools. Use them to accomplish the user's task.",
        "When you need to invoke a tool, respond with ONLY a single line in this exact format:",
        '««TOOL_CALL»» {"name": "TOOL_NAME", "arguments": {"PARAM_NAME": "PARAM_VALUE"}} ««/TOOL_CALL»»',
        "",
        "CRITICAL RULES:",
        "- Do NOT write any text before or after the tool call line.",
        "- Do NOT say 'Tool does not exist' or 'I cannot access tools'. All listed tools ARE available.",
        "- The JSON must have 'name' (exact tool name) and 'arguments' (object with parameter values).",
        "- NEVER generate <tool_result> blocks yourself.",
        "- After receiving a <tool_result> block, call another tool or give your final answer.",
        "",
        "Available tools:",
    ]
    for t in tools:
        fn = t.get("function", t)
        name = fn.get("name", "unknown")
        desc = fn.get("description", "")
        params = fn.get("parameters", {})
        param_strs = []
        if params.get("properties"):
            required = params.get("required", [])
            for pname, pinfo in params["properties"].items():
                req_tag = "required" if pname in required else "optional"
                param_strs.append(f"{pname} ({req_tag})")
        param_block = f" — params: {', '.join(param_strs)}" if param_strs else ""
        lines.append(f"  - {name}: {desc}{param_block}")
    return "\n".join(lines)


class LLMService:
    def __init__(self, config_overrides: Optional[Dict[str, Any]] = None):
        self.config_overrides: Dict[str, Any] = dict(config_overrides or {})
        self.config = load_config()
        self.config.update(self.config_overrides)
        self.sessions: Dict[str, Any] = {}
        self.provider_sessions: Dict[str, List[Dict[str, str]]] = {}
        self.agents: Dict[str, CodingAgent] = {}
        self.interrupted_sessions: set = set()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.workspace_path: Optional[str] = None
        self.workspace_id: Optional[str] = None
        self.response_filter = ResponseFilter(aggressive=False)
        self.thought_filter = ThoughtFilter()
        self.session_usage: Dict[str, Dict[str, int]] = {}
        # Subagent session tracking: parent_session_id -> list of child session ids
        self.subagent_sessions: Dict[str, Dict[str, Any]] = {}

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
        self.config.update(self.config_overrides)
        return self.config.get("active_provider", "g4f")

    def reset_provider_session(self) -> None:
        provider_name = self.get_active_provider()
        svc = get_provider_service(provider_name)
        if svc and hasattr(svc, "reset_session"):
            svc.reset_session()

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

    async def _stream_with_retry(
        self,
        provider_svc,
        messages: List[Dict[str, Any]],
        model: str,
        session_id: str,
        max_retries: int = 5,
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Wrap a provider's stream with transient-error retry + exponential backoff.

        Any error that is judged transient (connection aborted/reset, timeouts, 5xx, etc.)
        is retried by replaying the same request. Errors that yielded any output before
        the failure are dropped on retry (the model is stateless, so the next attempt
        will regenerate from scratch). Non-transient errors propagate to the caller.
        """
        attempt = 0
        last_exc: Optional[BaseException] = None
        while attempt <= max_retries:
            if self._is_interrupted(session_id):
                yield {"error": "*Interrupted by user.*", "is_final": True}
                return
            try:
                async for chunk in provider_svc.generate_stream(messages, model, **kwargs):
                    if "error" in chunk:
                        text = str(chunk.get("error", ""))
                        if any(s in text for s in (" 5", " 502", " 503", " 504", "timeout", "timed out")) and _is_transient(Exception(text)):
                            last_exc = Exception(text)
                            logger.warning("[LLM] transient stream error (attempt %d/%d): %s", attempt + 1, max_retries, text[:200])
                            break
                        yield chunk
                        return
                    yield chunk
                return
            except _TRANSIENT_EXCEPTIONS as exc:
                last_exc = exc
                logger.warning("[LLM] transient connection error (attempt %d/%d): %s", attempt + 1, max_retries, exc)
            except Exception as exc:
                if _is_transient(exc):
                    last_exc = exc
                    logger.warning("[LLM] transient error (attempt %d/%d): %s", attempt + 1, max_retries, exc)
                else:
                    raise

            attempt += 1
            if attempt > max_retries:
                break

            backoff = min(2 ** attempt, 30) + random.uniform(0, 0.5)
            yield {"text": f"\n*[Network blip — retrying in {backoff:.1f}s ({attempt}/{max_retries})...]*\n"}
            try:
                await asyncio.sleep(backoff)
            except asyncio.CancelledError:
                raise

        yield {"error": f"Network error after {max_retries} retries: {last_exc}"}

    async def generate_response(
        self,
        text: str,
        session_id: str = None,
        files: List[str] = None,
        history: Any = None,
        chat_type: str = "t2t",
        thinking_enabled: bool = True,
        thinking_mode: str = "Auto",
        reasoning_effort: str = "medium",
    ) -> AsyncGenerator[Dict[str, Any], None]:
        provider_name = self.get_active_provider()
        agent = self.get_agent(session_id) if session_id else None
        message_parts: List[Dict[str, Any]] = []
        images: List[str] = []

        try:
            if session_id in self.interrupted_sessions:
                self.interrupted_sessions.remove(session_id)

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
                iteration = 0

                while True:
                    if self._is_interrupted(session_id):
                        yield {"text": "\n\n*Agent interrupted by user.*", "is_final": True}
                        break

                    agent.increment_iteration()

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
                        yield {"text": "\n*[Context is getting full, compacting...]*\n"}
                        was = await perform_compaction(
                            session_id, self.provider_sessions,
                            self.session_usage, context_window,
                            provider_name, s_usage.get("model", "") if s_usage else "",
                            llm_service=self
                        )
                        if was:
                            if hasattr(provider_svc, "reset_session"):
                                provider_svc.reset_session()
                            yield {"text": "\n*[Context compacted — continuing...]*\n"}

                    accumulated_text = ""
                    accumulated_thought = ""
                    native_tool_calls: List[Dict[str, Any]] = []
                    in_think_block = False

                    provider_kwargs = {
                        "proxy": self.config.get("proxy"),
                        "chat_type": chat_type,
                        "thinking_enabled": thinking_enabled,
                        "thinking_mode": thinking_mode,
                        "reasoning_effort": reasoning_effort,
                        "files": files,
                        "max_tokens": get_max_output(
                            s_usage.get("provider", provider_name) if s_usage else provider_name,
                            s_usage.get("model", "") if s_usage else "",
                        ),
                    }
                    if provider_name == "grok":
                        provider_kwargs["proxy"] = self.config.get("grok_proxy") or provider_kwargs["proxy"]
                    elif provider_name == "deepseek":
                        provider_kwargs["token"] = self.config.get("deepseek_token", "")
                    elif provider_name == "glm":
                        provider_kwargs["token"] = self.config.get("glm_refresh_token", "")
                    elif provider_name == "chat2api":
                        provider_kwargs["base_url"] = self.config.get("chat2api_base_url", "http://127.0.0.1:8080")
                        provider_kwargs["api_key"] = self.config.get("chat2api_api_key", "")
                    elif provider_name == "lmarena":
                        provider_kwargs["lmarena_cookies"] = self.config.get("lmarena_cookies", "")
                    elif provider_name == "minimax":
                        provider_kwargs["token"] = self.config.get("minimax_token", "")
                        provider_kwargs["real_user_id"] = self.config.get("minimax_real_user_id", "")
                    elif provider_name == "mimo":
                        provider_kwargs["service_token"] = self.config.get("mimo_service_token", "")
                        provider_kwargs["user_id"] = self.config.get("mimo_user_id", "")
                        provider_kwargs["ph_token"] = self.config.get("mimo_ph_token", "")
                    elif provider_name == "perplexity":
                        provider_kwargs["session_token"] = self.config.get("perplexity_session_token", "")
                    elif provider_name == "unimodel":
                        provider_kwargs["api_key"] = self.config.get("unimodel_api_key", "")
                        provider_kwargs["base_url"] = self.config.get("unimodel_base_url", "https://unimodel.ai/v1")
                    elif provider_name == "bai":
                        provider_kwargs["api_key"] = self.config.get("bai_api_key", "")
                        provider_kwargs["base_url"] = self.config.get("bai_base_url", "https://api.b.ai/v1")
                    elif provider_name == "openmodel":
                        provider_kwargs["api_key"] = self.config.get("openmodel_api_key", "")
                        provider_kwargs["base_url"] = self.config.get("openmodel_base_url", "https://api.openmodel.app/v1")
                    elif provider_name == "paxsenix":
                        provider_kwargs["api_key"] = self.config.get("paxsenix_api_key", "")
                        provider_kwargs["base_url"] = self.config.get("paxsenix_base_url", "https://api.paxsenix.org/v1")
                    elif provider_name == "zenmux":
                        provider_kwargs["api_key"] = self.config.get("zenmux_api_key", "")
                        provider_kwargs["base_url"] = self.config.get("zenmux_base_url", "https://zenmux.ai/api/v1")
                    elif provider_name == "mistral":
                        provider_kwargs["api_key"] = self.config.get("mistral_api_key", "")
                        provider_kwargs["base_url"] = self.config.get("mistral_base_url", "https://api.mistral.ai/v1")
                    elif provider_name == "babestown":
                        provider_kwargs["api_key"] = self.config.get("babestown_api_key", "")
                        provider_kwargs["base_url"] = self.config.get("babestown_base_url", "https://api.babel.town/v1")

                    if agent and self.workspace_path and provider_svc.supports_native_tools:
                        tool_defs = agent.get_openai_tool_definitions()
                        if tool_defs:
                            provider_kwargs["tools"] = tool_defs
                            provider_kwargs["tool_choice"] = "auto"
                    elif provider_name == "qwen" and agent and self.workspace_path:
                        tool_defs = agent.get_openai_tool_definitions()
                        if tool_defs:
                            provider_kwargs["tools"] = tool_defs
                            provider_kwargs["is_openai_pass_through"] = True
                    elif agent and self.workspace_path:
                        tool_defs = agent.get_openai_tool_definitions()
                        if tool_defs:
                            tool_instruction = _build_text_tool_instruction(tool_defs)
                            messages_for_call = list(self.provider_sessions.get(session_id, []))
                            if not messages_for_call or messages_for_call[0].get("role") != "system":
                                messages_for_call.insert(0, {"role": "system", "content": tool_instruction})
                            else:
                                existing = messages_for_call[0].get("content") or ""
                                if "you have access to the following tools" not in existing.lower():
                                    messages_for_call[0] = {**messages_for_call[0], "content": existing + "\n\n" + tool_instruction}
                            provider_kwargs["messages"] = messages_for_call

                    target_messages = provider_kwargs.pop("messages", None)
                    async for chunk in self._stream_with_retry(
                        provider_svc,
                        target_messages or self.provider_sessions[session_id],
                        self.config.get("model", ""),
                        session_id=session_id,
                        **provider_kwargs,
                    ):
                        if "error" in chunk:
                            yield {"error": chunk["error"]}
                            message_parts.append({"type": "error", "content": chunk["error"]})
                            continue
                        if "thought" in chunk:
                            accumulated_thought += chunk["thought"]
                            yield {"thought": chunk["thought"]}
                        if "usage" in chunk:
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
                        if "tool_call" in chunk:
                            native_tool_calls.append(chunk["tool_call"])

                    response_text = accumulated_text
                    api_thoughts = accumulated_thought

                    clean_response = response_text
                    if api_thoughts:
                        message_parts.append({"type": "thought", "content": api_thoughts})

                    if native_tool_calls:
                        if response_text:
                            message_parts.append({"type": "text", "content": response_text})
                        all_results = []
                        for tc in native_tool_calls:
                            name = tc.get("name", "")
                            args_raw = tc.get("arguments", "{}")
                            try:
                                args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                            except json.JSONDecodeError:
                                args = {}

                            yield {"tool_call": {"name": name, "args": args}}
                            message_parts.append(
                                {"type": "tool_call", "content": {"name": name, "args": args}}
                            )

                            try:
                                from .support import run_subagent_task as _run_sub
                                if name in ("delegate_task", "task"):
                                    result = await _run_sub(
                                        self,
                                        task=args.get("task", ""),
                                        agent_type=args.get("agent_type", "general"),
                                        context=args.get("context", ""),
                                    )
                                else:
                                    result, _ = await agent.execute_tool(name, args)
                            except Exception as exc:
                                result = f"Error executing '{name}': {str(exc)}"

                            yield {"tool_result": result}
                            message_parts.append({"type": "tool_result", "content": result})
                            all_results.append(result)

                        if provider_svc.supports_native_tools:
                            tool_calls_list = []
                            for tc in native_tool_calls:
                                tc_id = tc.get("id") or f"call_{uuid.uuid4().hex[:16]}"
                                tc_args = tc.get("arguments", "{}")
                                tool_calls_list.append({
                                    "id": tc_id,
                                    "type": "function",
                                    "function": {
                                        "name": tc.get("name", ""),
                                        "arguments": tc_args if isinstance(tc_args, str) else json.dumps(tc_args),
                                    },
                                })
                            self.provider_sessions[session_id].append({
                                "role": "assistant",
                                "content": response_text or None,
                                "tool_calls": tool_calls_list,
                            })
                            for i, result in enumerate(all_results):
                                self.provider_sessions[session_id].append({
                                    "role": "tool",
                                    "content": result,
                                    "tool_call_id": tool_calls_list[i]["id"],
                                })
                        else:
                            self.provider_sessions[session_id].append({"role": "assistant", "content": response_text})
                            for result in all_results:
                                self.provider_sessions[session_id].append({"role": "tool", "content": result})
                        iteration += 1
                        continue

                    tool_call = agent.parse_tool_call(clean_response)
                    if not tool_call:
                        self.provider_sessions[session_id].append({"role": "assistant", "content": response_text})
                        final_text = clean_response_text(self, clean_response)
                        if final_text:
                            yield {"images": images, "is_final": True}
                            message_parts.append({"type": "text", "content": final_text})
                        elif images:
                            yield {"images": images, "is_final": True}
                        else:
                            yield {"is_final": True}
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
                        from .support import run_subagent_task as _run_sub
                        if tool_call["name"] in ("delegate_task", "task"):
                            tool_result = await _run_sub(
                                self,
                                task=tool_call["args"].get("task", ""),
                                agent_type=tool_call["args"].get("agent_type", "general"),
                                context=tool_call["args"].get("context", ""),
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
            import os
            import traceback

            if os.environ.get("FLASHY_DEBUG"):
                traceback.print_exc()
            error_msg = f"Error ({type(exc).__name__}): {str(exc)}"
            error_str = str(exc).lower()
            provider_name = self.get_active_provider()
            if "invalid response" in error_str or "403" in error_str or "failed to generate" in error_str:
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
        self.agents = {}
        self.interrupted_sessions.clear()
        self.active_tasks.clear()
