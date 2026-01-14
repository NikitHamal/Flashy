import os
import subprocess
import glob
from typing import Optional, List
from .git_manager import GitManager

class Tools:
    """Collection of tools the agent can use to interact with the local system."""
    
    def __init__(self, workspace_path: str = None):
        self.workspace_path = workspace_path or os.getcwd()
        self.git = GitManager(self.workspace_path)
    
    def set_workspace(self, path: str):
        """Set the workspace root path."""
        if os.path.isdir(path):
            self.workspace_path = os.path.abspath(path)
            self.git.workspace_path = self.workspace_path
            return f"Workspace set to: {self.workspace_path}"
        else:
            return f"Error: '{path}' is not a valid directory."
    
    def _resolve_path(self, relative_path: str) -> str:
        """Resolve a path relative to the workspace."""
        if os.path.isabs(relative_path):
            return relative_path
        return os.path.join(self.workspace_path, relative_path)
    
    def read_file(self, path: str) -> str:
        """Read the contents of a file."""
        try:
            full_path = self._resolve_path(path)
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"Content of {path}:\n```\n{content}\n```"
        except FileNotFoundError:
            return f"Error: File not found: {path}"
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def write_file(self, path: str, content: str) -> str:
        """Write content to a file, creating directories if needed."""
        try:
            full_path = self._resolve_path(path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True) if os.path.dirname(full_path) else None
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote {len(content)} characters to {path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def patch_file(self, path: str, target: str, replacement: str) -> str:
        """Replace a specific block of text in a file with new content."""
        try:
            full_path = self._resolve_path(path)
            if not os.path.exists(full_path):
                return f"Error: File '{path}' not found."
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if target not in content:
                return f"Error: Target block not found in {path}. Make sure it exactly matches (including whitespace)."
            
            new_content = content.replace(target, replacement, 1)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            return f"Successfully patched {path}. Replaced 1 occurrence."
        except Exception as e:
            return f"Error patching file: {str(e)}"
    
    def list_dir(self, path: str = ".") -> str:
        """List contents of a directory."""
        try:
            path = path or "."
            full_path = self._resolve_path(path)
            if not os.path.isdir(full_path):
                return f"Error: '{path}' is not a directory."
            items = os.listdir(full_path)
            dirs = sorted([f"📁 {item}/" for item in items if os.path.isdir(os.path.join(full_path, item))])
            files = sorted([f"📄 {item}" for item in items if os.path.isfile(os.path.join(full_path, item))])
            result = "\n".join(dirs + files)
            return f"Contents of {path}:\n{result}" if result else f"{path} is empty."
        except FileNotFoundError:
            return f"Error: Directory not found: {path}"
        except Exception as e:
            return f"Error listing directory: {str(e)}"
    
    def get_file_tree(self, path: str = ".", max_depth: int = 2) -> str:
        """Get a recursive tree view of the directory structure."""
        try:
            path = path or "."
            full_path = self._resolve_path(path)
            result = [f"Root: {path}"]
            
            def _build_tree(current_path, current_depth):
                if current_depth > max_depth:
                    return
                try:
                    items = os.listdir(current_path)
                    for i, item in enumerate(sorted(items)):
                        item_path = os.path.join(current_path, item)
                        is_dir = os.path.isdir(item_path)
                        prefix = "  " * current_depth + "└── "
                        result.append(f"{prefix}{item}{'/' if is_dir else ''}")
                        if is_dir:
                            _build_tree(item_path, current_depth + 1)
                except PermissionError:
                    result.append("  " * current_depth + "└── [Permission Denied]")

            _build_tree(full_path, 1)
            return "\n".join(result)
        except Exception as e:
            return f"Error generating tree: {str(e)}"

    def search_files(self, pattern: str, path: str = ".") -> str:
        """Search for files matching a glob pattern."""
        try:
            path = path or "."
            full_path = self._resolve_path(path)
            search_pattern = os.path.join(full_path, "**", pattern)
            matches = glob.glob(search_pattern, recursive=True)
            relative_matches = [os.path.relpath(m, self.workspace_path) for m in matches[:50]]
            if relative_matches:
                return f"Found {len(matches)} files matching '{pattern}':\n" + "\n".join(relative_matches)
            return f"No files found matching '{pattern}'"
        except Exception as e:
            return f"Error searching files: {str(e)}"
    
    def grep_search(self, query: str, path: str = ".", extensions: Optional[List[str]] = None) -> str:
        """Search for a string inside files (case-insensitive)."""
        try:
            path = path or "."
            full_path = self._resolve_path(path)
            results = []
            
            for root, dirs, files in os.walk(full_path):
                if any(exclude in root for exclude in ['.git', 'node_modules', '__pycache__', 'venv']):
                    continue
                    
                for file in files:
                    if extensions and not any(file.endswith(ext) for ext in extensions):
                        continue
                        
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for line_num, line in enumerate(f, 1):
                                if query.lower() in line.lower():
                                    rel_path = os.path.relpath(file_path, self.workspace_path)
                                    results.append(f"{rel_path}:{line_num}: {line.strip()}")
                                    if len(results) >= 50:
                                        return "Search results (capped at 50):\n" + "\n".join(results)
                    except: pass
            
            if results:
                return f"Search results for '{query}':\n" + "\n".join(results)
            return f"No matches found for '{query}'"
        except Exception as e:
            return f"Error during grep: {str(e)}"

    def run_command(self, command: str, cwd: Optional[str] = None) -> str:
        """Execute a shell command in the workspace."""
        try:
            work_dir = self._resolve_path(cwd) if cwd else self.workspace_path
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            output = result.stdout + result.stderr
            status = "✓ Success" if result.returncode == 0 else f"✗ Exit code: {result.returncode}"
            return f"Command: `{command}`\nStatus: {status}\nOutput:\n```\n{output.strip() or '(no output)'}\n```"
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after 60 seconds."
        except Exception as e:
            return f"Error running command: {str(e)}"

    def delete_path(self, path: str) -> str:
        """Delete a file or directory."""
        try:
            full_path = self._resolve_path(path)
            if not os.path.exists(full_path):
                return f"Error: Path '{path}' does not exist."
            
            if os.path.isfile(full_path):
                os.remove(full_path)
                return f"Successfully deleted file: {path}"
            else:
                import shutil
                shutil.rmtree(full_path)
                return f"Successfully deleted directory: {path}"
        except Exception as e:
            return f"Error deleting path: {str(e)}"

    def get_explorer_data(self, path: str = ".") -> dict:
        """Get a nested dictionary structure for the UI explorer."""
        try:
            path = path or "."
            full_path = self._resolve_path(path)
            
            def _scan(current_full_path):
                name = os.path.basename(current_full_path) or path
                item = {
                    "name": name,
                    "path": os.path.relpath(current_full_path, self.workspace_path),
                    "type": "directory" if os.path.isdir(current_full_path) else "file"
                }
                
                if item["type"] == "directory":
                    try:
                        item["children"] = []
                        # Sort: directories first, then alphabetical
                        entries = sorted(os.listdir(current_full_path))
                        for entry in entries:
                            if entry in ['.git', 'node_modules', '__pycache__']: continue
                            child_full_path = os.path.join(current_full_path, entry)
                            item["children"].append(_scan(child_full_path))
                        
                        # Sort children: directories first
                        item["children"].sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
                    except PermissionError:
                        item["error"] = "Permission Denied"
                
                return item

            return _scan(full_path)
        except Exception as e:
            return {"error": str(e)}

    def get_dependencies(self) -> str:
        """Analyze project dependencies (package.json, requirements.txt, etc.)."""
        results = []
        files_to_check = ["package.json", "requirements.txt", "pyproject.toml", "go.mod", "Cargo.toml"]
        
        for file in files_to_check:
            full_path = self._resolve_path(file)
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    results.append(f"--- {file} ---\n{content}")
                except: pass
        
        if results:
            return "\n\n".join(results)
        return "No dependency files found in root."

    def web_search(self, query: str) -> str:
        """Search the web using DuckDuckGo."""
        try:
            from requests_html import HTMLSession
            session = HTMLSession()
            # DuckDuckGo HTML version (simpler to parse)
            url = f"https://html.duckduckgo.com/html/?q={query}"
            resp = session.get(url)
            results = []
            for item in resp.html.find('.result'):
                title_node = item.find('.result__a', first=True)
                snippet_node = item.find('.result__snippet', first=True)
                if title_node and snippet_node:
                    results.append(f"Title: {title_node.text}\nLink: {title_node.attrs['href']}\nSnippet: {snippet_node.text}\n")
            
            if results:
                return "\n".join(results[:8])
            return "No web results found."
        except Exception as e:
            return f"Error during web search: {str(e)}"

    def web_browse(self, url: str) -> str:
        """Browse a website and return its text content."""
        try:
            from requests_html import HTMLSession
            session = HTMLSession()
            resp = session.get(url)
            # Basic text extraction
            text = resp.html.text
            # Clean up excessive whitespace
            import re
            text = re.sub(r'\n\s*\n', '\n\n', text)
            return f"Content of {url}:\n\n{text[:10000]}..." # Cap at 10k chars
        except Exception as e:
            return f"Error browsing {url}: {str(e)}"

    def get_symbol_info(self, symbol_name: str) -> str:
        """Find where a specific symbol (class/function/variable) is defined using grep."""
        # Search for definitions like "def symbol", "class symbol", "symbol =", "export const symbol"
        patterns = [
            f"def {symbol_name}",
            f"class {symbol_name}",
            f"{symbol_name} =",
            f"const {symbol_name}",
            f"function {symbol_name}"
        ]
        results = []
        for pattern in patterns:
            res = self.grep_search(pattern)
            if "Search results" in res:
                results.append(res)
        
        if results:
            return "\n\n".join(results)
        return f"Could not find any clear definitions for '{symbol_name}'."

    # --- Git Tools ---

    def git_status(self) -> str:
        """Check the status of the current git repository."""
        if not self.git.is_repo():
            return "Current workspace is not a git repository."
        return self.git.get_status()

    def git_commit(self, message: str) -> str:
        """Stage all changes and commit with a message."""
        if not self.git.is_repo():
            return "Error: Not a git repository."
        return self.git.commit(message)

    def git_push(self, remote: str = "origin", branch: str = None) -> str:
        """Push changes to a remote repository."""
        if not self.git.is_repo():
            return "Error: Not a git repository."
        # Note: We'll try to use the PAT from config if not already set in remote
        from .config import load_config
        config = load_config()
        pat = config.get("GITHUB_PAT")
        return self.git.push(remote, branch, pat=pat)

    def git_pull(self, remote: str = "origin", branch: str = None) -> str:
        """Pull changes from a remote repository."""
        if not self.git.is_repo():
            return "Error: Not a git repository."
        return self.git.pull(remote, branch)

    def git_branches(self) -> str:
        """List all branches in the current repository."""
        if not self.git.is_repo():
            return "Error: Not a git repository."
        branches = self.git.get_branches()
        return "\n".join([f"{'* ' if b['current'] else '  '}{b['name']}" for b in branches])

    def git_checkout(self, branch: str, create: bool = False) -> str:
        """Switch to a branch or create a new one."""
        if not self.git.is_repo():
            return "Error: Not a git repository."
        return self.git.checkout(branch, create)

    def git_log(self, limit: int = 10) -> str:
        """Show git commit history."""
        if not self.git.is_repo():
            return "Error: Not a git repository."
        return self.git.get_log(limit)

    def git_clone(self, url: str, path: str = ".") -> str:
        """Clone a git repository from a URL."""
        from .config import load_config
        config = load_config()
        pat = config.get("GITHUB_PAT")
        # Ensure path is absolute or relative to workspace
        full_target_path = self._resolve_path(path)
        return self.git.clone_repo(url, full_target_path, pat=pat)

    def git_init(self) -> str:
        """Initialize a new git repository in the current workspace."""
        return self.git.init_repo()

    def get_available_tools(self) -> list:
        """Return list of available tools with descriptions."""
        return [
            {"name": "read_file", "description": "Read file contents. Args: path (str)"},
            {"name": "write_file", "description": "Write/create file. Args: path (str), content (str)"},
            {"name": "patch_file", "description": "Replace a specific block of text. Args: path (str), target (str), replacement (str)"},
            {"name": "list_dir", "description": "List directory contents. Args: path (str, optional)"},
            {"name": "get_file_tree", "description": "Get recursive tree view text. Args: path (str, optional), max_depth (int, default 2)"},
            {"name": "get_explorer_data", "description": "Get recursive directory structure as JSON for UI. Args: path (str, optional)"},
            {"name": "search_files", "description": "Search for files by name pattern. Args: pattern (str), path (str, optional)"},
            {"name": "grep_search", "description": "Search for text inside files. Args: query (str), path (str, optional), extensions (list, optional)"},
            {"name": "run_command", "description": "Execute shell command. Args: command (str), cwd (str, optional)"},
            {"name": "delete_path", "description": "Delete file/directory. Args: path (str)"},
            {"name": "get_dependencies", "description": "Analyze project dependencies. No args."},
            {"name": "web_search", "description": "Search the web. Args: query (str)"},
            {"name": "web_browse", "description": "Browse a website. Args: url (str)"},
            {"name": "get_symbol_info", "description": "Find definition of a symbol. Args: symbol_name (str)"},
            {"name": "git_status", "description": "Get git status. No args."},
            {"name": "git_commit", "description": "Commit all changes. Args: message (str)"},
            {"name": "git_push", "description": "Push changes. Args: remote (str, optional), branch (str, optional)"},
            {"name": "git_pull", "description": "Pull changes. Args: remote (str, optional), branch (str, optional)"},
            {"name": "git_branches", "description": "List all branches. No args."},
            {"name": "git_checkout", "description": "Switch/create branch. Args: branch (str), create (bool, optional)"},
            {"name": "git_log", "description": "Show commit history. Args: limit (int, optional)"},
            {"name": "git_clone", "description": "Clone a repo. Args: url (str), path (str, optional)"},
            {"name": "git_init", "description": "Initialize a new git repo. No args."}
        ]
    
    def execute(self, tool_name: str, **kwargs) -> str:
        """Execute a tool by name with given arguments."""
        tool_map = {
            "read_file": self.read_file,
            "write_file": self.write_file,
            "patch_file": self.patch_file,
            "list_dir": self.list_dir,
            "get_file_tree": self.get_file_tree,
            "get_explorer_data": self.get_explorer_data,
            "search_files": self.search_files,
            "grep_search": self.grep_search,
            "run_command": self.run_command,
            "delete_path": self.delete_path
        }
        
        if tool_name not in tool_map:
            return f"Error: Unknown tool '{tool_name}'. Available: {list(tool_map.keys())}"
        
        try:
            return tool_map[tool_name](**kwargs)
        except TypeError as e:
            return f"Error: Invalid arguments for '{tool_name}': {str(e)}"
