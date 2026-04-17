from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
import json
import time
import logging
import uuid
from ..providers import get_provider_service

logger = logging.getLogger("flashy.openai")
router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]], None] = None
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    # Advanced features (passed as extra fields in OpenAI request)
    chat_type: Optional[str] = "t2t"
    thinking_enabled: Optional[bool] = True
    thinking_mode: Optional[str] = "Auto"

@router.get("/v1/models")
async def list_models():
    """List all available models with enhanced metadata for Lobe Chat auto-fetching."""
    all_models = []
    providers = ["airforce", "deepinfra", "qwen", "gradient"]
    
    for provider_name in providers:
        svc = get_provider_service(provider_name)
        if not svc:
            continue
            
        try:
            models = await svc.get_models()
            for m in models:
                model_id = f"{provider_name}/{m['id']}"
                display_name = m.get("name", m["id"])
                
                # Determine capabilities based on model ID
                is_vision = any(x in model_id.lower() for x in ["vl", "vision", "gpt-4o"])
                
                all_models.append({
                    "id": model_id,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": provider_name,
                    "name": display_name,
                    "context_window": 128000 if "qwen" in model_id or "gpt-4" in model_id else 32000,
                    "capabilities": {
                        "chat": True,
                        "stream": True,
                        "vision": is_vision
                    }
                })
        except Exception as e:
            logger.warning(f"[OPENAI] Failed to fetch models for {provider_name}: {e}")

    return {"object": "list", "data": all_models}

@router.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest, request: Request):
    """OpenAI-compatible chat completions endpoint."""
    
    # Extract plain text content for our internal providers
    def get_text_content(msg: ChatMessage):
        if isinstance(msg.content, str):
            return msg.content
        if isinstance(msg.content, list):
            # Extract text parts from multi-modal content
            return "\n".join([str(p.get("text", "")) for p in msg.content if p.get("type") == "text"])
        return ""

    # Detect if this is a title generation request
    is_title_request = False
    if req.messages:
        first_msg_text = get_text_content(req.messages[0]).lower()
        if "title generator" in first_msg_text or "summarize" in first_msg_text:
            is_title_request = True

    # Extract provider and actual model name
    model_parts = req.model.split("/", 1)
    if len(model_parts) == 2:
        provider_name = model_parts[0]
        actual_model = model_parts[1]
    else:
        provider_name = "airforce"
        actual_model = req.model

    # Title generation bypass
    if is_title_request and provider_name == "qwen":
        provider_name = "airforce"
        actual_model = "gpt-4o-mini"

    logger.info(f"[OPENAI] Request | provider={provider_name} model={actual_model} stream={req.stream} title_req={is_title_request}")

    provider_svc = get_provider_service(provider_name)
    if not provider_svc:
        raise HTTPException(status_code=400, detail=f"Provider '{provider_name}' not found")

    # Format messages for internal generate_stream
    messages = []
    for m in req.messages:
        messages.append({
            "role": m.role,
            "content": get_text_content(m)
        })
    
    # Prepare kwargs for generate_stream
    kwargs = {
        "tools": req.tools,
        "proxy": request.app.state.llm_service.config.get("proxy"),
        "chat_type": req.chat_type,
        "thinking_enabled": req.thinking_enabled,
        "thinking_mode": req.thinking_mode,
        "is_openai_pass_through": True  # Signal to providers not to inject Flashy specific prompts
    }

    if not req.stream:
        # Non-streaming implementation
        full_text = ""
        openai_tool_calls = []
        async for chunk in provider_svc.generate_stream(messages, actual_model, **kwargs):
            if "error" in chunk:
                return {
                    "error": {
                        "message": chunk["error"],
                        "type": "provider_error",
                        "param": None,
                        "code": None
                    }
                }
            if "text" in chunk:
                full_text += chunk["text"]
            if "tool_call" in chunk:
                tc = chunk["tool_call"]
                openai_tool_calls.append({
                    "id": tc.get("id", f"call_{uuid.uuid4().hex[:16]}"),
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["arguments"] if isinstance(tc["arguments"], str) else json.dumps(tc["arguments"])
                    }
                })
        
        response = {
            "id": f"chatcmpl-{uuid.uuid4().hex}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": req.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": full_text if not openai_tool_calls else None
                },
                "finish_reason": "tool_calls" if openai_tool_calls else "stop"
            }]
        }
        
        if openai_tool_calls:
            response["choices"][0]["message"]["tool_calls"] = openai_tool_calls
            
        return response

    # Streaming implementation
    async def openai_event_generator():
        completion_id = f"chatcmpl-{uuid.uuid4().hex}"
        created_time = int(time.time())
        tool_call_index = 0
        
        try:
            async for chunk in provider_svc.generate_stream(messages, actual_model, **kwargs):
                if "error" in chunk:
                    error_payload = {
                        "error": {
                            "message": chunk["error"],
                            "type": "provider_error",
                            "param": None,
                            "code": None
                        }
                    }
                    yield f"data: {json.dumps(error_payload)}\n\n"
                    break
                
                delta = {}
                finish_reason = None

                if "text" in chunk:
                    delta["content"] = chunk["text"]
                
                if "tool_call" in chunk:
                    tc = chunk["tool_call"]
                    delta["tool_calls"] = [{
                        "index": tool_call_index,
                        "id": tc.get("id", f"call_{uuid.uuid4().hex[:16]}"),
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": tc["arguments"] if isinstance(tc["arguments"], str) else json.dumps(tc["arguments"])
                        }
                    }]
                    tool_call_index += 1
                    finish_reason = "tool_calls"

                if chunk.get("is_final"):
                    finish_reason = finish_reason or "stop"

                if delta or finish_reason:
                    payload = {
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": created_time,
                        "model": req.model,
                        "choices": [{
                            "index": 0,
                            "delta": delta,
                            "finish_reason": finish_reason
                        }]
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                
                if chunk.get("is_final"):
                    break
                    
        except Exception as e:
            logger.exception(f"[OPENAI] Stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(openai_event_generator(), media_type="text/event-stream")
