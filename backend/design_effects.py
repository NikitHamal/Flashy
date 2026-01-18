"""
Design Effects Module

This module provides advanced visual effects for the Flashy Design Agent.
Includes gradients, shadows, filters, and blend modes for professional design output.

All effects are represented as data structures that map directly to CSS/Fabric.js properties.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import math


class GradientType(Enum):
    """Types of gradients."""
    LINEAR = "linear"
    RADIAL = "radial"
    CONIC = "conic"


class BlendMode(Enum):
    """CSS/Canvas blend modes."""
    NORMAL = "normal"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    OVERLAY = "overlay"
    DARKEN = "darken"
    LIGHTEN = "lighten"
    COLOR_DODGE = "color-dodge"
    COLOR_BURN = "color-burn"
    HARD_LIGHT = "hard-light"
    SOFT_LIGHT = "soft-light"
    DIFFERENCE = "difference"
    EXCLUSION = "exclusion"
    HUE = "hue"
    SATURATION = "saturation"
    COLOR = "color"
    LUMINOSITY = "luminosity"


class FilterType(Enum):
    """Available filter types."""
    BRIGHTNESS = "brightness"
    CONTRAST = "contrast"
    SATURATION = "saturation"
    GRAYSCALE = "grayscale"
    SEPIA = "sepia"
    INVERT = "invert"
    BLUR = "blur"
    HUE_ROTATE = "hue-rotate"


@dataclass
class GradientStop:
    """A single color stop in a gradient."""
    offset: float  # 0.0 to 1.0
    color: str  # hex or rgba

    def to_dict(self) -> Dict[str, Any]:
        return {"offset": self.offset, "color": self.color}


@dataclass
class LinearGradient:
    """Linear gradient definition."""
    stops: List[GradientStop]
    angle: float = 0  # degrees, 0 = left to right, 90 = top to bottom

    # Coordinates (0-1 range, relative to object bounds)
    x1: float = 0
    y1: float = 0.5
    x2: float = 1
    y2: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        # Calculate coordinates from angle
        rad = math.radians(self.angle)
        x1 = 0.5 - 0.5 * math.cos(rad)
        y1 = 0.5 - 0.5 * math.sin(rad)
        x2 = 0.5 + 0.5 * math.cos(rad)
        y2 = 0.5 + 0.5 * math.sin(rad)

        return {
            "type": "linear",
            "angle": self.angle,
            "coords": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
            "colorStops": [stop.to_dict() for stop in self.stops]
        }

    def to_css(self) -> str:
        """Convert to CSS gradient string."""
        stops_str = ", ".join(
            f"{stop.color} {stop.offset * 100}%" for stop in self.stops
        )
        return f"linear-gradient({self.angle}deg, {stops_str})"


@dataclass
class RadialGradient:
    """Radial gradient definition."""
    stops: List[GradientStop]

    # Center position (0-1 range, relative to object bounds)
    cx: float = 0.5
    cy: float = 0.5

    # Radii (0-1 range)
    r1: float = 0  # inner radius
    r2: float = 0.5  # outer radius

    # Focal point offset
    fx: float = 0.5
    fy: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "radial",
            "coords": {
                "x1": self.fx, "y1": self.fy,  # focal point
                "x2": self.cx, "y2": self.cy,  # center
                "r1": self.r1, "r2": self.r2
            },
            "colorStops": [stop.to_dict() for stop in self.stops]
        }

    def to_css(self) -> str:
        """Convert to CSS gradient string."""
        stops_str = ", ".join(
            f"{stop.color} {stop.offset * 100}%" for stop in self.stops
        )
        return f"radial-gradient(circle at {self.cx * 100}% {self.cy * 100}%, {stops_str})"


@dataclass
class ConicGradient:
    """Conic (angular) gradient definition."""
    stops: List[GradientStop]
    cx: float = 0.5  # center x
    cy: float = 0.5  # center y
    start_angle: float = 0  # degrees

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "conic",
            "coords": {"cx": self.cx, "cy": self.cy},
            "startAngle": self.start_angle,
            "colorStops": [stop.to_dict() for stop in self.stops]
        }

    def to_css(self) -> str:
        stops_str = ", ".join(
            f"{stop.color} {stop.offset * 360}deg" for stop in self.stops
        )
        return f"conic-gradient(from {self.start_angle}deg at {self.cx * 100}% {self.cy * 100}%, {stops_str})"


@dataclass
class Shadow:
    """Shadow effect definition (works for drop shadow and text shadow)."""
    offset_x: float = 4
    offset_y: float = 4
    blur: float = 8
    spread: float = 0  # only for box-shadow, not available in Fabric.js
    color: str = "rgba(0, 0, 0, 0.3)"
    inset: bool = False  # inner shadow

    def to_dict(self) -> Dict[str, Any]:
        return {
            "offsetX": self.offset_x,
            "offsetY": self.offset_y,
            "blur": self.blur,
            "spread": self.spread,
            "color": self.color,
            "inset": self.inset
        }

    def to_fabric_shadow(self) -> Dict[str, Any]:
        """Convert to Fabric.js shadow format."""
        return {
            "color": self.color,
            "blur": self.blur,
            "offsetX": self.offset_x,
            "offsetY": self.offset_y,
            "affectStroke": False,
            "nonScaling": False
        }

    def to_css(self) -> str:
        """Convert to CSS box-shadow string."""
        inset_str = "inset " if self.inset else ""
        return f"{inset_str}{self.offset_x}px {self.offset_y}px {self.blur}px {self.spread}px {self.color}"


@dataclass
class Filter:
    """Image/object filter effect."""
    filter_type: FilterType
    value: float  # Meaning depends on filter type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.filter_type.value,
            "value": self.value
        }

    def to_css(self) -> str:
        """Convert to CSS filter string."""
        ft = self.filter_type

        if ft == FilterType.BRIGHTNESS:
            return f"brightness({self.value})"
        elif ft == FilterType.CONTRAST:
            return f"contrast({self.value})"
        elif ft == FilterType.SATURATION:
            return f"saturate({self.value})"
        elif ft == FilterType.GRAYSCALE:
            return f"grayscale({self.value})"
        elif ft == FilterType.SEPIA:
            return f"sepia({self.value})"
        elif ft == FilterType.INVERT:
            return f"invert({self.value})"
        elif ft == FilterType.BLUR:
            return f"blur({self.value}px)"
        elif ft == FilterType.HUE_ROTATE:
            return f"hue-rotate({self.value}deg)"

        return ""


@dataclass
class FilterStack:
    """Stack of filters to apply to an object."""
    filters: List[Filter] = field(default_factory=list)

    def add(self, filter_type: FilterType, value: float) -> "FilterStack":
        """Add a filter to the stack."""
        self.filters.append(Filter(filter_type, value))
        return self

    def to_dict(self) -> List[Dict[str, Any]]:
        return [f.to_dict() for f in self.filters]

    def to_css(self) -> str:
        """Convert entire filter stack to CSS."""
        return " ".join(f.to_css() for f in self.filters)


@dataclass
class TextEffects:
    """Advanced text styling effects."""
    letter_spacing: float = 0  # pixels or em
    line_height: float = 1.2  # multiplier
    text_shadow: Optional[Shadow] = None
    stroke_width: float = 0
    stroke_color: str = "transparent"
    text_decoration: str = "none"  # none, underline, line-through
    text_transform: str = "none"  # none, uppercase, lowercase, capitalize

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "letterSpacing": self.letter_spacing,
            "lineHeight": self.line_height,
            "strokeWidth": self.stroke_width,
            "strokeColor": self.stroke_color,
            "textDecoration": self.text_decoration,
            "textTransform": self.text_transform,
        }
        if self.text_shadow:
            result["textShadow"] = self.text_shadow.to_dict()
        return result


@dataclass
class ObjectEffects:
    """Complete effects configuration for a canvas object."""
    shadow: Optional[Shadow] = None
    gradient: Optional[Any] = None  # LinearGradient, RadialGradient, or ConicGradient
    filters: Optional[FilterStack] = None
    blend_mode: BlendMode = BlendMode.NORMAL
    backdrop_blur: float = 0  # pixels, for glassmorphism effect
    border_radius: float = 0  # for rounded corners on any shape

    # For text objects
    text_effects: Optional[TextEffects] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "blendMode": self.blend_mode.value,
            "backdropBlur": self.backdrop_blur,
            "borderRadius": self.border_radius,
        }

        if self.shadow:
            result["shadow"] = self.shadow.to_dict()
        if self.gradient:
            result["gradient"] = self.gradient.to_dict()
        if self.filters:
            result["filters"] = self.filters.to_dict()
        if self.text_effects:
            result["textEffects"] = self.text_effects.to_dict()

        return result


# =============================================================================
# EFFECT PRESETS
# =============================================================================

class EffectPresets:
    """Pre-configured effect combinations for common use cases."""

    @staticmethod
    def soft_shadow() -> Shadow:
        """Subtle, soft drop shadow."""
        return Shadow(
            offset_x=0, offset_y=4, blur=12,
            spread=0, color="rgba(0, 0, 0, 0.15)"
        )

    @staticmethod
    def hard_shadow() -> Shadow:
        """Sharp, defined drop shadow."""
        return Shadow(
            offset_x=4, offset_y=4, blur=0,
            spread=0, color="rgba(0, 0, 0, 0.25)"
        )

    @staticmethod
    def glow(color: str = "#ffffff") -> Shadow:
        """Glowing effect around object."""
        return Shadow(
            offset_x=0, offset_y=0, blur=20,
            spread=0, color=color
        )

    @staticmethod
    def inner_shadow() -> Shadow:
        """Inner shadow for depth."""
        return Shadow(
            offset_x=2, offset_y=2, blur=4,
            spread=0, color="rgba(0, 0, 0, 0.2)",
            inset=True
        )

    @staticmethod
    def long_shadow(color: str = "rgba(0, 0, 0, 0.15)") -> Shadow:
        """Long flat shadow for flat design."""
        return Shadow(
            offset_x=20, offset_y=20, blur=0,
            spread=0, color=color
        )

    @staticmethod
    def gradient_blue_purple() -> LinearGradient:
        """Popular blue to purple gradient."""
        return LinearGradient(
            angle=135,
            stops=[
                GradientStop(0, "#667eea"),
                GradientStop(1, "#764ba2")
            ]
        )

    @staticmethod
    def gradient_sunset() -> LinearGradient:
        """Warm sunset gradient."""
        return LinearGradient(
            angle=135,
            stops=[
                GradientStop(0, "#f093fb"),
                GradientStop(0.5, "#f5576c"),
                GradientStop(1, "#f7971e")
            ]
        )

    @staticmethod
    def gradient_ocean() -> LinearGradient:
        """Ocean blue gradient."""
        return LinearGradient(
            angle=135,
            stops=[
                GradientStop(0, "#2193b0"),
                GradientStop(1, "#6dd5ed")
            ]
        )

    @staticmethod
    def gradient_midnight() -> LinearGradient:
        """Dark midnight gradient."""
        return LinearGradient(
            angle=135,
            stops=[
                GradientStop(0, "#232526"),
                GradientStop(1, "#414345")
            ]
        )

    @staticmethod
    def gradient_emerald() -> LinearGradient:
        """Fresh emerald green gradient."""
        return LinearGradient(
            angle=135,
            stops=[
                GradientStop(0, "#11998e"),
                GradientStop(1, "#38ef7d")
            ]
        )

    @staticmethod
    def gradient_fire() -> LinearGradient:
        """Hot fire gradient."""
        return LinearGradient(
            angle=135,
            stops=[
                GradientStop(0, "#f12711"),
                GradientStop(1, "#f5af19")
            ]
        )

    @staticmethod
    def gradient_rainbow() -> LinearGradient:
        """Full rainbow spectrum."""
        return LinearGradient(
            angle=90,
            stops=[
                GradientStop(0, "#ff0000"),
                GradientStop(0.16, "#ff8000"),
                GradientStop(0.33, "#ffff00"),
                GradientStop(0.5, "#00ff00"),
                GradientStop(0.66, "#0080ff"),
                GradientStop(0.83, "#8000ff"),
                GradientStop(1, "#ff00ff")
            ]
        )

    @staticmethod
    def gradient_radial_spotlight() -> RadialGradient:
        """Spotlight effect from center."""
        return RadialGradient(
            cx=0.5, cy=0.5, r1=0, r2=0.7,
            stops=[
                GradientStop(0, "rgba(255, 255, 255, 0.3)"),
                GradientStop(1, "rgba(0, 0, 0, 0)")
            ]
        )

    @staticmethod
    def glassmorphism() -> ObjectEffects:
        """Modern glassmorphism effect."""
        return ObjectEffects(
            backdrop_blur=10,
            shadow=Shadow(
                offset_x=0, offset_y=8, blur=32,
                color="rgba(0, 0, 0, 0.1)"
            ),
            border_radius=16
        )

    @staticmethod
    def neumorphism_light() -> Tuple[Shadow, Shadow]:
        """Light neumorphism with two shadows."""
        light_shadow = Shadow(
            offset_x=-8, offset_y=-8, blur=16,
            color="rgba(255, 255, 255, 0.8)"
        )
        dark_shadow = Shadow(
            offset_x=8, offset_y=8, blur=16,
            color="rgba(0, 0, 0, 0.1)"
        )
        return light_shadow, dark_shadow


# =============================================================================
# COLOR UTILITIES
# =============================================================================

def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """Convert hex color to rgba string."""
    hex_color = hex_color.lstrip('#')

    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    return f"rgba({r}, {g}, {b}, {alpha})"


def rgba_to_hex(rgba_str: str) -> Tuple[str, float]:
    """Parse rgba string to hex and alpha."""
    import re
    match = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)', rgba_str)
    if not match:
        return rgba_str, 1.0

    r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
    alpha = float(match.group(4)) if match.group(4) else 1.0

    hex_color = f"#{r:02x}{g:02x}{b:02x}"
    return hex_color, alpha


def lighten_color(hex_color: str, amount: float = 0.2) -> str:
    """Lighten a hex color by a given amount (0-1)."""
    hex_color = hex_color.lstrip('#')

    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    r = min(255, int(r + (255 - r) * amount))
    g = min(255, int(g + (255 - g) * amount))
    b = min(255, int(b + (255 - b) * amount))

    return f"#{r:02x}{g:02x}{b:02x}"


def darken_color(hex_color: str, amount: float = 0.2) -> str:
    """Darken a hex color by a given amount (0-1)."""
    hex_color = hex_color.lstrip('#')

    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    r = max(0, int(r * (1 - amount)))
    g = max(0, int(g * (1 - amount)))
    b = max(0, int(b * (1 - amount)))

    return f"#{r:02x}{g:02x}{b:02x}"


def get_complementary_color(hex_color: str) -> str:
    """Get the complementary (opposite) color."""
    hex_color = hex_color.lstrip('#')

    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)

    r = 255 - int(hex_color[0:2], 16)
    g = 255 - int(hex_color[2:4], 16)
    b = 255 - int(hex_color[4:6], 16)

    return f"#{r:02x}{g:02x}{b:02x}"


def create_color_palette(base_color: str, count: int = 5) -> List[str]:
    """Generate a color palette from a base color."""
    palette = [base_color]

    # Add lighter variations
    for i in range(1, (count + 1) // 2):
        palette.insert(0, lighten_color(base_color, i * 0.15))

    # Add darker variations
    for i in range(1, count - len(palette) + 1):
        palette.append(darken_color(base_color, i * 0.15))

    return palette[:count]


# =============================================================================
# GRADIENT BUILDERS
# =============================================================================

def create_linear_gradient(
    color1: str,
    color2: str,
    angle: float = 0,
    midpoint: float = 0.5
) -> LinearGradient:
    """Create a simple two-color linear gradient."""
    return LinearGradient(
        angle=angle,
        stops=[
            GradientStop(0, color1),
            GradientStop(midpoint, lighten_color(color1, 0.1) if midpoint != 0.5 else None),
            GradientStop(1, color2)
        ] if midpoint != 0.5 else [
            GradientStop(0, color1),
            GradientStop(1, color2)
        ]
    )


def create_multi_stop_gradient(
    colors: List[str],
    angle: float = 0
) -> LinearGradient:
    """Create a gradient with evenly distributed color stops."""
    count = len(colors)
    stops = []
    for i, color in enumerate(colors):
        offset = i / (count - 1) if count > 1 else 0
        stops.append(GradientStop(offset, color))

    return LinearGradient(angle=angle, stops=stops)


def create_radial_gradient(
    inner_color: str,
    outer_color: str,
    cx: float = 0.5,
    cy: float = 0.5
) -> RadialGradient:
    """Create a simple two-color radial gradient."""
    return RadialGradient(
        cx=cx, cy=cy, r1=0, r2=0.5,
        stops=[
            GradientStop(0, inner_color),
            GradientStop(1, outer_color)
        ]
    )


# =============================================================================
# SHADOW BUILDERS
# =============================================================================

def create_shadow(
    offset_x: float = 4,
    offset_y: float = 4,
    blur: float = 8,
    color: str = None,
    opacity: float = 0.3
) -> Shadow:
    """Create a shadow with configurable parameters."""
    if color is None:
        color = f"rgba(0, 0, 0, {opacity})"

    return Shadow(
        offset_x=offset_x,
        offset_y=offset_y,
        blur=blur,
        color=color
    )


def create_text_shadow(
    offset_x: float = 1,
    offset_y: float = 1,
    blur: float = 2,
    color: str = "rgba(0, 0, 0, 0.3)"
) -> Shadow:
    """Create a shadow optimized for text."""
    return Shadow(
        offset_x=offset_x,
        offset_y=offset_y,
        blur=blur,
        color=color
    )
