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
) -> tuple:
    """Returns (tool_system_prompt: str | None, source_messages: List[Dict])"""
    # Always inject tools into messages first so tool definitions are available
    if tools:
        effective_messages = inject_tools_into_messages(messages, tools)
        # Extract the tool system prompt so we can always prepend it
        if effective_messages and effective_messages[0].get("role") == "system":
            tool_system_prompt = effective_messages[0]["content"]
        else:
            tool_system_prompt = None
    else:
        effective_messages = messages
        tool_system_prompt = None

    if conversation and conversation.parent_id:
        last_assistant_idx = -1
        for i in range(len(effective_messages) - 1, -1, -1):
            if effective_messages[i].get("role") == "assistant":
                last_assistant_idx = i
                break

        if last_assistant_idx != -1 and last_assistant_idx < len(effective_messages) - 1:
            source_messages = effective_messages[last_assistant_idx + 1:]
        else:
            source_messages = [m for m in effective_messages if m.get("role") == "user"][-1:]
            if not source_messages:
                source_messages = effective_messages[-1:]
    else:
        source_messages = effective_messages

    return tool_system_prompt, source_messages


def build_prompt(tool_system_prompt: Optional[str], source_messages: List[Dict[str, str]]) -> str:
    prompt_parts = []

    # Always prepend tool system instructions when tools are present,
    # even if they were sliced out due to conversation resume logic
    if tool_system_prompt:
        # Avoid doubling up if the system message is already the first source message
        first_role = source_messages[0].get("role") if source_messages else None
        first_content = source_messages[0].get("content") if source_messages else ""
        if first_role != "system" or first_content != tool_system_prompt:
            prompt_parts.append(tool_system_prompt)

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
            # Only append system if not already added as tool_system_prompt above
            if content != tool_system_prompt:
                prompt_parts.append(content)
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
                prompt_parts.append(content)
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
            "research_mode": "normal" if chat_type != "deep_research" else "deep",
            "auto_search": chat_type in ("search", "deep_research"),
        }
    return {
        "thinking_enabled": False,
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
                # Disable safety/recitation filters
                "safety": {
                    "enabled": False,
                },
                "extra": {
                    "disable_recitation_policy": True,
                    "skip_safety_check": True,
                },
            }
        ],
    }


def resolve_chat_mode(chat_type: str) -> str:
    if chat_type == "search":
        return "search"
    if chat_type == "deep_research":
        return "deep_research"
    return "normal"