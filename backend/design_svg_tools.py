"""
SVG Design Tools

Provides SVG-based canvas tools for the Flashy Design agent.
"""

import uuid
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def _ns(tag: str) -> str:
    return f"{{{SVG_NS}}}{tag}"


def _generate_id(prefix: str = "svg") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class SvgDesignTools:
    def __init__(self, canvas_width: int = 1200, canvas_height: int = 800):
        self.width = canvas_width
        self.height = canvas_height
        self.background = "#ffffff"
        self.root = self._create_root()

    def _create_root(self) -> ET.Element:
        svg = ET.Element(_ns("svg"), {
            "xmlns": SVG_NS,
            "id": "design-svg",
            "class": "design-svg",
            "width": str(self.width),
            "height": str(self.height),
            "viewBox": f"0 0 {self.width} {self.height}",
            "fill": "none"
        })
        background = ET.SubElement(svg, _ns("rect"), {
            "id": "svg-background",
            "x": "0",
            "y": "0",
            "width": str(self.width),
            "height": str(self.height),
            "fill": self.background
        })
        return svg

    def _find_element_by_id(self, element_id: str) -> Optional[ET.Element]:
        for el in self.root.iter():
            if el.attrib.get("id") == element_id:
                return el
        return None

    def _serialize(self) -> str:
        return ET.tostring(self.root, encoding="unicode")

    def get_state(self) -> Dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "background": self.background,
            "svg": self._serialize()
        }

    def get_available_tools(self) -> List[Dict[str, str]]:
        return [
            {"name": "set_svg", "description": "Replace the full SVG markup"},
            {"name": "add_svg_element", "description": "Append an SVG element snippet to the canvas"},
            {"name": "update_svg_element", "description": "Update SVG element attributes by id"},
            {"name": "remove_svg_element", "description": "Remove an SVG element by id"},
            {"name": "get_svg", "description": "Get the current SVG markup"},
            {"name": "list_svg_elements", "description": "List element ids and types"},
            {"name": "get_svg_element", "description": "Get attributes for a single element by id"},
            {"name": "set_canvas_size", "description": "Update canvas width/height"},
            {"name": "set_background", "description": "Set canvas background color"},
            {"name": "clear_canvas", "description": "Clear all elements except background"}
        ]

    async def execute(self, tool_name: str, **kwargs) -> str:
        method = getattr(self, tool_name, None)
        if not method:
            return f"Error: Unknown tool '{tool_name}'"
        try:
            return method(**kwargs)
        except Exception as exc:
            return f"Error executing {tool_name}: {exc}"

    def set_svg(self, svg: str, width: int = None, height: int = None, background: str = None) -> str:
        if not svg:
            return "Error: svg content required"
        root = ET.fromstring(svg)
        if root.tag.endswith("svg"):
            self.root = root
        else:
            wrapper = self._create_root()
            wrapper.append(root)
            self.root = wrapper

        self.root.attrib.setdefault("id", "design-svg")
        self.root.attrib.setdefault("class", "design-svg")

        if width:
            self.width = int(width)
        if height:
            self.height = int(height)

        if background:
            self.background = background
        if not self._find_element_by_id("svg-background"):
            bg = ET.Element(_ns("rect"), {
                "id": "svg-background",
                "x": "0",
                "y": "0",
                "width": str(self.width),
                "height": str(self.height),
                "fill": self.background
            })
            self.root.insert(0, bg)

        if background:
            self.set_background(background)

        self._sync_root_size()
        return "SVG updated"

    def add_svg_element(self, svg: str) -> str:
        if not svg:
            return "Error: svg snippet required"
        fragment = ET.fromstring(f"<wrapper xmlns=\"{SVG_NS}\">{svg}</wrapper>")
        added = 0
        for child in list(fragment):
            if "id" not in child.attrib:
                child.attrib["id"] = _generate_id("el")
            self.root.append(child)
            added += 1
        return f"Added {added} element(s)"

    def update_svg_element(self, element_id: str, attributes: Dict[str, Any]) -> str:
        element = self._find_element_by_id(element_id)
        if not element:
            return f"Error: element '{element_id}' not found"
        for key, value in (attributes or {}).items():
            if value is None:
                continue
            element.attrib[key] = str(value)
        return f"Updated element '{element_id}'"

    def remove_svg_element(self, element_id: str) -> str:
        element = self._find_element_by_id(element_id)
        if not element:
            return f"Error: element '{element_id}' not found"
        parent = self._find_parent(element)
        if not parent:
            return f"Error: element '{element_id}' has no parent"
        parent.remove(element)
        return f"Removed element '{element_id}'"

    def get_svg(self) -> str:
        return self._serialize()

    def list_svg_elements(self) -> str:
        elements = []
        for el in self.root:
            if el.attrib.get("id") == "svg-background":
                continue
            elements.append({
                "id": el.attrib.get("id"),
                "type": el.tag.replace(f"{{{SVG_NS}}}", "")
            })
        return str(elements)

    def get_svg_element(self, element_id: str) -> str:
        element = self._find_element_by_id(element_id)
        if not element:
            return f"Error: element '{element_id}' not found"
        return str(element.attrib)

    def set_canvas_size(self, width: int, height: int) -> str:
        self.width = int(width)
        self.height = int(height)
        self._sync_root_size()
        return f"Canvas size set to {width}x{height}"

    def set_background(self, color: str) -> str:
        self.background = color
        bg = self._find_element_by_id("svg-background")
        if not bg:
            bg = ET.Element(_ns("rect"), {
                "id": "svg-background",
                "x": "0",
                "y": "0",
                "width": str(self.width),
                "height": str(self.height),
                "fill": color
            })
            self.root.insert(0, bg)
        else:
            bg.attrib["fill"] = color
        return f"Background set to {color}"

    def clear_canvas(self) -> str:
        preserved = [el for el in self.root if el.attrib.get("id") == "svg-background"]
        self.root = self._create_root()
        if preserved:
            self.root.remove(self._find_element_by_id("svg-background"))
            self.root.insert(0, preserved[0])
        return "Canvas cleared"

    def _sync_root_size(self):
        self.root.attrib["width"] = str(self.width)
        self.root.attrib["height"] = str(self.height)
        self.root.attrib["viewBox"] = f"0 0 {self.width} {self.height}"
        bg = self._find_element_by_id("svg-background")
        if bg:
            bg.attrib["width"] = str(self.width)
            bg.attrib["height"] = str(self.height)

    def _find_parent(self, element: ET.Element) -> Optional[ET.Element]:
        for parent in self.root.iter():
            for child in list(parent):
                if child is element:
                    return parent
        return None
