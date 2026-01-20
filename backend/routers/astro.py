"""
Astro Routes

Endpoints for Flashy Astro agent.
"""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json


router = APIRouter(prefix="/astro", tags=["astro"])


class AstroChatRequest(BaseModel):
    message: str
    session_id: str
    kundalis: List[Dict[str, Any]] = []
    active_kundali_id: Optional[str] = None


@router.post("/chat")
async def astro_chat(request: Request, data: AstroChatRequest):
    astro_service = request.app.state.astro_service

    async def response_generator():
        async for chunk in astro_service.generate_response(
            message=data.message,
            session_id=data.session_id,
            kundalis=data.kundalis,
            active_kundali_id=data.active_kundali_id
        ):
            yield json.dumps(chunk) + "\n"

    return StreamingResponse(response_generator(), media_type="application/x-ndjson")
