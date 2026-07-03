from .metadata import estimate_tokens
import json

COMPACTION_THRESHOLD = 0.80  # compact when usage reaches 80% of context window
KEEP_RECENT_TURNS = 6        # number of most recent messages to keep intact
COMPACTION_TRIGGER_MIN = 10  # minimum messages before triggering compaction


def should_compact(total_tokens: int, context_window: int) -> bool:
    if context_window <= 0 or total_tokens <= 0:
        return False
    return total_tokens >= context_window * COMPACTION_THRESHOLD


async def compact_messages(messages: list, llm_service=None, session_id: str=None, keep_recent: int = KEEP_RECENT_TURNS) -> tuple:
    """Compress older messages into a summary using an LLM, keeping recent ones intact.

    Returns (compacted_messages, was_compacted, summary_text).
    """
    if len(messages) < COMPACTION_TRIGGER_MIN:
        return messages, False, ""

    keep = keep_recent if keep_recent < len(messages) else len(messages) // 3
    if keep >= len(messages):
        return messages, False, ""

    # Check for existing summary in the first message
    existing_summary = ""
    if messages and messages[0].get("role") == "system" and "[Compressed conversation history]" in messages[0].get("content", ""):
        existing_summary = messages[0]["content"]

    to_compress = messages[1:-keep] if existing_summary else messages[:-keep]
    to_keep = messages[-keep:]
    
    if not to_compress:
        return messages, False, ""

    lines = []
    for msg in to_compress:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        # Remove tool results/calls from prompt to save tokens and focus on conversation if needed
        # But we might need them. We will just dump it as json.
        if isinstance(content, str) and content:
            if len(content) > 2000:
                content = content[:2000] + "..."
            lines.append(f"[{role}]: {content}")
        elif isinstance(content, list):
            # some multimodal or tool calls
            lines.append(f"[{role}]: [Complex Content]")

    history_text = "\n".join(lines)
    
    prompt = f"""You are an anchored context summarization assistant for coding sessions.

Summarize only the conversation history you are given. The newest turns may be kept verbatim outside your summary, so focus on the older context that still matters for continuing the work.

If the prompt includes a <previous-summary> block, treat it as the current anchored summary. Update it with the new history by preserving still-true details, removing stale details, and merging in new facts.

Always follow the exact output structure requested by the user prompt. Keep every section, preserve exact file paths and identifiers when known, and prefer terse bullets over paragraphs.

Do not answer the conversation itself. Do not mention that you are summarizing, compacting, or merging context. Respond in the same language as the conversation.

<previous-summary>
{existing_summary}
</previous-summary>

<history-to-summarize>
{history_text}
</history-to-summarize>
"""
    
    summary = ""
    if llm_service and session_id:
        try:
            # We call the provider directly without agent logic to get a fast summary
            provider_name = llm_service.get_active_provider()
            from ..providers import get_provider_service
            provider_svc = get_provider_service(provider_name)
            
            if provider_svc:
                temp_messages = [{"role": "user", "content": prompt}]
                async for chunk in provider_svc.generate_stream(
                    temp_messages,
                    llm_service.config.get("model", ""),
                    proxy=llm_service.config.get("proxy"),
                    chat_type="t2t",
                    thinking_enabled=False # Disable thinking for summarization to be fast
                ):
                    if "text" in chunk:
                        summary += chunk["text"]
        except Exception as e:
            print(f"[Compaction] LLM summarization failed: {e}")
            summary = history_text[:2000] + "\n... (Fallback summary due to error)"
    else:
        summary = history_text[:2000] + "\n..."

    # Before building compacted list, strip tool results that reference
    # tool_call_ids from messages that got compressed away (B.AI / OpenAI reject orphans)
    kept_tool_call_ids = set()
    for msg in to_keep:
        if msg.get("role") == "assistant":
            tcs = msg.get("tool_calls")
            if tcs:
                for tc in tcs:
                    tid = tc.get("id") if isinstance(tc, dict) else None
                    if tid:
                        kept_tool_call_ids.add(tid)
    to_keep = [m for m in to_keep if not (m.get("role") == "tool" and m.get("tool_call_id") not in kept_tool_call_ids)]

    compacted = [
        {"role": "system", "content": f"[Compressed conversation history]\n{summary}"}
    ] + to_keep

    return compacted, True, summary


async def perform_compaction(
    session_id: str,
    provider_sessions: dict,
    usage_tracker: dict,
    context_window: int,
    provider: str,
    model: str,
    llm_service = None,
) -> bool:
    """Compact a session's conversation and reset its usage tracking.

    Returns True if compaction occurred.
    """
    messages = provider_sessions.get(session_id, [])
    compacted, was_compacted, summary = await compact_messages(messages, llm_service, session_id)

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

