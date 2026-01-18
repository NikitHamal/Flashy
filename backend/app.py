from fastapi import FastAPI, UploadFile, File, Form, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, Response, FileResponse, JSONResponse
import os
import shutil
import time
import json
import asyncio
import httpx
import uuid
from typing import List, Optional

from .gemini_service import GeminiService
from .design_service import DesignService
from .storage import save_chat_message, get_workspace as get_workspace_data, add_workspace
from .websocket_manager import ws_manager, MessageType
from .routers import git_routes, workspace, chat, config, design

app = FastAPI()

# Share service instances
gemini_service = GeminiService()
design_service = DesignService()
app.state.gemini_service = gemini_service
app.state.design_service = design_service

app.include_router(git_routes.router)
app.include_router(workspace.router)
app.include_router(chat.router)
app.include_router(config.router)
app.include_router(design.router)

# Exception Handlers
@app.exception_handler(404)
async def spa_fallback_handler(request: Request, __):
    api_prefixes = ("/chat", "/history", "/workspace", "/workspaces", "/proxy_image", "/config", "/git", "/design")
    path = request.url.path
    if path.startswith(api_prefixes) or "." in path.split("/")[-1]:
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    return FileResponse("frontend/index.html")

UPLOAD_DIR = os.path.join(os.getenv("TEMP", "/tmp"), "flashy_uploads")
if not os.path.exists(UPLOAD_DIR): os.makedirs(UPLOAD_DIR)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon(): return Response(content="", media_type="image/x-icon")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Core Routes that need heavy logic or service integration ---

@app.get("/workspace")
async def get_current_workspace():
    return {"path": gemini_service.get_workspace()}

@app.post("/workspace")
async def set_workspace_route(data: workspace.WorkspaceUpdate):
    if not os.path.exists(data.path):
        raise HTTPException(status_code=400, detail="Path does not exist")
    ws = add_workspace(data.path)
    result = gemini_service.set_workspace(ws['path'], workspace_id=ws['id'])
    if "Error" in result:
        raise HTTPException(status_code=400, detail=result)
    return {"message": result, "path": gemini_service.get_workspace(), "id": ws['id']}

@app.post("/workspace/pick")
def pick_workspace_route():
    # Override router implementation to hook into service
    path = workspace._run_isolated_picker()
    if path:
        ws = add_workspace(path)
        gemini_service.set_workspace(path, workspace_id=ws['id'])
        return ws
    return {"message": "Cancelled"}

