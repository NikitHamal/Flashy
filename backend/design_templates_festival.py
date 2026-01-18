"""
Festival Template Catalog (Nepal)

Dedicated catalog for Nepal festival templates to keep file sizes modular.
"""

from .design_templates_base import DesignTemplate, TemplateElement, TemplateCategory, PALETTES


FESTIVAL_SARASWATI_PUJA = DesignTemplate(
    id="festival_saraswati_puja",
    name="Saraswati Puja Blessings",
    description="Serene Saraswati Puja wish for Nepal festivals",
    category=TemplateCategory.FESTIVAL,
    width=1080,
    height=1080,
    background="#F8FAFC",
    palette=PALETTES["saraswati_serene"],
    tags=["festival", "nepal", "saraswati", "puja", "instagram", "wish"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="top_band",
            x=0, y=0, width=1080, height=140,
            properties={"fill": "#E0E7FF"}
        ),
        TemplateElement(
            element_type="circle",
            name="halo",
            x=790, y=110, width=220, height=220,
            properties={"fill": "#DBEAFE", "opacity": 0.9, "radius": 110}
        ),
        TemplateElement(
            element_type="rectangle",
            name="logo_mark",
            x=80, y=50, width=90, height=90,
            properties={"fill": "#FFFFFF", "stroke": "#94A3B8", "strokeWidth": 2, "rx": 18, "ry": 18}
        ),
        TemplateElement(
            element_type="text",
            name="logo_text",
            x=125, y=95,
            width=90, height=24,
            properties={
                "text": "LOGO",
                "fontSize": 16,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#64748B",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="brand_name",
            x=190, y=80,
            width=600, height=32,
            properties={
                "text": "Pratigya Dairy",
                "fontSize": 24,
                "fontFamily": "Poppins",
                "fontWeight": "600",
                "fill": "#1E293B"
            }
        ),
        TemplateElement(
            element_type="text",
            name="festival_title",
            x=540, y=420,
            width=900, height=96,
            properties={
                "text": "Happy Saraswati Puja",
                "fontSize": 64,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#1D4ED8",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="festival_message",
            x=540, y=520,
            width=820, height=60,
            properties={
                "text": "May wisdom, knowledge, and creativity bloom in your life",
                "fontSize": 24,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#475569",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="footer_chip",
            x=360, y=680, width=360, height=54,
            properties={"fill": "#1D4ED8", "rx": 28, "ry": 28}
        ),
        TemplateElement(
            element_type="text",
            name="festival_date",
            x=540, y=707,
            width=320, height=24,
            properties={
                "text": "Magh 3 • Nepal",
                "fontSize": 18,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#FFFFFF",
                "textAlign": "center"
            }
        ),
    ]
)

FESTIVAL_DASHAIN = DesignTemplate(
    id="festival_dashain",
    name="Dashain Celebration",
    description="Festive Dashain greeting with bold Nepal palette",
    category=TemplateCategory.FESTIVAL,
    width=1080,
    height=1080,
    background="#FFF7ED",
    palette=PALETTES["nepal_festival_red"],
    tags=["festival", "nepal", "dashain", "tika", "social", "square"],
    elements=[
        TemplateElement(
            element_type="rectangle",
            name="frame",
            x=70, y=70, width=940, height=940,
            properties={"fill": "#FFFFFF", "stroke": "#F59E0B", "strokeWidth": 3, "rx": 40, "ry": 40}
        ),
        TemplateElement(
            element_type="circle",
            name="accent_left",
            x=120, y=760, width=200, height=200,
            properties={"fill": "#FDE68A", "opacity": 0.8, "radius": 100}
        ),
        TemplateElement(
            element_type="circle",
            name="accent_right",
            x=760, y=140, width=220, height=220,
            properties={"fill": "#DBEAFE", "opacity": 0.7, "radius": 110}
        ),
        TemplateElement(
            element_type="rectangle",
            name="logo_mark",
            x=140, y=150, width=86, height=86,
            properties={"fill": "#FFFFFF", "stroke": "#DC2626", "strokeWidth": 2, "rx": 18, "ry": 18}
        ),
        TemplateElement(
            element_type="text",
            name="logo_text",
            x=183, y=193,
            width=80, height=24,
            properties={
                "text": "LOGO",
                "fontSize": 14,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#DC2626",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="brand_name",
            x=240, y=178,
            width=700, height=32,
            properties={
                "text": "Pratigya Dairy",
                "fontSize": 22,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#1F2937"
            }
        ),
        TemplateElement(
            element_type="text",
            name="headline",
            x=540, y=420,
            width=860, height=90,
            properties={
                "text": "Happy Dashain",
                "fontSize": 72,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#DC2626",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="message",
            x=540, y=520,
            width=820, height=60,
            properties={
                "text": "Wishing you prosperity, joy, and family togetherness",
                "fontSize": 24,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#4B5563",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="cta_chip",
            x=360, y=700, width=360, height=52,
            properties={"fill": "#1D4ED8", "rx": 26, "ry": 26}
        ),
        TemplateElement(
            element_type="text",
            name="cta_text",
            x=540, y=726,
            width=320, height=24,
            properties={
                "text": "Warm Wishes from Our Family",
                "fontSize": 16,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#FFFFFF",
                "textAlign": "center"
            }
        ),
    ]
)

FESTIVAL_TIHAR = DesignTemplate(
    id="festival_tihar",
    name="Tihar Lights",
    description="Glowing Tihar celebration post with night-sky palette",
    category=TemplateCategory.FESTIVAL,
    width=1080,
    height=1080,
    background="#0F172A",
    palette=PALETTES["tihar_glow"],
    tags=["festival", "nepal", "tihar", "lights", "instagram", "night"],
    elements=[
        TemplateElement(
            element_type="circle",
            name="glow_left",
            x=60, y=120, width=260, height=260,
            properties={"fill": "#7C3AED", "opacity": 0.35, "radius": 130}
        ),
        TemplateElement(
            element_type="circle",
            name="glow_right",
            x=780, y=650, width=260, height=260,
            properties={"fill": "#F59E0B", "opacity": 0.35, "radius": 130}
        ),
        TemplateElement(
            element_type="rectangle",
            name="logo_mark",
            x=90, y=70, width=80, height=80,
            properties={"fill": "#1E293B", "stroke": "#F59E0B", "strokeWidth": 2, "rx": 18, "ry": 18}
        ),
        TemplateElement(
            element_type="text",
            name="logo_text",
            x=130, y=110,
            width=70, height=24,
            properties={
                "text": "LOGO",
                "fontSize": 14,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#F59E0B",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="brand_name",
            x=190, y=96,
            width=600, height=32,
            properties={
                "text": "Pratigya Dairy",
                "fontSize": 20,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#E2E8F0"
            }
        ),
        TemplateElement(
            element_type="text",
            name="headline",
            x=540, y=420,
            width=820, height=96,
            properties={
                "text": "Happy Tihar",
                "fontSize": 72,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#F8FAFC",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="message",
            x=540, y=520,
            width=820, height=60,
            properties={
                "text": "May the lights bring happiness, harmony, and abundance",
                "fontSize": 24,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#CBD5F5",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="rectangle",
            name="footer_line",
            x=320, y=690, width=440, height=2,
            properties={"fill": "#F59E0B"}
        ),
        TemplateElement(
            element_type="text",
            name="signature",
            x=540, y=720,
            width=600, height=24,
            properties={
                "text": "With love, Pratigya Dairy",
                "fontSize": 18,
                "fontFamily": "Inter",
                "fontWeight": "500",
                "fill": "#FDE68A",
                "textAlign": "center"
            }
        ),
    ]
)

FESTIVAL_HOLI = DesignTemplate(
    id="festival_holi",
    name="Holi Colors",
    description="Bright Holi wishes with vibrant color bursts",
    category=TemplateCategory.FESTIVAL,
    width=1080,
    height=1080,
    background="#FFFFFF",
    palette=PALETTES["creative_pink"],
    tags=["festival", "nepal", "holi", "colors", "instagram", "spring"],
    elements=[
        TemplateElement(
            element_type="circle",
            name="color_burst_1",
            x=80, y=680, width=260, height=260,
            properties={"fill": "#EC4899", "opacity": 0.22, "radius": 130}
        ),
        TemplateElement(
            element_type="circle",
            name="color_burst_2",
            x=760, y=120, width=260, height=260,
            properties={"fill": "#F59E0B", "opacity": 0.22, "radius": 130}
        ),
        TemplateElement(
            element_type="circle",
            name="color_burst_3",
            x=380, y=140, width=220, height=220,
            properties={"fill": "#7C3AED", "opacity": 0.2, "radius": 110}
        ),
        TemplateElement(
            element_type="rectangle",
            name="logo_mark",
            x=90, y=90, width=80, height=80,
            properties={"fill": "#FFFFFF", "stroke": "#EC4899", "strokeWidth": 2, "rx": 18, "ry": 18}
        ),
        TemplateElement(
            element_type="text",
            name="logo_text",
            x=130, y=130,
            width=70, height=24,
            properties={
                "text": "LOGO",
                "fontSize": 14,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#DB2777",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="brand_name",
            x=190, y=116,
            width=600, height=32,
            properties={
                "text": "Pratigya Dairy",
                "fontSize": 20,
                "fontFamily": "Inter",
                "fontWeight": "600",
                "fill": "#701A75"
            }
        ),
        TemplateElement(
            element_type="text",
            name="headline",
            x=540, y=430,
            width=820, height=90,
            properties={
                "text": "Happy Holi",
                "fontSize": 72,
                "fontFamily": "Poppins",
                "fontWeight": "700",
                "fill": "#701A75",
                "textAlign": "center"
            }
        ),
        TemplateElement(
            element_type="text",
            name="message",
            x=540, y=530,
            width=820, height=60,
            properties={
                "text": "Splash your day with colors of joy and unity",
                "fontSize": 24,
                "fontFamily": "Inter",
                "fontWeight": "400",
                "fill": "#A21CAF",
                "textAlign": "center"
            }
        ),
    ]
)


FESTIVAL_TEMPLATES = {
    "festival_saraswati_puja": FESTIVAL_SARASWATI_PUJA,
    "festival_dashain": FESTIVAL_DASHAIN,
    "festival_tihar": FESTIVAL_TIHAR,
    "festival_holi": FESTIVAL_HOLI,
}
