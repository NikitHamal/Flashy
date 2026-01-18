"""
Comprehensive Canvas Presets System

This module provides an extensive collection of canvas size presets for all major
social media platforms, print formats, and custom design needs. Each preset includes
metadata for optimal use cases, safe zones, and platform-specific requirements.

Categories:
- Social Media: Instagram, Facebook, Twitter/X, LinkedIn, TikTok, YouTube, Pinterest, Snapchat
- Business: Cards, letterheads, invoices, presentations
- Print: Posters, flyers, banners, brochures
- Web: Banners, headers, thumbnails, ads
- Custom: User-defined sizes with aspect ratio helpers
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


class PresetCategory(Enum):
    """Categories for canvas presets."""
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    PINTEREST = "pinterest"
    SNAPCHAT = "snapchat"
    WHATSAPP = "whatsapp"
    BUSINESS = "business"
    PRESENTATION = "presentation"
    PRINT = "print"
    WEB = "web"
    CUSTOM = "custom"


class AspectRatio(Enum):
    """Common aspect ratios."""
    SQUARE = "1:1"
    PORTRAIT_4_5 = "4:5"
    PORTRAIT_9_16 = "9:16"
    LANDSCAPE_16_9 = "16:9"
    LANDSCAPE_2_1 = "2:1"
    LANDSCAPE_3_1 = "3:1"
    GOLDEN_RATIO = "1.618:1"
    CUSTOM = "custom"


@dataclass
class SafeZone:
    """Safe zone margins for platform-specific content areas."""
    top: int = 0
    right: int = 0
    bottom: int = 0
    left: int = 0
    
    def to_dict(self) -> Dict[str, int]:
        return {
            "top": self.top,
            "right": self.right,
            "bottom": self.bottom,
            "left": self.left
        }


@dataclass
class CanvasPreset:
    """Complete canvas preset definition with metadata."""
    id: str
    name: str
    description: str
    category: PresetCategory
    width: int
    height: int
    aspect_ratio: AspectRatio
    safe_zone: Optional[SafeZone] = None
    recommended_dpi: int = 72
    max_file_size_mb: Optional[float] = None
    supported_formats: List[str] = field(default_factory=lambda: ["PNG", "JPG"])
    icon: str = "image"
    popular: bool = False
    tags: List[str] = field(default_factory=list)
    
    @property
    def aspect_ratio_decimal(self) -> float:
        return self.width / self.height
    
    @property
    def orientation(self) -> str:
        if self.width > self.height:
            return "landscape"
        elif self.width < self.height:
            return "portrait"
        return "square"
    
    @property
    def pixel_count(self) -> int:
        return self.width * self.height
    
    def get_safe_bounds(self) -> Dict[str, int]:
        """Get the safe content area bounds."""
        sz = self.safe_zone or SafeZone()
        return {
            "x": sz.left,
            "y": sz.top,
            "width": self.width - sz.left - sz.right,
            "height": self.height - sz.top - sz.bottom
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "width": self.width,
            "height": self.height,
            "aspectRatio": self.aspect_ratio.value,
            "aspectRatioDecimal": round(self.aspect_ratio_decimal, 3),
            "orientation": self.orientation,
            "safeZone": self.safe_zone.to_dict() if self.safe_zone else None,
            "safeBounds": self.get_safe_bounds(),
            "recommendedDpi": self.recommended_dpi,
            "maxFileSizeMb": self.max_file_size_mb,
            "supportedFormats": self.supported_formats,
            "icon": self.icon,
            "popular": self.popular,
            "tags": self.tags
        }
    
    def to_summary(self) -> Dict[str, Any]:
        """Get compact summary for UI listing."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "width": self.width,
            "height": self.height,
            "aspectRatio": self.aspect_ratio.value,
            "orientation": self.orientation,
            "icon": self.icon,
            "popular": self.popular
        }


# =============================================================================
# INSTAGRAM PRESETS
# =============================================================================

INSTAGRAM_POST_SQUARE = CanvasPreset(
    id="instagram_post_square",
    name="Instagram Post (Square)",
    description="Standard square Instagram feed post - optimal engagement format",
    category=PresetCategory.INSTAGRAM,
    width=1080,
    height=1080,
    aspect_ratio=AspectRatio.SQUARE,
    safe_zone=SafeZone(top=60, right=60, bottom=60, left=60),
    max_file_size_mb=30,
    icon="instagram",
    popular=True,
    tags=["instagram", "feed", "square", "post"]
)

INSTAGRAM_POST_PORTRAIT = CanvasPreset(
    id="instagram_post_portrait",
    name="Instagram Post (Portrait)",
    description="Vertical Instagram feed post - takes more screen space",
    category=PresetCategory.INSTAGRAM,
    width=1080,
    height=1350,
    aspect_ratio=AspectRatio.PORTRAIT_4_5,
    safe_zone=SafeZone(top=60, right=60, bottom=60, left=60),
    max_file_size_mb=30,
    icon="instagram",
    popular=True,
    tags=["instagram", "feed", "portrait", "vertical"]
)

INSTAGRAM_POST_LANDSCAPE = CanvasPreset(
    id="instagram_post_landscape",
    name="Instagram Post (Landscape)",
    description="Horizontal Instagram feed post - 1.91:1 ratio",
    category=PresetCategory.INSTAGRAM,
    width=1080,
    height=566,
    aspect_ratio=AspectRatio.CUSTOM,
    safe_zone=SafeZone(top=40, right=60, bottom=40, left=60),
    max_file_size_mb=30,
    icon="instagram",
    tags=["instagram", "feed", "landscape", "horizontal"]
)

