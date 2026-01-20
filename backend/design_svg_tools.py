"""
SVG Design Tools

Minimal SVG-based canvas state for the new design agent.
"""

from __future__ import annotations

import uuid
from typing import Dict, Any, List, Optional
import xml.etree.ElementTree as ET


SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def _ensure_svg_root(svg: str, width: int, height: int, background: str) -> str:
    if "<svg" not in svg:
        return _base_svg(width, height, background)
    return svg


def _base_svg(width: int, height: int, background: str) -> str:
    svg = ET.Element("svg", {
        "xmlns": SVG_NS,
        "width": str(width),
        "height": str(height),
        "viewBox": f"0 0 {width} {height}"
    })
    bg = ET.SubElement(svg, "rect", {
        "id": "bg",
        "x": "0",
        "y": "0",
        "width": str(width),
        "height": str(height),
        "fill": background
    })
    ET.SubElement(svg, "g", {"id": "artwork"})
    return ET.tostring(svg, encoding="unicode")


class SvgDesignTools:
    def __init__(self, canvas_width: int = 1200, canvas_height: int = 800, background: str = "#FFFFFF"):
        self.width = canvas_width
        self.height = canvas_height
        self.background = background
        self.svg = _base_svg(canvas_width, canvas_height, background)

    def get_available_tools(self) -> List[Dict[str, str]]:
        return [
            {"name": "set_svg", "description": "Replace full SVG markup"},
            {"name": "set_canvas", "description": "Update canvas width/height/background"},
            {"name": "insert_element", "description": "Insert an SVG element into the artwork layer"},
            {"name": "update_element", "description": "Update SVG element attributes by id"},
            {"name": "remove_element", "description": "Remove an SVG element by id"}
        ]

    def to_state(self) -> Dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "background": self.background,
            "svg": self.svg
        }

    def load_state(self, state: Dict[str, Any]) -> str:
        self.width = int(state.get("width", self.width))
        self.height = int(state.get("height", self.height))
        self.background = state.get("background", self.background)
        self.svg = _ensure_svg_root(state.get("svg", ""), self.width, self.height, self.background)
        return "SVG state loaded"

    def set_svg(self, svg: str) -> str:
        self.svg = _ensure_svg_root(svg, self.width, self.height, self.background)
        return "SVG updated"

    def set_canvas(self, width: int, height: int, background: str) -> str:
        self.width = int(width)
        self.height = int(height)
        self.background = background
        self.svg = _base_svg(self.width, self.height, self.background)
        return "Canvas updated"

    def _parse(self) -> ET.Element:
        return ET.fromstring(self.svg)

    def _serialize(self, root: ET.Element) -> None:
        self.svg = ET.tostring(root, encoding="unicode")

    def insert_element(self, tag: str, attributes: Dict[str, Any], content: Optional[str] = None) -> str:
        root = self._parse()
        artwork = root.find(f".//{{{SVG_NS}}}g[@id='artwork']")
        if artwork is None:
            artwork = ET.SubElement(root, "g", {"id": "artwork"})

        if "id" not in attributes:
            attributes["id"] = f"el_{uuid.uuid4().hex[:8]}"
        element = ET.SubElement(artwork, tag, {str(k): str(v) for k, v in attributes.items()})
        if content:
            element.text = content
        self._serialize(root)
        return f"Inserted {tag} with id {attributes['id']}"

    def update_element(self, element_id: str, attributes: Dict[str, Any]) -> str:
        root = self._parse()
        target = root.find(f".//*[@id='{element_id}']")
        if target is None:
            raise ValueError("Element not found")
        for key, value in attributes.items():
            target.set(str(key), str(value))
        self._serialize(root)
        return f"Updated element {element_id}"

    def remove_element(self, element_id: str) -> str:
        root = self._parse()
        parent_map = {c: p for p in root.iter() for c in p}
        target = root.find(f".//*[@id='{element_id}']")
        if target is None:
            raise ValueError("Element not found")
        parent = parent_map.get(target)
        if parent is not None:
            parent.remove(target)
        self._serialize(root)
        return f"Removed element {element_id}"

    async def execute(self, tool_name: str, **kwargs: Any) -> str:
        if tool_name == "set_svg":
            return self.set_svg(kwargs.get("svg", ""))
        if tool_name == "set_canvas":
            return self.set_canvas(kwargs.get("width"), kwargs.get("height"), kwargs.get("background", self.background))
        if tool_name == "insert_element":
            return self.insert_element(kwargs.get("tag"), kwargs.get("attributes", {}), kwargs.get("content"))
        if tool_name == "update_element":
            return self.update_element(kwargs.get("id"), kwargs.get("attributes", {}))
        if tool_name == "remove_element":
            return self.remove_element(kwargs.get("id"))
        raise ValueError(f"Unknown tool: {tool_name}")
