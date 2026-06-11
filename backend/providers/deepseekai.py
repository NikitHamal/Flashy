"""
Deep-Seek AI chat provider for Flashy.

Reverse-engineered from https://deep-seek.ai/chat (Laravel + OpenRouter proxy).

The site is a Laravel app that proxies requests to OpenRouter:
  - Chat endpoint: POST https://deep-seek.ai/api/chat
  - Auth: CSRF token from <meta name="csrf-token"> + session cookies (XSRF-TOKEN, deepseek_session)
  - Body: JSON {"model": "<model_id>", "messages": [{"role": "...", "content": "..."}]}
  - Response: SSE stream (OpenAI-compatible format)
  - Rate limit: HTTP 429 with {"error": {"limit_exhausted": true, "limit_type": "default"}}
  - Reasoning models: return "reasoning" and "reasoning_details" fields in delta

Models:
  - deepseek/deepseek-v4-flash (DeepSeek-V4 Flash)
  - deepseek/deepseek-r1 (DeepSeek-R1, reasoning)
  - deepseek/deepseek-v3.2 (DeepSeek-V3.2)

Flow:
  1. GET https://deep-seek.ai/chat to obtain CSRF token + session cookies
  2. POST /api/chat with CSRF token header + cookies + JSON body
  3. Parse SSE stream, yield OpenAI-compatible deltas
"""

import json
import logging
import re
from typing import AsyncGenerator, Dict, Any, List, Optional

import httpx

from .base import BaseProvider

logger = logging.getLogger("flashy.deepseekai")

SITE_URL = "https://deep-seek.ai"
CHAT_URL = f"{SITE_URL}/api/chat"
PAGE_URL = f"{SITE_URL}/chat"
REQUEST_TIMEOUT = 180

MODELS = [
    {"id": "deepseek/deepseek-v4-flash", "name": "DeepSeek-V4 Flash", "vision": False, "thinking": False},
    {"id": "deepseek/deepseek-r1", "name": "DeepSeek-R1", "vision": False, "thinking": True},
    {"id": "deepseek/deepseek-v3.2", "name": "DeepSeek-V3.2", "vision": False, "thinking": False},
]


class DeepSeekAIProvider(BaseProvider):
    def __init__(self):
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(REQUEST_TIMEOUT, connect=30),
            follow_redirects=True,
            http2=True,
        )

    async def _get_session(self) -> Dict[str, str]:
        """Fetch the chat page to obtain CSRF token and session cookies."""
        resp = await self._client.get(
            PAGE_URL,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"},
        )
        html = resp.text
        csrf_match = re.search(r'<meta\s+name="csrf-token"\s+content="([^"]+)"', html)
        csrf = csrf_match.group(1) if csrf_match else ""

        cookies = {}
        for name, value in resp.cookies.items():
            cookies[name] = value

        return {"csrf": csrf, "cookies": cookies}

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
                },
            }
            for m in MODELS
        ]

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        session = await self._get_session()
        csrf = session["csrf"]
        cookies = session["cookies"]

        # deep-seek.ai Laravel/OpenRouter proxy rejects role='system' and redirects to aichat.org.
        # We combine any 'system' prompt into the first 'user' message.
        formatted_messages = []
        system_content = ""
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                if system_content:
                    system_content += "\n" + content
                else:
                    system_content = content
            else:
                formatted_messages.append({"role": role, "content": content})

        if system_content:
            user_msg_idx = -1
            for idx, m in enumerate(formatted_messages):
                if m["role"] == "user":
                    user_msg_idx = idx
                    break
            if user_msg_idx != -1:
                formatted_messages[user_msg_idx]["content"] = f"[System Instructions]\n{system_content}\n\n{formatted_messages[user_msg_idx]['content']}"
            else:
                formatted_messages.insert(0, {"role": "user", "content": system_content})

        payload = {
            "model": model,
            "messages": formatted_messages,
        }

        headers = {
            "Content-Type": "application/json",
            "X-CSRF-TOKEN": csrf,
            "Accept": "text/event-stream",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Referer": f"{SITE_URL}/chat",
            "Origin": SITE_URL,
        }

        async with self._client.stream(
            "POST",
            CHAT_URL,
            json=payload,
            headers=headers,
            cookies=cookies,
        ) as resp:
            if resp.status_code == 429:
                try:
                    body = await resp.aread()
                    err = json.loads(body)
                    err_data = err.get("error", {})
                    raise httpx.HTTPStatusError(
                        f"Rate limited: {err_data.get('error', 'daily limit')}",
                        request=resp.request,
                        response=resp,
                    )
                except (json.JSONDecodeError, AttributeError):
                    raise httpx.HTTPStatusError(
                        "Rate limited (429)",
                        request=resp.request,
                        response=resp,
                    )

            if resp.status_code != 200:
                body = await resp.aread()
                raise httpx.HTTPStatusError(
                    f"HTTP {resp.status_code}: {body.decode('utf-8', errors='replace')[:500]}",
                    request=resp.request,
                    response=resp,
                )

            current_event = ""
            async for line_bytes in resp.aiter_lines():
                line = line_bytes.strip()
                if not line:
                    continue

                if line.startswith("event:"):
                    current_event = line[6:].strip()
                    continue

                if line.startswith(":"):
                    continue

                if line.startswith("data:"):
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        return

                    if current_event == "error":
                        try:
                            err = json.loads(data_str)
                            err_data = err.get("error", {})
                            yield {
                                "type": "error",
                                "error": err_data.get("error", "Unknown error"),
                                "limit_exhausted": err_data.get("limit_exhausted", False),
                                "limit_type": err_data.get("limit_type", "default"),
                            }
                        except json.JSONDecodeError:
                            pass
                        current_event = ""
                        continue

                    try:
                        chunk = json.loads(data_str)
                        choices = chunk.get("choices", [])
                        if not choices:
                            continue

                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                        reasoning = delta.get("reasoning", "")
                        finish_reason = choices[0].get("finish_reason")

                        if content:
                            yield {"type": "text", "content": content}

                        if reasoning:
                            yield {"type": "thinking", "content": reasoning}

                        if finish_reason == "stop":
                            yield {"type": "done", "finish_reason": "stop"}

                    except json.JSONDecodeError:
                        continue