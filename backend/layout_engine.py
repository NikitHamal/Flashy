"""
Smart Layout Engine

This module provides intelligent layout calculations, alignment helpers,
and positioning utilities for the Flashy Design Agent. It enables precise
element placement with professional design patterns.

Features:
- Smart positioning calculations
- Layout presets (header, hero, grid, footer)
- Alignment and distribution helpers
- Spacing and margin utilities
- Responsive layout calculations
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum
import math


class Alignment(Enum):
    """Alignment options for layout calculations."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


class LayoutRegion(Enum):
    """Predefined layout regions on the canvas."""
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    MIDDLE_LEFT = "middle_left"
    CENTER = "center"
    MIDDLE_RIGHT = "middle_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"


@dataclass
class BoundingBox:
    """Represents a rectangular bounding box."""
    x: float
    y: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2

    @property
    def center_y(self) -> float:
        return self.y + self.height / 2

    def contains(self, x: float, y: float) -> bool:
        return self.x <= x <= self.right and self.y <= y <= self.bottom

    def intersects(self, other: 'BoundingBox') -> bool:
        return not (self.right < other.x or other.right < self.x or
                    self.bottom < other.y or other.bottom < self.y)


@dataclass
class LayoutConfig:
    """Configuration for layout calculations."""
    canvas_width: int = 1200
    canvas_height: int = 800
    margin_small: int = 16
    margin_medium: int = 32
    margin_large: int = 48
    edge_margin: int = 40
    section_gap: int = 64
    element_gap: int = 24
    grid_columns: int = 12
    grid_gutter: int = 24


