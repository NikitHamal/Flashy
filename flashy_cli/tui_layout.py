"""Fullscreen TUI layout for Flashy CLI.

Implements a split-pane terminal UI:
  ┌──────────────────────────────────┐
  │  Scrollable chat output (top)    │
  │  ...                             │
  ├──────────────────────────────────┤  ← separator
  │  flashy ❯ [user types here]      │  ← STICKY INPUT (bottom)
  ├──────────────────────────────────┤
  │  📁 workspace │ 🤖 model │ ⚡ ctx│  ← status bar
  └──────────────────────────────────┘

The key difference from a plain PromptSession:
  - Output goes into a TextArea / log buffer that scrolls independently
  - The input field is pinned to the bottom via HSplit layout
  - The status bar is always visible below the input
  - Ctrl+C clears the input line; second Ctrl+C exits
"""
from __future__ import annotations

import asyncio
import sys
import io
from pathlib import Path
from typing import Any, Callable, Dict, Optional

# --------------------------------------------------------------------------- #
# Prompt-toolkit imports (all optional — plain fallback if missing)            #
# --------------------------------------------------------------------------- #
try:
    from prompt_toolkit import Application
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.completion import Completer
    from prompt_toolkit.document import Document
    from prompt_toolkit.filters import Condition
    from prompt_toolkit.formatted_text import HTML, AnyFormattedText
    from prompt_toolkit.history import FileHistory, InMemoryHistory
    from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
    from prompt_toolkit.key_binding.bindings.focus import focus_next
    from prompt_toolkit.layout.containers import (
        ConditionalContainer,
        Float,
        FloatContainer,
        HSplit,
        VSplit,
        Window,
        WindowAlign,
    )
    from prompt_toolkit.layout.controls import (
        BufferControl,
        FormattedTextControl,
    )
    from prompt_toolkit.layout.dimension import Dimension as D
    from prompt_toolkit.layout.layout import Layout
    from prompt_toolkit.layout.menus import CompletionsMenu
    from prompt_toolkit.layout.processors import (
        BeforeInput,
        HighlightSearchProcessor,
    )
    from prompt_toolkit.styles import Style
    from prompt_toolkit.widgets import SearchToolbar, TextArea

    _PT_OK = True
except ImportError:
    _PT_OK = False


# --------------------------------------------------------------------------- #
# Git helpers (lightweight, no subprocess dependencies beyond stdlib)          #
# --------------------------------------------------------------------------- #
def _git_branch(workspace: str) -> str:
    try:
        import subprocess
        r = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=workspace, capture_output=True, text=True, timeout=0.8,
        )
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def _git_dirty(workspace: str) -> bool:
    try:
        import subprocess
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=workspace, capture_output=True, text=True, timeout=0.8,
        )
        return bool(r.stdout.strip()) if r.returncode == 0 else False
    except Exception:
        return False


