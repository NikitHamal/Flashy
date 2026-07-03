"""Persist and resume chat sessions.

A session is a JSON document with the working directory, model, messages, and
metadata. Sessions are kept under the user's Flashy data directory by default,
with a safe project-local fallback for portable runs.
"""
from __future__ import annotations

import json
import os
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, List, Optional, Tuple

from .formatting import shorten_path


SESSIONS_DIRNAME = "sessions"
SESSION_FORMAT_VERSION = 1


def sessions_dir() -> Path:
    """Return the directory where sessions are stored."""
    from .runtime import ROOT
    from backend.desktop_runtime import data_file

    try:
        return Path(data_file(SESSIONS_DIRNAME))
    except Exception:
        flash_dir = ROOT / ".flashy"
        out = flash_dir / SESSIONS_DIRNAME
        out.mkdir(parents=True, exist_ok=True)
        return out


@dataclass
class Message:
    role: str
    content: Any
    ts: float = field(default_factory=time.time)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        return cls(
            role=str(data.get("role", "")),
            content=data.get("content", ""),
            ts=float(data.get("ts", time.time())),
            meta=dict(data.get("meta", {}) or {}),
        )


@dataclass
class Session:
    id: str
    title: str
    workspace: str
    provider: str
    model: str
    reasoning: str
    created_at: float
    updated_at: float
    messages: List[Message] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
    format_version: int = SESSION_FORMAT_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": self.format_version,
            "id": self.id,
            "title": self.title,
            "workspace": self.workspace,
            "provider": self.provider,
            "model": self.model,
            "reasoning": self.reasoning,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [m.to_dict() for m in self.messages],
            "meta": self.meta,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        return cls(
            id=str(data.get("id") or uuid.uuid4().hex[:12]),
            title=str(data.get("title") or "untitled"),
            workspace=str(data.get("workspace") or ""),
            provider=str(data.get("provider") or ""),
            model=str(data.get("model") or ""),
            reasoning=str(data.get("reasoning") or "medium"),
            created_at=float(data.get("created_at") or time.time()),
            updated_at=float(data.get("updated_at") or time.time()),
            messages=[Message.from_dict(m) for m in data.get("messages", []) or []],
            meta=dict(data.get("meta", {}) or {}),
            format_version=int(data.get("format_version") or SESSION_FORMAT_VERSION),
        )

    def short_title(self, max_len: int = 64) -> str:
        if self.title:
            return self.title[:max_len]
        for m in self.messages:
            if m.role == "user" and isinstance(m.content, str) and m.content.strip():
                first_line = m.content.strip().splitlines()[0]
                return first_line[:max_len]
        return "untitled"

    def turn_count(self) -> int:
        return sum(1 for m in self.messages if m.role in {"user", "assistant"})

    def age(self) -> str:
        """Return a human-readable relative time for the last update."""
        return _relative_time(self.updated_at)


def _relative_time(ts: float) -> str:
    delta = time.time() - ts
    if delta < 60:
        return "just now"
    if delta < 3600:
        return f"{int(delta // 60)}m ago"
    if delta < 86400:
        return f"{int(delta // 3600)}h ago"
    if delta < 86400 * 7:
        return f"{int(delta // 86400)}d ago"
    return time.strftime("%Y-%m-%d", time.localtime(ts))


def _safe_filename(name: str) -> str:
    keep = "-_."
    out = "".join(c if c.isalnum() or c in keep else "_" for c in name.strip())
    return out.strip("_") or "session"


def session_path(session_id: str) -> Path:
    return sessions_dir() / f"{_safe_filename(session_id)}.json"


