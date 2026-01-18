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
    FESTIVAL = "festival"
    NEPALI_FESTIVAL = "nepali_festival"
    LOCAL_BUSINESS = "local_business"


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
    
    # ==========================================================================
    # NEPALI FESTIVAL PALETTES
    # ==========================================================================
    
    "saraswoti_puja": ColorPalette(
        name="Saraswoti Puja",
        primary="#FFD700",  # Golden yellow (Basanta Panchami)
        secondary="#FFFFFF",  # White (purity, knowledge)
        accent="#FF6B35",  # Warm orange
        background="#FFFEF0",  # Soft cream
        surface="#FFF8DC",  # Cornsilk
        text="#5D4E37",  # Deep brown
        text_secondary="#8B7355"  # Medium brown
    ),
    "dashain": ColorPalette(
        name="Dashain",
        primary="#DC143C",  # Crimson red (tika)
        secondary="#FFD700",  # Golden (jamara, prosperity)
        accent="#228B22",  # Green (jamara sprouts)
        background="#FFF5F5",  # Light red tint
        surface="#FFFFFF",
        text="#8B0000",  # Dark red
        text_secondary="#A0522D"  # Sienna
    ),
    "tihar": ColorPalette(
        name="Tihar/Deepawali",
        primary="#FF6B00",  # Deep orange (diyo flame)
        secondary="#FFD700",  # Gold (lights, prosperity)
        accent="#E91E63",  # Pink (rangoli)
        background="#1A1A2E",  # Deep night blue
        surface="#16213E",  # Dark surface
        text="#FFD700",  # Gold text
        text_secondary="#FFA500"  # Orange
    ),
    "holi": ColorPalette(
        name="Holi/Fagu Purnima",
        primary="#FF1493",  # Deep pink
        secondary="#00BFFF",  # Deep sky blue
        accent="#FFD700",  # Gold
        background="#FFFFFF",
        surface="#FFF0F5",  # Lavender blush
        text="#4B0082",  # Indigo
        text_secondary="#8B008B"  # Dark magenta
    ),
    "nepali_new_year": ColorPalette(
        name="Nepali New Year",
        primary="#DC143C",  # Traditional red
        secondary="#1E3A8A",  # Deep blue (national color)
        accent="#FFD700",  # Gold
        background="#FEFEFE",
        surface="#F0F4FF",  # Light blue tint
        text="#1E3A8A",  # Deep blue
        text_secondary="#374151"
    ),
    "teej": ColorPalette(
        name="Teej",
        primary="#DC143C",  # Red (sindoor, married women)
        secondary="#FFD700",  # Gold (jewelry)
        accent="#228B22",  # Green (bangles, nature)
        background="#FFF0F5",  # Soft pink
        surface="#FFE4E1",  # Misty rose
        text="#8B0000",  # Dark red
        text_secondary="#A52A2A"  # Brown
    ),
    "chhath": ColorPalette(
        name="Chhath Puja",
        primary="#FF8C00",  # Dark orange (sunrise/sunset)
        secondary="#FFD700",  # Gold (sun)
        accent="#87CEEB",  # Sky blue (water)
        background="#FFF5E6",  # Warm cream
        surface="#FFFFFF",
        text="#8B4513",  # Saddle brown
        text_secondary="#A0522D"
    ),
    "buddha_jayanti": ColorPalette(
        name="Buddha Jayanti",
        primary="#FFD700",  # Gold (enlightenment)
        secondary="#FFFFFF",  # White (purity)
        accent="#FF6347",  # Tomato (monk robes)
        background="#F5F5DC",  # Beige
        surface="#FFFAF0",  # Floral white
        text="#4A4A4A",  # Dark gray
        text_secondary="#696969"
    ),
    "maha_shivaratri": ColorPalette(
        name="Maha Shivaratri",
        primary="#4169E1",  # Royal blue (Shiva)
        secondary="#FFFFFF",  # White (purity)
        accent="#FF6347",  # Orange (rudraksha)
        background="#F0F8FF",  # Alice blue
        surface="#E6E6FA",  # Lavender
        text="#191970",  # Midnight blue
        text_secondary="#4682B4"  # Steel blue
    ),
    "dairy_business": ColorPalette(
        name="Dairy Business",
        primary="#2E8B57",  # Sea green (fresh)
        secondary="#FFFFFF",  # White (milk)
        accent="#FFD700",  # Gold (quality)
        background="#F0FFF0",  # Honeydew
        surface="#FFFFFF",
        text="#1B4332",  # Dark green
        text_secondary="#40916C"
    ),
    "sweets_shop": ColorPalette(
        name="Sweets Shop",
        primary="#FF6B35",  # Warm orange (mithai)
        secondary="#FFD700",  # Gold (premium)
        accent="#DC143C",  # Red (festive)
        background="#FFF8F0",  # Seashell
        surface="#FFFFFF",
        text="#8B4513",  # Saddle brown
        text_secondary="#A0522D"
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
# NEPALI FESTIVAL TEMPLATES
# =============================================================================

SARASWOTI_PUJA_GREETING = DesignTemplate(
    id="saraswoti_puja_greeting",
    name="Saraswoti Puja Greeting",
    description="Elegant Saraswoti Puja/Basanta Panchami greeting with veena and lotus motifs",
    category=TemplateCategory.NEPALI_FESTIVAL,
    width=1080,
    height=1080,
    background="#FFFEF0",
    palette=PALETTES["saraswoti_puja"],
    tags=["saraswoti", "basanta panchami", "nepal", "festival", "education", "greeting"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="background_gradient",
            x=0, y=0, width=1080, height=1080,
            properties={"fill": "#FFFEF0"}
        ),
        TemplateElement(
            element_type="circle",
            name="decorative_circle_top",
            x=540, y=-200,
            width=600, height=600,
            properties={"fill": "#FFD700", "opacity": 0.15, "radius": 300}
        ),
        TemplateElement(
            element_type="circle",
            name="decorative_circle_bottom",
            x=540, y=1100,
            width=500, height=500,
            properties={"fill": "#FFD700", "opacity": 0.1, "radius": 250}
        ),
        TemplateElement(
            element_type="rectangle",
            name="logo_placeholder",
            x=540, y=100,
            width=120, height=120,
            properties={
                "fill": "#FFFFFF",
                "stroke": "#FFD700",
                "strokeWidth": 2,
                "rx": 60, "ry": 60
            }
        ),
        TemplateElement(
            element_type="text",
            name="festival_greeting",
            x=540, y=400,
            width=900, height=100,
            properties={
                "text": "Happy Saraswoti Puja",
                "fontSize": 56,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#5D4E37",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="nepali_greeting",
            x=540, y=480,
            width=800, height=50,
            properties={
                "text": "सरस्वती पूजाको हार्दिक मंगलमय शुभकामना",
                "fontSize": 28,
                "fontFamily": "Noto Sans Devanagari",
                "fontWeight": "500",
                "fill": "#8B7355",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="divider",
            x=440, y=550, width=200, height=3,
            properties={"fill": "#FFD700", "rx": 1, "ry": 1}
        ),
        TemplateElement(
            element_type="text",
            name="blessing_text",
            x=540, y=620,
            width=800, height=80,
            properties={
                "text": "May Goddess Saraswoti bless you\nwith knowledge and wisdom",
                "fontSize": 22,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#8B7355",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="brand_name",
            x=540, y=950,
            width=600, height=36,
            properties={
                "text": "Your Business Name",
                "fontSize": 24,
                "fontFamily": "Poppins",
                "fontWeight": "600",
                "fill": "#5D4E37",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="contact_info",
            x=540, y=1000,
            width=600, height=24,
            properties={
                "text": "Contact: 9800000000 | @yourbusiness",
                "fontSize": 14,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#8B7355",
                "textAlign": "center"
            }
        ),
    ]
)

DASHAIN_GREETING = DesignTemplate(
    id="dashain_greeting",
    name="Dashain Greeting",
    description="Traditional Dashain greeting with tika and jamara elements",
    category=TemplateCategory.NEPALI_FESTIVAL,
    width=1080,
    height=1080,
    background="#FFF5F5",
    palette=PALETTES["dashain"],
    tags=["dashain", "vijaya dashami", "nepal", "festival", "tika", "jamara", "greeting"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="background",
            x=0, y=0, width=1080, height=1080,
            properties={"fill": "#FFF5F5"}
        ),
        TemplateElement(
            element_type="rectangle",
            name="decorative_corner_tl",
            x=0, y=0, width=200, height=200,
            properties={"fill": "#DC143C", "opacity": 0.1}
        ),
        TemplateElement(
            element_type="rectangle",
            name="decorative_corner_br",
            x=880, y=880, width=200, height=200,
            properties={"fill": "#DC143C", "opacity": 0.1}
        ),
        TemplateElement(
            element_type="circle",
            name="tika_symbol",
            x=540, y=280,
            width=100, height=100,
            properties={"fill": "#DC143C", "radius": 50}
        ),
        TemplateElement(
            element_type="rectangle",
            name="logo_placeholder",
            x=540, y=80,
            width=100, height=100,
            properties={
                "fill": "#FFFFFF",
                "stroke": "#DC143C",
                "strokeWidth": 2,
                "rx": 8, "ry": 8
            }
        ),
        TemplateElement(
            element_type="text",
            name="main_greeting",
            x=540, y=420,
            width=900, height=80,
            properties={
                "text": "Happy Dashain",
                "fontSize": 64,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#8B0000",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="nepali_greeting",
            x=540, y=510,
            width=900, height=50,
            properties={
                "text": "विजया दशमीको हार्दिक मंगलमय शुभकामना",
                "fontSize": 28,
                "fontFamily": "Noto Sans Devanagari",
                "fontWeight": "500",
                "fill": "#A0522D",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="jamara_accent_left",
            x=300, y=580, width=4, height=60,
            properties={"fill": "#228B22", "rx": 2, "ry": 2}
        ),
        TemplateElement(
            element_type="rectangle",
            name="jamara_accent_center",
            x=538, y=570, width=4, height=80,
            properties={"fill": "#228B22", "rx": 2, "ry": 2}
        ),
        TemplateElement(
            element_type="rectangle",
            name="jamara_accent_right",
            x=776, y=580, width=4, height=60,
            properties={"fill": "#228B22", "rx": 2, "ry": 2}
        ),
        TemplateElement(
            element_type="text",
            name="blessing",
            x=540, y=700,
            width=800, height=80,
            properties={
                "text": "May this Dashain bring you joy,\nprosperity and good health",
                "fontSize": 22,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#A0522D",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="footer_accent",
            x=0, y=1040, width=1080, height=40,
            properties={"fill": "#DC143C", "opacity": 0.2}
        ),
        TemplateElement(
            element_type="text",
            name="brand_name",
            x=540, y=920,
            width=600, height=36,
            properties={
                "text": "Your Business Name",
                "fontSize": 26,
                "fontFamily": "Poppins",
                "fontWeight": "600",
                "fill": "#8B0000",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="contact",
            x=540, y=970,
            width=600, height=24,
            properties={
                "text": "Contact: 9800000000",
                "fontSize": 14,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#A0522D",
                "textAlign": "center"
            }
        ),
    ]
)

TIHAR_GREETING = DesignTemplate(
    id="tihar_greeting",
    name="Tihar/Deepawali Greeting",
    description="Festive Tihar greeting with diyo lights and rangoli patterns",
    category=TemplateCategory.NEPALI_FESTIVAL,
    width=1080,
    height=1080,
    background="#1A1A2E",
    palette=PALETTES["tihar"],
    tags=["tihar", "deepawali", "diwali", "nepal", "festival", "lights", "diyo", "greeting"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="dark_background",
            x=0, y=0, width=1080, height=1080,
            properties={"fill": "#1A1A2E"}
        ),
        TemplateElement(
            element_type="circle",
            name="glow_1",
            x=200, y=200,
            width=300, height=300,
            properties={"fill": "#FF6B00", "opacity": 0.15, "radius": 150}
        ),
        TemplateElement(
            element_type="circle",
            name="glow_2",
            x=880, y=300,
            width=250, height=250,
            properties={"fill": "#FFD700", "opacity": 0.12, "radius": 125}
        ),
        TemplateElement(
            element_type="circle",
            name="glow_3",
            x=150, y=800,
            width=280, height=280,
            properties={"fill": "#E91E63", "opacity": 0.1, "radius": 140}
        ),
        TemplateElement(
            element_type="circle",
            name="glow_4",
            x=900, y=850,
            width=220, height=220,
            properties={"fill": "#FF6B00", "opacity": 0.12, "radius": 110}
        ),
        TemplateElement(
            element_type="rectangle",
            name="logo_placeholder",
            x=540, y=100,
            width=100, height=100,
            properties={
                "fill": "#16213E",
                "stroke": "#FFD700",
                "strokeWidth": 2,
                "rx": 50, "ry": 50
            }
        ),
        TemplateElement(
            element_type="circle",
            name="diyo_flame",
            x=540, y=320,
            width=60, height=80,
            properties={"fill": "#FF6B00", "radius": 30}
        ),
        TemplateElement(
            element_type="text",
            name="main_greeting",
            x=540, y=460,
            width=900, height=80,
            properties={
                "text": "Happy Tihar",
                "fontSize": 68,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#FFD700",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="nepali_greeting",
            x=540, y=550,
            width=900, height=50,
            properties={
                "text": "तिहारको हार्दिक मंगलमय शुभकामना",
                "fontSize": 28,
                "fontFamily": "Noto Sans Devanagari",
                "fontWeight": "500",
                "fill": "#FFA500",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="rangoli_line_1",
            x=340, y=620, width=400, height=2,
            properties={"fill": "#E91E63", "rx": 1, "ry": 1}
        ),
        TemplateElement(
            element_type="circle",
            name="rangoli_dot_1",
            x=440, y=621, width=8, height=8,
            properties={"fill": "#FFD700", "radius": 4}
        ),
        TemplateElement(
            element_type="circle",
            name="rangoli_dot_2",
            x=540, y=621, width=8, height=8,
            properties={"fill": "#FFD700", "radius": 4}
        ),
        TemplateElement(
            element_type="circle",
            name="rangoli_dot_3",
            x=640, y=621, width=8, height=8,
            properties={"fill": "#FFD700", "radius": 4}
        ),
        TemplateElement(
            element_type="text",
            name="blessing",
            x=540, y=700,
            width=800, height=80,
            properties={
                "text": "May the festival of lights\nbring happiness to your life",
                "fontSize": 22,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#FFA500",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="brand_name",
            x=540, y=920,
            width=600, height=36,
            properties={
                "text": "Your Business Name",
                "fontSize": 26,
                "fontFamily": "Poppins",
                "fontWeight": "600",
                "fill": "#FFD700",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="contact",
            x=540, y=970,
            width=600, height=24,
            properties={
                "text": "Contact: 9800000000 | @yourbusiness",
                "fontSize": 14,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#FFA500",
                "textAlign": "center"
            }
        ),
    ]
)

HOLI_GREETING = DesignTemplate(
    id="holi_greeting",
    name="Holi/Fagu Purnima Greeting",
    description="Colorful Holi greeting with vibrant splash effects",
    category=TemplateCategory.NEPALI_FESTIVAL,
    width=1080,
    height=1080,
    background="#FFFFFF",
    palette=PALETTES["holi"],
    tags=["holi", "fagu purnima", "nepal", "festival", "colors", "greeting"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="background",
            x=0, y=0, width=1080, height=1080,
            properties={"fill": "#FFFFFF"}
        ),
        TemplateElement(
            element_type="circle",
            name="color_splash_pink",
            x=150, y=150,
            width=350, height=350,
            properties={"fill": "#FF1493", "opacity": 0.25, "radius": 175}
        ),
        TemplateElement(
            element_type="circle",
            name="color_splash_blue",
            x=850, y=200,
            width=300, height=300,
            properties={"fill": "#00BFFF", "opacity": 0.25, "radius": 150}
        ),
        TemplateElement(
            element_type="circle",
            name="color_splash_yellow",
            x=500, y=100,
            width=280, height=280,
            properties={"fill": "#FFD700", "opacity": 0.2, "radius": 140}
        ),
        TemplateElement(
            element_type="circle",
            name="color_splash_purple",
            x=100, y=750,
            width=320, height=320,
            properties={"fill": "#8B008B", "opacity": 0.2, "radius": 160}
        ),
        TemplateElement(
            element_type="circle",
            name="color_splash_green",
            x=900, y=800,
            width=280, height=280,
            properties={"fill": "#32CD32", "opacity": 0.2, "radius": 140}
        ),
        TemplateElement(
            element_type="rectangle",
            name="logo_placeholder",
            x=540, y=100,
            width=100, height=100,
            properties={
                "fill": "#FFFFFF",
                "stroke": "#FF1493",
                "strokeWidth": 3,
                "rx": 50, "ry": 50
            }
        ),
        TemplateElement(
            element_type="text",
            name="main_greeting",
            x=540, y=380,
            width=900, height=100,
            properties={
                "text": "Happy Holi",
                "fontSize": 72,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#4B0082",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="nepali_greeting",
            x=540, y=480,
            width=900, height=50,
            properties={
                "text": "फागु पूर्णिमाको हार्दिक शुभकामना",
                "fontSize": 28,
                "fontFamily": "Noto Sans Devanagari",
                "fontWeight": "500",
                "fill": "#8B008B",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="blessing",
            x=540, y=600,
            width=800, height=80,
            properties={
                "text": "May your life be filled with\ncolors of happiness and joy",
                "fontSize": 24,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#4B0082",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="brand_name",
            x=540, y=920,
            width=600, height=36,
            properties={
                "text": "Your Business Name",
                "fontSize": 26,
                "fontFamily": "Poppins",
                "fontWeight": "600",
                "fill": "#4B0082",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="contact",
            x=540, y=970,
            width=600, height=24,
            properties={
                "text": "Contact: 9800000000",
                "fontSize": 14,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#8B008B",
                "textAlign": "center"
            }
        ),
    ]
)

NEPALI_NEW_YEAR_GREETING = DesignTemplate(
    id="nepali_new_year_greeting",
    name="Nepali New Year Greeting",
    description="Elegant Nepali New Year (Naya Barsha) greeting",
    category=TemplateCategory.NEPALI_FESTIVAL,
    width=1080,
    height=1080,
    background="#FEFEFE",
    palette=PALETTES["nepali_new_year"],
    tags=["new year", "naya barsha", "bikram sambat", "nepal", "greeting"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="background",
            x=0, y=0, width=1080, height=1080,
            properties={"fill": "#FEFEFE"}
        ),
        TemplateElement(
            element_type="rectangle",
            name="top_accent",
            x=0, y=0, width=1080, height=8,
            properties={"fill": "#DC143C"}
        ),
        TemplateElement(
            element_type="rectangle",
            name="bottom_accent",
            x=0, y=1072, width=1080, height=8,
            properties={"fill": "#1E3A8A"}
        ),
        TemplateElement(
            element_type="circle",
            name="decorative_circle",
            x=540, y=280,
            width=160, height=160,
            properties={
                "fill": "transparent",
                "stroke": "#DC143C",
                "strokeWidth": 3,
                "radius": 80
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="logo_placeholder",
            x=540, y=80,
            width=100, height=100,
            properties={
                "fill": "#FFFFFF",
                "stroke": "#1E3A8A",
                "strokeWidth": 2,
                "rx": 8, "ry": 8
            }
        ),
        TemplateElement(
            element_type="text",
            name="year_number",
            x=540, y=290,
            width=200, height=60,
            properties={
                "text": "2082",
                "fontSize": 48,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#DC143C",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="main_greeting",
            x=540, y=440,
            width=900, height=80,
            properties={
                "text": "Happy New Year",
                "fontSize": 56,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#1E3A8A",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="nepali_greeting",
            x=540, y=530,
            width=900, height=50,
            properties={
                "text": "नयाँ वर्ष २०८२ को हार्दिक मंगलमय शुभकामना",
                "fontSize": 26,
                "fontFamily": "Noto Sans Devanagari",
                "fontWeight": "500",
                "fill": "#374151",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="divider",
            x=440, y=600, width=200, height=3,
            properties={"fill": "#DC143C", "rx": 1, "ry": 1}
        ),
        TemplateElement(
            element_type="text",
            name="blessing",
            x=540, y=680,
            width=800, height=80,
            properties={
                "text": "Wishing you a prosperous and\njoyful year ahead",
                "fontSize": 22,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#374151",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="brand_name",
            x=540, y=920,
            width=600, height=36,
            properties={
                "text": "Your Business Name",
                "fontSize": 26,
                "fontFamily": "Poppins",
                "fontWeight": "600",
                "fill": "#1E3A8A",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="contact",
            x=540, y=970,
            width=600, height=24,
            properties={
                "text": "Contact: 9800000000",
                "fontSize": 14,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#374151",
                "textAlign": "center"
            }
        ),
    ]
)

TEEJ_GREETING = DesignTemplate(
    id="teej_greeting",
    name="Teej Greeting",
    description="Beautiful Teej festival greeting for women's celebration",
    category=TemplateCategory.NEPALI_FESTIVAL,
    width=1080,
    height=1080,
    background="#FFF0F5",
    palette=PALETTES["teej"],
    tags=["teej", "haritalika", "nepal", "festival", "women", "greeting"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="background",
            x=0, y=0, width=1080, height=1080,
            properties={"fill": "#FFF0F5"}
        ),
        TemplateElement(
            element_type="circle",
            name="decorative_1",
            x=100, y=100,
            width=200, height=200,
            properties={"fill": "#DC143C", "opacity": 0.1, "radius": 100}
        ),
        TemplateElement(
            element_type="circle",
            name="decorative_2",
            x=950, y=150,
            width=180, height=180,
            properties={"fill": "#228B22", "opacity": 0.1, "radius": 90}
        ),
        TemplateElement(
            element_type="circle",
            name="decorative_3",
            x=80, y=880,
            width=220, height=220,
            properties={"fill": "#FFD700", "opacity": 0.15, "radius": 110}
        ),
        TemplateElement(
            element_type="rectangle",
            name="logo_placeholder",
            x=540, y=80,
            width=100, height=100,
            properties={
                "fill": "#FFFFFF",
                "stroke": "#DC143C",
                "strokeWidth": 2,
                "rx": 50, "ry": 50
            }
        ),
        TemplateElement(
            element_type="circle",
            name="bindi_symbol",
            x=540, y=280,
            width=40, height=40,
            properties={"fill": "#DC143C", "radius": 20}
        ),
        TemplateElement(
            element_type="text",
            name="main_greeting",
            x=540, y=400,
            width=900, height=80,
            properties={
                "text": "Happy Teej",
                "fontSize": 64,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#8B0000",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="nepali_greeting",
            x=540, y=490,
            width=900, height=50,
            properties={
                "text": "हरितालिका तीजको हार्दिक शुभकामना",
                "fontSize": 28,
                "fontFamily": "Noto Sans Devanagari",
                "fontWeight": "500",
                "fill": "#A52A2A",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="bangle_line_1",
            x=380, y=560, width=60, height=4,
            properties={"fill": "#228B22", "rx": 2, "ry": 2}
        ),
        TemplateElement(
            element_type="rectangle",
            name="bangle_line_2",
            x=510, y=560, width=60, height=4,
            properties={"fill": "#DC143C", "rx": 2, "ry": 2}
        ),
        TemplateElement(
            element_type="rectangle",
            name="bangle_line_3",
            x=640, y=560, width=60, height=4,
            properties={"fill": "#FFD700", "rx": 2, "ry": 2}
        ),
        TemplateElement(
            element_type="text",
            name="blessing",
            x=540, y=650,
            width=800, height=80,
            properties={
                "text": "May this auspicious festival bring\nhappiness and prosperity",
                "fontSize": 22,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#A52A2A",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="brand_name",
            x=540, y=920,
            width=600, height=36,
            properties={
                "text": "Your Business Name",
                "fontSize": 26,
                "fontFamily": "Poppins",
                "fontWeight": "600",
                "fill": "#8B0000",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="contact",
            x=540, y=970,
            width=600, height=24,
            properties={
                "text": "Contact: 9800000000",
                "fontSize": 14,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#A52A2A",
                "textAlign": "center"
            }
        ),
    ]
)

CHHATH_PUJA_GREETING = DesignTemplate(
    id="chhath_puja_greeting",
    name="Chhath Puja Greeting",
    description="Chhath Puja greeting with sunrise and water elements",
    category=TemplateCategory.NEPALI_FESTIVAL,
    width=1080,
    height=1080,
    background="#FFF5E6",
    palette=PALETTES["chhath"],
    tags=["chhath", "surya", "nepal", "festival", "sun", "greeting"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="background",
            x=0, y=0, width=1080, height=1080,
            properties={"fill": "#FFF5E6"}
        ),
        TemplateElement(
            element_type="circle",
            name="sun_glow",
            x=540, y=200,
            width=400, height=400,
            properties={"fill": "#FFD700", "opacity": 0.2, "radius": 200}
        ),
        TemplateElement(
            element_type="circle",
            name="sun_core",
            x=540, y=200,
            width=150, height=150,
            properties={"fill": "#FF8C00", "opacity": 0.8, "radius": 75}
        ),
        TemplateElement(
            element_type="rectangle",
            name="water_reflection",
            x=0, y=850, width=1080, height=230,
            properties={"fill": "#87CEEB", "opacity": 0.3}
        ),
        TemplateElement(
            element_type="rectangle",
            name="logo_placeholder",
            x=540, y=60,
            width=80, height=80,
            properties={
                "fill": "#FFFFFF",
                "stroke": "#FF8C00",
                "strokeWidth": 2,
                "rx": 40, "ry": 40
            }
        ),
        TemplateElement(
            element_type="text",
            name="main_greeting",
            x=540, y=420,
            width=900, height=80,
            properties={
                "text": "Happy Chhath Puja",
                "fontSize": 56,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#8B4513",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="nepali_greeting",
            x=540, y=510,
            width=900, height=50,
            properties={
                "text": "छठ पूजाको हार्दिक शुभकामना",
                "fontSize": 28,
                "fontFamily": "Noto Sans Devanagari",
                "fontWeight": "500",
                "fill": "#A0522D",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="blessing",
            x=540, y=620,
            width=800, height=80,
            properties={
                "text": "May the Sun God bless you with\nabundant health and prosperity",
                "fontSize": 22,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#A0522D",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="brand_name",
            x=540, y=760,
            width=600, height=36,
            properties={
                "text": "Your Business Name",
                "fontSize": 26,
                "fontFamily": "Poppins",
                "fontWeight": "600",
                "fill": "#8B4513",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="contact",
            x=540, y=810,
            width=600, height=24,
            properties={
                "text": "Contact: 9800000000",
                "fontSize": 14,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#A0522D",
                "textAlign": "center"
            }
        ),
    ]
)

BUDDHA_JAYANTI_GREETING = DesignTemplate(
    id="buddha_jayanti_greeting",
    name="Buddha Jayanti Greeting",
    description="Peaceful Buddha Jayanti greeting with lotus and enlightenment theme",
    category=TemplateCategory.NEPALI_FESTIVAL,
    width=1080,
    height=1080,
    background="#F5F5DC",
    palette=PALETTES["buddha_jayanti"],
    tags=["buddha", "jayanti", "nepal", "festival", "peace", "greeting"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="background",
            x=0, y=0, width=1080, height=1080,
            properties={"fill": "#F5F5DC"}
        ),
        TemplateElement(
            element_type="circle",
            name="enlightenment_glow",
            x=540, y=280,
            width=300, height=300,
            properties={"fill": "#FFD700", "opacity": 0.2, "radius": 150}
        ),
        TemplateElement(
            element_type="circle",
            name="lotus_base",
            x=540, y=340,
            width=120, height=60,
            properties={"fill": "#FFD700", "opacity": 0.5, "radius": 60}
        ),
        TemplateElement(
            element_type="rectangle",
            name="logo_placeholder",
            x=540, y=80,
            width=80, height=80,
            properties={
                "fill": "#FFFAF0",
                "stroke": "#FFD700",
                "strokeWidth": 2,
                "rx": 40, "ry": 40
            }
        ),
        TemplateElement(
            element_type="text",
            name="main_greeting",
            x=540, y=450,
            width=900, height=80,
            properties={
                "text": "Happy Buddha Jayanti",
                "fontSize": 52,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#4A4A4A",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="nepali_greeting",
            x=540, y=540,
            width=900, height=50,
            properties={
                "text": "बुद्ध जयन्तीको हार्दिक शुभकामना",
                "fontSize": 28,
                "fontFamily": "Noto Sans Devanagari",
                "fontWeight": "500",
                "fill": "#696969",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="quote",
            x=540, y=640,
            width=800, height=100,
            properties={
                "text": "\"Peace comes from within.\nDo not seek it without.\"",
                "fontSize": 20,
                "fontFamily": "Inter",
                "fontStyle": "italic",
                "fontWeight": "400",
                "fill": "#696969",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="brand_name",
            x=540, y=920,
            width=600, height=36,
            properties={
                "text": "Your Business Name",
                "fontSize": 26,
                "fontFamily": "Poppins",
                "fontWeight": "600",
                "fill": "#4A4A4A",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="contact",
            x=540, y=970,
            width=600, height=24,
            properties={
                "text": "Contact: 9800000000",
                "fontSize": 14,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#696969",
                "textAlign": "center"
            }
        ),
    ]
)


# =============================================================================
# LOCAL BUSINESS TEMPLATES (NEPAL)
# =============================================================================

DAIRY_BUSINESS_PROMO = DesignTemplate(
    id="dairy_business_promo",
    name="Dairy Business Promotion",
    description="Fresh and clean promotion template for dairy shops",
    category=TemplateCategory.LOCAL_BUSINESS,
    width=1080,
    height=1080,
    background="#F0FFF0",
    palette=PALETTES["dairy_business"],
    tags=["dairy", "milk", "nepal", "business", "local", "promo"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="background",
            x=0, y=0, width=1080, height=1080,
            properties={"fill": "#F0FFF0"}
        ),
        TemplateElement(
            element_type="circle",
            name="milk_drop_1",
            x=150, y=200,
            width=180, height=180,
            properties={"fill": "#FFFFFF", "opacity": 0.8, "radius": 90}
        ),
        TemplateElement(
            element_type="circle",
            name="milk_drop_2",
            x=900, y=300,
            width=140, height=140,
            properties={"fill": "#FFFFFF", "opacity": 0.7, "radius": 70}
        ),
        TemplateElement(
            element_type="rectangle",
            name="header_bar",
            x=0, y=0, width=1080, height=10,
            properties={"fill": "#2E8B57"}
        ),
        TemplateElement(
            element_type="rectangle",
            name="logo_placeholder",
            x=540, y=100,
            width=140, height=140,
            properties={
                "fill": "#FFFFFF",
                "stroke": "#2E8B57",
                "strokeWidth": 3,
                "rx": 70, "ry": 70
            }
        ),
        TemplateElement(
            element_type="text",
            name="business_name",
            x=540, y=320,
            width=800, height=60,
            properties={
                "text": "Fresh Dairy Shop",
                "fontSize": 48,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#1B4332",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="tagline",
            x=540, y=400,
            width=700, height=36,
            properties={
                "text": "Pure & Fresh - Direct from Farm",
                "fontSize": 24,
                "fontFamily": "Inter",
                "fontWeight": "500",
                "fill": "#40916C",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="offer_box",
            x=240, y=480, width=600, height=200,
            properties={
                "fill": "#FFFFFF",
                "stroke": "#2E8B57",
                "strokeWidth": 2,
                "rx": 12, "ry": 12
            }
        ),
        TemplateElement(
            element_type="text",
            name="offer_title",
            x=540, y=530,
            width=550, height=36,
            properties={
                "text": "TODAY'S SPECIAL",
                "fontSize": 18,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#2E8B57",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="offer_details",
            x=540, y=600,
            width=550, height=60,
            properties={
                "text": "Fresh Milk - Rs. 80/L\nCurd - Rs. 100/kg",
                "fontSize": 28,
                "fontFamily": "Poppins",
                "fontWeight": "600",
                "fill": "#1B4332",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="cta_button",
            x=390, y=750, width=300, height=60,
            properties={"fill": "#2E8B57", "rx": 30, "ry": 30}
        ),
        TemplateElement(
            element_type="text",
            name="cta_text",
            x=540, y=790,
            width=280, height=28,
            properties={
                "text": "Order Now",
                "fontSize": 20,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#FFFFFF",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="contact",
            x=540, y=900,
            width=600, height=60,
            properties={
                "text": "Contact: 9800000000\nLocation: Your Address Here",
                "fontSize": 16,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#40916C",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="footer_bar",
            x=0, y=1000, width=1080, height=80,
            properties={"fill": "#2E8B57", "opacity": 0.1}
        ),
    ]
)

SWEETS_SHOP_PROMO = DesignTemplate(
    id="sweets_shop_promo",
    name="Sweets Shop Promotion",
    description="Warm and inviting promotion template for sweet shops",
    category=TemplateCategory.LOCAL_BUSINESS,
    width=1080,
    height=1080,
    background="#FFF8F0",
    palette=PALETTES["sweets_shop"],
    tags=["sweets", "mithai", "nepal", "business", "local", "promo"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="background",
            x=0, y=0, width=1080, height=1080,
            properties={"fill": "#FFF8F0"}
        ),
        TemplateElement(
            element_type="circle",
            name="warm_glow_1",
            x=100, y=150,
            width=250, height=250,
            properties={"fill": "#FF6B35", "opacity": 0.1, "radius": 125}
        ),
        TemplateElement(
            element_type="circle",
            name="warm_glow_2",
            x=950, y=200,
            width=200, height=200,
            properties={"fill": "#FFD700", "opacity": 0.15, "radius": 100}
        ),
        TemplateElement(
            element_type="rectangle",
            name="decorative_border",
            x=40, y=40, width=1000, height=1000,
            properties={
                "fill": "transparent",
                "stroke": "#FF6B35",
                "strokeWidth": 2,
                "rx": 0, "ry": 0
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="logo_placeholder",
            x=540, y=100,
            width=120, height=120,
            properties={
                "fill": "#FFFFFF",
                "stroke": "#FF6B35",
                "strokeWidth": 3,
                "rx": 60, "ry": 60
            }
        ),
        TemplateElement(
            element_type="text",
            name="business_name",
            x=540, y=300,
            width=800, height=60,
            properties={
                "text": "Nepali Sweets",
                "fontSize": 52,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#8B4513",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="tagline",
            x=540, y=380,
            width=700, height=36,
            properties={
                "text": "Traditional Taste, Premium Quality",
                "fontSize": 22,
                "fontFamily": "Inter",
                "fontWeight": "500",
                "fill": "#A0522D",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="menu_box",
            x=190, y=450, width=700, height=280,
            properties={
                "fill": "#FFFFFF",
                "rx": 16, "ry": 16
            }
        ),
        TemplateElement(
            element_type="text",
            name="menu_title",
            x=540, y=490,
            width=650, height=30,
            properties={
                "text": "FESTIVAL SPECIAL MENU",
                "fontSize": 18,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#FF6B35",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="menu_items",
            x=540, y=600,
            width=650, height=120,
            properties={
                "text": "Laddu - Rs. 600/kg\nBarfi - Rs. 700/kg\nGulab Jamun - Rs. 500/kg",
                "fontSize": 24,
                "fontFamily": "Poppins",
                "fontWeight": "500",
                "fill": "#8B4513",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="order_button",
            x=390, y=780, width=300, height=60,
            properties={"fill": "#FF6B35", "rx": 30, "ry": 30}
        ),
        TemplateElement(
            element_type="text",
            name="order_text",
            x=540, y=820,
            width=280, height=28,
            properties={
                "text": "Order for Festivals",
                "fontSize": 18,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#FFFFFF",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="contact_info",
            x=540, y=920,
            width=600, height=60,
            properties={
                "text": "Call: 9800000000 | Free Delivery",
                "fontSize": 18,
                "fontFamily": "Inter",
                "fontWeight": "500",
                "fill": "#A0522D",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="location",
            x=540, y=970,
            width=600, height=24,
            properties={
                "text": "Location: Your Address, City",
                "fontSize": 14,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#A0522D",
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
    
    # Nepali Festivals
    "saraswoti_puja_greeting": SARASWOTI_PUJA_GREETING,
    "dashain_greeting": DASHAIN_GREETING,
    "tihar_greeting": TIHAR_GREETING,
    "holi_greeting": HOLI_GREETING,
    "nepali_new_year_greeting": NEPALI_NEW_YEAR_GREETING,
    "teej_greeting": TEEJ_GREETING,
    "chhath_puja_greeting": CHHATH_PUJA_GREETING,
    "buddha_jayanti_greeting": BUDDHA_JAYANTI_GREETING,
    
    # Local Business
    "dairy_business_promo": DAIRY_BUSINESS_PROMO,
    "sweets_shop_promo": SWEETS_SHOP_PROMO,
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
