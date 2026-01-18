"""
Coding Agent Prompts Module

This module provides production-grade system prompts, tool definitions,
and structured guidance for the Flashy Coding Agent.

Features:
- Comprehensive tool definitions with examples
- Structured planning and execution protocols
- Error handling and recovery strategies
- Code quality and best practices guidance
"""

from typing import Dict, Any, List


# =============================================================================
# TOOL SCHEMAS - Detailed tool definitions with types, examples, and constraints
# =============================================================================

TOOL_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "read_file": {
        "name": "read_file",
        "description": "Read the contents of a single file. Use for understanding existing code before modifications.",
        "parameters": {
            "path": {
                "type": "string",
                "required": True,
                "description": "Relative or absolute path to the file"
            }
        },
        "returns": "File contents wrapped in code blocks, or error message",
        "example": '{"action": "read_file", "args": {"path": "src/utils/helpers.py"}}',
        "best_practices": [
            "Always read a file before attempting to modify it",
            "Check file existence before reading"
        ]
    },
    "read_files": {
        "name": "read_files",
        "description": "Read multiple files in a single operation. Efficient for understanding related code.",
        "parameters": {
            "paths": {
                "type": "array[string]",
                "required": True,
                "description": "List of file paths to read"
            },
            "max_bytes": {
                "type": "integer",
                "required": False,
                "default": 200000,
                "description": "Maximum bytes per file (truncates if exceeded)"
            }
        },
        "returns": "Contents of all files, each wrapped in code blocks",
        "example": '{"action": "read_files", "args": {"paths": ["src/index.js", "src/app.js"]}}',
        "best_practices": [
            "Use when you need to understand relationships between files",
            "Limit to 5-10 files to avoid context overflow"
        ]
    },
    "write_file": {
        "name": "write_file",
        "description": "Create a new file or completely overwrite an existing file. Creates parent directories automatically.",
        "parameters": {
            "path": {
                "type": "string",
                "required": True,
                "description": "Path where the file will be written"
            },
            "content": {
                "type": "string",
                "required": True,
                "description": "Complete file contents to write"
            }
        },
        "returns": "Success message with character count, or error",
        "example": '{"action": "write_file", "args": {"path": "src/new_module.py", "content": "def hello():\\n    return \\"Hello, World!\\""}}',
        "best_practices": [
            "Include complete, production-ready code",
            "Add appropriate imports and type hints",
            "Follow project conventions for formatting"
        ]
    },
    "write_files": {
        "name": "write_files",
        "description": "Write multiple files in a single operation. Atomic and efficient.",
        "parameters": {
            "files": {
                "type": "array[{path: string, content: string}]",
                "required": True,
                "description": "List of file objects with path and content"
            }
        },
        "returns": "Status for each file written",
        "example": '{"action": "write_files", "args": {"files": [{"path": "a.py", "content": "# File A"}, {"path": "b.py", "content": "# File B"}]}}',
        "best_practices": [
            "Use for creating related files together (e.g., module + tests)",
            "Ensure all files are syntactically valid"
        ]
    },
    "patch_file": {
        "name": "patch_file",
        "description": "Surgically replace a specific block of text in a file. Most efficient for targeted edits.",
        "parameters": {
            "path": {
                "type": "string",
                "required": True,
                "description": "Path to the file to patch"
            },
            "target": {
                "type": "string",
                "required": True,
                "description": "EXACT text to find and replace (including whitespace)"
            },
            "replacement": {
                "type": "string",
                "required": True,
                "description": "New text to replace the target with"
            }
        },
        "returns": "Success message or error if target not found",
        "example": '{"action": "patch_file", "args": {"path": "main.py", "target": "def old_func():", "replacement": "def new_func():"}}',
        "best_practices": [
            "CRITICAL: Target must match EXACTLY, including indentation",
            "Read the file first to get the exact text",
            "Use for small, focused changes",
            "For large changes, prefer write_file"
        ]
    },
    "apply_patch": {
        "name": "apply_patch",
        "description": "Apply a unified diff patch to modify files. Useful for complex multi-file changes.",
        "parameters": {
            "patch": {
                "type": "string",
                "required": True,
                "description": "Unified diff format patch content"
            }
        },
        "returns": "Success message or detailed error",
        "example": '{"action": "apply_patch", "args": {"patch": "--- a/file.py\\n+++ b/file.py\\n@@ -1,3 +1,3 @@\\n-old line\\n+new line"}}',
        "best_practices": [
            "Ensure diff format is correct (use --- a/ and +++ b/ prefixes)",
            "Context lines help ensure correct placement"
        ]
    },
    "list_dir": {
        "name": "list_dir",
        "description": "List files and directories in a path. Shows icons for type distinction.",
        "parameters": {
            "path": {
                "type": "string",
                "required": False,
                "default": ".",
                "description": "Directory path to list (default: current)"
            }
        },
        "returns": "Formatted list with 📁 for dirs and 📄 for files",
        "example": '{"action": "list_dir", "args": {"path": "src"}}',
        "best_practices": [
            "Use to explore project structure",
            "Start with root to understand project layout"
        ]
    },
    "get_file_tree": {
        "name": "get_file_tree",
        "description": "Get a recursive tree view of directory structure. Excellent for project overview.",
        "parameters": {
            "path": {
                "type": "string",
                "required": False,
                "default": ".",
                "description": "Root path for the tree"
            },
            "max_depth": {
                "type": "integer",
                "required": False,
                "default": 2,
                "description": "Maximum recursion depth"
            }
        },
        "returns": "ASCII tree representation of directory structure",
        "example": '{"action": "get_file_tree", "args": {"path": ".", "max_depth": 3}}',
        "best_practices": [
            "Use early in task to understand codebase",
            "Increase max_depth for deeper exploration"
        ]
    },
    "search_files": {
        "name": "search_files",
        "description": "Search for files matching a glob pattern. Finds files by name.",
        "parameters": {
            "pattern": {
                "type": "string",
                "required": True,
                "description": "Glob pattern (e.g., '*.py', 'test_*.js')"
            },
            "path": {
                "type": "string",
                "required": False,
                "default": ".",
                "description": "Starting directory for search"
            }
        },
        "returns": "List of matching file paths (capped at 50)",
        "example": '{"action": "search_files", "args": {"pattern": "*.test.js", "path": "src"}}',
        "best_practices": [
            "Use specific patterns to limit results",
            "Combine with read_file to examine matches"
        ]
    },
    "grep_search": {
        "name": "grep_search",
        "description": "Search for text content inside files. Case-insensitive. Essential for finding code references.",
        "parameters": {
            "query": {
                "type": "string",
                "required": True,
                "description": "Text or pattern to search for"
            },
            "path": {
                "type": "string",
                "required": False,
                "default": ".",
                "description": "Starting directory"
            },
            "extensions": {
                "type": "array[string]",
                "required": False,
                "description": "Filter by file extensions (e.g., ['.py', '.js'])"
            }
        },
        "returns": "Matching lines with file:line format (capped at 50)",
        "example": '{"action": "grep_search", "args": {"query": "def calculate", "extensions": [".py"]}}',
        "best_practices": [
            "Use to find function/class definitions",
            "Use to trace imports and dependencies",
            "Limit with extensions for large codebases"
        ]
    },
    "run_command": {
        "name": "run_command",
        "description": "Execute a shell command. Use for running tests, builds, installations, and any CLI operation.",
        "parameters": {
            "command": {
                "type": "string",
                "required": True,
                "description": "Shell command to execute"
            },
            "cwd": {
                "type": "string",
                "required": False,
                "description": "Working directory for the command"
            }
        },
        "returns": "Command output with exit status",
        "example": '{"action": "run_command", "args": {"command": "npm test"}}',
        "best_practices": [
            "Use for verification (tests, linting, type checking)",
            "Check exit codes for success/failure",
            "Break long pipelines into separate commands for clarity"
        ],
        "security_note": "Commands run with user privileges. Avoid dangerous operations."
    },
    "delete_path": {
        "name": "delete_path",
        "description": "Permanently delete a file or directory. Use with caution.",
        "parameters": {
            "path": {
                "type": "string",
                "required": True,
                "description": "Path to delete"
            }
        },
        "returns": "Success confirmation or error",
        "example": '{"action": "delete_path", "args": {"path": "temp/old_file.txt"}}',
        "best_practices": [
            "Double-check path before deleting",
            "Consider git status before deleting tracked files"
        ]
    },
    "get_dependencies": {
        "name": "get_dependencies",
        "description": "Analyze project dependencies from package files (package.json, requirements.txt, etc.).",
        "parameters": {},
        "returns": "Contents of all found dependency files",
        "example": '{"action": "get_dependencies", "args": {}}',
        "best_practices": [
            "Run early to understand project tech stack",
            "Use to check for version conflicts"
        ]
    },
    "get_symbol_info": {
        "name": "get_symbol_info",
        "description": "Find where a symbol (function, class, variable) is defined.",
        "parameters": {
            "symbol_name": {
                "type": "string",
                "required": True,
                "description": "Name of the symbol to find"
            }
        },
        "returns": "Definition locations found via grep",
        "example": '{"action": "get_symbol_info", "args": {"symbol_name": "UserService"}}',
        "best_practices": [
            "Use to understand code before modifying",
            "Check usages before renaming"
        ]
    },
    "web_search": {
        "name": "web_search",
        "description": "Search the web for information using DuckDuckGo.",
        "parameters": {
            "query": {
                "type": "string",
                "required": True,
                "description": "Search query"
            }
        },
        "returns": "Top search results with titles, links, and snippets",
        "example": '{"action": "web_search", "args": {"query": "python asyncio best practices 2025"}}',
        "best_practices": [
            "Use for documentation, error solutions, best practices",
            "Be specific in queries for better results"
        ]
    },
    "web_browse": {
        "name": "web_browse",
        "description": "Browse a specific URL and extract text content.",
        "parameters": {
            "url": {
                "type": "string",
                "required": True,
                "description": "Full URL to browse"
            }
        },
        "returns": "Page text content (capped at 10k chars)",
        "example": '{"action": "web_browse", "args": {"url": "https://docs.python.org/3/library/asyncio.html"}}',
        "best_practices": [
            "Use to read documentation pages",
            "Follow up on web_search results"
        ]
    },
    "git_status": {
        "name": "git_status",
        "description": "Check current git repository status (changes, branch, etc.).",
        "parameters": {},
        "returns": "Git status output showing staged/unstaged changes",
        "example": '{"action": "git_status", "args": {}}',
        "best_practices": [
            "Check before and after making changes",
            "Verify what will be committed"
        ]
    },
    "git_commit": {
        "name": "git_commit",
        "description": "Stage all changes and create a commit.",
        "parameters": {
            "message": {
                "type": "string",
                "required": True,
                "description": "Commit message (follow conventional commits)"
            }
        },
        "returns": "Commit confirmation or error",
        "example": '{"action": "git_commit", "args": {"message": "feat: add user authentication module"}}',
        "best_practices": [
            "Use conventional commit format (type: description)",
            "Make atomic commits (one logical change)",
            "Verify changes with git_status first"
        ]
    },
    "git_push": {
        "name": "git_push",
        "description": "Push local commits to remote repository.",
        "parameters": {
            "remote": {
                "type": "string",
                "required": False,
                "default": "origin",
                "description": "Remote name"
            },
            "branch": {
                "type": "string",
                "required": False,
                "description": "Branch to push (default: current)"
            }
        },
        "returns": "Push result or error",
        "example": '{"action": "git_push", "args": {"remote": "origin", "branch": "feature/auth"}}',
        "best_practices": [
            "Ensure all tests pass before pushing",
            "Create feature branches for new work"
        ]
    },
    "git_pull": {
        "name": "git_pull",
        "description": "Pull latest changes from remote repository.",
        "parameters": {
            "remote": {
                "type": "string",
                "required": False,
                "default": "origin",
                "description": "Remote name"
            },
            "branch": {
                "type": "string",
                "required": False,
                "description": "Branch to pull"
            }
        },
        "returns": "Pull result showing changes",
        "example": '{"action": "git_pull", "args": {}}',
        "best_practices": [
            "Pull before starting new work",
            "Resolve conflicts carefully"
        ]
    },
    "git_branches": {
        "name": "git_branches",
        "description": "List all local and remote branches.",
        "parameters": {},
        "returns": "Branch list with current branch marked",
        "example": '{"action": "git_branches", "args": {}}',
        "best_practices": [
            "Check existing branches before creating new ones"
        ]
    },
    "git_checkout": {
        "name": "git_checkout",
        "description": "Switch to a branch or create a new one.",
        "parameters": {
            "branch": {
                "type": "string",
                "required": True,
                "description": "Branch name"
            },
            "create": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": "Create new branch if true"
            }
        },
        "returns": "Checkout confirmation",
        "example": '{"action": "git_checkout", "args": {"branch": "feature/new-api", "create": true}}',
        "best_practices": [
            "Use descriptive branch names (feature/, fix/, refactor/)",
            "Commit or stash changes before switching"
        ]
    },
    "git_log": {
        "name": "git_log",
        "description": "View commit history.",
        "parameters": {
            "limit": {
                "type": "integer",
                "required": False,
                "default": 10,
                "description": "Number of commits to show"
            }
        },
        "returns": "Commit history with hashes, authors, dates, messages",
        "example": '{"action": "git_log", "args": {"limit": 5}}',
        "best_practices": [
            "Review recent commits to understand context"
        ]
    },
    "git_clone": {
        "name": "git_clone",
        "description": "Clone a repository from a URL.",
        "parameters": {
            "url": {
                "type": "string",
                "required": True,
                "description": "Repository URL (HTTPS or SSH)"
            },
            "path": {
                "type": "string",
                "required": False,
                "default": ".",
                "description": "Target directory"
            }
        },
        "returns": "Clone result",
        "example": '{"action": "git_clone", "args": {"url": "https://github.com/user/repo.git", "path": "my-project"}}',
        "best_practices": [
            "Use HTTPS for public repos",
            "Ensure target directory is empty or doesn't exist"
        ]
    },
    "git_init": {
        "name": "git_init",
        "description": "Initialize a new git repository in the workspace.",
        "parameters": {},
        "returns": "Init confirmation",
        "example": '{"action": "git_init", "args": {}}',
        "best_practices": [
            "Add .gitignore after initialization",
            "Make an initial commit"
        ]
    },
    "delegate_task": {
        "name": "delegate_task",
        "description": "Delegate a sub-task to a specialized agent. Use for complex, self-contained subtasks.",
        "parameters": {
            "task": {
                "type": "string",
                "required": True,
                "description": "Clear description of the subtask"
            },
            "context": {
                "type": "string",
                "required": False,
                "description": "Relevant context from the main task"
            }
        },
        "returns": "Sub-agent completion result",
        "example": '{"action": "delegate_task", "args": {"task": "Write unit tests for UserService", "context": "UserService is in src/services/user.py"}}',
        "best_practices": [
            "Use for independent, well-defined subtasks",
            "Provide sufficient context for the sub-agent"
        ]
    }
}


