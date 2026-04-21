import json
import re
import uuid
import logging
from typing import List, Dict

logger = logging.getLogger("flashy.qwen.prompts")

TOOL_SYSTEM_PREFIX = (
    "You are a helpful AI coding assistant with access to tools.\n"
    "When you need to use a tool, you MUST respond with ONLY a single line in this exact format:\n\n"
    "««TOOL_CALL»» {\"name\": \"TOOL_NAME\", \"arguments\": {\"PARAM_NAME\": \"PARAM_VALUE\"}} ««/TOOL_CALL»»\n\n"
    "CRITICAL RULES:\n"
    "- Do NOT write any text before or after the tool call line.\n"
    "- Do NOT say 'Tool does not exist' or 'I cannot access tools'. All listed tools ARE available.\n"
    "- The JSON must have 'name' (exact tool name from the list) and 'arguments' (object with parameter values).\n"
    "- After receiving a <tool_result> block, call another tool or give your final answer as plain text.\n\n"
    "Available tools:\n"
)

TOOL_APPEND_SUFFIX = (
    "\n---\n"
    "Tool calling: when you need to use a tool, respond with ONLY a single line in this format:\n\n"
    "««TOOL_CALL»» {\"name\": \"TOOL_NAME\", \"arguments\": {\"PARAM_NAME\": \"PARAM_VALUE\"}} ««/TOOL_CALL»»\n\n"
    "IMPORTANT: All listed tools are available and functional. Do NOT say 'Tool does not exist'. "
    "Just emit the tool call directly.\n"
    "After receiving a <tool_result> block, call another tool or give your final answer.\n\n"
    "Available tools:\n"
)

TOOL_CALL_RE = re.compile(
    r"««TOOL_CALL»»\s*(\{.*?\})\s*««/TOOL_CALL»»",
    re.DOTALL,
)

TOOL_CALL_OPEN = "««TOOL_CALL»»"
TOOL_CALL_CLOSE = "««/TOOL_CALL»»"

QWEN_NATIVE_TOOLS = {
    "web_search", "code_interpreter", "image-generation", "amap", "fire-crawl", "file_reader",
}


def build_tool_system_prompt(tools: List[Dict], *, as_suffix: bool = False) -> str:
    base = TOOL_APPEND_SUFFIX if as_suffix else TOOL_SYSTEM_PREFIX
    lines = [base]
    for t in tools:
        fn = t.get("function", t)
        name = fn.get("name", "unknown")
        desc = fn.get("description", "")
        params = fn.get("parameters", {})
        lines.append(f"- **{name}**: {desc}")
        if params.get("properties"):
            for pname, pinfo in params["properties"].items():
                req = "required" if pname in params.get("required", []) else "optional"
                pdesc = pinfo.get("description", "")
                ptype = pinfo.get("type", "any")
                lines.append(f"  - {pname} ({ptype}, {req}): {pdesc}")
    lines.append("")
    return "\n".join(lines)


def inject_tools_into_messages(
    messages: List[Dict[str, str]],
    tools: List[Dict],
) -> List[Dict[str, str]]:
    if not tools:
        return messages

    out = list(messages)

    if out and out[0].get("role") == "system":
        tool_suffix = build_tool_system_prompt(tools, as_suffix=True)
        out[0] = {**out[0], "content": out[0]["content"] + tool_suffix}
    else:
        tool_prefix = build_tool_system_prompt(tools, as_suffix=False)
        out.insert(0, {"role": "system", "content": tool_prefix})

    return out


def parse_tool_calls_from_text(text: str):
    tool_calls = []
    clean = TOOL_CALL_RE.sub("", text)

    for m in TOOL_CALL_RE.finditer(text):
        json_str = m.group(1).strip()

        if json_str.startswith("```json"):
            json_str = json_str[7:]
        elif json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]

        json_str = json_str.strip()

        try:
            payload = json.loads(json_str)
            tc = {
                "id": f"call_{uuid.uuid4().hex[:8]}",
                "name": payload.get("name", ""),
                "arguments": json.dumps(payload.get("arguments", {})),
            }
            logger.info(f"[QWEN] Parsed tool call: name={tc['name']} args={tc['arguments'][:200]}")
            tool_calls.append(tc)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"[QWEN] Failed to parse tool call JSON: {e}\nRaw: {json_str[:500]}")
            clean += f"\n\n[System: Failed to parse tool call JSON: {e}]\n{json_str}"

    return clean.strip(), tool_calls