INSTAGRAM_STORY = CanvasPreset(
    id="instagram_story",
    name="Instagram Story/Reel",
    description="Full-screen vertical format for Stories and Reels",
    category=PresetCategory.INSTAGRAM,
    width=1080,
    height=1920,
    aspect_ratio=AspectRatio.PORTRAIT_9_16,
    safe_zone=SafeZone(top=200, right=80, bottom=280, left=80),
    max_file_size_mb=30,
    icon="instagram",
    popular=True,
    tags=["instagram", "story", "reels", "vertical", "fullscreen"]
)

INSTAGRAM_REEL_COVER = CanvasPreset(
    id="instagram_reel_cover",
    name="Instagram Reel Cover",
    description="Cover image for Instagram Reels",
    category=PresetCategory.INSTAGRAM,
    width=1080,
    height=1920,
    aspect_ratio=AspectRatio.PORTRAIT_9_16,
    safe_zone=SafeZone(top=120, right=80, bottom=350, left=80),
    icon="instagram",
    tags=["instagram", "reels", "cover", "thumbnail"]
)

INSTAGRAM_PROFILE_PHOTO = CanvasPreset(
    id="instagram_profile_photo",
    name="Instagram Profile Photo",
    description="Circular profile picture - displays at 110x110px",
    category=PresetCategory.INSTAGRAM,
    width=320,
    height=320,
    aspect_ratio=AspectRatio.SQUARE,
    icon="instagram",
    tags=["instagram", "profile", "avatar", "picture"]
)

INSTAGRAM_CAROUSEL = CanvasPreset(
    id="instagram_carousel",
    name="Instagram Carousel Slide",
    description="Square slide for carousel posts - up to 10 slides",
    category=PresetCategory.INSTAGRAM,
    width=1080,
    height=1080,
    aspect_ratio=AspectRatio.SQUARE,
    safe_zone=SafeZone(top=60, right=100, bottom=60, left=100),
    icon="instagram",
    popular=True,
    tags=["instagram", "carousel", "slideshow", "multi"]
)

INSTAGRAM_AD_SQUARE = CanvasPreset(
    id="instagram_ad_square",
    name="Instagram Ad (Square)",
    description="Square format for Instagram feed ads",
    category=PresetCategory.INSTAGRAM,
    width=1080,
    height=1080,
    aspect_ratio=AspectRatio.SQUARE,
    safe_zone=SafeZone(top=80, right=80, bottom=180, left=80),
    icon="instagram",
    tags=["instagram", "ad", "advertisement", "sponsored"]
)


# =============================================================================
# FACEBOOK PRESETS
# =============================================================================

FACEBOOK_POST = CanvasPreset(
    id="facebook_post",
    name="Facebook Post",
    description="Standard Facebook feed post image",
    category=PresetCategory.FACEBOOK,
    width=1200,
    height=630,
    aspect_ratio=AspectRatio.CUSTOM,
    safe_zone=SafeZone(top=40, right=60, bottom=40, left=60),
    icon="facebook",
    popular=True,
    tags=["facebook", "post", "feed", "share"]
)

FACEBOOK_POST_SQUARE = CanvasPreset(
    id="facebook_post_square",
    name="Facebook Post (Square)",
    description="Square Facebook post - good for mobile viewing",
    category=PresetCategory.FACEBOOK,
    width=1080,
    height=1080,
    aspect_ratio=AspectRatio.SQUARE,
    icon="facebook",
    tags=["facebook", "post", "square", "mobile"]
)

FACEBOOK_COVER = CanvasPreset(
    id="facebook_cover",
    name="Facebook Cover Photo",
    description="Profile cover photo - displays differently on desktop/mobile",
    category=PresetCategory.FACEBOOK,
    width=820,
    height=312,
    aspect_ratio=AspectRatio.CUSTOM,
    safe_zone=SafeZone(top=20, right=100, bottom=20, left=200),
    icon="facebook",
    popular=True,
    tags=["facebook", "cover", "banner", "profile"]
)

FACEBOOK_COVER_MOBILE_SAFE = CanvasPreset(
    id="facebook_cover_mobile",
    name="Facebook Cover (Mobile-Safe)",
    description="Cover photo optimized for both desktop and mobile viewing",
    category=PresetCategory.FACEBOOK,
    width=851,
    height=315,
    aspect_ratio=AspectRatio.CUSTOM,
    safe_zone=SafeZone(top=75, right=134, bottom=75, left=134),
    icon="facebook",
    tags=["facebook", "cover", "mobile", "responsive"]
)

FACEBOOK_EVENT_COVER = CanvasPreset(
    id="facebook_event_cover",
    name="Facebook Event Cover",
    description="Cover image for Facebook events",
    category=PresetCategory.FACEBOOK,
    width=1920,
    height=1005,
    aspect_ratio=AspectRatio.CUSTOM,
    safe_zone=SafeZone(top=60, right=100, bottom=150, left=100),
    icon="facebook",
    tags=["facebook", "event", "cover", "banner"]
)

FACEBOOK_GROUP_COVER = CanvasPreset(
    id="facebook_group_cover",
    name="Facebook Group Cover",
    description="Cover photo for Facebook groups",
    category=PresetCategory.FACEBOOK,
    width=1640,
    height=856,
    aspect_ratio=AspectRatio.CUSTOM,
    icon="facebook",
    tags=["facebook", "group", "cover", "community"]
)

FACEBOOK_AD = CanvasPreset(
    id="facebook_ad",
    name="Facebook Ad",
    description="Standard Facebook advertisement image",
    category=PresetCategory.FACEBOOK,
    width=1200,
    height=628,
    aspect_ratio=AspectRatio.CUSTOM,
    safe_zone=SafeZone(top=50, right=80, bottom=100, left=80),
    icon="facebook",
    tags=["facebook", "ad", "advertisement", "sponsored"]
)

