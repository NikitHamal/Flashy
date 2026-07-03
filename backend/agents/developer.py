"""
Developer Agent

Implements code, writes features, and fixes bugs.
"""

from typing import Dict, Any, List
import json

from .base import BaseAgent, AgentType, AgentResult


class DeveloperAgent(BaseAgent):
    """
    Developer Agent - Writes and modifies code.
    
    Responsibilities:
    - Implement new features
    - Fix bugs
    - Write clean, maintainable code
    - Follow coding standards
    - Create file modifications
    """
    
    def __init__(
        self,
        provider_name: str = "g4f",
        model: str = "gpt-5.4-nano",
        workspace_path: str = None,
        session_id: str = None
    ):
        super().__init__(
            agent_type=AgentType.DEVELOPER,
            provider_name=provider_name,
            model=model,
            workspace_path=workspace_path,
            session_id=session_id
        )
        
    def get_system_prompt(self) -> str:
        return """You are the Developer Agent for Flashy, a collaborative AI coding assistant.

Your role is to write high-quality, production-ready code.

When given a task, you should:
1. UNDERSTAND the requirements and architecture (if provided)
2. WRITE clean, well-documented code
3. FOLLOW best practices and coding standards
4. CREATE complete, working implementations
5. HANDLE edge cases and errors appropriately

Output your code changes in this format:
{
    "changes": [
        {
            "file": "path/to/file.py",
            "action": "create|modify|delete",
            "content": "full file content or diff",
            "description": "what this change does"
        }
    ],
    "summary": "Brief description of all changes",
    "next_steps": ["optional follow-up tasks"]
}

Write complete, working code. Don't use placeholders like '...' or 'TODO'.
Include proper imports, error handling, and documentation."""
    
    async def execute(
        self,
        task: str,
        context: Dict[str, Any] = None
    ) -> AgentResult:
        """Implement code for a given task."""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Implement the following:\n\n{task}"}
        ]
        
        if context:
            if "architecture" in context:
                messages[1]["content"] += f"\n\nArchitecture plan:\n{json.dumps(context['architecture'], indent=2)}"
            if "existing_code" in context:
                messages[1]["content"] += f"\n\nExisting code:\n{context['existing_code']}"
            if "file_contents" in context:
                for path, content in context["file_contents"].items():
                    messages[1]["content"] += f"\n\n--- {path} ---\n{content}"
        
        full_response = ""
        thoughts = ""
        
        async for chunk in self.generate_stream(messages):
            if "thought" in chunk:
                thoughts += chunk["thought"]
            elif "text" in chunk:
                full_response += chunk["text"]
            elif "error" in chunk:
                return AgentResult(
                    agent_type=self.agent_type,
                    success=False,
                    output="",
                    summary=f"Error: {chunk['error']}"
                )
        
        # Try to parse structured response
        artifacts = []
        try:
            start = full_response.find("{")
            end = full_response.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(full_response[start:end])
                changes = result.get("changes", [])
                artifacts = [c.get("file") for c in changes if c.get("file")]
                summary = result.get("summary", f"Made {len(changes)} code change(s)")
                return AgentResult(
                    agent_type=self.agent_type,
                    success=True,
                    output=full_response,
                    summary=summary,
                    artifacts=artifacts,
                    details=result
                )
        except json.JSONDecodeError:
            pass
        
        return AgentResult(
            agent_type=self.agent_type,
            success=True,
            output=full_response,
            summary="Code implementation completed",
            details={"raw_response": full_response, "thoughts": thoughts}
        )
