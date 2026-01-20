# CONTINUITY.md - Session Continuity Ledger

## Goal (incl. success criteria):
- Add new Flashy Astro agent with its own page, kundali list/create, persistent chat sidebar, local storage, and detailed kundali pages
- Integrate/port AstroWeb capabilities or equivalent for vedic chart generation and deep-dive details usable by astrologers without AI
- Replace design agent JSON canvas with SVG-based workflow, tools, and UI; modern neobrutalist responsive design; fixed aspect ratio canvas
- Maintain modular files (<=800 lines) and production-grade behavior across frontend/backend

## Constraints/Assumptions:
- No TODOs or stub code; production-grade only
- Always use modularization
- Use SVG-based design output + user controls
- Neobrutalist design language across app
- Predictions/astrology outputs must be accurate per vedic logic (UNCONFIRMED data sources)

## Key Decisions:
- Implemented Astro calculations on frontend using Astronomy library + Vedic calculator; backend agent uses kundali summaries from local storage
- Design agent switched to SVG state with server-side SVG tools and frontend SVG editor
- Applied neobrutalist theme via shared CSS variables and overrides

## State:

- Done:
  - Added Flashy Astro page with kundali list/create, persistent chat, and detailed chart view
  - Implemented Astro backend agent + tools + routing
  - Added frontend Vedic calculator + SVG chart rendering
  - Rebuilt Design agent/editor to SVG workflow with export and properties
  - Applied neobrutalist theme across main app, astro, and design

- Now:
  - Sanity-check flow and capture any follow-up fixes

- Next:
  - Provide summary + recommended next steps/tests

## Open Questions (UNCONFIRMED if needed):
- None

## Working Set (files/ids/commands):
- Backend: /backend/astro_service.py, /backend/astro_agent.py, /backend/astro_tools.py, /backend/astro_prompts.py, /backend/design_svg_tools.py, /backend/design_agent.py, /backend/design_prompts.py, /backend/design_service.py, /backend/app.py, /backend/routers/astro.py
- Frontend: /frontend/astro.html, /frontend/css/astro.css, /frontend/js/astro/*, /frontend/design.html, /frontend/css/design.css, /frontend/js/design/*, /frontend/css/main.css, /frontend/index.html
