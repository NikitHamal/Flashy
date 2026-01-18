"""
Compositional Layout Engine

This module provides a sophisticated compositional layout system for creating
professional, well-structured designs. It uses hierarchical zones, visual
hierarchy rules, and golden ratio calculations for optimal element placement.

Key Features:
- Hierarchical composition zones (header, hero, content, footer)
- Visual hierarchy scoring for element prioritization
- Golden ratio and rule-of-thirds positioning
- Smart element stacking and spacing
- Typography hierarchy with precise baselines
- Brand kit integration slots
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Union
from enum import Enum
import math


class ZoneType(Enum):
    """Composition zone types for layout structure."""
    HEADER = "header"
    HERO = "hero"
    CONTENT = "content"
    SIDEBAR = "sidebar"
    FOOTER = "footer"
    FULL_BLEED = "full_bleed"
    OVERLAY = "overlay"
    DECORATIVE = "decorative"


class ElementRole(Enum):
    """Semantic roles for design elements."""
    BACKGROUND = "background"
    DECORATION = "decoration"
    BRAND_LOGO = "brand_logo"
    MAIN_HEADING = "main_heading"
    SUBHEADING = "subheading"
    BODY_TEXT = "body_text"
    CALL_TO_ACTION = "call_to_action"
    IMAGE_HERO = "image_hero"
    IMAGE_SUPPORTING = "image_supporting"
    ICON = "icon"
    DIVIDER = "divider"
    CONTACT_INFO = "contact_info"
    SOCIAL_HANDLE = "social_handle"
    DATE_TIME = "date_time"
    ACCENT_SHAPE = "accent_shape"


class VisualWeight(Enum):
    """Visual weight categories for hierarchy."""
    DOMINANT = 5      # Main focal point
    STRONG = 4        # Secondary focal point
    MODERATE = 3      # Supporting elements
    LIGHT = 2         # Tertiary elements
    SUBTLE = 1        # Background/decorative


@dataclass
class CompositionZone:
    """Represents a composition zone within the canvas."""
    zone_type: ZoneType
    x: float
    y: float
    width: float
    height: float
    padding: float = 0
    alignment: str = "center"  # left, center, right
    vertical_alignment: str = "center"  # top, center, bottom
    layer_order: int = 0
    max_elements: int = 10
    
    @property
    def inner_x(self) -> float:
        return self.x + self.padding
    
    @property
    def inner_y(self) -> float:
        return self.y + self.padding
    
    @property
    def inner_width(self) -> float:
        return self.width - (2 * self.padding)
    
    @property
    def inner_height(self) -> float:
        return self.height - (2 * self.padding)
    
    @property
    def center_x(self) -> float:
        return self.x + self.width / 2
    
    @property
    def center_y(self) -> float:
        return self.y + self.height / 2
    
    def get_aligned_x(self, element_width: float) -> float:
        """Get X position based on zone alignment."""
        if self.alignment == "left":
            return self.inner_x
        elif self.alignment == "right":
            return self.inner_x + self.inner_width - element_width
        else:  # center
            return self.inner_x + (self.inner_width - element_width) / 2
    
    def get_aligned_y(self, element_height: float) -> float:
        """Get Y position based on vertical alignment."""
        if self.vertical_alignment == "top":
            return self.inner_y
        elif self.vertical_alignment == "bottom":
            return self.inner_y + self.inner_height - element_height
        else:  # center
            return self.inner_y + (self.inner_height - element_height) / 2
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_type": self.zone_type.value,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "padding": self.padding,
            "alignment": self.alignment,
            "vertical_alignment": self.vertical_alignment,
            "inner_bounds": {
                "x": self.inner_x,
                "y": self.inner_y,
                "width": self.inner_width,
                "height": self.inner_height
            }
        }


@dataclass
class ElementPlacement:
    """Represents a placed element with its role and position."""
    role: ElementRole
    x: float
    y: float
    width: float
    height: float
    zone: Optional[ZoneType] = None
    layer: int = 0
    visual_weight: VisualWeight = VisualWeight.MODERATE
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role.value,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "zone": self.zone.value if self.zone else None,
            "layer": self.layer,
            "visual_weight": self.visual_weight.value
        }


@dataclass
class TypographySpec:
    """Typography specifications for consistent text hierarchy."""
    role: ElementRole
    font_size: int
    font_weight: str
    line_height: float = 1.4
    letter_spacing: float = 0
    font_family: str = "Poppins"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role.value,
            "fontSize": self.font_size,
            "fontWeight": self.font_weight,
            "lineHeight": self.line_height,
            "letterSpacing": self.letter_spacing,
            "fontFamily": self.font_family
        }


class CompositionEngine:
    """
    Advanced compositional layout engine for professional designs.
    
    Provides hierarchical zone-based layouts with visual hierarchy
    calculations for creating well-structured, professional designs.
    """
    
    # Golden ratio constant
    PHI = 1.618033988749895
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.zones: List[CompositionZone] = []
        self.placements: List[ElementPlacement] = []
        self.typography_specs: Dict[ElementRole, TypographySpec] = {}
        
        # Initialize default typography
        self._init_typography_defaults()
    
    def _init_typography_defaults(self):
        """Initialize default typography specifications based on canvas size."""
        base_size = min(self.width, self.height)
        
        # Scale typography based on canvas size
        if base_size >= 1920:
            scale = 1.0
        elif base_size >= 1080:
            scale = 0.85
        elif base_size >= 800:
            scale = 0.7
        else:
            scale = 0.55
        
        self.typography_specs = {
            ElementRole.MAIN_HEADING: TypographySpec(
                role=ElementRole.MAIN_HEADING,
                font_size=int(72 * scale),
                font_weight="700",
                line_height=1.2,
                font_family="Poppins"
            ),
            ElementRole.SUBHEADING: TypographySpec(
                role=ElementRole.SUBHEADING,
                font_size=int(32 * scale),
                font_weight="500",
                line_height=1.4,
                font_family="Poppins"
            ),
            ElementRole.BODY_TEXT: TypographySpec(
                role=ElementRole.BODY_TEXT,
                font_size=int(18 * scale),
                font_weight="400",
                line_height=1.6,
                font_family="Inter"
            ),
            ElementRole.CALL_TO_ACTION: TypographySpec(
                role=ElementRole.CALL_TO_ACTION,
                font_size=int(20 * scale),
                font_weight="600",
                line_height=1.4,
                letter_spacing=0.5,
                font_family="Inter"
            ),
            ElementRole.CONTACT_INFO: TypographySpec(
                role=ElementRole.CONTACT_INFO,
                font_size=int(14 * scale),
                font_weight="400",
                line_height=1.5,
                font_family="Inter"
            ),
            ElementRole.DATE_TIME: TypographySpec(
                role=ElementRole.DATE_TIME,
                font_size=int(16 * scale),
                font_weight="500",
                line_height=1.4,
                font_family="Inter"
            ),
            ElementRole.SOCIAL_HANDLE: TypographySpec(
                role=ElementRole.SOCIAL_HANDLE,
                font_size=int(14 * scale),
                font_weight="400",
                line_height=1.4,
                font_family="Inter"
            )
        }
    
    def get_typography(self, role: ElementRole) -> TypographySpec:
        """Get typography specification for an element role."""
        return self.typography_specs.get(
            role,
            TypographySpec(role=role, font_size=16, font_weight="400")
        )
    
    # =========================================================================
    # GOLDEN RATIO & RULE OF THIRDS CALCULATIONS
    # =========================================================================
    
    def golden_ratio_split_horizontal(self) -> Tuple[float, float]:
        """Split canvas horizontally using golden ratio."""
        major = self.width / self.PHI
        minor = self.width - major
        return (major, minor)
    
    def golden_ratio_split_vertical(self) -> Tuple[float, float]:
        """Split canvas vertically using golden ratio."""
        major = self.height / self.PHI
        minor = self.height - major
        return (major, minor)
    
    def get_golden_points(self) -> List[Tuple[float, float]]:
        """Get golden ratio intersection points."""
        h_major, h_minor = self.golden_ratio_split_horizontal()
        v_major, v_minor = self.golden_ratio_split_vertical()
        
        return [
            (h_minor, v_minor),  # Top-left golden point
            (h_major, v_minor),  # Top-right golden point
            (h_minor, v_major),  # Bottom-left golden point
            (h_major, v_major),  # Bottom-right golden point
        ]
    
    def get_rule_of_thirds_points(self) -> List[Tuple[float, float]]:
        """Get rule of thirds intersection points."""
        third_x = self.width / 3
        third_y = self.height / 3
        
        return [
            (third_x, third_y),          # Top-left
            (2 * third_x, third_y),      # Top-right
            (third_x, 2 * third_y),      # Bottom-left
            (2 * third_x, 2 * third_y),  # Bottom-right
        ]
    
    def get_rule_of_thirds_lines(self) -> Dict[str, List[float]]:
        """Get rule of thirds grid lines."""
        third_x = self.width / 3
        third_y = self.height / 3
        
        return {
            "vertical": [third_x, 2 * third_x],
            "horizontal": [third_y, 2 * third_y]
        }
    
    # =========================================================================
    # COMPOSITION LAYOUTS
    # =========================================================================
    
    def create_banner_composition(self, style: str = "centered") -> List[CompositionZone]:
        """
        Create a banner composition layout.
        
        Styles:
        - centered: Central focus with symmetrical layout
        - left_heavy: Content weighted to left
        - right_heavy: Content weighted to right
        - split: 50-50 split layout
        """
        self.zones = []
        
        edge_margin = self.width * 0.05
        
        if style == "centered":
            # Background zone (full canvas)
            self.zones.append(CompositionZone(
                zone_type=ZoneType.FULL_BLEED,
                x=0, y=0,
                width=self.width, height=self.height,
                layer_order=0
            ))
            
            # Brand zone (top-left corner)
            brand_height = self.height * 0.15
            self.zones.append(CompositionZone(
                zone_type=ZoneType.HEADER,
                x=edge_margin, y=edge_margin,
                width=self.width * 0.3, height=brand_height,
                padding=10,
                alignment="left",
                vertical_alignment="center",
                layer_order=10
            ))
            
            # Hero zone (central content)
            hero_y = self.height * 0.25
            hero_height = self.height * 0.5
            self.zones.append(CompositionZone(
                zone_type=ZoneType.HERO,
                x=edge_margin, y=hero_y,
                width=self.width - (2 * edge_margin),
                height=hero_height,
                padding=20,
                alignment="center",
                vertical_alignment="center",
                layer_order=20
            ))
            
            # Footer zone (bottom)
            footer_height = self.height * 0.15
            self.zones.append(CompositionZone(
                zone_type=ZoneType.FOOTER,
                x=edge_margin,
                y=self.height - footer_height - edge_margin,
                width=self.width - (2 * edge_margin),
                height=footer_height,
                padding=10,
                alignment="center",
                layer_order=10
            ))
            
            # Decorative zones (corners)
            deco_size = min(self.width, self.height) * 0.2
            self.zones.append(CompositionZone(
                zone_type=ZoneType.DECORATIVE,
                x=0, y=0,
                width=deco_size, height=deco_size,
                layer_order=5
            ))
            self.zones.append(CompositionZone(
                zone_type=ZoneType.DECORATIVE,
                x=self.width - deco_size, y=self.height - deco_size,
                width=deco_size, height=deco_size,
                layer_order=5
            ))
        
        elif style == "split":
            # Left half
            half_width = self.width / 2
            self.zones.append(CompositionZone(
                zone_type=ZoneType.CONTENT,
                x=0, y=0,
                width=half_width, height=self.height,
                padding=edge_margin,
                alignment="center",
                layer_order=10
            ))
            
            # Right half
            self.zones.append(CompositionZone(
                zone_type=ZoneType.HERO,
                x=half_width, y=0,
                width=half_width, height=self.height,
                padding=edge_margin,
                alignment="center",
                layer_order=10
            ))
        
        elif style == "left_heavy":
            # Using golden ratio
            major, minor = self.golden_ratio_split_horizontal()
            
            # Left content (major portion)
            self.zones.append(CompositionZone(
                zone_type=ZoneType.HERO,
                x=0, y=0,
                width=major, height=self.height,
                padding=edge_margin,
                alignment="left",
                layer_order=10
            ))
            
            # Right sidebar (minor portion)
            self.zones.append(CompositionZone(
                zone_type=ZoneType.SIDEBAR,
                x=major, y=0,
                width=minor, height=self.height,
                padding=edge_margin * 0.5,
                alignment="center",
                layer_order=10
            ))
        
        elif style == "right_heavy":
            # Using golden ratio
            major, minor = self.golden_ratio_split_horizontal()
            
            # Left sidebar (minor portion)
            self.zones.append(CompositionZone(
                zone_type=ZoneType.SIDEBAR,
                x=0, y=0,
                width=minor, height=self.height,
                padding=edge_margin * 0.5,
                alignment="center",
                layer_order=10
            ))
            
            # Right content (major portion)
            self.zones.append(CompositionZone(
                zone_type=ZoneType.HERO,
                x=minor, y=0,
                width=major, height=self.height,
                padding=edge_margin,
                alignment="right",
                layer_order=10
            ))
        
        return self.zones
    
    def create_social_post_composition(self, aspect: str = "square") -> List[CompositionZone]:
        """
        Create social media post composition.
        
        Aspects:
        - square: 1:1 (Instagram post)
        - portrait: 4:5 (Instagram portrait)
        - story: 9:16 (Stories/Reels)
        """
        self.zones = []
        
        margin = min(self.width, self.height) * 0.08
        
        # Full bleed background
        self.zones.append(CompositionZone(
            zone_type=ZoneType.FULL_BLEED,
            x=0, y=0,
            width=self.width, height=self.height,
            layer_order=0
        ))
        
        if aspect == "square":
            # Header with logo
            header_height = self.height * 0.12
            self.zones.append(CompositionZone(
                zone_type=ZoneType.HEADER,
                x=margin, y=margin,
                width=self.width - (2 * margin),
                height=header_height,
                padding=0,
                alignment="left",
                layer_order=10
            ))
            
            # Main hero content
            hero_y = margin + header_height + (margin * 0.5)
            hero_height = self.height * 0.55
            self.zones.append(CompositionZone(
                zone_type=ZoneType.HERO,
                x=margin, y=hero_y,
                width=self.width - (2 * margin),
                height=hero_height,
                padding=margin * 0.5,
                alignment="center",
                vertical_alignment="center",
                layer_order=20
            ))
            
            # Footer/CTA area
            footer_height = self.height * 0.15
            self.zones.append(CompositionZone(
                zone_type=ZoneType.FOOTER,
                x=margin,
                y=self.height - margin - footer_height,
                width=self.width - (2 * margin),
                height=footer_height,
                padding=0,
                alignment="center",
                layer_order=10
            ))
        
        elif aspect == "story":
            # Vertical story layout
            # Top brand area
            header_height = self.height * 0.1
            self.zones.append(CompositionZone(
                zone_type=ZoneType.HEADER,
                x=margin, y=margin * 2,
                width=self.width - (2 * margin),
                height=header_height,
                alignment="center",
                layer_order=10
            ))
            
            # Main hero (middle)
            hero_y = self.height * 0.25
            hero_height = self.height * 0.45
            self.zones.append(CompositionZone(
                zone_type=ZoneType.HERO,
                x=margin, y=hero_y,
                width=self.width - (2 * margin),
                height=hero_height,
                padding=margin * 0.5,
                alignment="center",
                vertical_alignment="center",
                layer_order=20
            ))
            
            # Bottom content
            footer_height = self.height * 0.18
            self.zones.append(CompositionZone(
                zone_type=ZoneType.FOOTER,
                x=margin,
                y=self.height - margin * 3 - footer_height,
                width=self.width - (2 * margin),
                height=footer_height,
                alignment="center",
                layer_order=10
            ))
        
        return self.zones
    
    def create_festival_greeting_composition(self) -> List[CompositionZone]:
        """
        Create a festival greeting card composition.
        Optimized for festival wishes like Saraswoti Puja, Dashain, Tihar.
        """
        self.zones = []
        
        margin = min(self.width, self.height) * 0.06
        
        # Full bleed background
        self.zones.append(CompositionZone(
            zone_type=ZoneType.FULL_BLEED,
            x=0, y=0,
            width=self.width, height=self.height,
            layer_order=0
        ))
        
        # Decorative top corners
        corner_size = min(self.width, self.height) * 0.25
        self.zones.append(CompositionZone(
            zone_type=ZoneType.DECORATIVE,
            x=0, y=0,
            width=corner_size, height=corner_size,
            layer_order=5
        ))
        self.zones.append(CompositionZone(
            zone_type=ZoneType.DECORATIVE,
            x=self.width - corner_size, y=0,
            width=corner_size, height=corner_size,
            layer_order=5
        ))
        
        # Brand logo area (top center)
        logo_height = self.height * 0.12
        self.zones.append(CompositionZone(
            zone_type=ZoneType.HEADER,
            x=(self.width - self.width * 0.4) / 2,
            y=margin * 1.5,
            width=self.width * 0.4,
            height=logo_height,
            padding=0,
            alignment="center",
            layer_order=25
        ))
        
        # Festival imagery/symbol zone (upper middle)
        symbol_y = self.height * 0.18
        symbol_height = self.height * 0.32
        self.zones.append(CompositionZone(
            zone_type=ZoneType.OVERLAY,
            x=margin, y=symbol_y,
            width=self.width - (2 * margin),
            height=symbol_height,
            padding=margin * 0.5,
            alignment="center",
            layer_order=15
        ))
        
        # Main greeting text zone
        greeting_y = self.height * 0.52
        greeting_height = self.height * 0.22
        self.zones.append(CompositionZone(
            zone_type=ZoneType.HERO,
            x=margin, y=greeting_y,
            width=self.width - (2 * margin),
            height=greeting_height,
            padding=margin * 0.5,
            alignment="center",
            vertical_alignment="center",
            layer_order=20
        ))
        
        # Subtext/wishes zone
        wishes_y = self.height * 0.74
        wishes_height = self.height * 0.1
        self.zones.append(CompositionZone(
            zone_type=ZoneType.CONTENT,
            x=margin * 2, y=wishes_y,
            width=self.width - (4 * margin),
            height=wishes_height,
            alignment="center",
            layer_order=18
        ))
        
        # Footer with brand name
        footer_height = self.height * 0.08
        self.zones.append(CompositionZone(
            zone_type=ZoneType.FOOTER,
            x=margin,
            y=self.height - margin * 1.5 - footer_height,
            width=self.width - (2 * margin),
            height=footer_height,
            alignment="center",
            layer_order=10
        ))
        
        # Decorative bottom corners
        self.zones.append(CompositionZone(
            zone_type=ZoneType.DECORATIVE,
            x=0, y=self.height - corner_size,
            width=corner_size, height=corner_size,
            layer_order=5
        ))
        self.zones.append(CompositionZone(
            zone_type=ZoneType.DECORATIVE,
            x=self.width - corner_size,
            y=self.height - corner_size,
            width=corner_size, height=corner_size,
            layer_order=5
        ))
        
        return self.zones
    
    # =========================================================================
    # ELEMENT PLACEMENT HELPERS
    # =========================================================================
    
    def get_zone(self, zone_type: ZoneType) -> Optional[CompositionZone]:
        """Get the first zone of a given type."""
        for zone in self.zones:
            if zone.zone_type == zone_type:
                return zone
        return None
    
    def get_zones(self, zone_type: ZoneType) -> List[CompositionZone]:
        """Get all zones of a given type."""
        return [z for z in self.zones if z.zone_type == zone_type]
    
    def place_in_zone(
        self,
        zone_type: ZoneType,
        element_width: float,
        element_height: float,
        role: ElementRole = ElementRole.BODY_TEXT,
        offset_x: float = 0,
        offset_y: float = 0
    ) -> Optional[ElementPlacement]:
        """Place an element within a specific zone."""
        zone = self.get_zone(zone_type)
        if not zone:
            return None
        
        x = zone.get_aligned_x(element_width) + offset_x
        y = zone.get_aligned_y(element_height) + offset_y
        
        placement = ElementPlacement(
            role=role,
            x=x, y=y,
            width=element_width,
            height=element_height,
            zone=zone_type,
            layer=zone.layer_order
        )
        
        self.placements.append(placement)
        return placement
    
    def place_centered(
        self,
        element_width: float,
        element_height: float,
        role: ElementRole = ElementRole.BODY_TEXT
    ) -> ElementPlacement:
        """Place an element at the canvas center."""
        x = (self.width - element_width) / 2
        y = (self.height - element_height) / 2
        
        placement = ElementPlacement(
            role=role,
            x=x, y=y,
            width=element_width,
            height=element_height,
            layer=10
        )
        
        self.placements.append(placement)
        return placement
    
    def place_at_golden_point(
        self,
        element_width: float,
        element_height: float,
        point_index: int = 0,
        role: ElementRole = ElementRole.BODY_TEXT
    ) -> ElementPlacement:
        """Place an element at a golden ratio intersection point."""
        points = self.get_golden_points()
        point = points[point_index % len(points)]
        
        x = point[0] - element_width / 2
        y = point[1] - element_height / 2
        
        placement = ElementPlacement(
            role=role,
            x=x, y=y,
            width=element_width,
            height=element_height,
            visual_weight=VisualWeight.STRONG,
            layer=15
        )
        
        self.placements.append(placement)
        return placement
    
    def calculate_text_bounds(
        self,
        text: str,
        role: ElementRole,
        max_width: Optional[float] = None
    ) -> Tuple[float, float]:
        """Calculate approximate bounds for text."""
        spec = self.get_typography(role)
        
        # Approximate character width as 0.55x font size
        char_width = spec.font_size * 0.55
        
        # Calculate single line width
        line_width = len(text) * char_width
        
        # If max_width specified and text exceeds, calculate wrapped height
        if max_width and line_width > max_width:
            lines = math.ceil(line_width / max_width)
            width = max_width
            height = lines * spec.font_size * spec.line_height
        else:
            width = line_width
            height = spec.font_size * spec.line_height
        
        return (width, height)
    
    # =========================================================================
    # LAYOUT GENERATION HELPERS
    # =========================================================================
    
    def get_vertical_stack_positions(
        self,
        items: List[Tuple[float, float]],  # List of (width, height)
        start_y: float,
        spacing: float = 20,
        alignment: str = "center"
    ) -> List[Tuple[float, float]]:
        """Calculate positions for vertically stacked elements."""
        positions = []
        current_y = start_y
        
        for width, height in items:
            if alignment == "center":
                x = (self.width - width) / 2
            elif alignment == "left":
                x = self.width * 0.08
            else:  # right
                x = self.width - width - (self.width * 0.08)
            
            positions.append((x, current_y))
            current_y += height + spacing
        
        return positions
    
    def get_horizontal_stack_positions(
        self,
        items: List[Tuple[float, float]],  # List of (width, height)
        start_x: float,
        y: float,
        spacing: float = 20
    ) -> List[Tuple[float, float]]:
        """Calculate positions for horizontally stacked elements."""
        positions = []
        current_x = start_x
        
        for width, height in items:
            positions.append((current_x, y))
            current_x += width + spacing
        
        return positions
    
    def get_centered_horizontal_positions(
        self,
        items: List[Tuple[float, float]],
        y: float,
        spacing: float = 20
    ) -> List[Tuple[float, float]]:
        """Get positions for horizontally centered items."""
        total_width = sum(w for w, h in items) + spacing * (len(items) - 1)
        start_x = (self.width - total_width) / 2
        return self.get_horizontal_stack_positions(items, start_x, y, spacing)
    
    def get_composition_context(self) -> Dict[str, Any]:
        """Get full composition context for AI."""
        return {
            "canvas": {
                "width": self.width,
                "height": self.height,
                "center": (self.width / 2, self.height / 2),
                "aspect_ratio": round(self.width / self.height, 3)
            },
            "golden_ratio": {
                "horizontal_split": self.golden_ratio_split_horizontal(),
                "vertical_split": self.golden_ratio_split_vertical(),
                "points": self.get_golden_points()
            },
            "thirds": {
                "points": self.get_rule_of_thirds_points(),
                "lines": self.get_rule_of_thirds_lines()
            },
            "zones": [z.to_dict() for z in self.zones],
            "typography": {
                role.value: spec.to_dict() 
                for role, spec in self.typography_specs.items()
            },
            "margins": {
                "edge": self.width * 0.05,
                "section": self.height * 0.05,
                "element": min(self.width, self.height) * 0.02
            }
        }


# =============================================================================
# PRESET COMPOSITIONS
# =============================================================================

def create_instagram_square_composition(width: int = 1080, height: int = 1080) -> CompositionEngine:
    """Create optimized composition for Instagram square posts."""
    engine = CompositionEngine(width, height)
    engine.create_social_post_composition("square")
    return engine


def create_instagram_story_composition(width: int = 1080, height: int = 1920) -> CompositionEngine:
    """Create optimized composition for Instagram stories."""
    engine = CompositionEngine(width, height)
    engine.create_social_post_composition("story")
    return engine


def create_facebook_post_composition(width: int = 1200, height: int = 630) -> CompositionEngine:
    """Create optimized composition for Facebook posts."""
    engine = CompositionEngine(width, height)
    engine.create_banner_composition("centered")
    return engine


def create_festival_greeting_composition(width: int = 1080, height: int = 1080) -> CompositionEngine:
    """Create optimized composition for festival greetings."""
    engine = CompositionEngine(width, height)
    engine.create_festival_greeting_composition()
    return engine


def get_composition_for_preset(preset_name: str, width: int, height: int) -> CompositionEngine:
    """Get appropriate composition engine for a canvas preset."""
    engine = CompositionEngine(width, height)
    
    # Determine best composition based on aspect ratio and preset type
    aspect_ratio = width / height
    
    if "story" in preset_name.lower() or aspect_ratio < 0.6:
        engine.create_social_post_composition("story")
    elif "post" in preset_name.lower() and 0.9 <= aspect_ratio <= 1.1:
        engine.create_social_post_composition("square")
    elif "banner" in preset_name.lower() or "cover" in preset_name.lower():
        engine.create_banner_composition("centered")
    elif "greeting" in preset_name.lower() or "festival" in preset_name.lower():
        engine.create_festival_greeting_composition()
    else:
        engine.create_banner_composition("centered")
    
    return engine
