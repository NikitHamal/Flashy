"""
Reviewer Agent

Reviews code for quality, security, and best practices.
"""

from typing import Dict, Any, List
import json

from .base import BaseAgent, AgentType, AgentResult


class ReviewerAgent(BaseAgent):
    """
    Reviewer Agent - Reviews code and provides feedback.
    
    Responsibilities:
    - Code quality review
    - Security vulnerability detection
    - Best practices enforcement
    - Performance suggestions
    - Refactoring recommendations
    """
    
    def __init__(
        self,
        provider_name: str = "g4f",
        model: str = "qwen3-coder-plus",
        workspace_path: str = None,
        session_id: str = None
    ):
        super().__init__(
            agent_type=AgentType.REVIEWER,
            provider_name=provider_name,
            model=model,
            workspace_path=workspace_path,
            session_id=session_id
        )
        
    def get_system_prompt(self) -> str:
        return """You are the Code Reviewer Agent for Flashy, a collaborative AI coding assistant.

Your role is to review code for quality, security, and adherence to best practices.

When reviewing code, analyze:
1. CODE QUALITY: Readability, maintainability, DRY principles
2. SECURITY: Vulnerabilities, injection risks, authentication issues
3. PERFORMANCE: Efficiency, algorithmic complexity, resource usage
4. BEST PRACTICES: Design patterns, error handling, documentation
5. BUGS: Logic errors, edge cases, potential runtime issues

Output your review in this format:
{
    "overall_score": 1-10,
    "summary": "Brief overall assessment",
    "issues": [
        {
            "severity": "critical|high|medium|low",
            "type": "security|performance|quality|bug",
            "file": "path/to/file",
            "line": "line number or range",
            "description": "what's wrong",
            "suggestion": "how to fix it"
        }
    ],
    "positive_aspects": ["good thing 1", "good thing 2"],
    "recommended_actions": ["action 1", "action 2"]
}

Be thorough but constructive. Prioritize actionable feedback."""
    
    async def execute(
        self,
        task: str,
        context: Dict[str, Any] = None
    ) -> AgentResult:
        """Review code for a given task."""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Review the following:\n\n{task}"}
        ]
        
        if context:
            if "code" in context:
                messages[1]["content"] += f"\n\nCode to review:\n{context['code']}"
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
        try:
            start = full_response.find("{")
            end = full_response.rfind("}") + 1
            if start >= 0 and end > start:
                review = json.loads(full_response[start:end])
                score = review.get("overall_score", "N/A")
                issues = review.get("issues", [])
                critical = len([i for i in issues if i.get("severity") == "critical"])
                summary = f"Score: {score}/10. Found {len(issues)} issue(s)"
                if critical > 0:
                    summary += f" ({critical} critical)"
                return AgentResult(
                    agent_type=self.agent_type,
                    success=True,
                    output=full_response,
                    summary=summary,
                    details=review
                )
        except json.JSONDecodeError:
            pass
        
        return AgentResult(
            agent_type=self.agent_type,
            success=True,
            output=full_response,
            summary="Code review completed",
            details={"raw_response": full_response, "thoughts": thoughts}
        )
