"""Festival greeting templates for Nepal and regional celebrations."""

from .base import DesignTemplate, TemplateCategory, TemplateElement


SARASWATI_PUJA_PRATIGYA = DesignTemplate(
    id="festival_saraswati_puja_pratigya",
    name="Saraswati Puja Greeting",
    description="Warm Saraswati Puja greeting for dairy and sweets brands",
    category=TemplateCategory.SOCIAL_MEDIA,
    width=1080,
    height=1080,
    background="#FFF8E9",
    tags=["festival", "saraswati", "nepal", "greeting", "dairy"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="header_band",
            x=0, y=0, width=1080, height=160,
            properties={"fill": "#FCD34D"}
        ),
        TemplateElement(
            element_type="circle",
            name="sun_glow",
            x=760, y=10, width=260, height=260,
            properties={"fill": "#F59E0B", "opacity": 0.18, "radius": 130}
        ),
        TemplateElement(
            element_type="rectangle",
            name="content_card",
            x=80, y=220, width=920, height=600,
            properties={"fill": "#FFFFFF", "rx": 32, "ry": 32}
        ),
        TemplateElement(
            element_type="text",
            name="title",
            x=120, y=290,
            width=800, height=70,
            properties={
                "text": "Happy Saraswati Puja",
                "fontSize": 58,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#7C2D12"
            }
        ),
        TemplateElement(
            element_type="text",
            name="subtitle",
            x=120, y=370,
            width=760, height=48,
            properties={
                "text": "May wisdom and music bless your day",
                "fontSize": 26,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#92400E"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="accent_divider",
            x=120, y=440, width=120, height=4,
            properties={"fill": "#F59E0B", "rx": 2, "ry": 2}
        ),
        TemplateElement(
            element_type="text",
            name="brand",
            x=120, y=690,
            width=500, height=36,
            properties={
                "text": "Pratigya Dairy",
                "fontSize": 32,
                "fontFamily": "Poppins",
                "fontWeight": "600",
                "fill": "#7C2D12"
            }
        ),
        TemplateElement(
            element_type="text",
            name="tagline",
            x=120, y=738,
            width=500, height=24,
            properties={
                "text": "Pure. Fresh. Blessed.",
                "fontSize": 18,
                "fontFamily": "Inter",
                "fontWeight": "500",
                "fill": "#9A3412"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="logo_holder",
            x=840, y=680, width=160, height=160,
            properties={"fill": "#FDE68A", "rx": 28, "ry": 28}
        ),
        TemplateElement(
            element_type="text",
            name="logo_text",
            x=870, y=760,
            width=120, height=24,
            properties={
                "text": "LOGO",
                "fontSize": 20,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#92400E",
                "textAlign": "center"
            }
        ),
    ]
)


DASHAIN_GREETING_CLASSIC = DesignTemplate(
    id="festival_dashain_classic",
    name="Dashain Blessings",
    description="Classic Dashain greeting with bold red and gold tones",
    category=TemplateCategory.SOCIAL_MEDIA,
    width=1080,
    height=1080,
    background="#FFF1F2",
    tags=["festival", "dashain", "nepal", "greeting"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="top_band",
            x=0, y=0, width=1080, height=160,
            properties={"fill": "#BE123C"}
        ),
        TemplateElement(
            element_type="circle",
            name="gold_glow",
            x=820, y=20, width=220, height=220,
            properties={"fill": "#F59E0B", "opacity": 0.2, "radius": 110}
        ),
        TemplateElement(
            element_type="text",
            name="title",
            x=120, y=260,
            width=800, height=70,
            properties={
                "text": "Happy Dashain",
                "fontSize": 64,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#9F1239"
            }
        ),
        TemplateElement(
            element_type="text",
            name="subtitle",
            x=120, y=340,
            width=760, height=48,
            properties={
                "text": "Wishing you prosperity, joy, and blessings",
                "fontSize": 24,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#BE123C"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="bottom_card",
            x=80, y=540, width=920, height=380,
            properties={"fill": "#FFFFFF", "rx": 28, "ry": 28}
        ),
        TemplateElement(
            element_type="text",
            name="brand",
            x=120, y=620,
            width=500, height=36,
            properties={
                "text": "Pratigya Sweets",
                "fontSize": 30,
                "fontFamily": "Poppins",
                "fontWeight": "600",
                "fill": "#9F1239"
            }
        ),
        TemplateElement(
            element_type="text",
            name="offer",
            x=120, y=680,
            width=600, height=28,
            properties={
                "text": "Festive hampers now available",
                "fontSize": 18,
                "fontFamily": "Inter",
                "fontWeight": "500",
                "fill": "#BE123C"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="logo_holder",
            x=840, y=620, width=160, height=160,
            properties={"fill": "#FDE68A", "rx": 24, "ry": 24}
        ),
        TemplateElement(
            element_type="text",
            name="logo_text",
            x=870, y=700,
            width=120, height=24,
            properties={
                "text": "LOGO",
                "fontSize": 20,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#9F1239",
                "textAlign": "center"
            }
        ),
    ]
)


TIHAR_LIGHTS_GLOW = DesignTemplate(
    id="festival_tihar_glow",
    name="Tihar Lights",
    description="Glowing Tihar greeting with festive lights",
    category=TemplateCategory.SOCIAL_MEDIA,
    width=1080,
    height=1080,
    background="#0F172A",
    tags=["festival", "tihar", "deepawali", "lights"],
    elements=[
        TemplateElement(
            element_type="circle",
            name="light_1",
            x=80, y=100, width=180, height=180,
            properties={"fill": "#FBBF24", "opacity": 0.85, "radius": 90}
        ),
        TemplateElement(
            element_type="circle",
            name="light_2",
            x=860, y=140, width=140, height=140,
            properties={"fill": "#F472B6", "opacity": 0.7, "radius": 70}
        ),
        TemplateElement(
            element_type="circle",
            name="light_3",
            x=740, y=760, width=220, height=220,
            properties={"fill": "#22D3EE", "opacity": 0.6, "radius": 110}
        ),
        TemplateElement(
            element_type="text",
            name="title",
            x=120, y=340,
            width=800, height=70,
            properties={
                "text": "Happy Tihar",
                "fontSize": 66,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#F8FAFC"
            }
        ),
        TemplateElement(
            element_type="text",
            name="subtitle",
            x=120, y=420,
            width=760, height=48,
            properties={
                "text": "May your home glow with light and joy",
                "fontSize": 24,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#CBD5F5"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="brand_card",
            x=120, y=640, width=680, height=200,
            properties={"fill": "#1E293B", "rx": 24, "ry": 24}
        ),
        TemplateElement(
            element_type="text",
            name="brand",
            x=160, y=700,
            width=600, height=32,
            properties={
                "text": "Pratigya Dairy",
                "fontSize": 28,
                "fontFamily": "Poppins",
                "fontWeight": "600",
                "fill": "#FBBF24"
            }
        ),
        TemplateElement(
            element_type="text",
            name="tagline",
            x=160, y=744,
            width=560, height=24,
            properties={
                "text": "Festive flavors for your family",
                "fontSize": 18,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#E2E8F0"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="logo_holder",
            x=840, y=680, width=160, height=160,
            properties={"fill": "#FBBF24", "rx": 24, "ry": 24}
        ),
        TemplateElement(
            element_type="text",
            name="logo_text",
            x=870, y=760,
            width=120, height=24,
            properties={
                "text": "LOGO",
                "fontSize": 20,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#0F172A",
                "textAlign": "center"
            }
        ),
    ]
)


HOLI_COLOR_SPLASH = DesignTemplate(
    id="festival_holi_colors",
    name="Holi Color Splash",
    description="Vibrant Holi greeting with colorful accents",
    category=TemplateCategory.SOCIAL_MEDIA,
    width=1080,
    height=1080,
    background="#FFF7ED",
    tags=["festival", "holi", "colors", "celebration"],
    elements=[
        TemplateElement(
            element_type="circle",
            name="splash_orange",
            x=40, y=90, width=240, height=240,
            properties={"fill": "#FB923C", "opacity": 0.7, "radius": 120}
        ),
        TemplateElement(
            element_type="circle",
            name="splash_pink",
            x=720, y=60, width=280, height=280,
            properties={"fill": "#F472B6", "opacity": 0.65, "radius": 140}
        ),
        TemplateElement(
            element_type="circle",
            name="splash_blue",
            x=780, y=720, width=220, height=220,
            properties={"fill": "#60A5FA", "opacity": 0.7, "radius": 110}
        ),
        TemplateElement(
            element_type="text",
            name="title",
            x=120, y=340,
            width=800, height=70,
            properties={
                "text": "Happy Holi",
                "fontSize": 70,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#7C2D12"
            }
        ),
        TemplateElement(
            element_type="text",
            name="subtitle",
            x=120, y=430,
            width=760, height=48,
            properties={
                "text": "Celebrate with color, joy, and sweetness",
                "fontSize": 24,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#9A3412"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="brand_band",
            x=120, y=650, width=840, height=160,
            properties={"fill": "#FFFFFF", "rx": 24, "ry": 24}
        ),
        TemplateElement(
            element_type="text",
            name="brand",
            x=160, y=700,
            width=600, height=32,
            properties={
                "text": "Pratigya Dairy & Sweets",
                "fontSize": 26,
                "fontFamily": "Poppins",
                "fontWeight": "600",
                "fill": "#7C2D12"
            }
        ),
        TemplateElement(
            element_type="text",
            name="tagline",
            x=160, y=744,
            width=520, height=24,
            properties={
                "text": "Festive hampers available now",
                "fontSize": 18,
                "fontFamily": "Inter",
                "fontWeight": "500",
                "fill": "#9A3412"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="logo_holder",
            x=820, y=685, width=120, height=120,
            properties={"fill": "#FDE68A", "rx": 20, "ry": 20}
        ),
        TemplateElement(
            element_type="text",
            name="logo_text",
            x=845, y=745,
            width=80, height=22,
            properties={
                "text": "LOGO",
                "fontSize": 16,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#9A3412",
                "textAlign": "center"
            }
        ),
    ]
)


TEEJ_JOYOUS = DesignTemplate(
    id="festival_teej_joyous",
    name="Teej Celebration",
    description="Joyful Teej greeting with bright greens and pinks",
    category=TemplateCategory.SOCIAL_MEDIA,
    width=1080,
    height=1080,
    background="#ECFDF5",
    tags=["festival", "teej", "nepal", "celebration"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="left_panel",
            x=0, y=0, width=360, height=1080,
            properties={"fill": "#10B981"}
        ),
        TemplateElement(
            element_type="circle",
            name="accent_circle",
            x=760, y=120, width=220, height=220,
            properties={"fill": "#F472B6", "opacity": 0.5, "radius": 110}
        ),
        TemplateElement(
            element_type="text",
            name="title",
            x=420, y=260,
            width=620, height=70,
            properties={
                "text": "Happy Teej",
                "fontSize": 64,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#047857"
            }
        ),
        TemplateElement(
            element_type="text",
            name="subtitle",
            x=420, y=340,
            width=560, height=48,
            properties={
                "text": "Celebrating joy, devotion, and togetherness",
                "fontSize": 22,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#065F46"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="brand_card",
            x=420, y=640, width=560, height=180,
            properties={"fill": "#FFFFFF", "rx": 24, "ry": 24}
        ),
        TemplateElement(
            element_type="text",
            name="brand",
            x=460, y=700,
            width=420, height=32,
            properties={
                "text": "Pratigya Sweets",
                "fontSize": 26,
                "fontFamily": "Poppins",
                "fontWeight": "600",
                "fill": "#047857"
            }
        ),
        TemplateElement(
            element_type="text",
            name="tagline",
            x=460, y=744,
            width=420, height=24,
            properties={
                "text": "Festival specials now in store",
                "fontSize": 18,
                "fontFamily": "Inter",
                "fontWeight": "500",
                "fill": "#065F46"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="logo_holder",
            x=820, y=680, width=140, height=140,
            properties={"fill": "#FCE7F3", "rx": 22, "ry": 22}
        ),
        TemplateElement(
            element_type="text",
            name="logo_text",
            x=845, y=748,
            width=90, height=22,
            properties={
                "text": "LOGO",
                "fontSize": 16,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#9D174D",
                "textAlign": "center"
            }
        ),
    ]
)
