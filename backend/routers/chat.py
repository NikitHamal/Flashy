from fastapi import APIRouter, HTTPException, Body, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import logging
from fastapi.responses import StreamingResponse

from ..storage import (
    get_chat_history,
    get_all_chats,
    delete_chat,
)
from ..server import ProviderCatalog, ProviderGateway, ProviderRequest, resolve_provider_alias

logger = logging.getLogger("flashy.chat")
router = APIRouter()

_catalog = ProviderCatalog()
_gateway = ProviderGateway()


@router.post("/chat/interrupt")
async def interrupt_chat(
    session_id: str = Body(..., embed=True), request: Request = None
):
    if request:
        request.app.state.llm_service.interrupt_session(session_id)
    return {"message": "Interrupted"}


@router.get("/history")
async def list_chats():
    return get_all_chats()


@router.get("/history/{session_id}")
async def get_chat(session_id: str):
    history = get_chat_history(session_id)
    if not history:
        raise HTTPException(status_code=404, detail="Chat not found")
    return history


@router.delete("/history/{session_id}")
async def remove_chat(session_id: str):
    if delete_chat(session_id):
        return {"message": "Chat deleted"}
    raise HTTPException(status_code=404, detail="Chat not found")


@router.get("/models")
async def get_models(request: Request):
    service = request.app.state.llm_service
    provider_name = service.get_active_provider()

    if provider_name == "chat2api":
        from ..providers.chat2api import Chat2APIProvider, clear_model_cache
        clear_model_cache()
        base_url = request.app.state.llm_service.config.get("chat2api_base_url", "http://127.0.0.1:8080")
        api_key = request.app.state.llm_service.config.get("chat2api_api_key", "")
        models = await Chat2APIProvider.get_models(base_url, api_key)
        return [{"id": m["id"], "name": m["name"]} for m in models]

    if provider_name == "grok":
        from ..providers.grok import MODELS
        return [{"id": m["id"], "name": m["name"]} for m in MODELS]

    if provider_name == "zai-free":
        from ..providers.zai_free import MODELS as ZAI_FREE_MODELS
        return [{"id": m["id"], "name": m["name"]} for m in ZAI_FREE_MODELS]

    if provider_name == "glm":
        from ..providers.glm import MODELS as GLM_MODELS
        return [{"id": m["id"], "name": m["name"]} for m in GLM_MODELS]

    if provider_name == "lmarena":
        from ..providers.lmarena import LmarenaProvider
        models = await LmarenaProvider.get_models()
        return [{"id": m["id"], "name": m["name"]} for m in models]

    if provider_name == "deepseek":
        from ..providers.deepseek import MODELS as DEEPSEEK_MODELS
        return [{"id": m["id"], "name": m["name"]} for m in DEEPSEEK_MODELS]

    if provider_name == "minimax":
        from ..providers.minimax import MODELS as MINIMAX_MODELS
        return [{"id": m["id"], "name": m["name"]} for m in MINIMAX_MODELS]

    if provider_name == "mimo":
        from ..providers.mimo import MODELS as MIMO_MODELS
        return [{"id": m["id"], "name": m["name"]} for m in MIMO_MODELS]

    if provider_name == "perplexity":
        from ..providers.perplexity import MODELS as PERPLEXITY_MODELS
        return [{"id": m["id"], "name": m["name"]} for m in PERPLEXITY_MODELS]

    catalog = await _catalog.list_models([provider_name])
    return [
        {"id": item["id"].split("/", 1)[1], "name": item["name"]}
        for item in catalog["data"]
    ]


class GenerateRequest(BaseModel):
    messages: List[Dict[str, Any]]
    model: Optional[str] = None
    tools: Optional[List[Dict[str, Any]]] = None
    chat_type: str = "t2t"
    thinking_enabled: bool = True
    thinking_mode: str = "Auto"


@router.post("/chat/generate")
async def generate_chat(req: GenerateRequest, request: Request):
    """Simple provider pass-through with no Flashy agent prompt injection."""
    provider = resolve_provider_alias(request.headers.get("X-Provider", "airforce"))
    model = request.headers.get("X-Model", "") or req.model or ""

    logger.info(
        "[CHAT] /chat/generate | provider=%s model=%s msgs=%s tools=%s",
        provider,
        model,
        len(req.messages),
        len(req.tools or []),
    )

    provider_request = ProviderRequest(
        provider=provider,
        model=model,
        messages=req.messages,
        tools=req.tools,
        chat_type=req.chat_type,
        thinking_enabled=req.thinking_enabled,
        thinking_mode=req.thinking_mode,
        pass_through=True,
    )

    try:
        completion = await _gateway.complete(provider_request)
    except RuntimeError as exc:
        logger.error("[CHAT] Provider error: %s", exc)
        return {"error": str(exc)}

    result: Dict[str, Any] = {"text": completion.text}
    if completion.tool_calls:
        result["tool_calls"] = completion.tool_calls
    if completion.thoughts:
        result["thought"] = completion.thoughts
    return result


@router.post("/chat/generate/stream")
async def generate_chat_stream(req: GenerateRequest, request: Request):
    """Stream provider responses without Flashy agent behavior."""
    provider = resolve_provider_alias(request.headers.get("X-Provider", "airforce"))
    model = request.headers.get("X-Model", "") or req.model or ""

    logger.info(
        "[CHAT] /chat/generate/stream | provider=%s model=%s msgs=%s tools=%s",
        provider,
        model,
        len(req.messages),
        len(req.tools or []),
    )

    provider_request = ProviderRequest(
        provider=provider,
        model=model,
        messages=req.messages,
        tools=req.tools,
        chat_type=req.chat_type,
        thinking_enabled=req.thinking_enabled,
        thinking_mode=req.thinking_mode,
        pass_through=True,
    )

    async def event_generator():
        try:
            async for event in _gateway.stream(provider_request):
                if event["type"] == "error":
                    logger.error("[CHAT] Provider stream error: %s", event["error"])
                    yield f"data: {json.dumps({'error': event['error']})}\n\n"
                    break
                if event["type"] == "text":
                    yield f"data: {json.dumps({'text': event['text']})}\n\n"
                elif event["type"] == "thought":
                    yield f"data: {json.dumps({'thought': event['thought']})}\n\n"
                elif event["type"] == "tool_call":
                    yield f"data: {json.dumps({'tool_call': event['tool_call']})}\n\n"
                elif event["type"] == "final":
                    yield f"data: {json.dumps({'is_final': True, 'finish_reason': event.get('finish_reason', 'stop')})}\n\n"
                    break
        except Exception as exc:
            logger.exception("[CHAT] Exception in provider event stream: %s", exc)
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
