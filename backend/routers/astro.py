"""
Astro Routes Module

This module provides API endpoints for the Flashy Vedic Astrology Agent.
Handles kundali management, astrological consultations, and chart operations.

Key Features:
- Streaming consultations with tool execution
- Kundali CRUD operations
- Chart data synchronization with frontend
- Session state management
- Export/import functionality
"""

from fastapi import APIRouter, HTTPException, Body, Request, Query
from fastapi.responses import StreamingResponse, Response
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import json


router = APIRouter(prefix="/astro", tags=["astro"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ConsultationRequest(BaseModel):
    """Request model for astrological consultation."""
    message: str
    session_id: str
    kundalis: Optional[List[Dict[str, Any]]] = None
    active_kundali_id: Optional[str] = None


class KundaliCreateRequest(BaseModel):
    """Request model for kundali creation."""
    session_id: str
    name: str
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    place: str
    latitude: float
    longitude: float
    timezone: str  # e.g., "Asia/Kolkata" or "+05:30"
    gender: str = "male"  # male/female/other
    notes: str = ""
    tags: Optional[List[str]] = None


class ChartDataUpdate(BaseModel):
    """Request model for updating chart data after frontend calculation."""
    session_id: str
    kundali_id: str
    chart_data: Dict[str, Any]


class KundaliSyncRequest(BaseModel):
    """Request model for syncing kundalis from localStorage."""
    session_id: str
    kundalis: List[Dict[str, Any]]


class ActiveKundaliRequest(BaseModel):
    """Request model for setting active kundali."""
    session_id: str
    kundali_id: str


class SessionStateRequest(BaseModel):
    """Request model for restoring session state."""
    session_id: str
    state: Dict[str, Any]


class AyanamsaRequest(BaseModel):
    """Request model for setting ayanamsa."""
    session_id: str
    system: str


# ============================================================================
# CONSULTATION ENDPOINTS
# ============================================================================

@router.post("/consult")
async def consult(request: Request, data: ConsultationRequest):
    """
    Generate astrological reading based on user message.
    Returns a streaming NDJSON response with agent actions.

    The agent will:
    - Parse user intent (chart creation, analysis, compatibility, etc.)
    - Execute appropriate tools to gather astrological data
    - Provide blunt, truthful Vedic interpretations
    """
    astro_service = request.app.state.astro_service

    async def response_generator():
        try:
            async for chunk in astro_service.generate_reading(
                message=data.message,
                session_id=data.session_id,
                kundalis_data=data.kundalis,
                active_kundali_id=data.active_kundali_id
            ):
                yield json.dumps(chunk) + "\n"
        except Exception as e:
            print(f"[Astro] Error in streaming: {e}")
            yield json.dumps({
                "error": str(e),
                "is_final": True
            }) + "\n"

    return StreamingResponse(
        response_generator(),
        media_type="application/x-ndjson"
    )


@router.post("/interrupt")
async def interrupt_consultation(
    request: Request,
    session_id: str = Body(..., embed=True)
):
    """Interrupt an ongoing astrological consultation."""
    astro_service = request.app.state.astro_service
    astro_service.interrupt_session(session_id)
    return {"message": "Consultation interrupted by the seeker"}


# ============================================================================
# KUNDALI CRUD ENDPOINTS
# ============================================================================

@router.post("/kundali")
async def create_kundali(request: Request, data: KundaliCreateRequest):
    """
    Create a new kundali directly without AI involvement.
    Used for form-based chart creation from frontend.

    Note: Chart calculations are done client-side using AstroWeb.
    Use /kundali/chart-data to update with calculated data.
    """
    astro_service = request.app.state.astro_service

    try:
        result = await astro_service.create_kundali_direct(
            session_id=data.session_id,
            name=data.name,
            date=data.date,
            time=data.time,
            place=data.place,
            latitude=data.latitude,
            longitude=data.longitude,
            timezone=data.timezone,
            gender=data.gender,
            notes=data.notes,
            tags=data.tags
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/kundali/chart-data")
async def update_chart_data(request: Request, data: ChartDataUpdate):
    """
    Update chart data for a kundali after frontend calculation.

    The astronomical calculations are performed client-side using
    AstroWeb's calculation engine (based on NASA JPL DE405 ephemeris).
    This endpoint stores the calculated data for AI analysis.
    """
    astro_service = request.app.state.astro_service

    try:
        result = await astro_service.update_chart_data(
            session_id=data.session_id,
            kundali_id=data.kundali_id,
            chart_data=data.chart_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/kundali/{session_id}/{kundali_id}")
async def delete_kundali(request: Request, session_id: str, kundali_id: str):
    """Delete a kundali by ID."""
    astro_service = request.app.state.astro_service

    try:
        result = astro_service.delete_kundali(
            session_id=session_id,
            kundali_id=kundali_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/kundalis/{session_id}")
async def get_kundalis(request: Request, session_id: str):
    """Get all kundalis for a session."""
    astro_service = request.app.state.astro_service
    agent = astro_service.get_agent(session_id)

    return {
        "kundalis": agent.get_all_kundalis(),
        "active_kundali": {
            "id": agent.active_kundali_id,
            "name": agent.active_kundali_name
        }
    }


@router.get("/kundali/{session_id}/{kundali_id}")
async def get_kundali(request: Request, session_id: str, kundali_id: str):
    """Get a specific kundali by ID."""
    astro_service = request.app.state.astro_service
    agent = astro_service.get_agent(session_id)

    result = agent.tools.get_kundali(kundali_id)
    return json.loads(result)


@router.post("/kundalis/search")
async def search_kundalis(
    request: Request,
    session_id: str = Body(...),
    query: str = Body(...)
):
    """Search kundalis by name or tags."""
    astro_service = request.app.state.astro_service

    result = astro_service.search_kundalis(
        session_id=session_id,
        query=query
    )
    return result


# ============================================================================
# SYNC & PERSISTENCE ENDPOINTS
# ============================================================================

@router.post("/sync")
async def sync_kundalis(request: Request, data: KundaliSyncRequest):
    """
    Sync kundalis from frontend localStorage.
    Called on page load to restore session state.
    """
    astro_service = request.app.state.astro_service

    result = astro_service.sync_kundalis(
        session_id=data.session_id,
        kundalis_data=data.kundalis
    )
    return result


@router.get("/export/{session_id}")
async def export_kundalis(request: Request, session_id: str):
    """Export all kundalis for localStorage persistence."""
    astro_service = request.app.state.astro_service
    result = astro_service.export_kundalis(session_id)

    return Response(
        content=json.dumps(result, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=kundalis_{session_id}.json"
        }
    )


@router.post("/import")
async def import_kundalis(request: Request, data: KundaliSyncRequest):
    """Import kundalis from a JSON backup."""
    astro_service = request.app.state.astro_service

    result = astro_service.sync_kundalis(
        session_id=data.session_id,
        kundalis_data=data.kundalis
    )
    return result


# ============================================================================
# SESSION MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/active-kundali")
async def set_active_kundali(request: Request, data: ActiveKundaliRequest):
    """Set the active kundali for analysis context."""
    astro_service = request.app.state.astro_service

    result = astro_service.set_active_kundali(
        session_id=data.session_id,
        kundali_id=data.kundali_id
    )
    return result


@router.delete("/active-kundali/{session_id}")
async def clear_active_kundali(request: Request, session_id: str):
    """Clear the active kundali context."""
    astro_service = request.app.state.astro_service

    result = astro_service.clear_active_kundali(session_id)
    return result


@router.get("/session/{session_id}")
async def get_session_state(request: Request, session_id: str):
    """Get current session state for debugging/persistence."""
    astro_service = request.app.state.astro_service

    result = astro_service.get_session_state(session_id)
    return result


@router.post("/session/save")
async def save_session(
    request: Request,
    session_id: str = Body(..., embed=True)
):
    """Save session state for later restoration."""
    astro_service = request.app.state.astro_service

    result = astro_service.save_session(session_id)
    return result


@router.post("/session/restore")
async def restore_session(request: Request, data: SessionStateRequest):
    """Restore a saved session state."""
    astro_service = request.app.state.astro_service

    result = astro_service.restore_session(
        session_id=data.session_id,
        state=data.state
    )
    return result


@router.post("/session/reset")
async def reset_session(
    request: Request,
    session_id: str = Body(..., embed=True)
):
    """Reset a session to clean state."""
    astro_service = request.app.state.astro_service

    result = astro_service.reset_session(session_id)
    return result


# ============================================================================
# AYANAMSA & SETTINGS ENDPOINTS
# ============================================================================

@router.post("/ayanamsa")
async def set_ayanamsa(request: Request, data: AyanamsaRequest):
    """
    Set the ayanamsa system for calculations.

    Available systems:
    - Lahiri (default, Indian government standard)
    - Raman (B.V. Raman's system)
    - Krishnamurti (KP system)
    - FaganBradley (Western sidereal)
    - Yukteshwar
    - TrueChitra
    - PushyaPaksha
    """
    astro_service = request.app.state.astro_service

    result = astro_service.set_ayanamsa(
        session_id=data.session_id,
        system=data.system
    )
    return result


@router.get("/ayanamsas/{session_id}")
async def get_ayanamsas(request: Request, session_id: str):
    """Get list of available ayanamsa systems."""
    astro_service = request.app.state.astro_service

    result = astro_service.get_available_ayanamsas(session_id)
    return result


# ============================================================================
# REFERENCE DATA ENDPOINTS
# ============================================================================

@router.get("/reference/planet/{planet}")
async def get_planet_reference(request: Request, planet: str):
    """
    Get reference data for a planet.

    Returns significations, dignities, friends/enemies,
    gemstone, day, color, direction, etc.
    """
    astro_service = request.app.state.astro_service

    result = await astro_service.get_planet_info(planet)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/reference/houses")
async def get_house_meanings():
    """Get reference data for all 12 houses/bhavas."""
    house_meanings = {
        1: {
            "name": "Tanu Bhava (Lagna)",
            "theme": "Self, personality, physical body, health, appearance",
            "karaka": "Sun",
            "body_parts": ["Head", "Brain", "Overall vitality"]
        },
        2: {
            "name": "Dhana Bhava",
            "theme": "Wealth, speech, family, food, right eye, face",
            "karaka": "Jupiter",
            "body_parts": ["Face", "Right eye", "Mouth", "Teeth"]
        },
        3: {
            "name": "Sahaja Bhava",
            "theme": "Siblings, courage, short travels, communication, skills",
            "karaka": "Mars",
            "body_parts": ["Arms", "Hands", "Shoulders", "Ears"]
        },
        4: {
            "name": "Sukha Bhava",
            "theme": "Mother, home, comfort, vehicles, emotions, education",
            "karaka": "Moon",
            "body_parts": ["Chest", "Heart", "Lungs"]
        },
        5: {
            "name": "Putra Bhava",
            "theme": "Children, intelligence, creativity, romance, past merit",
            "karaka": "Jupiter",
            "body_parts": ["Stomach", "Upper abdomen"]
        },
        6: {
            "name": "Ripu/Roga Bhava",
            "theme": "Enemies, diseases, debts, service, daily work",
            "karaka": "Mars/Saturn",
            "body_parts": ["Lower abdomen", "Intestines", "Kidneys"]
        },
        7: {
            "name": "Kalatra Bhava",
            "theme": "Marriage, partnerships, business, public dealings",
            "karaka": "Venus",
            "body_parts": ["Lower back", "Reproductive organs"]
        },
        8: {
            "name": "Ayur Bhava",
            "theme": "Longevity, transformation, inheritance, occult",
            "karaka": "Saturn",
            "body_parts": ["Genitals", "Excretory organs"]
        },
        9: {
            "name": "Dharma Bhava",
            "theme": "Father, fortune, higher learning, spirituality, guru",
            "karaka": "Jupiter/Sun",
            "body_parts": ["Thighs", "Hips"]
        },
        10: {
            "name": "Karma Bhava",
            "theme": "Career, fame, authority, karma, government",
            "karaka": "Sun/Mercury/Saturn",
            "body_parts": ["Knees", "Bones"]
        },
        11: {
            "name": "Labha Bhava",
            "theme": "Gains, income, friends, elder siblings, desires",
            "karaka": "Jupiter",
            "body_parts": ["Ankles", "Calves"]
        },
        12: {
            "name": "Vyaya Bhava",
            "theme": "Losses, expenses, moksha, foreign lands, bed pleasures",
            "karaka": "Saturn/Ketu",
            "body_parts": ["Feet", "Left eye"]
        }
    }

    return {"houses": house_meanings}


@router.get("/reference/nakshatras")
async def get_nakshatra_reference():
    """Get reference data for all 27 nakshatras."""
    nakshatras = [
        {"index": 0, "name": "Ashwini", "lord": "Ketu", "deity": "Ashwini Kumaras", "symbol": "Horse head"},
        {"index": 1, "name": "Bharani", "lord": "Venus", "deity": "Yama", "symbol": "Yoni"},
        {"index": 2, "name": "Krittika", "lord": "Sun", "deity": "Agni", "symbol": "Razor/Flame"},
        {"index": 3, "name": "Rohini", "lord": "Moon", "deity": "Brahma", "symbol": "Chariot"},
        {"index": 4, "name": "Mrigashira", "lord": "Mars", "deity": "Soma", "symbol": "Deer head"},
        {"index": 5, "name": "Ardra", "lord": "Rahu", "deity": "Rudra", "symbol": "Teardrop"},
        {"index": 6, "name": "Punarvasu", "lord": "Jupiter", "deity": "Aditi", "symbol": "Bow"},
        {"index": 7, "name": "Pushya", "lord": "Saturn", "deity": "Brihaspati", "symbol": "Cow udder"},
        {"index": 8, "name": "Ashlesha", "lord": "Mercury", "deity": "Naga", "symbol": "Serpent"},
        {"index": 9, "name": "Magha", "lord": "Ketu", "deity": "Pitris", "symbol": "Throne"},
        {"index": 10, "name": "Purva Phalguni", "lord": "Venus", "deity": "Bhaga", "symbol": "Hammock"},
        {"index": 11, "name": "Uttara Phalguni", "lord": "Sun", "deity": "Aryaman", "symbol": "Bed"},
        {"index": 12, "name": "Hasta", "lord": "Moon", "deity": "Savitar", "symbol": "Hand"},
        {"index": 13, "name": "Chitra", "lord": "Mars", "deity": "Vishwakarma", "symbol": "Pearl"},
        {"index": 14, "name": "Swati", "lord": "Rahu", "deity": "Vayu", "symbol": "Coral"},
        {"index": 15, "name": "Vishakha", "lord": "Jupiter", "deity": "Indra-Agni", "symbol": "Archway"},
        {"index": 16, "name": "Anuradha", "lord": "Saturn", "deity": "Mitra", "symbol": "Lotus"},
        {"index": 17, "name": "Jyeshtha", "lord": "Mercury", "deity": "Indra", "symbol": "Earring"},
        {"index": 18, "name": "Moola", "lord": "Ketu", "deity": "Nirriti", "symbol": "Roots"},
        {"index": 19, "name": "Purva Ashadha", "lord": "Venus", "deity": "Apas", "symbol": "Fan"},
        {"index": 20, "name": "Uttara Ashadha", "lord": "Sun", "deity": "Vishwadeva", "symbol": "Elephant tusk"},
        {"index": 21, "name": "Shravana", "lord": "Moon", "deity": "Vishnu", "symbol": "Ear"},
        {"index": 22, "name": "Dhanishtha", "lord": "Mars", "deity": "Vasus", "symbol": "Drum"},
        {"index": 23, "name": "Shatabhisha", "lord": "Rahu", "deity": "Varuna", "symbol": "Circle"},
        {"index": 24, "name": "Purva Bhadrapada", "lord": "Jupiter", "deity": "Aja Ekapada", "symbol": "Sword"},
        {"index": 25, "name": "Uttara Bhadrapada", "lord": "Saturn", "deity": "Ahir Budhnya", "symbol": "Twins"},
        {"index": 26, "name": "Revati", "lord": "Mercury", "deity": "Pushan", "symbol": "Fish"}
    ]

    return {"nakshatras": nakshatras}


@router.get("/reference/dashas")
async def get_dasha_reference():
    """Get reference data for Vimshottari Dasha periods."""
    dasha_periods = {
        "vimshottari": {
            "total_years": 120,
            "sequence": ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"],
            "periods": {
                "Ketu": {"years": 7, "significations": ["Spirituality", "Detachment", "Past karma"]},
                "Venus": {"years": 20, "significations": ["Love", "Wealth", "Comforts", "Arts"]},
                "Sun": {"years": 6, "significations": ["Authority", "Father", "Government", "Health"]},
                "Moon": {"years": 10, "significations": ["Mind", "Mother", "Public", "Emotions"]},
                "Mars": {"years": 7, "significations": ["Energy", "Courage", "Property", "Siblings"]},
                "Rahu": {"years": 18, "significations": ["Obsession", "Foreign", "Ambition", "Material"]},
                "Jupiter": {"years": 16, "significations": ["Wisdom", "Children", "Fortune", "Dharma"]},
                "Saturn": {"years": 19, "significations": ["Karma", "Discipline", "Service", "Longevity"]},
                "Mercury": {"years": 17, "significations": ["Intelligence", "Commerce", "Communication"]}
            }
        }
    }

    return {"dashas": dasha_periods}


@router.get("/reference/yogas")
async def get_yoga_reference():
    """Get reference data for major yogas."""
    yogas = {
        "raja_yogas": {
            "description": "Formed when Kendra lords combine with Trikona lords",
            "results": "Power, authority, leadership, recognition"
        },
        "dhana_yogas": {
            "description": "Connection between 2nd, 5th, 9th, 11th houses",
            "results": "Wealth accumulation, financial prosperity"
        },
        "mahapurusha_yogas": {
            "ruchaka": {"planet": "Mars", "position": "Own/Exalted in Kendra", "results": "Commander, warrior"},
            "bhadra": {"planet": "Mercury", "position": "Own/Exalted in Kendra", "results": "Learned, eloquent"},
            "hamsa": {"planet": "Jupiter", "position": "Own/Exalted in Kendra", "results": "Righteous, spiritual"},
            "malavya": {"planet": "Venus", "position": "Own/Exalted in Kendra", "results": "Artistic, prosperous"},
            "shasha": {"planet": "Saturn", "position": "Own/Exalted in Kendra", "results": "Disciplined, authoritative"}
        },
        "gajakesari_yoga": {
            "description": "Jupiter in Kendra from Moon",
            "results": "Wisdom, fame, leadership, protection"
        },
        "kemadruma_yoga": {
            "description": "Moon with no planets in 2nd/12th from it",
            "results": "Struggles, self-reliance needed",
            "cancellation": "Planets in Kendra from Lagna or Moon"
        }
    }

    return {"yogas": yogas}
