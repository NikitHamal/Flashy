from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Body, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .gemini_service import GeminiService
from .config import load_config, save_config
from . import storage 
from .storage import save_chat_message, get_chat_history, get_all_chats, delete_chat, get_workspace as get_workspace_data, add_workspace
from .websocket_manager import ws_manager, MessageType
import uvicorn
import shutil
import os
import tempfile
import time
import httpx
import uuid
import json
import asyncio
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
                gemini_service.set_workspace(ws['path'], workspace_id=workspace_id)

        # Save user message using parts format
        save_chat_message(session_id, "user", parts=[{"type": "text", "content": message}], workspace_id=workspace_id)
        
        async def response_generator():
            try:
                async for chunk in gemini_service.generate_response(message, session_id, files=file_paths):
                    if "tool_call" in chunk:
                        yield json.dumps(chunk) + "\n"
                    elif "tool_result" in chunk:
                        yield json.dumps(chunk) + "\n"
                    else:
                        # Rewrite image URLs if present in the final chunk
                        if chunk.get("images"):
                            chunk["images"] = [f"/proxy_image?url={url}" for url in chunk["images"]]
                        
                        yield json.dumps(chunk) + "\n"
            except Exception as e:
                print(f"Error in streaming: {e}")
                yield json.dumps({"text": f"\n\n**STREAM ERROR:** {str(e)}", "is_final": True}) + "\n"
            finally:
                # Cleanup files after sending
                for path in file_paths:
                    try: os.remove(path)
                    except: pass

        return StreamingResponse(response_generator(), media_type="application/x-ndjson")
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/interrupt")
async def interrupt_chat(session_id: str = Body(..., embed=True)):
    gemini_service.interrupt_session(session_id)
    return {"message": "Interrupted"}

class CloneRequest(BaseModel):
    url: str
    parent_path: str
    name: Optional[str] = None

@app.post("/git/clone")
async def api_git_clone(request: CloneRequest):
    try:
        from .git_manager import GitManager
        
        if request.name:
            repo_name = request.name
        else:
            # Determine repo name from URL robustly
            clean_url = request.url.strip().rstrip("/")
            repo_name = clean_url.split("/")[-1].replace(".git", "")
        
        if not repo_name:
            raise HTTPException(status_code=400, detail="Could not determine repository name from URL")
            
        target_path = os.path.join(request.parent_path, repo_name)
        
        if os.path.exists(target_path) and os.listdir(target_path):
            raise HTTPException(status_code=400, detail=f"Directory already exists and is not empty: {target_path}")
        
        git = GitManager() # No workspace yet
        from .config import load_config
        pat = load_config().get("GITHUB_PAT")
        
        result = git.clone_repo(request.url, target_path, pat=pat)
        if "Error" in result:
            raise HTTPException(status_code=500, detail=result)
            
        # Add as workspace
        ws = storage.add_workspace(target_path)
        gemini_service.set_workspace(target_path, workspace_id=ws['id'])
        return ws
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Clone error: {e}")
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
    if not os.path.exists(data.path):
        raise HTTPException(status_code=400, detail="Path does not exist")
        
    # Get or create workspace ID
    ws = storage.add_workspace(data.path)
    
    # Set it in gemini service with the correct ID
    result = gemini_service.set_workspace(ws['path'], workspace_id=ws['id'])
    
    if "Error" in result:
        raise HTTPException(status_code=400, detail=result)
        
    return {"message": result, "path": gemini_service.get_workspace(), "id": ws['id']}

@app.get("/workspaces")
async def api_get_workspaces():
    return storage.get_workspaces()

@app.delete("/workspaces/{workspace_id}")
async def api_delete_workspace(workspace_id: str):
    if storage.delete_workspace(workspace_id):
        return {"message": "Workspace deleted"}
    raise HTTPException(status_code=404, detail="Workspace not found")

@app.post("/workspaces")
async def api_add_workspace(path: str = Body(..., embed=True)):
    if not os.path.exists(path):
        raise HTTPException(status_code=400, detail="Path does not exist")
    return storage.add_workspace(path)

@app.get("/workspaces/{workspace_id}/sessions")
async def api_get_workspace_sessions(workspace_id: str):
    return storage.get_workspace_sessions(workspace_id)

def _run_isolated_picker():
    """Run the folder picker in a separate process to avoid thread conflicts."""
    import subprocess
    import sys
    try:
        result = subprocess.run(
            [sys.executable, "backend/picker.py"],
            capture_output=True,
            text=True,
            timeout=120
        )
        output = result.stdout.strip()
        if output == "CANCELLED":
            return None
        if output.startswith("ERROR:"):
            raise Exception(output)
        return output
    except Exception as e:
        print(f"Isolated picker error: {e}")
        return None

@app.post("/workspace/pick")
def pick_workspace():
    path = _run_isolated_picker()
    if path:
        ws = storage.add_workspace(path)
        gemini_service.set_workspace(path, workspace_id=ws['id'])
        return ws
    return {"message": "Cancelled"}

