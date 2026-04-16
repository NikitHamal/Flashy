"""
Orchestrator Agent

The main coordinating agent that receives user requests, analyzes them,
and delegates to specialized agents with actual execution.
"""

from typing import Dict, Any, List, Optional
import json
import asyncio
import os

from .base import BaseAgent, AgentType, AgentMessage, AgentResult


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent - The team lead that coordinates all other agents.

    Responsibilities:
    - ANALYZE user requests and break them into sub-tasks
    - DELEGATE tasks to appropriate specialized agents
    - SYNTHESIZE results from multiple agents
    - PROVIDE unified summaries to users
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

        try:
            start = full_response.find("{")
            end = full_response.rfind("}") + 1
            if start >= 0 and end > start:
                plan = json.loads(full_response[start:end])
                self.task_history.append({"input": user_input, "plan": plan})
                return plan
        except json.JSONDecodeError:
            pass

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
        """Execute an orchestration task with actual delegation."""
        plan = await self.analyze_request(task, context)

        if "error" in plan:
            return AgentResult(
                agent_type=self.agent_type,
                success=False,
                output="",
                summary=f"Error analyzing task: {plan['error']}"
            )

        sub_tasks = plan.get('sub_tasks', [])
        results = []

        for sub_task in sorted(sub_tasks, key=lambda x: x.get('priority', 5)):
            agent_type_str = sub_task.get('agent', 'developer')
            task_desc = sub_task.get('task', task)

            try:
                agent_type = AgentType(agent_type_str)
            except ValueError:
                agent_type = AgentType.DEVELOPER

            result = await self.delegate_to_agent(agent_type, task_desc, context)
            results.append({
                "agent": agent_type.value,
                "task": task_desc,
                "success": result.success,
                "summary": result.summary,
                "artifacts": result.artifacts
            })

        summary = f"Task: {plan.get('understanding', '')}\n\n"
        summary += f"Complexity: {plan.get('complexity', 'unknown')}\n\n"
        summary += f"Results ({len(results)} sub-tasks):\n"
        for r in results:
            status = "\u2713" if r['success'] else "\u2717"
            summary += f"  {status} [{r['agent']}] {r['summary']}\n"
            if r['artifacts']:
                summary += f"    Artifacts: {', '.join(r['artifacts'])}\n"

        return AgentResult(
            agent_type=self.agent_type,
            success=True,
            output=json.dumps(results, indent=2),
            summary=summary,
            details={"plan": plan, "results": results},
            artifacts=[a for r in results for a in r.get('artifacts', [])]
        )

    async def delegate_to_agent(
        self,
        agent_type: AgentType,
        task: str,
        context: Dict[str, Any] = None
    ) -> AgentResult:
        """Delegate a task to a specific agent and get the result."""
        from .registry import agent_registry

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

        exec_context = context or {}

        if "file_tree" not in exec_context and self.workspace_path:
            try:
                tree_items = []
                for root, dirs, files in os.walk(self.workspace_path):
                    level = root.replace(self.workspace_path, '').count(os.sep)
                    if level > 2:
                        continue
                    indent = ' ' * 2 * level
                    tree_items.append(f'{indent}{os.path.basename(root)}/')
                    sub_indent = ' ' * 2 * (level + 1)
                    for f in files[:5]:
                        tree_items.append(f'{sub_indent}{f}')
                exec_context["file_tree"] = '\n'.join(tree_items[:50])
            except Exception:
                pass

        self.send_message(agent.agent_id, task, "task")
        result = await agent.execute(task, exec_context)

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
