import re
from typing import Any


def clean_response_text(service, text: str, tool_call_raw: str = None) -> str:
    if not text:
        return ""

    cleaned = text
    if tool_call_raw:
        cleaned = cleaned.replace(tool_call_raw, "").strip()

    json_block_pattern = r'```json\s*\{[^`]*?"(?:action|tool|name)"\s*:[^`]*?\}\s*```'
    cleaned = re.sub(json_block_pattern, "", cleaned, flags=re.DOTALL).strip()

    incomplete_pattern = r'```json\s*\{[^`]*$'
    cleaned = re.sub(incomplete_pattern, "", cleaned, flags=re.DOTALL).strip()

    standalone_pattern = r'(?<![`\w])\{\s*"(?:action|tool)"\s*:\s*"[^"]+"\s*,\s*"args"\s*:\s*\{[^}]*\}\s*\}(?![`\w])'
    cleaned = re.sub(standalone_pattern, "", cleaned).strip()

    return service.response_filter.filter(cleaned)


def separate_thinking(service, text: str) -> tuple:
    if not text:
        return None, ""
    return service.thought_filter.extract_thoughts(text)
