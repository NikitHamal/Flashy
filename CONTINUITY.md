# CONTINUITY.md - Session Continuity Ledger

## Goal (incl. success criteria):
- Add new “Flashy Astro” agent with dedicated pages for list/create/detail kundalis, persistent chat sidebar, local storage, and Vedic astrology tooling
- Update design agent to SVG-based generation with modern neobrutalist UI, proper canvas aspect ratios, and rich customization controls
- Maintain modular files (<800 lines) and production-grade behavior

## Constraints/Assumptions:
- Do not ask user questions; use expert judgment
- Use modularization and production-grade implementations only
- Neobrutalist, minimal, clean, responsive UI throughout
- Store kundalis locally (localStorage)
- Support gender selection for charts

## Key Decisions:
- Build Astro as dedicated backend service + frontend page with localStorage sync
- Replace design canvas with SVG pipeline and simplified SVG tools

## State:

- Done:
  - Added Astro backend modules (`astro_service`, `astro_agent`, `astro_tools`, `vedic_reference`, `routers/astro`)
  - Added Astro frontend page, storage, UI, chat modules, and CSS
  - Linked Flashy Astro entry in sidebar
  - Rebuilt design agent prompt and backend to SVG tools
  - Replaced design frontend canvas and toolchain with SVG-based editor
  - Updated core neobrutalist styles in `main.css` and design styles

- Now:
  - Finish polishing SVG editor styles and behaviors

- Next:
  - Review for missing hooks / UI regressions
  - Summarize changes and offer test guidance

## Open Questions (UNCONFIRMED if needed):
- UNCONFIRMED: Any missing design editor behaviors desired (multi-select, snapping, guides)

## Working Set (files/ids/commands):
- Backend: `backend/app.py`, `backend/astro_service.py`, `backend/astro_agent.py`, `backend/astro_tools.py`, `backend/vedic_reference.py`, `backend/routers/astro.py`, `backend/design_agent.py`, `backend/design_prompts.py`, `backend/design_service.py`, `backend/design_svg_tools.py`
- Frontend: `frontend/astro.html`, `frontend/css/astro.css`, `frontend/js/astro/*.js`, `frontend/design.html`, `frontend/js/design/*.js`, `frontend/css/design.css`, `frontend/css/main.css`, `frontend/index.html`