FACEBOOK_STORY = CanvasPreset(
    id="facebook_story",
    name="Facebook Story",
    description="Full-screen vertical format for Facebook Stories",
    category=PresetCategory.FACEBOOK,
    width=1080,
    height=1920,
    aspect_ratio=AspectRatio.PORTRAIT_9_16,
    safe_zone=SafeZone(top=180, right=80, bottom=250, left=80),
    icon="facebook",
    tags=["facebook", "story", "vertical", "fullscreen"]
)

FACEBOOK_PROFILE = CanvasPreset(
    id="facebook_profile",
    name="Facebook Profile Picture",
    description="Profile photo - displays at 170x170px on desktop",
    category=PresetCategory.FACEBOOK,
    width=320,
    height=320,
    aspect_ratio=AspectRatio.SQUARE,
    icon="facebook",
    tags=["facebook", "profile", "avatar", "picture"]
)


# =============================================================================
# TWITTER/X PRESETS
# =============================================================================

TWITTER_POST = CanvasPreset(
    id="twitter_post",
    name="Twitter/X Post",
    description="Standard Twitter post image - 16:9 recommended",
    category=PresetCategory.TWITTER,
    width=1200,
    height=675,
    aspect_ratio=AspectRatio.LANDSCAPE_16_9,
    safe_zone=SafeZone(top=40, right=60, bottom=40, left=60),
    icon="twitter",
    popular=True,
    tags=["twitter", "x", "post", "tweet"]
)

TWITTER_POST_SQUARE = CanvasPreset(
    id="twitter_post_square",
    name="Twitter/X Post (Square)",
    description="Square format for Twitter posts",
    category=PresetCategory.TWITTER,
    width=1080,
    height=1080,
    aspect_ratio=AspectRatio.SQUARE,
    icon="twitter",
    tags=["twitter", "x", "post", "square"]
)

TWITTER_HEADER = CanvasPreset(
    id="twitter_header",
    name="Twitter/X Header",
    description="Profile header/banner image",
    category=PresetCategory.TWITTER,
    width=1500,
    height=500,
    aspect_ratio=AspectRatio.LANDSCAPE_3_1,
    safe_zone=SafeZone(top=50, right=100, bottom=80, left=200),
    icon="twitter",
    popular=True,
    tags=["twitter", "x", "header", "banner", "profile"]
)

TWITTER_PROFILE = CanvasPreset(
    id="twitter_profile",
    name="Twitter/X Profile Picture",
    description="Circular profile picture",
    category=PresetCategory.TWITTER,
    width=400,
    height=400,
    aspect_ratio=AspectRatio.SQUARE,
    icon="twitter",
    tags=["twitter", "x", "profile", "avatar"]
)

TWITTER_CARD = CanvasPreset(
    id="twitter_card",
    name="Twitter/X Card Image",
    description="Summary card with large image",
    category=PresetCategory.TWITTER,
    width=1200,
    height=628,
    aspect_ratio=AspectRatio.CUSTOM,
    icon="twitter",
    tags=["twitter", "x", "card", "link", "preview"]
)


# =============================================================================
# LINKEDIN PRESETS
# =============================================================================

LINKEDIN_POST = CanvasPreset(
    id="linkedin_post",
    name="LinkedIn Post",
    description="Standard LinkedIn feed post image",
    category=PresetCategory.LINKEDIN,
    width=1200,
    height=628,
    aspect_ratio=AspectRatio.CUSTOM,
    safe_zone=SafeZone(top=40, right=60, bottom=40, left=60),
    icon="linkedin",
    popular=True,
    tags=["linkedin", "post", "feed", "professional"]
)

LINKEDIN_POST_SQUARE = CanvasPreset(
    id="linkedin_post_square",
    name="LinkedIn Post (Square)",
    description="Square format for LinkedIn posts",
    category=PresetCategory.LINKEDIN,
    width=1080,
    height=1080,
    aspect_ratio=AspectRatio.SQUARE,
    icon="linkedin",
    tags=["linkedin", "post", "square"]
)

LINKEDIN_BANNER = CanvasPreset(
    id="linkedin_banner",
    name="LinkedIn Profile Banner",
    description="Personal profile background banner",
    category=PresetCategory.LINKEDIN,
    width=1584,
    height=396,
    aspect_ratio=AspectRatio.CUSTOM,
    safe_zone=SafeZone(top=30, right=200, bottom=30, left=350),
    icon="linkedin",
    popular=True,
    tags=["linkedin", "banner", "profile", "background"]
)

LINKEDIN_COMPANY_COVER = CanvasPreset(
    id="linkedin_company_cover",
    name="LinkedIn Company Cover",
    description="Company page cover image",
    category=PresetCategory.LINKEDIN,
    width=1128,
    height=191,
    aspect_ratio=AspectRatio.CUSTOM,
    icon="linkedin",
    tags=["linkedin", "company", "cover", "business"]
)

LINKEDIN_PROFILE = CanvasPreset(
    id="linkedin_profile",
    name="LinkedIn Profile Picture",
    description="Professional profile photo",
    category=PresetCategory.LINKEDIN,
    width=400,
    height=400,
    aspect_ratio=AspectRatio.SQUARE,
    icon="linkedin",
    tags=["linkedin", "profile", "professional", "headshot"]
)

LINKEDIN_ARTICLE_COVER = CanvasPreset(
    id="linkedin_article_cover",
    name="LinkedIn Article Cover",
    description="Cover image for LinkedIn articles",
    category=PresetCategory.LINKEDIN,
    width=1280,
    height=720,
    aspect_ratio=AspectRatio.LANDSCAPE_16_9,
    icon="linkedin",
    tags=["linkedin", "article", "blog", "cover"]
)


