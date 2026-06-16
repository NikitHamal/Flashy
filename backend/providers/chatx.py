import json
import logging
import re
from typing import AsyncGenerator, Dict, Any, List, Optional

import httpx

from .base import BaseProvider

logger = logging.getLogger("flashy.chatx")

BASE_URL = "https://chatx.ai"
REQUEST_TIMEOUT = 120

POPULAR_MODELS = [
    {"id": "gpt3", "name": "GPT-5 nano", "vision": False, "thinking": False},
    {"id": "deepseek_flash", "name": "DeepSeek V4 Flash", "vision": False, "thinking": False},
    {"id": "gpto3", "name": "GPT-5.4 nano", "vision": False, "thinking": False},
    {"id": "gpt54_mini", "name": "GPT-5.4 mini", "vision": False, "thinking": False},
    {"id": "gpt4", "name": "GPT-5.4", "vision": True, "thinking": False},
    {"id": "gpt5_5", "name": "GPT-5.5", "vision": True, "thinking": False},
    {"id": "gpto1", "name": "GPT-5 mini", "vision": False, "thinking": False},
    {"id": "gemini", "name": "Gemini 3.1 Flash Lite", "vision": False, "thinking": False},
    {"id": "gemini_pro", "name": "Gemini 3.5 Flash", "vision": True, "thinking": False},
    {"id": "claude_haiku", "name": "Claude Haiku 4.5", "vision": False, "thinking": False},
    {"id": "claude_sonnet", "name": "Claude Sonnet 4.6", "vision": True, "thinking": False},
    {"id": "claude_opus", "name": "Claude Opus 4.8", "vision": True, "thinking": False},
    {"id": "deepseek_pro", "name": "DeepSeek V4 Pro", "vision": False, "thinking": False},
    {"id": "grok_fast", "name": "Grok 4 Fast", "vision": False, "thinking": False},
    {"id": "grok_default", "name": "Grok 4.3", "vision": False, "thinking": False},
    {"id": "gpt5_3", "name": "GPT-5.3", "vision": False, "thinking": False},
]

# Models that require registration to use
REGISTRATION_REQUIRED = {"gpt4", "gpt5_5", "gpto1", "gpt5_3", "gemini_pro", "nano_banana_pro", "claude_haiku", "claude_sonnet", "claude_opus", "deepseek_pro", "grok_fast", "grok_default"}


class ChatXProvider(BaseProvider):
    def __init__(self, cookie: str = "", base_url: str = ""):
        self.cookie = cookie
        self.base_url = (base_url or BASE_URL).rstrip("/")
        self._session_data = None

    async def _ensure_session(self, client: httpx.AsyncClient) -> dict:
        if self._session_data:
            return self._session_data

        resp = await client.get(f"{self.base_url}/gpt", timeout=30)
        html = resp.text

        csrf = re.search(r'<meta\s+name="csrf-token"\s+content="([^"]+)"', html)
        user_id = re.search(r'<input[^>]*id="user_id"[^>]*value="([^"]+)"', html)

        data = {
            "csrf": csrf.group(1) if csrf else "",
            "user_id": user_id.group(1) if user_id else "",
        }

        if not data["csrf"] or not data["user_id"]:
            raise RuntimeError("chatx: could not establish guest session")

        self._session_data = data
        return data

    def _base_headers(self, csrf: str) -> Dict[str, str]:
        headers = {
            "X-CSRF-TOKEN": csrf,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self.base_url}/gpt",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        if self.cookie:
            headers["Cookie"] = self.cookie
        return headers

    async def _register_model(self, client: httpx.AsyncClient, csrf: str, model: str) -> None:
        resp = await client.post(
            f"{self.base_url}/user_model",
            data={"_token": csrf, "model": model},
            headers=self._base_headers(csrf),
            timeout=15,
        )
        if resp.status_code != 200:
            logger.warning(f"chatx: model registration returned {resp.status_code}")

    async def _create_chat(self, client: httpx.AsyncClient, csrf: str, user_id: str) -> str:
        resp = await client.post(
            f"{self.base_url}/newchat",
            data={"_token": csrf, "user_id": user_id, "is_manual": "0"},
            headers=self._base_headers(csrf),
            timeout=15,
        )
        html = resp.text
        ids = re.findall(r'id="title(\d+)"', html)
        if ids:
            return ids[0]
        ids = re.findall(r"selectchat\((\d+)\)", html)
        if ids:
            return ids[0]
        return ""

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        cookie = kwargs.get("cookie") or self.cookie
        base_url = kwargs.get("base_url") or self.base_url

        async with httpx.AsyncClient(verify=False, timeout=REQUEST_TIMEOUT) as client:
            session = await self._ensure_session(client)
            csrf = session["csrf"]
            user_id = session["user_id"]

            headers = self._base_headers(csrf)

            # Step 1: Register model
            await self._register_model(client, csrf, model)

            # Step 2: Create a chat session
            chats_id = await self._create_chat(client, csrf, user_id)
            if not chats_id:
                yield {"error": "chatx: could not create chat session"}
                return

            # Build prompt from messages
            prompt = messages[-1]["content"] if messages else "hello"

            # Step 3: Send chat
            chat_resp = await client.post(
                f"{base_url}/sendchat",
                data={
                    "_token": csrf,
                    "user_id": user_id,
                    "chats_id": chats_id,
                    "prompt": prompt,
                    "current_model": model,
                    "is_web": "0",
                    "is_youtube": "0",
                },
                headers={**headers, "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
                timeout=30,
            )

            if chat_resp.status_code != 200:
                body = chat_resp.text[:500]
                yield {"error": f"chatx: HTTP {chat_resp.status_code}: {body}"}
                return

            try:
                result = chat_resp.json()
            except json.JSONDecodeError:
                yield {"error": f"chatx: invalid JSON response: {chat_resp.text[:200]}"}
                return

            if not result.get("response"):
                err = result.get("message", "unknown error")
                yield {"error": f"chatx: {err}"}
                return

            conv_id = result.get("conversions_id")
            ass_conv_id = result.get("ass_conversions_id", "")

            if not conv_id:
                yield {"error": "chatx: no conversions_id in response"}
                return

            # Step 4: Stream from SSE endpoint
            sse_url = (
                f"{base_url}/chats_stream"
                f"?user_id={user_id}"
                f"&chats_id={chats_id}"
                f"&current_model={model}"
                f"&conversions_id={conv_id}"
                f"&ass_conversions_id={ass_conv_id}"
                f"&captcha_token="
                f"&copyid={conv_id}"
            )

            async with client.stream("GET", sse_url, headers=headers) as sse_resp:
                if sse_resp.status_code != 200:
                    body = await sse_resp.aread()
                    yield {"error": f"chatx: SSE HTTP {sse_resp.status_code}: {body[:200]}"}
                    return

                async for line_bytes in sse_resp.aiter_lines():
                    line = line_bytes.decode("utf-8", errors="replace") if isinstance(line_bytes, bytes) else line_bytes
                    if line.strip() == "end":
                        return
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if not data_str:
                        continue
                    try:
                        event = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    event_type = event.get("type", "")
                    delta = event.get("delta", "")
                    if event_type == "response.output_text.delta" and delta:
                        yield {"text": delta}
                    elif event_type == "response.output_text.done":
                        pass
                    elif "available_token" in event:
                        pass

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        return POPULAR_MODELS
