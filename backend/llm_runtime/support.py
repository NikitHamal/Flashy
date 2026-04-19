import asyncio

from ..agents import agent_registry
from ..coding_agent import CodingAgent
from ..config import load_config
from ..image_service import get_image_service, ImageResult, ImageType
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
        proxy=service.config.get("proxy"),
        chat_type=chat_type,
        thinking_enabled=thinking_enabled,
        thinking_mode=thinking_mode,
        files=files,
        conversation=conversation,
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


async def handle_image_generation(service, args: dict, provider_name: str, chat_session, session_id: str) -> str:
    prompt = args.get("prompt", "")
    save_to_project = args.get("save_to_project", False)
    filename = args.get("filename")

    if provider_name != "gemini":
        return "Image generation only supported on Gemini provider."

    image_prompt = f"Generate an image: {prompt}. Use your image generation capabilities."
    try:
        image_response = await send_with_retry(service, chat_session, image_prompt, session_id=session_id)
    except Exception as exc:
        return f"Image generation failed: {str(exc)}"

    if not hasattr(image_response, "images") or not image_response.images:
        return "Image generation requested but no images returned."

    results = []
    for img in image_response.images:
        img_url = getattr(img, "url", "")
        if not img_url:
            continue

        img_type = "generated" if "generated" in type(img).__name__.lower() else "web"
        img_svc = get_image_service(service.workspace_path)
        img_result = ImageResult(
            url=img_url,
            image_type=ImageType.GENERATED if img_type == "generated" else ImageType.WEB,
            title=getattr(img, "title", None),
            alt=getattr(img, "alt", None),
        )
        img_svc.generated_images.append(img_result)

        if save_to_project and service.workspace_path:
            success, save_path = await img_svc.save_image_from_url(img_url, filename)
            if success:
                img_result.local_path = save_path
                img_result.saved = True
                results.append(f"Image generated and saved to: {save_path}")
            else:
                results.append(f"Image generated but failed to save: {save_path}")
        else:
            results.append(f"Image generated: {img_url[:60]}...")

    return "\n".join(results) if results else "Image generation completed with no results."


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
            return "Delegation currently optimized for Gemini provider."

        for _ in range(8):
            tool_call = temp_agent.parse_tool_call(response_text)
            if not tool_call:
                break
            tool_result, _ = await temp_agent.execute_tool(tool_call["name"], tool_call["args"])
            response = await asyncio.wait_for(chat.send_message(tool_result), timeout=120)
            response_text = response.text or ""

        return f"**Sub-agent Result:**\n{response_text}"
    except asyncio.TimeoutError:
        return "Error: Delegated task timed out"
    except Exception as exc:
        return f"Error in delegated task: {str(exc)}"
