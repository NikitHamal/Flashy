"""Runtime helpers for running Flashy from source, PyInstaller, or a desktop shell."""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "Flashy"


def is_frozen() -> bool:
    """Return True when running from a PyInstaller-built executable."""
    return bool(getattr(sys, "frozen", False))


def app_root() -> Path:
    """Directory that contains bundled read-only assets such as frontend/."""
    if hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS")).resolve()
    return Path(__file__).resolve().parent.parent


def resource_path(*parts: str) -> Path:
    return app_root().joinpath(*parts)


def user_data_dir() -> Path:
    """Writable user data directory for config, chats, workspaces, and artifacts."""
    override = os.environ.get("FLASHY_DATA_DIR")
    if override:
        path = Path(override).expanduser()
    elif sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        path = Path(base) / APP_NAME
    elif sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
        path = Path(base) / "flashy"

    path.mkdir(parents=True, exist_ok=True)
    return path


def data_file(*parts: str) -> Path:
    path = user_data_dir().joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def truthy_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}
