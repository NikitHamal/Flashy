"""
Design Routes Module

This module provides API endpoints for the Flashy Design Agent.
Handles design generation, canvas state management, and export operations.

Enhanced with comprehensive template support and canvas presets.
"""

from fastapi import APIRouter, HTTPException, Body, Request, UploadFile, File, Query
from fastapi.responses import StreamingResponse, Response
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import json
import base64
import io
import tempfile
import os

from ..design_templates import (
    get_template, get_all_templates, get_templates_by_category,
    get_palette, get_all_palettes, get_canvas_preset, get_all_canvas_presets,
    search_templates, apply_palette_to_template, TemplateCategory, TEMPLATES
)


router = APIRouter(prefix="/design", tags=["design"])


def _to_fabric_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """Convert backend canvas state to Fabric.js compatible state."""
    if not state or "objects" not in state:
        return state
    
    fabric_objects = []
    for obj in state["objects"]:
        fab_obj = _convert_template_element_to_canvas_object(obj)
        if fab_obj:
            fabric_objects.append(fab_obj)
    
    return {
        **state,
        "objects": fabric_objects
    }


class DesignRequest(BaseModel):
    """Request model for design generation."""
    prompt: str
    session_id: str
    canvas_state: Optional[Dict[str, Any]] = None
    screenshot_base64: Optional[str] = None
    images: Optional[List[Dict[str, str]]] = None


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
                screenshot_base64=data.screenshot_base64,
                images=data.images
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
    return _to_fabric_state(state)


@router.post("/canvas")
async def set_canvas_state(request: Request, data: CanvasStateUpdate):
    """Set canvas state for a session."""
    design_service = request.app.state.design_service
    result = design_service.set_canvas_state(data.session_id, data.state)
    return {
        "message": result,
        "canvas_state": _to_fabric_state(design_service.get_canvas_state(data.session_id))
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
        "canvas_state": _to_fabric_state(design_service.get_canvas_state(session_id))
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
async def get_design_templates(
    category: Optional[str] = Query(None, description="Filter by category")
):
    """Get available design templates with optional category filter."""
    if category:
        try:
            cat = TemplateCategory(category)
            templates = get_templates_by_category(cat)
            return {
                "templates": [t.to_dict() for t in templates],
                "category": category
            }
        except ValueError:
            pass

    # Return all templates summary
    return {"templates": get_all_templates()}


@router.get("/templates/{template_id}")
async def get_template_details(template_id: str):
    """Get detailed information about a specific template."""
    template = get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")

    return {"template": template.to_dict()}


@router.get("/templates/search/{query}")
async def search_design_templates(query: str):
    """Search templates by name, description, or tags."""
    results = search_templates(query)
    return {
        "query": query,
        "count": len(results),
        "templates": [t.to_dict() for t in results]
    }


@router.get("/palettes")
async def get_color_palettes():
    """Get all available color palettes."""
    return {"palettes": get_all_palettes()}


@router.get("/palettes/{palette_name}")
async def get_color_palette(palette_name: str):
    """Get a specific color palette by name."""
    palette = get_palette(palette_name)
    if not palette:
        raise HTTPException(status_code=404, detail=f"Palette '{palette_name}' not found")
    return {"palette": palette.to_dict()}


@router.get("/presets")
async def get_canvas_presets():
    """Get all available canvas size presets."""
    return {"presets": get_all_canvas_presets()}


@router.get("/presets/{preset_name}")
async def get_canvas_preset_detail(preset_name: str):
    """Get a specific canvas preset by name."""
    preset = get_canvas_preset(preset_name)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_name}' not found")
    return {"preset": {"id": preset_name, **preset}}


