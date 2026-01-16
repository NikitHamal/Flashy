from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body, Request
from typing import List, Optional
import os
import shutil
import time
import tempfile
import json
from fastapi.responses import StreamingResponse
from ..storage import save_chat_message, get_chat_history, get_all_chats, delete_chat, get_workspace as get_workspace_data
# We'll need access to GeminiService instance

router = APIRouter()

# Use system temp directory
UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "flashy_uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.post("/chat/interrupt")
async def interrupt_chat(session_id: str = Body(..., embed=True), request: Request = None):
    # Access service from app state
    if request:
        request.app.state.gemini_service.interrupt_session(session_id)
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