# =============================================================================
# YOUTUBE PRESETS
# =============================================================================

YOUTUBE_THUMBNAIL = CanvasPreset(
    id="youtube_thumbnail",
    name="YouTube Thumbnail",
    description="Video thumbnail - crucial for click-through rates",
    category=PresetCategory.YOUTUBE,
    width=1280,
    height=720,
    aspect_ratio=AspectRatio.LANDSCAPE_16_9,
    safe_zone=SafeZone(top=40, right=120, bottom=80, left=40),
    recommended_dpi=72,
    max_file_size_mb=2,
    supported_formats=["PNG", "JPG", "GIF", "BMP"],
    icon="youtube",
    popular=True,
    tags=["youtube", "thumbnail", "video", "preview"]
)

YOUTUBE_CHANNEL_ART = CanvasPreset(
    id="youtube_channel_art",
    name="YouTube Channel Banner",
    description="Channel banner - different crops on different devices",
    category=PresetCategory.YOUTUBE,
    width=2560,
    height=1440,
    aspect_ratio=AspectRatio.CUSTOM,
    safe_zone=SafeZone(top=520, right=507, bottom=520, left=507),
    icon="youtube",
    popular=True,
    tags=["youtube", "channel", "banner", "art", "header"]
)

YOUTUBE_CHANNEL_ICON = CanvasPreset(
    id="youtube_channel_icon",
    name="YouTube Channel Icon",
    description="Channel profile picture - displays at 98x98px",
    category=PresetCategory.YOUTUBE,
    width=800,
    height=800,
    aspect_ratio=AspectRatio.SQUARE,
    icon="youtube",
    tags=["youtube", "channel", "icon", "profile", "avatar"]
)

YOUTUBE_END_SCREEN = CanvasPreset(
    id="youtube_end_screen",
    name="YouTube End Screen",
    description="End screen template with element placement zones",
    category=PresetCategory.YOUTUBE,
    width=1920,
    height=1080,
    aspect_ratio=AspectRatio.LANDSCAPE_16_9,
    safe_zone=SafeZone(top=80, right=80, bottom=80, left=80),
    icon="youtube",
    tags=["youtube", "end", "screen", "outro", "subscribe"]
)


# =============================================================================
# TIKTOK PRESETS
# =============================================================================

TIKTOK_VIDEO = CanvasPreset(
    id="tiktok_video",
    name="TikTok Video",
    description="Full-screen vertical video format",
    category=PresetCategory.TIKTOK,
    width=1080,
    height=1920,
    aspect_ratio=AspectRatio.PORTRAIT_9_16,
    safe_zone=SafeZone(top=150, right=100, bottom=270, left=80),
    icon="tiktok",
    popular=True,
    tags=["tiktok", "video", "vertical", "fullscreen"]
)

TIKTOK_PROFILE = CanvasPreset(
    id="tiktok_profile",
    name="TikTok Profile Picture",
    description="Profile photo for TikTok",
    category=PresetCategory.TIKTOK,
    width=200,
    height=200,
    aspect_ratio=AspectRatio.SQUARE,
    icon="tiktok",
    tags=["tiktok", "profile", "avatar"]
)


# =============================================================================
# PINTEREST PRESETS
# =============================================================================

PINTEREST_PIN = CanvasPreset(
    id="pinterest_pin",
    name="Pinterest Pin",
    description="Standard pin - 2:3 ratio recommended",
    category=PresetCategory.PINTEREST,
    width=1000,
    height=1500,
    aspect_ratio=AspectRatio.CUSTOM,
    safe_zone=SafeZone(top=60, right=60, bottom=80, left=60),
    icon="pinterest",
    popular=True,
    tags=["pinterest", "pin", "vertical", "idea"]
)

PINTEREST_PIN_LONG = CanvasPreset(
    id="pinterest_pin_long",
    name="Pinterest Pin (Long)",
    description="Longer format pin - good for infographics",
    category=PresetCategory.PINTEREST,
    width=1000,
    height=2100,
    aspect_ratio=AspectRatio.CUSTOM,
    icon="pinterest",
    tags=["pinterest", "pin", "long", "infographic"]
)

PINTEREST_SQUARE = CanvasPreset(
    id="pinterest_square",
    name="Pinterest Square Pin",
    description="Square format pin",
    category=PresetCategory.PINTEREST,
    width=1000,
    height=1000,
    aspect_ratio=AspectRatio.SQUARE,
    icon="pinterest",
    tags=["pinterest", "pin", "square"]
)

PINTEREST_PROFILE = CanvasPreset(
    id="pinterest_profile",
    name="Pinterest Profile Picture",
    description="Profile photo for Pinterest",
    category=PresetCategory.PINTEREST,
    width=330,
    height=330,
    aspect_ratio=AspectRatio.SQUARE,
    icon="pinterest",
    tags=["pinterest", "profile", "avatar"]
)

PINTEREST_BOARD_COVER = CanvasPreset(
    id="pinterest_board_cover",
    name="Pinterest Board Cover",
    description="Cover image for Pinterest boards",
    category=PresetCategory.PINTEREST,
    width=600,
    height=600,
    aspect_ratio=AspectRatio.SQUARE,
    icon="pinterest",
    tags=["pinterest", "board", "cover"]
)


# =============================================================================
# SNAPCHAT PRESETS
# =============================================================================

SNAPCHAT_AD = CanvasPreset(
    id="snapchat_ad",
    name="Snapchat Ad/Story",
    description="Full-screen Snapchat format",
    category=PresetCategory.SNAPCHAT,
    width=1080,
    height=1920,
    aspect_ratio=AspectRatio.PORTRAIT_9_16,
    safe_zone=SafeZone(top=200, right=80, bottom=300, left=80),
    icon="snapchat",
    tags=["snapchat", "ad", "story", "vertical"]
)

