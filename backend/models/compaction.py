from .metadata import estimate_tokens


COMPACTION_THRESHOLD = 0.78  # compact when usage reaches 78% of context window
KEEP_RECENT_TURNS = 6        # number of most recent messages to keep intact
COMPACTION_TRIGGER_MIN = 10  # minimum messages before triggering compaction


def should_compact(total_tokens: int, context_window: int) -> bool:
    if context_window <= 0 or total_tokens <= 0:
        return False
    return total_tokens >= context_window * COMPACTION_THRESHOLD


def compact_messages(messages: list, keep_recent: int = KEEP_RECENT_TURNS) -> tuple:
    """Compress older messages into a summary, keeping recent ones intact.

    Returns (compacted_messages, was_compacted, summary_text).
    """
    if len(messages) < COMPACTION_TRIGGER_MIN:
        return messages, False, ""

    keep = keep_recent if keep_recent < len(messages) else len(messages) // 3
    if keep >= len(messages):
        return messages, False, ""

    to_compress = messages[:-keep]
    to_keep = messages[-keep:]

    lines = []
    for msg in to_compress:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if isinstance(content, str) and content:
            if len(content) > 800:
                content = content[:800] + "..."
            lines.append(f"[{role}]: {content}")

    summary = "\n".join(lines)

    compacted = [
        {"role": "system", "content": f"[Compressed conversation history]\n{summary}"}
    ] + to_keep

    return compacted, True, summary


def perform_compaction(
    session_id: str,
    provider_sessions: dict,
    usage_tracker: dict,
    context_window: int,
    provider: str,
    model: str,
) -> bool:
    """Compact a session's conversation and reset its usage tracking.

    Returns True if compaction occurred.
    """
    messages = provider_sessions.get(session_id, [])
    compacted, was_compacted, summary = compact_messages(messages)

    if was_compacted:
        provider_sessions[session_id] = compacted
        new_total = estimate_tokens(summary)
        for msg in compacted:
            c = msg.get("content", "")
            if isinstance(c, str):
                new_total += estimate_tokens(c)
        usage = usage_tracker.get(session_id)
        if usage:
            usage["input_tokens"] = new_total
        print(f"[Compaction] Session {session_id[:12]}... compacted "
              f"{len(messages)}→{len(compacted)} msgs, est. {new_total} tokens")
        return True
    return False
