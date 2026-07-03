"""Runtime helpers for Flashy's command-line surface."""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent

SECRET_MARKERS = ("token", "key", "secret", "password", "cookie", "pat", "1psid", "authorization")


@dataclass(frozen=True)
class Endpoint:
    name: str
    url: str


def ensure_project_on_path() -> None:
    root = str(ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


def merged_env(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    if extra:
        env.update({k: str(v) for k, v in extra.items() if v is not None})
    return env


def is_port_open(host: str, port: int, timeout: float = 0.4) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def find_free_port(preferred: int, host: str = "127.0.0.1") -> int:
    if not is_port_open(host, preferred):
        return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def http_json(url: str, timeout: float = 2.0) -> tuple[bool, dict[str, Any] | str]:
    try:
        request = Request(url, headers={"User-Agent": "flashy-cli"})
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            try:
                return True, json.loads(body)
            except json.JSONDecodeError:
                return True, body
    except HTTPError as exc:
        return False, f"HTTP {exc.code}: {exc.reason}"
    except (URLError, OSError, TimeoutError) as exc:
        return False, str(exc)


def run_python_module(
    module: str,
    *,
    env: Mapping[str, str] | None = None,
    foreground: bool = True,
    passthrough_args: Iterable[str] = (),
) -> subprocess.Popen[str] | None:
    cmd = [sys.executable, "-m", module, *list(passthrough_args)]
    if foreground:
        try:
            completed = subprocess.run(cmd, env=merged_env(env))
            if completed.returncode:
                raise SystemExit(completed.returncode)
        except KeyboardInterrupt:
            print("\nStopped.")
        return None
    return subprocess.Popen(
        cmd,
        env=merged_env(env),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )


def redact_value(key: str, value: Any) -> Any:
    if any(marker in key.lower() for marker in SECRET_MARKERS):
        if value in (None, ""):
            return value
        return "***"
    if isinstance(value, dict):
        return {k: redact_value(k, v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_value(key, item) for item in value]
    return value


def redact_config(config: Mapping[str, Any]) -> dict[str, Any]:
    return {key: redact_value(key, value) for key, value in sorted(config.items())}


def parse_config_value(raw: str) -> Any:
    lowered = raw.strip().lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def health_rows(main_port: int = 8000, provider_port: int = 8001) -> list[dict[str, Any]]:
    endpoints = [
        Endpoint("main", f"http://127.0.0.1:{main_port}/global/health"),
        Endpoint("provider", f"http://127.0.0.1:{provider_port}/health"),
    ]
    rows: list[dict[str, Any]] = []
    for endpoint in endpoints:
        ok, payload = http_json(endpoint.url)
        rows.append(
            {
                "service": endpoint.name,
                "status": "running" if ok else "down",
                "url": endpoint.url,
                "details": payload if isinstance(payload, str) else payload.get("status", "ok"),
            }
        )
    return rows


def project_version() -> str:
    from . import __version__

    return __version__