SNAPCHAT_GEOFILTER = CanvasPreset(
    id="snapchat_geofilter",
    name="Snapchat Geofilter",
    description="Custom geofilter overlay",
    category=PresetCategory.SNAPCHAT,
    width=1080,
    height=2340,
    aspect_ratio=AspectRatio.CUSTOM,
    icon="snapchat",
    tags=["snapchat", "geofilter", "overlay", "location"]
)


# =============================================================================
# WHATSAPP PRESETS
# =============================================================================

WHATSAPP_STATUS = CanvasPreset(
    id="whatsapp_status",
    name="WhatsApp Status",
    description="Full-screen WhatsApp status image",
    category=PresetCategory.WHATSAPP,
    width=1080,
    height=1920,
    aspect_ratio=AspectRatio.PORTRAIT_9_16,
    safe_zone=SafeZone(top=120, right=60, bottom=180, left=60),
    icon="whatsapp",
    popular=True,
    tags=["whatsapp", "status", "story", "vertical"]
)

WHATSAPP_PROFILE = CanvasPreset(
    id="whatsapp_profile",
    name="WhatsApp Profile Picture",
    description="Profile photo for WhatsApp",
    category=PresetCategory.WHATSAPP,
    width=500,
    height=500,
    aspect_ratio=AspectRatio.SQUARE,
    icon="whatsapp",
    tags=["whatsapp", "profile", "avatar"]
)


# =============================================================================
# BUSINESS PRESETS
# =============================================================================

BUSINESS_CARD_STANDARD = CanvasPreset(
    id="business_card_standard",
    name="Business Card (Standard)",
    description="Standard business card - 3.5 x 2 inches at 300 DPI",
    category=PresetCategory.BUSINESS,
    width=1050,
    height=600,
    aspect_ratio=AspectRatio.CUSTOM,
    recommended_dpi=300,
    supported_formats=["PNG", "PDF"],
    icon="card",
    popular=True,
    tags=["business", "card", "print", "professional"]
)

BUSINESS_CARD_SQUARE = CanvasPreset(
    id="business_card_square",
    name="Business Card (Square)",
    description="Modern square business card",
    category=PresetCategory.BUSINESS,
    width=600,
    height=600,
    aspect_ratio=AspectRatio.SQUARE,
    recommended_dpi=300,
    icon="card",
    tags=["business", "card", "square", "modern"]
)

LETTERHEAD_A4 = CanvasPreset(
    id="letterhead_a4",
    name="Letterhead (A4)",
    description="A4 letterhead template at 300 DPI",
    category=PresetCategory.BUSINESS,
    width=2480,
    height=3508,
    aspect_ratio=AspectRatio.CUSTOM,
    recommended_dpi=300,
    supported_formats=["PNG", "PDF"],
    icon="document",
    tags=["letterhead", "a4", "print", "document"]
)

LETTERHEAD_LETTER = CanvasPreset(
    id="letterhead_letter",
    name="Letterhead (US Letter)",
    description="US Letter size letterhead at 300 DPI",
    category=PresetCategory.BUSINESS,
    width=2550,
    height=3300,
    aspect_ratio=AspectRatio.CUSTOM,
    recommended_dpi=300,
    icon="document",
    tags=["letterhead", "letter", "us", "print"]
)

INVOICE_A4 = CanvasPreset(
    id="invoice_a4",
    name="Invoice (A4)",
    description="A4 invoice template",
    category=PresetCategory.BUSINESS,
    width=2480,
    height=3508,
    aspect_ratio=AspectRatio.CUSTOM,
    recommended_dpi=300,
    icon="document",
    tags=["invoice", "a4", "billing", "document"]
)


# =============================================================================
# PRESENTATION PRESETS
# =============================================================================

PRESENTATION_16_9 = CanvasPreset(
    id="presentation_16_9",
    name="Presentation (16:9)",
    description="Standard widescreen presentation slide",
    category=PresetCategory.PRESENTATION,
    width=1920,
    height=1080,
    aspect_ratio=AspectRatio.LANDSCAPE_16_9,
    safe_zone=SafeZone(top=60, right=80, bottom=60, left=80),
    icon="presentation",
    popular=True,
    tags=["presentation", "slide", "widescreen", "16:9"]
)

PRESENTATION_4_3 = CanvasPreset(
    id="presentation_4_3",
    name="Presentation (4:3)",
    description="Traditional presentation slide format",
    category=PresetCategory.PRESENTATION,
    width=1600,
    height=1200,
    aspect_ratio=AspectRatio.CUSTOM,
    icon="presentation",
    tags=["presentation", "slide", "standard", "4:3"]
)

PRESENTATION_A4 = CanvasPreset(
    id="presentation_a4",
    name="Presentation (A4)",
    description="A4 aspect ratio presentation slide",
    category=PresetCategory.PRESENTATION,
    width=1587,
    height=1123,
    aspect_ratio=AspectRatio.CUSTOM,
    icon="presentation",
    tags=["presentation", "slide", "a4", "document"]
)


# =============================================================================
# PRINT PRESETS
# =============================================================================

POSTER_A3_PORTRAIT = CanvasPreset(
    id="poster_a3_portrait",
    name="Poster A3 (Portrait)",
    description="A3 poster - 297 x 420mm at 300 DPI",
    category=PresetCategory.PRINT,
    width=3508,
    height=4961,
    aspect_ratio=AspectRatio.CUSTOM,
    recommended_dpi=300,
    supported_formats=["PNG", "PDF", "TIFF"],
    icon="poster",
    tags=["poster", "a3", "portrait", "print"]
)

