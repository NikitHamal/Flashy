"""DuckAI sidecar process control for Flashy."""
from __future__ import annotations

import atexit
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from .desktop_runtime import is_frozen, resource_path

_DUCKAI_PROCESS: subprocess.Popen | None = None
_DUCKAI_PORT: int = 3000
_DUCKAI_STARTED_AT: float | None = None

DUCKAI_DEFAULT_PORT = int(os.environ.get("DUCKAI_PORT", "3000"))
DUCKAI_DIR = resource_path() / "duckai"


def _port_available(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) != 0


def _find_port(preferred: int = DUCKAI_DEFAULT_PORT) -> int:
    if _port_available(preferred):
        return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _health(port: int) -> dict[str, Any]:
    try:
        with urlopen(f"http://127.0.0.1:{port}/health", timeout=0.75) as response:
            payload = response.read(4096).decode("utf-8", errors="replace")
            data = json.loads(payload) if payload else {}
            return {"ok": response.status == 200, "status_code": response.status, "payload": data}
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "error": str(exc)}


def _process_running() -> bool:
    return _DUCKAI_PROCESS is not None and _DUCKAI_PROCESS.poll() is None


def status() -> dict[str, Any]:
    port = _DUCKAI_PORT or DUCKAI_DEFAULT_PORT
    running = _process_running()
    health = _health(port) if running or not _port_available(port) else {"ok": False}
    uptime = None
    if running and _DUCKAI_STARTED_AT:
        uptime = max(0.0, time.time() - _DUCKAI_STARTED_AT)
    return {
        "running": running or bool(health.get("ok")),
        "managed": running,
        "pid": _DUCKAI_PROCESS.pid if running and _DUCKAI_PROCESS else None,
        "port": port,
        "url": f"http://127.0.0.1:{port}",
        "health": health,
        "uptime_seconds": uptime,
    }


def start(port: int | None = None) -> dict[str, Any]:
    global _DUCKAI_PROCESS, _DUCKAI_PORT, _DUCKAI_STARTED_AT

    if _process_running():
        return status()

    chosen_port = _find_port(port or DUCKAI_DEFAULT_PORT)
    _DUCKAI_PORT = chosen_port
    _DUCKAI_STARTED_AT = time.time()

    env = os.environ.copy()
    env["PORT"] = str(chosen_port)
    env["NODE_ENV"] = "production"

    is_win = sys.platform == "win32"

    if is_win:
        _DUCKAI_PROCESS = subprocess.Popen(
            ["cmd", "/c", "bun", "run", "src/server.ts"],
            cwd=str(DUCKAI_DIR),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    else:
        _DUCKAI_PROCESS = subprocess.Popen(
            ["bun", "run", "src/server.ts"],
            cwd=str(DUCKAI_DIR),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

    deadline = time.time() + 15
    while time.time() < deadline:
        current = status()
        if current.get("health", {}).get("ok"):
            return current
        if _DUCKAI_PROCESS.poll() is not None:
            break
        time.sleep(0.25)

    return status()


def stop() -> dict[str, Any]:
    global _DUCKAI_PROCESS

    proc = _DUCKAI_PROCESS
    if proc and proc.poll() is None:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/pid", str(proc.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            proc.terminate()
            try:
                proc.wait(timeout=4)
            except subprocess.TimeoutExpired:
                proc.kill()
    _DUCKAI_PROCESS = None
    return status()


def restart(port: int | None = None) -> dict[str, Any]:
    stop()
    return start(port=port)


atexit.register(stop)
