from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket

from ..config import load_config
from .desktop import DesktopAutomationError, DesktopController
from .models import ComputerUseEvent, ComputerUseSession, EventKind
from .planner import ComputerUsePlanner
from .storage import ComputerUseStorage


class ComputerUseService:
    def __init__(self) -> None:
        self.storage = ComputerUseStorage()
        self.planner = ComputerUsePlanner()
        self.connections: Dict[str, Set[WebSocket]] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.session_locks: Dict[str, asyncio.Lock] = {}

    def _lock(self, session_id: str) -> asyncio.Lock:
        if session_id not in self.session_locks:
            self.session_locks[session_id] = asyncio.Lock()
        return self.session_locks[session_id]

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        await websocket.accept()
        self.connections.setdefault(session_id, set()).add(websocket)
        await self._send_snapshot(websocket, session_id)
        await websocket.send_json({"type": "run_state", "payload": {"running": session_id in self.active_tasks}})

    async def disconnect(self, websocket: WebSocket, session_id: str) -> None:
        if session_id in self.connections:
            self.connections[session_id].discard(websocket)
            if not self.connections[session_id]:
                self.connections.pop(session_id, None)

    async def broadcast(self, session_id: str, message_type: str, payload: Dict[str, Any]) -> None:
        dead: List[WebSocket] = []
        for websocket in list(self.connections.get(session_id, set())):
            try:
                await websocket.send_json({"type": message_type, "payload": payload})
            except Exception:
                dead.append(websocket)
        for websocket in dead:
            await self.disconnect(websocket, session_id)

    async def _send_snapshot(self, websocket: WebSocket, session_id: str) -> None:
        session = self.storage.require_session(session_id)
        await websocket.send_json({"type": "session_snapshot", "payload": {"session": session.model_dump(mode="json")}})

    def list_sessions(self):
        return [item.model_dump(mode="json") for item in self.storage.list_sessions()]

    def get_session(self, session_id: str):
        session = self.storage.require_session(session_id)
        return session.model_dump(mode="json")

    def delete_session(self, session_id: str) -> bool:
        return self.storage.delete_session(session_id)

    def create_session(self, title: Optional[str] = None, provider: Optional[str] = None, model: Optional[str] = None):
        config = load_config()
        session = self.storage.create_session(
            title=title,
            provider=provider or config.get("computer_use_provider") or "airforce",
            model=model or config.get("computer_use_model") or config.get("model") or "",
        )
        return session.model_dump(mode="json")

    async def interrupt(self, session_id: str) -> None:
        task = self.active_tasks.get(session_id)
        if task and not task.done():
            task.cancel()

    async def start_task(self, session_id: str, prompt: str, provider: Optional[str], model: Optional[str]) -> None:
        if session_id in self.active_tasks and not self.active_tasks[session_id].done():
            raise RuntimeError("A computer-use run is already in progress for this session.")
        task = asyncio.create_task(self._run_task(session_id, prompt, provider, model))
        self.active_tasks[session_id] = task

    async def _record_event(
        self,
        session_id: str,
        *,
        kind: EventKind,
        title: str,
        detail: str = "",
        run_id: Optional[str] = None,
        action_name: Optional[str] = None,
        action_args: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        event = ComputerUseEvent(
            id=f"evt_{uuid.uuid4().hex[:12]}",
            kind=kind,
            title=title,
            detail=detail,
            timestamp=time.time(),
            run_id=run_id,
            action_name=action_name,
            action_args=action_args,
            metadata=metadata or {},
        )
        self.storage.append_event(session_id, event)
        await self.broadcast(session_id, "event", event.model_dump(mode="json"))
        await self.broadcast(session_id, "session_snapshot", {"session": self.storage.require_session(session_id).model_dump(mode="json")})

    def _build_session_context(self, session: ComputerUseSession) -> str:
        lines: List[str] = []
        for message in session.messages[-8:]:
            lines.append(f"{message.role.upper()}: {message.content}")
        if not lines and session.runs:
            for run in session.runs[-3:]:
                lines.append(f"RUN: {run.prompt}\nSTATUS: {run.status}\nSUMMARY: {run.summary or run.error}")
        return "\n\n".join(lines)

    async def _run_task(self, session_id: str, prompt: str, provider: Optional[str], model: Optional[str]) -> None:
        async with self._lock(session_id):
            config = load_config()
            resolved_provider = provider or config.get("computer_use_provider") or "airforce"
            resolved_model = model or config.get("computer_use_model") or config.get("model") or ""
            desktop = DesktopController()
            steps = 0
            session = self.storage.require_session(session_id)
            self.storage.append_message(session_id, "user", prompt)
            session, run = self.storage.start_run(session_id, prompt, resolved_provider, resolved_model)
            await self.broadcast(session_id, "run_state", {"running": True})
            await self._record_event(session_id, kind="status", title="Run started", detail=prompt, run_id=run.id)

            model_id = resolved_model.lower()
            vision_capable = any([
                "omni" in model_id,
                "vision" in model_id,
                "qwen2.5" in model_id and "32b" in model_id,
                "qwen2.5" in model_id and "72b" in model_id,
                "gpt-4o" in model_id,
                "claude" in model_id and "sonnet" in model_id,
            ])
            
            await self._record_event(session_id, kind="status", title="Vision mode", detail="enabled" if vision_capable else "disabled (text-only)", run_id=run.id)

            observation_messages: List[Dict[str, Any]] = []
            try:
                observation = desktop.capture_observation()

                while steps < 40:
                    session = self.storage.require_session(session_id)
                    steps += 1
                    decision = await self.planner.next_action(
                        provider=resolved_provider,
                        model=resolved_model,
                        vision_capable=vision_capable,
                        task=prompt,
                        session_context=self._build_session_context(session),
                        observations=[observation],
                        tool_messages=observation_messages,
                    )

                    if decision.reasoning:
                        await self.broadcast(session_id, "assistant_thought", {"content": decision.reasoning})

                    if decision.name == "finish_run":
                        summary = str(decision.arguments.get("summary", "Task completed.")).strip()
                        self.storage.append_message(session_id, "assistant", summary, run.id)
                        self.storage.complete_run(session_id, run.id, "completed", summary=summary, steps=steps - 1)
                        await self._record_event(session_id, kind="assistant", title="Completed", detail=summary, run_id=run.id)
                        await self.broadcast(session_id, "assistant", {"content": summary, "run_id": run.id})
                        return

                    if decision.name == "fail_run":
                        reason = str(decision.arguments.get("reason", "Unable to complete the task.")).strip()
                        self.storage.append_message(session_id, "assistant", reason, run.id)
                        self.storage.complete_run(session_id, run.id, "failed", error=reason, steps=steps - 1)
                        await self._record_event(session_id, kind="error", title="Run failed", detail=reason, run_id=run.id)
                        await self.broadcast(session_id, "assistant", {"content": reason, "run_id": run.id})
                        return

                    await self._record_event(
                        session_id,
                        kind="action",
                        title=f"Action {steps}: {decision.name}",
                        detail=json.dumps(decision.arguments, ensure_ascii=False),
                        run_id=run.id,
                        action_name=decision.name,
                        action_args=decision.arguments,
                    )

                    result = desktop.run_action(decision.name, decision.arguments)
                    desktop.wait(0.75)
                    observation = desktop.capture_observation()

                    await self._record_event(
                        session_id,
                        kind="result",
                        title=f"Result: {decision.name}",
                        detail=result.message,
                        run_id=run.id,
                        action_name=decision.name,
                        action_args=decision.arguments,
                        metadata=result.details,
                    )

                    tool_call_id = f"call_{steps}"
                    observation_messages.extend(
                        [
                            {
                                "role": "assistant",
                                "content": decision.raw_text or None,
                                "tool_calls": [
                                    {
                                        "id": tool_call_id,
                                        "type": "function",
                                        "function": {
                                            "name": decision.name,
                                            "arguments": json.dumps(decision.arguments, ensure_ascii=False),
                                        },
                                    }
                                ],
                            },
                            {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": json.dumps(
                                    {
                                        **result.to_tool_payload(),
                                        "active_window": observation.get("active_window", ""),
                                        "cursor": [observation.get("cursor_x", 0), observation.get("cursor_y", 0)],
                                    },
                                    ensure_ascii=False,
                                ),
                            },
                        ]
                    )

                timeout_message = "Reached the maximum action budget before the task could be completed."
                self.storage.append_message(session_id, "assistant", timeout_message, run.id)
                self.storage.complete_run(session_id, run.id, "failed", error=timeout_message, steps=steps)
                await self._record_event(session_id, kind="error", title="Run stopped", detail=timeout_message, run_id=run.id)
                await self.broadcast(session_id, "assistant", {"content": timeout_message, "run_id": run.id})
            except asyncio.CancelledError:
                interrupted = "Computer-use run interrupted."
                self.storage.complete_run(session_id, run.id, "interrupted", error=interrupted, steps=steps)
                await self._record_event(session_id, kind="status", title="Interrupted", detail=interrupted, run_id=run.id)
                await self.broadcast(session_id, "assistant", {"content": interrupted, "run_id": run.id})
            except Exception as exc:
                message = f"{type(exc).__name__}: {exc}"
                self.storage.append_message(session_id, "assistant", message, run.id)
                self.storage.complete_run(session_id, run.id, "failed", error=message, steps=steps)
                await self._record_event(session_id, kind="error", title="Execution error", detail=message, run_id=run.id)
                await self.broadcast(session_id, "assistant", {"content": message, "run_id": run.id})
            finally:
                self.active_tasks.pop(session_id, None)
                await self.broadcast(session_id, "run_state", {"running": False})
                await self.broadcast(session_id, "session_snapshot", {"session": self.storage.require_session(session_id).model_dump(mode="json")})


computer_use_service = ComputerUseService()
