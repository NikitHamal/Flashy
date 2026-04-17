import os
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from concurrent.futures import ThreadPoolExecutor
import winpty

router = APIRouter()

# Keep track of active PTYs
active_ptys = {}
executor = ThreadPoolExecutor(max_workers=10)


@router.websocket("/ws/terminal")
async def terminal_endpoint(websocket: WebSocket):
    await websocket.accept()
    pty = None
    loop = asyncio.get_running_loop()

    try:
        pty = winpty.PTY(80, 24)

        flashy_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        qwen_script = os.path.join(flashy_root, "qwen-free.mjs")

        # Windows requires the path to cmd.exe
        cmd_path = os.environ.get("COMSPEC", "C:\\Windows\\System32\\cmd.exe")

        # Start node script via cmd
        pty.spawn(cmd_path, f'cmd.exe /c "node {qwen_script}"', cwd=flashy_root)

        term_id = id(pty)
        active_ptys[term_id] = pty

        def read_from_pty():
            while pty.isalive():
                try:
                    data = pty.read(4096)
                    if data:
                        asyncio.run_coroutine_threadsafe(
                            websocket.send_text(data), loop
                        )
                    else:
                        break
                except Exception:
                    break
            # When PTY dies, close websocket
            asyncio.run_coroutine_threadsafe(websocket.close(), loop)

        # Run reader in thread
        loop.run_in_executor(executor, read_from_pty)

        while True:
            data = await websocket.receive_text()

            # If the data starts with { it might be a JSON command (like resize)
            if data.startswith("{") and data.endswith("}"):
                try:
                    msg = json.loads(data)
                    if msg.get("type") == "resize":
                        pty.set_size(msg.get("cols", 80), msg.get("rows", 24))
                        continue
                except json.JSONDecodeError:
                    pass

            # Send raw text to PTY
            pty.write(data)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Terminal error: {e}")
    finally:
        if pty:
            active_ptys.pop(id(pty), None)
            try:
                # pywinpty objects close automatically when deleted, but we can call cancel_io or let it GC
                pass
            except:
                pass
