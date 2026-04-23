import json
import uuid
import logging
from typing import Dict, Any, List, Optional

from ..response_types import (
    Reasoning, FinishReason, ToolCall,
    reasoning_to_dict, finish_reason_to_dict, tool_call_to_dict,
)
from .prompts import parse_tool_calls_from_text, QWEN_NATIVE_TOOLS

logger = logging.getLogger("flashy.qwen.stream")


class StreamState:
    __slots__ = (
        "buffer", "full_answer_text", "has_yielded_content",
        "current_fc_function_name", "current_fc_arguments", "current_fc_id",
        "saw_native_fc", "seen_function_call_deltas", "function_call_yielded",
        "pending_parent_id", "has_any_content",
    )

    def __init__(self):
        self.buffer = ""
        self.full_answer_text = ""
        self.has_yielded_content = False
        self.current_fc_function_name = ""
        self.current_fc_arguments = ""
        self.current_fc_id = ""
        self.saw_native_fc = False
        self.seen_function_call_deltas = False
        self.function_call_yielded = False
        self.pending_parent_id = None
        self.has_any_content = False


def _is_native_tool(name: str) -> bool:
    return name in QWEN_NATIVE_TOOLS


def _handle_native_function_call(
    delta: Dict[str, Any],
    state: StreamState,
) -> Optional[Dict[str, Any]]:
    function_call = delta.get("function_call")
    function_id = delta.get("function_id")
    fc_name_delta = delta.get("name")
    extra = delta.get("extra")

    if function_call:
        fc_name = function_call.get("name", "")
        fc_args = function_call.get("arguments", "")

        if _is_native_tool(fc_name):
            state.saw_native_fc = True
            logger.debug(f"[QWEN] Suppressing native tool call: {fc_name}")
            return

        logger.debug(f"[QWEN] Non-native function_call: name={fc_name} args_len={len(fc_args)}")
        state.seen_function_call_deltas = True
        if fc_name:
            state.current_fc_function_name = fc_name
        if fc_args:
            state.current_fc_arguments = fc_args
        if function_id:
            state.current_fc_id = function_id

    if fc_name_delta and function_id:
        if _is_native_tool(fc_name_delta):
            state.saw_native_fc = True
            logger.debug(f"[QWEN] Suppressing native tool call delta: {fc_name_delta}")
            return

        state.current_fc_id = function_id

    if fc_name_delta and function_id and extra:
        if state.current_fc_function_name and state.current_fc_arguments:
            final_args = state.current_fc_arguments
            try:
                json.loads(final_args)
            except json.JSONDecodeError:
                final_args = "{}"

            tool_call_data = {
                "id": state.current_fc_id or f"call_{uuid.uuid4().hex[:8]}",
                "name": state.current_fc_function_name,
                "arguments": final_args,
            }
            state.current_fc_function_name = ""
            state.current_fc_arguments = ""
            state.current_fc_id = ""
            state.function_call_yielded = True
            return {"tool_call": tool_call_data}

    return None


def _handle_content(
    content: str,
    phase: Optional[str],
    state: StreamState,
    has_tools: bool,
) -> Optional[Dict[str, Any]]:
    if not content:
        return None

    if phase == "think" or phase == "web_search":
        logger.debug(f"[QWEN] Reasoning phase={phase} len={len(content)}")
        state.has_any_content = True
        return reasoning_to_dict(Reasoning(content))

    state.full_answer_text += content
    state.has_any_content = True

    if has_tools:
        return None

    state.has_yielded_content = True
    return {"text": content}


