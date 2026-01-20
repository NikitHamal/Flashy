"""
SVG Design Tools Module

This module provides SVG-based design tools for the Flashy Design Agent.
Instead of JSON-based canvas manipulation, the AI generates SVG code directly
which is then rendered and made editable by the frontend.

Key Features:
- Direct SVG generation by AI
- Full SVG element support (shapes, text, paths, gradients, filters)
- SVG parsing and manipulation
- Export to various formats
"""

import re
import uuid
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import html
import json


class SVGElementType(Enum):
    """Supported SVG element types."""
    RECT = "rect"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    LINE = "line"
    POLYLINE = "polyline"
    POLYGON = "polygon"
    PATH = "path"
    TEXT = "text"
    TSPAN = "tspan"
    IMAGE = "image"
    GROUP = "g"
    DEFS = "defs"
    LINEAR_GRADIENT = "linearGradient"
    RADIAL_GRADIENT = "radialGradient"
    PATTERN = "pattern"
    FILTER = "filter"
    CLIP_PATH = "clipPath"
    MASK = "mask"
    USE = "use"
    SYMBOL = "symbol"


@dataclass
class SVGCanvas:
    """Represents an SVG canvas with its content."""
    width: int = 1200
    height: int = 800
    viewBox: str = "0 0 1200 800"
    background: str = "#ffffff"
    svg_content: str = ""
    elements: List[Dict[str, Any]] = field(default_factory=list)
    defs: str = ""  # Gradient and filter definitions
    
    def to_svg(self) -> str:
        """Generate complete SVG string."""
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" 
     width="{self.width}" height="{self.height}" 
     viewBox="{self.viewBox}"
     style="background-color: {self.background}">
