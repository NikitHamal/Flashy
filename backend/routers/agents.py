"""
Agent Configuration Router

Provides REST API for agent configuration management.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from ..agents import agent_registry, AgentType

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentConfigUpdate(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None


@router.get("/config")
async def get_all_agent_configs():
    """Get all agent configurations."""
    return agent_registry.get_all_configs()


@router.get("/config/{agent_type}")
async def get_agent_config(agent_type: str):
    """Get configuration for a specific agent type."""
    try:
        atype = AgentType(agent_type)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Unknown agent type: {agent_type}")
    
    return agent_registry.get_agent_config(atype)


@router.put("/config/{agent_type}")
async def update_agent_config(agent_type: str, config: AgentConfigUpdate):
    """Update configuration for a specific agent type."""
    try:
        atype = AgentType(agent_type)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Unknown agent type: {agent_type}")
    
    agent_registry.update_agent_config(
        atype,
        provider=config.provider,
        model=config.model
    )
    
    return {"status": "updated", "agent_type": agent_type}


@router.get("/types")
async def get_agent_types():
    """Get all available agent types."""
    return [
        {
            "type": at.value,
            "description": agent_registry.get_agent_config(at).get("description", "")
        }
        for at in AgentType
    ]


@router.get("/providers")
async def get_available_providers():
    """Get all available providers for agent configuration."""
    return [
        {"id": "gemini", "name": "Google Gemini"},
        {"id": "deepinfra", "name": "DeepInfra"},
        {"id": "qwen", "name": "Qwen (Alibaba)"},
    ]


@router.get("/status")
async def get_active_agents_status():
    """Get status of all active agents."""
    status = []
    for session_id, agent_session in agent_registry.sessions.items():
        agent = agent_session.agent
        status.append({
            "id": agent.session_id,
            "type": agent.agent_type.value,
            "provider": agent.provider_name,
            "model": agent.model,
            "last_active": agent_session.last_active,
            "task_count": agent_session.task_count
        })
    return status
