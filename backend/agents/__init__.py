"""
Flashy Agent System

Multi-agent architecture for collaborative AI-powered development.
"""

from .base import BaseAgent, AgentType, AgentMessage, AgentResult
from .registry import AgentRegistry, AgentSession, agent_registry
from .orchestrator import OrchestratorAgent
from .architect import ArchitectAgent
from .developer import DeveloperAgent
from .reviewer import ReviewerAgent
from .researcher import ResearcherAgent
from .explorer import ExplorerAgent
from .learner import LearnerAgent

__all__ = [
    "BaseAgent",
    "AgentType", 
    "AgentMessage",
    "AgentResult",
    "AgentRegistry",
    "AgentSession",
    "agent_registry",
    "OrchestratorAgent",
    "ArchitectAgent",
    "DeveloperAgent",
    "ReviewerAgent",
    "ResearcherAgent",
    "ExplorerAgent",
    "LearnerAgent"
]

