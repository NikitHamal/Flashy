"""Business-focused templates."""

from .base import DesignTemplate, TemplateCategory, TemplateElement
from .palettes import PALETTES


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