# --------------------------------------------------------------------------- #
# FlashyTUI — the split-pane application                                       #
# --------------------------------------------------------------------------- #
class FlashyTUI:
    """Fullscreen TUI with scrollable output pane and sticky bottom input bar.

    Usage::

        tui = FlashyTUI(...)
        await tui.run_async()        # runs the event loop
        # OR inside an existing loop:
        text = await tui.prompt_once(meta)   # returns user input once

    The caller writes to ``tui.output_buffer`` or calls ``tui.write(text)``
    to add text to the scrollable output region.
    """

    def __init__(
        self,
        *,
        workspace: str,
        provider: str,
        model: str,
        reasoning: str,
        history_path: str = "",
        completer: Optional[Completer] = None,
        palette: Any = None,
        get_usage: Optional[Callable[[], str]] = None,
    ):
        self.workspace = workspace
        self.provider = provider
        self.model = model
        self.reasoning = reasoning
        self.get_usage = get_usage or (lambda: "")
        self.palette = palette
        self._completer = completer
        self._history_path = history_path

        # Shared asyncio Future that resolves when user presses Enter
        self._answer_future: Optional[asyncio.Future] = None
        self._app: Optional[Application] = None
        self._output_lines: list[str] = []
        self._output_control: Optional[FormattedTextControl] = None

        if _PT_OK:
            self._build()

    # ---------------------------------------------------------------------- #
    # Public API                                                               #
    # ---------------------------------------------------------------------- #

    def write(self, text: str) -> None:
        """Append plain text to the scrollable output region."""
        self._output_lines.append(text)
        if self._output_control:
            self._output_control.text = self._get_output_text()

    def write_ansi(self, text: str) -> None:
        """Append ANSI-colored text to the scrollable output region."""
        # For simplicity, strip ANSI codes for the PT pane; Rich renders to
        # stdout directly. Just keep a text copy so history is preserved.
        self.write(text)

    async def prompt_once(
        self,
        *,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        reasoning: Optional[str] = None,
    ) -> str:
        """Show the TUI, wait for the user to type and press Enter.

        Returns the submitted text (stripped). Raises KeyboardInterrupt if
        Ctrl+C was pressed on an empty line.
        """
        if not _PT_OK or self._app is None:
            raise RuntimeError("prompt_toolkit not available")

        # Update live metadata in case caller changed provider/model
        if provider:
            self.provider = provider
        if model:
            self.model = model
        if reasoning:
            self.reasoning = reasoning

        loop = asyncio.get_event_loop()
        self._answer_future = loop.create_future()

        # Clear the input buffer so the user starts fresh
        self._input_buffer.reset()

        try:
            await self._app.run_async()
        except KeyboardInterrupt:
            raise
        except Exception:
            pass

        if self._answer_future.done():
            result = self._answer_future.result()
            if result is None:
                raise KeyboardInterrupt
            return result
        raise KeyboardInterrupt

    # ---------------------------------------------------------------------- #
    # Layout construction                                                      #
    # ---------------------------------------------------------------------- #

    def _build(self) -> None:
        """Construct the prompt_toolkit Application with split layout."""

        # ------------------------------------------------------------------ #
        # Output pane (scrollable)                                             #
        # ------------------------------------------------------------------ #
        self._output_control = FormattedTextControl(
            text=self._get_output_text,
            focusable=False,
        )
        output_window = Window(
            content=self._output_control,
            wrap_lines=True,
            dont_extend_height=False,
        )

        # ------------------------------------------------------------------ #
        # Input buffer + window                                                #
        # ------------------------------------------------------------------ #
        history = (
            FileHistory(self._history_path)
            if self._history_path
            else InMemoryHistory()
        )

        # Gate autocomplete with a Condition so we can suppress re-triggering
        # right after the user presses Enter to accept a completion.
        self._suppress_ac = False

        @Condition
        def _may_autocomplete() -> bool:
            return not self._suppress_ac

        self._input_buffer = Buffer(
            name="input",
            multiline=True,
            history=history,
            completer=self._completer,
            complete_while_typing=_may_autocomplete,
            auto_suggest=AutoSuggestFromHistory(),
        )

        # Prompt text rendered inline before the user cursor
        def _prompt_text() -> AnyFormattedText:
            accent = _color(self.palette, "accent", "#88c0d0")
            return HTML(f"<prompt.name>flashy</prompt.name> <prompt.arrow>❯</prompt.arrow> ")

        input_window = Window(
            content=BufferControl(
                buffer=self._input_buffer,
                focusable=True,
                input_processors=[BeforeInput(_prompt_text)],
            ),
            height=D(min=1, max=5),
            wrap_lines=True,
        )

        # ------------------------------------------------------------------ #
        # Separator line                                                        #
        # ------------------------------------------------------------------ #
        sep_text = "─" * 200  # will be clipped to terminal width
        separator = Window(
            content=FormattedTextControl(
                HTML(f"<separator>{sep_text}</separator>")
            ),
            height=1,
            dont_extend_height=True,
        )

        # ------------------------------------------------------------------ #
        # Status bar (always at bottom)                                        #
        # ------------------------------------------------------------------ #
        status_window = Window(
            content=FormattedTextControl(self._get_status_text),
            height=1,
            dont_extend_height=True,
            style="class:status-bar",
        )

        # ------------------------------------------------------------------ #
        # Completions float (drops up from the input window)                  #
        # ------------------------------------------------------------------ #
        completions_float = Float(
            xcursor=True,
            ycursor=True,
            content=CompletionsMenu(max_height=12, scroll_offset=2),
        )

        # ------------------------------------------------------------------ #
        # Full layout: output / separator / input / statusbar                 #
        # ------------------------------------------------------------------ #
        body = HSplit([
            output_window,
            separator,
            input_window,
            status_window,
        ])

        root_container = FloatContainer(
            content=body,
            floats=[completions_float],
        )

        layout = Layout(
            container=root_container,
            focused_element=input_window,
        )

        # ------------------------------------------------------------------ #
        # Key bindings                                                         #
        # ------------------------------------------------------------------ #
        kb = KeyBindings()

        @kb.add("c-c")
        def _ctrl_c(event):
            buf = event.app.current_buffer
            if buf.text:
                buf.reset()
            else:
                if self._answer_future and not self._answer_future.done():
                    self._answer_future.set_result(None)
                event.app.exit()

        @kb.add("escape")
        def _escape(event):
            buf = event.app.current_buffer
            if buf.text:
                buf.reset()
            else:
                if self._answer_future and not self._answer_future.done():
                    self._answer_future.set_result(None)
                event.app.exit()

        @kb.add("c-d")
        def _ctrl_d(event):
            if not event.app.current_buffer.text:
                if self._answer_future and not self._answer_future.done():
                    self._answer_future.set_result(None)
                event.app.exit()

        @kb.add("enter")
        def _accept(event):
            buf = event.app.current_buffer
            # If a completion popup is active, accept the highlighted completion
            # instead of submitting. This makes @file and /command completions
            # work naturally with Enter (no Tab needed).
            if buf.complete_state is not None:
                if buf.complete_state.current_completion:
                    # Suppress BEFORE apply_completion — the text-change
                    # handler fires synchronously inside the call and would
                    # otherwise re-trigger the same popup.
                    self._suppress_ac = True
                    buf.apply_completion(buf.complete_state.current_completion)
                    try:
                        loop = asyncio.get_running_loop()
                        loop.call_soon(
                            lambda: setattr(self, "_suppress_ac", False)
                        )
                    except RuntimeError:
                        self._suppress_ac = False
                    return
                # Menu visible but nothing selected — close it and stay editing
                buf.complete_state = None
                return
            text = buf.text
            buf.reset()
            if self._answer_future and not self._answer_future.done():
                self._answer_future.set_result(text)
            event.app.exit()

        @kb.add("s-enter")
        def _shift_enter(event):
            buf = event.app.current_buffer
            buf.insert_text("\n")

        @kb.add("up")
        def _up(event):
            event.app.current_buffer.history_backward()

        @kb.add("down")
        def _down(event):
            event.app.current_buffer.history_forward()

        # ------------------------------------------------------------------ #
        # Style                                                                #
        # ------------------------------------------------------------------ #
        accent = _color(self.palette, "accent", "#88c0d0")
        warn   = _color(self.palette, "warn",   "#ebcb8b")

        style = Style.from_dict({
            # Input area
            "prompt.name":  f"fg:{accent} bold",
            "prompt.arrow": f"fg:{accent}",
            # Separator
            "separator":    "fg:#3b4252",
            # Status bar
            "status-bar":             "fg:#d8dee9 bg:#2e3440",
            "status-bar.icon":        f"fg:#88c0d0 bold",
            "status-bar.text":        "fg:#d8dee9",
            "status-bar.accent":      f"fg:{accent} bold",
            "status-bar.warn":        f"fg:{warn} bold",
            "status-bar.dim":         "fg:#4c566a",
            # Completion menu
            "completion-menu":                    "bg:#2e3440 fg:#d8dee9",
            "completion-menu.completion":         "bg:#2e3440 fg:#d8dee9",
            "completion-menu.completion.current": "bg:#434c5e fg:#88c0d0 bold",
            "completion-menu.meta":               "bg:#232831 fg:#4c566a",
            "completion-menu.meta.completion.current": "bg:#434c5e fg:#eceff4",
            # General
            "scrollbar.background": "bg:#3b4252",
            "scrollbar.button":     "bg:#88c0d0",
        })

        # ------------------------------------------------------------------ #
        # Output — use Vt100 explicitly to survive Windows PowerShell/WT     #
        # which raises NoConsoleScreenBufferError with the default Win32 out  #
        # ------------------------------------------------------------------ #
        _output = None
        try:
            from prompt_toolkit.output.defaults import create_output
            _output = create_output()
        except Exception:
            try:
                from prompt_toolkit.output.vt100 import Vt100_Output
                import shutil
                cols, rows = shutil.get_terminal_size((220, 50))
                _output = Vt100_Output(sys.stdout, lambda: (cols, rows), term="xterm-256color")
            except Exception:
                _output = None

        # ------------------------------------------------------------------ #
        # Application                                                          #
        # ------------------------------------------------------------------ #
        self._app = Application(
            layout=layout,
            key_bindings=kb,
            style=style,
            full_screen=False,   # False = keeps scroll history, like Gemini CLI
            mouse_support=False,
            color_depth=None,    # auto-detect
            output=_output,
        )

    # ---------------------------------------------------------------------- #
    # Internal helpers                                                         #
    # ---------------------------------------------------------------------- #

    def _on_accept(self, buffer: "Buffer") -> bool:
        """Called when user presses Enter. Resolves the waiting future."""
        text = buffer.text
        buffer.reset()
        if self._answer_future and not self._answer_future.done():
            self._answer_future.set_result(text)
        if self._app:
            self._app.exit()
        return True  # keep history

    def _get_output_text(self) -> str:
        return "".join(self._output_lines)

    def _get_status_text(self) -> AnyFormattedText:
        ws_name = Path(self.workspace).name or self.workspace
        branch  = _git_branch(self.workspace)
        dirty   = _git_dirty(self.workspace) if branch else False
        usage   = self.get_usage()

        git_part = ""
        if branch:
            dirty_mark = " *" if dirty else ""
            g_cls = "status-bar.warn" if dirty else "status-bar.accent"
            git_part = (
                f" <status-bar.dim>│</status-bar.dim>"
                f" <status-bar.icon>🌿</status-bar.icon>"
                f" <{g_cls}>{branch}{dirty_mark}</{g_cls}>"
            )

        usage_part = ""
        if usage:
            usage_part = (
                f" <status-bar.dim>│</status-bar.dim>"
                f" <status-bar.icon>📊</status-bar.icon>"
                f" <status-bar.text>{usage}</status-bar.text>"
            )

        return HTML(
            f" <status-bar.icon>📁</status-bar.icon>"
            f" <status-bar.accent>{ws_name}</status-bar.accent>"
            f"{git_part}"
            f" <status-bar.dim>│</status-bar.dim>"
            f" <status-bar.icon>🤖</status-bar.icon>"
            f" <status-bar.text>{self.provider}/{self.model}</status-bar.text>"
            f" <status-bar.dim>│</status-bar.dim>"
            f" <status-bar.icon>⚡</status-bar.icon>"
            f" <status-bar.accent>{self.reasoning}</status-bar.accent>"
            f"{usage_part}"
            f" "
        )


# --------------------------------------------------------------------------- #
# Utility                                                                      #
# --------------------------------------------------------------------------- #

def _color(palette: Any, attr: str, fallback: str) -> str:
    if palette is None:
        return fallback
    val = getattr(palette, attr, None)
    if not val:
        return fallback
    # Rich color names → hex approximations for prompt_toolkit
    _MAP = {
        "cyan": "#88c0d0", "magenta": "#b48ead", "yellow": "#ebcb8b",
        "green": "#a3be8c", "blue": "#81a1c1", "white": "#eceff4",
        "red": "#bf616a", "grey50": "#4c566a", "grey70": "#6b7689",
        "bold cyan": "#88c0d0", "bold magenta": "#b48ead",
        "bold yellow": "#ebcb8b", "bold white": "#eceff4",
    }
    return _MAP.get(val, fallback)