@app.post("/path/pick")
def api_pick_path():
    """Pick a path without adding it as a workspace."""
    path = _run_isolated_picker()
    return {"path": path}

class CheckoutRequest(BaseModel):
    branch: str

@app.post("/workspace/{workspace_id}/git/checkout")
async def git_checkout(workspace_id: str, request: CheckoutRequest):
    try:
        ws = get_workspace_data(workspace_id)
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        from .git_manager import GitManager
        git = GitManager(ws['path'])
        result = git.checkout(request.branch)
        
        if "Error" in result:
            raise HTTPException(status_code=400, detail=result)
            
        return {"message": f"Switched to branch {request.branch}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workspace/{workspace_id}/git/pull")
async def git_pull(workspace_id: str):
    try:
        ws = get_workspace_data(workspace_id)
        if not ws: raise HTTPException(status_code=404, detail="Workspace not found")
        from .git_manager import GitManager
        git = GitManager(ws['path'])
        result = git.pull()
        if "failed" in result.lower(): raise HTTPException(status_code=400, detail=result)
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workspace/{workspace_id}/git/push")
async def git_push(workspace_id: str):
    try:
        ws = get_workspace_data(workspace_id)
        if not ws: raise HTTPException(status_code=404, detail="Workspace not found")
        from .git_manager import GitManager
        git = GitManager(ws['path'])
        from .config import load_config
        pat = load_config().get("GITHUB_PAT")
        result = git.push(pat=pat)
        if "failed" in result.lower(): raise HTTPException(status_code=400, detail=result)
        return {"message": result}
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

