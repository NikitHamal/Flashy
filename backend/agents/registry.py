"""
Agent Registry Module

Manages agent registration, instantiation, and session management.
"""

from typing import Dict, Any, List, Optional, Type
from dataclasses import dataclass, field
import json
import os

from .base import BaseAgent, AgentType, AgentMessage


# Default agent configurations
DEFAULT_AGENT_CONFIG = {
    AgentType.ORCHESTRATOR: {
        "provider": "qwen",
        "model": "qwen3.6-plus",
        "description": "Coordinates tasks and delegates to specialized agents"
    },
    AgentType.ARCHITECT: {
        "provider": "qwen",
        "model": "qwen3-235b-a22b",
        "description": "Designs system architecture and plans"
    },
    AgentType.DEVELOPER: {
        "provider": "qwen",
        "model": "qwen3-coder-plus",
        "description": "Implements code and features"
    },
    AgentType.REVIEWER: {
        "provider": "qwen",
        "model": "qwen3-coder-plus",
        "description": "Reviews code for quality and security"
    },
    AgentType.RESEARCHER: {
        "provider": "qwen",
        "model": "qwen3-235b-a22b",
        "description": "Searches documentation and web"
    },
    AgentType.EXPLORER: {
        "provider": "qwen",
        "model": "qwen3-235b-a22b",
        "description": "Explores and understands codebase"
    },
    AgentType.LEARNER: {
        "provider": "qwen",
        "model": "qwen3-235b-a22b",
        "description": "Learns from project and maintains memory"
    },
    AgentType.DOCUMENTATION: {
        "provider": "qwen",
        "model": "qwen3-coder-plus",
        "description": "Generates documentation"
    },
    AgentType.REFACTOR: {
        "provider": "qwen",
        "model": "qwen3-coder-plus",
        "description": "Refactors and improves code"
    },
    AgentType.TESTING: {
        "provider": "qwen",
        "model": "qwen3-coder-plus",
        "description": "Creates and runs tests"
    },
    AgentType.DEPLOY: {
        "provider": "qwen",
        "model": "qwen3.6-plus",
        "description": "Handles deployment tasks"
    }
}


@dataclass
class AgentSession:
    """Manages an active agent instance."""
    agent: BaseAgent
    created_at: float
    last_active: float
    task_count: int = 0
    
    def update_activity(self):
        import time
        self.last_active = time.time()
        self.task_count += 1


class AgentRegistry:
    """
    Central registry for agent types and configurations.
    
    Handles:
    - Agent type registration
    - Configuration loading/saving
    - Agent instantiation
    - Session management
    """
    
    def __init__(self, config_path: str = "agent_config.json"):
        self.config_path = config_path
        self.agent_classes: Dict[AgentType, Type[BaseAgent]] = {}
        self.sessions: Dict[str, AgentSession] = {}
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load agent configuration from file or use defaults."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    saved = json.load(f)
                    # Merge with defaults
                    config = {}
                    for agent_type in AgentType:
                        default = DEFAULT_AGENT_CONFIG.get(agent_type, {})
                        saved_config = saved.get(agent_type.value, {})
                        config[agent_type.value] = {**default, **saved_config}
                    return config
            except:
                pass
        
        # Return defaults
        return {k.value: v for k, v in DEFAULT_AGENT_CONFIG.items()}
    
    def save_config(self):
        """Save current configuration to file."""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_agent_config(self, agent_type: AgentType) -> Dict[str, Any]:
        """Get configuration for an agent type."""
        return self.config.get(agent_type.value, DEFAULT_AGENT_CONFIG.get(agent_type, {}))
    
    def update_agent_config(self, agent_type: AgentType, provider: str = None, model: str = None):
        """Update configuration for an agent type."""
        if agent_type.value not in self.config:
            self.config[agent_type.value] = {}
        
        if provider:
            self.config[agent_type.value]["provider"] = provider
        if model:
            self.config[agent_type.value]["model"] = model
            
        self.save_config()
    
    def register_agent_class(self, agent_type: AgentType, agent_class: Type[BaseAgent]):
        """Register an agent class for a type."""
        self.agent_classes[agent_type] = agent_class
    
    def create_agent(
        self,
        agent_type: AgentType,
        workspace_path: str = None,
        session_id: str = None,
        register: bool = True
    ) -> BaseAgent:
        """Create an agent instance with configured provider/model."""
        config = self.get_agent_config(agent_type)
        
        # Get the registered class or import dynamically
        agent_class = self.agent_classes.get(agent_type)
        if not agent_class:
            # Import dynamically based on type
            if agent_type == AgentType.ORCHESTRATOR:
                from .orchestrator import OrchestratorAgent
                agent_class = OrchestratorAgent
            elif agent_type == AgentType.ARCHITECT:
                from .architect import ArchitectAgent
                agent_class = ArchitectAgent
            elif agent_type == AgentType.DEVELOPER:
                from .developer import DeveloperAgent
                agent_class = DeveloperAgent
            elif agent_type == AgentType.REVIEWER:
                from .reviewer import ReviewerAgent
                agent_class = ReviewerAgent
            elif agent_type == AgentType.RESEARCHER:
                from .researcher import ResearcherAgent
                agent_class = ResearcherAgent
            elif agent_type == AgentType.EXPLORER:
                from .explorer import ExplorerAgent
                agent_class = ExplorerAgent
            elif agent_type == AgentType.LEARNER:
                from .learner import LearnerAgent
                agent_class = LearnerAgent
            elif agent_type == AgentType.DOCUMENTATION:
                from .subagents.documentation import DocumentationAgent
                agent_class = DocumentationAgent
            elif agent_type == AgentType.REFACTOR:
                from .subagents.refactor import RefactorAgent
                agent_class = RefactorAgent
            elif agent_type == AgentType.TESTING:
                from .subagents.testing import TestingAgent
                agent_class = TestingAgent
            elif agent_type == AgentType.DEPLOY:
                from .subagents.deploy import DeployAgent
                agent_class = DeployAgent
            else:
                return None
        
        agent = agent_class(
            provider_name=config.get("provider", "gemini"),
            model=config.get("model", "G_3_0_FLASH"),
            workspace_path=workspace_path,
            session_id=session_id
        )

        if register and session_id:
            self.register_session(session_id, agent)

        return agent
    
    def register_session(self, session_id: str, agent: Any):
        """Register an active agent session."""
        import time
        self.sessions[session_id] = AgentSession(
            agent=agent,
            created_at=time.time(),
            last_active=time.time()
        )

    def update_session(self, session_id: str):
        """Update activity for a session."""
        if session_id in self.sessions:
            self.sessions[session_id].update_activity()

    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all agent configurations for settings UI."""
        result = {}
        for agent_type in AgentType:
            config = self.get_agent_config(agent_type)
            result[agent_type.value] = {
                "provider": config.get("provider", "gemini"),
                "model": config.get("model", ""),
                "description": config.get("description", "")
            }
        return result


# Global registry instance
agent_registry = AgentRegistry()
