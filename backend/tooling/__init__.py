from .base import ToolsBase
from .filesystem import FileSystemMixin
from .execution import ExecutionMixin
from .collaboration import CollaborationMixin
from .web import WebMixin
from .git import GitMixin
from .registry import ToolRegistryMixin


class Tools(
    ToolsBase,
    FileSystemMixin,
    ExecutionMixin,
    CollaborationMixin,
    WebMixin,
    GitMixin,
    ToolRegistryMixin,
):
    """Collection of tools the agent can use to interact with the local system."""

    pass
