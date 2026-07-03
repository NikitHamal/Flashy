"""Diagnostics for making Flashy feel reliable before a coding session starts."""
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .runtime import ROOT, health_rows


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    hint: str = ""

    @property
    def status(self) -> str:
        return "ok" if self.ok else "warn"

    def as_row(self) -> dict[str, str]:
        return {"check": self.name, "status": self.status, "detail": self.detail, "hint": self.hint}


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _internet_reachable(timeout: float = 1.5) -> bool:
    """Cheap, non-blocking internet check that never raises."""
    import socket

    try:
        with socket.create_connection(("1.1.1.1", 53), timeout=timeout):
            return True
    except OSError:
        return False
    except Exception:
        return False


def run_diagnostics(workspace: str | None = None, main_port: int = 8000, provider_port: int = 8001) -> list[Check]:
    workspace_path = Path(workspace or os.getcwd()).expanduser().resolve()
    checks: list[Check] = []

    checks.append(
        Check(
            "python",
            sys.version_info >= (3, 10),
            f"{sys.version.split()[0]} at {sys.executable}",
            "Use Python 3.10+" if sys.version_info < (3, 10) else "",
        )
    )

    required_modules = ["fastapi", "uvicorn", "aiohttp", "httpx", "pydantic", "rich", "prompt_toolkit"]
    optional_modules = ["questionary"]
    missing = [module for module in required_modules if not _has_module(module)]
    optional_missing = [module for module in optional_modules if not _has_module(module)]
    checks.append(
        Check(
            "python dependencies",
            not missing,
            "installed" if not missing else "missing: " + ", ".join(missing),
            "Run: python -m pip install -r requirements.txt" if missing else "",
        )
    )
    if optional_missing:
        checks.append(
            Check(
                "optional dependencies",
                True,
                "missing optional: " + ", ".join(optional_missing),
                "Optional. Install for richer interactive prompts.",
            )
        )

    checks.append(
        Check(
            "workspace",
            workspace_path.is_dir(),
            str(workspace_path),
            "Pass --workspace /path/to/project" if not workspace_path.is_dir() else "",
        )
    )

    if workspace_path.is_dir():
        test_file = workspace_path / ".flashy-doctor.tmp"
        try:
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink(missing_ok=True)
            writable = True
        except Exception as exc:
            writable = False
            detail = str(exc)
        else:
            detail = "read/write ok"
        checks.append(Check("workspace write", writable, detail, "Check folder permissions" if not writable else ""))

    checks.append(Check("git", bool(shutil.which("git")), shutil.which("git") or "not found", "Install git" if not shutil.which("git") else ""))
    checks.append(Check("ripgrep", bool(shutil.which("rg")), shutil.which("rg") or "not found", "Optional but improves search speed" if not shutil.which("rg") else ""))
    checks.append(Check("node", bool(shutil.which("node")), shutil.which("node") or "not found", "Optional, needed only for JS/Tauri helpers" if not shutil.which("node") else ""))
    checks.append(Check("internet", _internet_reachable(), "reachable" if _internet_reachable() else "offline", "Many providers need internet" if not _internet_reachable() else ""))

    try:
        from backend.config import CONFIG_FILE, load_config

        config = load_config()
        checks.append(Check("config", Path(CONFIG_FILE).exists(), str(CONFIG_FILE)))
        checks.append(Check("provider", bool(config.get("active_provider")), str(config.get("active_provider", "not set"))))
        checks.append(Check("model", bool(config.get("model")), str(config.get("model", "not set"))))
    except Exception as exc:
        checks.append(Check("config", False, str(exc), "Check backend/config.py and JSON syntax"))

    for row in health_rows(main_port, provider_port):
        checks.append(
            Check(
                f"{row['service']} server",
                row["status"] == "running",
                str(row["details"]),
                f"Start with: flashy {row['service'] if row['service'] != 'main' else 'serve'}" if row["status"] != "running" else "",
            )
        )

    # Exercise the local tool registry without touching the network.
    try:
        from backend.tools import Tools

        tools = Tools(str(workspace_path))
        tool_count = len(tools.get_available_tools())
        checks.append(Check("tool registry", tool_count > 0, f"{tool_count} tools available"))
    except Exception as exc:
        checks.append(Check("tool registry", False, str(exc), "Tool imports are broken"))

    return checks


def summarize(checks: list[Check]) -> dict[str, Any]:
    """Return aggregate counts useful for `--json doctor` consumers."""
    total = len(checks)
    passed = sum(1 for c in checks if c.ok)
    failed = [c for c in checks if not c.ok]
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "issues": [asdict(c) for c in failed],
    }

