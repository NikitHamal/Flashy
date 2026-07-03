"""Welcome banner shown on chat startup."""
from __future__ import annotations

import os
import shutil
import socket
import time
from pathlib import Path
from typing import Any

try:
    from rich import box
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except Exception:  # pragma: no cover
    RICH_AVAILABLE = False

from .formatting import shorten_path


# A compact, clean Flashy mark designed to render well in monospaced terminals.
LOGO_LINES = [
    "  ███████╗██╗      █████╗ ███████╗██╗  ██╗██╗   ██╗",
    "  ██╔════╝██║     ██╔══██╗██╔════╝██║  ██║╚██╗ ██╔╝",
    "  █████╗  ██║     ███████║███████╗███████║ ╚████╔╝ ",
    "  ██╔══╝  ██║     ██╔══██║╚════██║██╔══██║  ╚██╔╝  ",
    "  ██║     ███████╗██║  ██║███████║██║  ██║   ██║   ",
    "  ╚═╝     ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝   ",
]


def _hostname() -> str:
    try:
        return socket.gethostname().split(".")[0] or "host"
    except Exception:  # pragma: no cover
        return "host"


def _git_branch(workspace: str) -> str:
    """Best-effort git branch detection. Cheap, never raises."""
    try:
        import subprocess

        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=1.0,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        return ""
    return ""


def _python_version() -> str:
    import sys

    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def _session_short(session_id: str) -> str:
    if not session_id:
        return "—"
    return session_id[:8]


def build_welcome(
    workspace: str,
    provider: str,
    model: str,
    reasoning: str,
    mode: str,
    session_id: str,
    *,
    show_logo: bool = True,
    tips: list[str] | None = None,
    extra: dict[str, str] | None = None,
) -> Any:
    """Return a renderable welcome panel. Falls back to a plain string when Rich is missing."""
    home = str(os.path.expanduser("~"))
    ws = shorten_path(workspace, home)
    branch = _git_branch(workspace) if os.path.isdir(workspace) else ""
    py = _python_version()
    host = _hostname()
    s_short = _session_short(session_id)

    default_tips = [
        "Type a task or ask anything. Use / for the command palette.",
        "Paste multi-line code directly; Enter sends, Esc+Enter inserts a newline.",
        "Try /help, /model, /status, /tools, /compact, /save.",
    ]
    tips = tips or default_tips
    extra = extra or {}

    if not RICH_AVAILABLE:
        header = "\n".join(LOGO_LINES) if show_logo else "Flashy"
        body = [
            header,
            f"Workspace  {ws}" + (f"  ({branch})" if branch else ""),
            f"Model      {provider} / {model}",
            f"Reasoning  {reasoning}  ·  mode {mode}",
            f"Session    {s_short}",
            f"Runtime    python {py}  ·  {host}",
            "",
            *(f"  • {tip}" for tip in tips),
        ]
        return "\n".join(body)

    # --- Rich version: a tight two-column grid + a soft tip block ---
    if show_logo:
        logo = Text()
        for i, line in enumerate(LOGO_LINES):
            color = "bright_cyan" if i == 0 else "cyan"
            logo.append(line + "\n", style=color)
    else:
        logo = Text("Flashy", style="bold bright_cyan")

    info = Table.grid(padding=(0, 1))
    info.add_column(style="dim", no_wrap=True)
    info.add_column(style="bold", overflow="fold")
    info.add_row("workspace", ws + (f"  [dim]({branch})[/dim]" if branch else ""))
    info.add_row("model", f"{provider} / {model}")
    info.add_row("reasoning", f"{reasoning}  ·  [dim]{mode}[/dim]")
    info.add_row("session", s_short)
    info.add_row("runtime", f"python {py}  ·  {host}")
    for key, value in extra.items():
        info.add_row(str(key), str(value))

    tip_text = Text()
    tip_text.append("Quick tips\n", style="bold")
    for tip in tips:
        tip_text.append(f"  • {tip}\n", style="dim")

    content = Group(info, Text(""), tip_text)
    header = Text()
    header.append("⚡ Flashy", style="bold bright_cyan")
    header.append("  ·  minimal AI coding terminal", style="dim")

    return Panel(
        content,
        title=header,
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2),
    )


def render_welcome(console, **kwargs) -> None:
    panel = build_welcome(**kwargs)
    if RICH_AVAILABLE:
        console.print(panel)
    else:
        console.print(panel)
        console.print("")


def render_mini_banner(console, workspace: str, provider: str, model: str, *, branch: str = "") -> None:
    """A single-line status header used when re-displaying context."""
    ws = shorten_path(workspace)
    branch_part = f"  [dim]({branch})[/dim]" if branch else ""
    if RICH_AVAILABLE:
        console.print(
            f"[dim]workspace[/dim] [bold]{ws}[/bold]{branch_part}  "
            f"[dim]·[/dim]  [bold cyan]{provider}[/bold cyan] [dim]/[/dim] [bold]{model}[/bold]"
        )
    else:
        plain_branch = f"  ({branch})" if branch else ""
        print(f"workspace {ws}{plain_branch}  ·  {provider} / {model}")


def status_footer(
    console,
    *,
    provider: str,
    model: str,
    reasoning: str,
    mode: str,
    context: str,
    elapsed: float = 0.0,
    width: int | None = None,
) -> None:
    """A dim single-line footer for end-of-turn summaries."""
    parts = [
        f"done in {elapsed:.1f}s" if elapsed else "",
        f"model {provider}/{model}",
        f"ctx {context}",
        f"reasoning {reasoning}",
        f"mode {mode}",
    ]
    parts = [p for p in parts if p]
    if not parts:
        return
    line = " · ".join(parts)
    if RICH_AVAILABLE:
        console.print(f"[dim]{line}[/dim]")
    else:
        print(line)

