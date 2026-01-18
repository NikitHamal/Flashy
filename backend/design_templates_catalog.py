"""
Design Template Catalog

This module contains core template definitions by category.
Festival templates are stored in a separate module for modularity.
"""

from .design_templates_base import DesignTemplate, TemplateElement, TemplateCategory, PALETTES
from .design_templates_festival import FESTIVAL_TEMPLATES


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
            width=600, height=24,
            properties={
                "text": "Creative Director",
                "fontSize": 20,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#64748B"
            }
        ),
        TemplateElement(
            element_type="text",
            name="contact",
            x=60, y=340,
            width=600, height=120,
            properties={
                "text": "john@company.com\n+1 555 000 0000\ncompany.com",
                "fontSize": 16,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#334155"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="logo_placeholder",
            x=780, y=60, width=200, height=200,
            properties={
                "fill": "#E2E8F0",
                "rx": 16, "ry": 16
            }
        ),
        TemplateElement(
            element_type="text",
            name="logo_text",
            x=880, y=150,
            width=200, height=24,
            properties={
                "text": "LOGO",
                "fontSize": 20,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#64748B",
                "textAlign": "center"
            }
        ),
    ]
)

BUSINESS_CARD_ELEGANT = DesignTemplate(
    id="business_card_elegant",
    name="Elegant Business Card",
    description="Luxury business card with serif typography",
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
            x=40, y=40, width=970, height=520,
            properties={"fill": "transparent", "stroke": "#B45309", "strokeWidth": 2}
        ),
        TemplateElement(
            element_type="text",
            name="brand",
            x=525, y=120,
            width=900, height=52,
            properties={
                "text": "LUXE STUDIO",
                "fontSize": 36,
                "fontFamily": "Playfair Display",
                "fontWeight": "700",
                "fill": "#78350F",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="name",
            x=525, y=220,
            width=900, height=60,
            properties={
                "text": "Sophia Carter",
                "fontSize": 42,
                "fontFamily": "Playfair Display",
                "fontWeight": "600",
                "fill": "#451A03",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="title",
            x=525, y=280,
            width=900, height=32,
            properties={
                "text": "Founder & Creative Lead",
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
    tags=["presentation", "slide", "title", "professional"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="accent_bar",
            x=0, y=0, width=120, height=1080,
            properties={"fill": "#2563EB"}
        ),
        TemplateElement(
            element_type="text",
            name="title",
            x=260, y=320,
            width=1400, height=120,
            properties={
                "text": "Your Presentation Title",
                "fontSize": 72,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#1E293B"
            }
        ),
        TemplateElement(
            element_type="text",
            name="subtitle",
            x=260, y=460,
            width=1200, height=60,
            properties={
                "text": "Subtitle or tagline goes here",
                "fontSize": 32,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#64748B"
            }
        ),
        TemplateElement(
            element_type="text",
            name="presenter",
            x=260, y=620,
            width=800, height=32,
            properties={
                "text": "Presenter Name | Date",
                "fontSize": 20,
                "fontFamily": "Inter",
                "fontWeight": "500",
                "fill": "#94A3B8"
            }
        ),
    ]
)

PRESENTATION_CONTENT_SLIDE = DesignTemplate(
    id="presentation_content_slide",
    name="Presentation Content Slide",
    description="Clean content slide with image and text",
    category=TemplateCategory.PRESENTATION,
    width=1920,
    height=1080,
    background="#FFFFFF",
    palette=PALETTES["corporate_blue"],
    tags=["presentation", "slide", "content", "layout"],
    elements=[
        TemplateElement(
            element_type="text",
            name="title",
            x=120, y=80,
            width=1200, height=80,
            properties={
                "text": "Section Title",
                "fontSize": 48,
                "fontFamily": "Poppins",
                "fontWeight": "600",
                "fill": "#1E293B"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="image_placeholder",
            x=120, y=220, width=720, height=520,
            properties={"fill": "#E2E8F0", "rx": 16, "ry": 16}
        ),
        TemplateElement(
            element_type="text",
            name="content",
            x=900, y=240,
            width=800, height=500,
            properties={
                "text": "• Point one with insight\n• Point two with detail\n• Point three with explanation\n• Key takeaway",
                "fontSize": 28,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#475569"
            }
        ),
    ]
)


# =============================================================================
# MARKETING TEMPLATES
# =============================================================================

MARKETING_POSTER_BOLD = DesignTemplate(
    id="marketing_poster_bold",
    name="Marketing Poster - Bold",
    description="Bold poster layout for marketing campaigns",
    category=TemplateCategory.MARKETING,
    width=1200,
    height=1800,
    background="#0F172A",
    palette=PALETTES["modern_dark"],
    tags=["poster", "marketing", "bold", "vertical"],
    elements=[
        TemplateElement(
            element_type="text",
            name="headline",
            x=600, y=240,
            width=1000, height=140,
            properties={
                "text": "BIG IDEA",
                "fontSize": 120,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#F8FAFC",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="subheadline",
            x=600, y=380,
            width=800, height=60,
            properties={
                "text": "Turn attention into action",
                "fontSize": 28,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#CBD5F5",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="image_placeholder",
            x=150, y=520, width=900, height=820,
            properties={"fill": "#1E293B", "rx": 24, "ry": 24}
        ),
        TemplateElement(
            element_type="rectangle",
            name="cta_button",
            x=360, y=1500, width=480, height=80,
            properties={"fill": "#3B82F6", "rx": 12, "ry": 12}
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


TEMPLATE_CATALOG = {
    "business_card_modern": BUSINESS_CARD_MODERN,
    "business_card_elegant": BUSINESS_CARD_ELEGANT,
    "instagram_post_modern": INSTAGRAM_POST_MODERN,
    "social_banner_gradient": SOCIAL_BANNER_GRADIENT,
    "presentation_title_slide": PRESENTATION_TITLE_SLIDE,
    "presentation_content_slide": PRESENTATION_CONTENT_SLIDE,
    "marketing_poster_bold": MARKETING_POSTER_BOLD,
    **FESTIVAL_TEMPLATES,
}
