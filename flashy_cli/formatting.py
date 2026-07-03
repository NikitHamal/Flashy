"""Lightweight markdown rendering for assistant output.

We keep this small and dependency-free where possible, falling back to plain text
when Rich isn't available. We render:
- **bold**, *italic*, `code`
- fenced code blocks with language hints (syntax highlighted when possible)
- simple bullet lists
- blockquotes
- inline links
- horizontal rules
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Iterable, List, Tuple

try:
    from rich.console import Console, Group
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.rule import Rule
    from rich.table import Table
    from rich.text import Text
    from rich.box import SIMPLE_HEAVY, ROUNDED

    RICH_AVAILABLE = True
except Exception:  # pragma: no cover
    RICH_AVAILABLE = False


@dataclass
class RenderOptions:
    width: int = 100
    code_theme: str = "monokai"
    show_line_numbers: bool = False
    inline_only: bool = False  # when True, render inline markdown only (no panels)


# Matches a fenced code block. We use re.MULTILINE to handle multi-line blocks.
_FENCE_RE = re.compile(r"```([a-zA-Z0-9_+\-]*)\n(.*?)\n```", re.DOTALL)


def _strip_fences_for_plain(text: str) -> str:
    """Make markdown look reasonable even without a renderer."""
    text = _FENCE_RE.sub(lambda m: f"\n[code:{m.group(1) or 'text'}]\n{m.group(2)}\n[/code]\n", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text


def render_markdown(console, text: str, options: RenderOptions | None = None) -> None:
    """Render markdown text through Rich if available, else plain."""
    options = options or RenderOptions()
    if RICH_AVAILABLE and not options.inline_only:
        try:
            console.print(Markdown(text, code_theme=options.code_theme))
            return
        except Exception:
            pass
    if RICH_AVAILABLE:
        # Inline path: just print the rendered markdown without code block panels.
        try:
            md = Markdown(text, code_theme=options.code_theme, inline_code_lexer="text")
            console.print(md)
            return
        except Exception:
            pass
    console.print(_strip_fences_for_plain(text))


def render_code(console, code: str, language: str = "") -> None:
    """Render a fenced code block with syntax highlighting when possible."""
    if RICH_AVAILABLE:
        try:
            from rich.syntax import Syntax

            console.print(
                Syntax(
                    code,
                    language or "text",
                    theme="monokai",
                    line_numbers=False,
                    word_wrap=True,
                )
            )
            return
        except Exception:
            pass
    fence = "─" * 3
    lang = f" ({language})" if language else ""
    console.print(f"{fence} code{lang} {fence}")
    console.print(code.rstrip("\n"))
    console.print(fence * (10 + len(lang)))


def render_diff(console, before: str, after: str, *, path: str = "", max_lines: int = 80) -> None:
    """Render a unified-ish diff for an edit using Rich when possible."""
    import difflib

    diff = list(
        difflib.unified_diff(
            before.splitlines(keepends=False),
            after.splitlines(keepends=False),
            fromfile=f"a/{path}" if path else "a",
            tofile=f"b/{path}" if path else "b",
            n=2,
            lineterm="",
        )
    )
    if not diff:
        console.print("[dim]no textual change[/dim]")
        return

    if RICH_AVAILABLE:
        try:
            from rich.syntax import Syntax

            console.print(
                Syntax(
                    "\n".join(diff[: max_lines * 2]),
                    "diff",
                    theme="monokai",
                    line_numbers=False,
                    word_wrap=True,
                )
            )
            if len(diff) > max_lines * 2:
                console.print(f"[dim]… {len(diff) - max_lines * 2} more diff lines[/dim]")
            return
        except Exception:
            pass

    for line in diff[: max_lines * 2]:
        if line.startswith("+") and not line.startswith("+++"):
            console.print(f"[green]{line}[/green]" if RICH_AVAILABLE else line)
        elif line.startswith("-") and not line.startswith("---"):
            console.print(f"[red]{line}[/red]" if RICH_AVAILABLE else line)
        elif line.startswith("@@"):
            console.print(f"[cyan]{line}[/cyan]" if RICH_AVAILABLE else line)
        else:
            console.print(line)


def render_kv_table(console, title: str, rows: List[Tuple[str, str]], *, style: str = "cyan") -> None:
    if RICH_AVAILABLE:
        table = Table(title=title, box=SIMPLE_HEAVY, border_style=style, show_lines=False)
        table.add_column("Key", style="bold")
        table.add_column("Value")
        for key, value in rows:
            table.add_row(str(key), str(value))
        console.print(table)
        return
    console.print(f"\n{title}")
    width = max(len(k) for k, _ in rows) if rows else 8
    for key, value in rows:
        console.print(f"  {key.ljust(width)}  {value}")


def render_help(console, groups: List[Tuple[str, List[Tuple[str, str]]]]) -> None:
    """Render grouped help, e.g. each section with a list of (cmd, desc) rows."""
    if RICH_AVAILABLE:
        from rich.console import Group as _Group

        renderables: list = []
        for title, items in groups:
            t = Table(box=SIMPLE_HEAVY, show_header=False, border_style="cyan", expand=True)
            t.add_column("Command", style="bold cyan", no_wrap=True)
            t.add_column("Action")
            for cmd, desc in items:
                t.add_row(cmd, desc)
            renderables.append(Panel(t, title=title, border_style="cyan", box=ROUNDED, padding=(0, 1)))
        console.print(_Group(*renderables))
        return
    for title, items in groups:
        console.print(f"\n{title}")
        width = max(len(c) for c, _ in items) if items else 8
        for cmd, desc in items:
            console.print(f"  {cmd.ljust(width)}  {desc}")


def shorten_path(path: str, home: str | None = None) -> str:
    if not path:
        return ""
    if home is None:
        try:
            home = str(__import__("pathlib").Path.home())
        except Exception:
            home = ""
    if home and path == home:
        return "~"
    if home and path.startswith(home + __import__("os").sep):
        return "~" + path[len(home) :]
    return path


def truncate(text: str, max_len: int = 120) -> str:
    s = str(text).replace("\r", " ").replace("\n", " ").strip()
    if len(s) <= max_len:
        return s
    keep = max(12, (max_len - 3) // 2)
    return f"{s[:keep]}…{s[-keep:]}"


def count_lines(text: str) -> int:
    if not text:
        return 0
    return len(text.splitlines()) or 1


# ---------------------------------------------------------------------------
# @file attachment parsing
# ---------------------------------------------------------------------------

ATTACH_RE = re.compile(r"(?:^|\s)@(?P<path>[A-Za-z0-9_./~\\:+-]+)")


def extract_attachments(message: str, workspace: str) -> Tuple[str, List[Tuple[str, str]]]:
    """Find @file tokens in a user message and return (cleaned_message, [(path, contents), ...]).

    The cleaned message keeps the tokens so the LLM still sees them as hints, but we
    also attach the file contents as a separate "context" payload for the model.
    Files that don't exist or are unreadable are silently skipped.
    """
    if not message:
        return message, []
    from pathlib import Path

    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    for match in ATTACH_RE.finditer(message):
        raw = match.group("path")
        if not raw:
            continue
        # Resolve against workspace, with a couple of fallbacks.
        candidates = []
        if os.path.isabs(raw):
            candidates.append(Path(raw))
        else:
            candidates.append(Path(workspace) / raw)
            candidates.append(Path(workspace) / raw.lstrip("/"))
        for cand in candidates:
            try:
                resolved = cand.resolve()
            except Exception:
                continue
            if not resolved.is_file():
                continue
            key = str(resolved).lower()
            if key in seen:
                continue
            seen.add(key)
            try:
                if resolved.stat().st_size > 256_000:
                    found.append((str(resolved), "<file larger than 256KB, skipped>"))
                else:
                    found.append((str(resolved), resolved.read_text(encoding="utf-8", errors="replace")))
            except Exception:
                continue
            break
    return message, found


def render_attachment_summary(console, attachments: List[Tuple[str, str]]) -> None:
    """Render a compact, dim summary of attached files."""
    if not attachments:
        return
    from .formatting import shorten_path, count_lines

    if RICH_AVAILABLE:
        console.print(f"[dim]attached {len(attachments)} file(s):[/dim]")
        for path, content in attachments:
            short = shorten_path(path)
            preview_lines = count_lines(content)
            console.print(f"[dim]  • {short}  ({preview_lines} lines)[/dim]")
    else:
        print(f"attached {len(attachments)} file(s):")
        for path, content in attachments:
            short = shorten_path(path)
            preview_lines = count_lines(content)
            print(f"  - {short}  ({preview_lines} lines)")


def render_key_value(console, pairs: Iterable[Tuple[str, str]], *, title: str = "", style: str = "cyan") -> None:
    rows = [(k, v) for k, v in pairs]
    if not rows:
        return
    if title:
        render_kv_table(console, title, rows, style=style)
        return
    render_kv_table(console, "details", rows, style=style)


def format_size(num_bytes: int) -> str:
    """Format a byte count as a human-readable string."""
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    idx = 0
    while size >= 1024.0 and idx < len(units) - 1:
        size /= 1024.0
        idx += 1
    if units[idx] == "B":
        return f"{int(size)}{units[idx]}"
    return f"{size:.1f}{units[idx]}"

