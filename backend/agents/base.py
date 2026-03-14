"""
Base Agent Module

Provides the foundational classes for all AI agents in Flashy.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time


class AgentType(Enum):
    """Types of agents in the system."""
    ORCHESTRATOR = "orchestrator"
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    REVIEWER = "reviewer"
    RESEARCHER = "researcher"
    EXPLORER = "explorer"
    LEARNER = "learner"
    # Sub-agents
    DOCUMENTATION = "documentation"
    REFACTOR = "refactor"
    TESTING = "testing"
    DEPLOY = "deploy"


@dataclass
class AgentMessage:
    """Message exchanged between agents."""
    sender: str
    recipient: str
    content: str
    message_type: str = "task"  # task, result, query, context
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class AgentResult:
    """Result from an agent's task execution."""
    agent_type: AgentType
    success: bool
    output: str
    artifacts: List[str] = field(default_factory=list)  # File paths created/modified
    summary: str = ""  # User-facing summary
    details: Dict[str, Any] = field(default_factory=dict)  # Hidden details for other agents


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    Each agent has:
    - A specific role and capabilities
    - Access to a provider for LLM calls
    - Ability to communicate with other agents
    - Access to shared context
    """
    
    def __init__(
        self,
        agent_type: AgentType,
        provider_name: str,
        model: str,
        workspace_path: str = None,
        session_id: str = None
    ):
        self.agent_type = agent_type
        self.provider_name = provider_name
        self.model = model
        self.workspace_path = workspace_path
        self.session_id = session_id
        self.agent_id = f"{agent_type.value}_{uuid.uuid4().hex[:8]}"
        self.message_history: List[AgentMessage] = []
        
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass
    
    @abstractmethod
    async def execute(
        self,
        task: str,
        context: Dict[str, Any] = None
    ) -> AgentResult:
        """Execute a task and return the result."""
        pass
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate a streaming response using the configured provider."""
        from ..providers import get_provider_service
        
        provider = get_provider_service(self.provider_name)
        if not provider:
            yield {"error": f"Provider '{self.provider_name}' not found"}
            return
            
        async for chunk in provider.generate_stream(messages, self.model, **kwargs):
            yield chunk
    
    def send_message(self, recipient: str, content: str, message_type: str = "task") -> AgentMessage:
        """Send a message to another agent."""
        msg = AgentMessage(
            sender=self.agent_id,
            recipient=recipient,
            content=content,
            message_type=message_type
        )
        self.message_history.append(msg)
        return msg
    
    def receive_message(self, message: AgentMessage):
        """Receive a message from another agent."""
        self.message_history.append(message)
    
    def get_context_summary(self) -> str:
        """Get a summary of this agent's recent activity for other agents."""
        if not self.message_history:
            return f"{self.agent_type.value}: No activity yet."
        
        recent = self.message_history[-5:]
        summary = f"{self.agent_type.value} recent activity:\n"
        for msg in recent:
            summary += f"- [{msg.message_type}] {msg.content[:100]}...\n"
        return summary
