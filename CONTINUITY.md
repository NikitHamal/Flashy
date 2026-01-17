# CONTINUITY.md - Session Continuity Ledger

## Goal (incl. success criteria):
- Enhance Flashy AI coding agent to next level (improve reliability, power)
- Add new "Flashy Designs" page with AI-powered design agent
- Canvas app with manual design tools + AI agent integration
- NOT text-to-image generation - customizable, resizable vector graphics/slides
- AI can view its own designs (via internal image upload) and iterate
- Production-grade, fully functional, modular (<800 lines/file)
- Professional UI/UX matching existing solid design

## Constraints/Assumptions:
- Gemini 3 Flash model is multimodal (can see images)
- File upload functionality exists and works
- Must maintain modular approach (500-800 lines max per file)
- No todos, basic implementations - must be production-grade
- Must follow existing UI/UX patterns (dark theme, panels, CSS variables)
- Export functionality must be perfect (PNG, SVG, PDF)
- Chat UI with tool call pills same as coding agent

## Key Decisions:
- Use fabric.js for canvas (industry standard, SVG support, serialization)
- Design agent communicates via JSON tool calls (similar to coding agent)
- Canvas state serializable to JSON for AI manipulation
- Internal screenshot capture for AI iteration feedback
- Separate design-agent.js, design-canvas.js, design-tools.js modules
- design.html as separate page linked in navigation
- Backend: design service similar to gemini_service.py

## State:

- Done:
  - Explored entire codebase thoroughly
  - Understood architecture (FastAPI backend, vanilla JS frontend)
  - Understood AI agent loop, tool calls, streaming
  - Understood UI/UX patterns, CSS approach
  - Created CONTINUITY.md
  - Created backend design service (design_service.py, design_agent.py, design_prompts.py, design_tools.py)
  - Created backend design router with all API endpoints
  - Updated app.py to include design router and service
  - Created design.html with full layout structure
  - Created design.css with professional dark theme styling
  - Created canvas.js module with fabric.js integration
  - Created tools.js for shape creation and manipulation
  - Created properties.js for property panel management
  - Created chat.js for AI agent chat interface
  - Created export.js for PNG, SVG, JSON exports
  - Created app.js main controller
  - Linked design page to main navigation in index.html
  - Added design link styling to main.css

- Now:
  - Test the implementation
  - Polish any remaining issues

- Next:
  - Production deployment ready

## Open Questions (UNCONFIRMED if needed):
- None - proceeding with expert judgment

## Working Set (files/ids/commands):
- Backend: /backend/app.py, /backend/gemini_service.py, /backend/agent.py
- Frontend: /frontend/index.html, /frontend/js/app.js, /frontend/js/ui/*.js
- CSS: /frontend/css/main.css
- New files to create:
  - /frontend/design.html
  - /frontend/js/design/canvas.js
  - /frontend/js/design/tools.js
  - /frontend/js/design/agent.js
  - /frontend/js/design/export.js
  - /frontend/js/design/ui.js
  - /frontend/js/design/app.js
  - /frontend/css/design.css
  - /backend/design_service.py
  - /backend/design_agent.py
  - /backend/design_prompts.py
