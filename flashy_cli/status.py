"""Lightweight live status helpers (spinner, elapsed timer, status line)."""
from __future__ import annotations

import contextlib
import os
import sys
import threading
import time
from dataclasses import dataclass
from typing import Callable, Iterator, Optional

try:
    from rich.console import Console
    from rich.live import Live
    from rich.spinner import Spinner
    from rich.text import Text

    RICH_AVAILABLE = True
except Exception:  # pragma: no cover
    RICH_AVAILABLE = False


@dataclass
class LiveStatus:
    """A tiny status reporter that updates a single line in the terminal.

    Works in two modes:
    - with Rich: uses Live + Spinner for a smooth animated spinner
    - without Rich: writes a fresh status line to stderr on each update
    """

    message: str = "Thinking"
    style: str = "cyan"
    no_color: bool = False
    enabled: bool = True
    spinner_name: str = "dots"

    def __post_init__(self) -> None:
        self._console = None
        self._live = None
        self._current = self.message
        self._stopped = False
        self._start_ts: float | None = None
        self._last_emit: float = 0.0
        if not self.enabled:
            return
        if RICH_AVAILABLE and not self.no_color:
            self._console = Console(stderr=True, force_terminal=not self.no_color)
        else:
            self._console = None

    def _format_text(self, message: str) -> "Text | str":
        if RICH_AVAILABLE:
            return Text.from_markup(f"[{self.style}]{message}[/{self.style}]")
        return f"  … {message}"

    def update(self, message: str) -> None:
        if not self.enabled or self._stopped:
            return
        self._current = message
        now = time.perf_counter()
        if self._live is not None and RICH_AVAILABLE:
            elapsed = (now - self._start_ts) if self._start_ts else 0.0
            spinner = Spinner(self.spinner_name, text=f" {message}  ", style=self.style)
            try:
                self._live.update(spinner)
            except Exception:
                pass
            self._last_emit = now
        else:
            # Throttle plain-text updates so we don't spam the terminal.
            if now - self._last_emit < 0.05:
                return
            sys.stderr.write(f"\r  … {message}".ljust(80))
            sys.stderr.flush()
            self._last_emit = now

    def set_message(self, message: str) -> None:
        self.update(message)

    def start(self) -> None:
        if not self.enabled or self._stopped:
            return
        self._start_ts = time.perf_counter()
        if RICH_AVAILABLE and self._console is not None:
            spinner = Spinner(self.spinner_name, text=f" {self.message}  ", style=self.style)
            self._live = Live(
                spinner,
                console=self._console,
                refresh_per_second=10,
                transient=True,
            )
            try:
                self._live.__enter__()
            except Exception:
                self._live = None
        else:
            sys.stderr.write(f"\r  … {self.message}".ljust(80))
            sys.stderr.flush()

    def stop(self, final: str | None = None) -> None:
        if self._stopped:
            return
        self._stopped = True
        if self._live is not None:
            try:
                self._live.__exit__(None, None, None)
            except Exception:
                pass
            self._live = None
        if self._console is None and self.enabled:
            sys.stderr.write("\r" + " " * 80 + "\r")
            sys.stderr.flush()
        if final:
            if self._console is not None and RICH_AVAILABLE:
                self._console.print(f"[{self.style}]✓ {final}[/{self.style}]")
            else:
                print(f"  ✓ {final}", file=sys.stderr)

    def __enter__(self) -> "LiveStatus":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()


@contextlib.contextmanager
def ephemeral_line(console, text: str) -> Iterator[None]:
    """Print a line to a console that gets cleared at the end (best-effort)."""
    if RICH_AVAILABLE and console is not None:
        try:
            with console.status(text, spinner="dots"):
                yield
            return
        except Exception:
            pass
    print(text, file=sys.stderr)
    yield


# ---------------------------------------------------------------------------
# Spinner for very short, one-off operations (under 2-3 seconds).
# ---------------------------------------------------------------------------


def quick_spin(console, text: str, duration: float = 0.6, style: str = "cyan") -> None:
    """Run a quick spinner for `duration` seconds, then clear it."""
    if RICH_AVAILABLE and console is not None:
        try:
            with console.status(text, spinner="dots", style=style):
                time.sleep(duration)
            return
        except Exception:
            pass
    sys.stderr.write(f"\r  … {text}".ljust(80))
    sys.stderr.flush()
    time.sleep(duration)
    sys.stderr.write("\r" + " " * 80 + "\r")
    sys.stderr.flush()

