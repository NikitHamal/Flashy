import os
import subprocess
import glob
import tempfile
import shutil
import json
import asyncio
import sys
from typing import Optional, List, Dict, Any

from ..git_manager import GitManager
from ..websocket_manager import ws_manager


def _get_shell_command(command: str) -> tuple:
    """Get the shell executable and arguments for cross-platform execution.
    
    Returns:
        tuple: (executable, args_prefix, shell_type)
    """
    if sys.platform == 'win32':
        # Check if running in Git Bash / MSYS2 / MinTTY
        msystem = os.environ.get('MSYSTEM', '')
        term = os.environ.get('TERM', '')
        is_git_bash = (
            msystem.startswith('MINGW') or
            msystem.startswith('MSYS') or
            'msys' in term.lower() or
            'cygwin' in term.lower()
        )
        
        if is_git_bash:
            # Use bash for Git Bash environments
            return ('bash', ['-c'], 'bash')
        
        # Check for PowerShell
        com_spec = os.environ.get('ComSpec', 'cmd.exe').lower()
        if com_spec.endswith('powershell.exe') or com_spec.endswith('pwsh.exe'):
            return (com_spec, ['-NoProfile', '-Command'], 'powershell')
        
        # Default to cmd.exe
        return (os.environ.get('ComSpec', 'cmd.exe'), ['/d', '/s', '/c'], 'cmd')
    
    # Unix-like systems (Linux, macOS)
    return ('/bin/bash', ['-c'], 'bash')


class ExecutionMixin:
    async def run_shell_command(self, command: str, cwd: Optional[str] = None, timeout: int = 300, is_background: bool = False) -> str:
        """Execute a shell command in the workspace.

        Args:
            command: Shell command to execute
            cwd: Working directory (resolved relative to workspace)
            timeout: Max execution time in seconds (default 300 = 5 min). Ignored if is_background=True.
            is_background: Run the command in the background without waiting.
        """
        try:
            if not command or not command.strip():
                return "Error: Command is empty."
            work_dir = self._resolve_path(cwd) if cwd else self.workspace_path
            
            # Ensure work_dir exists
            if not os.path.isdir(work_dir):
                return f"Error: Working directory does not exist: {work_dir}"

            if is_background:
                terminal_id = f"bg_{os.urandom(4).hex()}"
                
                # On Windows, create_subprocess_shell is more reliable
                # On Unix, we can use create_subprocess_exec with explicit shell
                if sys.platform == 'win32':
                    process = await asyncio.create_subprocess_shell(
                        command,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=work_dir,
                    )
                else:
                    shell_exe, shell_args, shell_type = _get_shell_command(command)
                    process = await asyncio.create_subprocess_exec(
                        shell_exe,
                        *shell_args,
                        command,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=work_dir,
                    )
                
                if not hasattr(ws_manager, 'bg_processes'):
                    ws_manager.bg_processes = {}
                    ws_manager.bg_buffers = {}
                
                ws_manager.bg_processes[terminal_id] = process
                ws_manager.bg_buffers[terminal_id] = []
                
                async def read_bg_stream(stream, term_id):
                    while True:
                        try:
                            chunk = await stream.read(4096)
                            if not chunk:
                                break
                            text = chunk.decode("utf-8", errors="replace")
                            if term_id in ws_manager.bg_buffers:
                                ws_manager.bg_buffers[term_id].append(text)
                            # keep buffer reasonably sized
                            if sum(len(c) for c in ws_manager.bg_buffers[term_id]) > 500000:
                                ws_manager.bg_buffers[term_id] = ws_manager.bg_buffers[term_id][-50:]
                        except Exception:
                            break
                            
                asyncio.create_task(read_bg_stream(process.stdout, terminal_id))
                asyncio.create_task(read_bg_stream(process.stderr, terminal_id))
                
                return f"Background process started with ID: {terminal_id}\nCommand: `{command}`\nUse `read_background_output` to check its logs."

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
            # On Windows, create_subprocess_shell is more reliable
            if sys.platform == 'win32':
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=work_dir,
                )
            else:
                shell_exe, shell_args, shell_type = _get_shell_command(command)
                process = await asyncio.create_subprocess_exec(
                    shell_exe,
                    *shell_args,
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
            import traceback
            error_details = str(e) if str(e) else f"{type(e).__name__}: {repr(e)}"
            tb_info = traceback.format_exc()
            return f"Error running command:\n```\n{error_details}\n{tb_info}\n```"

    def read_background_output(self, process_id: str) -> str:
        """Read the recent output of a background process."""
        if not hasattr(ws_manager, 'bg_processes') or process_id not in ws_manager.bg_processes:
            return f"Error: Background process '{process_id}' not found or already terminated."
            
        process = ws_manager.bg_processes[process_id]
        buffer = "".join(ws_manager.bg_buffers.get(process_id, []))
        
        status = "Running" if process.returncode is None else f"Terminated with code {process.returncode}"
        
        return f"Process: {process_id} ({status})\nOutput:\n```\n{buffer[-10000:].strip() or '(no output)'}\n```"

    def list_background_processes(self) -> str:
        """List all active and recently completed background processes."""
        if not hasattr(ws_manager, 'bg_processes') or not ws_manager.bg_processes:
            return "No background processes found."
            
        results = []
        for pid, proc in ws_manager.bg_processes.items():
            status = "Running" if proc.returncode is None else f"Terminated with code {proc.returncode}"
            results.append(f"- {pid}: {status}")
        return "Background Processes:\n" + "\n".join(results)
