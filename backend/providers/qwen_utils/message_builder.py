import json
import uuid
from typing import Dict, Any, List, Optional

from .prompts import inject_tools_into_messages, TOOL_CALL_OPEN, TOOL_CALL_CLOSE


class QwenConversation:
    __slots__ = ("chat_id", "parent_id")

    def __init__(self, chat_id: str, parent_id: Optional[str] = None):
        self.chat_id = chat_id
        self.parent_id = parent_id


def resolve_messages(
    messages: List[Dict[str, str]],
    tools: Optional[List[Dict]] = None,
    conversation: Optional[QwenConversation] = None,
) -> List[Dict[str, str]]:
    if tools:
        effective_messages = inject_tools_into_messages(messages, tools)
    else:
        effective_messages = messages

    if conversation and conversation.parent_id:
        source_messages = [m for m in effective_messages if m.get("role") == "user"][-1:]
        if not source_messages:
            source_messages = effective_messages[-1:]
    else:
        source_messages = effective_messages

    return source_messages


def build_prompt(source_messages: List[Dict[str, str]]) -> str:
    prompt_parts = []
    for msg in source_messages:
        role = msg.get("role", "user")
        raw_content = msg.get("content")

        if isinstance(raw_content, list):
            content = "\n".join(
                item.get("text", "")
                for item in raw_content
                if isinstance(item, dict) and item.get("type") == "text"
            )
        else:
            content = raw_content or ""

        if role == "system":
            prompt_parts.append(f"[System Instructions]\n{content}\n")
        elif role == "user":
            prompt_parts.append(content)
        elif role == "assistant":
            tool_calls = msg.get("tool_calls")
            if tool_calls:
                for tc in tool_calls:
                    fn = tc.get("function", {})
                    tc_name = fn.get("name", "unknown")
                    tc_args = fn.get("arguments", "{}")
                    tc_json = json.dumps({
                        "name": tc_name,
                        "arguments": json.loads(tc_args) if isinstance(tc_args, str) else tc_args,
                    })
                    prompt_parts.append(f"{TOOL_CALL_OPEN} {tc_json} {TOOL_CALL_CLOSE}")
            if content:
                prompt_parts.append(f"[Assistant]\n{content}")
        elif role == "tool":
            tool_name = msg.get("name", "") or msg.get("tool_call_id", "tool")
            prompt_parts.append(f'<tool_result name="{tool_name}">\n{content}\n</tool_result>')

    return "\n\n".join(p for p in prompt_parts if p)


def build_feature_config(
    thinking_enabled: bool,
    thinking_mode: str,
    chat_type: str,
) -> Dict[str, Any]:
    if thinking_enabled:
        return {
            "auto_thinking": thinking_mode == "Auto",
            "thinking_mode": thinking_mode,
            "thinking_enabled": True,
            "output_schema": "phase",
            "research_mode": "normal" if chat_type != "deep_research" else "deep",
            "auto_search": chat_type in ("search", "deep_research"),
        }
    return {
        "thinking_enabled": False,
        "output_schema": "phase",
        "thinking_budget": 81920,
    }


def build_msg_payload(
    chat_id: str,
    model: str,
    full_prompt: str,
    parent_id: Optional[str],
    uploaded_files: List[dict],
    chat_type: str,
    chat_mode: str,
    feature_config: Dict[str, Any],
) -> Dict[str, Any]:
    msg_id = str(uuid.uuid4())
    return {
        "stream": True,
        "incremental_output": True,
        "chat_id": chat_id,
        "chat_mode": chat_mode,
        "model": model,
        "parent_id": parent_id,
        "messages": [
            {
                "fid": msg_id,
                "parentId": parent_id,
                "childrenIds": [],
                "role": "user",
                "content": full_prompt,
                "user_action": "chat",
                "files": uploaded_files,
                "models": [model],
                "chat_type": chat_type,
                "feature_config": feature_config,
                "sub_chat_type": chat_type,
            }
        ],
    }


def resolve_chat_mode(chat_type: str) -> str:
    if chat_type == "search":
        return "search"
    if chat_type == "deep_research":
        return "deep_research"
    return "normal"