def _handle_finish_reason(
    finish_reason: Optional[str],
    state: StreamState,
    has_tools: bool,
) -> Optional[List[Dict[str, Any]]]:
    if not finish_reason:
        return None

    events: List[Dict[str, Any]] = []

    if state.seen_function_call_deltas and state.function_call_yielded:
        events.append({"is_final": True, "finish_reason": "tool_calls"})
        return events

    if state.full_answer_text and not state.has_yielded_content:
        clean_text, parsed_tool_calls = parse_tool_calls_from_text(state.full_answer_text)
        if parsed_tool_calls:
            if clean_text:
                events.append({"text": clean_text})
            for tc in parsed_tool_calls:
                tc_obj = ToolCall(id=tc["id"], name=tc["name"], arguments=tc["arguments"])
                events.append(tool_call_to_dict(tc_obj))
            events.append(finish_reason_to_dict(FinishReason("tool_calls")))
            return events
        events.append({"text": state.full_answer_text})

    events.append(finish_reason_to_dict(FinishReason(finish_reason or "stop")))
    return events


def parse_stream_chunks(
    raw_bytes: bytes,
    state: StreamState,
    conversation: Optional[Any],
    has_tools: bool,
) -> List[Dict[str, Any]]:
    state.buffer += raw_bytes.decode("utf-8", errors="ignore")
    events: List[Dict[str, Any]] = []

    while "\n" in state.buffer:
        line, state.buffer = state.buffer.split("\n", 1)
        line = line.strip()

        if not line or line.startswith(":"):
            continue

        if not line.startswith("data: "):
            continue

        chunk_str = line[6:]

        if chunk_str == "[DONE]":
            break

        try:
            chunk_data = json.loads(chunk_str)
        except json.JSONDecodeError:
            continue

        if "response.created" in chunk_data:
            resp_id = chunk_data.get("response.created", {}).get("response_id")
            if resp_id:
                state.pending_parent_id = resp_id

        choices = chunk_data.get("choices", [])
        if not choices:
            continue

        choice = choices[0]
        delta = choice.get("delta", {})
        phase = delta.get("phase")
        content = delta.get("content")
        finish_reason = choice.get("finish_reason")
        status = delta.get("status")

        if content or finish_reason or (phase and phase not in ("answer",)) or (status and status != "typing"):
            logger.debug(f"[QWEN] chunk: phase={phase} content_len={len(content) if content else 0} finish_reason={finish_reason} status={status} fc={bool(delta.get('function_call'))} fc_name={delta.get('name')}")

        if content:
            ev = _handle_content(content, phase, state, has_tools)
            if ev:
                events.append(ev)

        fc_event = _handle_native_function_call(delta, state)
        if fc_event:
            state.has_any_content = True
            events.append(fc_event)

        if finish_reason:
            if state.saw_native_fc and not state.function_call_yielded:
                logger.debug(f"[QWEN] Skipping finish_reason={finish_reason} after native FC, waiting for answer phase")
                state.saw_native_fc = False
                continue

            logger.debug(f"[QWEN] finish_reason={finish_reason} yielded={state.has_yielded_content} text_len={len(state.full_answer_text)}")
            finish_events = _handle_finish_reason(finish_reason, state, has_tools)
            if finish_events is not None:
                events.extend(finish_events)
                return events

    return events


def finalize_stream(state: StreamState, has_tools: bool, conversation=None) -> List[Dict[str, Any]]:
    logger.debug(f"[QWEN] finalize_stream: yielded={state.has_yielded_content} text_len={len(state.full_answer_text)} fc_yielded={state.function_call_yielded}")
    events: List[Dict[str, Any]] = []

    if state.has_any_content and state.pending_parent_id and conversation and hasattr(conversation, "parent_id"):
        conversation.parent_id = state.pending_parent_id

    if state.full_answer_text and not state.function_call_yielded:
        clean_text, parsed_tool_calls = parse_tool_calls_from_text(state.full_answer_text)
        if parsed_tool_calls:
            if clean_text:
                events.append({"text": clean_text})
            for tc in parsed_tool_calls:
                tc_obj = ToolCall(id=tc["id"], name=tc["name"], arguments=tc["arguments"])
                events.append(tool_call_to_dict(tc_obj))
            events.append({"is_final": True, "finish_reason": "tool_calls"})
            return events
        elif clean_text and not state.has_yielded_content:
            events.append({"text": clean_text})

    events.append({"is_final": True, "finish_reason": "stop"})
    return events