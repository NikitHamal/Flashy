"""
Memory Router

Provides REST API for project memorybase management.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from ..agents.learner import LearnerAgent
from ..storage import get_workspace

router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryCreate(BaseModel):
    category: str
    title: str
    content: str
    importance: int = 3


class MemoryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    importance: Optional[int] = None


# Store learner agents per workspace
_learner_agents: Dict[str, Any] = {}


def get_learner_agent(workspace_id: str):
    """Get or create a learner agent for a workspace."""
    if workspace_id not in _learner_agents:
        workspace = get_workspace(workspace_id)
        workspace_path = workspace.get("path") if workspace else None

        _learner_agents[workspace_id] = LearnerAgent(
            workspace_path=workspace_path,
            session_id=workspace_id
        )
    return _learner_agents[workspace_id]


@router.get("/{workspace_id}")
async def get_all_memories(workspace_id: str):
    """Get all memories for a workspace."""
    learner = get_learner_agent(workspace_id)
    return {"memories": learner.get_all_memories()}


@router.post("/{workspace_id}")
async def create_memory(workspace_id: str, memory: MemoryCreate):
    """Create a new memory."""
    learner = get_learner_agent(workspace_id)
    new_memory = learner.add_memory(
        category=memory.category,
        title=memory.title,
        content=memory.content,
        importance=memory.importance
    )
    return {"status": "created", "memory": new_memory}


@router.delete("/{workspace_id}/{memory_id}")
async def delete_memory(workspace_id: str, memory_id: str):
    """Delete a memory."""
    learner = get_learner_agent(workspace_id)
    if learner.delete_memory(memory_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Memory not found")


@router.get("/{workspace_id}/search")
async def search_memories(workspace_id: str, query: str, limit: int = 5):
    """Search memories relevant to a query."""
    learner = get_learner_agent(workspace_id)
    relevant = learner.get_relevant_memories(query, limit)
    return {"memories": relevant}
