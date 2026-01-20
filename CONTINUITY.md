# CONTINUITY.md - Session Continuity Ledger

## Goal (incl. success criteria):
1. **Add Flashy Astro Agent** - A new Vedic astrology agent with:
   - Dedicated page with kundali management (list, create, view details)
   - Persistent right sidebar for AI chat
   - Full vedic chart calculations (Lagna, planets, nakshatras, dashas, yogas)
   - AI can create kundalis by extracting birth details from conversation
   - Astrologers can view raw chart data without AI interpretation
   - Multiple kundali support stored in localStorage
   - Gender selection for chart creation
   - Deep dive into individual kundali details (dashas, yogas, transits)
   - Agent tools: create_kundali, list_kundalis, get_kundali_details, calculate_dasha, check_yogas, etc.
   - Professional, blunt, truth-speaking Vedic astrologer persona

2. **Update Design Agent to SVG-based approach**:
   - Replace JSON-based design with SVG generation
   - AI creates SVG that app renders
   - Full user control/customization of rendered SVG
   - Update all design tools for SVG operations
   - Fix canvas aspect ratio (proper sizing, not infinite)
   - Neobrutalist design throughout

3. **Apply Neobrutalist Design**:
   - Modern, clean, responsive, minimal
   - Avoid excessive shadows and hifi designs
   - Bold borders, stark contrasts, flat colors
   - Consistent across all pages

## Constraints/Assumptions:
- Modularization: 500-800 lines max per file
- Production-grade code only, no TODOs or stubs
- All vedic calculations must be precise and accurate
- Use AstroWeb's proven calculation engine as reference
- Maintain compatibility with existing Gemini API integration
- Use localStorage for kundali/profile persistence
- SVG for design agent instead of Fabric.js/JSON

## Key Decisions:
- Port AstroWeb's vedic calculation engine to Python backend for server-side calculations
- Create comprehensive astro_tools.py with all vedic astrology tools
- Use Swiss Ephemeris (pyswisseph) for astronomical calculations in Python
- Implement Lahiri ayanamsa by default with configurable options
- SVG-based design agent with inline editing capabilities
- Neobrutalist CSS theme with bold black borders, flat colors

## State:

- Done:
  - Explored existing Flashy codebase architecture
  - Cloned and analyzed AstroWeb repository
  - Documented comprehensive vedic calculation algorithms
  - Planned astro agent architecture
  - **Design Agent SVG Update COMPLETE**:
    - Backend: svg_tools.py, design_agent.py, design_service.py, design_prompts.py
    - Frontend HTML/CSS: design.html, design.css (neobrutalist)
    - Frontend JS: canvas.js (SVG-based), chat.js (SVG flow)
    - Frontend JS: tools.js (native SVG drawing)
    - Frontend JS: properties.js (SVG attributes)
    - Frontend JS: export.js (SVG export)
    - Frontend JS: app.js (Fabric.js refs removed)

- Now:
  - All Design Agent frontend files updated for native SVG
  - Ready for testing

- Next:
  - Test the complete Design Agent SVG flow
  - Continue with Astro Agent if needed

## Open Questions (UNCONFIRMED if needed):
- None currently

## Working Set (files/ids/commands):
- AstroWeb reference: /tmp/AstroWeb/
- Backend new files: 
  - backend/astro_engine.py (vedic calculations)
  - backend/astro_tools.py (agent tools)
  - backend/astro_agent.py (agent logic)
  - backend/astro_service.py (service layer)
  - backend/astro_prompts.py (system prompts)
  - backend/routers/astro.py (API routes)
- Frontend new files:
  - frontend/astro.html
  - frontend/css/astro.css
  - frontend/js/astro/app.js
  - frontend/js/astro/chat.js
  - frontend/js/astro/charts.js
  - frontend/js/astro/kundali.js
  - frontend/js/astro/storage.js
- Design update files (ALL COMPLETED):
  - backend/svg_tools.py (SVG manipulation tools)
  - backend/design_agent.py (SVG agent logic)
  - backend/design_service.py (SVG service layer)
  - backend/design_prompts.py (SVG system prompts)
  - frontend/design.html (neobrutalist UI)
  - frontend/css/design.css (neobrutalist styles)
  - frontend/js/design/canvas.js (native SVG renderer)
  - frontend/js/design/tools.js (native SVG drawing tools)
  - frontend/js/design/properties.js (SVG element properties)
  - frontend/js/design/export.js (SVG/PNG export)
  - frontend/js/design/chat.js (SVG chat flow)
  - frontend/js/design/app.js (main app controller)
