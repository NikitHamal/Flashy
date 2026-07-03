"""Terminal chat interface for Flashy's local coding agent.

This module intentionally keeps the UX dependency-light: Rich and prompt_toolkit are
used when available, but the CLI still works in a plain Python terminal.

Features:
- Clean Rich-powered welcome panel
- Markdown rendering for assistant output
- @file attachments resolved against the workspace
- Stdin / pipe support
- /save, /load, /sessions, /resume, /export commands
- Smooth Ctrl+C handling
- Per-turn timing, tool summary, context usage
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from threading import Event as ThreadEvent
from typing import Any, Dict, List, Optional, Tuple

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
except ImportError:  # pragma: no cover - fallback path
    RICH_AVAILABLE = False

try:
    import questionary

    QUESTIONARY_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    QUESTIONARY_AVAILABLE = False

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.filters import Condition
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.keys import Keys

    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    PROMPT_TOOLKIT_AVAILABLE = False

from backend.config import CONFIG_FILE, load_config, save_config
from backend.desktop_runtime import data_file
from backend.llm_runtime.service import LLMService
from backend.models import get_context_window, perform_compaction
from backend.server.catalog import ProviderCatalog

# Local CLI helpers
from flashy_cli import logs as flashy_logs
from flashy_cli import stats as flashy_stats
from flashy_cli.formatting import extract_attachments, render_attachment_summary, shorten_path
from flashy_cli.sessions import (
    Message as SessionMessage,
    Session as SessionRecord,
    auto_title,
    export as session_export,
    find_session as sessions_find,
    last_session,
    list_sessions,
    new_session_id,
    save_session,
    to_rows as sessions_to_rows,
)
from flashy_cli.chat_ui import ChatUI, ThinkingStreamer


COMMANDS: dict[str, str] = {
    "/help": "show command palette",
    "/clear": "clear screen and reset the conversation",
    "/reset": "reset the conversation (alias for /clear)",
    "/model": "switch provider and model",
    "/provider": "switch provider and model (alias)",
    "/thinking": "change reasoning effort",
    "/verbose": "toggle streamed thinking text",
    "/thoughts": "alias for /verbose",
    "/theme": "switch terminal theme (solarized, dracula, etc.)",
    "/compact": "compact long context manually",
    "/status": "run quick local diagnostics",
    "/doctor": "alias for /status",
    "/workspace": "show or change active workspace",
    "/cwd": "alias for /workspace",
    "/config": "show active provider/model settings",
    "/tools": "list local agent tools",
    "/todo": "manage workspace tasks and checklists interactively",
    "/cybertest": "ethical security scan: /cybertest <url> — recon, vulns, headers, ports",
    "/save": "save the current session",
    "/load": "load a previous session",
    "/sessions": "list recent sessions",
    "/export": "export the current session to a file",
    "/copy": "copy the last assistant reply to the clipboard",
    "/init": "create a project rules file (AGENTS.md)",
    "/exit": "quit",
    "/quit": "alias for /exit",
}


class ChatCLI:
    """Interactive coding chat with a polished terminal surface."""

    def __init__(
        self,
        workspace: str | None = None,
        config_overrides: Optional[Dict[str, Any]] = None,
        no_banner: bool = False,
        show_thinking: bool = False,
        no_color: bool = False,
        session_id: str | None = None,
        auto_save: bool = True,
    ):
        self.workspace = os.path.abspath(workspace or os.getcwd())
        self.session_id = session_id or new_session_id()
        self.config_overrides = dict(config_overrides or {})
        # Pop internal control flags
        self._resume_session_id = self.config_overrides.pop("__resume_session_id", None)
        self.llm_service = LLMService(config_overrides=self.config_overrides)
        self.ui = ChatUI(no_color=no_color)
        self.console = self.ui.console
        self.config = load_config()
        self.config.update(self.config_overrides)
        self.catalog = ProviderCatalog()
        self.no_banner = no_banner
        self.show_thinking = show_thinking or bool(self.config.get("show_thinking", False))
        self.auto_save = auto_save
        self._last_tool_started_at: float | None = None
        self._last_tool_name: str | None = None
        self._turn_counter = 0
        self._last_assistant_text: str = ""
        self._last_user_text: str = ""
        self._pending_attachments: List[Tuple[str, str]] = []
        self._stdin_buffer: List[str] = []
        self._session_title: str = ""
        
        try:
            history_path = str(data_file("cli_history"))
        except Exception:
            history_path = ""

        commands_with_desc = dict(COMMANDS)
        commands_with_desc.update({
            "/exit": "quit the session",
            "/quit": "quit the session (alias)",
            "/help": "show help dashboard",
        })

        # Try the proper split-pane TUI first (input pinned to bottom)
        self.tui = None
        self.prompt_session = None
        if history_path:
            self.tui = self.ui.build_tui(
                history_path=history_path,
                commands=commands_with_desc,
                workspace=self.workspace,
                provider=self.config.get("active_provider", "g4f"),
                model=self.config.get("model", "unknown"),
                reasoning=self._reasoning_label(),
                get_usage=self.get_context_usage,
            )
            if self.tui is None:
                # Fallback: plain PromptSession
                self.prompt_session = self.ui.build_prompt_session_and_completer(
                    history_path, commands_with_desc, self.workspace
                )

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------
    def get_model_display(self) -> str:
        provider = self.config.get("active_provider", "g4f")
        model = self.config.get("model", "unknown")
        return f"{provider} / {model}"

    def _reasoning_label(self) -> str:
        return str(self.config.get("reasoning_effort", "medium"))

    def _mode_label(self) -> str:
        return "verbose" if self.show_thinking else "clean"

    def print_welcome(self) -> None:
        self.ui.print_welcome(
            self.workspace,
            self.config.get("active_provider", "g4f"),
            self.config.get("model", "unknown"),
            self._reasoning_label(),
            self._mode_label(),
            self.session_id,
        )

    def print_error(self, msg: str) -> None:
        self.ui.print_error(msg)

    def print_info(self, msg: str) -> None:
        self.ui.print_info(msg)

    def print_dim(self, msg: str, *, end: str = "") -> None:
        self.ui.print_dim(msg, end=end)

    def print_agent_text(self, text: str) -> None:
        self.ui.print_agent_text(text)

    def _assistant_header(self) -> None:
        self.ui.print_turn_header(self._turn_counter)

    def _print_table(self, title: str, columns: list[str], rows: list[dict[str, Any]], *, border_style: str = "cyan") -> None:
        self.ui.print_table(title, columns, rows, style="flashy.accent")

    # ------------------------------------------------------------------
    # Model / config controls
    # ------------------------------------------------------------------
    async def handle_model_switch(self) -> None:
        if not QUESTIONARY_AVAILABLE:
            self.print_error("Install questionary to use the interactive model switcher: python -m pip install questionary")
            return

        from backend.server.catalog import DEFAULT_PROVIDERS

        providers = ["< Cancel >"] + list(DEFAULT_PROVIDERS)
        current_provider = self.config.get("active_provider", "g4f")
        if current_provider not in providers:
            current_provider = "deepseekai" if current_provider == "deepseek" else providers[1]

        provider = await questionary.select("Provider", choices=providers, default=current_provider).ask_async()
        if not provider or provider == "< Cancel >":
            return

        self.print_dim("Fetching models...\n")
        try:
            models_data = await self.catalog.list_models([provider])
            model_choices = [questionary.Choice(title="< Cancel >", value="< Cancel >")]
            for model_item in models_data.get("data", []):
                model_id = model_item["id"].split("/", 1)[-1] if "/" in model_item["id"] else model_item["id"]
                model_name = model_item.get("name") or model_id
                model_choices.append(questionary.Choice(title=model_name, value=model_id))
        except Exception as exc:
            self.print_error(f"Failed to fetch models: {exc}")
            model_choices = [questionary.Choice(title="< Cancel >", value="< Cancel >")]

        if len(model_choices) <= 1:
            model = await questionary.text(f"Model for {provider}", default=self.config.get("model", "")).ask_async()
        else:
            model_choices.append(questionary.Choice(title="...Type manually...", value="...Type manually..."))
            current_model = self.config.get("model", "")
            default_choice = next((choice for choice in model_choices if choice.value == current_model), model_choices[1])
            model = await questionary.select("Model", choices=model_choices, default=default_choice, use_indicator=True).ask_async()
            if not model or model == "< Cancel >":
                return
            if model == "...Type manually...":
                model = await questionary.text(f"Model for {provider}", default=current_model).ask_async()

        if not model:
            return

        self.config["active_provider"] = provider
        self.config["model"] = model
        save_config(self.config)
        self.llm_service.config = self.config
        self.llm_service.config_overrides = self.config_overrides
        await self._maybe_prompt_reasoning()
        self.print_info(f"Switched to {provider} / {model}")

    async def _maybe_prompt_reasoning(self) -> None:
        if not QUESTIONARY_AVAILABLE:
            return
        current = self.config.get("reasoning_effort", "medium")
        effort = await questionary.select(
            "Reasoning effort",
            choices=[
                questionary.Choice(title="off     no thinking tokens", value="off"),
                questionary.Choice(title="low     fast, minimal reasoning", value="low"),
                questionary.Choice(title="medium  balanced default", value="medium"),
                questionary.Choice(title="high    deeper reasoning", value="high"),
            ],
            default=current,
        ).ask_async()
        if effort and effort != current:
            self.config["reasoning_effort"] = effort
            save_config(self.config)
            self.print_info(f"Reasoning effort set to {effort}")

    async def handle_thinking(self) -> None:
        if not QUESTIONARY_AVAILABLE:
            self.print_error("Install questionary to use reasoning picker: python -m pip install questionary")
            return
        await self._maybe_prompt_reasoning()
        self.print_info(f"Reasoning effort: {self.config.get('reasoning_effort', 'medium')}")

    async def handle_theme_switch(self, arg: str) -> None:
        from flashy_cli import theme as flashy_theme
        arg = arg.strip().lower()
        if not arg:
            if QUESTIONARY_AVAILABLE:
                choices = list(flashy_theme.THEMES.keys())
                current = os.environ.get("FLASHY_THEME") or self.config.get("theme", "default")
                choice = await questionary.select("Theme", choices=choices, default=current).ask_async()
                if choice:
                    arg = choice
            else:
                self.print_info(f"Available themes: {', '.join(flashy_theme.THEMES.keys())}")
                self.print_info(f"Current theme: {os.environ.get('FLASHY_THEME') or self.config.get('theme', 'default')}")
                return

        if arg:
            if arg not in flashy_theme.THEMES:
                self.print_error(f"Unknown theme: {arg}. Try one of: {', '.join(flashy_theme.THEMES)}")
                return
            os.environ["FLASHY_THEME"] = arg
            self.config["theme"] = arg
            save_config(self.config)
            self.ui.refresh_theme()
            self.print_info(f"Theme set to '{arg}'.")

    async def handle_todo_command(self) -> None:
        import os
        import re
        from pathlib import Path

        # Search for task.md or plan.md in workspace
        workspace = Path(self.workspace)
        task_file = workspace / "task.md"
        if not task_file.exists():
            task_file = workspace / "plan.md"

        if not task_file.exists():
            # Create a default task.md
            self.print_info("No task list found. Creating default task.md...")
            default_content = (
                "# Tasks\n\n"
                "- [ ] Learn Flashy CLI commands\n"
                "- [ ] Refactor codebase\n"
                "- [ ] Run automated checks\n"
            )
            try:
                task_file = workspace / "task.md"
                task_file.write_text(default_content, encoding="utf-8")
            except Exception as exc:
                self.print_error(f"Could not create task.md: {exc}")
                return

        # Parse tasks
        try:
            content = task_file.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            self.print_error(f"Could not read {task_file.name}: {exc}")
            return

        lines = content.splitlines()
        tasks = []
        task_indices = []

        task_re = re.compile(r"^(?P<indent>\s*)-\s*\[(?P<status>[ xX/])\]\s*(?P<name>.*)$")

        for idx, line in enumerate(lines):
            m = task_re.match(line)
            if m:
                status_char = m.group("status")
                name = m.group("name").strip()
                completed = status_char in ("x", "X")
                in_progress = status_char == "/"
                tasks.append({
                    "name": name,
                    "completed": completed,
                    "in_progress": in_progress,
                    "indent": m.group("indent") or ""
                })
                task_indices.append(idx)

        if not tasks:
            self.print_info(f"No checkbox tasks found in {task_file.name}.")
            return

        if QUESTIONARY_AVAILABLE:
            import questionary

            # Format choices. Completed tasks are checked by default.
            choices = []
            for t in tasks:
                status_desc = " (in progress)" if t["in_progress"] else ""
                choices.append(questionary.Choice(
                    title=t["name"] + status_desc,
                    value=t["name"],
                    checked=t["completed"]
                ))

            self.print_info(f"Interactive Task Manager: Toggle tasks for {task_file.name} (Space to toggle, Enter to save)")
            try:
                selected_names = await questionary.checkbox(
                    "Select completed tasks:",
                    choices=choices
                ).ask_async()
            except Exception as exc:
                self.print_error(f"Error running checklist: {exc}")
                return

            if selected_names is None:
                self.print_info("Cancelled.")
                return

            # Update the tasks based on user choice
            selected_set = set(selected_names)
            for t in tasks:
                was_completed = t["completed"]
                now_completed = t["name"] in selected_set
                
                # Update completed status
                t["completed"] = now_completed
                if now_completed:
                    t["in_progress"] = False
                
                # Update line in lines array
                status_char = "x" if t["completed"] else ("/" if t["in_progress"] else " ")
                lines[task_indices[tasks.index(t)]] = f"{t['indent']}- [{status_char}] {t['name']}"

            # Save file
            try:
                task_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
                self.print_info(f"Updated tasks saved to {task_file.name}.")
            except Exception as exc:
                self.print_error(f"Could not save {task_file.name}: {exc}")
        else:
            # Questionary not available, print formatted table
            rows = []
            for t in tasks:
                status = "✅ Completed" if t["completed"] else ("⏳ In Progress" if t["in_progress"] else "⏹️ Todo")
                rows.append({"task": t["name"], "status": status})
            self.ui.print_table(f"Tasks in {task_file.name}", ["task", "status"], rows)

    # ------------------------------------------------------------------
    # Session state
    # ------------------------------------------------------------------
    def get_context_usage(self) -> str:
        usage = self.llm_service.session_usage.get(self.session_id)
        if not usage:
            return "0%"
        provider = self.config.get("active_provider", "g4f")
        model = self.config.get("model", "unknown")
        context_window = get_context_window(provider, model)
        if context_window <= 0:
            return "0%"
        used = int(usage.get("input_tokens", 0) or 0)
        pct = (used / context_window) * 100
        return f"{pct:.1f}% ({used}/{context_window})"

    async def handle_manual_compact(self) -> None:
        self.print_info("Compacting conversation history...")
        provider = self.config.get("active_provider", "g4f")
        model = self.config.get("model", "unknown")
        context_window = get_context_window(provider, model)
        compacted = await perform_compaction(
            self.session_id,
            self.llm_service.provider_sessions,
            self.llm_service.session_usage,
            context_window,
            provider,
            model,
            llm_service=self.llm_service,
        )
        if compacted:
            self.llm_service.reset_provider_session()
            self.print_info("Context compacted. Continuing with a leaner session.")
        else:
            self.print_info("Not enough history to compact yet.")

    def _reset_session(self, *, clear_screen: bool = False) -> None:
        self.session_id = new_session_id()
        self.llm_service.set_workspace(self.workspace, self.session_id)
        self.llm_service.reset_provider_session()
        self._session_title = ""
        self._last_assistant_text = ""
        if clear_screen:
            if RICH_AVAILABLE:
                self.console.clear()
            else:
                os.system("cls" if os.name == "nt" else "clear")
        if not self.no_banner:
            self.print_welcome()
        self.print_info("Conversation reset.")

    def _set_workspace(self, path: str) -> None:
        next_workspace = os.path.abspath(os.path.expanduser(path))
        if not os.path.isdir(next_workspace):
            self.print_error(f"Workspace does not exist or is not a directory: {path}")
            return
        self.workspace = next_workspace
        self.llm_service.set_workspace(self.workspace, self.session_id)
        self.print_info(f"Workspace: {_home_short(self.workspace)}")

    # ------------------------------------------------------------------
    # Session persistence
    # ------------------------------------------------------------------
    def _hydrate_from_resumed_session(self) -> None:
        """If a session id was provided, pull the saved transcript back into the LLM service."""
        if not self._resume_session_id:
            return
        session = sessions_find(self._resume_session_id)
        if not session:
            self.print_info(f"No saved session matches '{self._resume_session_id}'. Starting fresh.")
            return
        self.session_id = session.id
        self._session_title = session.title
        # Replay messages into the LLM service if it supports it.
        try:
            from backend.llm_runtime.service import _messages_to_provider  # type: ignore

            payload = []
            for m in session.messages:
                payload.append({"role": m.role, "content": m.content})
            provider_sessions = getattr(self.llm_service, "provider_sessions", None)
            if isinstance(provider_sessions, dict):
                provider_sessions[self.session_id] = payload
        except Exception:
            # Best-effort; if the runtime doesn't expose this, just continue.
            pass
        if session.workspace and os.path.isdir(session.workspace):
            self.workspace = session.workspace
            self.llm_service.set_workspace(self.workspace, self.session_id)
        self.print_info(f"Resumed session {session.id} ({session.short_title(60)})")

    def _snapshot_session(self) -> SessionRecord:
        """Build a SessionRecord from the current LLM service state."""
        messages: list[SessionMessage] = []
        try:
            provider_sessions = getattr(self.llm_service, "provider_sessions", {})
            history = provider_sessions.get(self.session_id, []) if isinstance(provider_sessions, dict) else []
            for entry in history:
                if isinstance(entry, dict):
                    role = entry.get("role", "")
                    content = entry.get("content", "")
                else:
                    role = getattr(entry, "role", "")
                    content = getattr(entry, "content", "")
                if not role:
                    continue
                messages.append(SessionMessage(role=str(role), content=content))
        except Exception:
            pass
        title = self._session_title or auto_title(self._last_user_text or "")
        return SessionRecord(
            id=self.session_id,
            title=title,
            workspace=self.workspace,
            provider=str(self.config.get("active_provider", "")),
            model=str(self.config.get("model", "")),
            reasoning=str(self.config.get("reasoning_effort", "medium")),
            created_at=time.time() if not messages else time.time(),
            updated_at=time.time(),
            messages=messages,
        )

    def save_current_session(self, *, silent: bool = False) -> Optional[Path]:
        session = self._snapshot_session()
        if not session.messages:
            if not silent:
                self.print_info("Nothing to save yet. Send a message first.")
            return None
        if not session.title or session.title == "new session":
            session.title = auto_title(self._last_user_text or session.messages[0].content or "session")
        path = save_session(session)
        flashy_logs.write("info", "session saved", id=session.id, path=str(path), turns=len(session.messages))
        if not silent:
            self.print_info(f"Saved session {session.id} ({len(session.messages)} messages) -> {_home_short(path)}")
        return path

    def handle_save(self, args: str) -> None:
        if args.strip().lower() in {"--md", "--markdown", "--json"}:
            # /save --md
            fmt = args.strip().lstrip("-").lower()
            session = self._snapshot_session()
            if not session.messages:
                self.print_info("Nothing to export yet.")
                return
            session.title = session.title or auto_title(self._last_user_text or "")
            try:
                filename, content = session_export(session, "md" if "md" in fmt else "json")
            except ValueError as exc:
                self.print_error(str(exc))
                return
            target = Path(self.workspace) / filename
            target.write_text(content, encoding="utf-8")
            self.print_info(f"Exported to {target}")
            return
        self.save_current_session()

    def handle_load(self, arg: str) -> None:
        if not arg.strip():
            self.print_info("Usage: /load <session-id-or-prefix>")
            return
        session = sessions_find(arg.strip())
        if not session:
            self.print_error(f"No session matches '{arg.strip()}'.")
            return
        self.session_id = session.id
        self._session_title = session.title
        if session.workspace and os.path.isdir(session.workspace):
            self.workspace = session.workspace
            self.llm_service.set_workspace(self.workspace, self.session_id)
        # Replay messages
        try:
            provider_sessions = getattr(self.llm_service, "provider_sessions", {})
            payload = []
            for m in session.messages:
                payload.append({"role": m.role, "content": m.content})
            if isinstance(provider_sessions, dict):
                provider_sessions[self.session_id] = payload
        except Exception:
            pass
        self.print_info(f"Loaded session {session.id} ({session.short_title(60)}) - {len(session.messages)} messages")

    def handle_sessions(self, args: str) -> None:
        limit = 20
        try:
            for token in args.split():
                if token.startswith("-n="):
                    limit = max(1, int(token.split("=", 1)[1]))
        except Exception:
            pass
        items = list_sessions(limit=limit)
        if not items:
            self.print_info("No saved sessions yet.")
            return
        self._print_table("Recent sessions", ["id", "title", "model", "turns", "updated", "workspace"], sessions_to_rows(items))
        self.print_info("Use /load <id> to resume, or /resume <id> to jump back in.")

    def handle_export(self, args: str) -> None:
        parts = args.split()
        fmt = "md"
        target: Optional[Path] = None
        for part in parts:
            if part in {"md", "markdown", "json"}:
                fmt = "md" if part in {"md", "markdown"} else "json"
            elif part.startswith("-"):
                continue
            else:
                target = Path(part).expanduser()
        session = self._snapshot_session()
        if not session.messages:
            self.print_info("Nothing to export yet.")
            return
        session.title = session.title or auto_title(self._last_user_text or "session")
        try:
            filename, content = session_export(session, fmt)
        except ValueError as exc:
            self.print_error(str(exc))
            return
        out_path = target or (Path(self.workspace) / filename)
        try:
            out_path.write_text(content, encoding="utf-8")
        except Exception as exc:
            self.print_error(f"Could not write {out_path}: {exc}")
            return
        self.print_info(f"Exported session to {out_path}")

    def handle_copy(self) -> None:
        text = self._last_assistant_text
        if not text:
            self.print_info("Nothing to copy yet.")
            return
        # Try a few clipboard mechanisms without depending on extra packages.
        copied = False
        if sys.platform == "win32":
            try:
                import subprocess

                subprocess.run(["clip"], input=text.encode("utf-16le"), check=True)
                copied = True
            except Exception:
                copied = False
        elif sys.platform == "darwin":
            try:
                import subprocess

                subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
                copied = True
            except Exception:
                copied = False
        else:
            for cmd in (["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"], ["wl-copy"]):
                try:
                    import subprocess

                    subprocess.run(cmd, input=text.encode("utf-8"), check=True)
                    copied = True
                    break
                except Exception:
                    continue
        if copied:
            self.print_info(f"Copied {len(text)} chars to clipboard.")
        else:
            self.print_error("No clipboard tool found. Install xclip / xsel / wl-copyboard, or copy manually.")
            self.print_dim(text[:400] + ("\n…(truncated)" if len(text) > 400 else ""))

    def handle_init_project(self) -> None:
        target = Path(self.workspace) / "AGENTS.md"
        if target.exists():
            self.print_info(f"{target} already exists. Leaving it alone.")
            return
        body = (
            f"# Project rules for Flashy\n\n"
            f"## Workspace\n{self.workspace}\n\n"
            f"## Conventions\n"
            f"- Prefer minimal, focused changes.\n"
            f"- Run tests after every meaningful change.\n"
            f"- Keep dependencies up to date; document new ones here.\n\n"
            f"## Active model\n{self.get_model_display()} · reasoning {self._reasoning_label()}\n"
        )
        try:
            target.write_text(body, encoding="utf-8")
            self.print_info(f"Wrote {target}.")
        except Exception as exc:
            self.print_error(f"Could not write {target}: {exc}")

    async def handle_cybertest(self, arg: str) -> None:
        """Run the CyberArmy ethical security scanner against a URL.

        Usage: /cybertest <url> [--quick] [--module <name>] [--json <path>]

        ⚠️  Only scan sites you own or have explicit written permission to test.
        Unauthorized scanning may be illegal in your jurisdiction.
        """
        raw = arg.strip()
        if not raw:
            self.print_error(
                "Usage: /cybertest <url> [--quick] [--module <name>] [--json <path>]\n"
                "Example: /cybertest https://example.com\n"
                "         /cybertest https://example.com --quick\n"
                "         /cybertest https://example.com --module injection --module xss\n"
                "         /cybertest https://example.com --json report.json\n"
                "\n⚠️  Only scan sites you own or have written permission to test."
            )
            return

        # Parse optional flags from arg
        flags = raw.split()
        url = flags[0]
        quick = False
        modules: list[str] = []
        json_path: str | None = None
        i = 1
        while i < len(flags):
            f = flags[i]
            if f == "--quick":
                quick = True
            elif f == "--module" and i + 1 < len(flags):
                i += 1
                modules.append(flags[i])
            elif f == "--json" and i + 1 < len(flags):
                i += 1
                json_path = flags[i]
            i += 1

        # Normalize
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        import urllib.parse as _up
        parsed = _up.urlparse(url)
        if not parsed.hostname:
            self.print_error(f"Invalid URL: {url!r}")
            return

        try:
            from flashy_cli.cybertest import CyberScanner
        except ImportError as e:
            self.print_error(f"CyberTest module not available: {e}")
            return

        # Use a VT100-capable console to avoid UnicodeEncodeError on Windows
        # when Rich tries to encode box-drawing characters (┌── etc.) into CP1252.
        from rich.console import Console as RichConsole
        scan_console = RichConsole(force_terminal=True)

        # Warn / confirm
        scan_console.print()
        scan_console.print(
            f"[bold red]⚠  ETHICAL USE NOTICE[/bold red]\n"
            f"[dim]You are about to scan:[/dim] [bold cyan]{url}[/bold cyan]\n"
            "[dim]Only proceed if you own this site or have explicit written authorization.\n"
            "Unauthorized scanning can be illegal. Flashy and its authors bear no liability.[/dim]"
        )
        scan_console.print()

        scanner = CyberScanner(console=scan_console)

        mode = "quick" if quick else f"{len(modules) if modules else 'full'} module{'s' if len(modules) != 1 else ''}"
        self.print_info(f"Starting ethical security scan of {url} ({mode}) …")
        scan_console.print("[dim]This may take 30–120 seconds depending on the target.[/dim]\n")

        try:
            # Run synchronous scan in a thread so we don't block the event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: scanner.scan(url, quick=quick, modules=modules or None),
            )
            scanner.render(result, json_path=json_path)

            # Inject the scan summary into conversation context so the AI can advise
            counts = result.counts()
            critical = counts.get("CRITICAL", 0)
            high     = counts.get("HIGH", 0)
            medium   = counts.get("MEDIUM", 0)
            findings_text = "\n".join(
                f"[{f.severity}] {f.module}: {f.title}"
                + (f"\n  → Fix: {f.remediation}" if f.remediation and f.severity not in ("OK", "INFO") else "")
                for f in result.by_severity()
                if f.severity not in ("OK", "INFO")
            )
            summary_msg = (
                f"I just ran an ethical security scan on {url}.\n\n"
                f"Results: {critical} CRITICAL, {high} HIGH, {medium} MEDIUM findings.\n\n"
                f"Key vulnerabilities found:\n{findings_text or 'None above INFO level.'}\n\n"
                f"Scanned in {result.elapsed:.1f}s. Please help me prioritize and fix these issues."
            )
            # Store as last user text so AI can reference it
            self._last_user_text = summary_msg

        except Exception as exc:
            self.print_error(f"Scan failed: {exc}")
            import traceback
            self.console.print(f"[dim]{traceback.format_exc()}[/dim]")


    # Main loop
    # ------------------------------------------------------------------
    async def run(self, initial_query: str = "", interactive: bool = False) -> None:
        if not self.no_banner:
            self.print_welcome()
        self.llm_service.set_workspace(self.workspace, self.session_id)
        self._hydrate_from_resumed_session()

        if initial_query:
            await self._handle_input(initial_query, echo=True)
            if not interactive:
                await self._maybe_autosave()
                return

        while True:
            try:
                user_input = await self._prompt()
            except (KeyboardInterrupt, EOFError):
                self.print_info("Goodbye.")
                await self._maybe_autosave()
                return
            if not user_input.strip():
                continue
            try:
                if await self._handle_command(user_input.strip()):
                    continue
                await self._handle_input(user_input, echo=True)
            except (KeyboardInterrupt, EOFError):
                self.print_info("Goodbye.")
                await self._maybe_autosave()
                return
            except asyncio.CancelledError:
                self.print_info("Cancelled.")
                break

    async def _maybe_autosave(self) -> None:
        if not self.auto_save:
            return
        if not self._last_user_text:
            return
        try:
            self.save_current_session(silent=True)
        except Exception:
            pass

    async def _prompt(self) -> str:
        usage = self.get_context_usage()

        provider  = self.config.get("active_provider", "g4f")
        model     = self.config.get("model", "unknown")
        reasoning = self._reasoning_label()
        mode      = self._mode_label()

        # Prefer the full-screen TUI; fall back to PromptSession or plain input
        active = self.tui if self.tui is not None else self.prompt_session

        return await self.ui.prompt_user(
            active,
            self.workspace,
            provider,
            model,
            reasoning,
            mode,
            usage,
        )

    async def _handle_command(self, raw: str) -> bool:
        lower = raw.lower()
        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if lower in {"exit", "quit", "/q", "/exit", "/quit"}:
            raise EOFError
        if cmd in {"/help", "help", "?"}:
            self.print_help()
            return True
        if cmd in {"/status", "/doctor"}:
            await self.print_status()
            return True
        if cmd in {"/workspace", "/cwd"}:
            if arg:
                self._set_workspace(arg)
            else:
                self.print_info(f"Workspace: {shorten_path(self.workspace)}")
            return True
        if cmd == "/config":
            self.print_config_summary()
            return True
        if cmd == "/tools":
            self.print_tools()
            return True
        if cmd in {"/clear", "/reset"}:
            self._reset_session(clear_screen=True)
            return True
        if cmd in {"/model", "/provider"}:
            await self.handle_model_switch()
            return True
        if cmd == "/theme":
            await self.handle_theme_switch(arg)
            return True
        if cmd == "/todo":
            await self.handle_todo_command()
            return True
        if cmd == "/compact":
            await self.handle_manual_compact()
            return True
        if cmd in {"/thinking", "/think", "/reasoning"}:
            await self.handle_thinking()
            return True
        if cmd in {"/verbose", "/thoughts"}:
            self.show_thinking = not self.show_thinking
            self.config["show_thinking"] = self.show_thinking
            save_config(self.config)
            self.print_info(f"Streamed thinking is now {'on' if self.show_thinking else 'off'}.")
            return True
        if cmd == "/save":
            self.handle_save(arg)
            return True
        if cmd == "/load":
            self.handle_load(arg)
            return True
        if cmd in {"/sessions", "/history", "/list"}:
            self.handle_sessions(arg)
            return True
        if cmd in {"/resume", "/continue"}:
            target = arg.strip()
            if not target:
                session = last_session(self.workspace)
                if not session:
                    self.print_info("No previous session in this workspace.")
                    return True
                target = session.id
            self.handle_load(target)
            return True
        if cmd == "/export":
            self.handle_export(arg)
            return True
        if cmd == "/copy":
            self.handle_copy()
            return True
        if cmd in {"/init", "/init-project", "/rules"}:
            self.handle_init_project()
            return True
        if cmd == "/cybertest":
            await self.handle_cybertest(arg)
            return True
        return False

    def _thinking_flags(self) -> tuple[bool, str]:
        reasoning_effort = self.config.get("reasoning_effort", "medium")
        if reasoning_effort == "off":
            return False, "Disabled"
        if reasoning_effort == "low":
            return True, "Fast"
        if reasoning_effort == "high":
            return True, "Deep"
        return True, "Auto"

    async def _process_input(self, user_input: str) -> None:
        self._turn_counter += 1
        self._assistant_header()
        started_at = time.perf_counter()
        accumulated_text = ""
        thinking_seen = False
        tools_seen = 0
        thinking_enabled, thinking_mode = self._thinking_flags()

        # Build the final prompt with attached files.
        final_input = user_input
        if self._pending_attachments:
            attachment_block = "\n\n".join(
                f"--- {shorten_path(path)} ---\n{content}" for path, content in self._pending_attachments
            )
            final_input = f"{user_input}\n\n{attachment_block}"
            self.print_dim(f"attached {len(self._pending_attachments)} file(s)\n", end="")
            self._pending_attachments.clear()

        # Echo the user message.
        if RICH_AVAILABLE:
            self.console.print(
                Text.assemble(
                    ("You", f"bold {self.ui.palette.user}"),
                    (f" [{self.get_context_usage()}]", "dim"),
                    (": ", ""),
                    (user_input, ""),
                )
            )
        else:
            print(f"\nYou [{self.get_context_usage()}]: {user_input}")

        thinking_streamer = ThinkingStreamer(self.ui.console, self.show_thinking, self.ui.palette)

        esc_listener = None
        stop_esc = ThreadEvent()
        if os.name == "nt":
            esc_listener = asyncio.ensure_future(self._esc_listener(stop_esc))

        try:
            async for chunk in self.llm_service.generate_response(
                text=final_input,
                session_id=self.session_id,
                chat_type="t2t",
                thinking_enabled=thinking_enabled,
                thinking_mode=thinking_mode,
                reasoning_effort=self.config.get("reasoning_effort", "medium"),
            ):
                if "error" in chunk:
                    self.print_error(chunk["error"])

                if "thought" in chunk:
                    token = str(chunk["thought"])
                    if self.show_thinking:
                        thinking_streamer.write(token)
                    elif not thinking_seen:
                        thinking_seen = True
                        self.print_dim("thinking...\n", end="")

                if "tool_call" in chunk:
                    if thinking_streamer.started:
                        thinking_streamer.end()
                    tools_seen += 1
                    self._last_tool_started_at = time.perf_counter()
                    self._last_tool_name = chunk["tool_call"].get("name")
                    action = self.ui.format_tool_action(
                        chunk["tool_call"].get("name", "tool"),
                        chunk["tool_call"].get("args", {}),
                        self.workspace,
                    )
                    if RICH_AVAILABLE and self.console:
                        self.console.print(action)
                    else:
                        print(action)

                if "tool_result" in chunk:
                    result = chunk["tool_result"]
                    elapsed = time.perf_counter() - (self._last_tool_started_at or time.perf_counter())
                    res = self.ui.format_tool_result(result, elapsed)
                    if RICH_AVAILABLE and self.console:
                        self.console.print(res)
                    else:
                        print(res)
                    self._last_tool_started_at = None

                if "text" in chunk:
                    token = str(chunk["text"])
                    if thinking_streamer.started:
                        thinking_streamer.end()
                    accumulated_text += token

                if chunk.get("is_final"):
                    if thinking_streamer.started:
                        thinking_streamer.end()
                    if accumulated_text:
                        import re as _re
                        cleaned = _re.sub(r'<tool_call>.*?</tool_call>|««TOOL_CALL»».*?««/TOOL_CALL»»', '', accumulated_text, flags=_re.DOTALL).strip()
                        if cleaned:
                            self.print_agent_text(cleaned)
                            self.print_agent_text("\n")

        except asyncio.CancelledError:
            self.print_error("Interrupted by user.")
        except Exception as exc:
            self.print_error(f"Generation error: {exc}")
            flashy_logs.write("error", "generation error", error=str(exc), session=self.session_id)
        finally:
            if esc_listener is not None:
                stop_esc.set()
                esc_listener.cancel()
            if thinking_streamer.started:
                thinking_streamer.end()
            elapsed = time.perf_counter() - started_at
            if accumulated_text:
                self._last_assistant_text = accumulated_text
            self.ui.print_turn_footer(elapsed, tools_seen, self.get_context_usage())
            # Persist to disk on every turn so a crash never loses work.
            try:
                self._last_user_text = user_input
                self.save_current_session(silent=True)
                tokens_in = 0
                usage = self.llm_service.session_usage.get(self.session_id) or {}
                if isinstance(usage, dict):
                    tokens_in = int(usage.get("input_tokens", 0) or 0)
                flashy_stats.record_session(
                    provider=str(self.config.get("active_provider", "")),
                    model=str(self.config.get("model", "")),
                    turns=self._turn_counter,
                    duration_s=elapsed,
                    tokens_in=tokens_in,
                )
            except Exception:
                pass

    async def _esc_listener(self, stop: ThreadEvent) -> None:
        """Background task: interrupt generation on ESC keypress (Windows only)."""
        import msvcrt
        loop = asyncio.get_running_loop()
        while not stop.is_set():
            if msvcrt.kbhit():
                key = await loop.run_in_executor(None, msvcrt.getch)
                if key == b'\x1b':
                    self.llm_service.interrupt_session(self.session_id)
                    self.print_dim("\n⏹  Stopping...\n", end="")
                    break
            await asyncio.sleep(0.1)

    async def _handle_input(self, user_input: str, *, echo: bool = False) -> None:
        # Resolve @file attachments before processing.
        cleaned, attachments = extract_attachments(user_input, self.workspace)
        if attachments:
            self._pending_attachments.extend(attachments)
            render_attachment_summary(self.console if RICH_AVAILABLE else sys.stdout, attachments)
        await self._process_input(cleaned or user_input)

    # ------------------------------------------------------------------
    # Command views
    # ------------------------------------------------------------------
    def print_help(self) -> None:
        rows = [{"command": command, "action": action} for command, action in COMMANDS.items()]
        if RICH_AVAILABLE:
            table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan")
            table.add_column("Command", style="bold")
            table.add_column("Action")
            for row in rows:
                table.add_row(row["command"], row["action"])
            tips = Text(
                "Bare prompts go straight to the coding agent. /verbose shows raw thinking tokens. /save persists every turn.",
                style="dim",
            )
            self.console.print(Panel(Group(table, tips), title="Flashy commands", border_style="cyan", box=box.ROUNDED))
        else:
            print("\nCommands")
            for row in rows:
                print(f"  {row['command']:<12} {row['action']}")

    def print_config_summary(self) -> None:
        rows = [
            {"key": "provider", "value": self.config.get("active_provider", "N/A")},
            {"key": "model", "value": self.config.get("model", "N/A")},
            {"key": "reasoning", "value": self.config.get("reasoning_effort", "medium")},
            {"key": "max iterations", "value": self.config.get("max_agent_iterations", 25)},
            {"key": "config", "value": _home_short(CONFIG_FILE)},
        ]
        self._print_table("Active config", ["key", "value"], rows)

    def print_tools(self) -> None:
        try:
            tools = self.llm_service.get_agent(self.session_id).tools.get_available_tools()
        except Exception as exc:
            self.print_error(f"Could not load tools: {exc}")
            return
        rows = [{"name": tool.get("name", ""), "description": truncate(tool.get("description", ""), 90)} for tool in tools]
        self._print_table(f"Agent tools ({len(rows)})", ["name", "description"], rows, border_style="blue")

    async def print_status(self) -> None:
        try:
            from flashy_cli.doctor import run_diagnostics

            checks = run_diagnostics(self.workspace)
            rows = []
            problems = []
            for check in checks:
                icon = "ok" if check.ok else "warn"
                rows.append({"check": check.name, "status": icon, "detail": check.detail, "hint": check.hint})
                if not check.ok and check.name not in {"main server", "provider server", "ripgrep", "node"}:
                    problems.append(check)
            self._print_table("Session status", ["check", "status", "detail", "hint"], rows)
            if problems:
                self.print_error("Some core checks need attention before a serious coding run.")
            else:
                self.print_info("Core checks passed. Workspace and tool registry look usable.")
        except Exception as exc:
            self.print_error(f"Status check failed: {exc}")


async def start_chat(
    workspace: str | None = None,
    initial_query: str = "",
    interactive: bool = False,
    config_overrides: Optional[Dict[str, Any]] = None,
    no_banner: bool = False,
    show_thinking: bool = False,
    no_color: bool = False,
    session_id: str | None = None,
    auto_save: bool = True,
    stdin_text: str = "",
) -> None:
    cli = ChatCLI(
        workspace,
        config_overrides=config_overrides,
        no_banner=no_banner,
        show_thinking=show_thinking,
        no_color=no_color,
        session_id=session_id,
        auto_save=auto_save,
    )
    # If something was piped in on stdin, treat it as the initial query when no explicit one was provided.
    if stdin_text and not initial_query:
        initial_query = stdin_text.strip()
    await cli.run(initial_query, interactive)


def collect_stdin(timeout: float = 0.0) -> str:
    """Best-effort stdin capture. Returns the contents if a pipe is connected, else ''."""
    if not sys.stdin or not sys.stdin.isatty():
        try:
            data = sys.stdin.read()
            return data
        except Exception:
            return ""
    return ""

