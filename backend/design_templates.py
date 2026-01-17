"""
Professional Design Templates

This module provides a comprehensive library of design templates and presets
for common design use cases. Templates include predefined layouts, color schemes,
and element configurations for professional output.

Template Categories:
- Business: Cards, letterheads, presentations
- Social Media: Posts, banners, stories
- Marketing: Flyers, posters, ads
- Web: Hero sections, features, CTAs
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


# =============================================================================
# COLOR PALETTES
# =============================================================================

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
}


# =============================================================================
# BUSINESS CARD TEMPLATES
# =============================================================================

BUSINESS_CARD_MODERN = DesignTemplate(
    id="business_card_modern",
    name="Modern Business Card",
    description="Clean, minimal business card with bold typography",
    category=TemplateCategory.BUSINESS,
    width=1050,
    height=600,
    background="#FFFFFF",
    palette=PALETTES["corporate_blue"],
    tags=["business", "card", "professional", "minimal"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="accent_bar",
            x=0, y=0, width=8, height=600,
            properties={"fill": "#2563EB", "rx": 0, "ry": 0}
        ),
        TemplateElement(
            element_type="text",
            name="name",
            x=60, y=180,
            width=600, height=48,
            properties={
                "text": "John Doe",
                "fontSize": 42,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#1E293B"
            }
        ),
        TemplateElement(
            element_type="text",
            name="title",
            x=60, y=240,
            width=500, height=24,
            properties={
                "text": "Senior Product Designer",
                "fontSize": 18,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#64748B"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="divider",
            x=60, y=290, width=80, height=3,
            properties={"fill": "#2563EB", "rx": 1, "ry": 1}
        ),
        TemplateElement(
            element_type="text",
            name="email",
            x=60, y=340,
            width=400, height=18,
            properties={
                "text": "john.doe@company.com",
                "fontSize": 14,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#64748B"
            }
        ),
        TemplateElement(
            element_type="text",
            name="phone",
            x=60, y=370,
            width=400, height=18,
            properties={
                "text": "+1 (555) 123-4567",
                "fontSize": 14,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#64748B"
            }
        ),
        TemplateElement(
            element_type="text",
            name="website",
            x=60, y=400,
            width=400, height=18,
            properties={
                "text": "www.company.com",
                "fontSize": 14,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#2563EB"
            }
        ),
        TemplateElement(
            element_type="circle",
            name="logo_circle",
            x=880, y=240,
            width=120, height=120,
            properties={"fill": "#2563EB", "radius": 60}
        ),
    ]
)

BUSINESS_CARD_ELEGANT = DesignTemplate(
    id="business_card_elegant",
    name="Elegant Business Card",
    description="Sophisticated design with luxury feel",
    category=TemplateCategory.BUSINESS,
    width=1050,
    height=600,
    background="#FFFBEB",
    palette=PALETTES["luxury_gold"],
    tags=["business", "card", "elegant", "luxury"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="border",
            x=20, y=20, width=1010, height=560,
            properties={
                "fill": "transparent",
                "stroke": "#B45309",
                "strokeWidth": 2,
                "rx": 0, "ry": 0
            }
        ),
        TemplateElement(
            element_type="text",
            name="name",
            x=525, y=200,
            width=600, height=52,
            properties={
                "text": "Alexandra Smith",
                "fontSize": 38,
                "fontFamily": "Playfair Display",
                "fontWeight": "600",
                "fill": "#451A03",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="title",
            x=525, y=260,
            width=500, height=20,
            properties={
                "text": "Creative Director",
                "fontSize": 16,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#78350F",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="divider_left",
            x=350, y=310, width=100, height=1,
            properties={"fill": "#B45309"}
        ),
        TemplateElement(
            element_type="rectangle",
            name="divider_right",
            x=600, y=310, width=100, height=1,
            properties={"fill": "#B45309"}
        ),
        TemplateElement(
            element_type="text",
            name="contact",
            x=525, y=360,
            width=600, height=80,
            properties={
                "text": "hello@studio.com | +1 555 000 0000",
                "fontSize": 13,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#78350F",
                "textAlign": "center"
            }
        ),
    ]
)


# =============================================================================
# SOCIAL MEDIA TEMPLATES
# =============================================================================

INSTAGRAM_POST_MODERN = DesignTemplate(
    id="instagram_post_modern",
    name="Instagram Post - Modern",
    description="Clean Instagram post with gradient accent",
    category=TemplateCategory.SOCIAL_MEDIA,
    width=1080,
    height=1080,
    background="#FFFFFF",
    palette=PALETTES["tech_purple"],
    tags=["instagram", "social", "modern", "gradient"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="gradient_bar",
            x=0, y=940, width=1080, height=140,
            properties={"fill": "#7C3AED", "rx": 0, "ry": 0}
        ),
        TemplateElement(
            element_type="text",
            name="headline",
            x=540, y=400,
            width=900, height=80,
            properties={
                "text": "Your Headline Here",
                "fontSize": 64,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#1C1917",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="subheadline",
            x=540, y=500,
            width=800, height=40,
            properties={
                "text": "Supporting text goes here with more details",
                "fontSize": 24,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#57534E",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="cta",
            x=540, y=1000,
            width=400, height=32,
            properties={
                "text": "LEARN MORE →",
                "fontSize": 18,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#FFFFFF",
                "textAlign": "center"
            }
        ),
    ]
)

SOCIAL_BANNER_GRADIENT = DesignTemplate(
    id="social_banner_gradient",
    name="Social Banner - Gradient",
    description="Eye-catching banner with gradient background",
    category=TemplateCategory.SOCIAL_MEDIA,
    width=1200,
    height=628,
    background="#7C3AED",
    palette=PALETTES["tech_purple"],
    tags=["banner", "social", "gradient", "facebook", "linkedin"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="overlay",
            x=0, y=0, width=1200, height=628,
            properties={"fill": "#4F46E5", "opacity": 0.3}
        ),
        TemplateElement(
            element_type="circle",
            name="accent_circle_1",
            x=-100, y=-100, width=400, height=400,
            properties={"fill": "#06B6D4", "opacity": 0.2, "radius": 200}
        ),
        TemplateElement(
            element_type="circle",
            name="accent_circle_2",
            x=1000, y=400, width=300, height=300,
            properties={"fill": "#EC4899", "opacity": 0.2, "radius": 150}
        ),
        TemplateElement(
            element_type="text",
            name="headline",
            x=600, y=260,
            width=1000, height=72,
            properties={
                "text": "Make Something Amazing",
                "fontSize": 56,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#FFFFFF",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="subheadline",
            x=600, y=340,
            width=800, height=32,
            properties={
                "text": "Transform your ideas into reality with our platform",
                "fontSize": 22,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#E0E7FF",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="cta_button",
            x=500, y=420, width=200, height=50,
            properties={
                "fill": "#FFFFFF",
                "rx": 25, "ry": 25
            }
        ),
        TemplateElement(
            element_type="text",
            name="cta_text",
            x=600, y=455,
            width=180, height=24,
            properties={
                "text": "Get Started",
                "fontSize": 16,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#7C3AED",
                "textAlign": "center"
            }
        ),
    ]
)


# =============================================================================
# PRESENTATION TEMPLATES
# =============================================================================

PRESENTATION_TITLE_SLIDE = DesignTemplate(
    id="presentation_title_slide",
    name="Presentation Title Slide",
    description="Professional title slide for presentations",
    category=TemplateCategory.PRESENTATION,
    width=1920,
    height=1080,
    background="#FFFFFF",
    palette=PALETTES["corporate_blue"],
    tags=["presentation", "title", "professional", "corporate"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="accent_bar",
            x=0, y=0, width=1920, height=8,
            properties={"fill": "#2563EB"}
        ),
        TemplateElement(
            element_type="text",
            name="title",
            x=960, y=420,
            width=1600, height=80,
            properties={
                "text": "Presentation Title",
                "fontSize": 72,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#1E293B",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="subtitle",
            x=960, y=520,
            width=1200, height=40,
            properties={
                "text": "A brief description or subtitle for your presentation",
                "fontSize": 28,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#64748B",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="divider",
            x=860, y=600, width=200, height=4,
            properties={"fill": "#2563EB", "rx": 2, "ry": 2}
        ),
        TemplateElement(
            element_type="text",
            name="author",
            x=960, y=680,
            width=600, height=28,
            properties={
                "text": "Presented by John Doe",
                "fontSize": 20,
                "fontFamily": "Inter",
                "fontWeight": "500",
                "fill": "#64748B",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="date",
            x=960, y=720,
            width=400, height=24,
            properties={
                "text": "January 2026",
                "fontSize": 16,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#94A3B8",
                "textAlign": "center"
            }
        ),
    ]
)

PRESENTATION_CONTENT_SLIDE = DesignTemplate(
    id="presentation_content_slide",
    name="Presentation Content Slide",
    description="Clean content slide with header",
    category=TemplateCategory.PRESENTATION,
    width=1920,
    height=1080,
    background="#FFFFFF",
    palette=PALETTES["corporate_blue"],
    tags=["presentation", "content", "professional"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="header_bg",
            x=0, y=0, width=1920, height=120,
            properties={"fill": "#F8FAFC"}
        ),
        TemplateElement(
            element_type="text",
            name="slide_title",
            x=100, y=70,
            width=1200, height=48,
            properties={
                "text": "Section Title",
                "fontSize": 40,
                "fontFamily": "Poppins",
                "fontWeight": "600",
                "fill": "#1E293B"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="content_area",
            x=100, y=180, width=1720, height=800,
            properties={"fill": "transparent"}
        ),
        TemplateElement(
            element_type="text",
            name="slide_number",
            x=1820, y=1040,
            width=60, height=24,
            properties={
                "text": "01",
                "fontSize": 16,
                "fontFamily": "Inter",
                "fontWeight": "500",
                "fill": "#94A3B8",
                "textAlign": "right"
            }
        ),
    ]
)


# =============================================================================
# MARKETING TEMPLATES
# =============================================================================

MARKETING_POSTER_BOLD = DesignTemplate(
    id="marketing_poster_bold",
    name="Bold Marketing Poster",
    description="High-impact poster with bold typography",
    category=TemplateCategory.MARKETING,
    width=1200,
    height=1800,
    background="#0F172A",
    palette=PALETTES["modern_dark"],
    tags=["poster", "marketing", "bold", "event"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="accent_shape_1",
            x=-200, y=1400, width=600, height=600,
            properties={"fill": "#3B82F6", "opacity": 0.15, "angle": 45}
        ),
        TemplateElement(
            element_type="rectangle",
            name="accent_shape_2",
            x=900, y=-100, width=400, height=400,
            properties={"fill": "#8B5CF6", "opacity": 0.15, "angle": -15}
        ),
        TemplateElement(
            element_type="text",
            name="eyebrow",
            x=600, y=300,
            width=800, height=24,
            properties={
                "text": "ANNOUNCING",
                "fontSize": 18,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#10B981",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="headline",
            x=600, y=500,
            width=1000, height=200,
            properties={
                "text": "THE BIG\nEVENT",
                "fontSize": 120,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#F8FAFC",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="date",
            x=600, y=800,
            width=600, height=40,
            properties={
                "text": "March 15, 2026",
                "fontSize": 32,
                "fontFamily": "Inter",
                "fontWeight": "500",
                "fill": "#94A3B8",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="cta_button",
            x=450, y=1500, width=300, height=60,
            properties={"fill": "#3B82F6", "rx": 8, "ry": 8}
        ),
        TemplateElement(
            element_type="text",
            name="cta_text",
            x=600, y=1540,
            width=280, height=28,
            properties={
                "text": "Register Now",
                "fontSize": 20,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#FFFFFF",
                "textAlign": "center"
            }
        ),
    ]
)


# =============================================================================
# TEMPLATE REGISTRY
# =============================================================================

TEMPLATES: Dict[str, DesignTemplate] = {
    # Business
    "business_card_modern": BUSINESS_CARD_MODERN,
    "business_card_elegant": BUSINESS_CARD_ELEGANT,

    # Social Media
    "instagram_post_modern": INSTAGRAM_POST_MODERN,
    "social_banner_gradient": SOCIAL_BANNER_GRADIENT,

    # Presentations
    "presentation_title_slide": PRESENTATION_TITLE_SLIDE,
    "presentation_content_slide": PRESENTATION_CONTENT_SLIDE,

    # Marketing
    "marketing_poster_bold": MARKETING_POSTER_BOLD,
}


# =============================================================================
# CANVAS SIZE PRESETS
# =============================================================================

CANVAS_PRESETS = {
    # Social Media
    "instagram_post": {"width": 1080, "height": 1080, "name": "Instagram Post"},
    "instagram_story": {"width": 1080, "height": 1920, "name": "Instagram Story"},
    "facebook_post": {"width": 1200, "height": 630, "name": "Facebook Post"},
    "facebook_cover": {"width": 820, "height": 312, "name": "Facebook Cover"},
    "twitter_post": {"width": 1200, "height": 675, "name": "Twitter Post"},
    "twitter_header": {"width": 1500, "height": 500, "name": "Twitter Header"},
    "linkedin_post": {"width": 1200, "height": 628, "name": "LinkedIn Post"},
    "linkedin_banner": {"width": 1584, "height": 396, "name": "LinkedIn Banner"},
    "youtube_thumbnail": {"width": 1280, "height": 720, "name": "YouTube Thumbnail"},
    "pinterest_pin": {"width": 1000, "height": 1500, "name": "Pinterest Pin"},

    # Business
    "business_card": {"width": 1050, "height": 600, "name": "Business Card"},
    "letterhead": {"width": 2480, "height": 3508, "name": "Letterhead A4"},
    "invoice": {"width": 2480, "height": 3508, "name": "Invoice A4"},

    # Presentations
    "presentation_16_9": {"width": 1920, "height": 1080, "name": "Presentation 16:9"},
    "presentation_4_3": {"width": 1600, "height": 1200, "name": "Presentation 4:3"},

    # Print
    "poster_portrait": {"width": 1200, "height": 1800, "name": "Poster Portrait"},
    "poster_landscape": {"width": 1800, "height": 1200, "name": "Poster Landscape"},
    "flyer_a5": {"width": 1748, "height": 2480, "name": "Flyer A5"},

    # Web
    "web_banner": {"width": 1920, "height": 600, "name": "Web Banner"},
    "hero_section": {"width": 1440, "height": 800, "name": "Hero Section"},
    "email_header": {"width": 600, "height": 200, "name": "Email Header"},
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_template(template_id: str) -> Optional[DesignTemplate]:
    """Get a template by its ID."""
    return TEMPLATES.get(template_id)


def get_templates_by_category(category: TemplateCategory) -> List[DesignTemplate]:
    """Get all templates in a category."""
    return [t for t in TEMPLATES.values() if t.category == category]


def get_all_templates() -> List[Dict[str, Any]]:
    """Get summary info for all templates."""
    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "category": t.category.value,
            "width": t.width,
            "height": t.height,
            "tags": t.tags,
        }
        for t in TEMPLATES.values()
    ]


def get_palette(palette_name: str) -> Optional[ColorPalette]:
    """Get a color palette by name."""
    return PALETTES.get(palette_name)


def get_all_palettes() -> List[Dict[str, str]]:
    """Get all available palettes."""
    return [p.to_dict() for p in PALETTES.values()]


def get_canvas_preset(preset_name: str) -> Optional[Dict[str, Any]]:
    """Get a canvas size preset."""
    return CANVAS_PRESETS.get(preset_name)


def get_all_canvas_presets() -> List[Dict[str, Any]]:
    """Get all canvas size presets."""
    return [
        {"id": k, **v}
        for k, v in CANVAS_PRESETS.items()
    ]


def search_templates(query: str) -> List[DesignTemplate]:
    """Search templates by name, description, or tags."""
    query = query.lower()
    results = []
    for template in TEMPLATES.values():
        if (query in template.name.lower() or
            query in template.description.lower() or
            any(query in tag.lower() for tag in template.tags)):
            results.append(template)
    return results


def apply_palette_to_template(
    template: DesignTemplate,
    palette: ColorPalette
) -> DesignTemplate:
    """Apply a different color palette to a template."""
    import copy
    new_template = copy.deepcopy(template)
    new_template.palette = palette

    # Update background if it matches old palette
    if template.palette:
        if template.background == template.palette.background:
            new_template.background = palette.background

    # Update element colors based on palette mapping
    color_map = {}
    if template.palette:
        old_p = template.palette
        color_map = {
            old_p.primary: palette.primary,
            old_p.secondary: palette.secondary,
            old_p.accent: palette.accent,
            old_p.background: palette.background,
            old_p.surface: palette.surface,
            old_p.text: palette.text,
            old_p.text_secondary: palette.text_secondary,
        }

    for element in new_template.elements:
        if "fill" in element.properties:
            old_fill = element.properties["fill"]
            if old_fill in color_map:
                element.properties["fill"] = color_map[old_fill]
        if "stroke" in element.properties:
            old_stroke = element.properties["stroke"]
            if old_stroke in color_map:
                element.properties["stroke"] = color_map[old_stroke]

    return new_template
