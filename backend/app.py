from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    Request,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, Response, FileResponse, JSONResponse
import os
import shutil
import time
import json
import asyncio
import uuid
import logging
import base64
import secrets
from typing import List, Optional

# ── Logging setup ──────────────────────────────────────────────────────────────
# flashy.* loggers print at DEBUG level so we can trace qwen-code integration.
# Set FLASHY_LOG_LEVEL=INFO in env if DEBUG is too verbose.
_log_level = os.environ.get("FLASHY_LOG_LEVEL", "DEBUG").upper()
logging.basicConfig(
    level=logging.WARNING,  # keep third-party loggers quiet
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
for _name in ("flashy.chat", "flashy.qwen", "flashy.deepinfra"):
    _logger = logging.getLogger(_name)
    _logger.setLevel(getattr(logging, _log_level, logging.DEBUG))
    if not _logger.handlers:
        _h = logging.StreamHandler()
        _h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S"))
        _logger.addHandler(_h)
    _logger.propagate = False
# ────────────────────────────────────────────────────────────────────────────────

from .llm_service import LLMService
from .storage import (
    save_chat_message,
    get_workspace as get_workspace_data,
    add_workspace,
)
from .websocket_manager import ws_manager, MessageType
from .desktop_runtime import resource_path, truthy_env, user_data_dir
from .routers import git_routes, workspace, chat, config, agents, memory
from .routers import qwen

app = FastAPI()

FRONTEND_DIR = resource_path("frontend")
FLASHY_HOST = os.environ.get("FLASHY_HOST", "127.0.0.1" if truthy_env("FLASHY_DESKTOP") else "0.0.0.0")
FLASHY_PORT = int(os.environ.get("FLASHY_PORT", "8000"))
FLASHY_RELOAD = truthy_env("FLASHY_RELOAD", default=not truthy_env("FLASHY_DESKTOP"))
AUTH_USERNAME = os.environ.get("FLASHY_DESKTOP_AUTH_USERNAME", "flashy")
AUTH_PASSWORD = os.environ.get("FLASHY_DESKTOP_AUTH_PASSWORD", "")
AUTH_ENABLED = bool(AUTH_PASSWORD)


def _auth_ok(auth_header: str | None) -> bool:
    if not AUTH_ENABLED:
        return True
    if not auth_header or not auth_header.lower().startswith("basic "):
        return False
    try:
        decoded = base64.b64decode(auth_header.split(" ", 1)[1]).decode("utf-8")
        username, password = decoded.split(":", 1)
    except Exception:
        return False
    return secrets.compare_digest(username, AUTH_USERNAME) and secrets.compare_digest(password, AUTH_PASSWORD)


def _token_ok(token: str | None) -> bool:
    return AUTH_ENABLED and bool(token) and secrets.compare_digest(token, AUTH_PASSWORD)


@app.middleware("http")
async def desktop_basic_auth(request: Request, call_next):
    # Keep the readiness probe unauthenticated so the desktop shell can detect start-up.
    if AUTH_ENABLED and request.url.path not in {"/global/health", "/healthz"}:
        if not _auth_ok(request.headers.get("authorization")):
            return Response(
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="Flashy Desktop"'},
                content="Authentication required",
            )
    return await call_next(request)


@app.get("/global/health", include_in_schema=False)
async def global_health():
    return {
        "status": "ok",
        "service": "flashy",
        "desktop": truthy_env("FLASHY_DESKTOP"),
        "data_dir": str(user_data_dir()),
    }


@app.get("/healthz", include_in_schema=False)
async def healthz():
    return {"status": "ok"}


# Share service instances
llm_service = LLMService()
app.state.llm_service = llm_service

app.include_router(git_routes.router)
app.include_router(workspace.router)
app.include_router(chat.router)
app.include_router(config.router)
app.include_router(agents.router)
app.include_router(memory.router)
app.include_router(qwen.router)

from . import qwencode_bridge

app.include_router(qwencode_bridge.router)


# Exception Handlers
@app.exception_handler(404)
async def spa_fallback_handler(request: Request, __):
    api_prefixes = (
        "/v1",
        "/chat",
        "/history",
        "/workspace",
        "/workspaces",
        "/config",
        "/git",
    )
    path = request.url.path
    if path.startswith(api_prefixes) or "." in path.split("/")[-1]:
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    return FileResponse(FRONTEND_DIR / "index.html")

UPLOAD_DIR = os.path.join(os.getenv("TEMP", "/tmp"), "flashy_uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(content="", media_type="image/x-icon")

@app.get("/qwencode", include_in_schema=False)
async def serve_qwen_code_ui():
    return FileResponse(FRONTEND_DIR / "qwencode.html")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Core Routes that need heavy logic or service integration ---


@app.get("/workspace")
async def get_current_workspace():
    return {"path": llm_service.get_workspace()}


@app.post("/workspace")
async def set_workspace_route(data: workspace.WorkspaceUpdate):
    if not os.path.exists(data.path):
        raise HTTPException(status_code=400, detail="Path does not exist")
    ws = add_workspace(data.path)
    result = llm_service.set_workspace(ws["path"], workspace_id=ws["id"])
    if "Error" in result:
        raise HTTPException(status_code=400, detail=result)
    return {"message": result, "path": llm_service.get_workspace(), "id": ws["id"]}


@app.post("/workspace/pick")
def pick_workspace_route():
    # Override router implementation to hook into service
    path = workspace._run_isolated_picker()
    if path:
        ws = add_workspace(path)
        llm_service.set_workspace(path, workspace_id=ws["id"])
        return ws
    return {"message": "Cancelled"}


@app.post("/chat")
async def chat_endpoint(
    message: str = Form(...),
    session_id: Optional[str] = Form(None),
    workspace_id: Optional[str] = Form(None),
    files: List[UploadFile] = File(None),
    chat_type: str = Form("t2t"),
    thinking_enabled: bool = Form(True),
    thinking_mode: str = Form("Auto"),
):
    print(f"[CHAT] chat_type={chat_type} thinking_enabled={thinking_enabled} thinking_mode={thinking_mode}")
    try:
        if not session_id:
            session_id = f"session_{int(time.time() * 1000)}"

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
                llm_service.set_workspace(ws["path"], workspace_id=workspace_id)

        save_chat_message(
            session_id,
            "user",
            parts=[{"type": "text", "content": message}],
            workspace_id=workspace_id,
        )

        async def response_generator():
            try:
                async for chunk in llm_service.generate_response(
                    message, 
                    session_id, 
                    files=file_paths,
                    chat_type=chat_type,
                    thinking_enabled=thinking_enabled,
                    thinking_mode=thinking_mode
                ):
                    if "error" in chunk:
                        yield json.dumps(chunk) + "\n"
                    elif "tool_call" in chunk:
                        yield json.dumps(chunk) + "\n"
                    elif "tool_result" in chunk:
                        yield json.dumps(chunk) + "\n"
                    else:
                        yield json.dumps(chunk) + "\n"
            except Exception as e:
                print(f"Error in streaming: {e}")
                yield (
                    json.dumps(
                        {"text": f"\n\n**STREAM ERROR:** {str(e)}", "is_final": True}
                    )
                    + "\n"
                )
            finally:
                for path in file_paths:
                    try:
                        os.remove(path)
                    except:
                        pass

        return StreamingResponse(
            response_generator(), media_type="application/x-ndjson"
        )
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- WebSocket ---


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    if AUTH_ENABLED and not (
        _auth_ok(websocket.headers.get("authorization"))
        or _token_ok(websocket.query_params.get("desktop_token"))
    ):
        await websocket.close(code=1008, reason="Authentication required")
        return

    workspace_id = websocket.query_params.get("workspace_id")
    connection_id = await ws_manager.connect(websocket, session_id, workspace_id)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "chat_message":
                lock = ws_manager.get_session_lock(session_id)
                if lock.locked():
                    await ws_manager.send_to_connection(
                        connection_id, MessageType.ERROR, {"message": "Agent is busy."}
                    )
                    continue

                chat_task = asyncio.create_task(
                    handle_ws_chat(
                        connection_id,
                        session_id,
                        data.get("message", ""),
                        data.get("workspace_id") or workspace_id,
                        data.get("files", []),
                        chat_type=data.get("chat_type", "t2t"),
                        thinking_enabled=data.get("thinking_enabled", True),
                        thinking_mode=data.get("thinking_mode", "Auto"),
                    )
                )
                ws_manager.register_session_task(session_id, chat_task)

            elif msg_type == "interrupt":
                llm_service.interrupt_session(session_id)
                ws_manager.cancel_session_task(session_id)
                await ws_manager.send_to_connection(
                    connection_id,
                    MessageType.TEXT,
                    {"content": "\n\n*Interrupted.*", "is_final": True},
                )

            elif msg_type == "ping":
                await ws_manager.send_to_connection(
                    connection_id, MessageType.PONG, {"timestamp": time.time()}
                )

            elif msg_type == "subscribe_terminal":
                if data.get("terminal_id"):
                    ws_manager.subscribe_to_terminal(
                        connection_id, data.get("terminal_id")
                    )

            elif msg_type == "user_response":
                question_id = data.get("question_id")
                response = data.get("response", "")
                if question_id and question_id in ws_manager.pending_questions:
                    future = ws_manager.pending_questions[question_id]
                    if not future.done():
                        future.set_result(response)
                        
            elif msg_type == "terminal_input":
                if data.get("terminal_id"):
                    await ws_manager.send_terminal_input(
                        data.get("terminal_id"), data.get("input", "")
                    )

            elif msg_type == "run_command":
                terminal_id = data.get("terminal_id") or f"term_{uuid.uuid4().hex[:8]}"
                ws_manager.subscribe_to_terminal(connection_id, terminal_id)
                asyncio.create_task(
                    ws_manager.run_streaming_command(
                        data.get("command", ""), terminal_id, data.get("cwd")
                    )
                )
                await ws_manager.send_to_connection(
                    connection_id,
                    MessageType.TERMINAL_OUTPUT,
                    {
                        "terminal_id": terminal_id,
                        "output": f"$ {data.get('command')}\n",
                        "is_error": False,
                    },
                )

            elif msg_type == "kill_terminal":
                if data.get("terminal_id"):
                    await ws_manager.kill_terminal(data.get("terminal_id"))

    except WebSocketDisconnect:
        await ws_manager.disconnect(connection_id)
    except Exception as e:
        print(f"[WS] Error: {e}")
        await ws_manager.disconnect(connection_id)


async def handle_ws_chat(
    connection_id: str,
    session_id: str,
    message: str,
    workspace_id: str = None,
    files: list = None,
    chat_type: str = "t2t",
    thinking_enabled: bool = True,
    thinking_mode: str = "Auto",
):
    lock = ws_manager.get_session_lock(session_id)
    async with lock:
        file_paths = []
        try:
            if workspace_id:
                ws = get_workspace_data(workspace_id)
                if ws:
                    llm_service.set_workspace(ws["path"], workspace_id=workspace_id)

            save_chat_message(
                session_id,
                "user",
                parts=[{"type": "text", "content": message}],
                workspace_id=workspace_id,
            )

            if files:
                import base64
                import binascii

                for f in files:
                    if "content" not in f:
                        continue
                    fname = f.get("name", f"upload_{uuid.uuid4().hex[:8]}")
                    # Sanitize filename to prevent path traversal
                    fname = os.path.basename(fname)
                    fpath = os.path.join(UPLOAD_DIR, fname)

                    raw_content = f["content"]
                    try:
                        # Validate base64 content before writing
                        if not isinstance(raw_content, str):
                            print(f"[WS] Skipping non-string file content for {fname}")
                            continue
                        decoded = base64.b64decode(raw_content, validate=True)
                        with open(fpath, "wb") as fo:
                            fo.write(decoded)
                        file_paths.append(fpath)
                    except binascii.Error as e:
                        print(f"[WS] Invalid base64 for file {fname}: {e}")
                        continue
                    except Exception as e:
                        print(f"[WS] Error processing file {fname}: {e}")
                        continue

            async for chunk in llm_service.generate_response(
                message, 
                session_id, 
                files=file_paths,
                chat_type=chat_type,
                thinking_enabled=thinking_enabled,
                thinking_mode=thinking_mode
            ):
                if "error" in chunk:
                    await ws_manager.send_to_session(
                        session_id, MessageType.ERROR, {"message": chunk["error"]}
                    )
                elif "thought" in chunk:
                    await ws_manager.send_to_session(
                        session_id, MessageType.THOUGHT, {"content": chunk["thought"]}
                    )
                elif "tool_call" in chunk:
                    await ws_manager.send_to_session(
                        session_id,
                        MessageType.TOOL_CALL,
                        {
                            "name": chunk["tool_call"]["name"],
                            "args": chunk["tool_call"]["args"],
                        },
                    )
                elif "tool_result" in chunk:
                    await ws_manager.send_to_session(
                        session_id,
                        MessageType.TOOL_RESULT,
                        {"content": chunk["tool_result"]},
                    )
                else:
                    await ws_manager.send_to_session(
                        session_id,
                        MessageType.TEXT,
                        {
                            "content": chunk.get("text", ""),
                            "images": chunk.get("images", []),
                            "is_final": chunk.get("is_final", False),
                        },
                    )

        except asyncio.CancelledError:
            await ws_manager.send_to_session(
                session_id,
                MessageType.TEXT,
                {"content": "\n\n*Cancelled.*", "is_final": True},
            )
        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"[WS] Error in handle_ws_chat: {e}")
            await ws_manager.send_to_session(
                session_id, MessageType.ERROR, {"message": str(e)}
            )
        finally:
            ws_manager.unregister_session_task(session_id)
            try:
                await ws_manager.send_to_session(session_id, MessageType.STREAM_END, {})
            except:
                pass
            for p in file_paths:
                try:
                    os.remove(p)
                except:
                    pass


app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app:app", host=FLASHY_HOST, port=FLASHY_PORT, reload=FLASHY_RELOAD)
