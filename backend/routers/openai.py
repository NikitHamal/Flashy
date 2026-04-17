import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..server import ChatCompletionRequest, OpenAIAdapter, ProviderCatalog

logger = logging.getLogger("flashy.openai")
router = APIRouter()

_catalog = ProviderCatalog()
_adapter = OpenAIAdapter()


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
