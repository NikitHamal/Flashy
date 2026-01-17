"""
Design Routes Module

This module provides API endpoints for the Flashy Design Agent.
Handles design generation, canvas state management, and export operations.
"""

from fastapi import APIRouter, HTTPException, Body, Request, UploadFile, File
from fastapi.responses import StreamingResponse, Response
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import json
import base64
import io
import tempfile
import os


router = APIRouter(prefix="/design", tags=["design"])


class DesignRequest(BaseModel):
    """Request model for design generation."""
    prompt: str
    session_id: str
    canvas_state: Optional[Dict[str, Any]] = None
    screenshot_base64: Optional[str] = None


class CanvasStateUpdate(BaseModel):
    """Request model for canvas state updates."""
    session_id: str
    state: Dict[str, Any]


class LocalToolRequest(BaseModel):
    """Request model for local tool execution."""
    session_id: str
    tool_name: str
    args: Dict[str, Any] = {}


class ReviewRequest(BaseModel):
    """Request model for screenshot review."""
    session_id: str
    screenshot_base64: str
    feedback: Optional[str] = ""


@router.post("/generate")
async def generate_design(request: Request, data: DesignRequest):
    """
    Generate or modify a design based on user prompt.
    Returns a streaming NDJSON response with design agent actions.
    """
    design_service = request.app.state.design_service

    async def response_generator():
        try:
            async for chunk in design_service.generate_design(
                prompt=data.prompt,
                session_id=data.session_id,
                canvas_state=data.canvas_state,
                screenshot_base64=data.screenshot_base64
            ):
                yield json.dumps(chunk) + "\n"
        except Exception as e:
            print(f"[Design] Error in streaming: {e}")
            yield json.dumps({
                "error": str(e),
                "is_final": True
            }) + "\n"

    return StreamingResponse(
        response_generator(),
        media_type="application/x-ndjson"
    )


@router.post("/review")
async def review_design(request: Request, data: ReviewRequest):
    """
    Send canvas screenshot to AI for review and iteration.
    This allows the AI to see its work and make improvements.
    """
    design_service = request.app.state.design_service

    async def response_generator():
        try:
            async for chunk in design_service.send_screenshot_for_review(
                session_id=data.session_id,
                screenshot_base64=data.screenshot_base64,
                additional_feedback=data.feedback
            ):
                yield json.dumps(chunk) + "\n"
        except Exception as e:
            print(f"[Design] Error in review: {e}")
            yield json.dumps({
                "error": str(e),
                "is_final": True
            }) + "\n"

    return StreamingResponse(
        response_generator(),
        media_type="application/x-ndjson"
    )


@router.post("/interrupt")
async def interrupt_design(
    request: Request,
    session_id: str = Body(..., embed=True)
):
    """Interrupt an ongoing design generation."""
    design_service = request.app.state.design_service
    design_service.interrupt_session(session_id)
    return {"message": "Design agent interrupted"}


@router.get("/canvas/{session_id}")
async def get_canvas_state(request: Request, session_id: str):
    """Get current canvas state for a session."""
    design_service = request.app.state.design_service
    state = design_service.get_canvas_state(session_id)
    return state


@router.post("/canvas")
async def set_canvas_state(request: Request, data: CanvasStateUpdate):
    """Set canvas state for a session."""
    design_service = request.app.state.design_service
    result = design_service.set_canvas_state(data.session_id, data.state)
    return {
        "message": result,
        "canvas_state": design_service.get_canvas_state(data.session_id)
    }


