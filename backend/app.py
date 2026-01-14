from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .gemini_service import GeminiService
from .config import load_config, save_config
from . import storage 
from .storage import save_chat_message, get_chat_history, get_all_chats, delete_chat, get_workspace as get_workspace_data, add_workspace
import uvicorn
import shutil
import os
import tempfile
import time
import httpx
import uuid
import json
from typing import List, Optional
from fastapi.responses import StreamingResponse, Response, FileResponse, JSONResponse

app = FastAPI()

@app.exception_handler(404)
async def spa_fallback_handler(request: Request, __):
    # If the request is for an API route or looks like a static file (has extension), return 404
    api_prefixes = ("/chat", "/history", "/workspace", "/workspaces", "/proxy_image", "/config")
    path = request.url.path
    
    if path.startswith(api_prefixes) or "." in path.split("/")[-1]:
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
        
    # Otherwise, return index.html for SPA support
    return FileResponse("frontend/index.html")

# Use system temp directory to avoid triggering uvicorn reload
UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "flashy_uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(content="", media_type="image/x-icon")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

gemini_service = GeminiService()

@app.post("/chat")
async def chat(
    message: str = Form(...),
    session_id: Optional[str] = Form(None),
    workspace_id: Optional[str] = Form(None),
    files: List[UploadFile] = File(None)
):
    try:
        if not session_id:
            session_id = f"session_{int(time.time()*1000)}"
            
        file_paths = []
        if files:
            for file in files:
                file_path = os.path.join(UPLOAD_DIR, file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                file_paths.append(file_path)
            
        if workspace_id:
            ws = get_workspace_data(workspace_id)
            if ws:
                gemini_service.set_workspace(ws['path'])

        # Save user message
        save_chat_message(session_id, "user", message, workspace_id=workspace_id)
        
        async def response_generator():
            full_text = ""
            tool_outputs = []
            last_tool_call = None
            
            async for chunk in gemini_service.generate_response(message, session_id, files=file_paths):
                if "tool_call" in chunk:
                    last_tool_call = chunk["tool_call"]
                    yield json.dumps(chunk) + "\n"
                elif "tool_result" in chunk:
                    tool_outputs.append({
                        "tool": last_tool_call["name"],
                        "args": last_tool_call["args"],
                        "result": chunk["tool_result"]
                    })
                    yield json.dumps(chunk) + "\n"
                else:
                    text = chunk.get("text", "")
                    full_text += text
                    # Rewrite image URLs if present in the final chunk
                    if chunk.get("images"):
                        chunk["images"] = [f"/proxy_image?url={url}" for url in chunk["images"]]
                    
                    yield json.dumps(chunk) + "\n"
                
            # Save AI message when done
            save_chat_message(session_id, "ai", full_text, tool_outputs=tool_outputs, workspace_id=workspace_id)
            
            # Cleanup files after sending
            for path in file_paths:
                try: os.remove(path)
                except: pass

        return StreamingResponse(response_generator(), media_type="application/x-ndjson")
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def list_chats():
    return get_all_chats()

@app.get("/history/{session_id}")
async def get_chat(session_id: str):
    history = get_chat_history(session_id)
    if not history:
        raise HTTPException(status_code=404, detail="Chat not found")
    return history

@app.delete("/history/{session_id}")
async def remove_chat(session_id: str):
    if delete_chat(session_id):
        return {"message": "Chat deleted"}
    raise HTTPException(status_code=404, detail="Chat not found")

class WorkspaceUpdate(BaseModel):
    path: str

@app.get("/workspace")
async def get_workspace():
    return {"path": gemini_service.get_workspace()}

@app.post("/workspace")
async def set_workspace(data: WorkspaceUpdate):
    result = gemini_service.set_workspace(data.path)
    if "Error" in result:
        raise HTTPException(status_code=400, detail=result)
    return {"message": result, "path": gemini_service.get_workspace()}

@app.get("/workspaces")
async def api_get_workspaces():
    return storage.get_workspaces()

@app.post("/workspaces")
async def api_add_workspace(path: str = Body(..., embed=True)):
    if not os.path.exists(path):
        raise HTTPException(status_code=400, detail="Path does not exist")
    return storage.add_workspace(path)

@app.get("/workspaces/{workspace_id}/sessions")
async def api_get_workspace_sessions(workspace_id: str):
    return storage.get_workspace_sessions(workspace_id)

@app.post("/workspace/pick")
async def pick_workspace():
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        path = filedialog.askdirectory()
        root.destroy()
        
        if path:
            # Register workspace and return it
            ws = storage.add_workspace(path)
            # Update agent workspace path
            gemini_service.set_workspace(path)
            return ws
        return {"message": "Cancelled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workspace/{workspace_id}/explorer")
async def get_explorer(workspace_id: str):
    try:
        ws = get_workspace_data(workspace_id)
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        # We need to use the tools directly to get explorer data
        from .tools import Tools
        tools = Tools(ws['path'])
        return tools.get_explorer_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/proxy_image")
async def proxy_image(url: str):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            return Response(content=resp.content, media_type=resp.headers.get("Content-Type"))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
class ConfigUpdate(BaseModel):
    Secure_1PSID: str
    Secure_1PSIDTS: str
    model: Optional[str] = None

@app.get("/config")
async def get_config():
    return load_config()

@app.post("/config")
async def update_config(data: ConfigUpdate):
    current_config = load_config()
    # Update only the fields provided which are not None
    new_data = {k: v for k, v in data.dict().items() if v is not None}
    current_config.update(new_data)
    save_config(current_config)
    await gemini_service.reset()
    return {"message": "Config updated and client reset"}

# Serve static files from the frontend directory
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Disable reload to ensure absolute stability during file uploads in this local tool
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
