"""
Subagent Definition System

Defines built-in subagent types and loads custom definitions from
.flashy/agents/*.md files. Each subagent has its own:
- System prompt / role description
- Model and provider configuration
- Tool permission scope (allow/deny lists)
"""

import os
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class ToolScope:
    allow: List[str] = field(default_factory=lambda: ["*"])
    deny: List[str] = field(default_factory=list)


@dataclass
class SubagentDef:
    name: str
    description: str
    system_prompt: str
    model: str
    provider: str
    tools: ToolScope = field(default_factory=ToolScope)


_SUBAGENTS: Dict[str, SubagentDef] = {}

# ---------------------------------------------------------------------------
# Built-in types – the defaults are usable immediately without any .flashy/
# directory.  Users can override them by placing a file in .flashy/agents/.
# ---------------------------------------------------------------------------

_BUILTIN: Dict[str, SubagentDef] = {
    "general": SubagentDef(
        name="general",
        description="General-purpose agent that can use any tool. Falls back to the parent's model/provider.",
        system_prompt=(
            "You are a general-purpose coding agent. "
            "Complete the delegated task to the best of your ability."
        ),
        model="",
        provider="",
    ),
    "explore": SubagentDef(
        name="explore",
        description="Fast codebase exploration agent. Reads files, searches, and summarizes.",
        system_prompt=(
            "You are an exploration agent specialised for reading and understanding code. "
            "Read files, search for symbols, inspect directory structures, and produce a concise summary.\n"
            "Do NOT write, edit, or delete files. Do NOT run shell commands unless reading output."
        ),
        model="deepseek-v4-flash",
        provider="openmodel",
        tools=ToolScope(
            allow=["*"],
            deny=["write_file", "write_files", "patch_file", "apply_patch",
                  "delete_path", "run_shell_command", "git_commit", "git_push",
                  "git_init", "git_clone", "spawn_subagent"],
        ),
    ),
    "researcher": SubagentDef(
        name="researcher",
        description="Web research agent. Browses docs, searches the web, and gathers information.",
        system_prompt=(
            "You are a research agent. Your job is to gather and synthesise information.\n"
            "Use web_browse, grep_search, read_file, and search_files to collect data.\n"
            "Do NOT modify any files. Do NOT run shell commands."
        ),
        model="deepseek-v4-flash",
        provider="openmodel",
        tools=ToolScope(
            allow=["web_browse", "read_file", "read_files", "search_files",
                   "grep_search", "list_dir", "get_file_tree", "activate_skill"],
            deny=[],
        ),
    ),
    "developer": SubagentDef(
        name="developer",
        description="Code implementation agent. Writes, edits, and tests code changes.",
        system_prompt=(
            "You are a developer agent. Implement code changes, write tests, "
            "run builds and verification commands, and commit when appropriate."
        ),
        model="",
        provider="",
    ),
}


def _load_markdown_def(file_path: str) -> Optional[SubagentDef]:
    """Parse a single .md frontmatter definition file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw = f.read()
    except Exception:
        return None

    # Split frontmatter from body
    if not raw.startswith("---"):
        return None
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return None
    frontmatter_str, body = parts[1].strip(), parts[2].strip()

    # Minimal YAML-like parser for the fields we need
    fields: Dict[str, str] = {}
    for line in frontmatter_str.splitlines():
        m = re.match(r"^(\w+):\s*(.+)$", line)
        if m:
            fields[m.group(1)] = m.group(2).strip().strip('"').strip("'")

    name = fields.get("name", os.path.splitext(os.path.basename(file_path))[0])
    description = fields.get("description", "")
    model = fields.get("model", "")
    provider = fields.get("provider", "")
    tools_raw = fields.get("tools", "allow all")

    tool_scope = ToolScope()
    if tools_raw.lower() in ("none", "deny all"):
        tool_scope.allow = []
    elif tools_raw.startswith("allow "):
        tool_scope.allow = [t.strip() for t in tools_raw[6:].split(",") if t.strip()]
    elif tools_raw.startswith("deny "):
        tool_scope.allow = ["*"]
        tool_scope.deny = [t.strip() for t in tools_raw[5:].split(",") if t.strip()]
    # "allow all" → default ToolScope with ["*"]

    return SubagentDef(
        name=name,
        description=description,
        system_prompt=body or description,
        model=model,
        provider=provider,
        tools=tool_scope,
    )


def load_custom_defs(workspace_path: str, global_home: Optional[str] = None):
    """Load .md files from .flashy/agents/ in workspace and global config."""
    candidates: List[str] = []

    ws_dir = os.path.join(workspace_path, ".flashy", "agents") if workspace_path else ""
    if ws_dir and os.path.isdir(ws_dir):
        for fn in sorted(os.listdir(ws_dir)):
            if fn.endswith(".md"):
                candidates.append(os.path.join(ws_dir, fn))

    if global_home:
        gl_dir = os.path.join(global_home, ".flashy", "agents")
        if os.path.isdir(gl_dir):
            for fn in sorted(os.listdir(gl_dir)):
                if fn.endswith(".md"):
                    fp = os.path.join(gl_dir, fn)
                    if fp not in candidates:
                        candidates.append(fp)

    for fp in candidates:
        d = _load_markdown_def(fp)
        if d:
            _SUBAGENTS[d.name] = d


def list_subagent_types() -> Dict[str, str]:
    """Return {name: description} of all available subagent types."""
    result = {}
    for name, d in _BUILTIN.items():
        result[name] = d.description
    for name, d in _SUBAGENTS.items():
        result[name] = d.description
    return result


def get_subagent_def(name: str) -> Optional[SubagentDef]:
    """Resolve a subagent definition (custom overrides built-in)."""
    if name in _SUBAGENTS:
        return _SUBAGENTS[name]
    return _BUILTIN.get(name)


def filter_tools(agent_type: str, available_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply tool scope filtering for a given subagent type."""
    d = get_subagent_def(agent_type)
    if not d:
        return available_tools

    scope = d.tools
    # "*" means everything is allowed (subject to deny list)
    if "*" in scope.allow:
        if not scope.deny:
            return available_tools
        denied = set(scope.deny)
        return [t for t in available_tools if t["name"] not in denied]

    allowed = set(scope.allow)
    return [t for t in available_tools if t["name"] in allowed]
