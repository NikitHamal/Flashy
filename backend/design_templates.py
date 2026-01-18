"""
Professional Design Templates

This module exposes template utilities, canvas presets, and palette helpers.
Template definitions are stored in a separate catalog for modularity.
"""

from typing import List, Dict, Any, Optional

from .design_templates_base import (
    TemplateCategory,
    ColorPalette,
    TemplateElement,
    DesignTemplate,
    PALETTES,
)
from .design_templates_catalog import TEMPLATE_CATALOG


TEMPLATES: Dict[str, DesignTemplate] = dict(TEMPLATE_CATALOG)


# =============================================================================
# CANVAS SIZE PRESETS
# =============================================================================

CANVAS_PRESETS = {
    # Social Media
    "instagram_post": {"width": 1080, "height": 1080, "name": "Instagram Post"},
    "instagram_story": {"width": 1080, "height": 1920, "name": "Instagram Story"},
    "instagram_reel": {"width": 1080, "height": 1920, "name": "Instagram Reel"},
    "instagram_portrait": {"width": 1080, "height": 1350, "name": "Instagram Portrait"},
    "instagram_landscape": {"width": 1080, "height": 566, "name": "Instagram Landscape"},
    "facebook_post": {"width": 1200, "height": 630, "name": "Facebook Post"},
    "facebook_story": {"width": 1080, "height": 1920, "name": "Facebook Story"},
    "facebook_cover": {"width": 820, "height": 312, "name": "Facebook Cover"},
    "twitter_post": {"width": 1200, "height": 675, "name": "Twitter/X Post"},
    "twitter_header": {"width": 1500, "height": 500, "name": "Twitter/X Header"},
    "linkedin_post": {"width": 1200, "height": 628, "name": "LinkedIn Post"},
    "linkedin_banner": {"width": 1584, "height": 396, "name": "LinkedIn Banner"},
    "threads_post": {"width": 1080, "height": 1350, "name": "Threads Post"},
    "youtube_thumbnail": {"width": 1280, "height": 720, "name": "YouTube Thumbnail"},
    "youtube_banner": {"width": 2560, "height": 1440, "name": "YouTube Channel Banner"},
    "pinterest_pin": {"width": 1000, "height": 1500, "name": "Pinterest Pin"},
    "tiktok_video": {"width": 1080, "height": 1920, "name": "TikTok Video"},
    "snapchat_story": {"width": 1080, "height": 1920, "name": "Snapchat Story"},
    "whatsapp_status": {"width": 1080, "height": 1920, "name": "WhatsApp Status"},

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
        {"id": key, **value}
        for key, value in CANVAS_PRESETS.items()
    ]


def search_templates(query: str) -> List[DesignTemplate]:
    """Search templates by name, description, or tags."""
    query = query.lower()
    results = []
    for template in TEMPLATES.values():
        if (
            query in template.name.lower()
            or query in template.description.lower()
            or any(query in tag.lower() for tag in template.tags)
        ):
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

    if template.palette:
        if template.background == template.palette.background:
            new_template.background = palette.background

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
