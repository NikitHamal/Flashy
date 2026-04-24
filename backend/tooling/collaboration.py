import os
import subprocess
import glob
import tempfile
import shutil
import json
import asyncio
from typing import Optional, List, Dict, Any

from ..git_manager import GitManager
from ..websocket_manager import ws_manager

class CollaborationMixin:
    def save_memory(self, category: str, title: str, content: str) -> str:
        """Save a persistent memory (project rules, user preferences, API keys, etc.) across sessions.
        
        Args:
            category: e.g., 'preference', 'architecture', 'gotcha'
            title: Brief summary of the memory
            content: The detailed information to remember
        """
        memory_dir = os.path.join(self.workspace_path, ".flashy")
        memory_file = os.path.join(memory_dir, "memory.json")
        
        try:
            os.makedirs(memory_dir, exist_ok=True)
            memories = []
            if os.path.exists(memory_file):
                with open(memory_file, 'r', encoding='utf-8') as f:
                    memories = json.load(f)
                    
            memories.append({
                "id": f"mem_{os.urandom(4).hex()}",
                "category": category,
                "title": title,
                "content": content,
                "timestamp": __import__('time').time()
            })
            
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(memories, f, indent=2)
                
            return f"Memory '{title}' saved successfully. It will be available in future sessions."
        except Exception as e:
            return f"Error saving memory: {str(e)}"

    def todo_write(self, content: str) -> str:
        """Write to the agent's scratchpad/plan (rendered in the UI's 'Current Plan' sidebar)."""
        plan_dir = os.path.join(self.workspace_path, ".flashy")
        plan_file = os.path.join(plan_dir, "plan.md")
        
        try:
            os.makedirs(plan_dir, exist_ok=True)
            with open(plan_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return "Plan updated successfully. The UI sidebar will reflect these changes."
        except Exception as e:
            return f"Error updating plan: {str(e)}"

    async def spawn_subagent(self, agent_type: str, task: str) -> str:
        """Spawn a specialized sub-agent with specific instructions."""
        try:
            from .agents.base import AgentType
            from .agents import get_agent
            
            # Map string to enum
            try:
                a_type = AgentType(agent_type.lower())
            except ValueError:
                return f"Error: Invalid agent_type '{agent_type}'. Must be one of: {[e.value for e in AgentType]}"
            
            # Use a temporary session ID for the subagent so it doesn't pollute the main chat
            sub_session_id = f"sub_{os.urandom(4).hex()}"
            subagent = get_agent(a_type, workspace_path=self.workspace_path, session_id=sub_session_id)
            
            if not subagent:
                return f"Error: Failed to initialize subagent of type '{agent_type}'"
            
            # Notify UI that a subagent started
            if self.session_id:
                try:
                    from .websocket_manager import MessageType
                    await ws_manager.send_to_session(
                        self.session_id,
                        MessageType.TEXT,
                        f"*[System] Spawning {agent_type} sub-agent for: {task[:50]}...*\n"
                    )
                except Exception:
                    pass
            
            # Execute task
            result = await subagent.execute(task)
            
            # Format result
            status = "Success" if result.success else "Failed"
            output = f"Sub-agent '{agent_type}' completed with status: {status}\n\n"
            output += f"Summary:\n{result.summary}\n\n"
            if result.artifacts:
                output += f"Modified/Created Files:\n" + "\n".join(f"- {f}" for f in result.artifacts)
                
            return output
            
        except Exception as e:
            return f"Error spawning subagent: {str(e)}"

    def activate_skill(self, skill_name: str) -> str:
        """Load a specific file-based skill (SKILL.md)."""
        # Look for skills in .flashy/skills/ or global ~/.flashy/skills/
        workspace_skills = os.path.join(self.workspace_path, ".flashy", "skills", skill_name, "SKILL.md")
        global_skills = os.path.expanduser(f"~/.flashy/skills/{skill_name}/SKILL.md")
        
        target_file = None
        if os.path.exists(workspace_skills):
            target_file = workspace_skills
        elif os.path.exists(global_skills):
            target_file = global_skills
            
        if not target_file:
            return f"Error: Skill '{skill_name}' not found. Ensure the skill is installed in .flashy/skills/{skill_name}/SKILL.md"
            
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                skill_content = f.read()
                
            return f"""<activated_skill name="{skill_name}">
{skill_content}
</activated_skill>

You MUST strictly follow the instructions in the <activated_skill> block above for the remainder of this task."""
        except Exception as e:
            return f"Error loading skill '{skill_name}': {str(e)}"

    async def ask_user_question(self, question: str) -> str:
        """Pause execution to ask the user a question and wait for their response."""
        if not self.session_id:
            return "Error: Cannot ask user a question outside of an active session."
        
        question_id = f"q_{os.urandom(4).hex()}"
        future = asyncio.get_event_loop().create_future()
        ws_manager.pending_questions[question_id] = future
        
        try:
            from .websocket_manager import MessageType
            await ws_manager.send_to_session(
                self.session_id,
                MessageType.ASK_USER_QUESTION,
                {"question_id": question_id, "question": question}
            )
            # Wait for response (no timeout, wait indefinitely)
            response = await future
            return f"User replied: {response}"
        except Exception as e:
            return f"Error asking user question: {str(e)}"
        finally:
            if question_id in ws_manager.pending_questions:
                del ws_manager.pending_questions[question_id]

    def self_check(self) -> Dict[str, Any]:
        """Run a global self-check across tools and environment."""
        result: Dict[str, Any] = {
            "workspace": {
                "path": self.workspace_path,
                "exists": os.path.isdir(self.workspace_path),
                "readable": False,
                "writable": False,
            },
            "git": {},
            "commands": {},
            "web": {"requests_html": False},
            "warnings": [],
            "errors": [],
        }

        # Workspace readability/writability
        if result["workspace"]["exists"]:
            try:
                test_file = os.path.join(self.workspace_path, ".flashy_write_test.tmp")
                with open(test_file, "w", encoding="utf-8") as f:
                    f.write("ok")
                result["workspace"]["writable"] = True
                with open(test_file, "r", encoding="utf-8") as f:
                    _ = f.read()
                result["workspace"]["readable"] = True
                os.remove(test_file)
            except Exception as e:
                result["errors"].append(f"Workspace read/write check failed: {e}")
        else:
            result["errors"].append("Workspace path does not exist or is not a directory.")

        # Command availability
        for cmd in ["git", "python"]:
            result["commands"][cmd] = bool(shutil.which(cmd))
            if not result["commands"][cmd]:
                result["warnings"].append(f"Command not found in PATH: {cmd}")

        # Git health
        try:
            from .config import load_config
            pat = load_config().get("GITHUB_PAT")
            result["git"] = self.git.get_health(pat=pat)
        except Exception as e:
            result["warnings"].append(f"Git health check failed: {e}")
            result["git"] = {"is_repo": False}

        # Web search dependency
        try:
            import requests_html  # noqa: F401
            result["web"]["requests_html"] = True
        except Exception:
            result["warnings"].append("requests_html not available; web_search may fail.")

        return result
