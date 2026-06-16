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


def _get_shell_command() -> tuple:
    """Detect the best available shell for cross-platform execution.
    
    Returns:
        tuple: (executable, args_prefix, shell_type)
    """
    if sys.platform == 'win32':
        # 1. Check for Git Bash / MSYS2 / MinTTY
        msystem = os.environ.get('MSYSTEM', '')
        term = os.environ.get('TERM', '')
        is_git_bash = (
            msystem.startswith('MINGW') or
            msystem.startswith('MSYS') or
            'msys' in term.lower() or
            'cygwin' in term.lower()
        )
        if is_git_bash:
            return ('bash', ['-c'], 'bash')
        
        # 2. Check for pwsh (PowerShell Core) in PATH
        import shutil
        pwsh_path = shutil.which('pwsh')
        if pwsh_path:
            return (pwsh_path, ['-NoProfile', '-Command'], 'pwsh')
        
        # 3. Check for Windows PowerShell in PATH
        powershell_path = shutil.which('powershell')
        if powershell_path:
            return (powershell_path, ['-NoProfile', '-Command'], 'powershell')
        
        # 4. Fall back to cmd.exe
        return (os.environ.get('ComSpec', 'cmd.exe'), ['/d', '/s', '/c'], 'cmd')
    
    # Unix-like systems (Linux, macOS)
    return ('/bin/bash', ['-c'], 'bash')


def _create_subprocess(command: str, cwd: str, **kwargs):
    """Create a subprocess using the best available shell."""
    shell_exe, shell_args, _ = _get_shell_command()
    return asyncio.create_subprocess_exec(
        shell_exe,
        *shell_args,
        command,
        cwd=cwd,
        **kwargs,
    )


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
                process = await _create_subprocess(
                    command, work_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    stdin=asyncio.subprocess.PIPE,
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
                            if sum(len(c) for c in ws_manager.bg_buffers[term_id]) > 500000:
                                ws_manager.bg_buffers[term_id] = ws_manager.bg_buffers[term_id][-50:]
                        except Exception:
                            break
                            
                asyncio.create_task(read_bg_stream(process.stdout, terminal_id))
                asyncio.create_task(read_bg_stream(process.stderr, terminal_id))
                
                return f"Background process started with ID: {terminal_id}\nCommand: `{command}`\nUse `read_background_output`, `send_terminal_input`, or `list_background_processes` to manage it."

            # If we have a session_id, stream the output via WebSocket
            if self.session_id:
                output, exit_code = await ws_manager.run_command_streamed(
                    self.session_id,
                    command,
                    cwd=work_dir
                )

                status = "✓ Success" if exit_code == 0 else f"✗ Exit code: {exit_code}"
                return f"Command: `{command}`\nStatus: {status}\nOutput:\n```\n{output.strip() or '(no output)'}\n```"

            # Non-session: use async subprocess with detected shell
            process = await _create_subprocess(
                command, work_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
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

    def send_terminal_input(self, process_id: str, input_text: str) -> str:
        """Send input to a running background process (stdin).

        Args:
            process_id: The background process ID (from run_shell_command with is_background=True)
            input_text: The text to send to the process's stdin
        """
        if not hasattr(ws_manager, 'bg_processes') or process_id not in ws_manager.bg_processes:
            return f"Error: Background process '{process_id}' not found."
        
        process = ws_manager.bg_processes[process_id]
        if process.returncode is not None:
            return f"Error: Process '{process_id}' has already terminated (exit code: {process.returncode})."
        
        if not process.stdin:
            return f"Error: Process '{process_id}' does not have stdin available."
        
        try:
            process.stdin.write(input_text.encode('utf-8'))
            # Use run_coroutine_threadsafe since this may be called from sync context
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(process.stdin.drain(), loop)
                else:
                    loop.run_until_complete(process.stdin.drain())
            except RuntimeError:
                pass
            return f"Sent '{input_text}' to process '{process_id}'."
        except Exception as e:
            return f"Error sending input: {str(e)}"

    def stop_background_process(self, process_id: str) -> str:
        """Kill/terminate a running background process.

        Args:
            process_id: The background process ID to terminate
        """
        if not hasattr(ws_manager, 'bg_processes') or process_id not in ws_manager.bg_processes:
            return f"Error: Background process '{process_id}' not found."
        
        process = ws_manager.bg_processes[process_id]
        if process.returncode is not None:
            return f"Process '{process_id}' has already terminated (exit code: {process.returncode})."
        
        try:
            process.terminate()
            return f"Process '{process_id}' terminated."
        except Exception as e:
            try:
                process.kill()
                return f"Process '{process_id}' killed (force)."
            except Exception as e2:
                return f"Error stopping process '{process_id}': {str(e2)}"
