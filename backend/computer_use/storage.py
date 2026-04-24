from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from typing import Dict, List, Optional

from ..desktop_runtime import user_data_dir

from .models import (
    ComputerUseEvent,
    ComputerUseMessage,
    ComputerUseRun,
    ComputerUseSession,
    SessionSummary,
)

DATA_DIR = os.environ.get("FLASHY_STORAGE_DIR", str(user_data_dir() / "data"))
COMPUTER_USE_FILE = os.path.join(DATA_DIR, "computer_use_sessions.json")


class ComputerUseStorage:
    def __init__(self, filepath: str = COMPUTER_USE_FILE) -> None:
        self.filepath = filepath
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

    def _load(self) -> Dict[str, dict]:
        if not os.path.exists(self.filepath):
            return {}
        with open(self.filepath, "r", encoding="utf-8") as handle:
            try:
                return json.load(handle)
            except json.JSONDecodeError:
                return {}

    def _save(self, payload: Dict[str, dict]) -> None:
        directory = os.path.dirname(self.filepath)
        fd, temp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False)
            os.replace(temp_path, self.filepath)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def list_sessions(self) -> List[SessionSummary]:
        records = []
        for raw in self._load().values():
            session = ComputerUseSession.model_validate(raw)
            last_prompt = session.runs[-1].prompt if session.runs else ""
            last_summary = session.runs[-1].summary if session.runs else ""
            records.append(
                SessionSummary(
                    id=session.id,
                    title=session.title,
                    status=session.status,
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                    provider=session.provider,
                    model=session.model,
                    last_prompt=last_prompt,
                    last_summary=last_summary,
                )
            )
        records.sort(key=lambda item: item.updated_at, reverse=True)
        return records

    def get_session(self, session_id: str) -> Optional[ComputerUseSession]:
        payload = self._load()
        raw = payload.get(session_id)
        return ComputerUseSession.model_validate(raw) if raw else None

    def save_session(self, session: ComputerUseSession) -> ComputerUseSession:
        payload = self._load()
        payload[session.id] = session.model_dump(mode="json")
        self._save(payload)
        return session

    def create_session(self, title: Optional[str], provider: str, model: str) -> ComputerUseSession:
        now = time.time()
        session_id = f"cu_{uuid.uuid4().hex[:12]}"
        session = ComputerUseSession(
            id=session_id,
            title=(title or "New Computer Use Session").strip(),
            status="idle",
            created_at=now,
            updated_at=now,
            provider=provider,
            model=model,
        )
        return self.save_session(session)

    def append_message(self, session_id: str, role: str, content: str, run_id: Optional[str] = None) -> ComputerUseSession:
        session = self.require_session(session_id)
        session.messages.append(
            ComputerUseMessage(
                id=f"msg_{uuid.uuid4().hex[:12]}",
                role=role,
                content=content,
                timestamp=time.time(),
                run_id=run_id,
            )
        )
        session.updated_at = time.time()
        return self.save_session(session)

    def append_event(self, session_id: str, event: ComputerUseEvent) -> ComputerUseSession:
        session = self.require_session(session_id)
        session.events.append(event)
        session.events = session.events[-250:]
        session.updated_at = time.time()
        return self.save_session(session)

    def start_run(self, session_id: str, prompt: str, provider: str, model: str) -> tuple[ComputerUseSession, ComputerUseRun]:
        session = self.require_session(session_id)
        now = time.time()
        run = ComputerUseRun(
            id=f"run_{uuid.uuid4().hex[:12]}",
            prompt=prompt,
            provider=provider,
            model=model,
            status="running",
            started_at=now,
        )
        session.status = "running"
        session.provider = provider
        session.model = model
        session.current_run_id = run.id
        session.runs.append(run)
        session.updated_at = now
        self.save_session(session)
        return session, run

    def complete_run(self, session_id: str, run_id: str, status: str, summary: str = "", error: str = "", steps: int = 0) -> ComputerUseSession:
        session = self.require_session(session_id)
        for run in reversed(session.runs):
            if run.id == run_id:
                run.status = status
                run.summary = summary
                run.error = error
                run.steps = steps
                run.ended_at = time.time()
                break
        session.status = status
        session.current_run_id = None
        session.updated_at = time.time()
        return self.save_session(session)

    def delete_session(self, session_id: str) -> bool:
        payload = self._load()
        if session_id not in payload:
            return False
        del payload[session_id]
        self._save(payload)
        return True

    def require_session(self, session_id: str) -> ComputerUseSession:
        session = self.get_session(session_id)
        if not session:
            raise KeyError(f"Computer use session not found: {session_id}")
        return session
