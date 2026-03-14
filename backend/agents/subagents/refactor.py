"""
Refactor Sub-Agent

Refactors and improves code quality.
"""

from typing import Dict, Any, List
import json

from ..base import BaseAgent, AgentType, AgentResult


class RefactorAgent(BaseAgent):
    """
    Refactor Agent - Improves code quality.
    
    Responsibilities:
    - Refactor code for readability
    - Apply design patterns
    - Reduce code duplication
    - Improve performance
    """
    
    def __init__(
        self,
        provider_name: str = "qwen",
        model: str = "qwen3-coder-plus",
        workspace_path: str = None,
        session_id: str = None
    ):
        super().__init__(
            agent_type=AgentType.REFACTOR,
            provider_name=provider_name,
            model=model,
            workspace_path=workspace_path,
            session_id=session_id
        )
        
    def get_system_prompt(self) -> str:
        return """You are the Refactor Agent for Flashy, a collaborative AI coding assistant.

Your role is to improve code quality through refactoring.

When refactoring code, you should:
1. IDENTIFY code smells and anti-patterns
2. APPLY appropriate design patterns
3. REDUCE duplication (DRY principle)
4. IMPROVE readability and maintainability
5. OPTIMIZE performance where beneficial

Output your refactoring in this format:
{
    "refactorings": [
        {
            "file": "path/to/file",
            "original": "original code snippet",
            "refactored": "refactored code",
            "reason": "why this change improves the code"
        }
    ],
    "summary": "Brief description of refactoring",
    "impact": "low|medium|high"
}

Preserve functionality while improving code quality."""
    
    async def execute(
        self,
        task: str,
        context: Dict[str, Any] = None
    ) -> AgentResult:
        """Refactor code."""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Refactor the following:\n\n{task}"}
        ]
        
        if context:
            if "code" in context:
                messages[1]["content"] += f"\n\nCode to refactor:\n{context['code']}"
            if "review_issues" in context:
                messages[1]["content"] += f"\n\nReview issues to address:\n{json.dumps(context['review_issues'])}"
        
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
                refactorings = result.get("refactorings", [])
                impact = result.get("impact", "medium")
                summary = f"Applied {len(refactorings)} refactoring(s) ({impact} impact)"
                return AgentResult(
                    agent_type=self.agent_type,
                    success=True,
                    output=full_response,
                    summary=summary,
                    details=result
                )
        except json.JSONDecodeError:
            pass
        
        return AgentResult(
            agent_type=self.agent_type,
            success=True,
            output=full_response,
            summary="Refactoring completed"
        )
