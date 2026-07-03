import asyncio

from ..agents import agent_registry
from ..coding_agent import CodingAgent
from ..config import load_config
from ..providers import get_provider_service
from ..models import get_max_output
from .helpers import clean_response_text, separate_thinking


async def generate_simple_response(
    service,
    full_prompt: str,
    provider_name: str,
    chat_session,
    files,
    session_id,
    message_parts: list,
    images: list,
    history,
    chat_type: str = "t2t",
    thinking_enabled: bool = True,
    thinking_mode: str = "Auto",
    reasoning_effort: str = "medium",
):
    provider_svc = get_provider_service(provider_name)
    if not provider_svc:
        yield {"error": f"Provider '{provider_name}' not found.", "is_final": True}
        return

    proxy = service.config.get("proxy")
    model_name = service.config.get("model", "")
    provider_kwargs = {"proxy": proxy, "thinking_enabled": thinking_enabled, "thinking_mode": thinking_mode, "reasoning_effort": reasoning_effort, "max_tokens": get_max_output(provider_name, model_name)}
    if provider_name == "grok":
        provider_kwargs["proxy"] = service.config.get("grok_proxy") or proxy
    elif provider_name == "glm":
        provider_kwargs["token"] = service.config.get("glm_refresh_token", "")
    elif provider_name == "chat2api":
        provider_kwargs["base_url"] = service.config.get("chat2api_base_url", "http://127.0.0.1:8080")
        provider_kwargs["api_key"] = service.config.get("chat2api_api_key", "")
    elif provider_name == "lmarena":
        provider_kwargs["lmarena_cookies"] = service.config.get("lmarena_cookies", "")
    elif provider_name == "unimodel":
        provider_kwargs["api_key"] = service.config.get("unimodel_api_key", "")
        provider_kwargs["base_url"] = service.config.get("unimodel_base_url", "https://unimodel.ai/v1")
    elif provider_name == "bai":
        provider_kwargs["api_key"] = service.config.get("bai_api_key", "")
        provider_kwargs["base_url"] = service.config.get("bai_base_url", "https://api.b.ai/v1")
    elif provider_name == "openmodel":
        provider_kwargs["api_key"] = service.config.get("openmodel_api_key", "")
        provider_kwargs["base_url"] = service.config.get("openmodel_base_url", "https://api.openmodel.app/v1")
    elif provider_name == "paxsenix":
        provider_kwargs["api_key"] = service.config.get("paxsenix_api_key", "")
        provider_kwargs["base_url"] = service.config.get("paxsenix_base_url", "https://api.paxsenix.org/v1")
    elif provider_name == "zenmux":
        provider_kwargs["api_key"] = service.config.get("zenmux_api_key", "")
        provider_kwargs["base_url"] = service.config.get("zenmux_base_url", "https://zenmux.ai/api/v1")
    elif provider_name == "mistral":
        provider_kwargs["api_key"] = service.config.get("mistral_api_key", "")
        provider_kwargs["base_url"] = service.config.get("mistral_base_url", "https://api.mistral.ai/v1")
    elif provider_name == "babestown":
        provider_kwargs["api_key"] = service.config.get("babestown_api_key", "")
        provider_kwargs["base_url"] = service.config.get("babestown_base_url", "https://api.babel.town/v1")

    # Get Qwen conversation if available
    conversation = None
    if provider_name == "qwen" and hasattr(service, 'qwen_conversations') and session_id:
        conversation = service.qwen_conversations.get(session_id)

    messages = [{"role": "user", "content": full_prompt}]
    accumulated_text = ""
    accumulated_thought = ""

    async for chunk in provider_svc.generate_stream(
        messages,
        service.config.get("model", ""),
        **provider_kwargs
    ):
        if "error" in chunk:
            yield {"error": chunk["error"], "is_final": True}
        if "conversation" in chunk:
            if hasattr(service, 'qwen_conversations') and session_id:
                service.qwen_conversations[session_id] = chunk["conversation"]
            continue
        if "thought" in chunk:
            accumulated_thought += chunk["thought"]
            yield {"thought": chunk["thought"]}
        if "text" in chunk:
            accumulated_text += chunk["text"]
            yield {"text": chunk["text"]}
        if chunk.get("is_final"):
            yield {"is_final": True}

    if accumulated_thought:
        message_parts.append({"type": "thought", "content": accumulated_thought})
    message_parts.append({"type": "text", "content": accumulated_text})
    yield {"images": images, "is_final": True}


