import json
import logging
import time
import uuid
from typing import AsyncGenerator, Dict, Any, List, Optional

import httpx

from .base import BaseProvider

logger = logging.getLogger("flashy.duckai")

DUCKAI_BASE = "http://127.0.0.1:3000"
REQUEST_TIMEOUT = 180

MODELS = [
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "vision": False, "thinking": False},
    {"id": "gpt-5-mini", "name": "GPT-5 Mini", "vision": False, "thinking": False},
    {"id": "claude-3-5-haiku-latest", "name": "Claude 3.5 Haiku", "vision": False, "thinking": False},
    {"id": "meta-llama/Llama-4-Scout-17B-16E-Instruct", "name": "Llama 4 Scout 17B", "vision": False, "thinking": False},
    {"id": "mistralai/Mistral-Small-24B-Instruct-2501", "name": "Mistral Small 24B", "vision": False, "thinking": False},
    {"id": "openai/gpt-oss-120b", "name": "GPT-OSS 120B", "vision": False, "thinking": False},
]


class DuckAIProvider(BaseProvider):
    _auto_started = False

    def __init__(self, base_url: str = DUCKAI_BASE):
        self.base_url = base_url
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(REQUEST_TIMEOUT, connect=10),
            follow_redirects=True,
        )
        self._auto_start()

    def _auto_start(self):
        if DuckAIProvider._auto_started:
            return
        DuckAIProvider._auto_started = True
        try:
            import urllib.request
            urllib.request.urlopen(f"{self.base_url}/health", timeout=1)
        except Exception:
            from ..duckai_control import start as duckai_start
            try:
                result = duckai_start()
                if result.get("health", {}).get("ok"):
                    import logging
                    logging.getLogger("flashy.duckai").info("DuckAI auto-started on %s", result.get("url"))
            except Exception:
                pass

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        return [
            {
                "id": m["id"],
                "name": m["name"],
                "capabilities": {
                    "chat": True,
                    "stream": True,
                    "vision": m.get("vision", False),
                    "thinking": m.get("thinking", False),
                    "tools": True,
                },
            }
            for m in MODELS
        ]

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o-mini",
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        logger.info("duckai: generate_stream model=%s messages=%d", model, len(messages))

        if not model:
            model = "gpt-4o-mini"

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens"),
            "top_p": kwargs.get("top_p", 1.0),
        }

        if kwargs.get("tools"):
            payload["tools"] = kwargs["tools"]
        if kwargs.get("tool_choice"):
            payload["tool_choice"] = kwargs["tool_choice"]

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer flashy-duckai",
        }

        try:
            async with self._client.stream(
                "POST",
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                if resp.status_code != 200:
                    error_body = await resp.aread()
                    error_text = error_body.decode("utf-8", errors="replace")[:500]
                    yield {"error": f"duckai: HTTP {resp.status_code}: {error_text}"}
                    return

                async for line in resp.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                        except (json.JSONDecodeError, ValueError):
                            continue

                        choices = chunk.get("choices", [])
                        if not choices:
                            continue

                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                        tool_calls = delta.get("tool_calls")
                        finish_reason = choices[0].get("finish_reason")

                        if content:
                            yield {"text": content}

                        if tool_calls:
                            for tc in tool_calls:
                                yield {
                                    "tool_call": {
                                        "id": tc.get("id", f"call_{uuid.uuid4().hex[:16]}"),
                                        "name": tc.get("function", {}).get("name", "unknown"),
                                        "arguments": tc.get("function", {}).get("arguments", "{}"),
                                    }
                                }

                        if finish_reason == "stop":
                            break
                        elif finish_reason == "tool_calls":
                            break

        except httpx.ConnectError:
            yield {"error": "duckai: cannot connect to DuckAI server (port 3000). Use Server Center to start it."}
            return
        except Exception as exc:
            logger.exception("duckai: stream error: %s", exc)
            yield {"error": f"duckai: stream error: {exc}"}
            return

        yield {"is_final": True, "finish_reason": "stop"}
