# Flashy Desktop Audit Report

## Executive summary

Flashy already had the right foundation for a desktop app: a FastAPI HTTP/WebSocket backend and a static frontend that talks to `window.location.origin`. The missing piece was not a rewrite; it was a native shell, deterministic startup, bundling, localhost hardening, and CI packaging.

This update adds an Electron desktop shell that launches the existing FastAPI app as a sidecar backend, injects per-launch localhost authentication, stores mutable data in the desktop user-data directory, and builds installable artifacts through GitHub Actions.

## What was added

### Desktop shell

- Added `desktop/` as a standalone Electron app.
- Electron starts the backend on a random `127.0.0.1` port.
- Electron generates a random UUID password on every launch.
- Electron injects Basic Auth into HTTP and WebSocket requests to the local backend.
- Electron exposes safe IPC helpers for folder picking, opening paths, revealing files, and restarting the backend.
- Electron logs backend stdout/stderr to a user-visible log file.

### Backend desktop hardening

- Added `/global/health` and `/healthz` readiness probes.
- Added environment-configurable host, port, and reload mode.
- Changed desktop mode from `0.0.0.0:8000` to `127.0.0.1:<random>`.
- Added optional Basic Auth middleware for desktop mode.
- Added WebSocket auth support via Authorization header or desktop token query parameter.
- Replaced hardcoded `frontend/...` paths with bundled resource paths.
- Moved desktop runtime config and data writes to a writable user data folder.
- Fixed the provider server host/port/reload settings to be env-driven.
- Fixed the Qwen bridge API URL to respect the runtime port.

### Packaging and CI

- Added PyInstaller sidecar build entrypoint and spec.
- Added `requirements-desktop.txt`.
- Added Electron Builder configuration for macOS, Windows, and Linux.
- Added `.github/workflows/desktop-release.yml` for tagged and manual releases.
- Added root npm convenience scripts.
- Added desktop documentation.

## Findings

### 1. Server was unsafe for desktop use

Before this update, the main app ran on `0.0.0.0:8000` with CORS wildcard and no authentication. Because the backend exposes workspace, file, git, terminal, and agent tooling, that is too permissive for a local desktop app. The desktop shell now forces `127.0.0.1`, a random port, and per-launch auth.

### 2. Runtime paths were not bundle-safe

The backend used relative paths such as `frontend/index.html`, `config.json`, and `data/chats.json`. These work from a source checkout but fail or write into the wrong place after packaging. The new `backend/desktop_runtime.py` centralizes resource and user-data paths.

### 3. Startup was not shell-friendly

The backend had no stable readiness endpoint and always used reload mode when run as `__main__`. Desktop shells need deterministic startup, no reload child process, and a health endpoint. This update adds those.

### 4. Native folder picking should belong to the shell

The previous folder picker launched a Python picker process. That can be fragile after bundling. The desktop shell now exposes native folder selection via IPC while preserving the old backend picker for browser/source use.

### 5. Packaging was absent

There was no desktop package manifest, no backend sidecar build, and no release workflow. This update adds all three.

## Remaining risks and next steps

### Agent usefulness is still a product/agent issue

The desktop shell makes Flashy installable and safer to run, but it does not by itself make the autonomous coding agent more capable. The next iteration should focus on benchmarkable agent loops: repository indexing, robust patch planning, deterministic tool execution, test-running, rollback, and evaluation traces.

### Qwen Code assets are not included in this zip

`backend/qwencode_bridge.py` expects `qwen-code/dist/cli.js`, but the uploaded project does not include a `qwen-code/` directory. The desktop app will still run, but Qwen Code bridge functionality will require that asset to be vendored, installed, or downloaded in CI.

### Signing is not configured

The workflow builds unsigned artifacts. For public release, add Apple notarization and Windows code signing secrets.

### PyInstaller hidden imports may need one CI pass

The spec collects all `backend` submodules and bundles `frontend/`, which is the right baseline. Provider libraries that rely on dynamic native dependencies can still require extra PyInstaller hooks after the first full CI run.

### API auth is local-only hardening, not multi-user security

The desktop authentication protects a local sidecar from casual cross-origin access. It is not designed to make Flashy a remote multi-user server. Do not expose this backend on a LAN or public network without a separate security review.