async def run_subagent_task(
    service,
    task: str,
    agent_type: str = "general",
    context: str = "",
) -> str:
    """Run a task using a subagent defined in subagent_defs.

    The subagent gets its own CodingAgent with the model/provider from
    the subagent definition, plus its role system prompt prepended.
    Falls back to the parent's provider/model when the def has empties.
    """
    try:
        from ..agents.subagent_defs import (get_subagent_def,
                                            load_custom_defs)

        ws = getattr(service, "workspace_path", None)
        if ws:
            load_custom_defs(ws)

        sub_def = get_subagent_def(agent_type)
        if not sub_def:
            return (f"Error: Unknown subagent type '{agent_type}'.")

        from ..coding_agent import CodingAgent

        temp_agent = CodingAgent(service.workspace_path)
        if sub_def.provider:
            temp_agent.provider_name = sub_def.provider
        if sub_def.model:
            temp_agent.model = sub_def.model

        provider_name = temp_agent.provider_name or service.get_active_provider()
        model_name = temp_agent.model or service.config.get("model", "")

        prompt = (
            f"{temp_agent.get_system_prompt()}\n\n"
            f"## Role\n\n{sub_def.system_prompt}\n\n"
            f"## Delegated Task\n"
            f"Context from parent agent: {context}\n\n"
            f"Task: {task}\n\n"
            "Execute this task autonomously. When done, output your final answer."
        )

        provider_svc = get_provider_service(provider_name)
        if not provider_svc:
            return f"Delegation error: Provider '{provider_name}' not found."

        messages = [{"role": "user", "content": prompt}]
        response_text = ""
        accumulated_text = ""
        try:
            async for chunk in provider_svc.generate_stream(
                messages,
                model_name,
                proxy=service.config.get("proxy"),
            ):
                if "text" in chunk:
                    accumulated_text += chunk["text"]
                if "error" in chunk:
                    return f"Delegation error: {chunk['error']}"
        except Exception as e:
            return f"Delegation error: {str(e)}"
        response_text = accumulated_text

        for _ in range(15):
            tool_call = temp_agent.parse_tool_call(response_text)
            if not tool_call:
                break
            if sub_def.tools.deny and tool_call["name"] in sub_def.tools.deny:
                err = f"Tool '{tool_call['name']}' not allowed for '{agent_type}' subagent"
                messages = [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": response_text},
                    {"role": "tool", "content": err},
                ]
                continue
            tool_result, _ = await temp_agent.execute_tool(
                tool_call["name"], tool_call["args"]
            )
            messages = [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": response_text},
                {"role": "tool", "content": tool_result},
            ]
            accumulated_text = ""
            async for chunk in provider_svc.generate_stream(
                messages,
                model_name,
                proxy=service.config.get("proxy"),
            ):
                if "text" in chunk:
                    accumulated_text += chunk["text"]
            response_text = accumulated_text

        return f"**Sub-agent ({agent_type}) result:**\n{response_text}"
    except asyncio.TimeoutError:
        return "Error: Delegated task timed out"
    except Exception as exc:
        return f"Error in delegated task: {str(exc)}"


async def run_delegated_task(service, task: str, context: str = "") -> str:
    """Legacy wrapper — delegates with the 'general' subagent type."""
    return await run_subagent_task(service, task, agent_type="general", context=context)
