"""
Qwen-Code Integration Router

This module provides integration with qwen-code CLI using free providers
(Qwen and DeepInfra) without requiring API keys.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List
import json
import asyncio

router = APIRouter(prefix="/api/qwen-code", tags=["qwen-code"])

AVAILABLE_PROVIDERS = {
    "qwen": {
        "name": "Qwen (Free)",
        "models": [
            {"id": "qwen3.6-plus", "name": "Qwen 3.6 Plus"},
            {"id": "qwen3.5-plus", "name": "Qwen 3.5 Plus"},
            {"id": "qwen3.5-flash", "name": "Qwen 3.5 Flash"},
            {"id": "qwen3-coder-plus", "name": "Qwen 3 Coder Plus"},
        ]
    },
    "deepinfra": {
        "name": "DeepInfra (Free)",
        "models": [
            {"id": "meta-llama/Meta-Llama-3-8B-Instruct", "name": "Llama 3 (8B)"},
            {"id": "meta-llama/Meta-Llama-3-70B-Instruct", "name": "Llama 3 (70B)"},
            {"id": "mistralai/Mistral-7B-Instruct-v0.2", "name": "Mistral 7B v0.2"},
            {"id": "Qwen/Qwen2.5-72B-Instruct", "name": "Qwen 2.5 (72B)"},
            {"id": "meta-llama/Llama-3.1-70B-Instruct", "name": "Llama 3.1 (70B)"},
            {"id": "google/gemma-2-27b-it", "name": "Gemma 2 (27B)"},
        ]
    }
}

@router.get("/providers")
async def get_providers():
    """Get available free providers and models."""
    return {"providers": AVAILABLE_PROVIDERS}

@router.get("/providers/{provider}/models")
async def get_models(provider: str):
    """Get models for a specific provider."""
    if provider not in AVAILABLE_PROVIDERS:
        raise HTTPException(f"Provider '{provider}' not found. Available: {list(AVAILABLE_PROVIDERS.keys())}")
    return {"models": AVAILABLE_PROVIDERS[provider]["models"]}

@router.post("/chat")
async def chat(
    request: Request,
    message: str,
    provider: str = "qwen",
    model: str = "qwen3.5-plus",
    session_id: Optional[str] = None,
    workspace: Optional[str] = None
):
    """
    Chat with qwen-code using free providers.
    
    - message: The user's message
    - provider: 'qwen' or 'deepinfra'
    - model: Model ID (depends on provider)
    - session_id: Optional session ID for continuity
    - workspace: Optional workspace path for file operations
    """
    if provider not in AVAILABLE_PROVIDERS:
        raise HTTPException(f"Invalid provider. Use: {', '.join(AVAILABLE_PROVIDERS.keys())}")
    
    valid_models = [m["id"] for m in AVAILABLE_PROVIDERS[provider]["models"]]
    if model not in valid_models:
        raise HTTPException(f"Invalid model for {provider}. Valid: {valid_models}")
    
    if not session_id:
        session_id = f"qwen-code-{provider}-{model}"
    
    llm_service = request.app.state.llm_service
    
    if workspace:
        llm_service.set_workspace(workspace, session_id)
    
    async def generate():
        from ..config import load_config
        config = load_config()
        old_provider = config.get("active_provider", "gemini")
        old_model = config.get("model", "G_2_5_FLASH")
        
        config["active_provider"] = provider
        config["model"] = model
        
        try:
            async for chunk in llm_service.generate_response(message, session_id=session_id):
                yield f"data: {json.dumps(chunk)}\n\n"
        finally:
            config["active_provider"] = old_provider
            config["model"] = old_model
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@router.post("/chat/stream")
async def chat_stream(
    request: Request,
    message: str,
    provider: str = "qwen",
    model: str = "qwen3.5-plus",
    session_id: Optional[str] = None
):
    """Streaming chat endpoint with provider/model selection."""
    return await chat(request, message, provider, model, session_id)

@router.get("/sessions")
async def list_sessions(request: Request):
    """List active chat sessions."""
    llm_service = request.app.state.llm_service
    return {"sessions": list(llm_service.sessions.keys())}

@router.delete("/sessions/{session_id}")
async def delete_session(request: Request, session_id: str):
    """Delete a chat session."""
    llm_service = request.app.state.llm_service
    if session_id in llm_service.sessions:
        del llm_service.sessions[session_id]
    if session_id in llm_service.provider_sessions:
        del llm_service.provider_sessions[session_id]
    return {"status": "deleted", "session_id": session_id}

@router.post("/sessions/{session_id}/reset")
async def reset_session(request: Request, session_id: str):
    """Reset a chat session."""
    llm_service = request.app.state.llm_service
    if session_id in llm_service.agents:
        llm_service.agents[session_id].reset_context()
    return {"status": "reset", "session_id": session_id}