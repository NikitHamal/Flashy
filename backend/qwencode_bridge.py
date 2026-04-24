import json
import asyncio
import uuid
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import subprocess

from .desktop_runtime import resource_path

router = APIRouter()

active_sessions = {}


class QwenCodeSession:
    def __init__(self, websocket: WebSocket, session_id: str):
        self.websocket = websocket
        self.session_id = session_id
        self.process = None

    async def send_message(self, msg_type: str, data: dict):
        try:
            await self.websocket.send_json({"type": msg_type, **data})
        except:
            pass

    async def start_qwen_code(
        self, prompt: str, auth_type: str, model: str, workspace_path: str
    ):
        flashy_root = str(resource_path())
        cli_js = os.path.join(flashy_root, "qwen-code", "dist", "cli.js")

        cmd = [
            "node",
            cli_js,
            "--auth-type",
            auth_type,
            "--model",
            model,
            "--input-format",
            "stream-json",
            "--output-format",
            "stream-json",
            "--include-partial-messages",
        ]

        if workspace_path:
            cmd.extend(["--add-dir", workspace_path])

        # Don't use session-id or chat-recording - causes duplicate responses
        # history_dir = os.path.join(flashy_root, "data", "qwencode_history")
        # os.makedirs(history_dir, exist_ok=True)
        # cmd.extend(["--session-id", self.session_id, "--chat-recording"])

        env = os.environ.copy()
        env["FLASHY_API_URL"] = f"http://127.0.0.1:{os.environ.get('FLASHY_PORT', '8000')}"

        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=workspace_path or flashy_root,
            env=env,
        )

        # Send the prompt
        msg = {"type": "submit_prompt", "prompt": [{"type": "text", "text": prompt}]}
        self.process.stdin.write((json.dumps(msg) + "\n").encode("utf-8"))
        await self.process.stdin.drain()

        # We don't need stdin anymore for a one-shot execution in stream-json mode
        self.process.stdin.close()

        # Read stdout
        asyncio.create_task(self.read_stdout())
        asyncio.create_task(self.read_stderr())

    async def read_stdout(self):
        buffer = ""
        while True:
            try:
                line = await self.process.stdout.readline()
                if not line:
                    break
                line = line.decode("utf-8").strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                    await self.handle_qwen_event(event)
                except json.JSONDecodeError:
                    print(f"[QwenCode] Unparseable line: {line}")
            except Exception as e:
                print(f"[QwenCode] Read error: {e}")
                break

        await self.process.wait()
        await self.send_message("stream_end", {})

    async def read_stderr(self):
        while True:
            line = await self.process.stderr.readline()
            if not line:
                break
            print(f"[QwenCode STDERR] {line.decode('utf-8').strip()}")

    async def handle_qwen_event(self, event: dict):
        # Translate Qwen Code stream-json to Flashy format
        event_type = event.get("type")

        if event_type == "stream_event":
            inner_event = event.get("event", {})
            inner_type = inner_event.get("type")

            if inner_type == "content_block_delta":
                delta = inner_event.get("delta", {})
                if delta.get("type") == "text_delta":
                    text = delta.get("text", "")
                    if text:
                        await self.send_message(
                            "text", {"content": text, "is_final": False}
                        )
                elif delta.get("type") == "thought_delta":
                    thought = delta.get("thought", "")
                    if thought:
                        await self.send_message("thought", {"content": thought})

            elif inner_type == "tool_use":
                # A tool is being used
                tool_name = inner_event.get("tool_use", {}).get("name", "unknown")
                tool_input = inner_event.get("tool_use", {}).get("input", {})
                await self.send_message(
                    "tool_call", {"name": tool_name, "args": tool_input}
                )

        elif event_type == "assistant":
            # The assistant message finished
            await self.send_message("text", {"content": "", "is_final": True})

        elif event_type == "result":
            # Execution finished
            if event.get("is_error"):
                err_msg = event.get("error", {}).get("message", "Unknown error")
                await self.send_message("error", {"message": err_msg})


@router.websocket("/ws/qwencode")
async def qwencode_endpoint(
    websocket: WebSocket, session_id: str = None, workspace_path: str = None
):
    await websocket.accept()
    if not session_id:
        session_id = f"qwen_session_{uuid.uuid4().hex[:8]}"

    session = QwenCodeSession(websocket, session_id)
    active_sessions[session_id] = session

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                prompt = msg.get("prompt", "")
                auth_type = msg.get("auth_type", "qwen-free")
                model = msg.get("model", "qwen3.6-plus")

                if prompt:
                    await session.start_qwen_code(
                        prompt, auth_type, model, workspace_path
                    )
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        if session.process:
            try:
                session.process.terminate()
            except:
                pass
        active_sessions.pop(session_id, None)
