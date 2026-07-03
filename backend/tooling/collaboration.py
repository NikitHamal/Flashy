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
        """Spawn a sub-agent with its own model/provider and system prompt.

        Uses subagent definitions from .flashy/agents/ or built-in types
        (general, explore, researcher, developer) to configure the
        sub-agent's model, provider, and role instructions.
        """
        try:
            from ..agents.subagent_defs import (get_subagent_def,
                                                list_subagent_types,
                                                load_custom_defs)

            load_custom_defs(self.workspace_path)

            sub_def = get_subagent_def(agent_type)
            if not sub_def:
                types = list_subagent_types()
                return (f"Error: Unknown subagent type '{agent_type}'. "
                        f"Available: {', '.join(sorted(types))}")

            from ..coding_agent import CodingAgent
            from ..providers import get_provider_service
            from ..config import load_config

            sub_agent = CodingAgent(
                workspace_path=self.workspace_path,
                session_id=f"sub_{os.urandom(4).hex()}",
            )

            if sub_def.provider:
                sub_agent.provider_name = sub_def.provider
            if sub_def.model:
                sub_agent.model = sub_def.model

            config = load_config()
            provider_name = sub_agent.provider_name or config.get("active_provider", "g4f")
            model_name = sub_agent.model or config.get("model", "")

            system = sub_agent.get_system_prompt()
            full_prompt = (
                f"{system}\n\n"
                f"## Role\n\n{sub_def.system_prompt}\n\n"
                f"## Task from parent agent\n\n{task}\n\n"
                "Complete this task. When done, output your final answer without a tool call."
            )

            provider_svc = get_provider_service(provider_name)
            if not provider_svc:
                return f"Error: Provider '{provider_name}' not found for subagent."

            messages = [{"role": "user", "content": full_prompt}]

            response_text = ""
            for iteration in range(15):
                accumulated = ""
                async for chunk in provider_svc.generate_stream(
                    messages,
                    model_name,
                    proxy=config.get("proxy"),
                ):
                    if "text" in chunk:
                        accumulated += chunk["text"]
                    if "error" in chunk:
                        return f"Sub-agent error: {chunk['error']}"

                response_text = accumulated

                tool_call = sub_agent.parse_tool_call(response_text)
                if not tool_call:
                    break

                # Skip tools the subagent type disallows
                if sub_def.tools.deny and tool_call["name"] in sub_def.tools.deny:
                    err = f"Tool '{tool_call['name']}' is not allowed for '{agent_type}' subagent"
                    messages.append({"role": "assistant", "content": response_text})
                    messages.append({"role": "tool", "content": err})
                    continue

                tool_result, _ = await sub_agent.execute_tool(
                    tool_call["name"], tool_call["args"]
                )
                messages = [
                    {"role": "user", "content": full_prompt},
                    {"role": "assistant", "content": response_text},
                    {"role": "tool", "content": tool_result},
                ]

            return (f"**Sub-agent ({agent_type}) result:**\n\n"
                    f"{response_text}")

        except Exception as e:
            return f"Error spawning subagent '{agent_type}': {str(e)}"

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
            from ..websocket_manager import MessageType
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
            from ..config import load_config
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
