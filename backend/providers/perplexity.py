import json
import logging
import uuid
from typing import Any, AsyncGenerator, Dict, List

from curl_cffi.requests import AsyncSession

from .base import BaseProvider

logger = logging.getLogger("flashy.perplexity")

MODELS = [
    {"id": "auto", "name": "Perplexity Auto", "context_window": 128000},
]

PERPLEXITY_HEADERS = {
    "Accept": "text/event-stream",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json",
    "Origin": "https://www.perplexity.ai",
    "Referer": "https://www.perplexity.ai/",
    "Sec-Ch-Ua": '"Google Chrome";v="134", "Chromium";v="134", "Not.A/Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
}


def _messages_to_query(messages: List[Dict[str, Any]]) -> str:
    parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if not content:
            continue
        if role == "system":
            parts.append(f"System: {content}")
        elif role == "user":
            parts.append(content)
        elif role == "assistant":
            parts.append(content)
    return "\n\n".join(parts)


def _extract_sources(text: str) -> str:
    import re
    cleaned = re.sub(r'\[perplexity\+?\d*\]', '', text)
    cleaned = re.sub(r'\[\d+\]', '', cleaned)
    return cleaned.strip()


class PerplexityProvider(BaseProvider):
    """Perplexity AI provider from perplexity.ai."""

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        return [{"id": m["id"], "name": m["name"]} for m in MODELS]

    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        session_token = kwargs.get("session_token") or kwargs.get("perplexity_session_token", "")
        if not session_token:
            yield {"error": "Perplexity requires a session token. Set perplexity_session_token in config."}
            return

        headers = {
            **PERPLEXITY_HEADERS,
            "Cookie": f"__Secure-next-auth.session-token={session_token};",
        }

        query = _messages_to_query(messages)
        if not query.strip():
            yield {"error": "No user message found"}
            return

        payload = {
            "params": {
                "query": query,
                "model_preference": "auto",
                "search_focus": "internet",
                "sources": ["web", "news"],
                "mode": "auto",
                "frontend_uuid": str(uuid.uuid4()),
                "frontend_context_uuid": str(uuid.uuid4()),
                "supported_block_use_cases": [
                    "markdown_block",
                    "block_with_sources",
                    "code_block",
                    "math_block",
                    "image_block",
                    "table_block",
                    "quote_block",
                    "chart_block",
                    "mindmap_block",
                    "goal_block",
                    "sources_mode_block",
                    "mermaid_block",
                    "text_element",
                    "code_element",
                ],
            },
        }

        try:
            async with AsyncSession(impersonate="chrome") as session:
                resp = await session.post(
                    "https://www.perplexity.ai/rest/sse/perplexity_ask",
                    headers=headers,
                    json=payload,
                    stream=True,
                    timeout=120,
                )

                if resp.status_code == 403:
                    yield {"error": "Perplexity: 403 Forbidden — session token may be invalid or expired."}
                    return
                if resp.status_code != 200:
                    error_text = resp.text[:300]
                    yield {"error": f"Perplexity error ({resp.status_code}): {error_text}"}
                    return

                buffer = ""
                accumulated_blocks = {}
                has_content = False

                async for chunk_bytes in resp.aiter_content():
                    buffer += chunk_bytes.decode("utf-8", errors="ignore")

                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue

                        if line.startswith("event: "):
                            continue
                        if line.startswith("retry: "):
                            continue

                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if not data_str or data_str == "[DONE]":
                                continue

                            try:
                                data = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue

                            event_type = data.get("type") or data.get("event", "")

                            if event_type == "backend_uuid":
                                continue

                            if event_type in ("text", "content", "delta"):
                                text = data.get("text") or data.get("content") or data.get("delta") or ""
                                if text:
                                    has_content = True
                                    yield {"text": text}

                            blocks = data.get("blocks") or data.get("block", [])
                            if isinstance(blocks, dict):
                                blocks = [blocks]

                            if isinstance(blocks, list):
                                for block in blocks:
                                    if not isinstance(block, dict):
                                        continue
                                    block_id = block.get("id") or str(id(block))
                                    text = block.get("text") or block.get("content") or ""
                                    block_type = block.get("type") or ""

                                    if not text:
                                        continue

                                    has_content = True

                                    if "goal" in block_type.lower() or "thinking" in block_type.lower() or "reasoning" in block_type.lower():
                                        prev = accumulated_blocks.get(block_id, "")
                                        if len(text) > len(prev):
                                            delta = text[len(prev):]
                                            accumulated_blocks[block_id] = text
                                            if delta:
                                                yield {"thought": delta}
                                    else:
                                        prev = accumulated_blocks.get(block_id, "")
                                        if len(text) > len(prev):
                                            delta = text[len(prev):]
                                            accumulated_blocks[block_id] = text
                                            if delta:
                                                cleaned = _extract_sources(delta)
                                                if cleaned:
                                                    yield {"text": cleaned}

                            if data.get("status") == "completed" or data.get("done"):
                                yield {"usage": {
                                    "prompt_tokens": data.get("prompt_tokens", 0),
                                    "completion_tokens": data.get("completion_tokens", 0),
                                    "total_tokens": data.get("total_tokens", 0),
                                }}
                                yield {"is_final": True, "finish_reason": "stop"}
                                return

                if has_content:
                    yield {"is_final": True, "finish_reason": "stop"}
                else:
                    yield {"error": "Perplexity returned no content."}

        except Exception as e:
            logger.exception(f"[PERPLEXITY] Error: {e}")
            yield {"error": f"Perplexity error: {str(e)}"}
