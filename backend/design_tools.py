"""
Design Tools Module

This module provides the tool definitions and execution logic for the
Flashy Design Agent. It handles canvas manipulation commands and
translates them into canvas state updates.

Enhanced with advanced effects: gradients, shadows, filters, and blend modes.
"""

import uuid
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import copy

from .design_effects import (
    GradientType, BlendMode, FilterType,
    GradientStop, LinearGradient, RadialGradient, ConicGradient,
    Shadow, Filter, FilterStack, TextEffects, ObjectEffects,
    EffectPresets, hex_to_rgba, lighten_color, darken_color,
    create_linear_gradient, create_radial_gradient, create_shadow
)


class ObjectType(Enum):
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    TRIANGLE = "triangle"
    LINE = "line"
    POLYGON = "polygon"
    STAR = "star"
    PATH = "path"
    TEXT = "text"
    IMAGE = "image"
    GROUP = "group"


@dataclass
class CanvasObject:
    """Represents a single object on the canvas with full effect support."""
    id: str
    type: ObjectType
    x: float = 0
    y: float = 0
    width: float = 100
    height: float = 100
    fill: str = "#000000"
    stroke: str = "transparent"
    strokeWidth: float = 0
    opacity: float = 1.0
    angle: float = 0
    scaleX: float = 1.0
    scaleY: float = 1.0
    visible: bool = True
    locked: bool = False

    # Advanced effects
    shadow: Optional[Dict[str, Any]] = None
    gradient: Optional[Dict[str, Any]] = None
    filters: Optional[List[Dict[str, Any]]] = None
    blendMode: str = "normal"
    backdropBlur: float = 0
    borderRadius: float = 0  # For rounded corners on rectangles

    # Type-specific properties stored here
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = {
            "id": self.id,
            "type": self.type.value,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "fill": self.fill,
            "stroke": self.stroke,
            "strokeWidth": self.strokeWidth,
            "opacity": self.opacity,
            "angle": self.angle,
            "scaleX": self.scaleX,
            "scaleY": self.scaleY,
            "visible": self.visible,
            "locked": self.locked,
            "blendMode": self.blendMode,
            "backdropBlur": self.backdropBlur,
            "borderRadius": self.borderRadius,
            **self.properties
        }

        # Include effects only if set
        if self.shadow:
            data["shadow"] = self.shadow
        if self.gradient:
            data["gradient"] = self.gradient
        if self.filters:
            data["filters"] = self.filters

        return data


@dataclass
class CanvasState:
    """Represents the complete state of the canvas."""
    width: int = 1200
    height: int = 800
    background: str = "#FFFFFF"
    objects: List[CanvasObject] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "width": self.width,
            "height": self.height,
            "background": self.background,
            "objects": [obj.to_dict() for obj in self.objects]
        }

    def find_object(self, obj_id: str) -> Optional[CanvasObject]:
        """Find an object by ID."""
        for obj in self.objects:
            if obj.id == obj_id:
                return obj
            # Check inside groups
            if obj.type == ObjectType.GROUP:
                for child in obj.properties.get("objects", []):
                    if child.id == obj_id:
                        return child
        return None

    def remove_object(self, obj_id: str) -> bool:
        """Remove an object by ID."""
        for i, obj in enumerate(self.objects):
            if obj.id == obj_id:
                self.objects.pop(i)
                return True
        return False