'''
        if self.defs:
            svg += f"  <defs>\n{self.defs}  </defs>\n"
        
        if self.svg_content:
            svg += self.svg_content
        
        svg += "</svg>"
        return svg
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "width": self.width,
            "height": self.height,
            "viewBox": self.viewBox,
            "background": self.background,
            "svg": self.to_svg(),
            "elements": self.elements
        }


class SVGTools:
    """
    SVG-based design tools.
    
    The AI generates SVG code directly, which is then:
    1. Validated and sanitized
    2. Parsed into editable elements
    3. Rendered by the frontend
    4. Made interactive for user customization
    """
    
    # Allowed SVG elements (security)
    ALLOWED_ELEMENTS = {
        'svg', 'g', 'defs', 'symbol', 'use',
        'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon', 'path',
        'text', 'tspan', 'textPath',
        'image',
        'linearGradient', 'radialGradient', 'stop', 'pattern',
        'filter', 'feGaussianBlur', 'feOffset', 'feBlend', 'feColorMatrix',
        'feFlood', 'feComposite', 'feMerge', 'feMergeNode', 'feDropShadow',
        'clipPath', 'mask',
        'title', 'desc',
        'animate', 'animateTransform', 'animateMotion'
    }
    
    # Allowed SVG attributes (security)
    ALLOWED_ATTRIBUTES = {
        # Core attributes
        'id', 'class', 'style', 'transform',
        # Presentation attributes
        'fill', 'stroke', 'stroke-width', 'stroke-linecap', 'stroke-linejoin',
        'stroke-dasharray', 'stroke-dashoffset', 'stroke-opacity', 'fill-opacity',
        'opacity', 'fill-rule', 'clip-rule',
        # Geometry attributes
        'x', 'y', 'x1', 'y1', 'x2', 'y2', 'cx', 'cy', 'r', 'rx', 'ry',
        'width', 'height', 'd', 'points', 'pathLength',
        # Text attributes
        'font-family', 'font-size', 'font-weight', 'font-style',
        'text-anchor', 'dominant-baseline', 'letter-spacing', 'word-spacing',
        'text-decoration', 'dx', 'dy',
        # Gradient attributes
        'gradientUnits', 'gradientTransform', 'spreadMethod',
        'offset', 'stop-color', 'stop-opacity',
        # Filter attributes
        'filter', 'filterUnits', 'primitiveUnits',
        'stdDeviation', 'in', 'in2', 'result', 'mode',
        # Image attributes
        'href', 'xlink:href', 'preserveAspectRatio',
        # Clip/Mask attributes
        'clip-path', 'mask',
        # Animation attributes
        'attributeName', 'from', 'to', 'dur', 'repeatCount', 'begin', 'values',
        # Other
        'viewBox', 'xmlns', 'xmlns:xlink', 'version',
        'data-id', 'data-type', 'data-label'
    }
    
    def __init__(self, width: int = 1200, height: int = 800):
        self.canvas = SVGCanvas(
            width=width,
            height=height,
            viewBox=f"0 0 {width} {height}"
        )
        self.history: List[str] = []
        self.history_index: int = -1
        self._save_state()
    
    def _generate_id(self) -> str:
        """Generate unique element ID."""
        return f"el_{uuid.uuid4().hex[:8]}"
    
    def _save_state(self):
        """Save current state to history."""
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        
        self.history.append(self.canvas.to_svg())
        
        if len(self.history) > 50:
            self.history.pop(0)
        else:
            self.history_index += 1
    
    def get_available_tools(self) -> List[Dict[str, str]]:
        """Get list of available SVG tools."""
        return [
            # Core SVG generation
            {"name": "set_svg", "description": "Set the complete SVG content (AI generates full SVG)"},
            {"name": "append_svg", "description": "Append SVG elements to existing content"},
            {"name": "replace_element", "description": "Replace a specific SVG element by ID"},
            {"name": "remove_element", "description": "Remove an SVG element by ID"},
            
            # Element creation helpers
            {"name": "add_rect", "description": "Add a rectangle element"},
            {"name": "add_circle", "description": "Add a circle element"},
            {"name": "add_ellipse", "description": "Add an ellipse element"},
            {"name": "add_line", "description": "Add a line element"},
            {"name": "add_path", "description": "Add a path element"},
            {"name": "add_polygon", "description": "Add a polygon element"},
            {"name": "add_text", "description": "Add a text element"},
            {"name": "add_image", "description": "Add an image element"},
            {"name": "add_group", "description": "Add a group element with children"},
            
            # Styling
            {"name": "add_gradient", "description": "Add a gradient definition"},
            {"name": "add_filter", "description": "Add a filter definition"},
            {"name": "apply_style", "description": "Apply styles to an element"},
            
            # Canvas operations
            {"name": "set_canvas_size", "description": "Set canvas dimensions"},
            {"name": "set_background", "description": "Set canvas background color"},
            {"name": "clear_canvas", "description": "Clear all SVG content"},
            {"name": "get_svg", "description": "Get current SVG content"},
            
            # Element manipulation
            {"name": "transform_element", "description": "Apply transform to element"},
            {"name": "update_attribute", "description": "Update element attribute"},
            
            # Information
            {"name": "list_elements", "description": "List all elements with IDs"},
            {"name": "get_element", "description": "Get element details by ID"},
            
            # History
            {"name": "undo", "description": "Undo last action"},
            {"name": "redo", "description": "Redo last undone action"}
        ]
    
    async def execute(self, tool_name: str, **kwargs) -> str:
        """Execute a tool by name."""
        method = getattr(self, tool_name, None)
        if method is None:
            return f"Error: Unknown tool '{tool_name}'"
        
        try:
            result = method(**kwargs)
            return result
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
    
    def sanitize_svg(self, svg: str) -> str:
        """
        Sanitize SVG content for security.
        Removes potentially dangerous elements and attributes.
        """
        try:
            # Parse SVG
            root = ET.fromstring(svg)
            
            # Recursively sanitize
            self._sanitize_element(root)
            
            # Convert back to string
            return ET.tostring(root, encoding='unicode')
        except ET.ParseError as e:
            # If parsing fails, do basic sanitization
            return self._basic_sanitize(svg)
    
    def _sanitize_element(self, element: ET.Element):
        """Recursively sanitize an element."""
        # Check tag
        tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag
        
        if tag.lower() not in self.ALLOWED_ELEMENTS:
            element.clear()
            return
        
        # Remove disallowed attributes
        attribs_to_remove = []
        for attr in element.attrib:
            attr_name = attr.split('}')[-1] if '}' in attr else attr
            if attr_name.lower() not in self.ALLOWED_ATTRIBUTES:
                attribs_to_remove.append(attr)
            # Remove javascript: URLs
            elif element.attrib[attr].lower().startswith('javascript:'):
                attribs_to_remove.append(attr)
        
        for attr in attribs_to_remove:
            del element.attrib[attr]
        
        # Sanitize children
        for child in list(element):
            self._sanitize_element(child)
    
    def _basic_sanitize(self, svg: str) -> str:
        """Basic sanitization when parsing fails."""
        # Remove script tags
        svg = re.sub(r'<script[^>]*>.*?</script>', '', svg, flags=re.DOTALL | re.IGNORECASE)
        # Remove event handlers
        svg = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', svg, flags=re.IGNORECASE)
        # Remove javascript: URLs
        svg = re.sub(r'javascript:', '', svg, flags=re.IGNORECASE)
        return svg
    
    def parse_elements(self, svg: str) -> List[Dict[str, Any]]:
        """Parse SVG and extract elements with their properties."""
        elements = []
        
        try:
            root = ET.fromstring(svg)
            self._extract_elements(root, elements)
        except ET.ParseError:
            pass
        
        return elements
    
    def _extract_elements(self, element: ET.Element, elements: List[Dict[str, Any]], parent_id: str = None):
        """Recursively extract elements."""
        tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag
        
        # Skip defs, they're definitions not visual elements
        if tag.lower() == 'defs':
            return
        
        elem_data = {
            "tag": tag,
            "id": element.attrib.get('id') or element.attrib.get('data-id'),
            "attributes": dict(element.attrib),
            "parent": parent_id
        }
        
        if tag.lower() in ('text', 'tspan'):
            elem_data["text"] = element.text or ""
        
        if elem_data["id"]:
            elements.append(elem_data)
        
        # Process children
        for child in element:
            self._extract_elements(child, elements, elem_data.get("id"))
    
    # === Core SVG Tools ===
    
    def set_svg(self, svg: str) -> str:
        """
        Set complete SVG content. 
        The AI generates the full SVG which is sanitized and stored.
        """
        # Clean up: extract inner content if full SVG provided
        svg = svg.strip()
        
        # If it's a complete SVG, extract dimensions and content
        if svg.startswith('<svg'):
            try:
                root = ET.fromstring(svg)
                
                # Extract dimensions
                width = root.attrib.get('width', str(self.canvas.width))
                height = root.attrib.get('height', str(self.canvas.height))
                viewBox = root.attrib.get('viewBox', f"0 0 {width} {height}")
                
                # Try to parse width/height
                try:
                    self.canvas.width = int(re.sub(r'[^\d]', '', str(width)) or 1200)
                    self.canvas.height = int(re.sub(r'[^\d]', '', str(height)) or 800)
                except ValueError:
                    pass
                
                self.canvas.viewBox = viewBox
                
                # Extract defs
                defs_elem = root.find('.//{http://www.w3.org/2000/svg}defs')
                if defs_elem is None:
                    defs_elem = root.find('.//defs')
                
                if defs_elem is not None:
                    self.canvas.defs = ET.tostring(defs_elem, encoding='unicode')
                    # Remove defs from content
                    root.remove(defs_elem)
                
                # Get inner content
                inner_content = ""
                for child in root:
                    inner_content += ET.tostring(child, encoding='unicode')
                
                svg = inner_content
                
            except ET.ParseError:
                # If parsing fails, use basic extraction
                inner_match = re.search(r'<svg[^>]*>(.*)</svg>', svg, re.DOTALL)
                if inner_match:
                    svg = inner_match.group(1)
        
        # Sanitize
        svg = self._basic_sanitize(svg)
        
        self.canvas.svg_content = svg
        self.canvas.elements = self.parse_elements(self.canvas.to_svg())
        
        self._save_state()
        
        element_count = len(self.canvas.elements)
        return f"SVG content set successfully ({element_count} elements)"
    
    def append_svg(self, svg: str) -> str:
        """Append SVG elements to existing content."""
        svg = self._basic_sanitize(svg.strip())
        self.canvas.svg_content += "\n" + svg
        self.canvas.elements = self.parse_elements(self.canvas.to_svg())
        self._save_state()
        return f"Appended SVG content"
    
    def replace_element(self, element_id: str, new_svg: str) -> str:
        """Replace a specific element by ID."""
        # Create pattern to find and replace element
        pattern = rf'(<[^>]*\s+id=["\']?{re.escape(element_id)}["\']?[^>]*>.*?</[^>]+>|<[^>]*\s+id=["\']?{re.escape(element_id)}["\']?[^>]*/\s*>)'
        
        new_svg = self._basic_sanitize(new_svg.strip())
        
        new_content, count = re.subn(pattern, new_svg, self.canvas.svg_content, flags=re.DOTALL)
        
        if count > 0:
            self.canvas.svg_content = new_content
            self.canvas.elements = self.parse_elements(self.canvas.to_svg())
            self._save_state()
            return f"Replaced element '{element_id}'"
        
        return f"Error: Element '{element_id}' not found"
    
    def remove_element(self, element_id: str) -> str:
        """Remove an element by ID."""
        pattern = rf'(<[^>]*\s+id=["\']?{re.escape(element_id)}["\']?[^>]*>.*?</[^>]+>|<[^>]*\s+id=["\']?{re.escape(element_id)}["\']?[^>]*/\s*>)'
        
        new_content, count = re.subn(pattern, '', self.canvas.svg_content, flags=re.DOTALL)
        
        if count > 0:
            self.canvas.svg_content = new_content
            self.canvas.elements = self.parse_elements(self.canvas.to_svg())
            self._save_state()
            return f"Removed element '{element_id}'"
        
        return f"Error: Element '{element_id}' not found"
    
    # === Element Creation ===
    
    def add_rect(
        self, x: float = 0, y: float = 0,
        width: float = 100, height: float = 100,
        fill: str = "#4A90D9", stroke: str = "none",
        stroke_width: float = 0, rx: float = 0, ry: float = 0,
        opacity: float = 1, transform: str = "",
        id: str = None
    ) -> str:
        """Add a rectangle element."""
        elem_id = id or self._generate_id()
        
        attrs = [
            f'id="{elem_id}"',
            f'x="{x}"',
            f'y="{y}"',
            f'width="{width}"',
            f'height="{height}"',
            f'fill="{fill}"'
        ]
        
        if stroke != "none":
            attrs.append(f'stroke="{stroke}"')
            attrs.append(f'stroke-width="{stroke_width}"')
        
        if rx > 0:
            attrs.append(f'rx="{rx}"')
        if ry > 0:
            attrs.append(f'ry="{ry}"')
        if opacity < 1:
            attrs.append(f'opacity="{opacity}"')
        if transform:
            attrs.append(f'transform="{transform}"')
        
        svg = f'<rect {" ".join(attrs)} />'
        self.canvas.svg_content += "\n  " + svg
        self.canvas.elements = self.parse_elements(self.canvas.to_svg())
        self._save_state()
        
        return f"Added rectangle with ID: {elem_id}"
    
    def add_circle(
        self, cx: float = 50, cy: float = 50, r: float = 50,
        fill: str = "#4A90D9", stroke: str = "none",
        stroke_width: float = 0, opacity: float = 1,
        transform: str = "", id: str = None
    ) -> str:
        """Add a circle element."""
        elem_id = id or self._generate_id()
        
        attrs = [
            f'id="{elem_id}"',
            f'cx="{cx}"',
            f'cy="{cy}"',
            f'r="{r}"',
            f'fill="{fill}"'
        ]
        
        if stroke != "none":
            attrs.append(f'stroke="{stroke}"')
            attrs.append(f'stroke-width="{stroke_width}"')
        if opacity < 1:
            attrs.append(f'opacity="{opacity}"')
        if transform:
            attrs.append(f'transform="{transform}"')
        
        svg = f'<circle {" ".join(attrs)} />'
        self.canvas.svg_content += "\n  " + svg
        self.canvas.elements = self.parse_elements(self.canvas.to_svg())
        self._save_state()
        
        return f"Added circle with ID: {elem_id}"
    
    def add_ellipse(
        self, cx: float = 100, cy: float = 50,
        rx: float = 100, ry: float = 50,
        fill: str = "#4A90D9", stroke: str = "none",
        stroke_width: float = 0, opacity: float = 1,
        transform: str = "", id: str = None
    ) -> str:
        """Add an ellipse element."""
        elem_id = id or self._generate_id()
        
        attrs = [
            f'id="{elem_id}"',
            f'cx="{cx}"',
            f'cy="{cy}"',
            f'rx="{rx}"',
            f'ry="{ry}"',
            f'fill="{fill}"'
        ]
        
        if stroke != "none":
            attrs.append(f'stroke="{stroke}"')
            attrs.append(f'stroke-width="{stroke_width}"')
        if opacity < 1:
            attrs.append(f'opacity="{opacity}"')
        if transform:
            attrs.append(f'transform="{transform}"')
        
        svg = f'<ellipse {" ".join(attrs)} />'
        self.canvas.svg_content += "\n  " + svg
        self.canvas.elements = self.parse_elements(self.canvas.to_svg())
        self._save_state()
        
        return f"Added ellipse with ID: {elem_id}"
    
    def add_line(
        self, x1: float = 0, y1: float = 0,
        x2: float = 100, y2: float = 100,
        stroke: str = "#000000", stroke_width: float = 2,
        stroke_linecap: str = "round", opacity: float = 1,
        transform: str = "", id: str = None
    ) -> str:
        """Add a line element."""
        elem_id = id or self._generate_id()
        
        attrs = [
            f'id="{elem_id}"',
            f'x1="{x1}"',
            f'y1="{y1}"',
            f'x2="{x2}"',
            f'y2="{y2}"',
            f'stroke="{stroke}"',
            f'stroke-width="{stroke_width}"',
            f'stroke-linecap="{stroke_linecap}"'
        ]
        
        if opacity < 1:
            attrs.append(f'opacity="{opacity}"')
        if transform:
            attrs.append(f'transform="{transform}"')
        
        svg = f'<line {" ".join(attrs)} />'
        self.canvas.svg_content += "\n  " + svg
        self.canvas.elements = self.parse_elements(self.canvas.to_svg())
        self._save_state()
        
        return f"Added line with ID: {elem_id}"
    
    def add_path(
        self, d: str, fill: str = "none",
        stroke: str = "#000000", stroke_width: float = 2,
        stroke_linecap: str = "round", stroke_linejoin: str = "round",
        opacity: float = 1, transform: str = "", id: str = None
    ) -> str:
        """Add a path element."""
        elem_id = id or self._generate_id()
        
        # Sanitize path data
        d = html.escape(d)
        
        attrs = [
            f'id="{elem_id}"',
            f'd="{d}"',
            f'fill="{fill}"',
            f'stroke="{stroke}"',
            f'stroke-width="{stroke_width}"',
            f'stroke-linecap="{stroke_linecap}"',
            f'stroke-linejoin="{stroke_linejoin}"'
        ]
        
        if opacity < 1:
            attrs.append(f'opacity="{opacity}"')
        if transform:
            attrs.append(f'transform="{transform}"')
        
        svg = f'<path {" ".join(attrs)} />'
        self.canvas.svg_content += "\n  " + svg
        self.canvas.elements = self.parse_elements(self.canvas.to_svg())
        self._save_state()
        
        return f"Added path with ID: {elem_id}"
    
    def add_polygon(
        self, points: str, fill: str = "#4A90D9",
        stroke: str = "none", stroke_width: float = 0,
        opacity: float = 1, transform: str = "", id: str = None
    ) -> str:
        """Add a polygon element."""
        elem_id = id or self._generate_id()
        
        attrs = [
            f'id="{elem_id}"',
            f'points="{points}"',
            f'fill="{fill}"'
        ]
        
        if stroke != "none":
            attrs.append(f'stroke="{stroke}"')
            attrs.append(f'stroke-width="{stroke_width}"')
        if opacity < 1:
            attrs.append(f'opacity="{opacity}"')
        if transform:
            attrs.append(f'transform="{transform}"')
        
        svg = f'<polygon {" ".join(attrs)} />'
        self.canvas.svg_content += "\n  " + svg
        self.canvas.elements = self.parse_elements(self.canvas.to_svg())
        self._save_state()
        
        return f"Added polygon with ID: {elem_id}"
    
    def add_text(
        self, x: float = 0, y: float = 0,
        text: str = "Text", font_size: int = 24,
        font_family: str = "Inter, sans-serif",
        font_weight: str = "normal", fill: str = "#000000",
        text_anchor: str = "start", opacity: float = 1,
        transform: str = "", id: str = None
    ) -> str:
        """Add a text element."""
        elem_id = id or self._generate_id()
        
        # Escape text content
        text = html.escape(text)
        
        attrs = [
            f'id="{elem_id}"',
            f'x="{x}"',
            f'y="{y}"',
            f'font-size="{font_size}"',
            f'font-family="{font_family}"',
            f'font-weight="{font_weight}"',
            f'fill="{fill}"',
            f'text-anchor="{text_anchor}"'
        ]
        
        if opacity < 1:
            attrs.append(f'opacity="{opacity}"')
        if transform:
            attrs.append(f'transform="{transform}"')
        
        svg = f'<text {" ".join(attrs)}>{text}</text>'
        self.canvas.svg_content += "\n  " + svg
        self.canvas.elements = self.parse_elements(self.canvas.to_svg())
        self._save_state()
        
        return f"Added text with ID: {elem_id}"
    
    def add_image(
        self, x: float = 0, y: float = 0,
        width: float = 200, height: float = 200,
        href: str = "", opacity: float = 1,
        transform: str = "", id: str = None
    ) -> str:
        """Add an image element."""
        elem_id = id or self._generate_id()
        
        # Sanitize URL
        href = html.escape(href)
        
        attrs = [
            f'id="{elem_id}"',
            f'x="{x}"',
            f'y="{y}"',
            f'width="{width}"',
            f'height="{height}"',
            f'href="{href}"',
            'preserveAspectRatio="xMidYMid meet"'
        ]
        
        if opacity < 1:
            attrs.append(f'opacity="{opacity}"')
        if transform:
            attrs.append(f'transform="{transform}"')
        
        svg = f'<image {" ".join(attrs)} />'
        self.canvas.svg_content += "\n  " + svg
        self.canvas.elements = self.parse_elements(self.canvas.to_svg())
        self._save_state()
        
        return f"Added image with ID: {elem_id}"
    
    def add_group(
        self, elements_svg: str, opacity: float = 1,
        transform: str = "", id: str = None
    ) -> str:
        """Add a group with child elements."""
        elem_id = id or self._generate_id()
        
        elements_svg = self._basic_sanitize(elements_svg)
        
        attrs = [f'id="{elem_id}"']
        if opacity < 1:
            attrs.append(f'opacity="{opacity}"')
        if transform:
            attrs.append(f'transform="{transform}"')
        
        svg = f'<g {" ".join(attrs)}>\n{elements_svg}\n</g>'
        self.canvas.svg_content += "\n  " + svg
        self.canvas.elements = self.parse_elements(self.canvas.to_svg())
        self._save_state()
        
        return f"Added group with ID: {elem_id}"
    
    # === Styling Tools ===
    
    def add_gradient(
        self, gradient_id: str,
        gradient_type: str = "linear",  # linear or radial
        colors: List[str] = None,
        stops: List[float] = None,
        x1: str = "0%", y1: str = "0%",
        x2: str = "100%", y2: str = "0%",  # for linear
        cx: str = "50%", cy: str = "50%", r: str = "50%"  # for radial
    ) -> str:
        """Add a gradient definition."""
        if colors is None:
            colors = ["#667eea", "#764ba2"]
        
        if stops is None:
            stops = [i / (len(colors) - 1) for i in range(len(colors))]
        
        stop_elements = ""
        for color, offset in zip(colors, stops):
            stop_elements += f'    <stop offset="{offset * 100}%" stop-color="{color}" />\n'
        
        if gradient_type == "linear":
            gradient_svg = f'''    <linearGradient id="{gradient_id}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">
{stop_elements}    </linearGradient>
'''
        else:  # radial
            gradient_svg = f'''    <radialGradient id="{gradient_id}" cx="{cx}" cy="{cy}" r="{r}">
{stop_elements}    </radialGradient>
'''
        
        self.canvas.defs += gradient_svg
        self._save_state()
        
        return f"Added {gradient_type} gradient with ID: {gradient_id}. Use fill=\"url(#{gradient_id})\" to apply."
    
    def add_filter(
        self, filter_id: str,
        filter_type: str = "shadow",  # shadow, blur, glow
        blur: float = 4,
        offset_x: float = 2, offset_y: float = 2,
        color: str = "rgba(0,0,0,0.3)"
    ) -> str:
        """Add a filter definition."""
        if filter_type == "shadow":
            filter_svg = f'''    <filter id="{filter_id}" x="-50%" y="-50%" width="200%" height="200%">
      <feDropShadow dx="{offset_x}" dy="{offset_y}" stdDeviation="{blur}" flood-color="{color}" />
    </filter>
