"""Presentation templates."""

from .base import DesignTemplate, TemplateCategory, TemplateElement
from .palettes import PALETTES


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
