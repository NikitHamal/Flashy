"""
SVG Renderer Module

Converts canvas state objects to clean, optimized SVG output.
Supports all design elements including gradients, shadows, filters, and effects.

This renderer allows the design agent to output pure SVG, enabling:
- Direct SVG manipulation without fabric.js dependency
- Clean, production-ready SVG export
- Server-side SVG generation for thumbnails/previews
- Neobrutalist design with crisp vector output
"""

import re
import math
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SVGConfig:
    """Configuration for SVG rendering."""
    indent: bool = True
    pretty_print: bool = True
    include_defs: bool = True
    optimize: bool = True
    viewport_width: Optional[int] = None
    viewport_height: Optional[int] = None
    class_prefix: str = "flashy-"


class SVGRenderer:
    """
    Renders canvas state to SVG format.

    Supports:
    - Basic shapes: rectangle, circle, ellipse, triangle, line, polygon, star
    - Text with full styling
    - Paths (SVG path data)
    - Gradients (linear, radial, conic)
    - Shadows (drop shadow filter)
    - Blend modes
    - Border radius
    - Groups
    """

    def __init__(self, config: Optional[SVGConfig] = None):
        self.config = config or SVGConfig()
        self.defs = []
        self.defs_ids = set()
        self.current_id = 0

    def _generate_id(self, prefix: str = "el") -> str:
        """Generate unique element ID."""
        self.current_id += 1
        return f"{self.config.class_prefix}{prefix}-{self.current_id}"

    def render(self, canvas_state: Dict[str, Any]) -> str:
        """
        Render complete canvas state to SVG string.

        Args:
            canvas_state: Dictionary with width, height, background, objects

        Returns:
            Complete SVG string
        """
        self.defs = []
        self.defs_ids = set()
        self.current_id = 0

        width = canvas_state.get("width", 1200)
        height = canvas_state.get("height", 800)
        background = canvas_state.get("background", "#FFFFFF")
        objects = canvas_state.get("objects", [])

        # Build SVG root
        svg_attrs = {
            "xmlns": "http://www.w3.org/2000/svg",
            "xmlns:xlink": "http://www.w3.org/1999/xlink",
            "width": str(width),
            "height": str(height),
            "viewBox": f"0 0 {width} {height}",
            "version": "1.1"
        }

        # Optional viewport sizing
        if self.config.viewport_width:
            svg_attrs["width"] = str(self.config.viewport_width)
        if self.config.viewport_height:
            svg_attrs["height"] = str(self.config.viewport_height)

        root = ET.Element("svg", svg_attrs)

        # Add background
        if background and background != "transparent":
            bg_rect = ET.SubElement(root, "rect", {
                "x": "0",
                "y": "0",
                "width": str(width),
                "height": str(height),
                "fill": background
            })

        # Render objects (collect defs along the way)
        elements = []
        for obj in objects:
            if not obj.get("visible", True):
                continue
            el = self._render_object(obj)
            if el is not None:
                elements.append(el)

        # Add defs if any
        if self.defs and self.config.include_defs:
            defs_el = ET.SubElement(root, "defs")
            for def_el in self.defs:
                defs_el.append(def_el)

        # Add rendered elements
        for el in elements:
            root.append(el)

        # Convert to string
        return self._to_string(root)

    def _render_object(self, obj: Dict[str, Any]) -> Optional[ET.Element]:
        """Render a single canvas object to SVG element."""
        obj_type = obj.get("type", "")

        renderers = {
            "rectangle": self._render_rectangle,
            "circle": self._render_circle,
            "ellipse": self._render_ellipse,
            "triangle": self._render_triangle,
            "line": self._render_line,
            "polygon": self._render_polygon,
            "star": self._render_star,
            "path": self._render_path,
            "text": self._render_text,
            "group": self._render_group,
            "image": self._render_image
        }

        renderer = renderers.get(obj_type)
        if not renderer:
            return None

        element = renderer(obj)
        if element is None:
            return None

        # Apply common transforms and styles
        self._apply_transforms(element, obj)
        self._apply_styles(element, obj)

        return element

    def _render_rectangle(self, obj: Dict[str, Any]) -> ET.Element:
        """Render rectangle element."""
        attrs = {
            "x": str(obj.get("x", 0)),
            "y": str(obj.get("y", 0)),
            "width": str(obj.get("width", 100)),
            "height": str(obj.get("height", 100))
        }

        # Border radius
        border_radius = obj.get("borderRadius", 0)
        if border_radius > 0:
            attrs["rx"] = str(border_radius)
            attrs["ry"] = str(border_radius)

        return ET.Element("rect", attrs)

    def _render_circle(self, obj: Dict[str, Any]) -> ET.Element:
        """Render circle element."""
        x = obj.get("x", 0)
        y = obj.get("y", 0)
        width = obj.get("width", 100)
        height = obj.get("height", 100)

        # Circle uses smaller dimension as diameter
        radius = min(width, height) / 2
        cx = x + width / 2
        cy = y + height / 2

        return ET.Element("circle", {
            "cx": str(cx),
            "cy": str(cy),
            "r": str(radius)
        })

    def _render_ellipse(self, obj: Dict[str, Any]) -> ET.Element:
        """Render ellipse element."""
        x = obj.get("x", 0)
        y = obj.get("y", 0)
        width = obj.get("width", 100)
        height = obj.get("height", 100)

        return ET.Element("ellipse", {
            "cx": str(x + width / 2),
            "cy": str(y + height / 2),
            "rx": str(width / 2),
            "ry": str(height / 2)
        })

    def _render_triangle(self, obj: Dict[str, Any]) -> ET.Element:
        """Render triangle as polygon."""
        x = obj.get("x", 0)
        y = obj.get("y", 0)
        width = obj.get("width", 100)
        height = obj.get("height", 100)

        # Triangle points: top-center, bottom-left, bottom-right
        points = [
            (x + width / 2, y),
            (x, y + height),
            (x + width, y + height)
        ]

        points_str = " ".join(f"{p[0]},{p[1]}" for p in points)
        return ET.Element("polygon", {"points": points_str})

    def _render_line(self, obj: Dict[str, Any]) -> ET.Element:
        """Render line element."""
        x = obj.get("x", 0)
        y = obj.get("y", 0)
        x2 = obj.get("x2", x + obj.get("width", 100))
        y2 = obj.get("y2", y + obj.get("height", 0))

        return ET.Element("line", {
            "x1": str(x),
            "y1": str(y),
            "x2": str(x2),
            "y2": str(y2)
        })

    def _render_polygon(self, obj: Dict[str, Any]) -> ET.Element:
        """Render polygon element."""
        points = obj.get("points", [])

        if not points:
            # Generate regular polygon from sides
            x = obj.get("x", 0)
            y = obj.get("y", 0)
            width = obj.get("width", 100)
            height = obj.get("height", 100)
            sides = obj.get("sides", 6)

            points = self._generate_regular_polygon(
                x + width / 2, y + height / 2,
                min(width, height) / 2, sides
            )

        points_str = " ".join(f"{p[0]},{p[1]}" for p in points)
        return ET.Element("polygon", {"points": points_str})

    def _render_star(self, obj: Dict[str, Any]) -> ET.Element:
        """Render star as polygon."""
        x = obj.get("x", 0)
        y = obj.get("y", 0)
        width = obj.get("width", 100)
        height = obj.get("height", 100)
        points_count = obj.get("points", 5)  # Number of star points
        inner_ratio = obj.get("innerRadius", 0.4)

        cx = x + width / 2
        cy = y + height / 2
        outer_r = min(width, height) / 2
        inner_r = outer_r * inner_ratio

        star_points = self._generate_star_points(
            cx, cy, outer_r, inner_r, points_count
        )

        points_str = " ".join(f"{p[0]},{p[1]}" for p in star_points)
        return ET.Element("polygon", {"points": points_str})

    def _render_path(self, obj: Dict[str, Any]) -> ET.Element:
        """Render SVG path element."""
        path_data = obj.get("path", obj.get("d", ""))

        return ET.Element("path", {"d": path_data})

    def _render_text(self, obj: Dict[str, Any]) -> ET.Element:
        """Render text element with styling."""
        x = obj.get("x", 0)
        y = obj.get("y", 0)
        text_content = obj.get("text", obj.get("content", ""))

        attrs = {
            "x": str(x),
            "y": str(y)
        }

        # Text styling
        font_family = obj.get("fontFamily", "Inter, sans-serif")
        font_size = obj.get("fontSize", 16)
        font_weight = obj.get("fontWeight", "normal")
        font_style = obj.get("fontStyle", "normal")
        text_align = obj.get("textAlign", "left")
        line_height = obj.get("lineHeight", 1.2)
        letter_spacing = obj.get("letterSpacing", 0)
        text_decoration = obj.get("textDecoration", "none")

        attrs["font-family"] = font_family
        attrs["font-size"] = str(font_size)
        attrs["font-weight"] = str(font_weight)
        attrs["font-style"] = font_style
        attrs["text-anchor"] = {"left": "start", "center": "middle", "right": "end"}.get(text_align, "start")

        if letter_spacing:
            attrs["letter-spacing"] = str(letter_spacing)
        if text_decoration != "none":
            attrs["text-decoration"] = text_decoration

        # Adjust y for baseline (SVG text uses baseline, not top)
        attrs["y"] = str(y + font_size * 0.85)

        text_el = ET.Element("text", attrs)

        # Handle multi-line text
        lines = text_content.split("\n")
        if len(lines) > 1:
            for i, line in enumerate(lines):
                tspan = ET.SubElement(text_el, "tspan", {
                    "x": str(x),
                    "dy": str(font_size * line_height) if i > 0 else "0"
                })
                tspan.text = line
        else:
            text_el.text = text_content

        return text_el

    def _render_group(self, obj: Dict[str, Any]) -> ET.Element:
        """Render group of objects."""
        group = ET.Element("g")

        children = obj.get("objects", obj.get("children", []))
        for child in children:
            child_el = self._render_object(child)
            if child_el is not None:
                group.append(child_el)

        return group

    def _render_image(self, obj: Dict[str, Any]) -> ET.Element:
        """Render image element."""
        x = obj.get("x", 0)
        y = obj.get("y", 0)
        width = obj.get("width", 100)
        height = obj.get("height", 100)
        src = obj.get("src", obj.get("url", ""))

        return ET.Element("image", {
            "x": str(x),
            "y": str(y),
            "width": str(width),
            "height": str(height),
            "href": src,
            "preserveAspectRatio": obj.get("preserveAspectRatio", "xMidYMid meet")
        })

    def _apply_transforms(self, element: ET.Element, obj: Dict[str, Any]):
        """Apply transforms to element."""
        transforms = []

        # Rotation around center
        angle = obj.get("angle", 0)
        if angle != 0:
            x = obj.get("x", 0)
            y = obj.get("y", 0)
            width = obj.get("width", 100)
            height = obj.get("height", 100)
            cx = x + width / 2
            cy = y + height / 2
            transforms.append(f"rotate({angle} {cx} {cy})")

        # Scale
        scale_x = obj.get("scaleX", 1)
        scale_y = obj.get("scaleY", 1)
        if scale_x != 1 or scale_y != 1:
            x = obj.get("x", 0)
            y = obj.get("y", 0)
            width = obj.get("width", 100)
            height = obj.get("height", 100)
            cx = x + width / 2
            cy = y + height / 2
            # Translate to origin, scale, translate back
            transforms.append(f"translate({cx} {cy})")
            transforms.append(f"scale({scale_x} {scale_y})")
            transforms.append(f"translate({-cx} {-cy})")

        if transforms:
            element.set("transform", " ".join(transforms))

    def _apply_styles(self, element: ET.Element, obj: Dict[str, Any]):
        """Apply fill, stroke, opacity and effects."""
        tag = element.tag

        # Fill
        fill = obj.get("fill", "#000000")
        gradient = obj.get("gradient")

        if gradient:
            gradient_id = self._add_gradient(gradient)
            fill = f"url(#{gradient_id})"

        if tag not in ("line",):
            element.set("fill", fill)
        else:
            element.set("fill", "none")

        # Stroke
        stroke = obj.get("stroke", "transparent")
        stroke_width = obj.get("strokeWidth", 0)

        if stroke != "transparent" and stroke_width > 0:
            element.set("stroke", stroke)
            element.set("stroke-width", str(stroke_width))
        elif tag == "line":
            # Lines need stroke
            element.set("stroke", fill)
            element.set("stroke-width", str(stroke_width or 2))

        # Opacity
        opacity = obj.get("opacity", 1)
        if opacity < 1:
            element.set("opacity", str(opacity))

        # Shadow filter
        shadow = obj.get("shadow")
        if shadow:
            filter_id = self._add_shadow_filter(shadow)
            element.set("filter", f"url(#{filter_id})")

        # Blend mode
        blend_mode = obj.get("blendMode", "normal")
        if blend_mode != "normal":
            element.set("style", f"mix-blend-mode: {blend_mode};")

        # Object ID
        obj_id = obj.get("id")
        if obj_id:
            element.set("id", obj_id)

    def _add_gradient(self, gradient: Dict[str, Any]) -> str:
        """Add gradient to defs and return its ID."""
        gradient_type = gradient.get("type", "linear")

        # Generate unique ID
        gradient_id = self._generate_id("grad")

        if gradient_type == "linear":
            grad_el = self._create_linear_gradient(gradient_id, gradient)
        elif gradient_type == "radial":
            grad_el = self._create_radial_gradient(gradient_id, gradient)
        else:
            grad_el = self._create_linear_gradient(gradient_id, gradient)

        self.defs.append(grad_el)
        return gradient_id

    def _create_linear_gradient(self, gradient_id: str, gradient: Dict[str, Any]) -> ET.Element:
        """Create linear gradient element."""
        angle = gradient.get("angle", 0)

        # Convert angle to x1,y1,x2,y2
        rad = math.radians(angle)
        x1 = 50 - 50 * math.cos(rad)
        y1 = 50 - 50 * math.sin(rad)
        x2 = 50 + 50 * math.cos(rad)
        y2 = 50 + 50 * math.sin(rad)

        grad = ET.Element("linearGradient", {
            "id": gradient_id,
            "x1": f"{x1}%",
            "y1": f"{y1}%",
            "x2": f"{x2}%",
            "y2": f"{y2}%"
        })

        stops = gradient.get("stops", [
            {"offset": 0, "color": "#000000"},
            {"offset": 1, "color": "#FFFFFF"}
        ])

        for stop in stops:
            stop_el = ET.SubElement(grad, "stop", {
                "offset": f"{stop.get('offset', 0) * 100}%",
                "stop-color": stop.get("color", "#000000"),
                "stop-opacity": str(stop.get("opacity", 1))
            })

        return grad

    def _create_radial_gradient(self, gradient_id: str, gradient: Dict[str, Any]) -> ET.Element:
        """Create radial gradient element."""
        cx = gradient.get("cx", 50)
        cy = gradient.get("cy", 50)
        r = gradient.get("r", 50)

        grad = ET.Element("radialGradient", {
            "id": gradient_id,
            "cx": f"{cx}%",
            "cy": f"{cy}%",
            "r": f"{r}%"
        })

        stops = gradient.get("stops", [
            {"offset": 0, "color": "#000000"},
            {"offset": 1, "color": "#FFFFFF"}
        ])

        for stop in stops:
            ET.SubElement(grad, "stop", {
                "offset": f"{stop.get('offset', 0) * 100}%",
                "stop-color": stop.get("color", "#000000"),
                "stop-opacity": str(stop.get("opacity", 1))
            })

        return grad

    def _add_shadow_filter(self, shadow: Dict[str, Any]) -> str:
        """Add drop shadow filter to defs."""
        filter_id = self._generate_id("shadow")

        offset_x = shadow.get("offsetX", 4)
        offset_y = shadow.get("offsetY", 4)
        blur = shadow.get("blur", 0)
        color = shadow.get("color", "rgba(0,0,0,0.5)")

        # Parse color
        rgba = self._parse_color(color)

        filter_el = ET.Element("filter", {
            "id": filter_id,
            "x": "-50%",
            "y": "-50%",
            "width": "200%",
            "height": "200%"
        })

        # feDropShadow
        drop = ET.SubElement(filter_el, "feDropShadow", {
            "dx": str(offset_x),
            "dy": str(offset_y),
            "stdDeviation": str(blur / 2),
            "flood-color": rgba[0],
            "flood-opacity": str(rgba[1])
        })

        self.defs.append(filter_el)
        return filter_id

    def _parse_color(self, color: str) -> Tuple[str, float]:
        """Parse color string to (hex, opacity)."""
        if color.startswith("rgba"):
            match = re.match(r"rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)", color)
            if match:
                r, g, b, a = match.groups()
                hex_color = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
                return (hex_color, float(a))
        elif color.startswith("rgb"):
            match = re.match(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", color)
            if match:
                r, g, b = match.groups()
                hex_color = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
                return (hex_color, 1.0)
        return (color, 1.0)

    def _generate_regular_polygon(self, cx: float, cy: float, radius: float, sides: int) -> List[Tuple[float, float]]:
        """Generate points for regular polygon."""
        points = []
        for i in range(sides):
            angle = (2 * math.pi * i / sides) - math.pi / 2
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            points.append((x, y))
        return points

    def _generate_star_points(
        self, cx: float, cy: float,
        outer_r: float, inner_r: float, points: int
    ) -> List[Tuple[float, float]]:
        """Generate points for star shape."""
        star_points = []
        for i in range(points * 2):
            angle = (math.pi * i / points) - math.pi / 2
            r = outer_r if i % 2 == 0 else inner_r
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            star_points.append((x, y))
        return star_points

    def _to_string(self, root: ET.Element) -> str:
        """Convert element tree to string."""
        if self.config.pretty_print:
            self._indent(root)

        return ET.tostring(root, encoding="unicode", method="xml")

    def _indent(self, elem: ET.Element, level: int = 0):
        """Add indentation to element tree."""
        indent = "\n" + "  " * level
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent


# Singleton instance
_renderer = SVGRenderer()


def render_canvas_to_svg(canvas_state: Dict[str, Any], config: Optional[SVGConfig] = None) -> str:
    """
    Render canvas state to SVG string.

    Args:
        canvas_state: Dictionary with width, height, background, objects
        config: Optional SVG configuration

    Returns:
        SVG string
    """
    renderer = SVGRenderer(config) if config else _renderer
    return renderer.render(canvas_state)


def create_svg_element(obj_type: str, properties: Dict[str, Any]) -> str:
    """
    Create a single SVG element from object properties.

    Useful for generating individual elements without full canvas context.
    """
    obj = {"type": obj_type, **properties}
    renderer = SVGRenderer()
    element = renderer._render_object(obj)

    if element is not None:
        return ET.tostring(element, encoding="unicode", method="xml")
    return ""
