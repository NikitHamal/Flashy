import os
import subprocess
import glob
import tempfile
import shutil
import json
import asyncio
from typing import Optional, List, Dict, Any
from .git_manager import GitManager
from .websocket_manager import ws_manager
from .image_service import get_image_service, ImageService

class Tools:
    """Collection of tools the agent can use to interact with the local system."""
    
    def __init__(self, workspace_path: str = None, session_id: str = None):
        self.workspace_path = workspace_path or os.getcwd()
        self.session_id = session_id
        self.git = GitManager(self.workspace_path)
        self.image_service = get_image_service(self.workspace_path)
        
        # Track pending image operations
        self._pending_image_save: Dict[str, Any] = {}
    
    def set_workspace(self, path: str):
        """Set the workspace root path."""
        if os.path.isdir(path):
            self.workspace_path = os.path.abspath(path)
            self.git.workspace_path = self.workspace_path
            self.image_service.set_workspace(self.workspace_path)
            return f"Workspace set to: {self.workspace_path}"
        else:
            return f"Error: '{path}' is not a valid directory."
    
    def _resolve_path(self, relative_path: str) -> str:
        """Resolve a path relative to the workspace."""
        if os.path.isabs(relative_path):
            return relative_path
        return os.path.join(self.workspace_path, relative_path)

    def _is_within_workspace(self, full_path: str) -> bool:
        """Check if a path is within the workspace root."""
        try:
            workspace = os.path.realpath(self.workspace_path)
            target = os.path.realpath(full_path)
            return os.path.commonpath([workspace, target]) == workspace
        except Exception:
            return False
    
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

    async def run_command(self, command: str, cwd: Optional[str] = None, timeout: int = 300) -> str:
        """Execute a shell command in the workspace with configurable timeout.

        Args:
            command: Shell command to execute
            cwd: Working directory (resolved relative to workspace)
            timeout: Max execution time in seconds (default 300 = 5 min)
        """
        try:
            if not command or not command.strip():
                return "Error: Command is empty."
            work_dir = self._resolve_path(cwd) if cwd else self.workspace_path

            # If we have a session_id, stream the output via WebSocket
            if self.session_id:
                output, exit_code = await ws_manager.run_command_streamed(
                    self.session_id,
                    command,
                    cwd=work_dir
                )

                status = "✓ Success" if exit_code == 0 else f"✗ Exit code: {exit_code}"
                return f"Command: `{command}`\nStatus: {status}\nOutput:\n```\n{output.strip() or '(no output)'}\n```"

            # Non-session: use asyncio subprocess for proper async execution
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
                output = stdout_bytes.decode('utf-8', errors='replace')
                stderr_output = stderr_bytes.decode('utf-8', errors='replace')
                combined = output + stderr_output
                status = "✓ Success" if process.returncode == 0 else f"✗ Exit code: {process.returncode}"
                return f"Command: `{command}`\nStatus: {status}\nOutput:\n```\n{combined.strip() or '(no output)'}\n```"
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return f"Error: Command timed out after {timeout} seconds. Process was killed."
        except Exception as e:
            return f"Error running command: {str(e)}"

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

    def web_search(self, query: str) -> str:
        """Search the web using DuckDuckGo."""
        try:
            from requests_html import HTMLSession
            session = HTMLSession()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            # DuckDuckGo HTML version (simpler to parse)
            url = f"https://html.duckduckgo.com/html/?q={query}"
            resp = session.get(url, timeout=20)
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
        finally:
            try:
                if 'session' in locals():
                    session.close()
            except Exception:
                pass

    def web_browse(self, url: str) -> str:
        """Browse a website and return its text content."""
        try:
            from requests_html import HTMLSession
            session = HTMLSession()
            resp = session.get(url, timeout=20)
            # Basic text extraction
            text = resp.html.text
            # Clean up excessive whitespace
            import re
            text = re.sub(r'\n\s*\n', '\n\n', text)
            return f"Content of {url}:\n\n{text[:10000]}..." # Cap at 10k chars
        except Exception as e:
            return f"Error browsing {url}: {str(e)}"
        finally:
            try:
                if 'session' in locals():
                    session.close()
            except Exception:
                pass

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

    def self_check(self) -> Dict[str, Any]:
        """Run a global self-check across tools and environment."""
        result: Dict[str, Any] = {
            "workspace": {
                "path": self.workspace_path,
                "exists": os.path.isdir(self.workspace_path),
                "readable": False,
                "writable": False,
            },
            "git": {},
            "commands": {},
            "web": {"requests_html": False},
            "image": {"available": self.image_service is not None},
            "warnings": [],
            "errors": [],
        }

        # Workspace readability/writability
        if result["workspace"]["exists"]:
            try:
                test_file = os.path.join(self.workspace_path, ".flashy_write_test.tmp")
                with open(test_file, "w", encoding="utf-8") as f:
                    f.write("ok")
                result["workspace"]["writable"] = True
                with open(test_file, "r", encoding="utf-8") as f:
                    _ = f.read()
                result["workspace"]["readable"] = True
                os.remove(test_file)
            except Exception as e:
                result["errors"].append(f"Workspace read/write check failed: {e}")
        else:
            result["errors"].append("Workspace path does not exist or is not a directory.")

        # Command availability
        for cmd in ["git", "python"]:
            result["commands"][cmd] = bool(shutil.which(cmd))
            if not result["commands"][cmd]:
                result["warnings"].append(f"Command not found in PATH: {cmd}")

        # Git health
        try:
            from .config import load_config
            pat = load_config().get("GITHUB_PAT")
            result["git"] = self.git.get_health(pat=pat)
        except Exception as e:
            result["warnings"].append(f"Git health check failed: {e}")
            result["git"] = {"is_repo": False}

        # Web search dependency
        try:
            import requests_html  # noqa: F401
            result["web"]["requests_html"] = True
        except Exception:
            result["warnings"].append("requests_html not available; web_search may fail.")

        return result

    # --- Image Tools ---

    def generate_image(self, prompt: str, save_to_project: bool = False, filename: str = None) -> str:
        """
        Request image generation from AI.
        
        This tool signals to the agent loop that an image should be generated.
        The actual generation happens via Gemini's internal image generation.
        
        Args:
            prompt: Description of the image to generate
            save_to_project: Whether to save the image to assets/images
            filename: Optional custom filename
        """
        # Store pending save request if needed
        if save_to_project:
            self._pending_image_save = {
                "save": True,
                "filename": filename,
                "prompt": prompt
            }
        
        # Return a formatted prompt that will trigger Gemini's image generation
        return f"""IMAGE_GENERATION_REQUEST:
Prompt: {prompt}
Save to project: {save_to_project}
Filename: {filename or 'auto'}

Please generate an image matching this description. Use your image generation capabilities to CREATE a new, original image. After generation, the image will appear in the response."""

    async def save_image(self, url: str, filename: str = None, subdir: str = None) -> str:
        """
        Save an image from URL to the project's assets folder.
        
        Args:
            url: Image URL to download and save
            filename: Optional custom filename
            subdir: Optional subdirectory within assets/images
        """
        success, result = await self.image_service.save_image_from_url(
            url, 
            filename, 
            subdir
        )
        
        if success:
            return f"Image saved successfully to: {result}"
        else:
            return f"Error saving image: {result}"

    async def save_generated_images(self, subdir: str = None) -> str:
        """
        Save all recently generated images to the project.
        
        Args:
            subdir: Optional subdirectory within assets/images
        """
        if not self.image_service.generated_images:
            return "No generated images available to save."
        
        saved = []
        errors = []
        
        for i, img in enumerate(self.image_service.generated_images):
            if img.saved:
                saved.append(f"Already saved: {img.local_path}")
                continue
                
            success, result = await self.image_service.save_image_from_url(
                img.url,
                filename=None,
                subdir=subdir
            )
            
            if success:
                img.local_path = result
                img.saved = True
                saved.append(f"Saved: {result}")
            else:
                errors.append(f"Failed: {result}")
        
        output = []
        if saved:
            output.append("Saved images:\\n" + "\\n".join(saved))
        if errors:
            output.append("Errors:\\n" + "\\n".join(errors))
        
        return "\\n\\n".join(output) if output else "No images to save."

    def get_pending_image_save(self) -> Dict[str, Any]:
        """Get and clear pending image save request."""
        pending = self._pending_image_save.copy()
        self._pending_image_save = {}
        return pending

    # --- Qwen Code Tool ---

    async def qwen_code(self, prompt: str, working_dir: str = None, model: str = "qwen3.6-plus") -> str:
        """Invoke qwen-code autonomous agent with FREE AI models.
        
        Uses the qwen-code-free-providers bridge for unlimited free access to:
        - qwen3.6-plus, qwen3.5-plus, qwen3.5-flash, qwen3-coder-plus
        - Llama 3 8B/70B, Mistral 7B
        
        Args:
            prompt: Task or question for qwen-code
            working_dir: Working directory (relative to workspace)
            model: Model to use (default: qwen3.6-plus)
        """
        try:
            from .qwen_code_tool import qwen_code_tool, qwen_code_setup
            
            # Setup if needed
            setup_result = await qwen_code_setup()
            if "Error" in setup_result:
                return f"Qwen Code setup: {setup_result}"
            
            # Resolve working directory
            if working_dir:
                work_dir = self._resolve_path(working_dir)
            else:
                work_dir = self.workspace_path
            
            # Run qwen-code
            return await qwen_code_tool(
                prompt=prompt,
                working_dir=work_dir,
                model=model,
                stream_output=True
            )
        except Exception as e:
            return f"Error using qwen-code tool: {str(e)}"

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
        return self.git.commit(message, stage_all=True)

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
        from .config import load_config
        config = load_config()
        pat = config.get("GITHUB_PAT")
        return self.git.pull(remote, branch, pat=pat)

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
            {"name": "run_command", "description": "Execute shell command. Args: command (str), cwd (str, optional)"},
            {"name": "delete_path", "description": "Delete file/directory. Args: path (str)"},
            {"name": "get_dependencies", "description": "Analyze project dependencies. No args."},
            {"name": "web_search", "description": "Search the web. Args: query (str)"},
            {"name": "web_browse", "description": "Browse a website. Args: url (str)"},
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
            # Image Tools
            {"name": "generate_image", "description": "Generate an AI image. Args: prompt (str), save_to_project (bool, optional), filename (str, optional)"},
            {"name": "save_image", "description": "Save image from URL to project. Args: url (str), filename (str, optional), subdir (str, optional)"},
            {"name": "save_generated_images", "description": "Save all recently generated images. Args: subdir (str, optional)"},
            # Qwen Code Tool
            {"name": "qwen_code", "description": "Use qwen-code autonomous coding agent with FREE AI models. Args: prompt (str), working_dir (str, optional), model (str, optional)"}
        ]
    
    async def execute(self, tool_name: str, **kwargs) -> str:
        """Execute a tool by name with given arguments."""
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
            "run_command": self.run_command,
            "delete_path": self.delete_path,
            # Analysis Tools
            "get_dependencies": self.get_dependencies,
            "get_symbol_info": self.get_symbol_info,
            # Web Tools
            "web_search": self.web_search,
            "web_browse": self.web_browse,
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
            # Image Tools
            "generate_image": self.generate_image,
            "save_image": self.save_image,
            "save_generated_images": self.save_generated_images,
            # Qwen Code Tool
            "qwen_code": self.qwen_code,
        }
        
        if tool_name not in tool_map:
            return f"Error: Unknown tool '{tool_name}'. Available: {list(tool_map.keys())}"
        
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
