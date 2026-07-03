"""
Documentation Sub-Agent

Generates documentation, docstrings, and README files.
"""

from typing import Dict, Any, List
import json

from ..base import BaseAgent, AgentType, AgentResult


class DocumentationAgent(BaseAgent):
    """
    Documentation Agent - Generates documentation.
    
    Responsibilities:
    - Write docstrings
    - Generate README files
    - Create API documentation
    - Write inline comments
    """
    
    def __init__(
        self,
        provider_name: str = "g4f",
        model: str = "qwen3-coder-plus",
        workspace_path: str = None,
        session_id: str = None
    ):
        super().__init__(
            agent_type=AgentType.DOCUMENTATION,
            provider_name=provider_name,
            model=model,
            workspace_path=workspace_path,
            session_id=session_id
        )
        
    def get_system_prompt(self) -> str:
        return """You are the Documentation Agent for Flashy, a collaborative AI coding assistant.

Your role is to generate clear, comprehensive documentation.

When documenting code, you should:
1. UNDERSTAND the code's purpose and functionality
2. WRITE clear docstrings following conventions (Google/NumPy style for Python)
3. CREATE README files with usage examples
4. ADD helpful inline comments for complex logic
5. GENERATE API documentation when needed

Output your documentation in this format:
{
    "documentation": [
        {
            "type": "docstring|readme|inline|api",
            "file": "path/to/file",
            "content": "the documentation content",
            "target": "function/class name or section"
        }
    ],
    "summary": "Brief description of documentation added"
}

Write documentation that helps developers understand and use the code effectively."""
    
    async def execute(
        self,
        task: str,
        context: Dict[str, Any] = None
    ) -> AgentResult:
        """Generate documentation for code."""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Generate documentation for:\n\n{task}"}
        ]
        
        if context:
            if "code" in context:
                messages[1]["content"] += f"\n\nCode:\n{context['code']}"
            if "file_contents" in context:
                for path, content in context["file_contents"].items():
                    messages[1]["content"] += f"\n\n--- {path} ---\n{content}"
        
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
                docs = result.get("documentation", [])
                summary = result.get("summary", f"Generated {len(docs)} documentation item(s)")
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
            summary="Documentation generated"
        )
