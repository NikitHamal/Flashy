# CONTINUITY.md - Session Continuity Ledger

## Goal (incl. success criteria):
- Fix Flashy Designs agent so AI output applies to canvas and messages render correctly
- Improve Flashy Designs UX (responsive layout, better tools, export/import, templates, alignment)
- Enhance Flashy coding agent reliability/power with stronger tools + UI feedback
- Maintain modular files (<800 lines) and production-grade behavior
- Keep AI multimodal feedback loop for design screenshots

## Constraints/Assumptions:
- Gemini 3 Flash model is multimodal (can see images)
- File upload exists for design chat
- No TODOs or stub code; production-grade only
- Maintain modular approach (500-800 lines max per file)
- Keep UI/UX consistent with existing app styling

## Key Decisions:
- Unify design tool schema between backend and frontend
- Stream tool calls plus canvas actions to frontend for live updates
- Add robust streaming error handling and message rendering

## State:

- Done:
  - Unified design tool schema across backend/frontend
  - Added canvas_action streaming and frontend canvas execution
  - Fixed screenshot base64 decoding and image attachment handling
  - Added grid/snap toggles, align/distribute tools, and richer export options
  - Expanded coding agent tools (read/write multiple files, apply patch) and UI tool mapping
  - Added response sanitization for YouTube links across backend and UI
  - Tightened agent prompts for concise output and explicit coordinate system

- Now:
  - Validate integration and update summary

- Next:
  - Optional: test runtime UX (manual run) and iterate

## Open Questions (UNCONFIRMED if needed):
- None

## Working Set (files/ids/commands):
- Backend: /backend/design_service.py, /backend/design_agent.py, /backend/design_tools.py, /backend/routers/design.py, /backend/tools.py, /backend/prompts.py
- Frontend: /frontend/design.html, /frontend/css/design.css, /frontend/js/design/*.js, /frontend/js/ui/chat.js
