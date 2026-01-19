"""Marketing templates."""

from .base import DesignTemplate, TemplateCategory, TemplateElement
from .palettes import PALETTES


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
