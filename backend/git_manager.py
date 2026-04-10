import os
import subprocess
import json
from typing import List, Dict, Optional
from urllib.parse import urlparse, urlunparse, quote

class GitManager:
    def __init__(self, workspace_path: str = None):
        self.workspace_path = workspace_path

    def _run_git(self, args: List[str], cwd: str = None, redact: str = None) -> Dict:
        """Helper to run git commands and return structured output."""
        target_cwd = cwd or self.workspace_path
        try:
            env = os.environ.copy()
            # Prevent hanging prompts for credentials in non-interactive runs
            env.setdefault("GIT_TERMINAL_PROMPT", "0")
            env.setdefault("GCM_INTERACTIVE", "Never")
            result = subprocess.run(
                ['git'] + args,
                cwd=target_cwd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env
            )
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            if redact:
                stdout = stdout.replace(redact, "***")
                stderr = stderr.replace(redact, "***")
            return {
                "success": result.returncode == 0,
                "stdout": stdout,
                "stderr": stderr,
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
            parsed = urlparse(url)
            if parsed.scheme in ("http", "https"):
                netloc = parsed.netloc.split("@", 1)[-1]
                netloc = f"{quote(pat, safe='')}@{netloc}"
                url = urlunparse(parsed._replace(netloc=netloc))
        
        # Clone into the target path
        res = self._run_git(['clone', url, path], cwd=os.path.dirname(path) or ".", redact=pat)
        return res["stdout"] if res["success"] else f"Error: {res['stderr']}"

    def get_status(self) -> str:
        """Get git status."""
        res = self._run_git(['status', '--short'])
        return res["stdout"] if res["success"] else f"Error: {res['stderr']}"

    def get_status_full(self) -> Dict[str, List[Dict]]:
        """Get structured git status separating staged and unstaged changes."""
        res = self._run_git(['status', '--porcelain'])
        if not res["success"]:
            return {"staged": [], "unstaged": []}
        
        staged = []
        unstaged = []
        
        for line in res["stdout"].split('\n'):
            if not line or len(line) < 3:
                continue

            if line.startswith("?? "):
                path = line[3:].strip()
                unstaged.append({"path": path, "status": "untracked"})
                continue
            
            x = line[0] # Index status
            y = line[1] # Work tree status
            path = line[3:].strip()
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            
            # Map status codes to human readable
            status_map = {
                'M': 'modified',
                'A': 'added',
                'D': 'deleted',
                'R': 'renamed',
                'C': 'copied',
                'U': 'unmerged',
                '?': 'untracked'
            }
            
            if x in status_map:
                staged.append({"path": path, "status": status_map[x]})
            
            if y in status_map:
                unstaged.append({"path": path, "status": status_map[y]})
                
        return {"staged": staged, "unstaged": unstaged}

    def stage_file(self, path: str) -> str:
        """Stage a specific file."""
        res = self._run_git(['add', path])
        return "Success" if res["success"] else f"Error: {res['stderr']}"
        
    def unstage_file(self, path: str) -> str:
        """Unstage a specific file (reset)."""
        res = self._run_git(['restore', '--staged', path])
        if not res["success"]:
            # Fallback for older git versions
            res = self._run_git(['reset', 'HEAD', path])
        return "Success" if res["success"] else f"Error: {res['stderr']}"

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
            if "->" in name:
                continue
            branches.append({"name": name, "current": is_current})
        return branches

    def checkout(self, branch: str, create: bool = False) -> str:
        """Switch or create branches."""
        args = ['checkout', '-b', branch] if create else ['checkout', branch]
        res = self._run_git(args)
        return res["stdout"] if res["success"] else f"Error: {res['stderr']}"

    def commit(self, message: str, stage_all: bool = False) -> str:
        """Commit changes."""
        if stage_all:
            self._run_git(['add', '-A'])
        res = self._run_git(['commit', '-m', message])
        return res["stdout"] if res["success"] else f"Error: {res['stderr']}"

    def push(self, remote: str = "origin", branch: str = None, pat: str = None) -> str:
        """Push changes."""
        if not branch:
            curr = self._run_git(['branch', '--show-current'])
            branch = curr["stdout"]
        if not branch:
            return "Push failed: No current branch (detached HEAD?)."

        authed_remote = remote
        redact_pat = None
        if pat:
            remote_url = self._run_git(['remote', 'get-url', remote])
            if remote_url["success"]:
                parsed = urlparse(remote_url["stdout"].splitlines()[0].strip())
                if parsed.scheme in ("http", "https") and "github.com" in parsed.netloc:
                    netloc = parsed.netloc.split("@", 1)[-1]
                    authed_netloc = f"{quote(pat, safe='')}@{netloc}"
                    authed_remote = urlunparse(parsed._replace(netloc=authed_netloc))
                    redact_pat = pat
        
        # If PAT is provided, we use it for this specific command via an environment variable or URL update
        # For security and simplicity in subprocess, we'll assume the remote is already authenticated 
        # or the user has a credential helper. 
        res = self._run_git(['push', authed_remote, branch], redact=redact_pat)
        if res["success"]:
            return f"Successfully pushed to {remote}/{branch}"
        return f"Push failed: {res['stderr']}"

    def pull(self, remote: str = "origin", branch: str = None, pat: str = None) -> str:
        """Pull changes."""
        if not branch:
            curr = self._run_git(['branch', '--show-current'])
            branch = curr["stdout"]
        if not branch:
            return "Pull failed: No current branch (detached HEAD?)."
        authed_remote = remote
        redact_pat = None
        if pat:
            remote_url = self._run_git(['remote', 'get-url', remote])
            if remote_url["success"]:
                parsed = urlparse(remote_url["stdout"].splitlines()[0].strip())
                if parsed.scheme in ("http", "https") and "github.com" in parsed.netloc:
                    netloc = parsed.netloc.split("@", 1)[-1]
                    authed_netloc = f"{quote(pat, safe='')}@{netloc}"
                    authed_remote = urlunparse(parsed._replace(netloc=authed_netloc))
                    redact_pat = pat
        res = self._run_git(['pull', authed_remote, branch], redact=redact_pat)
        if res["success"]:
            return f"Successfully pulled from {remote}/{branch}"
        return f"Pull failed: {res['stderr']}"

    def get_log(self, limit: int = 10) -> List[Dict]:
        """Get structured commit history."""
        # Format: hash|date|author|subject
        format_str = "%H|%cr|%an|%s"
        res = self._run_git(['log', '-n', str(limit), f'--pretty=format:{format_str}'])
        
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

    def get_version(self) -> Optional[str]:
        """Get git version string."""
        res = self._run_git(['--version'])
        return res["stdout"] if res["success"] else None

    def get_root(self) -> Optional[str]:
        """Get repo root path."""
        res = self._run_git(['rev-parse', '--show-toplevel'])
        return res["stdout"] if res["success"] else None

    def get_current_branch(self) -> Optional[str]:
        """Get current branch name or HEAD if detached."""
        res = self._run_git(['rev-parse', '--abbrev-ref', 'HEAD'])
        return res["stdout"] if res["success"] else None

    def get_upstream(self) -> Optional[str]:
        """Get upstream tracking branch (e.g., origin/main)."""
        res = self._run_git(['rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}'])
        return res["stdout"] if res["success"] else None

    def get_remotes(self) -> List[Dict[str, str]]:
        """Get remotes with fetch/push URLs."""
        res = self._run_git(['remote', '-v'])
        if not res["success"]:
            return []
        remotes = {}
        for line in res["stdout"].splitlines():
            parts = line.split()
            if len(parts) < 3:
                continue
            name, url, kind = parts[0], parts[1], parts[2].strip("()")
            remotes.setdefault(name, {})[kind] = url
        return [{"name": k, **v} for k, v in remotes.items()]

    def get_health(self, pat: str = None) -> Dict[str, Any]:
        """Return a structured self-check of git state for the workspace."""
        health: Dict[str, Any] = {
            "is_repo": self.is_repo(),
            "git_version": self.get_version(),
            "repo_root": None,
            "branch": None,
            "detached": None,
            "upstream": None,
            "remotes": [],
            "status": {"staged": [], "unstaged": []},
            "warnings": [],
            "errors": [],
        }

        if not health["is_repo"]:
            health["warnings"].append("Not a git repository.")
            return health

        health["repo_root"] = self.get_root()
        branch = self.get_current_branch()
        health["branch"] = branch
        health["detached"] = branch == "HEAD"
        health["upstream"] = self.get_upstream()
        health["remotes"] = self.get_remotes()
        health["status"] = self.get_status_full()

        if health["detached"]:
            health["warnings"].append("Detached HEAD state; push/pull may fail.")
        if not health["remotes"]:
            health["warnings"].append("No remotes configured.")
        if not health["upstream"]:
            health["warnings"].append("No upstream tracking branch set.")

        # Hint about auth readiness for GitHub HTTPS remotes
        github_https = [
            r for r in health["remotes"]
            if any(
                url and url.startswith("https://") and "github.com" in url
                for url in (r.get("fetch"), r.get("push"))
            )
        ]
        if github_https and not pat:
            health["warnings"].append(
                "GitHub HTTPS remote detected but no PAT configured; push/pull may require credential helper."
            )

        return health