POSTER_A3_LANDSCAPE = CanvasPreset(
    id="poster_a3_landscape",
    name="Poster A3 (Landscape)",
    description="A3 poster landscape orientation",
    category=PresetCategory.PRINT,
    width=4961,
    height=3508,
    aspect_ratio=AspectRatio.CUSTOM,
    recommended_dpi=300,
    icon="poster",
    tags=["poster", "a3", "landscape", "print"]
)

POSTER_18X24 = CanvasPreset(
    id="poster_18x24",
    name="Poster 18x24 inches",
    description="Large format poster at 300 DPI",
    category=PresetCategory.PRINT,
    width=5400,
    height=7200,
    aspect_ratio=AspectRatio.CUSTOM,
    recommended_dpi=300,
    icon="poster",
    tags=["poster", "large", "print", "event"]
)

FLYER_A5 = CanvasPreset(
    id="flyer_a5",
    name="Flyer (A5)",
    description="A5 flyer - 148 x 210mm at 300 DPI",
    category=PresetCategory.PRINT,
    width=1748,
    height=2480,
    aspect_ratio=AspectRatio.CUSTOM,
    recommended_dpi=300,
    icon="flyer",
    popular=True,
    tags=["flyer", "a5", "print", "handout"]
)

FLYER_A6 = CanvasPreset(
    id="flyer_a6",
    name="Flyer (A6)",
    description="A6 flyer - 105 x 148mm at 300 DPI",
    category=PresetCategory.PRINT,
    width=1240,
    height=1748,
    aspect_ratio=AspectRatio.CUSTOM,
    recommended_dpi=300,
    icon="flyer",
    tags=["flyer", "a6", "print", "small"]
)

BROCHURE_TRIFOLD = CanvasPreset(
    id="brochure_trifold",
    name="Trifold Brochure (Letter)",
    description="US Letter trifold brochure unfolded",
    category=PresetCategory.PRINT,
    width=3300,
    height=2550,
    aspect_ratio=AspectRatio.CUSTOM,
    recommended_dpi=300,
    icon="brochure",
    tags=["brochure", "trifold", "print", "marketing"]
)

BANNER_ROLL_UP = CanvasPreset(
    id="banner_roll_up",
    name="Roll-up Banner (85x200cm)",
    description="Standard roll-up banner at 150 DPI",
    category=PresetCategory.PRINT,
    width=5039,
    height=11811,
    aspect_ratio=AspectRatio.CUSTOM,
    recommended_dpi=150,
    icon="banner",
    tags=["banner", "roll-up", "standing", "display"]
)


# =============================================================================
# WEB PRESETS
# =============================================================================

WEB_BANNER_LEADERBOARD = CanvasPreset(
    id="web_banner_leaderboard",
    name="Web Banner (Leaderboard)",
    description="Standard leaderboard ad - 728 x 90",
    category=PresetCategory.WEB,
    width=728,
    height=90,
    aspect_ratio=AspectRatio.CUSTOM,
    icon="web",
    tags=["web", "banner", "ad", "leaderboard"]
)

WEB_BANNER_MEDIUM = CanvasPreset(
    id="web_banner_medium",
    name="Web Banner (Medium Rectangle)",
    description="Medium rectangle ad - 300 x 250",
    category=PresetCategory.WEB,
    width=300,
    height=250,
    aspect_ratio=AspectRatio.CUSTOM,
    icon="web",
    tags=["web", "banner", "ad", "rectangle"]
)

WEB_BANNER_LARGE = CanvasPreset(
    id="web_banner_large",
    name="Web Banner (Large Rectangle)",
    description="Large rectangle ad - 336 x 280",
    category=PresetCategory.WEB,
    width=336,
    height=280,
    aspect_ratio=AspectRatio.CUSTOM,
    icon="web",
    tags=["web", "banner", "ad", "large"]
)

WEB_BANNER_SKYSCRAPER = CanvasPreset(
    id="web_banner_skyscraper",
    name="Web Banner (Skyscraper)",
    description="Wide skyscraper ad - 160 x 600",
    category=PresetCategory.WEB,
    width=160,
    height=600,
    aspect_ratio=AspectRatio.CUSTOM,
    icon="web",
    tags=["web", "banner", "ad", "skyscraper"]
)

HERO_SECTION = CanvasPreset(
    id="hero_section",
    name="Website Hero Section",
    description="Full-width hero section image",
    category=PresetCategory.WEB,
    width=1920,
    height=1080,
    aspect_ratio=AspectRatio.LANDSCAPE_16_9,
    safe_zone=SafeZone(top=100, right=200, bottom=200, left=200),
    icon="web",
    popular=True,
    tags=["web", "hero", "header", "landing"]
)

EMAIL_HEADER = CanvasPreset(
    id="email_header",
    name="Email Header",
    description="Header image for email newsletters",
    category=PresetCategory.WEB,
    width=600,
    height=200,
    aspect_ratio=AspectRatio.LANDSCAPE_3_1,
    icon="email",
    tags=["email", "header", "newsletter", "marketing"]
)

BLOG_FEATURED = CanvasPreset(
    id="blog_featured",
    name="Blog Featured Image",
    description="Featured image for blog posts",
    category=PresetCategory.WEB,
    width=1200,
    height=630,
    aspect_ratio=AspectRatio.CUSTOM,
    icon="blog",
    tags=["blog", "featured", "article", "post"]
)

OG_IMAGE = CanvasPreset(
    id="og_image",
    name="Open Graph Image",
    description="Social sharing preview image",
    category=PresetCategory.WEB,
    width=1200,
    height=630,
    aspect_ratio=AspectRatio.CUSTOM,
    icon="share",
    popular=True,
    tags=["og", "opengraph", "share", "preview", "meta"]
)


