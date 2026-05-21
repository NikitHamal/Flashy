# Flashy production pass

## What changed

- Repaired the workspace layout so Explorer, Git, Plan, and Memory are mutually exclusive right-docked utility panels instead of competing with the left project rail.
- Added a dedicated **Server Center** screen with start, stop, restart, status, endpoint, PID, uptime, health, provider request telemetry, and provider logs.
- Added backend process control APIs under `/server/*` and a managed provider-server launcher for `python run.py server` / packaged desktop usage.
- Added provider request telemetry in `backend/server_app.py` so requests and response status/duration appear in the Server Center.
- Added realtime refresh paths: websocket stream completion now refreshes state, explorer, git, plan, and memory; visible workspace surfaces also refresh on interval and window focus.
- Tightened frontend safety by escaping dynamic workspace/session/file/git strings before rendering.
- Reworked typography and surface treatment with a stronger Sora / IBM Plex Sans / JetBrains Mono design system.
- Fixed the broken `reorder_html.py` utility.
- Removed checked-in `__pycache__` artifacts from the packaged source.
- Updated desktop packaging to produce an installable Windows NSIS setup with desktop/start-menu shortcuts and a custom icon.
- Reduced avoidable package bloat by removing the portable Windows target, enabling maximum installer compression, keeping Electron `asar`, hiding the backend console window, stripping non-Windows sidecars, and cleaning cache artifacts in the backend build script.

## Build commands

```bash
npm install --prefix desktop
python -m pip install -r requirements-desktop.txt
npm run desktop:build-backend
npm run desktop:dist
```

The Windows release artifact is now expected to be an installer named similar to:

```text
Flashy-Setup-0.1.0-x64.exe
```

## Server Center endpoints

```text
GET  /server/status
POST /server/start
POST /server/stop
POST /server/restart
GET  /server/logs
GET  /server/events
```

The provider server still exposes its OpenAI-compatible routes through `backend.server_app`, but can now be managed from inside Flashy.
