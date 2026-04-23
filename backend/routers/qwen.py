import logging
import json
import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..providers.qwen import QwenProvider

logger = logging.getLogger("flashy.qwen")
router = APIRouter()

_qwen_provider = QwenProvider()
_conversations: Dict[str, Any] = {}


class QwenStreamRequest(BaseModel):
    messages: List[Dict[str, Any]]
    model: str = "qwen3.6-max-preview"
    thinking_enabled: bool = True
    thinking_mode: str = "Auto"
    chat_type: str = "t2t"
    tools: Optional[List[Dict[str, Any]]] = None
    is_openai_pass_through: bool = False
    conversation_id: Optional[str] = None


async def _stream_qwen(request: QwenStreamRequest):
    """Stream Qwen responses as SSE events."""
    conversation_id = request.conversation_id or str(uuid.uuid4())
    conversation = _conversations.get(conversation_id)
    
    yield f"data: {json.dumps({'type': 'conversation_id', 'conversation_id': conversation_id})}\n\n"

    async for event in _qwen_provider.generate_stream(
        request.messages,
        request.model,
        thinking_enabled=request.thinking_enabled,
        thinking_mode=request.thinking_mode,
        chat_type=request.chat_type,
        tools=request.tools,
        is_openai_pass_through=request.is_openai_pass_through,
        conversation=conversation
    ):
        # Handle different event formats from QwenProvider
        if "error" in event:
            yield f"data: {json.dumps({'type': 'error', 'error': event['error']})}\n\n"
            return
        elif "thought" in event:
            yield f"data: {json.dumps({'type': 'thought', 'thought': event['thought']})}\n\n"
        elif "text" in event:
            yield f"data: {json.dumps({'type': 'text', 'text': event['text']})}\n\n"
        elif "tool_call" in event:
            yield f"data: {json.dumps({'type': 'tool_call', 'tool_call': event['tool_call']})}\n\n"
        elif "conversation" in event:
            _conversations[conversation_id] = event["conversation"]
        elif event.get("is_final"):
            yield f"data: {json.dumps({'type': 'final', 'finish_reason': event.get('finish_reason', 'stop')})}\n\n"
            return

    yield f"data: {json.dumps({'type': 'final', 'finish_reason': 'stop'})}\n\n"


@router.post("/api/qwen/stream")
async def qwen_stream(request: QwenStreamRequest):
    """Stream Qwen chat completions."""
    return StreamingResponse(
        _stream_qwen(request),
        media_type="text/event-stream",
    )


@router.get("/api/qwen/models")
async def qwen_models():
    """List available Qwen models."""
    models = await _qwen_provider.get_models()
    return {"models": models}