# =============================================================================
# NEPALI FESTIVAL PRESETS
# =============================================================================

NEPALI_FESTIVAL_SQUARE = CanvasPreset(
    id="nepali_festival_square",
    name="Festival Greeting (Square)",
    description="Square format ideal for Nepali festival wishes - Dashain, Tihar, etc.",
    category=PresetCategory.CUSTOM,
    width=1080,
    height=1080,
    aspect_ratio=AspectRatio.SQUARE,
    safe_zone=SafeZone(top=80, right=80, bottom=80, left=80),
    icon="festival",
    popular=True,
    tags=["nepal", "festival", "greeting", "dashain", "tihar", "square"]
)

NEPALI_FESTIVAL_STORY = CanvasPreset(
    id="nepali_festival_story",
    name="Festival Greeting (Story)",
    description="Vertical story format for festival wishes",
    category=PresetCategory.CUSTOM,
    width=1080,
    height=1920,
    aspect_ratio=AspectRatio.PORTRAIT_9_16,
    safe_zone=SafeZone(top=180, right=80, bottom=250, left=80),
    icon="festival",
    popular=True,
    tags=["nepal", "festival", "greeting", "story", "vertical"]
)

NEPALI_BUSINESS_POST = CanvasPreset(
    id="nepali_business_post",
    name="Business Promo (Nepal)",
    description="Business promotion post for local Nepali businesses",
    category=PresetCategory.CUSTOM,
    width=1080,
    height=1080,
    aspect_ratio=AspectRatio.SQUARE,
    safe_zone=SafeZone(top=60, right=60, bottom=120, left=60),
    icon="business",
    tags=["nepal", "business", "promo", "local", "shop"]
)


# =============================================================================
# PRESET REGISTRY
# =============================================================================

