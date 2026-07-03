"""Flashy command-line application."""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .completions import all_shells, render as render_completion
from .doctor import run_diagnostics, summarize as doctor_summarize
from .runtime import (
    ROOT,
    find_free_port,
    health_rows,
    parse_config_value,
    project_version,
    redact_config,
    run_python_module,
)
from .sessions import (
    delete_session as sessions_delete,
    export as sessions_export,
    find_session as sessions_find,
    last_session,
    list_sessions,
    to_rows as sessions_to_rows,
)
from .stats import load_all as stats_load_all, reset as stats_reset, summary_lines as stats_summary, to_rows as stats_to_rows
from . import logs as flashy_logs
from . import theme as flashy_theme
from .ui import UI


def _build_parser() -> argparse.ArgumentParser:
    description = "Flashy - minimal, fast AI coding CLI."
    epilog = """
Examples:
  flashy "refactor this repo and run tests"
  flashy chat -w .
  flashy ask "explain the auth flow" --reasoning low
  flashy doctor
  flashy session list
  flashy theme set dracula
  flashy stats
  flashy completions bash
"""
    parser = argparse.ArgumentParser(
        prog="flashy",
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON where supported")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("-C", "--cwd", default=None, help="Run as if started in this directory")

    sub = parser.add_subparsers(dest="command", help="Commands")

    p_chat = sub.add_parser("chat", aliases=["ask", "interactive"], help="Start an AI coding session")
    p_chat.add_argument("query", nargs="*", help="Initial query. Without one, starts interactive mode.")
    p_chat.add_argument("-w", "--workspace", default=None, help="Workspace directory, default: current directory")
    p_chat.add_argument("-i", "--interactive", action="store_true", help="Stay interactive after the initial query")
    p_chat.add_argument("--provider", default=None, help="Temporarily use this provider for the session")
    p_chat.add_argument("--model", default=None, help="Temporarily use this model for the session")
    p_chat.add_argument("--reasoning", choices=["off", "low", "medium", "high"], default=None, help="Reasoning effort for the session")
    p_chat.add_argument("--max-iterations", type=int, default=None, help="Max tool-loop iterations for this session")
    p_chat.add_argument("--no-banner", action="store_true", help="Skip the welcome panel")
    p_chat.add_argument("--show-thinking", action="store_true", help="Stream raw thinking tokens instead of the clean progress view")
    p_chat.add_argument("--resume", default=None, help="Resume a session by id (or id prefix)")
    p_chat.add_argument("--continue", dest="continue_last", action="store_true", help="Resume the most recent session in this workspace")

    p_serve = sub.add_parser("serve", aliases=["start", "run"], help="Start the Flashy web server")
    p_serve.add_argument("--host", default=None, help="Host to bind, default: 127.0.0.1")
    p_serve.add_argument("--port", type=int, default=None, help="Port to bind, default: 8000")
    p_serve.add_argument("--auto-port", action="store_true", help="Pick a free port when the requested one is busy")
    p_serve.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    p_serve.add_argument("--verbose", action="store_true", help="Verbose backend logging")

    p_server = sub.add_parser("server", help="Start the OpenAI-compatible provider server")
    p_server.add_argument("--host", default=None, help="Host to bind, default: 127.0.0.1")
    p_server.add_argument("--port", type=int, default=None, help="Port to bind, default: 8001")
    p_server.add_argument("--auto-port", action="store_true", help="Pick a free port when the requested one is busy")
    p_server.add_argument("--verbose", action="store_true", help="Verbose backend logging")

    p_status = sub.add_parser("status", help="Check local server status")
    p_status.add_argument("--port", type=int, default=8000, help="Main server port")
    p_status.add_argument("--provider-port", type=int, default=8001, help="Provider server port")

    p_config = sub.add_parser("config", help="View or modify CLI configuration")
    config_group = p_config.add_mutually_exclusive_group()
    config_group.add_argument("--show", action="store_true", help="Show redacted config")
    config_group.add_argument("--path", action="store_true", help="Show config file path")
    config_group.add_argument("--get", dest="get_key", help="Get a config value")
    config_group.add_argument("--set", dest="set_key", help="Set a config key")
    config_group.add_argument("--unset", dest="unset_key", help="Remove a config key")
    config_group.add_argument("--edit", action="store_true", help="Open the config file in $EDITOR")
    p_config.add_argument("value", nargs="?", help="Value for --set")
    p_config.add_argument("--raw", action="store_true", help="Do not redact config output")

    p_init = sub.add_parser("init", help="Create or update Flashy config")
    p_init.add_argument("--provider", default="g4f", help="Default provider")
    p_init.add_argument("--model", default="gpt-5.4-nano", help="Default model")
    p_init.add_argument("--reasoning", choices=["off", "low", "medium", "high"], default="medium", help="Default reasoning effort")
    p_init.add_argument("--yes", "-y", action="store_true", help="Use defaults without prompting")

    p_doctor = sub.add_parser("doctor", help="Run pre-flight diagnostics")
    p_doctor.add_argument("-w", "--workspace", default=None, help="Workspace to inspect")
    p_doctor.add_argument("--port", type=int, default=8000, help="Main server port")
    p_doctor.add_argument("--provider-port", type=int, default=8001, help="Provider server port")
    p_doctor.add_argument("--strict", action="store_true", help="Exit non-zero on any failed check")

    sub.add_parser("tools", help="List tools available to the coding agent")

    p_models = sub.add_parser("models", help="List available models for a provider")
    p_models.add_argument("provider", nargs="?", default=None, help="Provider to query, default: active provider")

    # Session management
    p_session = sub.add_parser("session", help="Manage chat sessions")
    session_sub = p_session.add_subparsers(dest="session_command")
    p_session_list = session_sub.add_parser("list", aliases=["ls"], help="List saved sessions")
    p_session_list.add_argument("-n", "--limit", type=int, default=20, help="Maximum sessions to show")
    p_session_list.add_argument("-w", "--workspace", default=None, help="Filter by workspace path")
    p_session_show = session_sub.add_parser("show", help="Show a session by id (or prefix)")
    p_session_show.add_argument("session_id", help="Session id or prefix")
    p_session_delete = session_sub.add_parser("delete", aliases=["rm"], help="Delete a session")
    p_session_delete.add_argument("session_id", help="Session id or prefix")
    p_session_delete.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    p_session_export = session_sub.add_parser("export", help="Export a session as markdown or json")
    p_session_export.add_argument("session_id", help="Session id or prefix")
    p_session_export.add_argument("--format", choices=["md", "json"], default="md", help="Export format")
    p_session_export.add_argument("--output", "-o", default=None, help="Output file (default: <title>.<ext>)")
    p_session_resume = session_sub.add_parser("resume", help="Resume a session in chat")
    p_session_resume.add_argument("session_id", nargs="?", default=None, help="Session id or prefix (default: most recent)")
    p_session_resume.add_argument("-w", "--workspace", default=None, help="Workspace filter for the most-recent lookup")

    # Theme
    p_theme = sub.add_parser("theme", help="List or switch themes")
    theme_sub = p_theme.add_subparsers(dest="theme_command")
    theme_sub.add_parser("list", help="List available themes")
    p_theme_set = theme_sub.add_parser("set", help="Set the active theme")
    p_theme_set.add_argument("name", help="Theme name")
    p_theme_show = theme_sub.add_parser("show", help="Show the current theme")

    # Stats
    p_stats = sub.add_parser("stats", help="Show local session statistics")
    p_stats.add_argument("--reset", action="store_true", help="Reset all statistics")

    # Logs
    p_logs = sub.add_parser("logs", help="View or clear Flashy logs")
    p_logs.add_argument("-n", "--limit", type=int, default=20, help="Number of recent log lines")
    p_logs.add_argument("--level", default=None, help="Filter by level (info, warn, error, debug)")
    p_logs.add_argument("--clear", action="store_true", help="Clear the log file")
    p_logs.add_argument("--path", action="store_true", help="Print the log file path")

    # Completions
    p_compl = sub.add_parser("completions", help="Print shell completion scripts")
    p_compl.add_argument("shell", nargs="?", default=None, help="bash, zsh, fish, or powershell")
    p_compl.add_argument("--list", action="store_true", help="List supported shells")

    sub.add_parser("version", help="Show version and runtime info")
    return parser


def _ui(args: argparse.Namespace) -> UI:
    return UI(json_mode=bool(getattr(args, "json", False)), no_color=bool(getattr(args, "no_color", False)))


def _apply_cwd(args: argparse.Namespace) -> None:
    cwd = getattr(args, "cwd", None)
    if cwd:
        os.chdir(Path(cwd).expanduser().resolve())


def _ensure_setup(ui: UI) -> bool:
    """Make sure a config exists; prompt the user to run `flashy init` if not."""
    try:
        from backend.config import CONFIG_FILE, load_config
    except Exception as exc:
        ui.error(f"Could not import backend: {exc}")
        return False
    if not Path(CONFIG_FILE).exists():
        ui.warn(f"No config found at {CONFIG_FILE}.")
        if ui.confirm("Run `flashy init` with sensible defaults now?", default=True):
            cmd_init(
                argparse.Namespace(
                    provider="g4f",
                    model="gpt-5.4-nano",
                    reasoning="medium",
                    yes=True,
                ),
                ui,
            )
            return True
        ui.hint("You can run `flashy init` later to create one.")
        return False
    return True


def cmd_serve(args: argparse.Namespace, ui: UI) -> None:
    host = args.host or os.environ.get("FLASHY_HOST", "127.0.0.1")
    port = args.port or int(os.environ.get("FLASHY_PORT", "8000"))
    if args.auto_port:
        port = find_free_port(port, host)
    env: dict[str, str] = {"FLASHY_HOST": host, "FLASHY_PORT": str(port)}
    if args.no_reload:
        env["FLASHY_RELOAD"] = ""
    if args.verbose:
        env["FLASHY_LOG_LEVEL"] = "DEBUG"
    flashy_logs.write("info", "starting main server", host=host, port=port)
    ui.panel("Flashy server", f"http://{host}:{port}\nCtrl+C to stop", style="cyan")
    run_python_module("backend.app", env=env)


def cmd_server(args: argparse.Namespace, ui: UI) -> None:
    host = args.host or os.environ.get("FLASHY_PROVIDER_HOST", "127.0.0.1")
    port = args.port or int(os.environ.get("FLASHY_PROVIDER_PORT", "8001"))
    if args.auto_port:
        port = find_free_port(port, host)
    env: dict[str, str] = {"FLASHY_PROVIDER_HOST": host, "FLASHY_PROVIDER_PORT": str(port)}
    if args.verbose:
        env["FLASHY_LOG_LEVEL"] = "DEBUG"
    flashy_logs.write("info", "starting provider server", host=host, port=port)
    ui.panel("Flashy provider server", f"http://{host}:{port}\nCtrl+C to stop", style="magenta")
    run_python_module("backend.server_app", env=env)


def cmd_status(args: argparse.Namespace, ui: UI) -> None:
    rows = health_rows(args.port, args.provider_port)
    if ui.json_mode:
        ui.json(rows)
    else:
        ui.table("Flashy status", rows, ["service", "status", "url", "details"])


def cmd_config(args: argparse.Namespace, ui: UI) -> None:
    from backend.config import CONFIG_FILE, load_config, save_config

    if args.edit:
        if not Path(CONFIG_FILE).exists():
            ui.error(f"Config not found: {CONFIG_FILE}")
            raise SystemExit(1)
        editor = os.environ.get("EDITOR") or ("notepad" if sys.platform == "win32" else "vi")
        try:
            import subprocess

            subprocess.run([editor, CONFIG_FILE], check=False)
            return
        except FileNotFoundError:
            ui.error(f"Editor not found: {editor}")
            raise SystemExit(1)

    config = load_config()
    if args.path:
        ui.json({"path": CONFIG_FILE}) if ui.json_mode else ui.print(CONFIG_FILE)
        return
    if args.get_key:
        if args.get_key not in config:
            ui.error(f"Key not found: {args.get_key}")
            raise SystemExit(1)
        value = config[args.get_key]
        ui.json({args.get_key: value}) if ui.json_mode else ui.print(str(value))
        return
    if args.set_key:
        if args.value is None:
            ui.error("Missing value for --set")
            raise SystemExit(2)
        value = parse_config_value(args.value)
        config[args.set_key] = value
        save_config(config)
        ui.json({"set": args.set_key, "value": value}) if ui.json_mode else ui.success(f"Set {args.set_key}")
        return
    if args.unset_key:
        existed = args.unset_key in config
        config.pop(args.unset_key, None)
        save_config(config)
        ui.json({"unset": args.unset_key, "existed": existed}) if ui.json_mode else ui.success(f"Unset {args.unset_key}" if existed else f"Key was not set: {args.unset_key}")
        return

    output = dict(sorted(config.items())) if args.raw else redact_config(config)
    if ui.json_mode:
        ui.json(output)
    else:
        ui.print(f"Config: {CONFIG_FILE}")
        for key, value in output.items():
            ui.print(f"  {key}: {value}")


def cmd_init(args: argparse.Namespace, ui: UI) -> None:
    from backend.config import CONFIG_FILE, load_config, save_config

    if not args.yes:
        ui.info("Flashy will set up the following defaults:")
        ui.print(f"  provider  = {args.provider}")
        ui.print(f"  model     = {args.model}")
        ui.print(f"  reasoning = {args.reasoning}")
        if not ui.confirm("Apply these defaults?", default=True):
            ui.hint("Re-run `flashy init` with custom flags, e.g. `flashy init --provider gemini --model gemini-2.5-pro`.")
            return

    config = load_config()
    config.update({"active_provider": args.provider, "model": args.model, "reasoning_effort": args.reasoning})
    save_config(config)
    data = {"config": CONFIG_FILE, "active_provider": args.provider, "model": args.model, "reasoning_effort": args.reasoning}
    if ui.json_mode:
        ui.json(data)
    else:
        ui.success("Flashy config is ready.")
        ui.print(f"  Config:   {CONFIG_FILE}")
        ui.print(f"  Provider: {args.provider}")
        ui.print(f"  Model:    {args.model}")
        ui.print(f"  Reasoning: {args.reasoning}")


def cmd_doctor(args: argparse.Namespace, ui: UI) -> None:
    checks = run_diagnostics(args.workspace, args.port, args.provider_port)
    if ui.json_mode:
        ui.json(doctor_summarize(checks))
        return
    rows = [check.as_row() for check in checks]
    ui.table("Flashy doctor", rows, ["check", "status", "detail", "hint"])
    summary = doctor_summarize(checks)
    if summary["failed"]:
        ui.warn(f"{summary['failed']} check(s) need attention before a serious coding session.")
        if args.strict:
            raise SystemExit(1)
    else:
        ui.success(f"All {summary['total']} checks passed.")


def cmd_tools(args: argparse.Namespace, ui: UI) -> None:
    from backend.tools import Tools

    tools = Tools(os.getcwd()).get_available_tools()
    rows = [{"name": t.get("name", ""), "description": t.get("description", "")} for t in tools]
    if ui.json_mode:
        ui.json(rows)
    else:
        ui.table(f"Agent tools ({len(tools)})", rows, ["name", "description"])


async def _list_models(provider: str | None) -> list[dict[str, Any]]:
    from backend.config import load_config
    from backend.server.catalog import ProviderCatalog

    config = load_config()
    selected_provider = provider or config.get("active_provider", "g4f")
    catalog = ProviderCatalog()
    data = await catalog.list_models([selected_provider])
    models = []
    for item in data.get("data", []):
        model_id = item.get("id", "")
        models.append({"provider": selected_provider, "id": model_id, "name": item.get("name", model_id)})
    return models


def cmd_models(args: argparse.Namespace, ui: UI) -> None:
    try:
        rows = asyncio.run(_list_models(args.provider))
    except Exception as exc:
        ui.error(f"Could not list models: {exc}")
        raise SystemExit(1)
    if ui.json_mode:
        ui.json(rows)
    else:
        ui.table("Models", rows, ["provider", "id", "name"])


def cmd_chat(args: argparse.Namespace, ui: UI) -> None:
    from backend.cli_chat import start_chat, collect_stdin

    workspace = Path(args.workspace or os.getcwd()).expanduser().resolve()
    query = " ".join(args.query or [])
    # If the user piped data into stdin, fold it in.
    stdin_text = ""
    if not sys.stdin or not sys.stdin.isatty():
        try:
            stdin_text = sys.stdin.read()
        except Exception:
            stdin_text = ""
        if stdin_text and stdin_text.strip():
            if query:
                query = f"{query}\n\n--- stdin ---\n{stdin_text}"
            else:
                query = stdin_text
    overrides: dict[str, Any] = {}
    if args.provider:
        overrides["active_provider"] = args.provider
    if args.model:
        overrides["model"] = args.model
    if args.reasoning:
        overrides["reasoning_effort"] = args.reasoning
    if args.max_iterations:
        overrides["max_agent_iterations"] = max(1, args.max_iterations)

    resume_id = getattr(args, "resume", None)
    continue_last = bool(getattr(args, "continue_last", False))
    if resume_id:
        session = sessions_find(resume_id)
        if not session:
            ui.error(f"No session matches '{resume_id}'.")
            raise SystemExit(1)
        ui.info(f"Resuming session {session.id} ({session.short_title()})")
        query = query or (session.messages[-1].content if session.messages and isinstance(session.messages[-1].content, str) else "")
        if not session.workspace:
            session.workspace = str(workspace)
        workspace = Path(session.workspace)
        overrides.setdefault("active_provider", session.provider or overrides.get("active_provider"))
        overrides.setdefault("model", session.model or overrides.get("model"))
        overrides.setdefault("reasoning_effort", session.reasoning or overrides.get("reasoning_effort"))
        overrides["__resume_session_id"] = session.id
    elif continue_last:
        session = last_session(str(workspace))
        if session:
            ui.info(f"Continuing session {session.id} ({session.short_title()})")
            overrides.setdefault("active_provider", session.provider or overrides.get("active_provider"))
            overrides.setdefault("model", session.model or overrides.get("model"))
            overrides.setdefault("reasoning_effort", session.reasoning or overrides.get("reasoning_effort"))
            overrides["__resume_session_id"] = session.id
        else:
            ui.warn("No previous session in this workspace. Starting a new one.")

    try:
        asyncio.run(
            start_chat(
                str(workspace),
                query,
                bool(args.interactive),
                overrides or None,
                no_banner=bool(args.no_banner),
                show_thinking=bool(args.show_thinking),
                no_color=bool(getattr(args, "no_color", False)),
            )
        )
    except KeyboardInterrupt:
        ui.print("\nExiting...")


def cmd_version(args: argparse.Namespace, ui: UI) -> None:
    data = {
        "flashy_cli": __version__,
        "package": project_version(),
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "root": str(ROOT),
        "data_dir": str(_user_data_dir()),
    }
    if ui.json_mode:
        ui.json(data)
    else:
        for key, value in data.items():
            ui.print(f"{key}: {value}")


def _user_data_dir():
    from backend.desktop_runtime import user_data_dir as _d
    return _d()


# ---------------------------------------------------------------------------
# Session command
# ---------------------------------------------------------------------------


def cmd_session(args: argparse.Namespace, ui: UI) -> None:
    sub = getattr(args, "session_command", None)
    if sub in (None, "list", "ls"):
        workspace = getattr(args, "workspace", None)
        items = list_sessions(limit=getattr(args, "limit", 20) or 20, workspace=workspace)
        if ui.json_mode:
            ui.json([s.to_dict() for s in items])
            return
        if not items:
            ui.print("No saved sessions yet. Start a chat with `flashy`.")
            return
        rows = sessions_to_rows(items)
        ui.table("Saved sessions", rows, ["id", "title", "model", "turns", "updated", "workspace"])
        ui.hint("Use `flashy session show <id>` to inspect, `flashy session resume <id>` to continue.")
        return

    if sub == "show":
        session = sessions_find(args.session_id)
        if not session:
            ui.error(f"No session matches '{args.session_id}'.")
            raise SystemExit(1)
        if ui.json_mode:
            ui.json(session.to_dict())
            return
        rows = [
            {"field": "id", "value": session.id},
            {"field": "title", "value": session.short_title(120)},
            {"field": "provider", "value": session.provider or ""},
            {"field": "model", "value": session.model or ""},
            {"field": "reasoning", "value": session.reasoning},
            {"field": "turns", "value": str(session.turn_count())},
            {"field": "created", "value": session.age()},
            {"field": "workspace", "value": session.workspace or ""},
        ]
        ui.table(f"Session {session.id}", rows, ["field", "value"])
        if session.messages:
            ui.rule("last messages", style="blue")
            tail = session.messages[-4:]
            for m in tail:
                role = m.role or "?"
                content = m.content if isinstance(m.content, str) else _json_dumps(m.content)
                ui.print(f"  [bold]{role}[/bold]: {_truncate(content, 200)}" if _is_rich(ui) else f"  {role}: {_truncate(content, 200)}")
        return

    if sub in ("delete", "rm"):
        session = sessions_find(args.session_id)
        if not session:
            ui.error(f"No session matches '{args.session_id}'.")
            raise SystemExit(1)
        if not args.yes and not ui.confirm(f"Delete session {session.id} ({session.short_title(40)})?", default=False):
            ui.hint("Cancelled.")
            return
        ok = sessions_delete(session.id)
        if ui.json_mode:
            ui.json({"deleted": ok, "id": session.id})
        elif ok:
            ui.success(f"Deleted {session.id}")
        else:
            ui.error(f"Could not delete {session.id}")
            raise SystemExit(1)
        return

    if sub == "export":
        session = sessions_find(args.session_id)
        if not session:
            ui.error(f"No session matches '{args.session_id}'.")
            raise SystemExit(1)
        try:
            filename, content = sessions_export(session, args.format)
        except ValueError as exc:
            ui.error(str(exc))
            raise SystemExit(2)
        if args.output:
            target = Path(args.output).expanduser()
            try:
                target.write_text(content, encoding="utf-8")
            except Exception as exc:
                ui.error(f"Could not write {target}: {exc}")
                raise SystemExit(1)
            if ui.json_mode:
                ui.json({"path": str(target), "format": args.format, "id": session.id})
            else:
                ui.success(f"Exported to {target}")
        else:
            sys.stdout.write(content)
        return

    if sub == "resume":
        sid = args.session_id
        if not sid:
            session = last_session(getattr(args, "workspace", None))
            if not session:
                ui.error("No sessions to resume.")
                raise SystemExit(1)
            sid = session.id
        args.session_id = sid
        # Reuse chat path
        chat_args = argparse.Namespace(
            query=[],
            workspace=getattr(args, "workspace", None),
            interactive=True,
            provider=None,
            model=None,
            reasoning=None,
            max_iterations=None,
            no_banner=False,
            show_thinking=False,
            resume=sid,
            continue_last=False,
        )
        cmd_chat(chat_args, ui)
        return

    # Fallback: print help for the session command.
    parser = _build_parser()
    parser.parse_args(["session", "--help"])

def _is_rich(ui: UI) -> bool:
    return ui.console is not None


def _truncate(text: str, n: int) -> str:
    s = (text or "").replace("\n", " ").strip()
    if len(s) <= n:
        return s
    return s[: max(0, n - 1)] + "…"


def _json_dumps(data) -> str:
    import json as _json

    try:
        return _json.dumps(data, ensure_ascii=False)[:400]
    except Exception:
        return str(data)[:400]


# ---------------------------------------------------------------------------
# Theme / Stats / Logs / Completions
# ---------------------------------------------------------------------------


def cmd_theme(args: argparse.Namespace, ui: UI) -> None:
    sub = getattr(args, "theme_command", None) or "list"
    if sub == "list":
        rows = [{"name": name, "accent": p.accent, "banner": p.banner_title} for name, p in flashy_theme.THEMES.items()]
        if ui.json_mode:
            ui.json(rows)
        else:
            ui.table("Themes", rows, ["name", "accent", "banner"])
            ui.hint("Use `flashy theme set <name>` and restart chat. Set FLASHY_THEME=<name> for one-shot use.")
        return
    if sub == "set":
        name = args.name.lower()
        if name not in flashy_theme.THEMES:
            ui.error(f"Unknown theme: {name}. Try one of: {', '.join(flashy_theme.THEMES)}")
            raise SystemExit(1)
        os.environ["FLASHY_THEME"] = name
        # Best-effort: persist into config so future shells pick it up
        try:
            from backend.config import load_config, save_config
            cfg = load_config()
            cfg["theme"] = name
            save_config(cfg)
        except Exception:
            pass
        if ui.json_mode:
            ui.json({"theme": name})
        else:
            ui.success(f"Theme set to '{name}'. Restart chat to see it.")
        return
    if sub == "show":
        palette = flashy_theme.current_palette()
        # Determine the effective theme name from env first, then config.
        env_name = os.environ.get("FLASHY_THEME")
        cfg_name = None
        try:
            from backend.config import load_config as _load
            cfg_name = (_load() or {}).get("theme")
        except Exception:
            cfg_name = None
        effective = env_name or cfg_name or "default"
        if ui.json_mode:
            ui.json({"theme": effective, "source": ("env" if env_name else ("config" if cfg_name else "default")), "palette": palette.__dict__})
        else:
            ui.print(f"theme: {effective}")
            ui.print(f"source: {'env' if env_name else ('config' if cfg_name else 'default')}")
            for k, v in palette.__dict__.items():
                ui.print(f"  {k}: {v}")
        return


def cmd_stats(args: argparse.Namespace, ui: UI) -> None:
    if args.reset:
        if not ui.confirm("Reset all Flashy statistics?", default=False):
            ui.hint("Cancelled.")
            return
        stats_reset()
        if ui.json_mode:
            ui.json({"reset": True})
        else:
            ui.success("Statistics reset.")
        return
    data = stats_load_all()
    summary = [{"metric": k, "value": v} for k, v in stats_summary()]
    if ui.json_mode:
        ui.json({"summary": {k: v for k, v in stats_summary()}, "breakdown": stats_to_rows(), "raw": data})
    else:
        ui.table("Lifetime stats", summary, ["metric", "value"])
        breakdown = stats_to_rows()
        if breakdown:
            ui.rule("Breakdown", style="blue")
            ui.table("Usage by provider/model", breakdown, ["name", "type", "count", "share"])


def cmd_logs(args: argparse.Namespace, ui: UI) -> None:
    if args.path:
        ui.print(str(flashy_logs.log_path()))
        return
    if args.clear:
        if flashy_logs.clear():
            ui.success("Logs cleared.")
        else:
            ui.hint("No logs to clear.")
        return
    rows = flashy_logs.tail(limit=args.limit, level=args.level)
    if ui.json_mode:
        ui.json(rows)
        return
    if not rows:
        ui.hint("No log lines yet.")
        return
    for row in rows:
        ts = row.get("iso") or row.get("ts") or "?"
        level = str(row.get("level", "info")).upper()
        msg = row.get("msg", "")
        level_color = {"ERROR": "red", "WARN": "yellow", "DEBUG": "dim", "INFO": "cyan"}.get(level, "white")
        ui.print(f"[dim]{ts}[/dim] [{level_color}]{level}[/{level_color}] {msg}" if ui.console else f"{ts} {level} {msg}")


def cmd_completions(args: argparse.Namespace, ui: UI) -> None:
    if args.list or not args.shell:
        shells = all_shells()
        if ui.json_mode:
            ui.json(shells)
        else:
            ui.print("Supported shells: " + ", ".join(shells))
            ui.print("Example: flashy completions bash >> ~/.bashrc")
        return
    try:
        script = render_completion(args.shell)
    except ValueError as exc:
        ui.error(str(exc))
        raise SystemExit(1)
    sys.stdout.write(script)
    if not script.endswith("\n"):
        sys.stdout.write("\n")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


KNOWN_COMMANDS = {
    "serve", "start", "run", "server", "status", "config", "init", "doctor",
    "tools", "models", "chat", "ask", "interactive", "version",
    "session", "theme", "stats", "logs", "completions",
}


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args_list = list(argv if argv is not None else sys.argv[1:])
    # Accept common global flags before or after subcommands, matching modern CLIs.
    for global_flag in ("--json", "--no-color"):
        if global_flag in args_list:
            args_list = [arg for arg in args_list if arg != global_flag]
            args_list.insert(0, global_flag)
    first_positional = next((arg for arg in args_list if not arg.startswith("-")), None)
    if args_list and first_positional and first_positional not in KNOWN_COMMANDS:
        insert_at = args_list.index(first_positional)
        args_list.insert(insert_at, "chat")

    args = parser.parse_args(args_list)
    _apply_cwd(args)
    ui = _ui(args)

    if args.command in (None, "chat", "ask", "interactive"):
        if args.command is None:
            args = parser.parse_args(["chat"])
            ui = _ui(args)
        # Make sure config exists before launching chat.
        if not _ensure_setup(ui):
            sys.exit(0)
        cmd_chat(args, ui)
    elif args.command in ("serve", "start", "run"):
        cmd_serve(args, ui)
    elif args.command == "server":
        cmd_server(args, ui)
    elif args.command == "status":
        cmd_status(args, ui)
    elif args.command == "config":
        cmd_config(args, ui)
    elif args.command == "init":
        cmd_init(args, ui)
    elif args.command == "doctor":
        cmd_doctor(args, ui)
    elif args.command == "tools":
        cmd_tools(args, ui)
    elif args.command == "models":
        cmd_models(args, ui)
    elif args.command == "version":
        cmd_version(args, ui)
    elif args.command == "session":
        cmd_session(args, ui)
    elif args.command == "theme":
        cmd_theme(args, ui)
    elif args.command == "stats":
        cmd_stats(args, ui)
    elif args.command == "logs":
        cmd_logs(args, ui)
    elif args.command == "completions":
        cmd_completions(args, ui)
    else:  # pragma: no cover
        parser.print_help()
        raise SystemExit(2)


if __name__ == "__main__":
    main()

