import json
import logging
from typing import AsyncGenerator, Dict, Any, List

import httpx

from .base import BaseProvider

logger = logging.getLogger("flashy.chatgptoss")

URL = "https://chat-gpt-oss.com"
API_ENDPOINT = "https://chat-gpt-oss.com/api/message"
REQUEST_TIMEOUT = 120

MODELS = [
    {"id": "gpt-oss-120b", "name": "GPT OSS 120B"},
    {"id": "gpt-5-nano", "name": "GPT 5 Nano"},
]


def _build_prompt(messages: List[Dict[str, str]]) -> str:
    parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            content = "\n".join(text_parts)
        if role == "system":
            parts.append(f"System: {content}")
        elif role == "assistant":
            parts.append(f"Assistant: {content}")
        else:
            parts.append(content)
    return "\n\n".join(parts)


class ChatGptOssProvider(BaseProvider):
    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        return [
            {
                "id": m["id"],
                "name": m["name"],
                "capabilities": {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": False},
            }
            for m in MODELS
        ]

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-oss-120b",
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        if model not in ("gpt-oss-120b", "gpt-5-nano"):
            if "oss" in model.lower() or "120" in model:
                model = "gpt-oss-120b"
            else:
                model = "gpt-5-nano"

        prompt = _build_prompt(messages)

        headers = {
            "accept": "text/event-stream",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": URL,
            "referer": f"{URL}/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        }

        payload = {
            "conversation_id": None,
            "model": model,
            "content": prompt,
            "reasoning_effort": "low",
        }

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            try:
                async with client.stream("POST", API_ENDPOINT, json=payload, headers=headers) as resp:
                    if resp.status_code != 200:
                        body = await resp.aread()
                        yield {"error": f"chatgptoss: HTTP {resp.status_code}: {body.decode('utf-8', errors='replace')[:300]}"}
                        return

                    event_type = None
                    async for line_bytes in resp.aiter_lines():
                        if isinstance(line_bytes, bytes):
                            line = line_bytes.decode("utf-8")
                        else:
                            line = line_bytes
                        line = line.rstrip("\r")

                        if not line:
                            event_type = None
                            continue

                        if line.startswith("event:"):
                            event_type = line[6:].strip()
                            continue

                        if line.startswith("data:") and event_type == "message":
                            data_str = line[5:].strip()
                            if not data_str:
                                continue
                            try:
                                chunk = json.loads(data_str)
                                content = chunk.get("content", "")
                                if content:
                                    yield {"text": content}
                            except json.JSONDecodeError:
                                continue

                        if event_type == "summary":
                            break

            except httpx.TimeoutException:
                yield {"error": "chatgptoss: request timed out"}
                return
            except Exception as exc:
                logger.exception("chatgptoss: error: %s", exc)
                yield {"error": f"chatgptoss: {exc}"}
                return

        yield {"is_final": True, "finish_reason": "stop"}
