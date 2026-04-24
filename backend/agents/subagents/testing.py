"""
Testing Sub-Agent

Creates and runs tests.
"""

from typing import Dict, Any, List
import json

from ..base import BaseAgent, AgentType, AgentResult


class TestingAgent(BaseAgent):
    """
    Testing Agent - Creates tests.
    
    Responsibilities:
    - Write unit tests
    - Create integration tests
    - Generate test fixtures
    - Suggest test cases
    """
    
    def __init__(
        self,
        provider_name: str = "qwen",
        model: str = "qwen3-coder-plus",
        workspace_path: str = None,
        session_id: str = None
    ):
        super().__init__(
            agent_type=AgentType.TESTING,
            provider_name=provider_name,
            model=model,
            workspace_path=workspace_path,
            session_id=session_id
        )
        
    def get_system_prompt(self) -> str:
        return """You are the Testing Agent for Flashy, a collaborative AI coding assistant.

Your role is to create comprehensive tests for code.

When creating tests, you should:
1. ANALYZE the code to understand what needs testing
2. WRITE unit tests for individual functions/methods
3. CREATE integration tests for component interactions
4. GENERATE meaningful test data and fixtures
5. ENSURE edge cases are covered

Output your tests in this format:
{
    "tests": [
        {
            "file": "test_filename.py",
            "type": "unit|integration|e2e",
            "content": "full test file content",
            "covers": ["function1", "function2"]
        }
    ],
    "fixtures": [
        {"name": "fixture_name", "content": "fixture data"}
    ],
    "summary": "Brief description of tests created",
    "coverage_estimate": "percentage or description"
}

Write tests that are clear, maintainable, and provide good coverage."""
    
    async def execute(
        self,
        task: str,
        context: Dict[str, Any] = None
    ) -> AgentResult:
        """Create tests for code."""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Create tests for:\n\n{task}"}
        ]
        
        if context:
            if "code" in context:
                messages[1]["content"] += f"\n\nCode to test:\n{context['code']}"
            if "existing_tests" in context:
                messages[1]["content"] += f"\n\nExisting tests:\n{context['existing_tests']}"
        
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
                tests = result.get("tests", [])
                coverage = result.get("coverage_estimate", "unknown")
                summary = f"Created {len(tests)} test file(s). Coverage: {coverage}"
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
            summary="Tests created"
        )
