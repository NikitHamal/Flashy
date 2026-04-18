from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


SessionStatus = Literal["idle", "running", "completed", "failed", "interrupted"]
EventKind = Literal["status", "action", "result", "preview", "assistant", "error"]


class DesktopObservation(BaseModel):
    width: int
    height: int
    active_window: str = ""
    platform: str
    cursor_x: int
    cursor_y: int
    screenshot_data_url: str


class ComputerUseMessage(BaseModel):
    id: str
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: float
    run_id: Optional[str] = None


class ComputerUseEvent(BaseModel):
    id: str
    kind: EventKind
    title: str
    detail: str = ""
    timestamp: float
    run_id: Optional[str] = None
    action_name: Optional[str] = None
    action_args: Optional[Dict[str, Any]] = None
    screenshot_data_url: Optional[str] = None
    screenshot_width: Optional[int] = None
    screenshot_height: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ComputerUseRun(BaseModel):
    id: str
    prompt: str
    provider: str
    model: str
    status: SessionStatus
    started_at: float
    ended_at: Optional[float] = None
    summary: str = ""
    error: str = ""
    steps: int = 0


class ComputerUseSession(BaseModel):
    id: str
    title: str
    status: SessionStatus
    created_at: float
    updated_at: float
    provider: str = "airforce"
    model: str = ""
    current_run_id: Optional[str] = None
    messages: List[ComputerUseMessage] = Field(default_factory=list)
    events: List[ComputerUseEvent] = Field(default_factory=list)
    runs: List[ComputerUseRun] = Field(default_factory=list)


class CreateSessionRequest(BaseModel):
    title: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None


class StartTaskPayload(BaseModel):
    prompt: str = Field(min_length=1)
    provider: Optional[str] = None
    model: Optional[str] = None


class SessionSummary(BaseModel):
    id: str
    title: str
    status: SessionStatus
    created_at: float
    updated_at: float
    provider: str
    model: str
    last_prompt: str = ""
    last_summary: str = ""


class SessionSnapshot(BaseModel):
    session: ComputerUseSession


class WsEnvelope(BaseModel):
    type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
