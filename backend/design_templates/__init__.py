"""Design template library with palettes, presets, and registry helpers."""

from typing import List, Dict, Any, Optional

from .base import TemplateCategory, DesignTemplate, TemplateElement, ColorPalette
from .palettes import PALETTES
from .presets import CANVAS_PRESETS
from .templates_business import BUSINESS_CARD_MODERN, BUSINESS_CARD_ELEGANT
from .templates_social import INSTAGRAM_POST_MODERN, SOCIAL_BANNER_GRADIENT
from .templates_presentation import PRESENTATION_TITLE_SLIDE, PRESENTATION_CONTENT_SLIDE
from .templates_marketing import MARKETING_POSTER_BOLD
from .templates_festival import (
    SARASWATI_PUJA_PRATIGYA,
    DASHAIN_GREETING_CLASSIC,
    TIHAR_LIGHTS_GLOW,
    HOLI_COLOR_SPLASH,
    TEEJ_JOYOUS,
)


TEMPLATES: Dict[str, DesignTemplate] = {
    # Business
    "business_card_modern": BUSINESS_CARD_MODERN,
    "business_card_elegant": BUSINESS_CARD_ELEGANT,

    # Social Media
    "instagram_post_modern": INSTAGRAM_POST_MODERN,
    "social_banner_gradient": SOCIAL_BANNER_GRADIENT,

    # Festivals (Social)
    "festival_saraswati_puja_pratigya": SARASWATI_PUJA_PRATIGYA,
    "festival_dashain_classic": DASHAIN_GREETING_CLASSIC,
    "festival_tihar_glow": TIHAR_LIGHTS_GLOW,
    "festival_holi_colors": HOLI_COLOR_SPLASH,
    "festival_teej_joyous": TEEJ_JOYOUS,

    # Presentations
    "presentation_title_slide": PRESENTATION_TITLE_SLIDE,
    "presentation_content_slide": PRESENTATION_CONTENT_SLIDE,

    # Marketing
    "marketing_poster_bold": MARKETING_POSTER_BOLD,
}


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

    if template.palette and template.background == template.palette.background:
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


__all__ = [
    "TemplateCategory",
    "DesignTemplate",
    "TemplateElement",
    "ColorPalette",
    "PALETTES",
    "CANVAS_PRESETS",
    "TEMPLATES",
    "get_template",
    "get_templates_by_category",
    "get_all_templates",
    "get_palette",
    "get_all_palettes",
    "get_canvas_preset",
    "get_all_canvas_presets",
    "search_templates",
    "apply_palette_to_template",
]
