import json
import logging
import time
from typing import AsyncGenerator, Dict, Any, List, Optional

import httpx

from .base import BaseProvider

logger = logging.getLogger("flashy.rsk")

RSK_API_BASE = "https://x.rsk.cn/api"
REQUEST_TIMEOUT = 180
MODELS_CACHE_TTL = 300

FREE_MODEL_IDS = [
    "gemini-3.1-flash-lite",
    "gpt-5.4-mini",
    "deepseek-v4-flash",
    "glm-5-free",
    "gpt-5.4-nano",
    "qwen3.7-plus",
]

PREMIUM_MODEL_IDS = [
    "claude-opus-4-8",
    "grok-4.3",
    "deepseek-v4-pro",
    "gemini-3.1-pro-preview",
    "gpt-5.5",
    "qwen3.7-max",
]


class _ModelsCache:
    def __init__(self):
        self._models: List[Dict[str, Any]] = []
        self._ts: float = 0

    async def get(self) -> List[Dict[str, Any]]:
        now = time.time()
        if self._models and (now - self._ts) < MODELS_CACHE_TTL:
            return self._models
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(
                    f"{RSK_API_BASE}/chat/display-models?capability=chat",
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                if r.status_code == 200:
                    data = r.json()
                    if isinstance(data, list):
                        self._models = data
                        self._ts = now
                        return self._models
        except Exception as exc:
            logger.warning("rsk: failed to fetch models: %s", exc)
        return self._models

    def get_display_id(self, model_name: str) -> Optional[str]:
        for m in self._models:
            if m.get("name") == model_name:
                return m.get("id")
        return None

    def is_locked(self, model_name: str) -> bool:
        for m in self._models:
            if m.get("name") == model_name:
                return m.get("tier") == "premium"
        return model_name not in FREE_MODEL_IDS


_models_cache = _ModelsCache()


def _parse_messages(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    result = []
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
            role = "user"
        if content:
            result.append({"role": role, "content": content})
    return result


class RSKProvider(BaseProvider):

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        await _models_cache.get()
        models = []
        seen = set()
        for mid in FREE_MODEL_IDS + PREMIUM_MODEL_IDS:
            if mid in seen:
                continue
            seen.add(mid)
            locked = _models_cache.is_locked(mid)
            display_id = _models_cache.get_display_id(mid)
            models.append({
                "id": mid,
                "name": mid,
                "capabilities": {
                    "chat": True,
                    "stream": True,
                    "vision": False,
                    "reasoning": False,
                    "tools": False,
                },
                "locked": locked,
                "display_id": display_id,
            })
        return models

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "",
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        logger.info("rsk: generate_stream model=%s messages=%d", model, len(messages))

        if not model:
            model = "gpt-5.4-nano"

        parsed_messages = _parse_messages(messages)
        if not parsed_messages:
            yield {"error": "rsk: no messages to send"}
            return

        await _models_cache.get()
        display_id = _models_cache.get_display_id(model)
        if not display_id:
            yield {"error": f"rsk: unknown model '{model}'"}
            return

        body = {
            "model": model,
            "displayModelId": display_id,
            "messages": parsed_messages,
            "stream": True,
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Origin": "https://rsk.cn",
            "Referer": "https://rsk.cn/",
        }

        has_content = False
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                async with client.stream(
                    "POST",
                    f"{RSK_API_BASE}/chat/stream",
                    json=body,
                    headers=headers,
                ) as resp:
                    if resp.status_code == 401:
                        error_body = await resp.aread()
                        yield {"error": f"rsk: unauthorized (401): {error_body.decode('utf-8', errors='replace')[:300]}"}
                        return

                    if resp.status_code == 429:
                        error_body = await resp.aread()
                        yield {"error": f"rsk: rate limited (429): {error_body.decode('utf-8', errors='replace')[:300]}"}
                        return

                    if resp.status_code != 200:
                        error_body = await resp.aread()
                        yield {"error": f"rsk: HTTP {resp.status_code}: {error_body.decode('utf-8', errors='replace')[:300]}"}
                        return

                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue

                        if line.startswith("data: "):
                            data_str = line[6:]
                        elif line.startswith("data:"):
                            data_str = line[5:].strip()
                        else:
                            continue

                        if data_str == "[DONE]":
                            break

                        try:
                            event = json.loads(data_str)
                        except (json.JSONDecodeError, ValueError):
                            continue

                        if event.get("done"):
                            yield {"is_final": True, "finish_reason": event.get("finish_reason", "stop")}
                            return

                        if event.get("error"):
                            yield {"error": f"rsk: {event['error']}"}
                            return

                        content = event.get("content", "")
                        if content:
                            has_content = True
                            yield {"text": content}

                        status = event.get("status")
                        if status:
                            yield {"meta": {"status": status}}

        except Exception as exc:
            logger.exception("rsk: stream error: %s", exc)
            yield {"error": f"rsk: stream error: {exc}"}
            return

        yield {"is_final": True, "finish_reason": "stop"}
