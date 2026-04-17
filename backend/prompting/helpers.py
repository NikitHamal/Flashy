from typing import Any, Dict, List

from .schemas import TOOL_SCHEMAS
from .templates import CODING_SYSTEM_PROMPT, CODING_TOOL_RESULT_TEMPLATE, ERROR_RECOVERY_GUIDANCE


def get_system_prompt(workspace_path: str, workspace_context: str = "") -> str:
    context_section = f"\n{workspace_context}" if workspace_context else ""
    return CODING_SYSTEM_PROMPT.format(
        workspace_path=workspace_path or "[Not Set]",
        workspace_context=context_section,
    )


def get_tool_result_template(tool_name: str, output: str, success: bool = True) -> str:
    status = "SUCCESS" if success else "ERROR"
    return CODING_TOOL_RESULT_TEMPLATE.format(
        tool_name=tool_name,
        status=status,
        output=output,
    )


def get_tool_schema(tool_name: str) -> Dict[str, Any]:
    return TOOL_SCHEMAS.get(tool_name)


def get_all_tool_schemas() -> Dict[str, Dict[str, Any]]:
    return TOOL_SCHEMAS


def format_tool_help(tool_name: str) -> str:
    schema = TOOL_SCHEMAS.get(tool_name)
    if not schema:
        return f"Unknown tool: {tool_name}"

    lines = [f"## {schema['name']}", schema['description'], "", "### Parameters:"]
    params = schema.get("parameters", {})
    if params:
        for name, info in params.items():
            required = "required" if info.get("required") else "optional"
            default = f", default: {info.get('default')}" if 'default' in info else ""
            lines.append(f"- `{name}` ({info['type']}, {required}{default}): {info['description']}")
    else:
        lines.append("- None")

    lines.extend([
        "",
        f"### Returns: {schema.get('returns', 'Result of operation')}",
        "",
        "### Example:",
        "```json",
        schema.get("example", "{}"),
        "```",
    ])

    if schema.get("best_practices"):
        lines.extend(["", "### Best Practices:"])
        for practice in schema["best_practices"]:
            lines.append(f"- {practice}")

    return "\n".join(lines)


def get_error_recovery_hint(error_message: str) -> str:
    import re

    error_lower = error_message.lower()
    for info in ERROR_RECOVERY_GUIDANCE.values():
        if re.search(info["pattern"], error_lower, re.IGNORECASE):
            return f"Recovery hint: {info['recovery']}"
    return "Analyze the error message and try a different approach."


def build_workspace_context(file_tree: str = "", recent_files: List[str] = None) -> str:
    parts = []
    if file_tree:
        parts.append(f"### Project Structure\n```\n{file_tree}\n```")
    if recent_files:
        parts.append("### Recently Modified Files\n" + "\n".join(f"- {item}" for item in recent_files[:10]))
    return "\n\n".join(parts) if parts else ""
