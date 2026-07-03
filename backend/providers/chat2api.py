import json
import logging
from typing import Any, AsyncGenerator, Dict, List

import aiohttp

from .base import BaseProvider, ProviderType

logger = logging.getLogger("flashy.chat2api")

MODELS = []

def clear_model_cache():
    global MODELS
    MODELS = []

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def _decode_grpc_web(data: bytes) -> List[bytes]:
    messages = []
    pos = 0
    while pos < len(data):
        if pos + 5 > len(data):
            break
        length = int.from_bytes(data[pos + 1:pos + 5], "big")
        pos += 5
        if pos + length > len(data):
            break
        messages.append(data[pos:pos + length])
        pos += length
    return messages


class Chat2APIProvider(BaseProvider):
    """Chat2API local proxy provider."""

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.PROXY

    def __init__(self, base_url: str = "http://127.0.0.1:8080"):
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/v1"

    @classmethod
    async def get_models(cls, base_url: str = "http://127.0.0.1:8080", api_key: str = "") -> List[Dict[str, Any]]:
        global MODELS
        if MODELS:
            return MODELS

        headers = {**HEADERS}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            async with aiohttp.ClientSession() as session:
                resp = await session.get(
                    f"{base_url.rstrip('/')}/v1/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                )
                if resp.status == 200:
                    data = await resp.json()
                    MODELS = [
                        {"id": m["id"], "name": m["id"], "context_window": 128000}
                        for m in data.get("data", [])
                    ]
                    logger.info(f"[Chat2API] Found {len(MODELS)} models")
                    return MODELS
                else:
                    error_text = await resp.text()
                    logger.error(f"[Chat2API] Failed to fetch models: {resp.status} - {error_text}")
        except Exception as e:
            logger.error(f"[Chat2API] Error fetching models: {e}")

        return []

    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        token = kwargs.get("token") or kwargs.get("api_key", "")
        base_url = kwargs.get("base_url", "http://127.0.0.1:8080")
        
        headers = {**HEADERS}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        chat_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if not content:
                continue
            chat_messages.append({"role": role, "content": content})

        if not chat_messages:
            yield {"type": "error", "error": "No user message found"}
            return

        headers["Content-Type"] = "application/json"
        api_url = f"{base_url.rstrip('/')}/v1"

        # Track last character to detect missing spaces
        last_char = ""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{api_url}/chat/completions",
                    json={
                        "model": model,
                        "messages": chat_messages,
                        "stream": True
                    },
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    if resp.status == 401:
                        yield {"type": "error", "error": "Chat2API: Invalid or missing API key"}
                        return
                    if resp.status != 200:
                        error_text = await resp.text()
                        yield {"type": "error", "error": f"Chat2API error: {resp.status} - {error_text[:200]}"}
                        return

                    buffer = ""
                    async for chunk_bytes in resp.content.iter_any():
                        buffer += chunk_bytes.decode("utf-8", errors="ignore")
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            # Only strip trailing whitespace, keep leading space after 'data: '
                            line = line.rstrip()
                            if not line or not line.startswith("data:"):
                                continue
                            
                            chunk_str = line[5:].strip()
                            if chunk_str == "[DONE]":
                                yield {"is_final": True}
                                return
                            
                            try:
                                data = json.loads(chunk_str)
                            except json.JSONDecodeError:
                                continue

                            if data.get("error"):
                                yield {"error": str(data["error"])}
                                return

                            choices = data.get("choices", [])
                            if choices:
                                choice = choices[0]
                                delta = choice.get("delta", {})
                                content = delta.get("content", "")
                                reasoning = delta.get("reasoning_content", "")
                                finish = choice.get("finish_reason")

                                if reasoning:
                                    if last_char and last_char.isalnum() and reasoning[0].isalnum():
                                        reasoning = " " + reasoning
                                    if reasoning:
                                        last_char = reasoning[-1]
                                    yield {"thought": reasoning}
                                if content:
                                    # If the previous chunk ended with a word char and this starts with one, add a space
                                    if last_char and last_char.isalnum() and content[0].isalnum():
                                        content = " " + content
                                    if content:
                                        last_char = content[-1]
                                    yield {"text": content}
                                
                                if finish and finish in ["stop", "length"]:
                                    yield {"is_final": True, "finish_reason": finish}
                                    return

        except Exception as e:
            logger.error(f"[Chat2API] Error: {e}")
            yield {"type": "error", "error": str(e)}