# =============================================================================
# SYSTEM PROMPT - Production-grade agent instructions
# =============================================================================

CODING_SYSTEM_PROMPT = """You are Flashy, an elite autonomous coding assistant. You operate within the user's local workspace with full access to their filesystem and development tools.

## Core Principles

1. **Read Before Write**: ALWAYS read existing code before modifying it. Understand context, patterns, and conventions.
2. **Precision Over Speed**: Take time to understand the codebase. Incorrect changes waste more time than careful analysis.
3. **Verify Your Work**: Run tests, linters, or type checkers after making changes to ensure correctness.
4. **Minimal Changes**: Make the smallest change that solves the problem. Avoid unnecessary refactoring.
5. **Production Quality**: All code must be complete, tested, and production-ready. No TODOs or placeholders.

## Your Capabilities

### File System Tools
| Tool | Purpose | Key Args |
|------|---------|----------|
| `read_file` | Read single file | path |
| `read_files` | Read multiple files | paths[], max_bytes |
| `write_file` | Create/overwrite file | path, content |
| `write_files` | Write multiple files | files[{{path, content}}] |
| `patch_file` | Surgical text replacement | path, target, replacement |
| `apply_patch` | Apply unified diff | patch |
| `list_dir` | List directory | path |
| `get_file_tree` | Recursive tree view | path, max_depth |
| `search_files` | Find files by pattern | pattern, path |
| `grep_search` | Search file contents | query, path, extensions |
| `run_command` | Execute shell command | command, cwd |
| `delete_path` | Delete file/directory | path |

### Code Analysis Tools
| Tool | Purpose | Key Args |
|------|---------|----------|
| `get_dependencies` | List project dependencies | (none) |
| `get_symbol_info` | Find symbol definitions | symbol_name |

### Web Tools
| Tool | Purpose | Key Args |
|------|---------|----------|
| `web_search` | Search the internet | query |
| `web_browse` | Browse a URL | url |

### Git Tools
| Tool | Purpose | Key Args |
|------|---------|----------|
| `git_status` | Show repo status | (none) |
| `git_commit` | Commit all changes | message |
| `git_push` | Push to remote | remote, branch |
| `git_pull` | Pull from remote | remote, branch |
| `git_branches` | List branches | (none) |
| `git_checkout` | Switch/create branch | branch, create |
| `git_log` | View commit history | limit |
| `git_clone` | Clone repository | url, path |
| `git_init` | Initialize repo | (none) |

### Delegation
| Tool | Purpose | Key Args |
|------|---------|----------|
| `delegate_task` | Spawn sub-agent | task, context |

## Execution Protocol

### Phase 1: Understand
Before any action, understand the context:
1. Use `get_file_tree` to see project structure
2. Use `read_file` to examine relevant files
3. Use `grep_search` to find related code
4. Use `get_dependencies` to understand tech stack

### Phase 2: Plan
For non-trivial tasks, create a mental plan:
- What files need to be modified?
- What is the correct order of operations?
- What could go wrong?
- How will I verify success?

### Phase 3: Execute
Make changes systematically:
1. Make one logical change at a time
2. Use `patch_file` for targeted edits (exact match required!)
3. Use `write_file` for new files or complete rewrites
4. Handle errors gracefully and retry with corrections

### Phase 4: Verify
Always verify your changes:
1. Run tests: `run_command` with test command (npm test, pytest, etc.)
2. Run linters: Check for style/syntax issues
3. Use `git_status` to review changes
4. Read modified files to confirm correctness

## Tool Call Format

CRITICAL: Use JSON code blocks for tool calls. Stop immediately after the JSON block.

```json
{{
  "action": "tool_name",
  "args": {{
    "key": "value"
  }}
}}
```

## Error Recovery

When a tool fails:
1. **Read the error carefully** - It often contains the solution
2. **Gather more information** - Use read_file or grep_search
3. **Try a different approach** - There's usually another way
4. **Ask clarifying questions** - If stuck, ask the user

Common error patterns:
- "Target block not found" → Read the file first, copy EXACT text including whitespace
- "File not found" → Check path with list_dir or search_files
- "Command failed" → Check output, install missing dependencies
- "Permission denied" → Check file permissions, use sudo if appropriate

## Code Quality Standards

All code you write must:
1. Follow the project's existing style and conventions
2. Include proper error handling
3. Be properly typed (if TypeScript/typed Python)
4. Have clear, concise comments for complex logic
5. Use meaningful variable and function names
6. Be secure (no hardcoded secrets, proper input validation)

## Current Workspace

Path: {workspace_path}
{workspace_context}

---

Execute tasks autonomously. Be thorough, precise, and verify your work.
"""


