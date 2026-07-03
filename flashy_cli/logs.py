"""Logs helpers for the Flashy CLI.

Provides a tiny JSONL log file that other components (chat, doctor, etc.) can
append to, plus a tail-style reader. Logs are best-effort: we never let logging
fail the surrounding operation.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Iterable, Optional


LOG_FILENAME = "flashy.log"
LOG_LIMIT_BYTES = 1_000_000  # 1 MB rolling cap


def log_path() -> Path:
    from backend.desktop_runtime import data_file

    try:
        return Path(data_file(LOG_FILENAME))
    except Exception:
        from .runtime import ROOT

        out = ROOT / ".flashy" / LOG_FILENAME
        out.parent.mkdir(parents=True, exist_ok=True)
        return out


def _rotate_if_needed(path: Path) -> None:
    try:
        if path.exists() and path.stat().st_size > LOG_LIMIT_BYTES:
            backup = path.with_suffix(".log.1")
            if backup.exists():
                backup.unlink()
            path.replace(backup)
    except Exception:
        pass


def write(level: str, message: str, **fields: Any) -> None:
    """Append a single JSONL log line. Never raises."""
    level = (level or "info").lower()
    payload = {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "level": level,
        "msg": str(message),
    }
    payload.update({k: v for k, v in fields.items() if v is not None})
    path = log_path()
    _rotate_if_needed(path)
    try:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass


def tail(limit: int = 50, *, level: str | None = None) -> list[dict[str, Any]]:
    path = log_path()
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []
    rows: list[dict[str, Any]] = []
    for raw in lines[-limit:]:
        raw = raw.strip()
        if not raw:
            continue
        try:
            row = json.loads(raw)
        except Exception:
            row = {"iso": "?", "level": "info", "msg": raw}
        if level and row.get("level") != level.lower():
            continue
        rows.append(row)
    return rows


def clear() -> bool:
    path = log_path()
    if not path.exists():
        return False
    try:
        path.unlink()
        return True
    except Exception:
        return False