class DesignTools:
    """
    Manages design tools and canvas state.
    Provides methods for all design operations.
    """

    def __init__(self, canvas_width: int = 1200, canvas_height: int = 800):
        self.canvas = CanvasState(width=canvas_width, height=canvas_height)
        self.history: List[CanvasState] = []
        self.history_index: int = -1
        self.max_history: int = 50
        self._save_state()

    def _generate_id(self) -> str:
        """Generate unique object ID."""
        return f"obj_{uuid.uuid4().hex[:8]}"

    def _save_state(self):
        """Save current state to history for undo/redo."""
        # Remove any redo states
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]

        # Deep copy current state
        state_copy = CanvasState(
            width=self.canvas.width,
            height=self.canvas.height,
            background=self.canvas.background,
            objects=[copy.deepcopy(obj) for obj in self.canvas.objects]
        )

        self.history.append(state_copy)

        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
        else:
            self.history_index += 1

    def get_available_tools(self) -> List[Dict[str, str]]:
        """Get list of available design tools with descriptions."""
        return [
            # Shape tools
            {"name": "add_rectangle", "description": "Add a rectangle shape"},
            {"name": "add_circle", "description": "Add a circle shape"},
            {"name": "add_ellipse", "description": "Add an ellipse shape"},
            {"name": "add_triangle", "description": "Add a triangle shape"},
            {"name": "add_line", "description": "Add a line"},
            {"name": "add_polygon", "description": "Add a polygon (points or center/radius/sides)"},
            {"name": "add_star", "description": "Add a star shape"},
            {"name": "add_path", "description": "Add an SVG path"},

            # Text tools
            {"name": "add_text", "description": "Add text to the canvas"},
            {"name": "update_text", "description": "Update text content"},
            {"name": "style_text", "description": "Apply advanced text styling (shadow, spacing, decoration)"},

            # Image tools
            {"name": "add_image", "description": "Add an image from URL"},

            # Object manipulation
            {"name": "select_object", "description": "Select an object by ID"},
            {"name": "delete_object", "description": "Delete an object"},
            {"name": "modify_object", "description": "Modify object properties"},
            {"name": "move_object", "description": "Move an object"},
            {"name": "resize_object", "description": "Resize an object"},
            {"name": "rotate_object", "description": "Rotate an object"},
            {"name": "scale_object", "description": "Scale an object"},

            # Style tools
            {"name": "set_fill", "description": "Change fill color"},
            {"name": "set_stroke", "description": "Change stroke color and width"},
            {"name": "set_opacity", "description": "Change opacity"},
            {"name": "set_border_radius", "description": "Set rounded corners"},

            # Advanced effects
            {"name": "add_shadow", "description": "Add drop shadow to an object"},
            {"name": "remove_shadow", "description": "Remove shadow from an object"},
            {"name": "set_gradient", "description": "Apply gradient fill (linear or radial)"},
            {"name": "remove_gradient", "description": "Remove gradient, restore solid fill"},
            {"name": "add_filter", "description": "Add filter effect (blur, brightness, contrast, etc.)"},
            {"name": "remove_filters", "description": "Remove all filters from object"},
            {"name": "set_blend_mode", "description": "Set blend/composite mode"},
            {"name": "set_backdrop_blur", "description": "Set background blur (glassmorphism)"},
            {"name": "apply_effect_preset", "description": "Apply a pre-defined effect preset"},

            # Layer ordering
            {"name": "bring_to_front", "description": "Bring object to front"},
            {"name": "send_to_back", "description": "Send object to back"},
            {"name": "bring_forward", "description": "Bring object forward"},
            {"name": "send_backward", "description": "Send object backward"},

            # Cloning
            {"name": "duplicate_object", "description": "Duplicate an object"},

            # Canvas operations
            {"name": "set_background", "description": "Set canvas background color or gradient"},
            {"name": "set_canvas_size", "description": "Set canvas dimensions"},
            {"name": "clear_canvas", "description": "Clear all objects"},
            {"name": "get_canvas_state", "description": "Get current canvas state"},

            # History
            {"name": "undo", "description": "Undo last action"},
            {"name": "redo", "description": "Redo last undone action"},

            # Grouping
            {"name": "group_objects", "description": "Group multiple objects"},
            {"name": "ungroup_object", "description": "Ungroup a group"},
            {"name": "ungroup_objects", "description": "Ungroup a group (alias)"},

            # Alignment & Distribution
            {"name": "align_objects", "description": "Align multiple objects"},
            {"name": "distribute_objects", "description": "Distribute objects evenly"},

            # Information
            {"name": "list_objects", "description": "List all objects"},
            {"name": "get_object_properties", "description": "Get object properties"},
            {"name": "get_effect_presets", "description": "Get available effect presets"},
        ]

    async def execute(self, tool_name: str, **kwargs) -> str:
        """Execute a design tool and return result."""
        method = getattr(self, tool_name, None)
        if method is None:
            return f"Error: Unknown tool '{tool_name}'"

        try:
            result = method(**kwargs)
            return result
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    # === Shape Tools ===

    def add_rectangle(
        self, x: float = 100, y: float = 100,
        width: float = 200, height: float = 100,
        fill: str = "#4A90D9", stroke: str = "transparent",
        strokeWidth: float = 0, opacity: float = 1.0,
        rx: float = 0, ry: float = 0, angle: float = 0
    ) -> str:
        """Add a rectangle to the canvas."""
        obj_id = self._generate_id()
        obj = CanvasObject(
            id=obj_id,
            type=ObjectType.RECTANGLE,
            x=x, y=y, width=width, height=height,
            fill=fill, stroke=stroke, strokeWidth=strokeWidth,
            opacity=opacity, angle=angle,
            properties={"rx": rx, "ry": ry}
        )
        self.canvas.objects.append(obj)
        self._save_state()
        return f"Added rectangle with ID: {obj_id}"

    def add_circle(
        self, x: float = 100, y: float = 100,
        radius: float = 50, fill: str = "#4A90D9",
        stroke: str = "transparent", strokeWidth: float = 0,
        opacity: float = 1.0
    ) -> str:
        """Add a circle to the canvas."""
        obj_id = self._generate_id()
        obj = CanvasObject(
            id=obj_id,
            type=ObjectType.CIRCLE,
            x=x, y=y, width=radius * 2, height=radius * 2,
            fill=fill, stroke=stroke, strokeWidth=strokeWidth,
            opacity=opacity,
            properties={"radius": radius}
        )
        self.canvas.objects.append(obj)
        self._save_state()
        return f"Added circle with ID: {obj_id}"

    def add_ellipse(
        self, x: float = 100, y: float = 100,
        rx: float = 100, ry: float = 50, fill: str = "#4A90D9",
        stroke: str = "transparent", strokeWidth: float = 0,
        opacity: float = 1.0, angle: float = 0
    ) -> str:
        """Add an ellipse to the canvas."""
        obj_id = self._generate_id()
        obj = CanvasObject(
            id=obj_id,
            type=ObjectType.ELLIPSE,
            x=x, y=y, width=rx * 2, height=ry * 2,
            fill=fill, stroke=stroke, strokeWidth=strokeWidth,
            opacity=opacity, angle=angle,
            properties={"rx": rx, "ry": ry}
        )
        self.canvas.objects.append(obj)
        self._save_state()
        return f"Added ellipse with ID: {obj_id}"

    def add_triangle(
        self, x: float = 100, y: float = 100,
        width: float = 100, height: float = 100,
        fill: str = "#4A90D9", stroke: str = "transparent",
        strokeWidth: float = 0, opacity: float = 1.0,
        angle: float = 0
    ) -> str:
        """Add a triangle to the canvas."""
        obj_id = self._generate_id()
        obj = CanvasObject(
            id=obj_id,
            type=ObjectType.TRIANGLE,
            x=x, y=y, width=width, height=height,
            fill=fill, stroke=stroke, strokeWidth=strokeWidth,
            opacity=opacity, angle=angle
        )
        self.canvas.objects.append(obj)
        self._save_state()
        return f"Added triangle with ID: {obj_id}"

    def add_line(
        self, x1: float = 0, y1: float = 0,
        x2: float = 100, y2: float = 100,
        stroke: str = "#000000", strokeWidth: float = 2,
        opacity: float = 1.0
    ) -> str:
        """Add a line to the canvas."""
        obj_id = self._generate_id()
        obj = CanvasObject(
            id=obj_id,
            type=ObjectType.LINE,
            x=min(x1, x2), y=min(y1, y2),
            width=abs(x2 - x1), height=abs(y2 - y1),
            fill="transparent", stroke=stroke, strokeWidth=strokeWidth,
            opacity=opacity,
            properties={"x1": x1, "y1": y1, "x2": x2, "y2": y2}
        )
        self.canvas.objects.append(obj)
        self._save_state()
        return f"Added line with ID: {obj_id}"

    def add_polygon(
        self, x: float = 100, y: float = 100,
        radius: float = 60, sides: int = 6,
        fill: str = "#4A90D9", stroke: str = "transparent",
        strokeWidth: float = 0, opacity: float = 1.0,
        angle: float = 0, points: Optional[List[List[float]]] = None
    ) -> str:
        """Add a polygon with points or a regular polygon."""
        obj_id = self._generate_id()

        center_x = x + radius
        center_y = y + radius
        polygon_points = points or self._build_polygon_points(center_x, center_y, radius, sides)
        if polygon_points:
            xs = [p[0] for p in polygon_points]
            ys = [p[1] for p in polygon_points]
            min_x, min_y = min(xs), min(ys)
            width = max(xs) - min_x
            height = max(ys) - min_y
            x, y = min_x, min_y
        else:
            width, height = 0, 0

        obj = CanvasObject(
            id=obj_id,
            type=ObjectType.POLYGON,
            x=x, y=y, width=width, height=height,
            fill=fill, stroke=stroke, strokeWidth=strokeWidth,
            opacity=opacity,
            angle=angle,
            properties={"points": polygon_points}
        )
        self.canvas.objects.append(obj)
        self._save_state()
        return f"Added polygon with ID: {obj_id}"

    def add_star(
        self, x: float = 100, y: float = 100,
        outerRadius: float = 80, innerRadius: float = 40,
        points: int = 5, fill: str = "#4A90D9",
        stroke: str = "transparent", strokeWidth: float = 0,
        opacity: float = 1.0, angle: float = 0
    ) -> str:
        """Add a star shape."""
        obj_id = self._generate_id()
        center_x = x + outerRadius
        center_y = y + outerRadius
        star_points = self._build_star_points(center_x, center_y, outerRadius, innerRadius, points)
        if star_points:
            xs = [p[0] for p in star_points]
            ys = [p[1] for p in star_points]
            min_x, min_y = min(xs), min(ys)
            width = max(xs) - min_x
            height = max(ys) - min_y
            x, y = min_x, min_y
        else:
            width, height = 0, 0

        obj = CanvasObject(
            id=obj_id,
            type=ObjectType.STAR,
            x=x, y=y, width=width, height=height,
            fill=fill, stroke=stroke, strokeWidth=strokeWidth,
            opacity=opacity, angle=angle,
            properties={
                "points": star_points,
                "outerRadius": outerRadius,
                "innerRadius": innerRadius,
                "pointCount": points
            }
        )
        self.canvas.objects.append(obj)
        self._save_state()
        return f"Added star with ID: {obj_id}"

    def add_path(
        self, path: str, fill: str = "#4A90D9",
        stroke: str = "transparent", strokeWidth: float = 0,
        opacity: float = 1.0
    ) -> str:
        """Add an SVG path."""
        obj_id = self._generate_id()
        obj = CanvasObject(
            id=obj_id,
            type=ObjectType.PATH,
            fill=fill, stroke=stroke, strokeWidth=strokeWidth,
            opacity=opacity,
            properties={"path": path}
        )
        self.canvas.objects.append(obj)
        self._save_state()
        return f"Added path with ID: {obj_id}"

    # === Text Tools ===

    def add_text(
        self, x: float = 100, y: float = 100,
        text: str = "Text", fontSize: int = 24,
        fontFamily: str = "Arial", fill: str = "#000000",
        fontWeight: str = "normal", fontStyle: str = "normal",
        textAlign: str = "left", angle: float = 0
    ) -> str:
        """Add text to the canvas."""
        obj_id = self._generate_id()
        # Estimate text dimensions
        estimated_width = len(text) * fontSize * 0.6
        estimated_height = fontSize * 1.2

        obj = CanvasObject(
            id=obj_id,
            type=ObjectType.TEXT,
            x=x, y=y, width=estimated_width, height=estimated_height,
            fill=fill, angle=angle,
            properties={
                "text": text,
                "fontSize": fontSize,
                "fontFamily": fontFamily,
                "fontWeight": fontWeight,
                "fontStyle": fontStyle,
                "textAlign": textAlign
            }
        )
        self.canvas.objects.append(obj)
        self._save_state()
        return f"Added text '{text}' with ID: {obj_id}"

    def update_text(self, id: str, text: str) -> str:
        """Update text content of an existing text object."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"
        if obj.type != ObjectType.TEXT:
            return f"Error: Object '{id}' is not a text object"

        obj.properties["text"] = text
        # Update estimated dimensions
        fontSize = obj.properties.get("fontSize", 24)
        obj.width = len(text) * fontSize * 0.6

        self._save_state()
        return f"Updated text of object '{id}'"

    def modify_object(self, id: str, **kwargs) -> str:
        """Modify multiple properties of an object."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"

        if "x" in kwargs:
            obj.x = kwargs["x"]
        if "y" in kwargs:
            obj.y = kwargs["y"]
        if "width" in kwargs:
            obj.width = kwargs["width"]
            if obj.type == ObjectType.CIRCLE:
                obj.properties["radius"] = obj.width / 2
        if "height" in kwargs:
            obj.height = kwargs["height"]
            if obj.type == ObjectType.ELLIPSE:
                obj.properties["ry"] = obj.height / 2
        if "fill" in kwargs:
            obj.fill = kwargs["fill"]
        if "stroke" in kwargs:
            obj.stroke = kwargs["stroke"]
        if "strokeWidth" in kwargs:
            obj.strokeWidth = kwargs["strokeWidth"]
        if "opacity" in kwargs:
            obj.opacity = max(0, min(1, kwargs["opacity"]))
        if "angle" in kwargs:
            obj.angle = kwargs["angle"]
        if "scaleX" in kwargs:
            obj.scaleX = kwargs["scaleX"]
        if "scaleY" in kwargs:
            obj.scaleY = kwargs["scaleY"]

        text_fields = {"text", "fontSize", "fontFamily", "fontWeight", "fontStyle", "textAlign"}
        for key in text_fields:
            if key in kwargs:
                obj.properties[key] = kwargs[key]

        if "rx" in kwargs:
            obj.properties["rx"] = kwargs["rx"]
        if "ry" in kwargs:
            obj.properties["ry"] = kwargs["ry"]

        self._save_state()
        return f"Modified object '{id}'"

    # === Image Tools ===

    def add_image(
        self, x: float = 100, y: float = 100,
        url: str = "", width: float = 200, height: float = 200,
        opacity: float = 1.0, angle: float = 0
    ) -> str:
        """Add an image from URL."""
        obj_id = self._generate_id()
        obj = CanvasObject(
            id=obj_id,
            type=ObjectType.IMAGE,
            x=x, y=y, width=width, height=height,
            opacity=opacity, angle=angle,
            properties={"src": url}
        )
        self.canvas.objects.append(obj)
        self._save_state()
        return f"Added image with ID: {obj_id}"

    # === Object Manipulation ===

    def select_object(self, id: str) -> str:
        """Select an object by ID (informational)."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"
        return f"Selected object '{id}' ({obj.type.value})"

    def delete_object(self, id: str) -> str:
        """Delete an object by ID."""
        if self.canvas.remove_object(id):
            self._save_state()
            return f"Deleted object '{id}'"
        return f"Error: Object '{id}' not found"

    def move_object(self, id: str, x: float, y: float) -> str:
        """Move an object to a new position."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"

        obj.x = x
        obj.y = y
        self._save_state()
        return f"Moved object '{id}' to ({x}, {y})"

    def resize_object(self, id: str, width: float, height: float) -> str:
        """Resize an object."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"

        obj.width = width
        obj.height = height

        # Update type-specific properties
        if obj.type == ObjectType.CIRCLE:
            obj.properties["radius"] = width / 2
        elif obj.type == ObjectType.ELLIPSE:
            obj.properties["rx"] = width / 2
            obj.properties["ry"] = height / 2

        self._save_state()
        return f"Resized object '{id}' to {width}x{height}"

    def rotate_object(self, id: str, angle: float) -> str:
        """Rotate an object."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"

        obj.angle = angle
        self._save_state()
        return f"Rotated object '{id}' to {angle} degrees"

    def scale_object(self, id: str, scaleX: float, scaleY: float) -> str:
        """Scale an object."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"

        obj.scaleX = scaleX
        obj.scaleY = scaleY
        self._save_state()
        return f"Scaled object '{id}' to ({scaleX}, {scaleY})"

    def set_fill(self, id: str, color: str) -> str:
        """Change fill color."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"

        obj.fill = color
        self._save_state()
        return f"Set fill of '{id}' to {color}"

    def set_stroke(self, id: str, color: str, width: float = 1) -> str:
        """Change stroke."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"

        obj.stroke = color
        obj.strokeWidth = width
        self._save_state()
        return f"Set stroke of '{id}' to {color} with width {width}"

    def set_opacity(self, id: str, opacity: float) -> str:
        """Change opacity."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"

        obj.opacity = max(0, min(1, opacity))
        self._save_state()
        return f"Set opacity of '{id}' to {opacity}"

    def bring_to_front(self, id: str) -> str:
        """Bring object to front."""
        for i, obj in enumerate(self.canvas.objects):
            if obj.id == id:
                self.canvas.objects.append(self.canvas.objects.pop(i))
                self._save_state()
                return f"Brought '{id}' to front"
        return f"Error: Object '{id}' not found"

    def send_to_back(self, id: str) -> str:
        """Send object to back."""
        for i, obj in enumerate(self.canvas.objects):
            if obj.id == id:
                self.canvas.objects.insert(0, self.canvas.objects.pop(i))
                self._save_state()
                return f"Sent '{id}' to back"
        return f"Error: Object '{id}' not found"

    def bring_forward(self, id: str) -> str:
        """Bring object forward by one layer."""
        for i, obj in enumerate(self.canvas.objects):
            if obj.id == id:
                new_index = min(i + 1, len(self.canvas.objects) - 1)
                self.canvas.objects.insert(new_index, self.canvas.objects.pop(i))
                self._save_state()
                return f"Brought '{id}' forward"
        return f"Error: Object '{id}' not found"

    def send_backward(self, id: str) -> str:
        """Send object backward by one layer."""
        for i, obj in enumerate(self.canvas.objects):
            if obj.id == id:
                new_index = max(i - 1, 0)
                self.canvas.objects.insert(new_index, self.canvas.objects.pop(i))
                self._save_state()
                return f"Sent '{id}' backward"
        return f"Error: Object '{id}' not found"

    def duplicate_object(self, id: str) -> str:
        """Duplicate an object."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"

        new_id = self._generate_id()
        new_obj = copy.deepcopy(obj)
        new_obj.id = new_id
        new_obj.x += 20  # Offset for visibility
        new_obj.y += 20

        self.canvas.objects.append(new_obj)
        self._save_state()
        return f"Duplicated '{id}' as '{new_id}'"

    # === Canvas Operations ===

    def set_background(self, color: str) -> str:
        """Set canvas background color."""
        self.canvas.background = color
        self._save_state()
        return f"Set background to {color}"

    def set_canvas_size(self, width: int, height: int) -> str:
        """Set canvas dimensions."""
        self.canvas.width = width
        self.canvas.height = height
        self._save_state()
        return f"Set canvas size to {width}x{height}"

    def clear_canvas(self) -> str:
        """Clear all objects from canvas."""
        self.canvas.objects = []
        self._save_state()
        return "Cleared all objects from canvas"

    def get_canvas_state(self) -> str:
        """Get current canvas state as JSON."""
        return json.dumps(self.canvas.to_dict(), indent=2)

    def undo(self) -> str:
        """Undo last action."""
        if self.history_index > 0:
            self.history_index -= 1
            state = self.history[self.history_index]
            self.canvas = CanvasState(
                width=state.width,
                height=state.height,
                background=state.background,
                objects=[copy.deepcopy(obj) for obj in state.objects]
            )
            return "Undone last action"
        return "Nothing to undo"

    def redo(self) -> str:
        """Redo last undone action."""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            state = self.history[self.history_index]
            self.canvas = CanvasState(
                width=state.width,
                height=state.height,
                background=state.background,
                objects=[copy.deepcopy(obj) for obj in state.objects]
            )
            return "Redone action"
        return "Nothing to redo"

    # === Grouping ===

    def group_objects(self, ids: List[str]) -> str:
        """Group multiple objects."""
        objects_to_group = []
        for obj_id in ids:
            obj = self.canvas.find_object(obj_id)
            if obj:
                objects_to_group.append(obj)

        if len(objects_to_group) < 2:
            return "Error: Need at least 2 objects to group"

        # Remove objects from main list
        for obj in objects_to_group:
            self.canvas.remove_object(obj.id)

        # Calculate group bounds
        xs = [obj.x for obj in objects_to_group]
        ys = [obj.y for obj in objects_to_group]
        x2s = [obj.x + obj.width for obj in objects_to_group]
        y2s = [obj.y + obj.height for obj in objects_to_group]

        group_id = self._generate_id()
        group = CanvasObject(
            id=group_id,
            type=ObjectType.GROUP,
            x=min(xs), y=min(ys),
            width=max(x2s) - min(xs),
            height=max(y2s) - min(ys),
            properties={"objects": objects_to_group}
        )

        self.canvas.objects.append(group)
        self._save_state()
        return f"Created group '{group_id}' with {len(objects_to_group)} objects"

    def ungroup_object(self, id: str) -> str:
        """Ungroup a group."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"
        if obj.type != ObjectType.GROUP:
            return f"Error: Object '{id}' is not a group"

        children = obj.properties.get("objects", [])
        self.canvas.remove_object(id)

        for child in children:
            self.canvas.objects.append(child)

        self._save_state()
        return f"Ungrouped '{id}', released {len(children)} objects"

    def ungroup_objects(self, group_id: str) -> str:
        """Alias for ungroup_object for compatibility."""
        return self.ungroup_object(group_id)

    # === Alignment & Distribution ===

    def align_objects(self, ids: List[str], alignment: str) -> str:
        """Align objects."""
        objects = [self.canvas.find_object(obj_id) for obj_id in ids]
        objects = [obj for obj in objects if obj is not None]

        if len(objects) < 2:
            return "Error: Need at least 2 objects to align"

        if alignment == "left":
            min_x = min(obj.x for obj in objects)
            for obj in objects:
                obj.x = min_x
        elif alignment == "center":
            center_x = sum(obj.x + obj.width / 2 for obj in objects) / len(objects)
            for obj in objects:
                obj.x = center_x - obj.width / 2
        elif alignment == "right":
            max_x = max(obj.x + obj.width for obj in objects)
            for obj in objects:
                obj.x = max_x - obj.width
        elif alignment == "top":
            min_y = min(obj.y for obj in objects)
            for obj in objects:
                obj.y = min_y
        elif alignment == "middle":
            center_y = sum(obj.y + obj.height / 2 for obj in objects) / len(objects)
            for obj in objects:
                obj.y = center_y - obj.height / 2
        elif alignment == "bottom":
            max_y = max(obj.y + obj.height for obj in objects)
            for obj in objects:
                obj.y = max_y - obj.height
        else:
            return f"Error: Unknown alignment '{alignment}'"

        self._save_state()
        return f"Aligned {len(objects)} objects to {alignment}"

    def distribute_objects(self, ids: List[str], direction: str) -> str:
        """Distribute objects evenly."""
        objects = [self.canvas.find_object(obj_id) for obj_id in ids]
        objects = [obj for obj in objects if obj is not None]

        if len(objects) < 3:
            return "Error: Need at least 3 objects to distribute"

        if direction == "horizontal":
            objects.sort(key=lambda o: o.x)
            total_width = sum(obj.width for obj in objects)
            start = objects[0].x
            end = objects[-1].x + objects[-1].width
            spacing = (end - start - total_width) / (len(objects) - 1)

            current_x = start
            for obj in objects:
                obj.x = current_x
                current_x += obj.width + spacing

        elif direction == "vertical":
            objects.sort(key=lambda o: o.y)
            total_height = sum(obj.height for obj in objects)
            start = objects[0].y
            end = objects[-1].y + objects[-1].height
            spacing = (end - start - total_height) / (len(objects) - 1)

            current_y = start
            for obj in objects:
                obj.y = current_y
                current_y += obj.height + spacing
        else:
            return f"Error: Unknown direction '{direction}'"

        self._save_state()
        return f"Distributed {len(objects)} objects {direction}ly"

    # === Information ===

    def list_objects(self) -> str:
        """List all objects with their IDs and types."""
        if not self.canvas.objects:
            return "Canvas is empty"

        lines = ["Objects on canvas:"]
        for obj in self.canvas.objects:
            lines.append(f"  - {obj.id}: {obj.type.value} at ({obj.x:.0f}, {obj.y:.0f})")

        return "\n".join(lines)

    def get_object_properties(self, id: str) -> str:
        """Get all properties of an object."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"

        return json.dumps(obj.to_dict(), indent=2)

    def load_state(self, state_dict: Dict[str, Any]) -> str:
        """Load canvas state from dictionary."""
        try:
            self.canvas.width = state_dict.get("width", 1200)
            self.canvas.height = state_dict.get("height", 800)
            self.canvas.background = state_dict.get("background", "#FFFFFF")
            self.canvas.objects = []

            def build_object(data: Dict[str, Any]) -> CanvasObject:
                obj_type = self._map_object_type(data.get("type"))
                x = data.get("x", data.get("left", 0))
                y = data.get("y", data.get("top", 0))
                width = data.get("width", 100)
                height = data.get("height", 100)
                scale_x = data.get("scaleX", 1.0)
                scale_y = data.get("scaleY", 1.0)

                if data.get("type") == "circle" and data.get("radius") is not None:
                    radius = data.get("radius")
                    width = radius * 2 * scale_x
                    height = radius * 2 * scale_y
                else:
                    width = width * scale_x
                    height = height * scale_y

                obj = CanvasObject(
                    id=data.get("id", self._generate_id()),
                    type=obj_type,
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    fill=data.get("fill", "#000000"),
                    stroke=data.get("stroke", "transparent"),
                    strokeWidth=data.get("strokeWidth", 0),
                    opacity=data.get("opacity", 1.0),
                    angle=data.get("angle", 0),
                    scaleX=scale_x,
                    scaleY=scale_y,
                    visible=data.get("visible", True),
                    locked=data.get("locked", False)
                )
                standard_keys = {
                    "id", "type", "x", "y", "width", "height",
                    "fill", "stroke", "strokeWidth", "opacity",
                    "angle", "scaleX", "scaleY", "visible", "locked"
                }
                for key, value in data.items():
                    if key not in standard_keys:
                        obj.properties[key] = value

                if obj_type == ObjectType.LINE and "x1" in data:
                    obj.properties["x1"] = data.get("x1")
                    obj.properties["y1"] = data.get("y1")
                    obj.properties["x2"] = data.get("x2")
                    obj.properties["y2"] = data.get("y2")
                if obj_type == ObjectType.TEXT and "text" in data:
                    obj.properties["text"] = data.get("text")
                    obj.properties["fontSize"] = data.get("fontSize", 24)
                    obj.properties["fontFamily"] = data.get("fontFamily", "Inter")
                    obj.properties["fontWeight"] = data.get("fontWeight", "normal")
                    obj.properties["fontStyle"] = data.get("fontStyle", "normal")
                    obj.properties["textAlign"] = data.get("textAlign", "left")
                if obj_type == ObjectType.IMAGE:
                    obj.properties["src"] = data.get("src") or data.get("url") or data.get("image") or ""

                if obj_type == ObjectType.GROUP and isinstance(data.get("objects"), list):
                    children = [build_object(child) for child in data.get("objects", [])]
                    obj.properties["objects"] = children

                return obj

            for obj_data in state_dict.get("objects", []):
                self.canvas.objects.append(build_object(obj_data))

            self._save_state()
            return f"Loaded canvas with {len(self.canvas.objects)} objects"
        except Exception as e:
            return f"Error loading state: {str(e)}"

    def _map_object_type(self, type_name: Optional[str]) -> ObjectType:
        """Map fabric/object types to internal enum."""
        if not type_name:
            return ObjectType.RECTANGLE

        mapping = {
            "rect": ObjectType.RECTANGLE,
            "rectangle": ObjectType.RECTANGLE,
            "circle": ObjectType.CIRCLE,
            "ellipse": ObjectType.ELLIPSE,
            "triangle": ObjectType.TRIANGLE,
            "line": ObjectType.LINE,
            "polygon": ObjectType.POLYGON,
            "path": ObjectType.PATH,
            "i-text": ObjectType.TEXT,
            "text": ObjectType.TEXT,
            "textbox": ObjectType.TEXT,
            "image": ObjectType.IMAGE,
            "group": ObjectType.GROUP,
            "activeSelection": ObjectType.GROUP,
            "star": ObjectType.STAR
        }
        return mapping.get(type_name, ObjectType.RECTANGLE)

    def _build_polygon_points(self, x: float, y: float, radius: float, sides: int) -> List[List[float]]:
        """Generate points for a regular polygon."""
        if sides < 3:
            return []
        import math
        points = []
        for i in range(sides):
            angle = (2 * math.pi * i) / sides - math.pi / 2
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            points.append([px, py])
        return points

    def _build_star_points(
        self, x: float, y: float, outer_radius: float, inner_radius: float, points: int
    ) -> List[List[float]]:
        """Generate points for a star polygon."""
        if points < 3:
            return []
        import math
        coords = []
        step = math.pi / points
        for i in range(points * 2):
            radius = outer_radius if i % 2 == 0 else inner_radius
            angle = i * step - math.pi / 2
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            coords.append([px, py])
        return coords

    # =========================================================================
    # ADVANCED EFFECT TOOLS
    # =========================================================================

    def add_shadow(
        self, id: str,
        offset_x: float = 4, offset_y: float = 4,
        blur: float = 8, color: str = "rgba(0, 0, 0, 0.3)",
        spread: float = 0, inset: bool = False
    ) -> str:
        """Add a drop shadow to an object."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"

        shadow = Shadow(
            offset_x=offset_x,
            offset_y=offset_y,
            blur=blur,
            spread=spread,
            color=color,
            inset=inset
        )
        obj.shadow = shadow.to_dict()
        self._save_state()

        shadow_type = "inner shadow" if inset else "drop shadow"
        return f"Added {shadow_type} to '{id}'"

    def remove_shadow(self, id: str) -> str:
        """Remove shadow from an object."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"

        obj.shadow = None
        self._save_state()
        return f"Removed shadow from '{id}'"

    def set_gradient(
        self, id: str,
        gradient_type: str = "linear",  # linear, radial, conic
        colors: List[str] = None,
        angle: float = 0,  # for linear
        stops: List[float] = None,  # custom stop positions (0-1)
        cx: float = 0.5, cy: float = 0.5,  # for radial/conic
        preset: str = None  # Use a preset gradient name
    ) -> str:
        """Apply a gradient fill to an object."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"

        # Handle preset gradients
        if preset:
            preset_map = {
                "blue_purple": EffectPresets.gradient_blue_purple,
                "sunset": EffectPresets.gradient_sunset,
                "ocean": EffectPresets.gradient_ocean,
                "midnight": EffectPresets.gradient_midnight,
                "emerald": EffectPresets.gradient_emerald,
                "fire": EffectPresets.gradient_fire,
                "rainbow": EffectPresets.gradient_rainbow,
            }
            if preset.lower() in preset_map:
                gradient = preset_map[preset.lower()]()
                obj.gradient = gradient.to_dict()
                self._save_state()
                return f"Applied '{preset}' gradient preset to '{id}'"
            else:
                return f"Error: Unknown preset '{preset}'. Available: {', '.join(preset_map.keys())}"

        # Build custom gradient
        if not colors or len(colors) < 2:
            colors = ["#667eea", "#764ba2"]  # Default blue-purple

        # Build gradient stops
        gradient_stops = []
        if stops and len(stops) == len(colors):
            for i, color in enumerate(colors):
                gradient_stops.append(GradientStop(stops[i], color))
        else:
            # Evenly distribute colors
            for i, color in enumerate(colors):
                offset = i / (len(colors) - 1) if len(colors) > 1 else 0
                gradient_stops.append(GradientStop(offset, color))

        if gradient_type == "linear":
            gradient = LinearGradient(angle=angle, stops=gradient_stops)
        elif gradient_type == "radial":
            gradient = RadialGradient(
                cx=cx, cy=cy, r1=0, r2=0.5, fx=cx, fy=cy,
                stops=gradient_stops
            )
        elif gradient_type == "conic":
            gradient = ConicGradient(
                cx=cx, cy=cy, start_angle=angle,
                stops=gradient_stops
            )
        else:
            return f"Error: Unknown gradient type '{gradient_type}'"

        obj.gradient = gradient.to_dict()
        self._save_state()
        return f"Applied {gradient_type} gradient to '{id}'"

    def remove_gradient(self, id: str, restore_color: str = None) -> str:
        """Remove gradient from an object, optionally restore a solid color."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"

        obj.gradient = None
        if restore_color:
            obj.fill = restore_color
        self._save_state()
        return f"Removed gradient from '{id}'"

    def add_filter(
        self, id: str,
        filter_type: str,  # blur, brightness, contrast, saturation, grayscale, sepia, invert, hue-rotate
        value: float
    ) -> str:
        """Add a filter effect to an object."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"

        # Map string to FilterType
        filter_map = {
            "blur": FilterType.BLUR,
            "brightness": FilterType.BRIGHTNESS,
            "contrast": FilterType.CONTRAST,
            "saturation": FilterType.SATURATION,
            "saturate": FilterType.SATURATION,
            "grayscale": FilterType.GRAYSCALE,
            "sepia": FilterType.SEPIA,
            "invert": FilterType.INVERT,
            "hue-rotate": FilterType.HUE_ROTATE,
            "hue_rotate": FilterType.HUE_ROTATE,
        }

        ft = filter_map.get(filter_type.lower())
        if not ft:
            return f"Error: Unknown filter '{filter_type}'. Available: {', '.join(filter_map.keys())}"

        new_filter = Filter(ft, value).to_dict()

        if obj.filters is None:
            obj.filters = []

        # Replace existing filter of same type or add new
        existing_idx = None
        for i, f in enumerate(obj.filters):
            if f.get("type") == ft.value:
                existing_idx = i
                break

        if existing_idx is not None:
            obj.filters[existing_idx] = new_filter
        else:
            obj.filters.append(new_filter)

        self._save_state()
        return f"Applied {filter_type}({value}) filter to '{id}'"

    def remove_filters(self, id: str, filter_type: str = None) -> str:
        """Remove all filters or a specific filter type from an object."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"

        if filter_type:
            if obj.filters:
                obj.filters = [f for f in obj.filters if f.get("type") != filter_type.lower()]
                if not obj.filters:
                    obj.filters = None
            self._save_state()
            return f"Removed '{filter_type}' filter from '{id}'"
        else:
            obj.filters = None
            self._save_state()
            return f"Removed all filters from '{id}'"

    def set_blend_mode(self, id: str, mode: str) -> str:
        """Set the blend/composite mode for an object."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"

        # Validate blend mode
        valid_modes = {m.value for m in BlendMode}
        if mode.lower() not in valid_modes:
            return f"Error: Unknown blend mode '{mode}'. Available: {', '.join(sorted(valid_modes))}"

        obj.blendMode = mode.lower()
        self._save_state()
        return f"Set blend mode of '{id}' to '{mode}'"

    def set_backdrop_blur(self, id: str, blur: float) -> str:
        """Set backdrop blur for glassmorphism effect."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"

        obj.backdropBlur = max(0, blur)
        self._save_state()
        return f"Set backdrop blur of '{id}' to {blur}px"

    def set_border_radius(self, id: str, radius: float) -> str:
        """Set border radius for rounded corners."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"

        obj.borderRadius = max(0, radius)

        # Also update rx/ry for rectangles (Fabric.js compatibility)
        if obj.type == ObjectType.RECTANGLE:
            obj.properties["rx"] = radius
            obj.properties["ry"] = radius

        self._save_state()
        return f"Set border radius of '{id}' to {radius}px"

    def style_text(
        self, id: str,
        letter_spacing: float = None,
        line_height: float = None,
        text_shadow_x: float = None,
        text_shadow_y: float = None,
        text_shadow_blur: float = None,
        text_shadow_color: str = None,
        text_decoration: str = None,  # none, underline, line-through
        text_transform: str = None  # none, uppercase, lowercase, capitalize
    ) -> str:
        """Apply advanced text styling."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"
        if obj.type != ObjectType.TEXT:
            return f"Error: Object '{id}' is not a text object"

        changes = []

        if letter_spacing is not None:
            obj.properties["letterSpacing"] = letter_spacing
            changes.append(f"letter-spacing={letter_spacing}")

        if line_height is not None:
            obj.properties["lineHeight"] = line_height
            changes.append(f"line-height={line_height}")

        if text_decoration is not None:
            obj.properties["textDecoration"] = text_decoration
            changes.append(f"text-decoration={text_decoration}")

        if text_transform is not None:
            obj.properties["textTransform"] = text_transform
            changes.append(f"text-transform={text_transform}")

        # Handle text shadow
        if any([text_shadow_x, text_shadow_y, text_shadow_blur, text_shadow_color]):
            shadow = Shadow(
                offset_x=text_shadow_x or 1,
                offset_y=text_shadow_y or 1,
                blur=text_shadow_blur or 2,
                color=text_shadow_color or "rgba(0, 0, 0, 0.3)"
            )
            obj.properties["textShadow"] = shadow.to_dict()
            changes.append("text-shadow")

        self._save_state()

        if changes:
            return f"Styled text '{id}': {', '.join(changes)}"
        return f"No changes made to text '{id}'"

    def apply_effect_preset(self, id: str, preset: str) -> str:
        """Apply a pre-defined effect preset to an object."""
        obj = self.canvas.find_object(id)
        if not obj:
            return f"Error: Object '{id}' not found"

        preset_lower = preset.lower().replace(" ", "_").replace("-", "_")

        # Shadow presets
        if preset_lower == "soft_shadow":
            shadow = EffectPresets.soft_shadow()
            obj.shadow = shadow.to_dict()
            self._save_state()
            return f"Applied soft shadow preset to '{id}'"

        elif preset_lower == "hard_shadow":
            shadow = EffectPresets.hard_shadow()
            obj.shadow = shadow.to_dict()
            self._save_state()
            return f"Applied hard shadow preset to '{id}'"

        elif preset_lower.startswith("glow"):
            # Extract color if specified: glow_blue, glow_#ff0000
            parts = preset_lower.split("_")
            color = "#ffffff"
            if len(parts) > 1:
                color_name = parts[1]
                color_map = {
                    "blue": "#3B82F6",
                    "purple": "#8B5CF6",
                    "pink": "#EC4899",
                    "green": "#10B981",
                    "yellow": "#F59E0B",
                    "red": "#EF4444",
                    "white": "#FFFFFF",
                    "cyan": "#06B6D4",
                }
                color = color_map.get(color_name, color_name if color_name.startswith("#") else "#ffffff")
            shadow = EffectPresets.glow(color)
            obj.shadow = shadow.to_dict()
            self._save_state()
            return f"Applied glow preset ({color}) to '{id}'"

        elif preset_lower == "inner_shadow":
            shadow = EffectPresets.inner_shadow()
            obj.shadow = shadow.to_dict()
            self._save_state()
            return f"Applied inner shadow preset to '{id}'"

        elif preset_lower == "long_shadow":
            shadow = EffectPresets.long_shadow()
            obj.shadow = shadow.to_dict()
            self._save_state()
            return f"Applied long shadow preset to '{id}'"

        # Glassmorphism
        elif preset_lower == "glassmorphism" or preset_lower == "glass":
            effects = EffectPresets.glassmorphism()
            obj.backdropBlur = effects.backdrop_blur
            obj.borderRadius = effects.border_radius
            if effects.shadow:
                obj.shadow = effects.shadow.to_dict()
            # Make semi-transparent for glass effect
            if obj.fill.startswith("#"):
                obj.fill = hex_to_rgba(obj.fill, 0.7)
            self._save_state()
            return f"Applied glassmorphism preset to '{id}'"

        # Gradient presets
        elif preset_lower in ["blue_purple", "sunset", "ocean", "midnight", "emerald", "fire", "rainbow"]:
            return self.set_gradient(id, preset=preset_lower)

        # Filter presets
        elif preset_lower == "grayscale":
            return self.add_filter(id, "grayscale", 1.0)

        elif preset_lower == "sepia":
            return self.add_filter(id, "sepia", 1.0)

        elif preset_lower == "blur_light":
            return self.add_filter(id, "blur", 2)

        elif preset_lower == "blur_medium":
            return self.add_filter(id, "blur", 5)

        elif preset_lower == "blur_heavy":
            return self.add_filter(id, "blur", 10)

        elif preset_lower == "brighten":
            return self.add_filter(id, "brightness", 1.3)

        elif preset_lower == "darken":
            return self.add_filter(id, "brightness", 0.7)

        elif preset_lower == "high_contrast":
            return self.add_filter(id, "contrast", 1.5)

        elif preset_lower == "desaturate":
            return self.add_filter(id, "saturation", 0.5)

        elif preset_lower == "vivid":
            return self.add_filter(id, "saturation", 1.5)

        else:
            available = [
                "soft_shadow", "hard_shadow", "glow", "glow_blue", "glow_purple",
                "inner_shadow", "long_shadow", "glassmorphism",
                "blue_purple", "sunset", "ocean", "midnight", "emerald", "fire", "rainbow",
                "grayscale", "sepia", "blur_light", "blur_medium", "blur_heavy",
                "brighten", "darken", "high_contrast", "desaturate", "vivid"
            ]
            return f"Error: Unknown preset '{preset}'. Available: {', '.join(available)}"

    def get_effect_presets(self) -> str:
        """Get list of available effect presets."""
        presets = {
            "shadows": [
                "soft_shadow - Subtle, soft drop shadow",
                "hard_shadow - Sharp, defined drop shadow",
                "glow - Glowing effect (glow, glow_blue, glow_purple, etc.)",
                "inner_shadow - Inner shadow for depth",
                "long_shadow - Flat design long shadow"
            ],
            "gradients": [
                "blue_purple - Popular blue to purple gradient",
                "sunset - Warm sunset gradient",
                "ocean - Ocean blue gradient",
                "midnight - Dark midnight gradient",
                "emerald - Fresh emerald green gradient",
                "fire - Hot fire gradient",
                "rainbow - Full rainbow spectrum"
            ],
            "effects": [
                "glassmorphism - Modern glass effect with blur",
                "grayscale - Convert to grayscale",
                "sepia - Sepia tone filter",
                "blur_light - Light blur (2px)",
                "blur_medium - Medium blur (5px)",
                "blur_heavy - Heavy blur (10px)",
                "brighten - Increase brightness",
                "darken - Decrease brightness",
                "high_contrast - High contrast",
                "desaturate - Reduce saturation",
                "vivid - Increase saturation"
            ]
        }
        return json.dumps(presets, indent=2)

    def set_background(
        self, color: str = None,
        gradient_type: str = None,
        colors: List[str] = None,
        angle: float = 0
    ) -> str:
        """Set canvas background color or gradient."""
        if gradient_type and colors and len(colors) >= 2:
            # Build gradient for background
            gradient_stops = []
            for i, c in enumerate(colors):
                offset = i / (len(colors) - 1) if len(colors) > 1 else 0
                gradient_stops.append(GradientStop(offset, c))

            if gradient_type == "linear":
                gradient = LinearGradient(angle=angle, stops=gradient_stops)
            elif gradient_type == "radial":
                gradient = RadialGradient(
                    cx=0.5, cy=0.5, r1=0, r2=0.7,
                    stops=gradient_stops
                )
            else:
                gradient = LinearGradient(angle=angle, stops=gradient_stops)

            # Store as CSS string for background
            self.canvas.background = gradient.to_css()
            self._save_state()
            return f"Set background to {gradient_type} gradient"

        elif color:
            self.canvas.background = color
            self._save_state()
            return f"Set background to {color}"

        return "Error: Provide either 'color' or 'gradient_type' with 'colors'"