class LayoutEngine:
    """
    Smart layout engine for precise element positioning.
    Provides helper methods for common design patterns.
    """

    def __init__(self, config: Optional[LayoutConfig] = None):
        self.config = config or LayoutConfig()

    def set_canvas_size(self, width: int, height: int):
        """Update canvas dimensions."""
        self.config.canvas_width = width
        self.config.canvas_height = height

    # =========================================================================
    # POSITION CALCULATIONS
    # =========================================================================

    def center_horizontally(self, element_width: float) -> float:
        """Calculate X position to center element horizontally."""
        return (self.config.canvas_width - element_width) / 2

    def center_vertically(self, element_height: float) -> float:
        """Calculate Y position to center element vertically."""
        return (self.config.canvas_height - element_height) / 2

    def center_element(self, width: float, height: float) -> Tuple[float, float]:
        """Calculate position to center element on canvas."""
        return (
            self.center_horizontally(width),
            self.center_vertically(height)
        )

    def align_right(self, element_width: float, margin: Optional[float] = None) -> float:
        """Calculate X position for right alignment."""
        m = margin if margin is not None else self.config.edge_margin
        return self.config.canvas_width - element_width - m

    def align_bottom(self, element_height: float, margin: Optional[float] = None) -> float:
        """Calculate Y position for bottom alignment."""
        m = margin if margin is not None else self.config.edge_margin
        return self.config.canvas_height - element_height - m

    def get_region_center(self, region: LayoutRegion) -> Tuple[float, float]:
        """Get the center point of a layout region."""
        w = self.config.canvas_width
        h = self.config.canvas_height
        x_third = w / 3
        y_third = h / 3

        region_centers = {
            LayoutRegion.TOP_LEFT: (x_third / 2, y_third / 2),
            LayoutRegion.TOP_CENTER: (w / 2, y_third / 2),
            LayoutRegion.TOP_RIGHT: (w - x_third / 2, y_third / 2),
            LayoutRegion.MIDDLE_LEFT: (x_third / 2, h / 2),
            LayoutRegion.CENTER: (w / 2, h / 2),
            LayoutRegion.MIDDLE_RIGHT: (w - x_third / 2, h / 2),
            LayoutRegion.BOTTOM_LEFT: (x_third / 2, h - y_third / 2),
            LayoutRegion.BOTTOM_CENTER: (w / 2, h - y_third / 2),
            LayoutRegion.BOTTOM_RIGHT: (w - x_third / 2, h - y_third / 2),
        }
        return region_centers.get(region, (w / 2, h / 2))

    def position_in_region(
        self, region: LayoutRegion, element_width: float, element_height: float
    ) -> Tuple[float, float]:
        """Calculate position to place element centered in a region."""
        cx, cy = self.get_region_center(region)
        return (cx - element_width / 2, cy - element_height / 2)

    def get_region_bounds(self, region: LayoutRegion) -> BoundingBox:
        """Get the bounding box of a layout region."""
        w = self.config.canvas_width
        h = self.config.canvas_height
        x_third = w / 3
        y_third = h / 3

        col = 0
        row = 0
        if region in (LayoutRegion.TOP_CENTER, LayoutRegion.CENTER, LayoutRegion.BOTTOM_CENTER):
            col = 1
        elif region in (LayoutRegion.TOP_RIGHT, LayoutRegion.MIDDLE_RIGHT, LayoutRegion.BOTTOM_RIGHT):
            col = 2

        if region in (LayoutRegion.MIDDLE_LEFT, LayoutRegion.CENTER, LayoutRegion.MIDDLE_RIGHT):
            row = 1
        elif region in (LayoutRegion.BOTTOM_LEFT, LayoutRegion.BOTTOM_CENTER, LayoutRegion.BOTTOM_RIGHT):
            row = 2

        return BoundingBox(
            x=col * x_third,
            y=row * y_third,
            width=x_third,
            height=y_third
        )

    # =========================================================================
    # GRID SYSTEM
    # =========================================================================

    def get_column_width(self, span: int = 1) -> float:
        """Calculate width of column(s) in the grid system."""
        total_gutter = (self.config.grid_columns - 1) * self.config.grid_gutter
        available_width = self.config.canvas_width - (2 * self.config.edge_margin) - total_gutter
        single_col = available_width / self.config.grid_columns
        return single_col * span + self.config.grid_gutter * (span - 1)

    def get_column_x(self, column: int) -> float:
        """Get X position for a specific column (0-indexed)."""
        single_col = self.get_column_width(1)
        return self.config.edge_margin + column * (single_col + self.config.grid_gutter)

    def get_grid_position(self, column: int, row: int, row_height: float) -> Tuple[float, float]:
        """Get position for a grid cell."""
        x = self.get_column_x(column)
        y = self.config.edge_margin + row * (row_height + self.config.element_gap)
        return (x, y)

    # =========================================================================
    # LAYOUT SECTIONS
    # =========================================================================

    def get_header_bounds(self, height: Optional[float] = None) -> BoundingBox:
        """Get bounds for header section (top 10-15%)."""
        h = height if height else self.config.canvas_height * 0.12
        return BoundingBox(
            x=self.config.edge_margin,
            y=self.config.edge_margin,
            width=self.config.canvas_width - (2 * self.config.edge_margin),
            height=h
        )

    def get_hero_bounds(self, header_height: float = 0) -> BoundingBox:
        """Get bounds for hero section (top 40-50% after header)."""
        start_y = self.config.edge_margin + header_height + self.config.section_gap
        hero_height = self.config.canvas_height * 0.4
        return BoundingBox(
            x=self.config.edge_margin,
            y=start_y,
            width=self.config.canvas_width - (2 * self.config.edge_margin),
            height=hero_height
        )

    def get_content_bounds(self, hero_bottom: float = 0) -> BoundingBox:
        """Get bounds for main content section."""
        start_y = hero_bottom + self.config.section_gap if hero_bottom else self.config.canvas_height * 0.35
        footer_height = self.config.canvas_height * 0.12
        return BoundingBox(
            x=self.config.edge_margin,
            y=start_y,
            width=self.config.canvas_width - (2 * self.config.edge_margin),
            height=self.config.canvas_height - start_y - footer_height - self.config.section_gap
        )

    def get_footer_bounds(self, height: Optional[float] = None) -> BoundingBox:
        """Get bounds for footer section (bottom 10-12%)."""
        h = height if height else self.config.canvas_height * 0.1
        return BoundingBox(
            x=self.config.edge_margin,
            y=self.config.canvas_height - self.config.edge_margin - h,
            width=self.config.canvas_width - (2 * self.config.edge_margin),
            height=h
        )

    # =========================================================================
    # ELEMENT DISTRIBUTION
    # =========================================================================

    def distribute_horizontally(
        self,
        count: int,
        element_width: float,
        start_x: Optional[float] = None,
        end_x: Optional[float] = None
    ) -> List[float]:
        """Calculate X positions to distribute elements horizontally."""
        sx = start_x if start_x is not None else self.config.edge_margin
        ex = end_x if end_x is not None else self.config.canvas_width - self.config.edge_margin

        if count <= 1:
            return [sx + (ex - sx - element_width) / 2]

        available = ex - sx - (count * element_width)
        spacing = available / (count - 1) if count > 1 else 0

        positions = []
        current_x = sx
        for _ in range(count):
            positions.append(current_x)
            current_x += element_width + spacing

        return positions

    def distribute_vertically(
        self,
        count: int,
        element_height: float,
        start_y: Optional[float] = None,
        end_y: Optional[float] = None
    ) -> List[float]:
        """Calculate Y positions to distribute elements vertically."""
        sy = start_y if start_y is not None else self.config.edge_margin
        ey = end_y if end_y is not None else self.config.canvas_height - self.config.edge_margin

        if count <= 1:
            return [sy + (ey - sy - element_height) / 2]

        available = ey - sy - (count * element_height)
        spacing = available / (count - 1) if count > 1 else 0

        positions = []
        current_y = sy
        for _ in range(count):
            positions.append(current_y)
            current_y += element_height + spacing

        return positions

    def create_grid_layout(
        self,
        items: int,
        columns: int,
        cell_width: float,
        cell_height: float,
        gap_x: Optional[float] = None,
        gap_y: Optional[float] = None,
        start_x: Optional[float] = None,
        start_y: Optional[float] = None
    ) -> List[Tuple[float, float]]:
        """Create positions for a grid of items."""
        gx = gap_x if gap_x is not None else self.config.element_gap
        gy = gap_y if gap_y is not None else self.config.element_gap
        sx = start_x if start_x is not None else self.center_horizontally(
            columns * cell_width + (columns - 1) * gx
        )
        sy = start_y if start_y is not None else self.config.edge_margin

        positions = []
        for i in range(items):
            col = i % columns
            row = i // columns
            x = sx + col * (cell_width + gx)
            y = sy + row * (cell_height + gy)
            positions.append((x, y))

        return positions

    # =========================================================================
    # TYPOGRAPHY POSITIONING
    # =========================================================================

    def position_heading(
        self,
        text_width: float,
        font_size: float,
        alignment: Alignment = Alignment.CENTER,
        y_offset: Optional[float] = None
    ) -> Tuple[float, float]:
        """Calculate position for a heading."""
        if alignment == Alignment.LEFT:
            x = self.config.edge_margin
        elif alignment == Alignment.RIGHT:
            x = self.align_right(text_width)
        else:
            x = self.center_horizontally(text_width)

        y = y_offset if y_offset is not None else self.config.edge_margin + font_size

        return (x, y)

    def position_subheading(
        self,
        text_width: float,
        heading_bottom: float,
        alignment: Alignment = Alignment.CENTER
    ) -> Tuple[float, float]:
        """Position subheading below main heading."""
        if alignment == Alignment.LEFT:
            x = self.config.edge_margin
        elif alignment == Alignment.RIGHT:
            x = self.align_right(text_width)
        else:
            x = self.center_horizontally(text_width)

        y = heading_bottom + self.config.margin_medium

        return (x, y)

    def get_text_baseline_offset(self, font_size: float) -> float:
        """Get the baseline offset for positioning text."""
        return font_size * 0.8

    # =========================================================================
    # BUSINESS CARD LAYOUT
    # =========================================================================

    def get_business_card_layout(self) -> Dict[str, BoundingBox]:
        """Get predefined positions for business card elements."""
        w = self.config.canvas_width
        h = self.config.canvas_height

        return {
            "logo": BoundingBox(x=60, y=60, width=80, height=80),
            "name": BoundingBox(x=60, y=180, width=w - 120, height=48),
            "title": BoundingBox(x=60, y=240, width=w - 120, height=24),
            "divider": BoundingBox(x=60, y=290, width=100, height=2),
            "email": BoundingBox(x=60, y=340, width=w - 120, height=20),
            "phone": BoundingBox(x=60, y=370, width=w - 120, height=20),
            "website": BoundingBox(x=60, y=400, width=w - 120, height=20),
            "address": BoundingBox(x=60, y=440, width=w - 120, height=40),
        }

    # =========================================================================
    # SOCIAL MEDIA LAYOUTS
    # =========================================================================

    def get_social_banner_layout(self) -> Dict[str, BoundingBox]:
        """Get predefined positions for social media banner elements."""
        w = self.config.canvas_width
        h = self.config.canvas_height

        return {
            "background": BoundingBox(x=0, y=0, width=w, height=h),
            "headline": BoundingBox(
                x=w * 0.1, y=h * 0.3,
                width=w * 0.8, height=h * 0.2
            ),
            "subheadline": BoundingBox(
                x=w * 0.15, y=h * 0.52,
                width=w * 0.7, height=h * 0.1
            ),
            "cta_button": BoundingBox(
                x=(w - 200) / 2, y=h * 0.7,
                width=200, height=50
            ),
            "logo": BoundingBox(x=40, y=40, width=100, height=40),
            "accent_left": BoundingBox(x=0, y=0, width=w * 0.1, height=h),
            "accent_right": BoundingBox(x=w * 0.9, y=0, width=w * 0.1, height=h),
        }

    # =========================================================================
    # PRESENTATION SLIDE LAYOUT
    # =========================================================================

    def get_slide_layout(self, layout_type: str = "title") -> Dict[str, BoundingBox]:
        """Get predefined positions for presentation slide elements."""
        w = self.config.canvas_width
        h = self.config.canvas_height

        layouts = {
            "title": {
                "title": BoundingBox(x=w * 0.1, y=h * 0.35, width=w * 0.8, height=h * 0.15),
                "subtitle": BoundingBox(x=w * 0.2, y=h * 0.55, width=w * 0.6, height=h * 0.08),
                "footer": BoundingBox(x=w * 0.1, y=h - 60, width=w * 0.8, height=30),
            },
            "content": {
                "title": BoundingBox(x=80, y=60, width=w - 160, height=80),
                "content": BoundingBox(x=80, y=160, width=w - 160, height=h - 240),
                "footer": BoundingBox(x=80, y=h - 60, width=w - 160, height=30),
            },
            "two_column": {
                "title": BoundingBox(x=80, y=60, width=w - 160, height=80),
                "left_column": BoundingBox(x=80, y=160, width=(w - 200) / 2, height=h - 240),
                "right_column": BoundingBox(
                    x=80 + (w - 200) / 2 + 40, y=160,
                    width=(w - 200) / 2, height=h - 240
                ),
                "footer": BoundingBox(x=80, y=h - 60, width=w - 160, height=30),
            },
            "image_left": {
                "title": BoundingBox(x=80, y=60, width=w - 160, height=80),
                "image": BoundingBox(x=80, y=160, width=(w - 200) * 0.45, height=h - 240),
                "content": BoundingBox(
                    x=80 + (w - 200) * 0.5, y=160,
                    width=(w - 200) * 0.5, height=h - 240
                ),
                "footer": BoundingBox(x=80, y=h - 60, width=w - 160, height=30),
            },
        }
        return layouts.get(layout_type, layouts["content"])

    # =========================================================================
    # COLLISION DETECTION & SMART PLACEMENT
    # =========================================================================

    def find_non_overlapping_position(
        self,
        element_width: float,
        element_height: float,
        existing_boxes: List[BoundingBox],
        preferred_region: Optional[LayoutRegion] = None
    ) -> Tuple[float, float]:
        """Find a position that doesn't overlap with existing elements."""
        margin = self.config.element_gap

        if preferred_region:
            region_bounds = self.get_region_bounds(preferred_region)
            start_x, start_y = region_bounds.x + margin, region_bounds.y + margin
            end_x = region_bounds.right - element_width - margin
            end_y = region_bounds.bottom - element_height - margin
        else:
            start_x, start_y = self.config.edge_margin, self.config.edge_margin
            end_x = self.config.canvas_width - element_width - self.config.edge_margin
            end_y = self.config.canvas_height - element_height - self.config.edge_margin

        step = 20
        for y in range(int(start_y), int(end_y), step):
            for x in range(int(start_x), int(end_x), step):
                candidate = BoundingBox(x=x, y=y, width=element_width, height=element_height)
                overlaps = any(
                    self._boxes_overlap_with_margin(candidate, box, margin)
                    for box in existing_boxes
                )
                if not overlaps:
                    return (float(x), float(y))

        # Fallback to center if no position found
        return self.center_element(element_width, element_height)

    def _boxes_overlap_with_margin(
        self, box1: BoundingBox, box2: BoundingBox, margin: float
    ) -> bool:
        """Check if two boxes overlap with margin."""
        expanded_box2 = BoundingBox(
            x=box2.x - margin,
            y=box2.y - margin,
            width=box2.width + 2 * margin,
            height=box2.height + 2 * margin
        )
        return box1.intersects(expanded_box2)

    # =========================================================================
    # SNAP-TO-GRID
    # =========================================================================

    def snap_to_grid(
        self, x: float, y: float, grid_size: int = 8
    ) -> Tuple[float, float]:
        """Snap coordinates to nearest grid point."""
        return (
            round(x / grid_size) * grid_size,
            round(y / grid_size) * grid_size
        )

    def snap_dimensions(
        self, width: float, height: float, grid_size: int = 8
    ) -> Tuple[float, float]:
        """Snap dimensions to nearest grid values."""
        return (
            round(width / grid_size) * grid_size,
            round(height / grid_size) * grid_size
        )

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def estimate_text_width(self, text: str, font_size: float) -> float:
        """Estimate text width based on character count and font size."""
        avg_char_width = font_size * 0.6
        return len(text) * avg_char_width

    def estimate_text_height(self, font_size: float, line_count: int = 1) -> float:
        """Estimate text height based on font size and lines."""
        line_height = font_size * 1.4
        return line_height * line_count

    def calculate_aspect_ratio_height(
        self, width: float, aspect_ratio: float = 16 / 9
    ) -> float:
        """Calculate height to maintain aspect ratio."""
        return width / aspect_ratio

    def calculate_aspect_ratio_width(
        self, height: float, aspect_ratio: float = 16 / 9
    ) -> float:
        """Calculate width to maintain aspect ratio."""
        return height * aspect_ratio

    def get_canvas_info(self) -> Dict[str, Any]:
        """Get comprehensive canvas information for the AI."""
        w = self.config.canvas_width
        h = self.config.canvas_height

        return {
            "width": w,
            "height": h,
            "center": (w / 2, h / 2),
            "regions": {
                "top_left": (w / 6, h / 6),
                "top_center": (w / 2, h / 6),
                "top_right": (5 * w / 6, h / 6),
                "middle_left": (w / 6, h / 2),
                "center": (w / 2, h / 2),
                "middle_right": (5 * w / 6, h / 2),
                "bottom_left": (w / 6, 5 * h / 6),
                "bottom_center": (w / 2, 5 * h / 6),
                "bottom_right": (5 * w / 6, 5 * h / 6),
            },
            "margins": {
                "edge": self.config.edge_margin,
                "small": self.config.margin_small,
                "medium": self.config.margin_medium,
                "large": self.config.margin_large,
            },
            "safe_area": {
                "x": self.config.edge_margin,
                "y": self.config.edge_margin,
                "width": w - 2 * self.config.edge_margin,
                "height": h - 2 * self.config.edge_margin,
            }
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_layout_engine(width: int = 1200, height: int = 800) -> LayoutEngine:
    """Create a layout engine with the given canvas dimensions."""
    config = LayoutConfig(canvas_width=width, canvas_height=height)
    return LayoutEngine(config)


def calculate_center(canvas_width: int, canvas_height: int, element_width: float, element_height: float) -> Tuple[float, float]:
    """Quick calculation to center an element."""
    return (
        (canvas_width - element_width) / 2,
        (canvas_height - element_height) / 2
    )


def calculate_right_align(canvas_width: int, element_width: float, margin: float = 40) -> float:
    """Quick calculation for right alignment."""
    return canvas_width - element_width - margin


def calculate_bottom_align(canvas_height: int, element_height: float, margin: float = 40) -> float:
    """Quick calculation for bottom alignment."""
    return canvas_height - element_height - margin
