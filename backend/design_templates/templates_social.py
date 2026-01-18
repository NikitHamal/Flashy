"""Social media templates."""

from .base import DesignTemplate, TemplateCategory, TemplateElement
from .palettes import PALETTES


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