'''
        elif filter_type == "blur":
            filter_svg = f'''    <filter id="{filter_id}">
      <feGaussianBlur stdDeviation="{blur}" />
    </filter>
'''
        elif filter_type == "glow":
            filter_svg = f'''    <filter id="{filter_id}" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="{blur}" result="blur" />
      <feFlood flood-color="{color}" result="color" />
      <feComposite in="color" in2="blur" operator="in" result="glow" />
      <feMerge>
        <feMergeNode in="glow" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
'''
        else:
            return f"Error: Unknown filter type '{filter_type}'"
        
        self.canvas.defs += filter_svg
        self._save_state()
        
        return f"Added {filter_type} filter with ID: {filter_id}. Use filter=\"url(#{filter_id})\" to apply."
    
    def apply_style(self, element_id: str, styles: Dict[str, Any]) -> str:
        """Apply styles to an element by updating its attributes."""
        # Build style updates
        for attr, value in styles.items():
            self.update_attribute(element_id, attr, str(value))
        
        return f"Applied styles to '{element_id}'"
    
    # === Canvas Operations ===
    
    def set_canvas_size(self, width: int, height: int) -> str:
        """Set canvas dimensions."""
        self.canvas.width = width
        self.canvas.height = height
        self.canvas.viewBox = f"0 0 {width} {height}"
        self._save_state()
        return f"Set canvas size to {width}x{height}"
    
    def set_background(self, color: str) -> str:
        """Set canvas background color."""
        self.canvas.background = color
        self._save_state()
        return f"Set background to {color}"
    
    def clear_canvas(self) -> str:
        """Clear all SVG content."""
        self.canvas.svg_content = ""
        self.canvas.defs = ""
        self.canvas.elements = []
        self._save_state()
        return "Cleared canvas"
    
    def get_svg(self) -> str:
        """Get current SVG content."""
        return self.canvas.to_svg()
    
    # === Element Manipulation ===
    
    def transform_element(self, element_id: str, transform: str) -> str:
        """Apply transform to an element."""
        return self.update_attribute(element_id, "transform", transform)
    
    def update_attribute(self, element_id: str, attribute: str, value: str) -> str:
        """Update an element's attribute."""
        # Pattern to find element and update/add attribute
        pattern = rf'(<[^>]*\s+id=["\']?{re.escape(element_id)}["\']?)([^>]*)(/?>\s*)'
        
        def replacer(match):
            before = match.group(1)
            attrs = match.group(2)
            after = match.group(3)
            
            # Check if attribute exists
            attr_pattern = rf'\s+{re.escape(attribute)}=["\'][^"\']*["\']'
            if re.search(attr_pattern, attrs):
                # Update existing
                attrs = re.sub(attr_pattern, f' {attribute}="{value}"', attrs)
            else:
                # Add new
                attrs += f' {attribute}="{value}"'
            
            return before + attrs + after
        
        new_content, count = re.subn(pattern, replacer, self.canvas.svg_content)
        
        if count > 0:
            self.canvas.svg_content = new_content
            self._save_state()
            return f"Updated {attribute} of '{element_id}'"
        
        return f"Error: Element '{element_id}' not found"
    
    # === Information ===
    
    def list_elements(self) -> str:
        """List all elements with IDs."""
        if not self.canvas.elements:
            return "Canvas is empty"
        
        lines = ["Elements on canvas:"]
        for elem in self.canvas.elements:
            attrs = elem.get('attributes', {})
            info = f"  - {elem['id']}: <{elem['tag']}>"
            if 'x' in attrs and 'y' in attrs:
                info += f" at ({attrs.get('x', '?')}, {attrs.get('y', '?')})"
            if 'text' in elem:
                info += f" \"{elem['text'][:20]}...\""
            lines.append(info)
        
        return "\n".join(lines)
    
    def get_element(self, element_id: str) -> str:
        """Get element details by ID."""
        for elem in self.canvas.elements:
            if elem.get('id') == element_id:
                return json.dumps(elem, indent=2)
        
        return f"Error: Element '{element_id}' not found"
    
    # === History ===
    
    def undo(self) -> str:
        """Undo last action."""
        if self.history_index > 0:
            self.history_index -= 1
            self.canvas.svg_content = ""
            # Restore from history (need to re-parse)
            svg = self.history[self.history_index]
            try:
                root = ET.fromstring(svg)
                inner_content = ""
                for child in root:
                    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    if tag != 'defs':
                        inner_content += ET.tostring(child, encoding='unicode')
                self.canvas.svg_content = inner_content
            except:
                pass
            self.canvas.elements = self.parse_elements(svg)
            return "Undone last action"
        return "Nothing to undo"
    
    def redo(self) -> str:
        """Redo last undone action."""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            svg = self.history[self.history_index]
            try:
                root = ET.fromstring(svg)
                inner_content = ""
                for child in root:
                    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    if tag != 'defs':
                        inner_content += ET.tostring(child, encoding='unicode')
                self.canvas.svg_content = inner_content
            except:
                pass
            self.canvas.elements = self.parse_elements(svg)
            return "Redone action"
        return "Nothing to redo"
    
    # === Load/Export ===
    
    def load_state(self, state_dict: Dict[str, Any]) -> str:
        """Load canvas state from dictionary."""
        try:
            self.canvas.width = state_dict.get("width", 1200)
            self.canvas.height = state_dict.get("height", 800)
            self.canvas.viewBox = state_dict.get("viewBox", f"0 0 {self.canvas.width} {self.canvas.height}")
            self.canvas.background = state_dict.get("background", "#ffffff")
            
            svg = state_dict.get("svg", "")
            if svg:
                self.set_svg(svg)
            
            return f"Loaded SVG canvas"
        except Exception as e:
            return f"Error loading state: {str(e)}"
