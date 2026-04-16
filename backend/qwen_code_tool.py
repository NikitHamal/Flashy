"""
Qwen Code Tool - Integrates qwen-code CLI as a sub-agent for flashy.
Allows flashy to invoke qwen-code for coding tasks with FREE providers.
"""

import asyncio
import json
import subprocess
import os
from typing import Optional
from pathlib import Path

class QwenCodeTool:
    """Tool for invoking qwen-code as a sub-agent."""
    
    def __init__(self):
        self.bridge_port = 8787
        self.bridge_process: Optional[subprocess.Popen] = None
    
    async def start_bridge(self) -> bool:
        """Start the free providers bridge server."""
        bridge_path = Path(__file__).parent.parent / "qwen-code-free-providers" / "bridge_server.py"
        
        if not bridge_path.exists():
            return False
        
        env = os.environ.copy()
        env["QWEN_BRIDGE_PORT"] = str(self.bridge_port)
        
        try:
            self.bridge_process = subprocess.Popen(
                ["python3", str(bridge_path)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            # Wait a moment for server to start
            await asyncio.sleep(3)
            return self.bridge_process.poll() is None
        except Exception as e:
            print(f"Error starting bridge: {e}")
            return False
    
    def stop_bridge(self):
        """Stop the bridge server."""
        if self.bridge_process:
            self.bridge_process.terminate()
            self.bridge_process = None
    
    async def run_qwen_code(
        self,
        prompt: str,
        working_dir: str,
        model: str = "qwen3.6-plus",
        stream: bool = True
    ) -> str:
        """
        Run qwen-code with a prompt.
        
        Args:
            prompt: The prompt/question for qwen-code
            working_dir: Directory to run in
            model: Model to use (qwen3.6-plus, qwen3.5-plus, etc.)
            stream: Whether to stream output
        
        Returns:
            The response from qwen-code
        """
        # Ensure bridge is running
        if not self.bridge_process or self.bridge_process.poll() is not None:
            success = await self.start_bridge()
            if not success:
                return "Error: Could not start free providers bridge server"
        
        # Configure environment for qwen-code
        env = os.environ.copy()
        env["QWEN_BRIDGE_PORT"] = str(self.bridge_port)
        
        # Build the command
        cmd = [
            "qwen",
            "-p", prompt
        ]
        
        # Add model flag if specified
        if model:
            cmd.extend(["--model", model])
        
        try:
            # Run qwen-code
            result = subprocess.run(
                cmd,
                cwd=working_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return "Error: qwen-code timed out after 5 minutes"
        except Exception as e:
            return f"Error running qwen-code: {e}"
    
    async def interactive_session(self, working_dir: str):
        """
        Start an interactive qwen-code session.
        This is useful for complex multi-turn coding tasks.
        """
        if not self.bridge_process or self.bridge_process.poll() is not None:
            success = await self.start_bridge()
            if not success:
                print("Error: Could not start free providers bridge server")
                return
        
        env = os.environ.copy()
        env["QWEN_BRIDGE_PORT"] = str(self.bridge_port)
        
        # Start qwen in the working directory
        subprocess.run(
            ["qwen"],
            cwd=working_dir,
            env=env
        )


# Singleton instance
_qwen_code_tool: Optional[QwenCodeTool] = None


def get_qwen_code_tool() -> QwenCodeTool:
    """Get the singleton qwen-code tool instance."""
    global _qwen_code_tool
    if _qwen_code_tool is None:
        _qwen_code_tool = QwenCodeTool()
    return _qwen_code_tool


async def qwen_code_tool(
    prompt: str,
    working_dir: str = ".",
    model: str = "qwen3.6-plus",
    stream_output: bool = True
) -> str:
    """
    Use qwen-code CLI agent for coding tasks with FREE AI models.
    
    This tool invokes qwen-code, an autonomous coding agent that can:
    - Analyze codebases
    - Generate code
    - Refactor files
    - Run tests
    - Fix bugs
    
    Models available (all FREE):
    - qwen3.6-plus: Latest Qwen 3.6 model
    - qwen3.5-plus: Qwen 3.5 with thinking
    - qwen3.5-flash: Fast Qwen 3.5
    - qwen3-coder-plus: Code-optimized
    - meta-llama/Meta-Llama-3-8B-Instruct: Llama 3 8B
    - meta-llama/Meta-Llama-3-70B-Instruct: Llama 3 70B
    - mistralai/Mistral-7B-Instruct-v0.3: Mistral 7B
    
    Args:
        prompt: The task or question for qwen-code
        working_dir: Directory to work in (default: current)
        model: Model to use (default: qwen3.6-plus)
        stream_output: Whether to stream output
    
    Returns:
        Response from qwen-code
    
    Example:
        result = await qwen_code_tool(
            "Refactor this function to use async/await",
            working_dir="/path/to/project",
            model="qwen3.6-plus"
        )
    """
    tool = get_qwen_code_tool()
    return await tool.run_qwen_code(prompt, working_dir, model, stream_output)


async def qwen_code_setup() -> str:
    """
    Setup qwen-code with free providers.
    
    This configures qwen-code to use the free providers bridge server,
    enabling access to Qwen and DeepInfra models without API keys.
    
    Returns:
        Setup status message
    """
    try:
        setup_script = Path(__file__).parent.parent / "qwen-code-free-providers" / "qwen-free"
        
        if not setup_script.exists():
            return f"Error: Setup script not found at {setup_script}"
        
        result = subprocess.run(
            [str(setup_script), "setup"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error setting up qwen-code: {e}"


# Tool definition for agent tool registry
TOOL_DEFINITION = {
    "name": "qwen_code",
    "description": """Use qwen-code autonomous coding agent for coding tasks.

This tool invokes qwen-code CLI with FREE AI models (no API keys needed).
Available models: qwen3.6-plus, qwen3.5-plus, qwen3.5-flash, 
qwen3-coder-plus, Llama 3 8B/70B, Mistral 7B.

Use this when you need to:
- Analyze or understand codebases
- Generate new code
- Refactor existing code
- Run tests or debug issues
- Work with multiple files

The tool starts a bridge server automatically for free API access.
""",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The task or question for qwen-code"
            },
            "working_dir": {
                "type": "string",
                "description": "Directory to work in (default: current)",
                "default": "."
            },
            "model": {
                "type": "string",
                "description": "Model to use (default: qwen3.6-plus)",
                "default": "qwen3.6-plus",
                "enum": [
                    "qwen3.6-plus",
                    "qwen3.5-plus",
                    "qwen3.5-flash",
                    "qwen3-coder-plus",
                    "meta-llama/Meta-Llama-3-8B-Instruct",
                    "meta-llama/Meta-Llama-3-70B-Instruct",
                    "mistralai/Mistral-7B-Instruct-v0.3"
                ]
            }
        },
        "required": ["prompt"]
    }
}
