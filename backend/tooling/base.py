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

class ToolsBase:
    def __init__(self, workspace_path: str = None, session_id: str = None):
        self.workspace_path = workspace_path or os.getcwd()
        self.session_id = session_id
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

    def _is_within_workspace(self, full_path: str) -> bool:
        """Check if a path is within the workspace root."""
        try:
            workspace = os.path.realpath(self.workspace_path)
            target = os.path.realpath(full_path)
            return os.path.commonpath([workspace, target]) == workspace
        except Exception:
            return False
