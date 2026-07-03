"""
Deploy Sub-Agent

Handles deployment tasks and scripts.
"""

from typing import Dict, Any, List
import json

from ..base import BaseAgent, AgentType, AgentResult


class DeployAgent(BaseAgent):
    """
    Deploy Agent - Handles deployments.
    
    Responsibilities:
    - Create deployment scripts
    - Configure CI/CD
    - Generate Docker files
    - Write infrastructure code
    """
    
    def __init__(
        self,
        provider_name: str = "g4f",
        model: str = "qwen3.6-plus",
        workspace_path: str = None,
        session_id: str = None
    ):
        super().__init__(
            agent_type=AgentType.DEPLOY,
            provider_name=provider_name,
            model=model,
            workspace_path=workspace_path,
            session_id=session_id
        )
        
    def get_system_prompt(self) -> str:
        return """You are the Deploy Agent for Flashy, a collaborative AI coding assistant.

Your role is to handle deployment and infrastructure tasks.

When handling deployments, you should:
1. ANALYZE the project structure and requirements
2. CREATE deployment scripts and configurations
3. GENERATE Dockerfiles and docker-compose files
4. CONFIGURE CI/CD pipelines (GitHub Actions, etc.)
5. WRITE infrastructure-as-code when needed

Output your deployment artifacts in this format:
{
    "artifacts": [
        {
            "file": "Dockerfile",
            "type": "docker|script|config|ci",
            "content": "full file content",
            "purpose": "what this file does"
        }
    ],
    "commands": [
        {"name": "build", "command": "command to run", "description": "what it does"}
    ],
    "summary": "Brief description of deployment setup",
    "prerequisites": ["requirement 1", "requirement 2"]
}

Create production-ready deployment configurations."""
    
    async def execute(
        self,
        task: str,
        context: Dict[str, Any] = None
    ) -> AgentResult:
        """Create deployment artifacts."""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Create deployment setup for:\n\n{task}"}
        ]
        
        if context:
            if "project_structure" in context:
                messages[1]["content"] += f"\n\nProject structure:\n{json.dumps(context['project_structure'])}"
            if "requirements" in context:
                messages[1]["content"] += f"\n\nRequirements:\n{context['requirements']}"
        
        full_response = ""
        async for chunk in self.generate_stream(messages):
            if "text" in chunk:
                full_response += chunk["text"]
            elif "error" in chunk:
                return AgentResult(
                    agent_type=self.agent_type,
                    success=False,
                    output="",
                    summary=f"Error: {chunk['error']}"
                )
        
        # Parse response
        try:
            start = full_response.find("{")
            end = full_response.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(full_response[start:end])
                artifacts = result.get("artifacts", [])
                summary = f"Created {len(artifacts)} deployment artifact(s)"
                return AgentResult(
                    agent_type=self.agent_type,
                    success=True,
                    output=full_response,
                    summary=summary,
                    artifacts=[a.get("file") for a in artifacts],
                    details=result
                )
        except json.JSONDecodeError:
            pass
        
        return AgentResult(
            agent_type=self.agent_type,
            success=True,
            output=full_response,
            summary="Deployment setup created"
        )
