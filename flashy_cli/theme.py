"""Theme and color system for Flashy.

Centralizes colors so the whole CLI looks consistent and is easy to recolor.
Respects NO_COLOR and the FLASHY_THEME env var.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

try:
    from rich.theme import Theme as RichTheme

    RICH_AVAILABLE = True
except Exception:  # pragma: no cover
    RICH_AVAILABLE = False


@dataclass(frozen=True)
class Palette:
    """Named color slots used across the CLI."""

    accent: str = "cyan"
    accent_alt: str = "magenta"
    user: str = "green"
    agent: str = "cyan"
    rule: str = "blue"
    dim: str = "grey50"
    error: str = "red"
    warn: str = "yellow"
    ok: str = "green"
    info: str = "cyan"
    tool: str = "cyan"
    tool_path: str = "white"
    tool_diff_add: str = "green"
    tool_diff_remove: str = "red"
    prompt_name: str = "bold cyan"
    prompt_arrow: str = "cyan"
    code_fence: str = "grey50"
    banner_border: str = "cyan"
    banner_title: str = "bold cyan"


THEMES: dict[str, Palette] = {
    "default": Palette(),
    "mono": Palette(
        accent="white",
        accent_alt="white",
        user="white",
        agent="white",
        rule="white",
        dim="grey70",
        error="bright_red",
        warn="bright_yellow",
        ok="white",
        info="white",
        tool="white",
        tool_path="white",
        tool_diff_add="white",
        tool_diff_remove="grey70",
        prompt_name="bold white",
        prompt_arrow="white",
        code_fence="grey70",
        banner_border="white",
        banner_title="bold white",
    ),
    "solarized": Palette(
        accent="yellow",
        accent_alt="cyan",
        user="green",
        agent="cyan",
        rule="blue",
        dim="grey50",
        error="red",
        warn="yellow",
        ok="green",
        info="cyan",
        tool="yellow",
        tool_path="white",
        tool_diff_add="green",
        tool_diff_remove="red",
        prompt_name="bold yellow",
        prompt_arrow="yellow",
        code_fence="grey50",
        banner_border="yellow",
        banner_title="bold yellow",
    ),
    "dracula": Palette(
        accent="magenta",
        accent_alt="cyan",
        user="green",
        agent="magenta",
        rule="blue",
        dim="grey50",
        error="red",
        warn="yellow",
        ok="green",
        info="cyan",
        tool="magenta",
        tool_path="white",
        tool_diff_add="green",
        tool_diff_remove="red",
        prompt_name="bold magenta",
        prompt_arrow="magenta",
        code_fence="grey50",
        banner_border="magenta",
        banner_title="bold magenta",
    ),
}

THEME_NAMES = list(THEMES.keys())


def wants_color() -> bool:
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("FLASHY_NO_COLOR") is not None:
        return False
    return True


def current_palette() -> Palette:
    name = os.environ.get("FLASHY_THEME", "").lower()
    if not name:
        # Fall back to the persisted config (best-effort, never raises).
        try:
            from backend.config import load_config as _load

            name = str((_load() or {}).get("theme", "") or "").lower()
        except Exception:
            name = ""
    return THEMES.get(name or "default", THEMES["default"])


def rich_theme() -> Any:
    """Return a Rich Theme object for the active palette, or None if Rich is missing."""
    if not RICH_AVAILABLE:
        return None
    p = current_palette()
    return RichTheme(
        {
            "flashy.accent": p.accent,
            "flashy.accent_alt": p.accent_alt,
            "flashy.user": p.user,
            "flashy.agent": p.agent,
            "flashy.dim": p.dim,
            "flashy.error": p.error,
            "flashy.warn": p.warn,
            "flashy.ok": p.ok,
            "flashy.info": p.info,
            "flashy.tool": p.tool,
            "flashy.tool_path": p.tool_path,
            "flashy.tool_diff_add": p.tool_diff_add,
            "flashy.tool_diff_remove": p.tool_diff_remove,
            "flashy.prompt_name": p.prompt_name,
            "flashy.prompt_arrow": p.prompt_arrow,
            "flashy.code_fence": p.code_fence,
            "flashy.banner_border": p.banner_border,
            "flashy.banner_title": p.banner_title,
            "repr.number": p.accent_alt,
            "repr.string": p.ok,
            "repr.bool": p.warn,
            "repr.none": p.dim,
        }
    )