def list_sessions(limit: int = 50, workspace: str | None = None) -> List[Session]:
    """Return the most-recently-updated sessions.

    If `workspace` is provided, the list is filtered to sessions in that workspace.
    """
    directory = sessions_dir()
    if not directory.exists():
        return []
    files = sorted(directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    sessions: List[Session] = []
    for path in files:
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            session = Session.from_dict(data)
        except Exception:
            continue
        if workspace and session.workspace and os.path.normpath(session.workspace) != os.path.normpath(workspace):
            continue
        sessions.append(session)
        if len(sessions) >= limit:
            break
    return sessions


def find_session(prefix: str) -> Optional[Session]:
    """Find a session by id, or by id prefix."""
    if not prefix:
        return None
    path = session_path(prefix)
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as handle:
                return Session.from_dict(json.load(handle))
        except Exception:
            return None
    for session in list_sessions(limit=500):
        if session.id.startswith(prefix):
            return session
    return None


def load_session(session_id: str) -> Optional[Session]:
    return find_session(session_id)


def save_session(session: Session) -> Path:
    directory = sessions_dir()
    directory.mkdir(parents=True, exist_ok=True)
    session.updated_at = time.time()
    path = session_path(session.id)
    tmp = path.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(session.to_dict(), handle, indent=2, ensure_ascii=False)
    os.replace(tmp, path)
    return path


def delete_session(session_id: str) -> bool:
    path = session_path(session_id)
    if path.exists():
        try:
            path.unlink()
            return True
        except Exception:
            return False
    return False


def last_session(workspace: str | None = None) -> Optional[Session]:
    """Return the most recently updated session, optionally scoped to a workspace."""
    items = list_sessions(limit=1, workspace=workspace)
    return items[0] if items else None


def new_session_id() -> str:
    return uuid.uuid4().hex[:12]


def auto_title(first_user_message: str, max_len: int = 64) -> str:
    text = (first_user_message or "").strip().splitlines()
    if not text:
        return "new session"
    head = text[0].strip()
    if not head:
        return "new session"
    # Avoid code-fence markers / paths dominating the title.
    head = re.sub(r"^```[a-zA-Z0-9_+-]*\s*", "", head).strip()
    return head[:max_len]


def to_rows(sessions: Iterable[Session]) -> List[dict[str, str]]:
    """Convert sessions to display rows."""
    out: list[dict[str, str]] = []
    for s in sessions:
        out.append(
            {
                "id": s.id,
                "title": s.short_title(),
                "model": f"{s.provider}/{s.model}" if s.provider or s.model else "",
                "turns": str(s.turn_count()),
                "updated": s.age(),
                "workspace": shorten_path(s.workspace) if s.workspace else "",
            }
        )
    return out


def export_markdown(session: Session) -> str:
    """Render a session as a readable markdown transcript."""
    lines: list[str] = []
    lines.append(f"# {session.title or 'Session ' + session.id}")
    lines.append("")
    if session.provider or session.model:
        lines.append(f"**Model:** `{session.provider}/{session.model}`")
    if session.workspace:
        lines.append(f"**Workspace:** `{session.workspace}`")
    lines.append(f"**Created:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(session.created_at))}")
    lines.append(f"**Updated:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(session.updated_at))}")
    lines.append("")
    for m in session.messages:
        role = m.role.capitalize()
        lines.append(f"## {role}")
        lines.append("")
        content = m.content
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    if part.get("type") == "text":
                        lines.append(str(part.get("text", "")))
                    else:
                        lines.append(f"```{part.get('type', '')}\n{json.dumps(part, ensure_ascii=False, indent=2)}\n```")
                else:
                    lines.append(str(part))
        else:
            lines.append(str(content))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def export_json(session: Session) -> str:
    return json.dumps(session.to_dict(), indent=2, ensure_ascii=False)


def export(session: Session, fmt: str) -> Tuple[str, str]:
    """Return (filename, content) for a session export."""
    fmt = (fmt or "md").lower().lstrip(".")
    safe_title = re.sub(r"[^\w\-.]+", "_", session.short_title(40)).strip("_") or session.id
    if fmt in {"md", "markdown"}:
        return f"{safe_title}.md", export_markdown(session)
    if fmt in {"json"}:
        return f"{safe_title}.json", export_json(session)
    raise ValueError(f"Unknown export format: {fmt}. Use 'md' or 'json'.")

