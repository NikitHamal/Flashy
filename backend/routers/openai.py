import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..server import ChatCompletionRequest, OpenAIAdapter, ProviderCatalog

logger = logging.getLogger("flashy.openai")
router = APIRouter()

_catalog = ProviderCatalog()
_adapter = OpenAIAdapter()


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
        return StreamingResponse(
            _adapter.stream_openai_events(request, provider_request),
            media_type="text/event-stream",
        )

    completion = await _adapter.gateway.complete(provider_request)
    return _adapter.to_openai_response(request, completion)


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
    return _adapter.to_responses_response(request, completion)
