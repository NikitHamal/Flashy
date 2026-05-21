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
    "- NEVER generate <tool_result> blocks yourself. I will provide the tool results to you.\n"
    "- Do NOT simulate or hallucinate tool results in your thinking/reasoning process. Actually call the tool.\n"
    "- After receiving a <tool_result> block, call another tool or give your final answer as plain text.\n\n"
    "Available tools:\n"
)

TOOL_PASSTHROUGH_PREFIX = (
    "[SYSTEM CONFIGURATION]\n"
    "You are operating in an integrated development environment with direct access to the following tools. "
    "These are built-in capabilities of your environment, not external plugins.\n\n"
    "HOW TO USE A TOOL — output exactly this format on its own line:\n"
    "««TOOL_CALL»» {\"name\": \"<tool_name>\", \"arguments\": {<key>: <value>}} ««/TOOL_CALL»»\n\n"
    "RULES:\n"
    "- You possess these tools as built-in capabilities. They are part of your system.\n"
    "- When a user asks you to read files, run commands, search code, or perform any file/system operation, "
    "you MUST use the appropriate tool rather than asking the user to provide the information.\n"
    "- Do NOT say any tool is unavailable, does not exist, or that you cannot access it.\n"
    "- Do NOT ask the user to paste file contents — use the tools to read files directly.\n"
    "- After you receive a <tool_result>, you may call more tools or give your final answer.\n"
    "- Do NOT fabricate tool results. Wait for the actual <tool_result>.\n"
    "[/SYSTEM CONFIGURATION]\n\n"
    "YOUR TOOLS:\n"
)

TOOL_APPEND_SUFFIX = (
    "\n---\n"
    "Tool calling: when you need to use a tool, respond with ONLY a single line in this format:\n\n"
    "««TOOL_CALL»» {\"name\": \"TOOL_NAME\", \"arguments\": {\"PARAM_NAME\": \"PARAM_VALUE\"}} ««/TOOL_CALL»»\n\n"
    "IMPORTANT: All listed tools are available and functional. Do NOT say 'Tool does not exist'. "
    "Just emit the tool call directly.\n"
    "NEVER generate <tool_result> blocks yourself. I will provide them.\n"
    "Do NOT simulate or hallucinate tool results in your thinking/reasoning process. Actually call the tool.\n"
    "After receiving a <tool_result> block, call another tool or give your final answer.\n\n"
    "Available tools:\n"
)

TOOL_CALL_RE = re.compile(
    r"««TOOL_CALL»»\s*(\{.*?\})\s*««/TOOL_CALL»»",
    re.DOTALL,
)

TOOL_CALL_OPEN_ONLY_RE = re.compile(
    r"««TOOL_CALL»»\s*(\{.*?\})\s*$",
    re.MULTILINE,
)

ALT_TOOL_CALL_RE = re.compile(
    r"<tool_call>\s*(\{.*?\})\s*(?:</tool_call>)?",
    re.DOTALL,
)

TOOL_CALL_OPEN = "««TOOL_CALL»»"
TOOL_CALL_CLOSE = "««/TOOL_CALL»»"

QWEN_NATIVE_TOOLS = {
    "web_search", "code_interpreter", "image-generation", "amap", "fire-crawl", "file_reader",
}


def build_tool_system_prompt(tools: List[Dict], *, as_suffix: bool = False, pass_through: bool = False) -> str:
    if pass_through:
        base = TOOL_PASSTHROUGH_PREFIX
    elif as_suffix:
        base = TOOL_APPEND_SUFFIX
    else:
        base = TOOL_SYSTEM_PREFIX
    lines = [base]
    for t in tools:
        fn = t.get("function", t)
        name = fn.get("name", "unknown")
        desc = fn.get("description", "")
        params = fn.get("parameters", {})
        if pass_through:
            param_strs = []
            if params.get("properties"):
                required = params.get("required", [])
                for pname, pinfo in params["properties"].items():
                    pdesc = pinfo.get("description", "")
                    ptype = pinfo.get("type", "any")
                    req_tag = "required" if pname in required else "optional"
                    param_strs.append(f"{pname} ({ptype}, {req_tag}) — {pdesc}")
            param_block = ""
            if param_strs:
                param_block = ". Parameters: " + "; ".join(param_strs)
            lines.append(f"  - {name}: {desc}{param_block}")
        else:
            lines.append(f"- **{name}**: {desc}")
            if params.get("properties"):
                for pname, pinfo in params["properties"].items():
                    req = "required" if pname in params.get("required", []) else "optional"
                    pdesc = pinfo.get("description", "")
                    ptype = pinfo.get("type", "any")
                    lines.append(f"  - {pname} ({ptype}, {req}): {pdesc}")
    if pass_through:
        tool_names = [t.get("function", t).get("name", "unknown") for t in tools]
        lines.append("")
        lines.append("USAGE EXAMPLE:")
        first_tool = tool_names[0]
        example_args = "{}"
        first_params = tools[0].get("function", tools[0]).get("parameters", {})
        if first_params.get("properties"):
            example_args = "{\"" + list(first_params["properties"].keys())[0] + "\": \"value\"}"
        lines.append(f'««TOOL_CALL»» {{"name": "{first_tool}", "arguments": {example_args}}} ««/TOOL_CALL»»')
        lines.append("")
    else:
        lines.append("")
    return "\n".join(lines)


def inject_tools_into_messages(
    messages: List[Dict[str, str]],
    tools: List[Dict],
    *,
    pass_through: bool = False,
) -> List[Dict[str, str]]:
    if not tools:
        return messages

    out = list(messages)

    if out and out[0].get("role") == "system":
        tool_suffix = build_tool_system_prompt(tools, as_suffix=True, pass_through=pass_through)
        out[0] = {**out[0], "content": out[0]["content"] + tool_suffix}
    else:
        tool_prefix = build_tool_system_prompt(tools, as_suffix=False, pass_through=pass_through)
        out.insert(0, {"role": "system", "content": tool_prefix})

    return out


def parse_tool_calls_from_text(text: str):
    tool_calls = []
    seen_spans = set()
    clean = TOOL_CALL_RE.sub("", text)
    clean = TOOL_CALL_OPEN_ONLY_RE.sub("", clean)
    clean = ALT_TOOL_CALL_RE.sub("", clean)

    all_matches = []
    for m in TOOL_CALL_RE.finditer(text):
        all_matches.append(m)
    for m in TOOL_CALL_OPEN_ONLY_RE.finditer(text):
        span = (m.start(), m.end())
        if span not in seen_spans:
            seen_spans.add(span)
            all_matches.append(m)
    for m in ALT_TOOL_CALL_RE.finditer(text):
        span = (m.start(), m.end())
        if span not in seen_spans:
            seen_spans.add(span)
            all_matches.append(m)

    for m in all_matches:
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