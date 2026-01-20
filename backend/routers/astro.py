"""
Astro Router Module

This module provides the API endpoints for the Flashy Astro agent.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json

router = APIRouter(prefix="/astro", tags=["astro"])


class AstroChatRequest(BaseModel):
    """Request model for astro chat."""
    message: str
    session_id: str
    profiles: Optional[List[Dict[str, Any]]] = None


class CreateKundaliRequest(BaseModel):
    """Request model for creating a kundali."""
    session_id: str
    name: str
    birth_date: str  # YYYY-MM-DD
    birth_time: str  # HH:MM
    latitude: float
    longitude: float
    place_name: str = ""
    timezone: str = "UTC"
    gender: str = "other"


class ProfilesRequest(BaseModel):
    """Request model for profiles sync."""
    session_id: str
    profiles: List[Dict[str, Any]]


@router.post("/chat")
async def astro_chat(request: Request, data: AstroChatRequest):
    """
    Chat with the Astro agent.
    Returns streaming NDJSON responses.
    """
    astro_service = request.app.state.astro_service
    
    async def response_generator():
        try:
            async for chunk in astro_service.chat(
                message=data.message,
                session_id=data.session_id,
                profiles_data=data.profiles
            ):
                yield json.dumps(chunk) + "\n"
        except Exception as e:
            yield json.dumps({
                "error": str(e),
                "is_final": True
            }) + "\n"
    
    return StreamingResponse(
        response_generator(),
        media_type="application/x-ndjson"
    )


@router.post("/create")
async def create_kundali(request: Request, data: CreateKundaliRequest):
    """Create a new kundali directly (without AI)."""
    astro_service = request.app.state.astro_service
    
    result = astro_service.create_kundali_direct(
        session_id=data.session_id,
        name=data.name,
        birth_date=data.birth_date,
        birth_time=data.birth_time,
        latitude=data.latitude,
        longitude=data.longitude,
        place_name=data.place_name,
        timezone=data.timezone,
        gender=data.gender
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create kundali"))
    
    return result


@router.delete("/kundali/{session_id}/{profile_id}")
async def delete_kundali(request: Request, session_id: str, profile_id: str):
    """Delete a kundali."""
    astro_service = request.app.state.astro_service
    
    result = astro_service.delete_kundali_direct(session_id, profile_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Kundali not found")
    
    return result


@router.get("/profiles/{session_id}")
async def get_profiles(request: Request, session_id: str):
    """Get all profiles for a session."""
    astro_service = request.app.state.astro_service
    profiles = astro_service.get_profiles(session_id)
    return {"profiles": profiles}


@router.post("/profiles/sync")
async def sync_profiles(request: Request, data: ProfilesRequest):
    """Sync profiles from frontend localStorage."""
    astro_service = request.app.state.astro_service
    astro_service.set_profiles(data.session_id, data.profiles)
    return {"success": True, "count": len(data.profiles)}


@router.get("/chart/{session_id}/{profile_id}")
async def get_chart(request: Request, session_id: str, profile_id: str):
    """Get chart data for frontend rendering."""
    astro_service = request.app.state.astro_service
    chart_data = astro_service.get_chart_data(session_id, profile_id)
    
    if not chart_data:
        raise HTTPException(status_code=404, detail="Chart not found")
    
    return chart_data


@router.get("/analysis/{session_id}/{profile_id}")
async def get_analysis(request: Request, session_id: str, profile_id: str):
    """Get quick analysis without AI interpretation."""
    astro_service = request.app.state.astro_service
    analysis = await astro_service.quick_analysis(session_id, profile_id)
    
    if "error" in analysis:
        raise HTTPException(status_code=404, detail=analysis["error"])
    
    return analysis


@router.post("/interrupt/{session_id}")
async def interrupt_session(request: Request, session_id: str):
    """Interrupt a running astro session."""
    astro_service = request.app.state.astro_service
    astro_service.interrupt_session(session_id)
    return {"success": True, "message": "Session interrupted"}
