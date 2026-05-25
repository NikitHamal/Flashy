"""PyInstaller entrypoint for the Flashy desktop backend sidecar."""
from __future__ import annotations

import os

import uvicorn

from backend.desktop_runtime import app_root


if __name__ == "__main__":
    # A few legacy modules still resolve bundled read-only assets relative to CWD.
    os.chdir(app_root())

    mode = os.environ.get("FLASHY_BACKEND_MODE", "flashy").strip().lower()
    if mode in {"server", "provider", "provider_server"}:
        uvicorn.run(
            "backend.server_app:app",
            host=os.environ.get("FLASHY_PROVIDER_HOST", "127.0.0.1"),
            port=int(os.environ.get("FLASHY_PROVIDER_PORT", "8001")),
            reload=False,
            access_log=True,
        )
    else:
        uvicorn.run(
            "backend.app:app",
            host=os.environ.get("FLASHY_HOST", "127.0.0.1"),
            port=int(os.environ.get("FLASHY_PORT", "8000")),
            reload=False,
            access_log=os.environ.get("FLASHY_ACCESS_LOG", "0").lower() in {"1", "true", "yes"},
        )
