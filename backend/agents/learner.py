"""
Learner Agent

Learns from project interactions and maintains the project memorybase.
"""

from typing import Dict, Any, List
import json
import os
from datetime import datetime

from .base import BaseAgent, AgentType, AgentResult


class LearnerAgent(BaseAgent):
    """
    The Learner Agent - Maintains project memory and learnings.
    
    Responsibilities:
    - Observe all agent interactions
    - Extract key learnings and patterns
    - Maintain project memorybase
    - Provide context from past sessions
    """
    
    def __init__(
        self,
        provider_name: str = "g4f",
        model: str = "qwen3-235b-a22b",
        workspace_path: str = None,
        session_id: str = None
    ):
        super().__init__(
            agent_type=AgentType.LEARNER,
            provider_name=provider_name,
            model=model,
            workspace_path=workspace_path,
            session_id=session_id
        )
        self.memorybase_path = self._get_memorybase_path()
        self.memories: List[Dict[str, Any]] = self._load_memories()
        
    def _get_memorybase_path(self) -> str:
        """Get path to project memorybase file."""
        if self.workspace_path:
            return os.path.join(self.workspace_path, ".flashy", "memorybase.json")
        return "memorybase.json"
    
    def _load_memories(self) -> List[Dict[str, Any]]:
        """Load existing memories from file."""
        if os.path.exists(self.memorybase_path):
            try:
                with open(self.memorybase_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def _save_memories(self):
        """Save memories to file."""
        os.makedirs(os.path.dirname(self.memorybase_path), exist_ok=True)
        with open(self.memorybase_path, 'w') as f:
            json.dump(self.memories, f, indent=2)
        
    def get_system_prompt(self) -> str:
        return """You are The Learner Agent for Flashy, a collaborative AI coding assistant.

Your role is to learn from project interactions and maintain a knowledge base.

When observing interactions, you should:
1. IDENTIFY key decisions and their rationale
2. EXTRACT patterns and conventions used
3. NOTE important considerations and gotchas
4. REMEMBER user preferences and project specifics
5. STORE learnings for future reference

For each learning, output in this format:
{
    "learnings": [
        {
            "category": "architecture|pattern|preference|decision|gotcha|convention",
            "title": "Brief title",
            "content": "What was learned",
            "importance": 1-5,
            "context": "When this applies"
        }
    ],
    "summary": "Brief summary of what was learned"
}

Focus on information that will be useful in future sessions."""
    
    async def execute(
        self,
        task: str,
        context: Dict[str, Any] = None
    ) -> AgentResult:
        """Extract learnings from an interaction."""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Extract learnings from:\n\n{task}"}
        ]
        
        if context:
            if "interaction_history" in context:
                messages[1]["content"] += f"\n\nInteraction history:\n{json.dumps(context['interaction_history'], indent=2)}"
        
        # Include existing memories for context
        if self.memories:
            recent = self.memories[-10:]  # Last 10 memories
            messages[1]["content"] += f"\n\nExisting memories (for context):\n{json.dumps(recent, indent=2)}"
        
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
        
        # Try to parse and store learnings
        new_learnings = []
        try:
            start = full_response.find("{")
            end = full_response.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(full_response[start:end])
                learnings = result.get("learnings", [])
                
                for learning in learnings:
                    memory = {
                        "id": f"mem_{len(self.memories) + 1}",
                        "timestamp": datetime.now().isoformat(),
                        "session_id": self.session_id,
                        **learning
                    }
                    self.memories.append(memory)
                    new_learnings.append(memory)
                
                if new_learnings:
                    self._save_memories()
                
                summary = f"Extracted {len(new_learnings)} new learning(s)"
                return AgentResult(
                    agent_type=self.agent_type,
                    success=True,
                    output=full_response,
                    summary=summary,
                    details={"new_learnings": new_learnings}
                )
        except json.JSONDecodeError:
            pass
        
        return AgentResult(
            agent_type=self.agent_type,
            success=True,
            output=full_response,
            summary="Learning extraction completed",
            details={"raw_response": full_response, "thoughts": thoughts}
        )
    
    def get_relevant_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get memories relevant to a query. Simple keyword matching for now."""
        query_lower = query.lower()
        scored = []
        
        for memory in self.memories:
            score = 0
            content = (memory.get("title", "") + " " + memory.get("content", "")).lower()
            for word in query_lower.split():
                if word in content:
                    score += 1
            if score > 0:
                scored.append((score, memory))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:limit]]
    
    def add_memory(self, category: str, title: str, content: str, importance: int = 3) -> Dict[str, Any]:
        """Manually add a memory."""
        memory = {
            "id": f"mem_{len(self.memories) + 1}",
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "category": category,
            "title": title,
            "content": content,
            "importance": importance,
            "source": "user"
        }
        self.memories.append(memory)
        self._save_memories()
        return memory
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        for i, m in enumerate(self.memories):
            if m.get("id") == memory_id:
                self.memories.pop(i)
                self._save_memories()
                return True
        return False
    
    def get_all_memories(self) -> List[Dict[str, Any]]:
        """Get all memories."""
        return self.memories
