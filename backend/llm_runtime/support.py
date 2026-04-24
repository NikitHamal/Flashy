import asyncio

from ..agents import agent_registry
from ..coding_agent import CodingAgent
from ..config import load_config
from ..providers import get_provider_service
from .gemini import get_gemini_client, send_with_retry
from .helpers import clean_response_text, separate_thinking, resolve_gemini_model


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
):
    if provider_name == "gemini":
        gemini_resp = await send_with_retry(service, chat_session, full_prompt, files=files, session_id=session_id)
        response_text = gemini_resp.text or ""
        api_thoughts = getattr(gemini_resp, "thoughts", None) or ""
        embedded_thinking, clean_text = separate_thinking(service, response_text)
        clean_text = service.response_filter.filter(clean_text)

        all_thoughts = api_thoughts
        if embedded_thinking:
            all_thoughts = f"{all_thoughts}\n\n{embedded_thinking}".strip() if all_thoughts else embedded_thinking
        if all_thoughts:
            yield {"thought": all_thoughts}
            message_parts.append({"type": "thought", "content": all_thoughts})

        if hasattr(gemini_resp, "images") and gemini_resp.images:
            for img in gemini_resp.images:
                img_url = getattr(img, "url", "")
                if img_url:
                    images.append(img_url)

        yield {"text": clean_text, "images": images, "is_final": True}
        message_parts.append({"type": "text", "content": clean_text})
        return

    provider_svc = get_provider_service(provider_name)
    if not provider_svc:
        yield {"error": f"Provider '{provider_name}' not found.", "is_final": True}
        return

    proxy = service.config.get("proxy")
    provider_kwargs = {"proxy": proxy}
    if provider_name == "grok":
        provider_kwargs["proxy"] = service.config.get("grok_proxy") or proxy
    elif provider_name == "kimi":
        provider_kwargs["token"] = service.config.get("kimi_token", "")
    elif provider_name == "zai":
        provider_kwargs["token"] = service.config.get("zai_token", "")
    elif provider_name == "glm":
        provider_kwargs["token"] = service.config.get("glm_refresh_token", "")
    elif provider_name == "chat2api":
        provider_kwargs["base_url"] = service.config.get("chat2api_base_url", "http://127.0.0.1:8080")
        provider_kwargs["api_key"] = service.config.get("chat2api_api_key", "")
    elif provider_name == "lmarena":
        provider_kwargs["lmarena_cookies"] = service.config.get("lmarena_cookies", "")

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


async def run_delegated_task(service, task: str, context: str = "") -> str:
    try:
        provider_name = service.get_active_provider()
        temp_agent = CodingAgent(service.workspace_path)
        prompt = f"""{temp_agent.get_system_prompt()}

## Delegated Task
Context from parent agent: {context}

Task: {task}

Execute this task autonomously and provide a complete summary of what you accomplished."""

        response_text = ""
        if provider_name == "gemini":
            client = await get_gemini_client(service)
            model_name = service.config.get("model", "G_2_5_FLASH")
            model = resolve_gemini_model(model_name)
            chat = client.start_chat(model=model)
            response = await asyncio.wait_for(chat.send_message(prompt), timeout=120)
            response_text = response.text or ""
        else:
            provider_svc = get_provider_service(provider_name)
            if not provider_svc:
                return f"Delegation error: Provider '{provider_name}' not found."
            messages = [{"role": "user", "content": prompt}]
            accumulated_text = ""
            try:
                async for chunk in provider_svc.generate_stream(
                    messages,
                    service.config.get("model", ""),
                    proxy=service.config.get("proxy"),
                ):
                    if "text" in chunk:
                        accumulated_text += chunk["text"]
                    if "error" in chunk:
                        return f"Delegation error: {chunk['error']}"
            except Exception as e:
                return f"Delegation error: {str(e)}"
            response_text = accumulated_text

        for _ in range(8):
            tool_call = temp_agent.parse_tool_call(response_text)
            if not tool_call:
                break
            tool_result, _ = await temp_agent.execute_tool(tool_call["name"], tool_call["args"])
            if provider_name == "gemini":
                response = await asyncio.wait_for(chat.send_message(tool_result), timeout=120)
                response_text = response.text or ""
            else:
                followup_messages = [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": response_text},
                    {"role": "tool", "content": tool_result},
                ]
                accumulated_text = ""
                async for chunk in provider_svc.generate_stream(
                    followup_messages,
                    service.config.get("model", ""),
                    proxy=service.config.get("proxy"),
                ):
                    if "text" in chunk:
                        accumulated_text += chunk["text"]
                response_text = accumulated_text

        return f"**Sub-agent Result:**\n{response_text}"
    except asyncio.TimeoutError:
        return "Error: Delegated task timed out"
    except Exception as exc:
        return f"Error in delegated task: {str(exc)}"
