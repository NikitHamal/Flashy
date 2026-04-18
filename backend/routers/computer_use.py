from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request, WebSocket, WebSocketDisconnect

from ..config import load_config
from ..server import ProviderCatalog, resolve_provider_alias
from ..computer_use.models import CreateSessionRequest
from ..computer_use.service import computer_use_service

router = APIRouter(prefix="/api/computer-use", tags=["computer-use"])
_catalog = ProviderCatalog()


@router.get("/sessions")
async def list_sessions():
    return computer_use_service.list_sessions()


@router.post("/sessions")
async def create_session(payload: CreateSessionRequest):
    return computer_use_service.create_session(
        title=payload.title,
        provider=payload.provider,
        model=payload.model,
    )


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    try:
        return computer_use_service.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    deleted = computer_use_service.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"ok": True}


@router.get("/models")
async def get_models(provider: str | None = Query(default=None)):
    config = load_config()
    resolved_provider = resolve_provider_alias(provider or config.get("computer_use_provider") or "airforce")
    try:
        catalog = await _catalog.list_models([resolved_provider])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    models = []
    for item in catalog.get("data", []):
        capabilities = item.get("capabilities") or {}
        models.append(
            {
                "id": item["id"].split("/", 1)[1],
                "name": item.get("name") or item["id"],
                "provider": resolved_provider,
                "vision": bool(capabilities.get("vision")),
                "reasoning": bool(capabilities.get("reasoning")),
                "tools": bool(capabilities.get("tools")),
            }
        )

    current = config.get("computer_use_model") or config.get("model") or ""
    if current and not any(item["id"] == current for item in models):
        models.insert(
            0,
            {
                "id": current,
                "name": current,
                "provider": resolved_provider,
                "vision": False,
                "reasoning": True,
                "tools": True,
            },
        )
    return models


@router.websocket("/ws/{session_id}")
async def computer_use_ws(websocket: WebSocket, session_id: str):
    await computer_use_service.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            payload = data.get("payload") or {}
            if msg_type == "start_task":
                try:
                    await computer_use_service.start_task(
                        session_id,
                        prompt=payload.get("prompt", ""),
                        provider=payload.get("provider"),
                        model=payload.get("model"),
                    )
                except Exception as exc:
                    await websocket.send_json({"type": "error", "payload": {"message": str(exc)}})
            elif msg_type == "interrupt":
                await computer_use_service.interrupt(session_id)
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong", "payload": {}})
    except WebSocketDisconnect:
        await computer_use_service.disconnect(websocket, session_id)