ALL_PRESETS: Dict[str, CanvasPreset] = {
    # Instagram
    "instagram_post_square": INSTAGRAM_POST_SQUARE,
    "instagram_post_portrait": INSTAGRAM_POST_PORTRAIT,
    "instagram_post_landscape": INSTAGRAM_POST_LANDSCAPE,
    "instagram_story": INSTAGRAM_STORY,
    "instagram_reel_cover": INSTAGRAM_REEL_COVER,
    "instagram_profile_photo": INSTAGRAM_PROFILE_PHOTO,
    "instagram_carousel": INSTAGRAM_CAROUSEL,
    "instagram_ad_square": INSTAGRAM_AD_SQUARE,
    
    # Facebook
    "facebook_post": FACEBOOK_POST,
    "facebook_post_square": FACEBOOK_POST_SQUARE,
    "facebook_cover": FACEBOOK_COVER,
    "facebook_cover_mobile": FACEBOOK_COVER_MOBILE_SAFE,
    "facebook_event_cover": FACEBOOK_EVENT_COVER,
    "facebook_group_cover": FACEBOOK_GROUP_COVER,
    "facebook_ad": FACEBOOK_AD,
    "facebook_story": FACEBOOK_STORY,
    "facebook_profile": FACEBOOK_PROFILE,
    
    # Twitter
    "twitter_post": TWITTER_POST,
    "twitter_post_square": TWITTER_POST_SQUARE,
    "twitter_header": TWITTER_HEADER,
    "twitter_profile": TWITTER_PROFILE,
    "twitter_card": TWITTER_CARD,
    
    # LinkedIn
    "linkedin_post": LINKEDIN_POST,
    "linkedin_post_square": LINKEDIN_POST_SQUARE,
    "linkedin_banner": LINKEDIN_BANNER,
    "linkedin_company_cover": LINKEDIN_COMPANY_COVER,
    "linkedin_profile": LINKEDIN_PROFILE,
    "linkedin_article_cover": LINKEDIN_ARTICLE_COVER,
    
    # YouTube
    "youtube_thumbnail": YOUTUBE_THUMBNAIL,
    "youtube_channel_art": YOUTUBE_CHANNEL_ART,
    "youtube_channel_icon": YOUTUBE_CHANNEL_ICON,
    "youtube_end_screen": YOUTUBE_END_SCREEN,
    
    # TikTok
    "tiktok_video": TIKTOK_VIDEO,
    "tiktok_profile": TIKTOK_PROFILE,
    
    # Pinterest
    "pinterest_pin": PINTEREST_PIN,
    "pinterest_pin_long": PINTEREST_PIN_LONG,
    "pinterest_square": PINTEREST_SQUARE,
    "pinterest_profile": PINTEREST_PROFILE,
    "pinterest_board_cover": PINTEREST_BOARD_COVER,
    
    # Snapchat
    "snapchat_ad": SNAPCHAT_AD,
    "snapchat_geofilter": SNAPCHAT_GEOFILTER,
    
    # WhatsApp
    "whatsapp_status": WHATSAPP_STATUS,
    "whatsapp_profile": WHATSAPP_PROFILE,
    
    # Business
    "business_card_standard": BUSINESS_CARD_STANDARD,
    "business_card_square": BUSINESS_CARD_SQUARE,
    "letterhead_a4": LETTERHEAD_A4,
    "letterhead_letter": LETTERHEAD_LETTER,
    "invoice_a4": INVOICE_A4,
    
    # Presentation
    "presentation_16_9": PRESENTATION_16_9,
    "presentation_4_3": PRESENTATION_4_3,
    "presentation_a4": PRESENTATION_A4,
    
    # Print
    "poster_a3_portrait": POSTER_A3_PORTRAIT,
    "poster_a3_landscape": POSTER_A3_LANDSCAPE,
    "poster_18x24": POSTER_18X24,
    "flyer_a5": FLYER_A5,
    "flyer_a6": FLYER_A6,
    "brochure_trifold": BROCHURE_TRIFOLD,
    "banner_roll_up": BANNER_ROLL_UP,
    
    # Web
    "web_banner_leaderboard": WEB_BANNER_LEADERBOARD,
    "web_banner_medium": WEB_BANNER_MEDIUM,
    "web_banner_large": WEB_BANNER_LARGE,
    "web_banner_skyscraper": WEB_BANNER_SKYSCRAPER,
    "hero_section": HERO_SECTION,
    "email_header": EMAIL_HEADER,
    "blog_featured": BLOG_FEATURED,
    "og_image": OG_IMAGE,
    
    # Nepali/Custom
    "nepali_festival_square": NEPALI_FESTIVAL_SQUARE,
    "nepali_festival_story": NEPALI_FESTIVAL_STORY,
    "nepali_business_post": NEPALI_BUSINESS_POST,
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_preset(preset_id: str) -> Optional[CanvasPreset]:
    """Get a preset by its ID."""
    return ALL_PRESETS.get(preset_id)


def get_presets_by_category(category: PresetCategory) -> List[CanvasPreset]:
    """Get all presets in a specific category."""
    return [p for p in ALL_PRESETS.values() if p.category == category]


def get_popular_presets() -> List[CanvasPreset]:
    """Get all popular/frequently used presets."""
    return [p for p in ALL_PRESETS.values() if p.popular]


def get_all_presets() -> List[Dict[str, Any]]:
    """Get all presets as dictionaries."""
    return [p.to_dict() for p in ALL_PRESETS.values()]


def get_all_preset_summaries() -> List[Dict[str, Any]]:
    """Get compact summaries of all presets for UI listing."""
    return [p.to_summary() for p in ALL_PRESETS.values()]


def get_presets_grouped_by_category() -> Dict[str, List[Dict[str, Any]]]:
    """Get all presets grouped by their category."""
    grouped = {}
    for preset in ALL_PRESETS.values():
        category = preset.category.value
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(preset.to_summary())
    return grouped


def search_presets(query: str) -> List[CanvasPreset]:
    """Search presets by name, description, or tags."""
    query = query.lower()
    results = []
    for preset in ALL_PRESETS.values():
        if (query in preset.name.lower() or
            query in preset.description.lower() or
            any(query in tag.lower() for tag in preset.tags)):
            results.append(preset)
    return results


def get_presets_by_orientation(orientation: str) -> List[CanvasPreset]:
    """Get presets by orientation: 'portrait', 'landscape', or 'square'."""
    return [p for p in ALL_PRESETS.values() if p.orientation == orientation]


def get_presets_by_aspect_ratio(aspect_ratio: AspectRatio) -> List[CanvasPreset]:
    """Get presets by aspect ratio."""
    return [p for p in ALL_PRESETS.values() if p.aspect_ratio == aspect_ratio]


def create_custom_preset(
    name: str,
    width: int,
    height: int,
    description: str = "Custom canvas size"
) -> CanvasPreset:
    """Create a custom preset with specified dimensions."""
    # Determine aspect ratio
    if width == height:
        aspect = AspectRatio.SQUARE
    elif abs(width / height - 16/9) < 0.01:
        aspect = AspectRatio.LANDSCAPE_16_9
    elif abs(height / width - 16/9) < 0.01:
        aspect = AspectRatio.PORTRAIT_9_16
    else:
        aspect = AspectRatio.CUSTOM
    
    return CanvasPreset(
        id=f"custom_{width}x{height}",
        name=name,
        description=description,
        category=PresetCategory.CUSTOM,
        width=width,
        height=height,
        aspect_ratio=aspect,
        icon="custom",
        tags=["custom", "user"]
    )


def get_category_info() -> List[Dict[str, Any]]:
    """Get information about all preset categories."""
    category_names = {
        PresetCategory.INSTAGRAM: "Instagram",
        PresetCategory.FACEBOOK: "Facebook",
        PresetCategory.TWITTER: "Twitter/X",
        PresetCategory.LINKEDIN: "LinkedIn",
        PresetCategory.YOUTUBE: "YouTube",
        PresetCategory.TIKTOK: "TikTok",
        PresetCategory.PINTEREST: "Pinterest",
        PresetCategory.SNAPCHAT: "Snapchat",
        PresetCategory.WHATSAPP: "WhatsApp",
        PresetCategory.BUSINESS: "Business",
        PresetCategory.PRESENTATION: "Presentation",
        PresetCategory.PRINT: "Print",
        PresetCategory.WEB: "Web",
        PresetCategory.CUSTOM: "Custom/Nepal",
    }
    
    category_icons = {
        PresetCategory.INSTAGRAM: "instagram",
        PresetCategory.FACEBOOK: "facebook",
        PresetCategory.TWITTER: "twitter",
        PresetCategory.LINKEDIN: "linkedin",
        PresetCategory.YOUTUBE: "youtube",
        PresetCategory.TIKTOK: "tiktok",
        PresetCategory.PINTEREST: "pinterest",
        PresetCategory.SNAPCHAT: "snapchat",
        PresetCategory.WHATSAPP: "whatsapp",
        PresetCategory.BUSINESS: "briefcase",
        PresetCategory.PRESENTATION: "presentation",
        PresetCategory.PRINT: "printer",
        PresetCategory.WEB: "globe",
        PresetCategory.CUSTOM: "star",
    }
    
    result = []
    for category in PresetCategory:
        presets = get_presets_by_category(category)
        result.append({
            "id": category.value,
            "name": category_names.get(category, category.value.title()),
            "icon": category_icons.get(category, "image"),
            "count": len(presets),
            "presets": [p.to_summary() for p in presets]
        })
    
    return result
