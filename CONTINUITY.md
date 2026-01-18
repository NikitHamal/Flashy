# CONTINUITY.md - Session Continuity Ledger

## Goal (incl. success criteria):
- Transform Flashy Designs from basic to professional-grade design tool
- Fix element positioning and layout issues (main flaw identified by user)
- Add canvas size presets for all social media platforms
- Create comprehensive festival templates for Nepal (Saraswoti Puja, Dashain, Tihar, etc.)
- Enhance AI prompts for structured, professional layouts
- Make designs comparable to Gamma AI / Slides AI quality
- Enable user to fulfill contract work for dairy, sweets, and other businesses

## Constraints/Assumptions:
- Maximum 500-800 lines per file (modular architecture)
- Production-grade code only, no TODOs or stubs
- Gemini 3 Flash multimodal model in use
- Fabric.js 5.x for canvas rendering
- Must maintain existing API contract for frontend-backend communication

## Key Decisions:
- Implement hierarchical composition system for precise layouts
- Create pre-defined zones for professional banner/poster composition
- Add comprehensive social media presets with visual selector
- Create Nepal festival template pack with brand integration slots
- Enhance AI system prompt with strict layout rules and calculations
- Add visual hierarchy scoring for better element placement

## State:

### COMPLETED:

1. **Compositional Layout Engine** (`/backend/composition_engine.py`) - ~952 lines
   - Hierarchical composition zones (header, hero, content, footer, decorative)
   - Visual hierarchy with element roles (MAIN_HEADING, SUBHEADING, BRAND_LOGO, etc.)
   - Golden ratio and rule-of-thirds calculations
   - Multiple composition styles: centered, split, left_heavy, right_heavy
   - Festival greeting composition optimized for Nepali festivals
   - Typography specifications scaled to canvas size
   - Placement helpers for precise element positioning

2. **Comprehensive Canvas Presets** (`/backend/canvas_presets.py`) - ~800+ lines
   - Instagram: Post (Square/Portrait/Landscape), Story, Reel Cover, Profile, Carousel, Ad
   - Facebook: Post, Cover, Event Cover, Group Cover, Ad, Story, Profile
   - Twitter/X: Post, Header, Card, Profile
   - LinkedIn: Post, Banner, Company Cover, Article Cover, Profile
   - YouTube: Thumbnail, Channel Banner, Channel Icon, End Screen
   - TikTok: Video, Profile
   - Pinterest: Pin (Standard/Long/Square), Board Cover, Profile
   - Snapchat: Ad/Story, Geofilter
   - WhatsApp: Status, Profile
   - Business: Card (Standard/Square), Letterhead (A4/Letter), Invoice
   - Presentation: 16:9, 4:3, A4
   - Print: Poster A3, Flyer A5/A6, Brochure, Roll-up Banner
   - Web: Banners (Leaderboard/Rectangle/Skyscraper), Hero Section, Email Header, Blog Featured, OG Image
   - Nepal Festival Presets: Square Greeting, Story Greeting, Business Promo

3. **Nepal Festival Templates** (`/backend/design_templates.py` enhanced)
   - New palettes: Saraswoti Puja, Dashain, Tihar, Holi, Nepali New Year, Teej, Chhath, Buddha Jayanti
   - Business palettes: Dairy Business, Sweets Shop
   - Festival templates with full element positioning:
     - Saraswoti Puja Greeting (yellow/white, veena, education theme)
     - Dashain Greeting (red tika, green jamara, family blessings)
     - Tihar Greeting (orange diyo, dark background, rangoli)
     - Holi Greeting (colorful splash effects)
     - Nepali New Year 2082 (national colors)
     - Teej Greeting (red sindoor, bangles motif)
     - Chhath Puja Greeting (sunrise, water reflection)
     - Buddha Jayanti Greeting (lotus, enlightenment glow)
   - Local business templates:
     - Dairy Business Promo (fresh green, milk drops)
     - Sweets Shop Promo (warm orange, traditional borders)

4. **Enhanced AI System Prompts** (`/backend/design_prompts.py` overhauled)
   - Zone-based composition system with strict positioning rules
   - Mathematical position calculation formulas (centering, alignment)
   - Golden ratio and rule of thirds integration
   - Element role specifications with typography sizes
   - Nepali festival color palettes and typography guidance
   - Common Nepali greetings in Devanagari script
   - Position verification checklist for AI
   - Local business design guidelines

5. **Frontend Preset Selector** (`/frontend/js/design/presets.js`)
   - Modal UI with category sidebar
   - Visual preset cards with dimensions
   - Search functionality across all presets
   - Custom size input with aspect ratio helpers
   - Template list for quick festival/business designs
   - Integration with canvas resize functionality
   - Notification system for user feedback

6. **CSS Styles for Preset Modal** (`/frontend/css/design.css` extended)
   - Responsive preset modal layout
   - Category buttons with icons
   - Preset grid with hover effects
   - Custom size form styling
   - Notification animations
   - Template section styling

7. **Design Service Integration** (`/backend/design_service.py` enhanced)
   - Composition engine integration for dynamic zone context
   - Festival type detection from user prompts
   - Automatic palette suggestions for Nepali festivals
   - Enhanced tool result messaging with object IDs

### IN PROGRESS:
- None currently

### NEXT (Future Enhancements):
- Visual hierarchy scoring for element prioritization
- Brand kit integration (saved logos, color schemes)
- Template gallery with preview thumbnails
- Auto-layout tools based on content analysis
- Multi-language support (Nepali font rendering)
- Export presets (quality/format per platform)

## Working Set (files modified/created):

### Backend (Python):
- `/backend/composition_engine.py` - NEW - Compositional layout system
- `/backend/canvas_presets.py` - NEW - Comprehensive presets database
- `/backend/design_templates.py` - ENHANCED - Nepal festivals + palettes
- `/backend/design_prompts.py` - OVERHAULED - Zone-based positioning
- `/backend/design_service.py` - ENHANCED - Composition integration

### Frontend (JavaScript/HTML/CSS):
- `/frontend/js/design/presets.js` - NEW - Preset selector UI
- `/frontend/design.html` - MODIFIED - Script include for presets.js
- `/frontend/css/design.css` - EXTENDED - Modal and preset styles

## Testing Notes:
- Run the application and test preset selector from canvas properties panel
- Try creating a Dashain greeting - AI should use red/green palette and proper zones
- Test canvas resize to Instagram Story (1080x1920) - should work correctly
- Festival templates accessible via template list in properties sidebar
