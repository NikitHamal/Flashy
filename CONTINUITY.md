# CONTINUITY.md - Session Continuity Ledger

## Goal (incl. success criteria):
1. **Flashy Astro Agent**: Build production-grade Vedic Astrology agent with:
   - Dedicated astro.html page with neobrutalist design
   - Kundali list, creation, and detailed views
   - AI sidebar that never disappears (agentic Vedic astrologer)
   - Full Vedic calculations (planets, houses, nakshatras, dashas, yogas, shadbala, ashtakavarga)
   - Tools: create_kundali, list_kundalis, get_kundali_details, get_planetary_data, get_dasha_info, etc.
   - LocalStorage persistence for multiple profiles
   - Gender selection in profile creation
   - Astrologer-friendly detailed views (manual interpretation without AI)

2. **Design Agent SVG Update**: Transform JSON-based design to SVG-based:
   - Replace JSON canvas state with SVG generation
   - AI creates SVG that renders directly
   - Full SVG customization controls for users
   - Proper aspect ratio canvas (not infinite)
   - Neobrutalist design throughout app
   - Update all design tools for SVG paradigm

## Constraints/Assumptions:
- Modularization: 500-800 lines per file max
- Production-grade only - no TODOs, stubs, or basic implementations
- Vedic calculations must be precise (based on NASA JPL ephemeris via AstroWeb)
- Neobrutalist design: bold borders, solid colors, minimal shadows, brutalist typography
- LocalStorage for persistence (no backend DB changes needed)
- Copy/integrate AstroWeb calculation engine into Flashy

## Key Decisions:
- Copy AstroWeb astro calculation modules to frontend/js/astro/
- Create new backend service: astro_service.py, astro_agent.py, astro_tools.py
- Create new frontend page: frontend/astro.html with dedicated CSS
- For Design Agent: Implement SVG-based rendering with full control panel
- Use NASA JPL Astronomy Engine (via AstroWeb's astronomy.min.js) for calculations

## State:

- Done:
  - Explored existing Flashy codebase structure
  - Explored AstroWeb repository (14,450+ lines of Vedic calculations)
  - Cloned AstroWeb to /tmp/AstroWeb
  - Analyzed design agent implementation (design_service.py, design_agent.py, design_tools.py)

- Now:
  - Create Flashy Astro agent backend infrastructure
  - Copy AstroWeb calculation modules
  - Build astro_tools.py with all Vedic astrology tools

- Next:
  - Create astro_service.py and astro_agent.py
  - Create astro_prompts.py with expert Vedic astrologer persona
  - Build frontend astro.html with neobrutalist design
  - Build frontend JS modules for astro (kundali rendering, chat, etc.)
  - Update design agent to SVG-based approach
  - Apply neobrutalist design throughout app

## Open Questions (UNCONFIRMED if needed):
- None - proceeding with expert judgment per instructions

## Working Set (files/ids/commands):
- Source: /tmp/AstroWeb/js/astro/* (Vedic calculation modules)
- Backend new: /backend/astro_service.py, astro_agent.py, astro_tools.py, astro_prompts.py
- Backend router: /backend/routers/astro.py
- Frontend new: /frontend/astro.html, /frontend/css/astro.css
- Frontend JS: /frontend/js/astro/* (copied from AstroWeb + custom modules)
- Design update: /backend/design_service.py, design_tools.py, design_prompts.py
- Frontend design: /frontend/design.html, /frontend/js/design/*
