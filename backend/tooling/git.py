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

class GitMixin:
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