# =============================================================================
# TOOL RESULT TEMPLATE
# =============================================================================

CODING_TOOL_RESULT_TEMPLATE = """
<tool_result>
<tool>{tool_name}</tool>
<status>{status}</status>
<output>
{output}
</output>
</tool_result>

Analyze the result above:
1. Did the operation succeed or fail?
2. If success: What is the next step?
3. If error: What went wrong and how will you fix it?

Continue with the appropriate action.
"""


# =============================================================================
# ERROR HANDLING GUIDANCE
# =============================================================================

ERROR_RECOVERY_GUIDANCE = {
    "file_not_found": {
        "pattern": r"(?:file not found|no such file|doesn't exist)",
        "recovery": "Use list_dir or search_files to find the correct path. Check for typos in the filename."
    },
    "target_not_found": {
        "pattern": r"target (?:block |text )?not found",
        "recovery": "Read the file first with read_file to get the EXACT text including whitespace and indentation."
    },
    "permission_denied": {
        "pattern": r"permission denied",
        "recovery": "Check file permissions. You may need to use sudo for system files."
    },
    "command_failed": {
        "pattern": r"(?:exit code|command failed|non-zero)",
        "recovery": "Review the error output. Common issues: missing dependencies, syntax errors, path issues."
    },
    "import_error": {
        "pattern": r"(?:import error|module not found|no module named)",
        "recovery": "Check if the module is installed. Use pip install or npm install as appropriate."
    },
    "syntax_error": {
        "pattern": r"(?:syntax error|unexpected token|parse error)",
        "recovery": "Review the code for syntax issues. Check matching brackets, quotes, and indentation."
    },
    "timeout": {
        "pattern": r"(?:timeout|timed out)",
        "recovery": "The command took too long. Consider breaking it into smaller operations or increasing timeout."
    },
    "git_conflict": {
        "pattern": r"(?:merge conflict|conflict|cannot pull)",
        "recovery": "There are merge conflicts. Read the conflicted files and resolve manually."
    }
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_system_prompt(workspace_path: str, workspace_context: str = "") -> str:
    """Generate the system prompt with workspace context."""
    context_section = ""
    if workspace_context:
        context_section = f"\n{workspace_context}"

    return CODING_SYSTEM_PROMPT.format(
        workspace_path=workspace_path or "[Not Set]",
        workspace_context=context_section
    )


def get_tool_result_template(tool_name: str, output: str, success: bool = True) -> str:
    """Format a tool result for the agent."""
    status = "SUCCESS" if success else "ERROR"
    return CODING_TOOL_RESULT_TEMPLATE.format(
        tool_name=tool_name,
        status=status,
        output=output
    )


def get_tool_schema(tool_name: str) -> Dict[str, Any]:
    """Get the schema for a specific tool."""
    return TOOL_SCHEMAS.get(tool_name)


def get_all_tool_schemas() -> Dict[str, Dict[str, Any]]:
    """Get all tool schemas."""
    return TOOL_SCHEMAS


def format_tool_help(tool_name: str) -> str:
    """Format detailed help for a tool."""
    schema = TOOL_SCHEMAS.get(tool_name)
    if not schema:
        return f"Unknown tool: {tool_name}"

    lines = [
        f"## {schema['name']}",
        f"{schema['description']}",
        "",
        "### Parameters:"
    ]

    params = schema.get("parameters", {})
    if params:
        for name, info in params.items():
            required = "required" if info.get("required") else "optional"
            default = f", default: {info.get('default')}" if "default" in info else ""
            lines.append(f"- `{name}` ({info['type']}, {required}{default}): {info['description']}")
    else:
        lines.append("- None")

    lines.extend([
        "",
        f"### Returns: {schema.get('returns', 'Result of operation')}",
        "",
        f"### Example:",
        f"```json",
        f"{schema.get('example', '{}')}",
        f"```"
    ])

    if schema.get("best_practices"):
        lines.extend([
            "",
            "### Best Practices:"
        ])
        for practice in schema["best_practices"]:
            lines.append(f"- {practice}")

    return "\n".join(lines)


def get_error_recovery_hint(error_message: str) -> str:
    """Get recovery hints for common errors."""
    import re
    error_lower = error_message.lower()

    for error_type, info in ERROR_RECOVERY_GUIDANCE.items():
        if re.search(info["pattern"], error_lower, re.IGNORECASE):
            return f"Recovery hint: {info['recovery']}"

    return "Analyze the error message and try a different approach."


def build_workspace_context(file_tree: str = "", recent_files: List[str] = None) -> str:
    """Build workspace context string for the system prompt."""
    parts = []

    if file_tree:
        parts.append(f"### Project Structure\n```\n{file_tree}\n```")

    if recent_files:
        parts.append(f"### Recently Modified Files\n" + "\n".join(f"- {f}" for f in recent_files[:10]))

    return "\n\n".join(parts) if parts else ""
