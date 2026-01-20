"""
Astro Routes
"""

from fastapi import APIRouter, Body, Request
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import json
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/astro", tags=["astro"])


class AstroChatRequest(BaseModel):
    prompt: str
    session_id: str
    kundalis_state: Optional[List[Dict[str, Any]]] = None


class AstroSyncRequest(BaseModel):
    session_id: str
    kundalis_state: List[Dict[str, Any]]


@router.post("/chat")
async def astro_chat(request: Request, data: AstroChatRequest):
    astro_service = request.app.state.astro_service

    async def response_generator():
        async for chunk in astro_service.generate_response(
            prompt=data.prompt,
            session_id=data.session_id,
            kundalis_state=data.kundalis_state
        ):
            yield json.dumps(chunk) + "\n"

    return StreamingResponse(response_generator(), media_type="application/x-ndjson")


@router.post("/sync")
async def astro_sync(request: Request, data: AstroSyncRequest):
    astro_service = request.app.state.astro_service
    return astro_service.set_kundalis_state(data.session_id, data.kundalis_state)


@router.get("/kundalis/{session_id}")
async def astro_kundalis(request: Request, session_id: str):
    astro_service = request.app.state.astro_service
    return {"kundalis_state": astro_service.get_kundalis_state(session_id)}


@router.post("/interrupt")
async def astro_interrupt(request: Request, session_id: str = Body(..., embed=True)):
    astro_service = request.app.state.astro_service
    astro_service.interrupt_session(session_id)
    return {"message": "Astro session interrupted"}
