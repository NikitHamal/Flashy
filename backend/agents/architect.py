"""
Code Architect Agent

Designs system architecture, plans file structure, and makes high-level
technical decisions.
"""

from typing import Dict, Any, List
import json

from .base import BaseAgent, AgentType, AgentResult


class ArchitectAgent(BaseAgent):
    """
    Code Architect Agent - Designs systems and plans implementations.
    
    Responsibilities:
    - Design system architecture
    - Plan file/folder structure
    - Choose design patterns
    - Define interfaces and contracts
    - Make technology decisions
    """
    
    def __init__(
        self,
        provider_name: str = "g4f",
        model: str = "qwen3-235b-a22b",
        workspace_path: str = None,
        session_id: str = None
    ):
        super().__init__(
            agent_type=AgentType.ARCHITECT,
            provider_name=provider_name,
            model=model,
            workspace_path=workspace_path,
            session_id=session_id
        )
        
    def get_system_prompt(self) -> str:
        return """You are the Code Architect Agent for Flashy, a collaborative AI coding assistant.

Your role is to design robust, scalable, and maintainable software architectures.

When given a task, you should:
1. ANALYZE the requirements thoroughly
2. CONSIDER existing codebase structure (if provided)
3. DESIGN a clear architecture with:
   - File/folder structure
   - Component responsibilities
   - Data flow
   - Interfaces between components
4. SELECT appropriate design patterns
5. DOCUMENT your decisions with rationale

Your output should be structured as:
{
    "architecture_summary": "High-level description",
    "file_structure": [
        {"path": "path/to/file.py", "purpose": "description", "new": true/false}
    ],
    "components": [
        {"name": "ComponentName", "responsibility": "what it does", "dependencies": ["dep1"]}
    ],
    "patterns_used": ["pattern1", "pattern2"],
    "implementation_order": ["step1", "step2"],
    "considerations": ["important note 1", "important note 2"]
}

Be thorough but practical. Prioritize simplicity and maintainability."""
    
    async def execute(
        self,
        task: str,
        context: Dict[str, Any] = None
    ) -> AgentResult:
        """Design architecture for a given task."""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Design the architecture for:\n\n{task}"}
        ]
        
        if context:
            if "existing_files" in context:
                messages[1]["content"] += f"\n\nExisting files:\n{json.dumps(context['existing_files'], indent=2)}"
            if "codebase_summary" in context:
                messages[1]["content"] += f"\n\nCodebase summary:\n{context['codebase_summary']}"
        
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
                design = json.loads(full_response[start:end])
                summary = design.get("architecture_summary", "Architecture designed")
                return AgentResult(
                    agent_type=self.agent_type,
                    success=True,
                    output=full_response,
                    summary=summary,
                    details=design,
                    artifacts=[]
                )
        except json.JSONDecodeError:
            pass
        
        # Return raw response if not structured
        return AgentResult(
            agent_type=self.agent_type,
            success=True,
            output=full_response,
            summary="Architecture design completed",
            details={"raw_response": full_response, "thoughts": thoughts}
        )