@app.post("/chat")
async def chat_endpoint(
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
                gemini_service.set_workspace(ws['path'], workspace_id=workspace_id)

        save_chat_message(session_id, "user", parts=[{"type": "text", "content": message}], workspace_id=workspace_id)
        
        async def response_generator():
            try:
                async for chunk in gemini_service.generate_response(message, session_id, files=file_paths):
                    if "tool_call" in chunk:
                        yield json.dumps(chunk) + "\n"
                    elif "tool_result" in chunk:
                        yield json.dumps(chunk) + "\n"
                    else:
                        if chunk.get("images"):
                            chunk["images"] = [f"/proxy_image?url={url}" for url in chunk["images"]]
                        yield json.dumps(chunk) + "\n"
            except Exception as e:
                print(f"Error in streaming: {e}")
                yield json.dumps({"text": f"\n\n**STREAM ERROR:** {str(e)}", "is_final": True}) + "\n"
            finally:
                for path in file_paths:
                    try: os.remove(path)
                    except: pass

        return StreamingResponse(response_generator(), media_type="application/x-ndjson")
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/proxy_image")
async def proxy_image(url: str):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            return Response(content=resp.content, media_type=resp.headers.get("Content-Type"))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# --- WebSocket ---

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    workspace_id = websocket.query_params.get("workspace_id")
    connection_id = await ws_manager.connect(websocket, session_id, workspace_id)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "chat_message":
                lock = ws_manager.get_session_lock(session_id)
                if lock.locked():
                    await ws_manager.send_to_connection(connection_id, MessageType.ERROR, {"message": "Agent is busy."})
                    continue

                chat_task = asyncio.create_task(
                    handle_ws_chat(connection_id, session_id, data.get("message", ""), data.get("workspace_id") or workspace_id, data.get("files", []))
                )
                ws_manager.register_session_task(session_id, chat_task)
            
            elif msg_type == "interrupt":
                gemini_service.interrupt_session(session_id)
                ws_manager.cancel_session_task(session_id)
                await ws_manager.send_to_connection(connection_id, MessageType.TEXT, {"content": "\n\n*Interrupted.*", "is_final": True})
            
            elif msg_type == "ping":
                await ws_manager.send_to_connection(connection_id, MessageType.PONG, {"timestamp": time.time()})
            
            elif msg_type == "subscribe_terminal":
                if data.get("terminal_id"): ws_manager.subscribe_to_terminal(connection_id, data.get("terminal_id"))
            
            elif msg_type == "terminal_input":
                if data.get("terminal_id"): await ws_manager.send_terminal_input(data.get("terminal_id"), data.get("input", ""))
            
            elif msg_type == "run_command":
                terminal_id = data.get("terminal_id") or f"term_{uuid.uuid4().hex[:8]}"
                ws_manager.subscribe_to_terminal(connection_id, terminal_id)
                asyncio.create_task(ws_manager.run_streaming_command(data.get("command", ""), terminal_id, data.get("cwd")))
                await ws_manager.send_to_connection(connection_id, MessageType.TERMINAL_OUTPUT, {"terminal_id": terminal_id, "output": f"$ {data.get('command')}\n", "is_error": False})
            
            elif msg_type == "kill_terminal":
                if data.get("terminal_id"): await ws_manager.kill_terminal(data.get("terminal_id"))

    except WebSocketDisconnect:
        await ws_manager.disconnect(connection_id)
    except Exception as e:
        print(f"[WS] Error: {e}")
        await ws_manager.disconnect(connection_id)

async def handle_ws_chat(connection_id: str, session_id: str, message: str, workspace_id: str = None, files: list = None):
    lock = ws_manager.get_session_lock(session_id)
    async with lock:
        file_paths = []
        try:
            if workspace_id:
                ws = get_workspace_data(workspace_id)
                if ws: gemini_service.set_workspace(ws['path'], workspace_id=workspace_id)
            
            save_chat_message(session_id, "user", parts=[{"type": "text", "content": message}], workspace_id=workspace_id)
            
            if files:
                import base64
                for f in files:
                    if 'content' in f:
                        fname = f.get('name', f'upload_{uuid.uuid4().hex[:8]}')
                        fpath = os.path.join(UPLOAD_DIR, fname)
                        with open(fpath, 'wb') as fo:
                            fo.write(base64.b64decode(f['content']))
                        file_paths.append(fpath)
            
            async for chunk in gemini_service.generate_response(message, session_id, files=file_paths):
                if "thought" in chunk:
                    await ws_manager.send_to_session(session_id, MessageType.THOUGHT, {"content": chunk["thought"]})
                elif "tool_call" in chunk:
                    await ws_manager.send_to_session(session_id, MessageType.TOOL_CALL, {"name": chunk["tool_call"]["name"], "args": chunk["tool_call"]["args"]})
                elif "tool_result" in chunk:
                    await ws_manager.send_to_session(session_id, MessageType.TOOL_RESULT, {"content": chunk["tool_result"]})
                else:
                    await ws_manager.send_to_session(session_id, MessageType.TEXT, {"content": chunk.get("text", ""), "images": chunk.get("images", []), "is_final": chunk.get("is_final", False)})
                    
        except asyncio.CancelledError:
            await ws_manager.send_to_session(session_id, MessageType.TEXT, {"content": "\n\n*Cancelled.*", "is_final": True})
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[WS] Error in handle_ws_chat: {e}")
            await ws_manager.send_to_session(session_id, MessageType.ERROR, {"message": str(e)})
        finally:
            ws_manager.unregister_session_task(session_id)
            try: await ws_manager.send_to_session(session_id, MessageType.STREAM_END, {})
            except: pass
            for p in file_paths: 
                try: os.remove(p) 
                except: pass

app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)