@app.get("/workspace/{workspace_id}/git")
async def get_git_info(workspace_id: str):
    try:
        ws = get_workspace_data(workspace_id)
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        from .git_manager import GitManager
        git = GitManager(ws['path'])
        
        if not git.is_repo():
            return {"is_repo": False}
        
        return {
            "is_repo": True,
            "status": git.get_status(),
            "branches": git.get_branches(),
            "log": git.get_log(10)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workspace/{workspace_id}/plan")
async def get_plan(workspace_id: str):
    try:
        ws = get_workspace_data(workspace_id)
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        plan_path = os.path.join(ws['path'], "plan.md")
        if os.path.exists(plan_path):
            with open(plan_path, 'r', encoding='utf-8') as f:
                return {"content": f.read()}
        return {"content": None}
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
    Secure_1PSIDCC: Optional[str] = None
    GITHUB_PAT: Optional[str] = None
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


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time communication.
    
    Message Types (Client -> Server):
    - chat_message: {type: "chat_message", message: str, workspace_id: str, files: []}
    - interrupt: {type: "interrupt"}
    - subscribe_terminal: {type: "subscribe_terminal", terminal_id: str}
    - terminal_input: {type: "terminal_input", terminal_id: str, input: str}
    - run_command: {type: "run_command", command: str, cwd: str}
    
    Message Types (Server -> Client):
    - thought: {type: "thought", content: str}
    - text: {type: "text", content: str, is_final: bool}
    - tool_call: {type: "tool_call", name: str, args: {}}
    - tool_result: {type: "tool_result", content: str}
    - terminal_output: {type: "terminal_output", terminal_id: str, output: str}
    - terminal_exit: {type: "terminal_exit", terminal_id: str, exit_code: int}
    - error: {type: "error", message: str}
    - stream_end: {type: "stream_end"}
    """
    # Get workspace_id from query params if provided
    workspace_id = websocket.query_params.get("workspace_id")
    
    connection_id = await ws_manager.connect(websocket, session_id, workspace_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "chat_message":
                # Check if an agent is already working for this session
                # If so, we'll try to acquire the lock. If locked, we inform the user.
                lock = ws_manager.get_session_lock(session_id)
                if lock.locked():
                    await ws_manager.send_to_connection(
                        connection_id,
                        MessageType.ERROR,
                        {"message": "Agent is already busy with another request in this session. Please wait."}
                    )
                    continue

                # Run chat handler in a dedicated task so we can track and cancel it
                chat_task = asyncio.create_task(
                    handle_ws_chat(
                        connection_id=connection_id,
                        session_id=session_id,
                        message=data.get("message", ""),
                        workspace_id=data.get("workspace_id") or workspace_id,
                        files=data.get("files", [])
                    )
                )
                ws_manager.register_session_task(session_id, chat_task)
            
            elif msg_type == "interrupt":
                # Interrupt the current agent session
                gemini_service.interrupt_session(session_id)
                ws_manager.cancel_session_task(session_id)
                await ws_manager.send_to_connection(
                    connection_id, 
                    MessageType.TEXT, 
                    {"content": "\n\n*Agent interrupted by user.*", "is_final": True}
                )
            
            elif msg_type == "ping":
                # Heartbeat
                await ws_manager.send_to_connection(
                    connection_id,
                    MessageType.PONG,
                    {"timestamp": time.time()}
                )
            
            elif msg_type == "subscribe_terminal":
                # Subscribe to terminal output
                terminal_id = data.get("terminal_id")
                if terminal_id:
                    ws_manager.subscribe_to_terminal(connection_id, terminal_id)
            
            elif msg_type == "terminal_input":
                # Send input to a running terminal
                terminal_id = data.get("terminal_id")
                input_text = data.get("input", "")
                if terminal_id:
                    await ws_manager.send_terminal_input(terminal_id, input_text)
            
            elif msg_type == "run_command":
                # Run a command with streaming output
                command = data.get("command", "")
                cwd = data.get("cwd")
                terminal_id = data.get("terminal_id") or f"term_{uuid.uuid4().hex[:8]}"
                
                # Auto-subscribe the requester
                ws_manager.subscribe_to_terminal(connection_id, terminal_id)
                
                # Run command in background
                asyncio.create_task(
                    ws_manager.run_streaming_command(command, terminal_id, cwd)
                )
                
                # Send back the terminal_id
                await ws_manager.send_to_connection(
                    connection_id,
                    MessageType.TERMINAL_OUTPUT,
                    {"terminal_id": terminal_id, "output": f"$ {command}\n", "is_error": False}
                )
            
            elif msg_type == "kill_terminal":
                terminal_id = data.get("terminal_id")
                if terminal_id:
                    await ws_manager.kill_terminal(terminal_id)
            
            else:
                await ws_manager.send_to_connection(
                    connection_id,
                    MessageType.ERROR,
                    {"message": f"Unknown message type: {msg_type}"}
                )
    
    except WebSocketDisconnect:
        await ws_manager.disconnect(connection_id)
    except Exception as e:
        print(f"[WS] Error in connection {connection_id}: {e}")
        await ws_manager.disconnect(connection_id)


async def handle_ws_chat(connection_id: str, session_id: str, message: str, workspace_id: str = None, files: list = None):
    """Handle a chat message received via WebSocket."""
    # Acquire session lock to prevent concurrent runs
    lock = ws_manager.get_session_lock(session_id)
    
    async with lock:
        file_paths = []
        try:
            # Set workspace if provided
            if workspace_id:
                ws = get_workspace_data(workspace_id)
                if ws:
                    gemini_service.set_workspace(ws['path'], workspace_id=workspace_id)
            
            # Save user message
            save_chat_message(session_id, "user", parts=[{"type": "text", "content": message}], workspace_id=workspace_id)
            
            # Process uploaded files if any (base64 encoded)
            if files:
                for file_data in files:
                    if isinstance(file_data, dict) and 'content' in file_data:
                        import base64
                        filename = file_data.get('name', f'upload_{uuid.uuid4().hex[:8]}')
                        file_path = os.path.join(UPLOAD_DIR, filename)
                        with open(file_path, 'wb') as f:
                            f.write(base64.b64decode(file_data['content']))
                        file_paths.append(file_path)
            
            # Stream response via WebSocket
            async for chunk in gemini_service.generate_response(message, session_id, files=file_paths):
                # Check for task cancellation (standard asyncio way)
                # if asyncio.current_task().cancelled():
                #     break
                    
                if "thought" in chunk:
                    await ws_manager.send_to_session(
                        session_id,
                        MessageType.THOUGHT,
                        {"content": chunk["thought"]}
                    )
                elif "tool_call" in chunk:
                    await ws_manager.send_to_session(
                        session_id,
                        MessageType.TOOL_CALL,
                        {"name": chunk["tool_call"]["name"], "args": chunk["tool_call"]["args"]}
                    )
                elif "tool_result" in chunk:
                    await ws_manager.send_to_session(
                        session_id,
                        MessageType.TOOL_RESULT,
                        {"content": chunk["tool_result"]}
                    )
                else:
                    # Text response
                    await ws_manager.send_to_session(
                        session_id,
                        MessageType.TEXT,
                        {
                            "content": chunk.get("text", ""),
                            "images": chunk.get("images", []),
                            "is_final": chunk.get("is_final", False)
                        }
                    )
                    
        except asyncio.CancelledError:
            print(f"[WS] Chat task explicitly cancelled for session {session_id}")
            await ws_manager.send_to_session(
                session_id,
                MessageType.TEXT,
                {"content": "\n\n*Agent task cancelled (connection lost or interrupted).*", "is_final": True}
            )
        except Exception as e:
            print(f"[WS] Chat error: {e}")
            await ws_manager.send_to_session(
                session_id,
                MessageType.ERROR,
                {"message": str(e)}
            )
        finally:
            # Always unregister task
            ws_manager.unregister_session_task(session_id)
            
            # Signal end of stream
            try:
                await ws_manager.send_to_session(session_id, MessageType.STREAM_END, {})
            except:
                pass
            
            # Cleanup files
            for path in file_paths:
                try:
                    os.remove(path)
                except:
                    pass


# Serve static files from the frontend directory
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Disable reload to ensure absolute stability during file uploads in this local tool
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
