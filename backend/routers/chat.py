from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import shutil
import time
import tempfile
import json
import logging
from fastapi.responses import StreamingResponse
from ..storage import (
    save_chat_message,
    get_chat_history,
    get_all_chats,
    delete_chat,
    get_workspace as get_workspace_data,
)
from ..llm_service import LLMService

logger = logging.getLogger("flashy.chat")
router = APIRouter()

# Use system temp directory
UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "flashy_uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


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

    if provider_name == "gemini":
        return [{"id": "G_2_5_FLASH", "name": "Agent Flashy"}]

    from ..providers import get_provider_service

    provider_inst = get_provider_service(provider_name)
    if not provider_inst:
        return []

    return await provider_inst.get_models()


class GenerateRequest(BaseModel):
    messages: List[Dict[str, Any]]
    model: Optional[str] = None
    # OpenAI-format tool definitions forwarded from qwen-code
    tools: Optional[List[Dict[str, Any]]] = None
    # Advanced features
    chat_type: Optional[str] = "t2t"
    thinking_enabled: Optional[bool] = True
    thinking_mode: Optional[str] = "Auto"


@router.post("/chat/generate")
async def generate_chat(req: GenerateRequest, request: Request):
    """Simple pass-through to Qwen/DeepInfra APIs - NO Flashy agent behavior"""
    provider = request.headers.get("X-Provider", "")
    model = request.headers.get("X-Model", "")

    logger.info(f"[CHAT] /chat/generate | provider={provider} model={model} msgs={len(req.messages)} tools={len(req.tools or [])}")

    if provider in ["qwen-free", "deepinfra-free"]:
        from ..providers import get_provider_service

        actual_provider = "qwen" if provider == "qwen-free" else "deepinfra"
        provider_svc = get_provider_service(actual_provider)
        if not provider_svc:
            return {"error": f"Provider '{actual_provider}' not found"}

        full_response = ""
        collected_tool_calls = []

        async for chunk in provider_svc.generate_stream(
            req.messages, 
            model or "", 
            tools=req.tools or None,
            chat_type=req.chat_type,
            thinking_enabled=req.thinking_enabled,
            thinking_mode=req.thinking_mode
        ):
            logger.debug(f"[CHAT] chunk from provider: {list(chunk.keys())}")
            if "error" in chunk:
                logger.error(f"[CHAT] Provider error: {chunk['error']}")
                return {"error": chunk["error"]}
            if "text" in chunk:
                full_response += chunk["text"]
            if "tool_call" in chunk:
                collected_tool_calls.append(chunk["tool_call"])

        logger.info(f"[CHAT] /chat/generate done | text_len={len(full_response)} tool_calls={len(collected_tool_calls)}")

        result: Dict[str, Any] = {"text": full_response}
        if collected_tool_calls:
            result["tool_calls"] = collected_tool_calls
        return result

    return {"error": "Invalid provider. Use X-Provider: qwen-free or deepinfra-free"}


@router.post("/chat/generate/stream")
async def generate_chat_stream(req: GenerateRequest, request: Request):
    """Simple streaming pass-through to Qwen/DeepInfra APIs - NO Flashy agent behavior"""
    provider = request.headers.get("X-Provider", "")
    model = request.headers.get("X-Model", "")

    logger.info(f"[CHAT] /chat/generate/stream | provider={provider} model={model} msgs={len(req.messages)} tools={len(req.tools or [])}")

    if provider in ["qwen-free", "deepinfra-free"]:
        from ..providers import get_provider_service

        actual_provider = "qwen" if provider == "qwen-free" else "deepinfra"
        provider_svc = get_provider_service(actual_provider)
        if not provider_svc:
            return {"error": f"Provider '{actual_provider}' not found"}

        async def event_generator():
            chunk_count = 0
            text_chunks = 0
            tool_call_chunks = 0
            try:
                async for chunk in provider_svc.generate_stream(
                    req.messages, 
                    model or "", 
                    tools=req.tools or None,
                    chat_type=req.chat_type,
                    thinking_enabled=req.thinking_enabled,
                    thinking_mode=req.thinking_mode
                ):
                    chunk_count += 1
                    logger.debug(f"[CHAT] stream chunk#{chunk_count}: keys={list(chunk.keys())}")

                    if "error" in chunk:
                        logger.error(f"[CHAT] Provider stream error: {chunk['error']}")
                        yield f"data: {json.dumps({'error': chunk['error']})}\n\n"
                        break

                    if "text" in chunk:
                        text_chunks += 1
                        yield f"data: {json.dumps({'text': chunk['text']})}\n\n"

                    if "thought" in chunk:
                        yield f"data: {json.dumps({'thought': chunk['thought']})}\n\n"

                    if "tool_call" in chunk:
                        tool_call_chunks += 1
                        logger.info(f"[CHAT] Streaming tool_call: {chunk['tool_call']['name']}")
                        yield f"data: {json.dumps({'tool_call': chunk['tool_call']})}\n\n"

                    if chunk.get("is_final"):
                        logger.info(f"[CHAT] Stream finished | total_chunks={chunk_count} text_chunks={text_chunks} tool_call_chunks={tool_call_chunks}")
                        yield f"data: {json.dumps({'is_final': True, 'finish_reason': 'stop'})}\n\n"
                        break

            except Exception as e:
                logger.exception(f"[CHAT] Exception in event_generator: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            finally:
                yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    return {"error": "Invalid provider"}
