import os
import subprocess
import json
from typing import List, Dict, Optional

class GitManager:
    def __init__(self, workspace_path: str = None):
        self.workspace_path = workspace_path

    def _run_git(self, args: List[str], cwd: str = None) -> Dict:
        """Helper to run git commands and return structured output."""
        target_cwd = cwd or self.workspace_path
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=target_cwd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "exit_code": result.returncode
            }
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "exit_code": -1}

    def is_repo(self, path: str = None) -> bool:
        """Check if a path is a git repository."""
        path = path or self.workspace_path
        if not path or not os.path.exists(path):
            return False
        res = self._run_git(['rev-parse', '--is-inside-work-tree'], cwd=path)
        return res["success"]

    def init_repo(self, path: str = None) -> str:
        """Initialize a new git repository."""
        path = path or self.workspace_path
        res = self._run_git(['init'], cwd=path)
        return res["stdout"] if res["success"] else f"Error: {res['stderr']}"

    def clone_repo(self, url: str, path: str, pat: str = None) -> str:
        """Clone a repository, optionally using a PAT."""
        # If PAT is provided, inject it into the URL
        if pat and "github.com" in url:
            if url.startswith("https://"):
                url = url.replace("https://", f"https://{pat}@")
        
        # Clone into the target path
        res = self._run_git(['clone', url, path], cwd=os.path.dirname(path) or ".")
        return res["stdout"] if res["success"] else f"Error: {res['stderr']}"

    def get_status(self) -> str:
        """Get git status."""
        res = self._run_git(['status', '--short'])
        return res["stdout"] if res["success"] else f"Error: {res['stderr']}"

    def get_branches(self) -> List[Dict]:
        """Get list of branches."""
        res = self._run_git(['branch', '-a'])
        if not res["success"]:
            return []
        
        branches = []
        for line in res["stdout"].split('\n'):
            line = line.strip()
            if not line: continue
            is_current = line.startswith('*')
            name = line.replace('*', '').strip()
            branches.append({"name": name, "current": is_current})
        return branches

    def checkout(self, branch: str, create: bool = False) -> str:
        """Switch or create branches."""
        args = ['checkout', '-b', branch] if create else ['checkout', branch]
        res = self._run_git(args)
        return res["stdout"] if res["success"] else f"Error: {res['stderr']}"

    def commit(self, message: str) -> str:
        """Stage all and commit."""
        self._run_git(['add', '.'])
        res = self._run_git(['commit', '-m', message])
        return res["stdout"] if res["success"] else f"Error: {res['stderr']}"

    def push(self, remote: str = "origin", branch: str = None, pat: str = None) -> str:
        """Push changes."""
        if not branch:
            curr = self._run_git(['branch', '--show-current'])
            branch = curr["stdout"]
        
        # If PAT is provided, we use it for this specific command via an environment variable or URL update
        # For security and simplicity in subprocess, we'll assume the remote is already authenticated 
        # or the user has a credential helper. 
        res = self._run_git(['push', remote, branch])
        if res["success"]:
            return f"Successfully pushed to {remote}/{branch}"
        return f"Push failed: {res['stderr']}"

    def pull(self, remote: str = "origin", branch: str = None) -> str:
        """Pull changes."""
        if not branch:
            curr = self._run_git(['branch', '--show-current'])
            branch = curr["stdout"]
        res = self._run_git(['pull', remote, branch])
        if res["success"]:
            return f"Successfully pulled from {remote}/{branch}"
        return f"Pull failed: {res['stderr']}"

    def get_log(self, limit: int = 10) -> List[Dict]:
        """Get structured commit history."""
        # Format: hash|date|author|subject
        format_str = "%H|%cr|%an|%s"
        res = self._run_git(['log', f'-n {limit}', f'--pretty=format:{format_str}'])
        
        if not res["success"]:
            return []
        
        commits = []
        for line in res["stdout"].split('\n'):
            if not line: continue
            parts = line.split('|')
            if len(parts) >= 4:
                commits.append({
                    "hash": parts[0][:7],
                    "date": parts[1],
                    "author": parts[2],
                    "message": parts[3]
                })
        return commits
