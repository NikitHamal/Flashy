import asyncio
import os
import sys
import json
import shutil
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()

QWEN_CODE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "qwen-code")


@router.get("/qwen-code")
async def qwen_code_page():
    frontend_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "frontend", "qwen-code", "index.html"
    )
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    raise HTTPException(status_code=404, detail="Qwen Code page not found")


@router.websocket("/ws/qwen-code-terminal")
async def qwen_code_terminal(websocket: WebSocket):
    await websocket.accept()

    process = None
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "start_qwen":
                if process and process.returncode is None:
                    process.kill()

                provider = data.get("provider", "free-qwen")
                model = data.get("model", "qwen3.6-plus")

                qwen_bin = shutil.which("qwen") or os.path.join(
                    QWEN_CODE_DIR, "node_modules", ".bin", "qwen"
                )

                env = os.environ.copy()
                env["FREE_QWEN"] = "1" if provider == "free-qwen" else ""
                env["FREE_DEEPINFRA"] = "1" if provider == "free-deepinfra" else ""

                cmd = [qwen_bin or "npx", "qwen-code",
                       "--auth-type", provider,
                       "--model", model]

                try:
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.STDOUT,
                        env=env,
                    )

                    async def read_output():
                        try:
                            while True:
                                chunk = await process.stdout.read(4096)
                                if not chunk:
                                    break
                                try:
                                    await websocket.send_json({
                                        "type": "output",
                                        "data": chunk.decode("utf-8", errors="replace")
                                    })
                                except Exception:
                                    break
                        except Exception:
                            pass
                        finally:
                            try:
                                await websocket.send_json({
                                    "type": "exit",
                                    "code": process.returncode
                                })
                            except Exception:
                                pass

                    asyncio.create_task(read_output())

                except FileNotFoundError:
                    await websocket.send_json({
                        "type": "output",
                        "data": (
                            "\r\n\x1b[31mQwen Code CLI not found.\x1b[0m\r\n"
                            "Please install it first:\r\n"
                            "  cd qwen-code && npm install && npm run build && npm run bundle\r\n"
                        )
                    })

            elif msg_type == "input":
                if process and process.stdin and not process.stdin.is_closing():
                    try:
                        process.stdin.write(data.get("data", "").encode())
                        await process.stdin.drain()
                    except Exception:
                        pass

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[QwenCode Terminal] Error: {e}")
    finally:
        if process and process.returncode is None:
            try:
                process.kill()
            except Exception:
                pass
