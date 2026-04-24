import os
import subprocess
import glob
import tempfile
import shutil
import json
import asyncio
from typing import Optional, List, Dict, Any

from ..git_manager import GitManager
from ..websocket_manager import ws_manager

class ToolRegistryMixin:
    @staticmethod
    def _normalize_tool_name(tool_name: str) -> str:
        if tool_name is None:
            return ""
        normalized = str(tool_name).strip().strip("`'\"")
        alias_map = {
            "read": "read_file",
            "cat": "read_file",
            "bash": "run_shell_command",
            "run_command": "run_shell_command",
            "shell_command": "run_shell_command",
            "execute_command": "run_shell_command",
            "glob": "search_files",
            "question": "ask_user_question",
            "ask": "ask_user_question",
            "ls": "list_dir",
            "tree": "get_file_tree",
        }
        return alias_map.get(normalized, normalized)

    @staticmethod
    def _normalize_tool_args(tool_name: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        args = dict(kwargs or {})

        if tool_name == "read_file":
            if "path" not in args:
                args["path"] = args.get("filePath") or args.get("file_path") or args.get("target")
        elif tool_name == "run_shell_command":
            if "command" not in args:
                args["command"] = args.get("cmd") or args.get("script")
        elif tool_name == "search_files":
            if "pattern" not in args:
                args["pattern"] = args.get("glob") or args.get("query")
        elif tool_name == "ask_user_question":
            if "question" not in args:
                args["question"] = args.get("prompt") or args.get("text")

        return {k: v for k, v in args.items() if v is not None}

    def get_available_tools(self) -> list:
        """Return list of available tools with descriptions."""
        return [
            {"name": "read_file", "description": "Read file contents. Args: path (str)"},
            {"name": "read_files", "description": "Read multiple files. Args: paths (list[str]), max_bytes (int, optional)"},
            {"name": "write_file", "description": "Write/create file. Args: path (str), content (str)"},
            {"name": "write_files", "description": "Write multiple files. Args: files (list of {path, content})"},
            {"name": "patch_file", "description": "Replace a specific block of text. Args: path (str), target (str), replacement (str)"},
            {"name": "apply_patch", "description": "Apply a unified diff patch. Args: patch (str)"},
            {"name": "list_dir", "description": "List directory contents. Args: path (str, optional)"},
            {"name": "get_file_tree", "description": "Get recursive tree view text. Args: path (str, optional), max_depth (int, default 2)"},
            {"name": "get_explorer_data", "description": "Get recursive directory structure as JSON for UI. Args: path (str, optional)"},
            {"name": "search_files", "description": "Search for files by name pattern. Args: pattern (str), path (str, optional)"},
            {"name": "grep_search", "description": "Search for text inside files. Args: query (str), path (str, optional), extensions (list, optional)"},
            {"name": "run_shell_command", "description": "Execute shell command. Args: command (str), cwd (str, optional), timeout (int, optional), is_background (bool, optional)"},
            {"name": "read_background_output", "description": "Read logs of a background process. Args: process_id (str)"},
            {"name": "list_background_processes", "description": "List all background processes. No args."},
            {"name": "ask_user_question", "description": "Pause execution to ask the user a question and wait for their response. Args: question (str)"},
            {"name": "save_memory", "description": "Save persistent project rules/preferences. Args: category (str), title (str), content (str)"},
            {"name": "todo_write", "description": "Write to the agent's plan/scratchpad. Args: content (str)"},
            {"name": "delete_path", "description": "Delete file/directory. Args: path (str)"},
            {"name": "spawn_subagent", "description": "Spawn a specialized sub-agent for a focused task. Args: agent_type (str), task (str)"},
            {"name": "activate_skill", "description": "Load a specific file-based skill to adopt expert behaviors. Args: skill_name (str)"},
            {"name": "get_dependencies", "description": "Analyze project dependencies. No args."},
            {"name": "get_symbol_info", "description": "Find definition of a symbol. Args: symbol_name (str)"},
            {"name": "self_check", "description": "Run a global health check for tools and environment. No args."},
            {"name": "git_status", "description": "Get git status. No args."},
            {"name": "git_commit", "description": "Commit all changes. Args: message (str)"},
            {"name": "git_push", "description": "Push changes. Args: remote (str, optional), branch (str, optional)"},
            {"name": "git_pull", "description": "Pull changes. Args: remote (str, optional), branch (str, optional)"},
            {"name": "git_branches", "description": "List all branches. No args."},
            {"name": "git_checkout", "description": "Switch/create branch. Args: branch (str), create (bool, optional)"},
            {"name": "git_log", "description": "Show commit history. Args: limit (int, optional)"},
            {"name": "git_clone", "description": "Clone a repo. Args: url (str), path (str, optional)"},
            {"name": "git_init", "description": "Initialize a new git repo. No args."},
        ]

    async def execute(self, tool_name: str, **kwargs) -> str:
        """Execute a tool by name with given arguments."""
        requested_tool_name = tool_name
        tool_name = self._normalize_tool_name(tool_name)
        kwargs = self._normalize_tool_args(tool_name, kwargs)
        tool_map = {
            # File System Tools
            "read_file": self.read_file,
            "read_files": self.read_files,
            "write_file": self.write_file,
            "write_files": self.write_files,
            "patch_file": self.patch_file,
            "apply_patch": self.apply_patch,
            "list_dir": self.list_dir,
            "get_file_tree": self.get_file_tree,
            "get_explorer_data": self.get_explorer_data,
            "search_files": self.search_files,
            "grep_search": self.grep_search,
            "run_shell_command": self.run_shell_command,
            "read_background_output": self.read_background_output,
            "list_background_processes": self.list_background_processes,
            "ask_user_question": self.ask_user_question,
            "save_memory": self.save_memory,
            "todo_write": self.todo_write,
            "delete_path": self.delete_path,
            "spawn_subagent": self.spawn_subagent,
            "activate_skill": self.activate_skill,
            # Analysis Tools
            "get_dependencies": self.get_dependencies,
            "get_symbol_info": self.get_symbol_info,
            # Git Tools
            "self_check": self.self_check,
            "git_status": self.git_status,
            "git_commit": self.git_commit,
            "git_push": self.git_push,
            "git_pull": self.git_pull,
            "git_branches": self.git_branches,
            "git_checkout": self.git_checkout,
            "git_log": self.git_log,
            "git_clone": self.git_clone,
            "git_init": self.git_init,
        }
        
        if tool_name not in tool_map:
            return f"Error: Unknown tool '{requested_tool_name}'. Available: {list(tool_map.keys())}"
        
        try:
            func = tool_map[tool_name]
            import inspect
            if inspect.iscoroutinefunction(func):
                result = await func(**kwargs)
            else:
                result = func(**kwargs)
            if not isinstance(result, str):
                try:
                    return json.dumps(result, indent=2, ensure_ascii=False)
                except Exception:
                    return str(result)
            return result
        except TypeError as e:
            return f"Error: Invalid arguments for '{tool_name}': {str(e)}"
        except KeyError as e:
            return f"Error: Missing key requirement for '{tool_name}': {str(e)}"
        except Exception as e:
            return f"Error executing '{tool_name}': {type(e).__name__}: {str(e)}"
