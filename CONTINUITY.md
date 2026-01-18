# CONTINUITY.md - Session Continuity Ledger

## Goal (incl. success criteria):
- Deliver professional, structured design outputs with correct element placement
- Add post size presets + custom sizing for popular social platforms
- Provide high-end festival templates/presets (Nepal focus) with logos
- Improve Flashy Designs UX/tools and overall agent quality
- Maintain modular files (<800 lines) and production-grade behavior
- Keep AI multimodal feedback loop for design screenshots

## Constraints/Assumptions:
- Gemini 3 Flash model is multimodal (can see images)
- File upload exists for design chat
- No TODOs or stub code; production-grade only
- Maintain modular approach (500-800 lines max per file)
- Keep UI/UX consistent with existing app styling
- Do not ask the user follow-up questions

## Key Decisions:
- Unify design tool schema between backend and frontend
- Stream tool calls plus canvas actions to frontend for live updates
- Add robust streaming error handling and message rendering

## State:

- Done:
  - Added layout guidance into design prompts and streaming context
  - Fixed polygon/star positioning to use top-left input coords
  - Added size preset UI with custom sizing + swap/apply controls
  - Added Nepal festival template catalog + new palettes
  - Refactored templates into modular files under 800 lines

- Now:
  - Verify template/preset flows and final UX polish

- Next:
  - Summarize changes and suggest validation steps

## Open Questions (UNCONFIRMED if needed):
- None

## Working Set (files/ids/commands):
- Backend: /backend/design_service.py, /backend/design_agent.py, /backend/design_tools.py, /backend/routers/design.py, /backend/tools.py, /backend/prompts.py
- Frontend: /frontend/design.html, /frontend/css/design.css, /frontend/js/design/*.js, /frontend/js/ui/chat.js
