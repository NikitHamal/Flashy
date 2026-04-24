# Flashy Desktop

Flashy now follows the same high-level pattern as OpenCode Desktop: a native shell launches the existing HTTP/WebSocket backend as a local sidecar and renders the existing web UI in a desktop webview.

## Architecture

```text
┌─────────────────────────────────────┐
│ Electron native shell               │
│ - Creates a random localhost port   │
│ - Generates per-launch Basic Auth   │
│ - Spawns Flashy backend sidecar     │
│ - Owns menus, dialogs, logs         │
└──────────┬──────────────────────────┘
           │ HTTP + WebSocket on 127.0.0.1
           │ Basic Auth + WS desktop token
┌──────────▼──────────────────────────┐
│ Flashy FastAPI backend              │
│ - Existing agent/chat routes         │
│ - Existing workspace/git/tools APIs  │
│ - Static frontend serving            │
└──────────┬──────────────────────────┘
           │ relative REST/WS calls
┌──────────▼──────────────────────────┐
│ Existing Flashy frontend             │
│ - Rendered inside BrowserWindow      │
└─────────────────────────────────────┘
```

## Important files

- `desktop/src/main.js` — Electron main process; starts/stops the backend, injects auth, creates menus, opens logs.
- `desktop/src/preload.js` — safe desktop bridge exposed as `window.flashyDesktop`.
- `desktop/pyinstaller/backend_entry.py` — PyInstaller entrypoint for the backend sidecar.
- `desktop/pyinstaller/flashy-backend.spec` — backend bundling spec, including `frontend/` assets.
- `.github/workflows/desktop-release.yml` — builds macOS, Windows, and Linux desktop artifacts.
- `backend/desktop_runtime.py` — shared runtime helper for bundled asset paths and user data paths.

## Run in development

From the repository root:

```bash
python -m pip install -r requirements.txt
npm install --prefix desktop
npm run desktop:dev
```

Development mode starts `python -m backend.app` from the repo root and loads the UI from a random `127.0.0.1` port.

## Build a local desktop app

```bash
python -m pip install -r requirements-desktop.txt
npm install --prefix desktop
npm run desktop:build-backend
npm run desktop:dist
```

Artifacts are written to `desktop/release/`.

## Release from GitHub Actions

Push a tag such as:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The workflow builds:

- macOS ARM64 and x64: `.dmg` and `.zip`
- Windows x64: `.exe` installer and portable executable
- Linux x64: `.AppImage` and `.deb`

## Optional production signing

The workflow is unsigned by default, which is suitable for private/internal use. For public distribution, add signing in the platform-specific Electron Builder configuration and configure these secrets:

- macOS: Apple Developer ID certificate, password, Team ID, and notarization credentials.
- Windows: either a PFX signing certificate or Azure Trusted Signing configuration.

## Runtime data

In desktop mode, Flashy writes mutable data outside the read-only app bundle:

- Config: `${userData}/backend-data/config.json`
- Chats/workspaces/computer-use data: `${userData}/backend-data/data/`
- Backend logs: `${userData}/logs/backend.log`

The exact `${userData}` path is shown in the **Backend → Open Backend Log** menu and returned by `window.flashyDesktop.getContext()`.
