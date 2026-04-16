# CONTINUITY.md - Session Continuity Ledger

## Goal (incl. success criteria):
- Enhance Flashy coding agent reliability/power with stronger tools + UI feedback
- Maintain modular files (<800 lines) and production-grade behavior
- Provide intelligent reasoning while maintaining direct access to local file system and Git tools
- Add FREE AI providers (Qwen, DeepInfra) for users without API keys

## Constraints/Assumptions:
- Gemini models are multimodal and capable of complex reasoning
- No TODOs or stub code; production-grade only
- Maintain modular approach (500-800 lines max per file)
- Keep UI/UX consistent with existing app styling

## Key Decisions:
- Stream tool calls to frontend for live updates
- Add robust streaming error handling and message rendering
- Use a plan-based approach for complex coding tasks
- Integrate qwen-code CLI with free providers (Qwen, DeepInfra)

## State:

- Done:
  - Expanded coding agent tools (read/write multiple files, apply patch) and UI tool mapping
  - Cleaned up app by removing legacy Design Agent and related components
  - Added Qwen-Code integration with FREE providers (Qwen, DeepInfra)
  - Created qwen-code modal UI for provider/model selection
  - Added free provider implementations to qwen-code package

- Now:
  - Qwen-Code free mode integration complete.

- Next:
  - Continue enhancing coding agent capabilities.

## Open Questions (UNCONFIRMED if needed):
- None

## Working Set (files/ids/commands):
- Backend: /backend/agent.py, /backend/coding_agent.py, /backend/tools.py, /backend/prompts.py, /backend/routers/qwen_code.py
- Frontend: /frontend/index.html, /frontend/js/app.js, /frontend/js/ui/chat.js, /frontend/js/ui/qwen_code.js
- Qwen-Code: /qwen-code/packages/core/src/core/openaiContentGenerator/provider/qwen_free.ts, /qwen-code/packages/core/src/core/openaiContentGenerator/provider/deepinfra_free.ts