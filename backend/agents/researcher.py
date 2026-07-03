"""
Researcher Agent

Searches documentation, web, and learns about new APIs/technologies.
"""

from typing import Dict, Any, List
import json

from .base import BaseAgent, AgentType, AgentResult


class ResearcherAgent(BaseAgent):
    """
    Researcher Agent - Gathers information and documentation.
    
    Responsibilities:
    - Search documentation
    - Research APIs and libraries
    - Find relevant examples
    - Summarize findings
    """
    
    def __init__(
        self,
        provider_name: str = "g4f",
        model: str = "qwen3-235b-a22b",
        workspace_path: str = None,
        session_id: str = None
    ):
        super().__init__(
            agent_type=AgentType.RESEARCHER,
            provider_name=provider_name,
            model=model,
            workspace_path=workspace_path,
            session_id=session_id
        )
        
    def get_system_prompt(self) -> str:
        return """You are the Researcher Agent for Flashy, a collaborative AI coding assistant.

Your role is to gather information, research technologies, and provide knowledge.

When given a research task, you should:
1. ANALYZE what information is needed
2. SEARCH your knowledge for relevant information
3. EXPLAIN concepts clearly and concisely
4. PROVIDE code examples when helpful
5. CITE sources or documentation when possible

Output your research in this format:
{
    "topic": "What was researched",
    "summary": "Brief 2-3 sentence summary",
    "key_findings": [
        {"point": "important finding", "details": "explanation"}
    ],
    "code_examples": [
        {"description": "what it shows", "code": "example code", "language": "python"}
    ],
    "resources": ["url or doc name 1", "url or doc name 2"],
    "recommendations": ["how to use this info"]
}

Be accurate and practical. Focus on actionable information."""
    
    async def execute(
        self,
        task: str,
        context: Dict[str, Any] = None
    ) -> AgentResult:
        """Research a topic or technology."""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Research the following:\n\n{task}"}
        ]
        
        if context:
            if "specific_questions" in context:
                messages[1]["content"] += f"\n\nSpecific questions:\n{json.dumps(context['specific_questions'])}"
        
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
                research = json.loads(full_response[start:end])
                topic = research.get("topic", "Research")
                findings = research.get("key_findings", [])
                summary = f"Researched: {topic}. Found {len(findings)} key points."
                return AgentResult(
                    agent_type=self.agent_type,
                    success=True,
                    output=full_response,
                    summary=summary,
                    details=research
                )
        except json.JSONDecodeError:
            pass
        
        return AgentResult(
            agent_type=self.agent_type,
            success=True,
            output=full_response,
            summary="Research completed",
            details={"raw_response": full_response, "thoughts": thoughts}
        )
