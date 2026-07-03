"""Per-session statistics for the Flashy CLI."""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

from .formatting import format_size


STATS_FILENAME = "stats.json"


def _stats_path() -> Path:
    from backend.desktop_runtime import data_file

    try:
        return Path(data_file(STATS_FILENAME))
    except Exception:
        from .runtime import ROOT

        out = ROOT / ".flashy" / STATS_FILENAME
        out.parent.mkdir(parents=True, exist_ok=True)
        return out


def _load() -> dict[str, Any]:
    path = _stats_path()
    if not path.exists():
        return {"total_sessions": 0, "total_turns": 0, "total_tokens_in": 0, "total_tokens_out": 0, "total_duration_s": 0.0, "providers": {}, "models": {}}
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return {}


def _save(data: dict[str, Any]) -> None:
    path = _stats_path()
    try:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
    except Exception:
        pass


def record_session(*, provider: str, model: str, turns: int, duration_s: float, tokens_in: int = 0, tokens_out: int = 0) -> None:
    data = _load()
    data["total_sessions"] = int(data.get("total_sessions", 0)) + 1
    data["total_turns"] = int(data.get("total_turns", 0)) + max(0, int(turns))
    data["total_tokens_in"] = int(data.get("total_tokens_in", 0)) + max(0, int(tokens_in))
    data["total_tokens_out"] = int(data.get("total_tokens_out", 0)) + max(0, int(tokens_out))
    data["total_duration_s"] = float(data.get("total_duration_s", 0.0)) + max(0.0, float(duration_s))
    providers = data.get("providers") or {}
    if provider:
        providers[provider] = int(providers.get(provider, 0)) + 1
    data["providers"] = providers
    models = data.get("models") or {}
    if model:
        models[model] = int(models.get(model, 0)) + 1
    data["models"] = models
    _save(data)


def reset() -> None:
    path = _stats_path()
    if path.exists():
        try:
            path.unlink()
        except Exception:
            pass


def load_all() -> dict[str, Any]:
    return _load()


def to_rows() -> list[dict[str, str]]:
    data = _load()
    rows: list[dict[str, str]] = []
    for provider, count in (data.get("providers") or {}).items():
        rows.append({"name": provider, "type": "provider", "count": str(count), "share": _share(count, sum((data.get("providers") or {}).values()))})
    for model, count in (data.get("models") or {}).items():
        rows.append({"name": model, "type": "model", "count": str(count), "share": _share(count, sum((data.get("models") or {}).values()))})
    return rows


def _share(part: int, total: int) -> str:
    if not total:
        return "0%"
    return f"{(part / total) * 100:.0f}%"


def summary_lines() -> list[tuple[str, str]]:
    data = _load()
    total_sessions = int(data.get("total_sessions", 0))
    total_turns = int(data.get("total_turns", 0))
    total_in = int(data.get("total_tokens_in", 0))
    total_out = int(data.get("total_tokens_out", 0))
    total_duration = float(data.get("total_duration_s", 0.0))
    return [
        ("Sessions", str(total_sessions)),
        ("Total turns", str(total_turns)),
        ("Tokens in", f"{total_in:,}"),
        ("Tokens out", f"{total_out:,}"),
        ("Time spent", f"{total_duration / 60:.1f} min" if total_duration else "0 min"),
    ]

