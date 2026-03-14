"""
Orchestrator Agent

The main coordinating agent that receives user requests, analyzes them,
and delegates to specialized agents.
"""

from typing import Dict, Any, List, Optional
import json

from .base import BaseAgent, AgentType, AgentMessage, AgentResult


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent - The team lead that coordinates all other agents.
    
    Responsibilities:
    - Analyze user requests and break them into sub-tasks
    - Delegate tasks to appropriate specialized agents
    - Synthesize results from multiple agents
    - Provide unified summaries to users
    """
    
    def __init__(
        self,
        provider_name: str = "gemini",
        model: str = "G_2_5_FLASH",
        workspace_path: str = None,
        session_id: str = None
    ):
        super().__init__(
            agent_type=AgentType.ORCHESTRATOR,
            provider_name=provider_name,
            model=model,
            workspace_path=workspace_path,
            session_id=session_id
        )
        self.active_agents: Dict[str, BaseAgent] = {}
        self.task_history: List[Dict[str, Any]] = []
        
    def get_system_prompt(self) -> str:
        return """You are the Orchestrator Agent for Flashy, a collaborative AI coding assistant.

Your role is to:
1. ANALYZE user requests and understand their intent
2. BREAK DOWN complex tasks into sub-tasks
3. IDENTIFY which specialized agent(s) should handle each sub-task
4. COORDINATE the workflow between agents
5. SYNTHESIZE results into clear, actionable summaries

Available Agents:
- ARCHITECT: System design, file structure planning, architecture decisions
- DEVELOPER: Code implementation, writing new features, bug fixes
- REVIEWER: Code review, security analysis, best practices
- RESEARCHER: Web search, documentation lookup, learning new APIs
- EXPLORER: Codebase navigation, understanding existing code
- LEARNER: Project memory, patterns, past decisions

When analyzing a request, respond with a JSON object:
{
    "understanding": "Brief summary of what the user wants",
    "complexity": "simple|moderate|complex",
    "primary_agent": "agent_type",
    "sub_tasks": [
        {"agent": "agent_type", "task": "specific task description", "priority": 1-5}
    ],
    "requires_exploration": true/false,
    "requires_research": true/false
}

For simple tasks, you may handle them directly without delegation.
Always prioritize user experience and provide clear progress updates."""
    
    async def analyze_request(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze a user request and create a task plan."""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Analyze this request and create a task plan:\n\n{user_input}"}
        ]
        
        if context:
            context_str = json.dumps(context, indent=2)
            messages[1]["content"] += f"\n\nContext:\n{context_str}"
        
        full_response = ""
        async for chunk in self.generate_stream(messages):
            if "text" in chunk:
                full_response += chunk["text"]
            elif "error" in chunk:
                return {"error": chunk["error"]}
        
        # Parse the JSON response
        try:
            # Find JSON in response
            start = full_response.find("{")
            end = full_response.rfind("}") + 1
            if start >= 0 and end > start:
                plan = json.loads(full_response[start:end])
                self.task_history.append({"input": user_input, "plan": plan})
                return plan
        except json.JSONDecodeError:
            pass
        
        # Fallback for non-JSON response
        return {
            "understanding": full_response[:200],
            "complexity": "simple",
            "primary_agent": "developer",
            "sub_tasks": [{"agent": "developer", "task": user_input, "priority": 1}],
            "requires_exploration": False,
            "requires_research": False
        }
    
    async def execute(
        self,
        task: str,
        context: Dict[str, Any] = None
    ) -> AgentResult:
        """Execute an orchestration task."""
        # Analyze the task
        plan = await self.analyze_request(task, context)
        
        if "error" in plan:
            return AgentResult(
                agent_type=self.agent_type,
                success=False,
                output="",
                summary=f"Error analyzing task: {plan['error']}"
            )
        
        # For now, return the plan - actual delegation will be implemented
        # when other agents are connected
        summary = f"Task analyzed. Complexity: {plan.get('complexity', 'unknown')}. "
        summary += f"Primary agent: {plan.get('primary_agent', 'developer')}. "
        
        sub_tasks = plan.get('sub_tasks', [])
        if sub_tasks:
            summary += f"Sub-tasks: {len(sub_tasks)}"
        
        return AgentResult(
            agent_type=self.agent_type,
            success=True,
            output=json.dumps(plan, indent=2),
            summary=summary,
            details=plan
        )
    
    async def delegate_to_agent(
        self,
        agent_type: AgentType,
        task: str,
        context: Dict[str, Any] = None
    ) -> AgentResult:
        """Delegate a task to a specific agent."""
        from .registry import agent_registry
        
        # Get or create agent
        agent_key = f"{agent_type.value}_{self.session_id}"
        if agent_key not in self.active_agents:
            agent = agent_registry.create_agent(
                agent_type,
                workspace_path=self.workspace_path,
                session_id=self.session_id
            )
            if agent:
                self.active_agents[agent_key] = agent
        
        agent = self.active_agents.get(agent_key)
        if not agent:
            return AgentResult(
                agent_type=agent_type,
                success=False,
                output="",
                summary=f"Agent {agent_type.value} not available"
            )
        
        # Send message and execute
        self.send_message(agent.agent_id, task, "task")
        result = await agent.execute(task, context)
        
        # Receive result message
        result_msg = AgentMessage(
            sender=agent.agent_id,
            recipient=self.agent_id,
            content=result.summary,
            message_type="result"
        )
        self.receive_message(result_msg)
        
        return result
    
    def get_active_agents_summary(self) -> str:
        """Get a summary of currently active agents."""
        if not self.active_agents:
            return "No agents currently active."
        
        summaries = []
        for key, agent in self.active_agents.items():
            summaries.append(agent.get_context_summary())
        
        return "\n".join(summaries)
