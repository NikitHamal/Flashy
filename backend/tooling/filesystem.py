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

class FileSystemMixin:
    def read_file(self, path: str) -> str:
        """Read the contents of a file."""
        try:
            full_path = self._resolve_path(path)
            if not self._is_within_workspace(full_path):
                return f"Error: Path is outside the workspace: {path}"
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(200000)
            return f"Content of {path}:\n```\n{content}\n```"
        except FileNotFoundError:
            return f"Error: File not found: {path}"
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def read_files(self, paths: List[str], max_bytes: int = 200000) -> str:
        """Read multiple files with a per-file byte limit."""
        outputs = []
        for path in paths:
            try:
                full_path = self._resolve_path(path)
                if not self._is_within_workspace(full_path):
                    outputs.append(f"Error: Path is outside the workspace: {path}")
                    continue
                with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read(max_bytes)
                outputs.append(f"Content of {path}:\n```\n{content}\n```")
            except FileNotFoundError:
                outputs.append(f"Error: File not found: {path}")
            except Exception as e:
                outputs.append(f"Error reading {path}: {str(e)}")
        return "\n\n".join(outputs)

    def write_file(self, path: str, content: str) -> str:
        """Write content to a file, creating directories if needed."""
        try:
            full_path = self._resolve_path(path)
            if not self._is_within_workspace(full_path):
                return f"Error: Path is outside the workspace: {path}"
            os.makedirs(os.path.dirname(full_path), exist_ok=True) if os.path.dirname(full_path) else None
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote {len(content)} characters to {path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def write_files(self, files: List[dict]) -> str:
        """Write multiple files. Each entry: {path, content}."""
        if not isinstance(files, list):
            return "Error: arguments for write_files must be a list of dictionaries."
            
        results = []
        for entry in files:
            if not isinstance(entry, dict):
                results.append(f"Error: Invalid entry in write_files (expected dict): {entry}")
                continue
                
            path = entry.get("path")
            content = entry.get("content", "")
            if not path:
                results.append("Error: Missing path in write_files entry.")
                continue
            results.append(self.write_file(path, content))
        return "\n".join(results)

    def apply_patch(self, patch: str) -> str:
        """Apply a unified diff patch to the workspace."""
        import tempfile
        if not patch or not patch.strip():
            return "Error: Patch content is empty."

        temp_file = None
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".patch")
            temp_file.write(patch.encode("utf-8"))
            temp_file.close()

            commands = [
                ["patch", "-p1", "-i", temp_file.name],
                ["patch", "-p0", "-i", temp_file.name],
                ["git", "apply", temp_file.name]
            ]
            for cmd in commands:
                try:
                    result = subprocess.run(
                        cmd,
                        cwd=self.workspace_path,
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        return f"Patch applied successfully.\n{result.stdout.strip()}"
                    error = result.stderr.strip() or result.stdout.strip()
                except FileNotFoundError:
                    continue

            return f"Error applying patch: {error or 'Unknown error'}"
        except Exception as e:
            return f"Error applying patch: {str(e)}"
        finally:
            if temp_file:
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass

    def patch_file(self, path: str, target: str, replacement: str) -> str:
        """Replace a specific block of text in a file with new content."""
        try:
            full_path = self._resolve_path(path)
            if not self._is_within_workspace(full_path):
                return f"Error: Path is outside the workspace: {path}"
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
                        if os.path.islink(item_path):
                            result.append("  " * current_depth + "├── " + item + " [symlink]")
                            continue
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
        """Search for a string inside files (case-insensitive).

        Uses ripgrep (rg) when available for O(1) indexed search performance.
        Falls back to optimized Python scanning for systems without ripgrep.
        """
        try:
            path = path or "."
            full_path = self._resolve_path(path)
            exclude_dirs = {'.git', 'node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build'}

            # Try ripgrep first — it's orders of magnitude faster on large codebases
            rg_path = shutil.which("rg")
            if rg_path:
                rg_cmd = [
                    rg_path,
                    "--ignore-case",
                    "--no-heading",
                    "--line-number",
                    "--max-count", "50",
                    "--glob", "!.git/**",
                    "--glob", "!node_modules/**",
                    "--glob", "!__pycache__/**",
                    "--glob", "!venv/**",
                    "--glob", "!.venv/**",
                ]
                # Filter by extensions via glob patterns
                if extensions:
                    for ext in extensions:
                        rg_cmd.extend(["--glob", f"*{ext}"])

                rg_cmd.extend([query, full_path])

                try:
                    result = subprocess.run(
                        rg_cmd,
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='replace',
                        timeout=30
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        lines = result.stdout.strip().split('\n')[:50]
                        # Convert absolute paths back to relative
                        rel_lines = []
                        for line in lines:
                            # rg output format: path:line_num:content
                            parts = line.split(':', 2)
                            if len(parts) >= 3:
                                rel_path = os.path.relpath(parts[0], self.workspace_path)
                                rel_lines.append(f"{rel_path}:{parts[1]}: {parts[2]}")
                            else:
                                rel_lines.append(line)
                        return f"Search results for '{query}':\n" + "\n".join(rel_lines)
                    elif result.returncode == 1:
                        return f"No matches found for '{query}'"
                    # If rg fails for some reason, fall through to Python implementation
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass

            # Python fallback — optimized with early exit and directory pruning
            results = []
            query_lower = query.lower()
            extensions_set = set(extensions) if extensions else None

            for root, dirs, files in os.walk(full_path):
                # Prune excluded directories in-place to prevent recursion
                dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]

                for file in files:
                    if extensions_set and not any(file.endswith(ext) for ext in extensions_set):
                        continue

                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for line_num, line in enumerate(f, 1):
                                if query_lower in line.lower():
                                    rel_path = os.path.relpath(file_path, self.workspace_path)
                                    results.append(f"{rel_path}:{line_num}: {line.rstrip()}")
                                    if len(results) >= 50:
                                        return "Search results (capped at 50):\n" + "\n".join(results)
                    except (PermissionError, OSError):
                        pass

            if results:
                return f"Search results for '{query}':\n" + "\n".join(results)
            return f"No matches found for '{query}'"
        except Exception as e:
            return f"Error during grep: {str(e)}"

    def delete_path(self, path: str) -> str:
        """Delete a file or directory."""
        try:
            full_path = self._resolve_path(path)
            if not self._is_within_workspace(full_path):
                return f"Error: Path is outside the workspace: {path}"
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
                            if os.path.islink(child_full_path):
                                continue
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
                        content = f.read(200000)
                    results.append(f"--- {file} ---\n{content}")
                except: pass
        
        if results:
            return "\n\n".join(results)
        return "No dependency files found in root."

    def get_symbol_info(self, symbol_name: str) -> str:
        """Find where a specific symbol (class/function/variable) is defined using advanced grep patterns."""
        if not symbol_name or not symbol_name.strip():
            return "Error: Symbol name is empty."
            
        results = []
        
        # Try ripgrep first for exact symbol definitions across common languages
        rg_path = shutil.which("rg")
        if rg_path:
            # Patterns for Python, JS/TS, Go, Rust, Java, C/C++
            patterns = [
                f"^(?:async\\s+)?def\\s+{symbol_name}\\b",               # Python functions
                f"^class\\s+{symbol_name}\\b",                           # Python/JS/TS/Java/C++ classes
                f"^(?:export\\s+)?(?:const|let|var)\\s+{symbol_name}\\s*=", # JS/TS variables/arrows
                f"^(?:export\\s+)?(?:async\\s+)?function\\s+{symbol_name}\\b", # JS/TS functions
                f"^(?:export\\s+)?(?:interface|type)\\s+{symbol_name}\\b",     # TS types
                f"^func\\s+{symbol_name}\\b",                            # Go functions
                f"^type\\s+{symbol_name}\\s+struct\\b",                  # Go structs
                f"^fn\\s+{symbol_name}\\b",                              # Rust functions
                f"^(?:pub\\s+)?(?:struct|enum|trait)\\s+{symbol_name}\\b",     # Rust types
                f"\\b{symbol_name}\\s*:=.*",                             # Go assignment / general assignment
            ]
            
            for pattern in patterns:
                rg_cmd = [
                    rg_path,
                    "--line-number",
                    "--no-heading",
                    "--max-count", "10",
                    "--glob", "!.git/**",
                    "--glob", "!node_modules/**",
                    "--glob", "!venv/**",
                    "--glob", "!.venv/**",
                    "--glob", "!__pycache__/**",
                    pattern,
                    self.workspace_path
                ]
                try:
                    result = subprocess.run(rg_cmd, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0 and result.stdout.strip():
                        lines = result.stdout.strip().split('\n')
                        for line in lines:
                            parts = line.split(':', 2)
                            if len(parts) >= 3:
                                rel_path = os.path.relpath(parts[0], self.workspace_path)
                                results.append(f"{rel_path}:{parts[1]}: {parts[2].strip()}")
                except Exception:
                    pass

        # Python fallback (if ripgrep fails or isn't installed)
        if not results:
            basic_patterns = [
                f"def {symbol_name}",
                f"class {symbol_name}",
                f"{symbol_name} =",
                f"const {symbol_name}",
                f"function {symbol_name}"
            ]
            for pattern in basic_patterns:
                res = self.grep_search(pattern)
                if "Search results" in res:
                    results.append(res.replace(f"Search results for '{pattern}':\n", ""))

        if results:
            # Deduplicate while preserving order
            seen = set()
            unique_results = []
            for r in results:
                if r not in seen:
                    seen.add(r)
                    unique_results.append(r)
            return f"Found potential definitions for '{symbol_name}':\n" + "\n".join(unique_results[:30])
            
        return f"Could not find any clear definitions for '{symbol_name}'. Try using grep_search for broader results."