@router.post("/template/apply")
async def apply_template(
    request: Request,
    session_id: str = Body(...),
    template_id: str = Body(...),
    palette_name: Optional[str] = Body(None)
):
    """
    Apply a template to initialize the canvas.
    Optionally apply a different color palette.
    """
    design_service = request.app.state.design_service

    # Check for full template with elements
    full_template = get_template(template_id)
    if full_template:
        # Optionally apply different palette
        if palette_name:
            palette = get_palette(palette_name)
            if palette:
                full_template = apply_palette_to_template(full_template, palette)

        # Build canvas state from template
        state = {
            "width": full_template.width,
            "height": full_template.height,
            "background": full_template.background,
            "objects": []
        }

        # Convert template elements to canvas objects
        for element in full_template.elements:
            obj = _convert_template_element_to_canvas_object(element.to_dict())
            if obj:
                state["objects"].append(obj)

        design_service.set_canvas_state(session_id, state)

        return {
            "message": f"Applied template: {full_template.name}",
            "canvas_state": _to_fabric_state(design_service.get_canvas_state(session_id))
        }

    # Check for canvas preset
    preset = get_canvas_preset(template_id)
    if preset:
        state = {
            "width": preset["width"],
            "height": preset["height"],
            "background": "#FFFFFF",
            "objects": []
        }
        design_service.set_canvas_state(session_id, state)
        return {
            "message": f"Applied preset: {preset['name']}",
            "canvas_state": _to_fabric_state(design_service.get_canvas_state(session_id))
        }

    # Fallback to blank canvas
    state = {
        "width": 1200,
        "height": 800,
        "background": "#FFFFFF",
        "objects": []
    }
    design_service.set_canvas_state(session_id, state)

    return {
        "message": "Applied blank canvas",
        "canvas_state": _to_fabric_state(design_service.get_canvas_state(session_id))
    }


def _convert_template_element_to_canvas_object(element: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Convert a template element definition to a Fabric.js canvas object."""
    element_type = element.get("type", "").lower()

    # Base properties common to all objects
    base_props = {
        "left": element.get("x", 0),
        "top": element.get("y", 0),
        "fill": element.get("fill", "#000000"),
        "stroke": element.get("stroke", "transparent"),
        "strokeWidth": element.get("strokeWidth", 0),
        "opacity": element.get("opacity", 1),
        "angle": element.get("angle", 0),
        "selectable": element.get("selectable", True),
        "id": element.get("id"),
        "name": element.get("name")
    }

    if element_type == "rectangle" or element_type == "rect":
        return {
            "type": "rect",
            **base_props,
            "width": element.get("width", 100),
            "height": element.get("height", 50),
            "rx": element.get("rx", 0),
            "ry": element.get("ry", 0),
        }

    elif element_type == "circle":
        radius = element.get("radius", element.get("width", 50) / 2)
        return {
            "type": "circle",
            **base_props,
            "radius": radius,
        }

    elif element_type == "text" or element_type == "i-text" or element_type == "itext":
        return {
            "type": "textbox",
            **base_props,
            "text": element.get("text", "Text"),
            "fontSize": element.get("fontSize", 24),
            "fontFamily": element.get("fontFamily", "Inter"),
            "fontWeight": element.get("fontWeight", "normal"),
            "textAlign": element.get("textAlign", "left"),
            "width": element.get("width", 200),
        }
    
    elif element_type == "textbox":
        return {
            "type": "textbox",
            **base_props,
            "width": element.get("width", 200),
            "text": element.get("text", "Text"),
            "fontSize": element.get("fontSize", 24),
            "fontFamily": element.get("fontFamily", "Inter"),
            "fontWeight": element.get("fontWeight", "normal"),
            "textAlign": element.get("textAlign", "left"),
        }

    elif element_type == "triangle":
        return {
            "type": "triangle",
            **base_props,
            "width": element.get("width", 100),
            "height": element.get("height", 100),
        }

    elif element_type == "line":
        return {
            "type": "line",
            **base_props,
            "x1": element.get("x1", 0),
            "y1": element.get("y1", 0),
            "x2": element.get("x2", 100),
            "y2": element.get("y2", 0),
            "stroke": element.get("stroke", "#000000"),
            "strokeWidth": element.get("strokeWidth", 2),
        }

    elif element_type == "image":
        src = element.get("src", "")
        if src.startswith("http://") or src.startswith("https://"):
            if not src.startswith("/proxy_image"):
                src = f"/proxy_image?url={src}"
                
        # Image objects in Fabric often need scaleX/scaleY rather than width/height
        # unless they are already resized. For templates, we'll pass both.
        return {
            "type": "image",
            **base_props,
            "width": element.get("width", 200),
            "height": element.get("height", 200),
            "src": src,
        }

    elif element_type == "group":
        objects = []
        for child in element.get("objects", []):
            fab_child = _convert_template_element_to_canvas_object(child)
            if fab_child:
                objects.append(fab_child)
                
        return {
            "type": "group",
            **base_props,
            "objects": objects
        }

    return None
