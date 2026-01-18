"""
Design Template Base Definitions

This module defines the core data structures and shared palettes for
Flashy Design templates. It is intentionally kept small and reusable
across multiple template catalogs.
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
    FESTIVAL = "festival"


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


PALETTES = {
    "corporate_blue": ColorPalette(
        name="Corporate Blue",
        primary="#2563EB",
        secondary="#1E40AF",
        accent="#F59E0B",
        background="#FFFFFF",
        surface="#F8FAFC",
        text="#1E293B",
        text_secondary="#64748B"
    ),
    "modern_dark": ColorPalette(
        name="Modern Dark",
        primary="#3B82F6",
        secondary="#8B5CF6",
        accent="#10B981",
        background="#0F172A",
        surface="#1E293B",
        text="#F8FAFC",
        text_secondary="#94A3B8"
    ),
    "minimal_light": ColorPalette(
        name="Minimal Light",
        primary="#18181B",
        secondary="#52525B",
        accent="#DC2626",
        background="#FAFAFA",
        surface="#FFFFFF",
        text="#18181B",
        text_secondary="#71717A"
    ),
    "nature_green": ColorPalette(
        name="Nature Green",
        primary="#059669",
        secondary="#0891B2",
        accent="#F97316",
        background="#ECFDF5",
        surface="#FFFFFF",
        text="#064E3B",
        text_secondary="#047857"
    ),
    "luxury_gold": ColorPalette(
        name="Luxury Gold",
        primary="#B45309",
        secondary="#78350F",
        accent="#A16207",
        background="#FFFBEB",
        surface="#FEF3C7",
        text="#451A03",
        text_secondary="#78350F"
    ),
    "tech_purple": ColorPalette(
        name="Tech Purple",
        primary="#7C3AED",
        secondary="#4F46E5",
        accent="#06B6D4",
        background="#FAFAF9",
        surface="#FFFFFF",
        text="#1C1917",
        text_secondary="#57534E"
    ),
    "healthcare_blue": ColorPalette(
        name="Healthcare Blue",
        primary="#0EA5E9",
        secondary="#0284C7",
        accent="#22C55E",
        background="#F0F9FF",
        surface="#FFFFFF",
        text="#0C4A6E",
        text_secondary="#0369A1"
    ),
    "creative_pink": ColorPalette(
        name="Creative Pink",
        primary="#EC4899",
        secondary="#DB2777",
        accent="#F59E0B",
        background="#FDF4FF",
        surface="#FFFFFF",
        text="#701A75",
        text_secondary="#A21CAF"
    ),
    "sunset_gradient": ColorPalette(
        name="Sunset Gradient",
        primary="#F97316",
        secondary="#EF4444",
        accent="#FBBF24",
        background="#FFF7ED",
        surface="#FFFFFF",
        text="#7C2D12",
        text_secondary="#C2410C"
    ),
    "ocean_depth": ColorPalette(
        name="Ocean Depth",
        primary="#0891B2",
        secondary="#0E7490",
        accent="#14B8A6",
        background="#ECFEFF",
        surface="#FFFFFF",
        text="#164E63",
        text_secondary="#0E7490"
    ),
    "nepal_festival_red": ColorPalette(
        name="Nepal Festival Red",
        primary="#DC2626",
        secondary="#1D4ED8",
        accent="#F59E0B",
        background="#FFF7ED",
        surface="#FFFFFF",
        text="#1F2937",
        text_secondary="#9CA3AF"
    ),
    "saraswati_serene": ColorPalette(
        name="Saraswati Serene",
        primary="#2563EB",
        secondary="#7C3AED",
        accent="#F59E0B",
        background="#F8FAFC",
        surface="#FFFFFF",
        text="#1E293B",
        text_secondary="#64748B"
    ),
    "tihar_glow": ColorPalette(
        name="Tihar Glow",
        primary="#7C3AED",
        secondary="#EC4899",
        accent="#F59E0B",
        background="#0F172A",
        surface="#1E293B",
        text="#F8FAFC",
        text_secondary="#CBD5F5"
    ),
}
