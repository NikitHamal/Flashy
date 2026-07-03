"""Small UI helpers for a fast, dependency-light command line."""
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

try:  # Rich is optional at runtime but listed in setup.py for packaged installs.
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.rule import Rule
    from rich.text import Text
    from rich import box

    RICH_AVAILABLE = True
except Exception:  # pragma: no cover - intentionally graceful fallback
    Console = None  # type: ignore
    Table = None  # type: ignore
    Panel = None  # type: ignore
    box = None  # type: ignore
    RICH_AVAILABLE = False


@dataclass
class UI:
    """Output adapter with JSON mode and Rich fallback support."""

    json_mode: bool = False
    no_color: bool = False
    quiet: bool = False

    def __post_init__(self) -> None:
        force_terminal = None if not self.no_color else False
        self.console = Console(force_terminal=force_terminal) if RICH_AVAILABLE else None

    # ---- primitives ------------------------------------------------------
    def print(self, message: str = "", *, style: str | None = None) -> None:
        if self.quiet:
            return
        if self.console and not self.json_mode:
            self.console.print(message, style=style)
        else:
            print(message)

    def error(self, message: str) -> None:
        if self.console and not self.json_mode:
            self.console.print(f"[bold red]Error:[/bold red] {message}", file=sys.stderr)
        else:
            print(f"Error: {message}", file=sys.stderr)

    def success(self, message: str) -> None:
        self.print(message, style="green")

    def info(self, message: str) -> None:
        self.print(message, style="cyan")

    def warn(self, message: str) -> None:
        self.print(message, style="yellow")

    def hint(self, message: str) -> None:
        if self.console and not self.json_mode:
            self.console.print(f"[dim]hint:[/dim] {message}")
        else:
            print(f"hint: {message}")

    def rule(self, title: str = "", *, style: str = "blue") -> None:
        if self.quiet or self.json_mode:
            return
        if RICH_AVAILABLE and self.console is not None:
            self.console.rule(title, style=style)
        else:
            bar = "─" * max(8, (40 - len(title)) // 2)
            print(f"{bar} {title} {bar}".rstrip())

    def json(self, data: Any) -> None:
        # Use ASCII-safe JSON on terminals that can't render unicode so subprocess
        # capture on Windows consoles doesn't crash. Rich's console handles unicode fine.
        try:
            print(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True))
        except UnicodeEncodeError:
            print(json.dumps(data, indent=2, ensure_ascii=True, sort_keys=True))

    # ---- composite widgets ----------------------------------------------
    def panel(self, title: str, body: str, *, style: str = "cyan", padding=(1, 2)) -> None:
        if self.json_mode or self.quiet:
            return
        if self.console:
            self.console.print(Panel(body, title=title, border_style=style, padding=padding))
        else:
            print(f"\n{title}\n{'=' * len(title)}\n{body}\n")

    def table(self, title: str, rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> None:
        if self.json_mode:
            self.json(list(rows))
            return
        if not rows:
            self.print("No rows.")
            return
        if self.console:
            table = Table(title=title, box=box.SIMPLE_HEAVY if box else None, header_style="bold")
            for column in columns:
                table.add_column(column.replace("_", " ").title())
            for row in rows:
                table.add_row(*[str(row.get(column, "")) for column in columns])
            self.console.print(table)
            return

        widths = {col: max(len(col), *(len(str(row.get(col, ""))) for row in rows)) for col in columns}
        header = "  ".join(col.ljust(widths[col]) for col in columns)
        sep = "  ".join("-" * widths[col] for col in columns)
        print(title)
        print(header)
        print(sep)
        for row in rows:
            print("  ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns))

    # ---- prompts ---------------------------------------------------------
    def ask(self, question: str, *, default: str = "") -> str:
        if self.console and not self.no_color:
            try:
                return self.console.input(f"[bold cyan]?[/bold cyan] {question} ")
            except Exception:
                pass
        suffix = f" [{default}]" if default else ""
        try:
            return input(f"? {question}{suffix}: ").strip() or default
        except (EOFError, KeyboardInterrupt):
            return default

    def confirm(self, question: str, *, default: bool = False) -> bool:
        suffix = " [Y/n]" if default else " [y/N]"
        if self.console and not self.no_color:
            try:
                reply = self.console.input(f"[bold yellow]![/bold yellow] {question}{suffix} ").strip().lower()
            except Exception:
                return default
        else:
            try:
                reply = input(f"! {question}{suffix}: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                return default
        if not reply:
            return default
        return reply in {"y", "yes"}


def wants_color() -> bool:
    return os.environ.get("NO_COLOR") is None

