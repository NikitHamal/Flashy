"""Color palette library for design templates."""

from .base import ColorPalette


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
}
