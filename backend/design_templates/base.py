"""
Design Template Base Types

Core dataclasses and enums for template definitions.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class TemplateCategory(Enum):
    """Categories for design templates."""
    BUSINESS = "business"
    SOCIAL_MEDIA = "social_media"
    MARKETING = "marketing"
    WEB = "web"
    PRESENTATION = "presentation"
    PRINT = "print"


@dataclass
class ColorPalette:
    """Color palette definition."""
    name: str
    primary: str
    secondary: str
    accent: str
    background: str
    surface: str
    text: str
    text_secondary: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "background": self.background,
            "surface": self.surface,
            "text": self.text,
            "text_secondary": self.text_secondary,
        }


@dataclass
class TemplateElement:
    """Definition of a single template element."""
    element_type: str
    name: str
    x: float
    y: float
    width: float
    height: float
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.element_type,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            **self.properties
        }


@dataclass
class DesignTemplate:
    """Complete design template definition."""
    id: str
    name: str
    description: str
    category: TemplateCategory
    width: int
    height: int
    background: str
    elements: List[TemplateElement]
    palette: Optional[ColorPalette] = None
    tags: List[str] = field(default_factory=list)
    thumbnail: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "width": self.width,
            "height": self.height,
            "background": self.background,
            "elements": [e.to_dict() for e in self.elements],
            "palette": self.palette.to_dict() if self.palette else None,
            "tags": self.tags,
        }
