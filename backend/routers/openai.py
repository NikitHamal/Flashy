import logging
import time
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from ..server import ChatCompletionRequest, OpenAIAdapter, ProviderCatalog
from ..server.cost import format_cost_log

logger = logging.getLogger("flashy.openai")
router = APIRouter()

_catalog = ProviderCatalog()
_adapter = OpenAIAdapter()


async def _stream_with_cost_log(
    stream_gen: AsyncGenerator[str, None],
    provider: str,
    model: str,
) -> AsyncGenerator[str, None]:
    captured_usage = None
    async for chunk in stream_gen:
        if chunk.startswith("data: [DONE]"):
            if captured_usage:
                pt = captured_usage.get("prompt_tokens", 0) or 0
                ct = captured_usage.get("completion_tokens", 0) or 0
                logger.info(format_cost_log(provider, model, pt, ct, pt + ct))
            yield chunk
            return
        yield chunk
        if chunk.startswith('data: ') and '"usage"' in chunk:
            try:
                import json
                data = json.loads(chunk[6:])
                if data.get("usage"):
                    captured_usage = data["usage"]
            except Exception:
                pass


class ResponseMessage(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]], None] = None


class ResponseRequest(BaseModel):
    model: str
    input: Optional[Any] = None
    text: Optional[str] = None
    stream: bool = False
    temperature: float = 0.7
    top_p: float = 1.0
    max_tokens: Optional[int] = None
    thinking_enabled: bool = True
    thinking_mode: str = "Auto"


@router.get("/v1/models")
async def list_models():
    """List all available provider models in OpenAI-compatible format."""
    return await _catalog.list_models()


@router.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """Provider-only OpenAI-compatible chat completions endpoint."""
    provider_request = _adapter.build_provider_request(request)
    logger.info(
        "[OPENAI] provider=%s model=%s stream=%s tools=%s",
        provider_request.provider,
        provider_request.model,
        request.stream,
        len(request.tools or []),
    )

    if request.stream:
        stream_gen = _adapter.stream_openai_events(request, provider_request)
        return StreamingResponse(
            _stream_with_cost_log(stream_gen, provider_request.provider, provider_request.model),
            media_type="text/event-stream",
        )

    completion = await _adapter.gateway.complete(provider_request)
    response = _adapter.to_openai_response(request, completion)
    logger.info(
        format_cost_log(
            provider_request.provider,
            provider_request.model,
            completion.input_tokens or 0,
            completion.output_tokens or 0,
            (completion.input_tokens or 0) + (completion.output_tokens or 0),
        )
    )
    return response


@router.post("/v1/responses")
async def responses(request: ResponseRequest):
    """OpenAI Responses API compatible endpoint."""
    messages = []
    if request.input:
        if isinstance(request.input, list):
            for msg in request.input:
                if isinstance(msg, dict):
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        text_content = ""
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "input_text":
                                text_content += block.get("text", "")
                        messages.append({"role": role, "content": text_content})
                    else:
                        messages.append({"role": role, "content": str(content) if content else ""})
        elif isinstance(request.input, dict) and "messages" in request.input:
            for msg in request.input.get("messages", []):
                if isinstance(msg, dict):
                    messages.append(msg)
    elif request.text:
        messages = [{"role": "user", "content": request.text}]

    chat_request = ChatCompletionRequest(
        model=request.model,
        messages=messages,
        stream=request.stream,
        temperature=request.temperature,
        top_p=request.top_p,
        max_tokens=request.max_tokens,
        thinking_enabled=request.thinking_enabled,
        thinking_mode=request.thinking_mode,
    )

    provider_request = _adapter.build_provider_request(chat_request)
    logger.info(
        "[RESPONSES] provider=%s model=%s stream=%s",
        provider_request.provider,
        provider_request.model,
        request.stream,
    )

    if request.stream:
        return StreamingResponse(
            _adapter.stream_responses_events(chat_request, provider_request),
            media_type="text/event-stream",
        )

    completion = await _adapter.gateway.complete(provider_request)
    response = _adapter.to_responses_response(request, completion)
    logger.info(
        format_cost_log(
            provider_request.provider,
            provider_request.model,
            completion.input_tokens or 0,
            completion.output_tokens or 0,
            (completion.input_tokens or 0) + (completion.output_tokens or 0),
        )
    )
    return response


@router.get("/v1/{provider_name}/models")
async def provider_models(provider_name: str):
    """List models for a specific provider."""
    from ..providers import get_provider_service
    service = get_provider_service(provider_name)
    if not service:
        return JSONResponse(status_code=404, content={"error": f"Provider '{provider_name}' not found"})
    models = await service.get_models()
    data = []
    for m in models:
        data.append({
            "id": m.get("id", m.get("model", "")),
            "object": "model",
            "created": int(time.time()),
            "owned_by": provider_name,
        })
    return {"object": "list", "data": data}


@router.post("/v1/{provider_name}/chat/completions")
async def provider_chat_completions(provider_name: str, request: Request):
    """Chat completions routed to a specific provider via URL path."""
    body = await request.json()
    model = body.get("model", "")
    if "/" not in model:
        body["model"] = f"{provider_name}/{model}"
    chat_request = ChatCompletionRequest(**body)
    provider_request = _adapter.build_provider_request(chat_request)
    logger.info(
        "[%s] model=%s stream=%s tools=%s",
        provider_name.upper(),
        provider_request.model,
        body.get("stream"),
        len(body.get("tools") or []),
    )

    if body.get("stream"):
        stream_gen = _adapter.stream_openai_events(chat_request, provider_request)
        return StreamingResponse(
            _stream_with_cost_log(stream_gen, provider_request.provider, provider_request.model),
            media_type="text/event-stream",
        )

    completion = await _adapter.gateway.complete(provider_request)
    response = _adapter.to_openai_response(chat_request, completion)
    logger.info(
        format_cost_log(
            provider_request.provider,
            provider_request.model,
            completion.input_tokens or 0,
            completion.output_tokens or 0,
            (completion.input_tokens or 0) + (completion.output_tokens or 0),
        )
    )
    return response
