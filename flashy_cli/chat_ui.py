"""Themed chat UI and terminal formatting controller for Flashy CLI.

This module encapsulates all prompt construction, formatting, progress rendering,
and dashboard widgets for the interactive coding terminal. It dynamically respects
the selected theme palette and handles terminal fallbacks gracefully.
"""
from __future__ import annotations

import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

try:
    from rich import box
    from rich.console import Console, Group
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.rule import Rule
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import Completer, Completion, WordCompleter
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.keys import Keys
    from prompt_toolkit.styles import Style

    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False

try:
    from flashy_cli.tui_layout import FlashyTUI, _PT_OK as TUI_AVAILABLE
except Exception:
    FlashyTUI = None  # type: ignore
    TUI_AVAILABLE = False

from flashy_cli.theme import current_palette, rich_theme
from flashy_cli.formatting import count_lines, shorten_path, truncate

# Tool icon and friendly label mapping
TOOL_LABELS = {
    "read_file": ("Read", "📖 READ"),
    "write_file": ("Write", "💾 WRITE"),
    "replace": ("Edit", "🔧 EDIT"),
    "replace_in_file": ("Edit", "🔧 EDIT"),
    "patch_file": ("Patch", "🩹 PATCH"),
    "run_shell_command": ("Run", "💻 RUN"),
    "execute_command": ("Run", "💻 RUN"),
    "list_directory": ("List", "📁 LIST"),
    "list_dir": ("List", "📁 LIST"),
    "glob": ("Find", "🔍 FIND"),
    "search_files": ("Find", "🔍 FIND"),
    "grep_search": ("Grep", "🔎 GREP"),
    "web_browse": ("Browse", "🌐 BROWSE"),
    "git_status": ("Git", "🌿 GIT"),
    "git_commit": ("Commit", "🌿 COMMIT"),
    "git_push": ("Push", "🌿 PUSH"),
    "git_pull": ("Pull", "🌿 PULL"),
    "git_log": ("Log", "🌿 LOG"),
    "git_diff": ("Diff", "🌿 DIFF"),
    "save_memory": ("Note", "📝 NOTE"),
    "todo_write": ("Plan", "📋 PLAN"),
    "ask_user_question": ("Ask", "❓ ASK"),
    "spawn_subagent": ("Agent", "🤖 AGENT"),
    "activate_skill": ("Skill", "⚡ SKILL"),
    "read_files": ("Read", "📖 READ"),
    "write_files": ("Write", "💾 WRITE"),
    "get_file_tree": ("Tree", "📁 TREE"),
    "get_explorer_data": ("Tree", "📁 TREE"),
    "apply_patch": ("Patch", "🩹 PATCH"),
    "delete_path": ("Delete", "❌ DELETE"),
    "read_background_output": ("Tail", "📜 TAIL"),
    "list_background_processes": ("List BG", "⚙️ BG"),
    "send_terminal_input": ("Stdin", "⌨️ BG"),
    "stop_background_process": ("Kill", "🛑 BG"),
    "get_dependencies": ("Deps", "🔗 DEPS"),
    "get_symbol_info": ("Symbol", "🏷️ SYMBOL"),
    "self_check": ("Self-check", "✅ CHECK"),
    "git_init": ("Init", "🌿 GIT"),
    "git_clone": ("Clone", "🌿 GIT"),
    "git_branches": ("Branches", "🌿 GIT"),
    "git_checkout": ("Checkout", "🌿 GIT"),
}

LOGO_LINES = [
    "  ███████╗██╗      █████╗ ███████╗██╗  ██╗██╗   ██╗",
    "  ██╔════╝██║     ██╔══██╗██╔════╝██║  ██║╚██╗ ██╔╝",
    "  █████╗  ██║     ███████║███████╗███████║ ╚████╔╝ ",
    "  ██╔══╝  ██║     ██╔══██║╚════██║██╔══██║  ╚██╔╝  ",
    "  ██║     ███████╗██║  ██║███████║██║  ██║   ██║   ",
    "  ╚═╝     ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝   ",
]


class GitState:
    """Helper to detect git branch and dirty modifications dynamically."""

    @staticmethod
    def get_branch(workspace: str) -> str:
        try:
            out = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=0.8,
            )
            if out.returncode == 0:
                return out.stdout.strip()
        except Exception:
            pass
        return ""

    @staticmethod
    def is_dirty(workspace: str) -> bool:
        try:
            out = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=0.8,
            )
            if out.returncode == 0:
                return len(out.stdout.strip()) > 0
        except Exception:
            pass
        return False


