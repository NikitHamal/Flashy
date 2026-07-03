"""
Codebase Explorer Agent

Navigates and understands existing codebase structure.
"""

from typing import Dict, Any, List
import json

from .base import BaseAgent, AgentType, AgentResult


class ExplorerAgent(BaseAgent):
    """
    Codebase Explorer Agent - Understands existing code.
    
    Responsibilities:
    - Navigate codebase structure
    - Understand code relationships
    - Find relevant files and functions
    - Explain how code works
    """
    
    def __init__(
        self,
        provider_name: str = "g4f",
        model: str = "qwen3-235b-a22b",
        workspace_path: str = None,
        session_id: str = None
    ):
        super().__init__(
            agent_type=AgentType.EXPLORER,
            provider_name=provider_name,
            model=model,
            workspace_path=workspace_path,
            session_id=session_id
        )
        
    def get_system_prompt(self) -> str:
        return """You are the Codebase Explorer Agent for Flashy, a collaborative AI coding assistant.

Your role is to navigate, understand, and explain existing codebases.

When exploring code, you should:
1. ANALYZE the overall structure and architecture
2. IDENTIFY key files, classes, and functions
3. TRACE data flow and dependencies
4. EXPLAIN how components work together
5. FIND specific code relevant to a task

Output your exploration in this format:
{
    "overview": "High-level description of what this code does",
    "structure": {
        "entry_points": ["main files or functions"],
        "core_components": ["key classes/modules"],
        "utilities": ["helper files/functions"]
    },
    "relevant_files": [
        {"path": "path/to/file", "purpose": "what it does", "relevance": "why it matters"}
    ],
    "code_flow": "Description of how data/control flows through the system",
    "key_functions": [
        {"name": "function_name", "file": "path", "purpose": "what it does"}
    ],
    "recommendations": ["where to look", "what to modify"]
}

Be thorough and help other agents understand the codebase."""
    
    async def execute(
        self,
        task: str,
        context: Dict[str, Any] = None
    ) -> AgentResult:
        """Explore codebase for a given task."""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Explore and analyze:\n\n{task}"}
        ]
        
        if context:
            if "file_tree" in context:
                messages[1]["content"] += f"\n\nFile structure:\n{json.dumps(context['file_tree'], indent=2)}"
            if "file_contents" in context:
                for path, content in context["file_contents"].items():
                    messages[1]["content"] += f"\n\n--- {path} ---\n{content[:2000]}"
        
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
                exploration = json.loads(full_response[start:end])
                relevant = exploration.get("relevant_files", [])
                summary = f"Explored codebase. Found {len(relevant)} relevant file(s)."
                return AgentResult(
                    agent_type=self.agent_type,
                    success=True,
                    output=full_response,
                    summary=summary,
                    details=exploration
                )
        except json.JSONDecodeError:
            pass
        
        return AgentResult(
            agent_type=self.agent_type,
            success=True,
            output=full_response,
            summary="Codebase exploration completed",
            details={"raw_response": full_response, "thoughts": thoughts}
        )
