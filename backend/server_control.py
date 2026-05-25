"""Provider server process control and telemetry helpers for Flashy."""
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

from .desktop_runtime import data_file, is_frozen, resource_path

_PROVIDER_PROCESS: subprocess.Popen | None = None
_PROVIDER_PORT: int | None = None
_PROVIDER_STARTED_AT: float | None = None
_LAST_HEALTH_CHECK_TIME: float = 0.0
_CACHED_HEALTH_RESULT: dict[str, Any] | None = None

DEFAULT_PROVIDER_PORT = int(os.environ.get("FLASHY_PROVIDER_PORT_DEFAULT", "8001"))


def provider_log_path() -> Path:
    return data_file("provider-server.log")


def provider_events_path() -> Path:
    return data_file("provider-server-events.jsonl")


def _port_available(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) != 0


def _find_port(preferred: int = DEFAULT_PROVIDER_PORT) -> int:
    if _port_available(preferred):
        return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _health(port: int) -> dict[str, Any]:
    global _LAST_HEALTH_CHECK_TIME, _CACHED_HEALTH_RESULT
    now = time.time()
    if _CACHED_HEALTH_RESULT is not None and (now - _LAST_HEALTH_CHECK_TIME) < 5.0:
        return _CACHED_HEALTH_RESULT

    try:
        with urlopen(f"http://127.0.0.1:{port}/health", timeout=0.75) as response:
            payload = response.read(4096).decode("utf-8", errors="replace")
            data = json.loads(payload) if payload else {}
            res = {"ok": response.status == 200, "status_code": response.status, "payload": data}
            _CACHED_HEALTH_RESULT = res
            _LAST_HEALTH_CHECK_TIME = now
            return res
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        res = {"ok": False, "error": str(exc)}
        _CACHED_HEALTH_RESULT = res
        _LAST_HEALTH_CHECK_TIME = now
        return res


def _process_running() -> bool:
    return _PROVIDER_PROCESS is not None and _PROVIDER_PROCESS.poll() is None


def _command() -> list[str]:
    if is_frozen():
        # The PyInstaller executable can run the provider server when this mode is set.
        return [sys.executable]
    return [sys.executable, "-m", "backend.server_app"]


def _base_env(port: int) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "FLASHY_PROVIDER_HOST": "127.0.0.1",
            "FLASHY_PROVIDER_PORT": str(port),
            "FLASHY_PROVIDER_LOG": str(provider_log_path()),
            "FLASHY_PROVIDER_EVENTS": str(provider_events_path()),
            "FLASHY_BACKEND_MODE": "provider_server",
            "PYTHONUNBUFFERED": "1",
        }
    )
    if not is_frozen():
        env["PYTHONPATH"] = str(resource_path())
    return env


def status() -> dict[str, Any]:
    port = _PROVIDER_PORT or DEFAULT_PROVIDER_PORT
    running = _process_running()
    health = _health(port) if running or not _port_available(port) else {"ok": False}
    uptime = None
    if running and _PROVIDER_STARTED_AT:
        uptime = max(0.0, time.time() - _PROVIDER_STARTED_AT)
    return {
        "running": running or bool(health.get("ok")),
        "managed": running,
        "pid": _PROVIDER_PROCESS.pid if running and _PROVIDER_PROCESS else None,
        "port": port,
        "url": f"http://127.0.0.1:{port}",
        "health": health,
        "uptime_seconds": uptime,
        "log_path": str(provider_log_path()),
        "events_path": str(provider_events_path()),
    }


def start(port: int | None = None) -> dict[str, Any]:
    global _PROVIDER_PROCESS, _PROVIDER_PORT, _PROVIDER_STARTED_AT, _LAST_HEALTH_CHECK_TIME, _CACHED_HEALTH_RESULT

    # Invalidate cache so startup check works instantly
    _LAST_HEALTH_CHECK_TIME = 0.0
    _CACHED_HEALTH_RESULT = None

    if _process_running():
        return status()

    chosen_port = _find_port(port or DEFAULT_PROVIDER_PORT)
    _PROVIDER_PORT = chosen_port
    _PROVIDER_STARTED_AT = time.time()

    provider_log_path().parent.mkdir(parents=True, exist_ok=True)
    provider_events_path().parent.mkdir(parents=True, exist_ok=True)
    provider_log_path().write_text("", encoding="utf-8")

    cmd = _command()
    cwd = str(resource_path())
    log_file = provider_log_path().open("ab")
    _PROVIDER_PROCESS = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=_base_env(chosen_port),
        stdin=subprocess.DEVNULL,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        close_fds=(sys.platform != "win32"),
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )

    deadline = time.time() + 12
    while time.time() < deadline:
        current = status()
        if current.get("health", {}).get("ok"):
            return current
        if _PROVIDER_PROCESS.poll() is not None:
            break
        time.sleep(0.25)

    return status()


def stop() -> dict[str, Any]:
    global _PROVIDER_PROCESS, _LAST_HEALTH_CHECK_TIME, _CACHED_HEALTH_RESULT

    # Invalidate cache
    _LAST_HEALTH_CHECK_TIME = 0.0
    _CACHED_HEALTH_RESULT = None

    proc = _PROVIDER_PROCESS
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
    _PROVIDER_PROCESS = None
    return status()


def restart(port: int | None = None) -> dict[str, Any]:
    stop()
    return start(port=port)


atexit.register(stop)


def tail_log(max_lines: int = 300) -> dict[str, Any]:
    path = provider_log_path()
    if not path.exists():
        return {"path": str(path), "lines": []}
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        lines = handle.readlines()[-max(1, min(max_lines, 2000)) :]
    return {"path": str(path), "lines": [line.rstrip("\n") for line in lines]}


def recent_events(limit: int = 120) -> dict[str, Any]:
    path = provider_events_path()
    if not path.exists():
        return {"path": str(path), "events": []}
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle.readlines()[-max(1, min(limit, 500)) :]:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return {"path": str(path), "events": rows}