class ChatCompleter(Completer):
    """Autocomplete for commands (/) and workspace files (@) with metadata/descriptions."""

    def __init__(self, commands: Dict[str, str], workspace: str):
        self.commands = commands
        self.workspace = workspace

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        tokens = text.split()
        if not tokens:
            if text.endswith("/"):
                current_token = "/"
            elif text.endswith("@"):
                current_token = "@"
            else:
                return
        else:
            current_token = tokens[-1]
            if text.endswith(" "):
                current_token = ""

        # Case 1: Slash commands
        if current_token.startswith("/"):
            for cmd, desc in self.commands.items():
                if cmd.lower().startswith(current_token.lower()):
                    yield Completion(
                        cmd,
                        start_position=-len(current_token),
                        display_meta=desc
                    )
            return

        # Case 2: Workspace files prefixed with @
        if "@" in text:
            last_at_idx = text.rfind("@")
            # Only trigger if @ is at start-of-line or preceded by a space.
            # This avoids treating email addresses like user@domain.com as file refs.
            if last_at_idx > 0 and text[last_at_idx - 1] != " ":
                return
            last_part = text[last_at_idx:]
            if " " not in last_part:
                search_val = last_part[1:].replace("\\", "/")
                
                if "/" in search_val:
                    dir_part, file_prefix = search_val.rsplit("/", 1)
                    target_dir = os.path.join(self.workspace, dir_part)
                else:
                    dir_part, file_prefix = "", search_val
                    target_dir = self.workspace

                if os.path.isdir(target_dir):
                    try:
                        entries = sorted(os.listdir(target_dir), key=str.lower)
                        for entry in entries:
                            if entry.startswith(".") or entry == "__pycache__":
                                continue
                            full_path = os.path.join(target_dir, entry)
                            is_dir = os.path.isdir(full_path)
                            
                            if entry.lower().startswith(file_prefix.lower()):
                                rel_path = os.path.join(dir_part, entry).replace("\\", "/")
                                suffix = "/" if is_dir else ""
                                disp_name = entry + suffix
                                meta = "Directory" if is_dir else f"{os.path.getsize(full_path) // 1024} KB"
                                yield Completion(
                                    "@" + rel_path + suffix,
                                    start_position=-len(last_part),
                                    display=disp_name,
                                    display_meta=meta
                                )
                    except Exception:
                        pass


class ThinkingStreamer:
    """Streams thinking tokens in grey/dim — no boxes, no headers, just the color."""

    def __init__(self, console: Optional[Console], show_thinking: bool, palette: Any):
        self.console = console
        self.show_thinking = show_thinking
        self.palette = palette
        self.started = False

    def start(self) -> None:
        if not self.show_thinking:
            return
        self.started = True

    def write(self, token: str) -> None:
        if not self.show_thinking:
            return
        if not self.started:
            self.start()

        color = self.palette.code_fence
        if RICH_AVAILABLE and self.console:
            self.console.print(f"[{color}]{token}[/{color}]", end="")
        else:
            print(token, end="")

    def end(self) -> None:
        if not self.started:
            return
        self.started = False