@router.post("/tool")
async def execute_local_tool(request: Request, data: LocalToolRequest):
    """
    Execute a design tool locally without AI involvement.
    Used for manual canvas operations from the frontend.
    """
    design_service = request.app.state.design_service

    try:
        result = design_service.execute_local_tool(
            session_id=data.session_id,
            tool_name=data.tool_name,
            args=data.args
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/export/png")
async def export_as_png(
    request: Request,
    session_id: str = Body(...),
    canvas_data: str = Body(...),
    width: int = Body(1200),
    height: int = Body(800),
    scale: float = Body(1.0)
):
    """
    Export canvas as PNG.
    canvas_data should be base64-encoded PNG from frontend canvas.toDataURL()
    """
    try:
        # Remove data URL prefix if present
        if "," in canvas_data:
            canvas_data = canvas_data.split(",")[1]

        image_data = base64.b64decode(canvas_data)

        return Response(
            content=image_data,
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename=design_{session_id}.png"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Export failed: {str(e)}")


@router.post("/export/svg")
async def export_as_svg(
    request: Request,
    session_id: str = Body(...),
    svg_data: str = Body(...)
):
    """
    Export canvas as SVG.
    svg_data should be the SVG string from fabric.js toSVG()
    """
    try:
        return Response(
            content=svg_data,
            media_type="image/svg+xml",
            headers={
                "Content-Disposition": f"attachment; filename=design_{session_id}.svg"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Export failed: {str(e)}")


@router.post("/export/json")
async def export_as_json(
    request: Request,
    session_id: str = Body(...)
):
    """Export canvas state as JSON for backup/restore."""
    design_service = request.app.state.design_service
    state = design_service.get_canvas_state(session_id)

    return Response(
        content=json.dumps(state, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=design_{session_id}.json"
        }
    )


@router.post("/import/json")
async def import_from_json(
    request: Request,
    session_id: str = Body(...),
    state: Dict[str, Any] = Body(...)
):
    """Import canvas state from JSON."""
    design_service = request.app.state.design_service
    result = design_service.set_canvas_state(session_id, state)
    return {
        "message": result,
        "canvas_state": design_service.get_canvas_state(session_id)
    }


@router.post("/upload-image")
async def upload_image_for_canvas(
    request: Request,
    file: UploadFile = File(...)
):
    """
    Upload an image to be used in canvas designs.
    Returns a URL that can be used in add_image tool.
    """
    try:
        # Save to temp directory
        temp_dir = tempfile.mkdtemp(prefix="flashy_design_img_")
        file_path = os.path.join(temp_dir, file.filename)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Return as base64 data URL for canvas use
        import mimetypes
        mime_type = mimetypes.guess_type(file.filename)[0] or "image/png"
        base64_data = base64.b64encode(content).decode()
        data_url = f"data:{mime_type};base64,{base64_data}"

        return {
            "url": data_url,
            "filename": file.filename,
            "size": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")


@router.get("/templates")
async def get_design_templates():
    """Get available design templates."""
    templates = [
        {
            "id": "blank",
            "name": "Blank Canvas",
            "description": "Start with an empty canvas",
            "preview": None,
            "size": {"width": 1200, "height": 800}
        },
        {
            "id": "presentation_16_9",
            "name": "Presentation (16:9)",
            "description": "Standard presentation slide",
            "preview": None,
            "size": {"width": 1920, "height": 1080}
        },
        {
            "id": "social_square",
            "name": "Social Media (Square)",
            "description": "Instagram post format",
            "preview": None,
            "size": {"width": 1080, "height": 1080}
        },
        {
            "id": "social_story",
            "name": "Social Media (Story)",
            "description": "Instagram/Facebook story format",
            "preview": None,
            "size": {"width": 1080, "height": 1920}
        },
        {
            "id": "banner_web",
            "name": "Web Banner",
            "description": "Standard web banner",
            "preview": None,
            "size": {"width": 1200, "height": 628}
        },
        {
            "id": "poster_a4",
            "name": "Poster (A4)",
            "description": "A4 sized poster",
            "preview": None,
            "size": {"width": 2480, "height": 3508}
        },
        {
            "id": "business_card",
            "name": "Business Card",
            "description": "Standard business card",
            "preview": None,
            "size": {"width": 1050, "height": 600}
        },
        {
            "id": "youtube_thumbnail",
            "name": "YouTube Thumbnail",
            "description": "YouTube video thumbnail",
            "preview": None,
            "size": {"width": 1280, "height": 720}
        }
    ]
    return {"templates": templates}


@router.post("/template/apply")
async def apply_template(
    request: Request,
    session_id: str = Body(...),
    template_id: str = Body(...)
):
    """Apply a template to initialize the canvas."""
    templates = {
        "blank": {"width": 1200, "height": 800, "background": "#FFFFFF"},
        "presentation_16_9": {"width": 1920, "height": 1080, "background": "#FFFFFF"},
        "social_square": {"width": 1080, "height": 1080, "background": "#FFFFFF"},
        "social_story": {"width": 1080, "height": 1920, "background": "#FFFFFF"},
        "banner_web": {"width": 1200, "height": 628, "background": "#FFFFFF"},
        "poster_a4": {"width": 2480, "height": 3508, "background": "#FFFFFF"},
        "business_card": {"width": 1050, "height": 600, "background": "#FFFFFF"},
        "youtube_thumbnail": {"width": 1280, "height": 720, "background": "#FF0000"}
    }

    template = templates.get(template_id, templates["blank"])
    state = {
        "width": template["width"],
        "height": template["height"],
        "background": template["background"],
        "objects": []
    }

    design_service = request.app.state.design_service
    result = design_service.set_canvas_state(session_id, state)

    return {
        "message": f"Applied template: {template_id}",
        "canvas_state": design_service.get_canvas_state(session_id)
    }