class ChatUI:
    """Dynamic output decorator and prompt builder using themes and markdown."""

    def __init__(self, no_color: bool = False, json_mode: bool = False):
        self.no_color = no_color
        self.json_mode = json_mode
        self.palette = current_palette()
        self.console = (
            Console(no_color=no_color, theme=rich_theme(), force_terminal=True)
            if RICH_AVAILABLE
            else None
        )

    def refresh_theme(self) -> None:
        self.palette = current_palette()
        if RICH_AVAILABLE:
            self.console = Console(
                no_color=self.no_color, theme=rich_theme(), force_terminal=True
            )

    def print_welcome(
        self,
        workspace: str,
        provider: str,
        model: str,
        reasoning: str,
        mode: str,
        session_id: str,
    ) -> None:
        if self.json_mode:
            return

        # Fetch git details
        branch = GitState.get_branch(workspace)
        git_str = f"🌿 [flashy.user]{branch}[/flashy.user]" if branch else ""
        dirty = GitState.is_dirty(workspace)
        if dirty and git_str:
            git_str += " [flashy.warn]*[/flashy.warn]"

        ws_short = shorten_path(workspace)

        tips = [
            "Type a query or code instruction directly. Use [bold]/[/bold] prefix for commands.",
            "Insert files dynamically by typing [bold]@filename[/bold] (autocompletes workspace files).",
            "Use [bold]/theme set [solarized|dracula|mono|default][/bold] to change style instantly.",
            "Use [bold]/copy[/bold] to copy the last assistant response to your clipboard.",
        ]

        if RICH_AVAILABLE and self.console:
            # Ascii Logo with theme
            logo = Text()
            for i, line in enumerate(LOGO_LINES):
                logo.append(line + "\n", style="flashy.accent")

            # Meta table
            meta = Table.grid(padding=(0, 2))
            meta.add_column(style="flashy.dim", no_wrap=True)
            meta.add_column(style="bold", overflow="fold")
            meta.add_row("workspace", f"{ws_short}  {git_str}".strip())
            meta.add_row("model", f"{provider} [flashy.dim]/[/flashy.dim] {model}")
            meta.add_row("reasoning", reasoning)
            meta.add_row("session", session_id[:8])

            tip_text = Text()
            tip_text.append("Quick tips\n", style="bold flashy.accent")
            for tip in tips:
                tip_text.append("  • ")
                tip_text.append(Text.from_markup(tip, style="flashy.dim"))
                tip_text.append("\n")

            panel_content = Group(logo, Text(""), meta, Text(""), tip_text)
            welcome_header = Text.assemble(
                ("⚡ ", "bold flashy.accent"),
                ("Flashy", "bold flashy.banner_title"),
            )
            self.console.print(
                Panel(
                    panel_content,
                    title=welcome_header,
                    border_style="flashy.banner_border",
                    box=box.ROUNDED,
                    padding=(1, 2),
                )
            )
        else:
            print("\n" + "=" * 60)
            print("⚡ Flashy")
            print("-" * 60)
            print(f"Workspace: {ws_short} " + (f"({branch})" if branch else ""))
            print(f"Model:     {provider} / {model}")
            print(f"Reasoning: {reasoning}")
            print(f"Session:   {session_id[:8]}")
            print("=" * 60)
            for tip in tips:
                print(f"  - {tip.replace('[bold]', '').replace('[/bold]', '')}")
            print("-" * 60)

    def print_error(self, message: str) -> None:
        if self.json_mode:
            return
        if RICH_AVAILABLE and self.console:
            self.console.print(
                Panel(
                    Text(message, style="bold flashy.error"),
                    title="Error",
                    border_style="flashy.error",
                    box=box.ROUNDED,
                )
            )
        else:
            print(f"\nError: {message}", file=sys.stderr)

    def print_info(self, message: str) -> None:
        if self.json_mode:
            return
        if RICH_AVAILABLE and self.console:
            self.console.print(message, style="flashy.info")
        else:
            print(f"\n[Info] {message}")

    def print_dim(self, message: str, end: str = "") -> None:
        if self.json_mode:
            return
        if RICH_AVAILABLE and self.console:
            self.console.print(message, style="flashy.dim", end=end)
        else:
            print(message, end=end)

    def print_agent_text(self, text: str) -> None:
        if not text:
            return
        if RICH_AVAILABLE and self.console:
            try:
                # Set dynamic markdown spacing/theme
                self.console.print(Markdown(text, code_theme="monokai"))
                return
            except Exception:
                pass
        try:
            sys.stdout.write(text)
            sys.stdout.flush()
        except UnicodeEncodeError:
            safe = text.encode(
                sys.stdout.encoding or "utf-8", errors="replace"
            ).decode(sys.stdout.encoding or "utf-8", errors="replace")
            sys.stdout.write(safe)
            sys.stdout.flush()

    def print_turn_header(self, turn: int) -> None:
        if self.json_mode:
            return
        if RICH_AVAILABLE and self.console:
            self.console.print(
                Rule(
                    Text(f" Flashy Turn {turn} ", style="bold flashy.accent"),
                    style="flashy.rule",
                )
            )
        else:
            print(f"\n──────────────────── Flashy Turn {turn} ────────────────────")

    def print_turn_footer(
        self, elapsed: float, tools_seen: int, usage: str
    ) -> None:
        if self.json_mode:
            return
        summary = f"done in {elapsed:.1f}s"
        if tools_seen:
            summary += f"  •  {tools_seen} tool call{'s' if tools_seen != 1 else ''}"
        summary += f"  •  ctx {usage}"

        if RICH_AVAILABLE and self.console:
            self.console.print(f"[flashy.dim]{summary}[/flashy.dim]")
        else:
            print(summary)

    def print_help(self, commands: Dict[str, str]) -> None:
        if RICH_AVAILABLE and self.console:
            table = Table(
                box=box.SIMPLE_HEAVY, show_header=True, header_style="bold flashy.accent"
            )
            table.add_column("Command", style="bold flashy.accent_alt")
            table.add_column("Action")
            for cmd, desc in sorted(commands.items()):
                table.add_row(cmd, desc)

            tips = Text(
                "Plain prompts go straight to the coding agent. Attach files with @filename.",
                style="flashy.dim italic",
            )
            self.console.print(
                Panel(
                    Group(table, Text(""), tips),
                    title="Flashy Command Dashboard",
                    border_style="flashy.accent",
                    box=box.ROUNDED,
                )
            )
        else:
            print("\nAvailable Commands:")
            for cmd, desc in sorted(commands.items()):
                print(f"  {cmd:<12} {desc}")

    def print_config(self, rows: List[Dict[str, Any]]) -> None:
        self.print_table("Active Settings", ["key", "value"], rows)

    def print_tools(self, rows: List[Dict[str, Any]]) -> None:
        self.print_table("Available Tools", ["name", "description"], rows, style="flashy.rule")

    def print_status(self, rows: List[Dict[str, Any]]) -> None:
        self.print_table("System Status Diagnostics", ["check", "status", "detail", "hint"], rows)

    def print_table(
        self,
        title: str,
        columns: List[str],
        rows: List[Dict[str, Any]],
        *,
        style: str = "flashy.accent",
    ) -> None:
        if self.json_mode:
            import json

            print(json.dumps(rows, indent=2))
            return
        if not rows:
            self.print_dim("No items in table.")
            return

        if RICH_AVAILABLE and self.console:
            table = Table(
                title=title,
                box=box.SIMPLE_HEAVY,
                border_style=style,
                show_lines=False,
                header_style="bold",
            )
            for col in columns:
                table.add_column(col.replace("_", " ").title())
            for row in rows:
                table.add_row(*[str(row.get(col, "")) for col in columns])
            self.console.print(table)
        else:
            print(f"\n{title}")
            for row in rows:
                print("  " + " | ".join(str(row.get(c, "")) for c in columns))

    # ---- Tool action formatting -----------------------------------------
    def format_tool_action(
        self, name: str, args: Dict[str, Any], workspace: str
    ) -> Text | str:
        label, icon = TOOL_LABELS.get(name, (name, "🔨"))

        # Extract path or main argument
        main_arg = self._main_arg(name, args)

        if RICH_AVAILABLE:
            text = Text()
            text.append(f"  {icon}  ", style="flashy.accent")
            text.append(f"{label:<14}", style="bold flashy.tool")
            text.append(main_arg, style="flashy.tool_path")

            # Inline addition/deletion summary for edits
            if name in {"write_file", "replace", "replace_in_file"}:
                if name == "write_file":
                    added = count_lines(str(args.get("content", "")))
                    removed = 0
                else:
                    added, removed = self._get_diff_stats(
                        str(args.get("old_string", "")),
                        str(args.get("new_string", "")),
                    )
                text.append("  [")
                text.append(f"+{added}", style="flashy.tool_diff_add")
                text.append(" ")
                text.append(f"-{removed}", style="flashy.tool_diff_remove")
                text.append("]")
            return text

        # Plain text fallback
        return f"  {icon} {label:<12} {main_arg}"

    def format_tool_result(self, result: Any, elapsed: float) -> Text | str:
        text_result = str(result or "")
        line_count = count_lines(text_result)
        is_error = self._tool_result_is_error(text_result)

        elapsed_str = f"in {elapsed:.1f}s"

        if RICH_AVAILABLE:
            text = Text()
            if is_error:
                text.append("   └─ ❌ failed ", style="flashy.error")
                text.append(f"({elapsed_str})", style="flashy.dim")
                if text_result:
                    text.append(" · ", style="flashy.dim")
                    text.append(truncate(text_result, 180), style="flashy.error")
            else:
                text.append("   └─ ✅ ok ", style="flashy.ok")
                text.append(f"({elapsed_str})", style="flashy.dim")
                if line_count:
                    text.append(
                        f" · {line_count} line{'s' if line_count != 1 else ''}",
                        style="flashy.dim",
                    )
            return text

        status = "failed" if is_error else "ok"
        return f"     └─ {status} ({elapsed_str}): {truncate(text_result, 160)}"

    def _main_arg(self, name: str, args: Dict[str, Any]) -> str:
        if name in {
            "read_file",
            "write_file",
            "replace",
            "replace_in_file",
            "patch_file",
        }:
            return shorten_path(args.get("path", "unknown"))
        if name in {"run_shell_command", "execute_command"}:
            return truncate(args.get("command", "unknown"), 100)
        if name in {"list_directory", "list_dir"}:
            return shorten_path(args.get("dir_path", args.get("path", ".")))
        if name in {"glob", "search_files"}:
            return truncate(args.get("pattern", "*"), 100)
        if name == "grep_search":
            return truncate(args.get("pattern", ""), 100)
        if name == "web_browse":
            return truncate(args.get("url", "unknown"), 100)
        if name in {"git_commit"}:
            return truncate(args.get("message", ""), 80)
        if name in {"ask_user_question"}:
            return truncate(args.get("question", args.get("prompt", "")), 100)
        return truncate(str(args), 100)

    def _get_diff_stats(self, old_text: str, new_text: str) -> Tuple[int, int]:
        return count_lines(new_text), count_lines(old_text)

    def _tool_result_is_error(self, result: str) -> bool:
        lowered = result.lower()
        return any(
            marker in lowered
            for marker in (
                "error",
                "exception",
                "traceback",
                "permission denied",
                "failed",
            )
        )

    # ---- Interactive input prompt ---------------------------------------

    def build_tui(
        self,
        history_path: str,
        commands: Dict[str, str],
        workspace: str,
        provider: str,
        model: str,
        reasoning: str,
        get_usage: Any = None,
    ) -> Any:
        """Build and return a FlashyTUI split-pane instance (preferred path).

        Falls back to None when prompt_toolkit is unavailable.
        """
        if not TUI_AVAILABLE or FlashyTUI is None:
            return None
        try:
            completer = ChatCompleter(commands, workspace)
            return FlashyTUI(
                workspace=workspace,
                provider=provider,
                model=model,
                reasoning=reasoning,
                history_path=history_path,
                completer=completer,
                palette=self.palette,
                get_usage=get_usage,
            )
        except Exception as exc:
            try:
                import traceback
                with open("tui_error.log", "w", encoding="utf-8") as _f:
                    _f.write(f"FlashyTUI creation failed: {exc}\n")
                    traceback.print_exc(file=_f)
            except Exception:
                pass
            return None

    def build_prompt_session_and_completer(
        self, history_path: str, commands: Dict[str, str], workspace: str
    ) -> Any:
        """Legacy PromptSession fallback (used when TUI is unavailable)."""
        if not PROMPT_TOOLKIT_AVAILABLE:
            return None
        try:
            completer = ChatCompleter(commands, workspace)
            bindings = KeyBindings()

            @bindings.add(Keys.ControlC)
            def _ctrl_c(event):
                buf = event.app.current_buffer
                if buf.text:
                    buf.reset()
                else:
                    event.app.exit(exception=KeyboardInterrupt, style="class:aborting")

            prompt_style = Style.from_dict({
                "bottom-toolbar":                      "fg:#d8dee9 bg:#2e3440",
                "bottom-toolbar.icon":                 "fg:#88c0d0 bold",
                "bottom-toolbar.text":                 "fg:#d8dee9",
                "bottom-toolbar.accent":               f"fg:{self.palette.accent} bold",
                "bottom-toolbar.warn":                 f"fg:{self.palette.warn} bold",
                "completion-menu":                     "bg:#2e3440 fg:#d8dee9",
                "completion-menu.completion.current":  "bg:#434c5e fg:#88c0d0 bold",
                "completion-menu.meta":                "bg:#232831 fg:#4c566a",
                "completion-menu.meta.completion.current": "bg:#434c5e fg:#d8dee9",
                "prompt.name":  f"fg:{self.palette.accent} bold",
                "prompt.arrow": f"fg:{getattr(self.palette, 'prompt_arrow', 'cyan')}",
            })

            try:
                return PromptSession(
                    history=FileHistory(history_path),
                    completer=completer,
                    complete_while_typing=True,
                    auto_suggest=AutoSuggestFromHistory(),
                    key_bindings=bindings,
                    style=prompt_style,
                )
            except Exception:
                from prompt_toolkit.output.vt100 import Vt100_Output
                out = Vt100_Output(sys.stdout, lambda: None)
                return PromptSession(
                    history=FileHistory(history_path),
                    completer=completer,
                    complete_while_typing=True,
                    auto_suggest=AutoSuggestFromHistory(),
                    key_bindings=bindings,
                    style=prompt_style,
                    output=out,
                )
        except Exception as exc:
            try:
                import traceback
                with open("prompt_error.log", "w", encoding="utf-8") as _f:
                    _f.write(f"PromptSession creation failed: {exc}\n")
                    traceback.print_exc(file=_f)
            except Exception:
                pass
            return None

    async def prompt_user(
        self,
        tui_or_session: Any,
        workspace: str,
        provider: str,
        model: str,
        reasoning: str,
        mode: str,
        usage: str,
    ) -> Any:
        """Get one line of input from the user.

        If ``tui_or_session`` is a :class:`FlashyTUI` instance, delegates to
        its ``prompt_once()`` method which keeps the input bar pinned to the
        bottom of the screen.  Falls back to a Rich/plain-input prompt when
        no TUI is available.
        """
        # --- preferred path: fullscreen split-pane TUI ----------------------
        if TUI_AVAILABLE and FlashyTUI is not None and isinstance(tui_or_session, FlashyTUI):
            tui: FlashyTUI = tui_or_session
            # Keep live metadata in sync
            tui.provider  = provider
            tui.model     = model
            tui.reasoning = reasoning
            try:
                return await tui.prompt_once()
            except KeyboardInterrupt:
                raise
            except Exception:
                pass  # fall through to rich/plain fallback

        # --- legacy fallback: inline PromptSession --------------------------
        if PROMPT_TOOLKIT_AVAILABLE and tui_or_session is not None:
            branch = GitState.get_branch(workspace)
            dirty  = GitState.is_dirty(workspace)
            ws_name = Path(workspace).name or workspace

            def _toolbar():
                gp = ""
                if branch:
                    dm = " *" if dirty else ""
                    gc = "bottom-toolbar.warn" if dirty else "bottom-toolbar.accent"
                    gp = f" │ <bottom-toolbar.icon>🌿</bottom-toolbar.icon> <{gc}>{branch}{dm}</{gc}>"
                return HTML(
                    f" <bottom-toolbar.icon>📁</bottom-toolbar.icon> <b>{ws_name}</b>{gp}"
                    f" │ <bottom-toolbar.icon>🤖</bottom-toolbar.icon>"
                    f" <bottom-toolbar.text>{provider}/{model}</bottom-toolbar.text>"
                    f" │ <bottom-toolbar.icon>⚡</bottom-toolbar.icon>"
                    f" <bottom-toolbar.accent>{reasoning}</bottom-toolbar.accent>"
                    f" │ <bottom-toolbar.icon>📊</bottom-toolbar.icon>"
                    f" <bottom-toolbar.text>{usage}</bottom-toolbar.text> │"
                )

            prompt_html = HTML("<prompt.name>flashy</prompt.name> <prompt.arrow>❯</prompt.arrow> ")
            try:
                return await tui_or_session.prompt_async(
                    prompt_html, bottom_toolbar=_toolbar
                )
            except KeyboardInterrupt:
                raise
            except Exception:
                pass

        # --- plain text fallback --------------------------------------------
        branch = GitState.get_branch(workspace)
        usage_simple = usage.split(" ")[0] if usage else "0%"
        git_simple   = f" ({branch})" if branch else ""
        if RICH_AVAILABLE and self.console:
            prompt_str = (
                f"\n[bold {self.palette.prompt_name}]flashy[/bold {self.palette.prompt_name}]"
                f" [dim]{usage_simple}{git_simple}[/dim]"
                f" [bold {self.palette.prompt_arrow}]❯[/bold {self.palette.prompt_arrow}] "
            )
            return Prompt.ask(prompt_str)
        return input(f"\nflashy [{usage_simple}{git_simple}] ❯ ")
