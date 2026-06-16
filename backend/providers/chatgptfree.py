"""
ChatGPTFree.ai (AIPKit) provider for Flashy.

Reverse-engineered from https://chatgptfree.ai/

WordPress site using the AIPKit plugin (gpt3-ai-content-generator-premium).

API Details:
  - All requests go through WordPress admin-ajax.php
  - Two-step process: cache message, then stream via EventSource
  - Nonce-based auth (refreshable via aipkit_get_frontend_chat_nonce)
  - Guest UUID for session tracking
  - Conversation UUID for multi-turn

Steps:
  1. GET homepage to obtain CF cookies (cloudscraper)
  2. POST aipkit_get_frontend_chat_nonce → get fresh nonce
  3. POST aipkit_cache_sse_message → get cache_key
  4. GET aipkit_frontend_chat_stream (EventSource) → SSE stream with deltas

Available bots (bot_id → name, provider):
  25871 → ChatGPT 5 Nano (OpenAI, web_search)
  25874 → Gemini (OpenRouter, web_search)
  25873 → DeepSeek (OpenRouter, no web_search)
  25875 → Claude (Claude, web_search)
  25872 → Xai/Grok (OpenRouter, web_search)
  29624 → Perplexity Sonar (OpenRouter, no web_search)
  25870 → Meta Llama 4 Maverick (OpenRouter, no web_search)
  25869 → Qwen 3 30B A3B (OpenRouter, web_search)

SSE event types:
  message_start → {message_id: "..."}
  status → {type: "response.created"} | {type: "response.in_progress"} | {delta: "token"}
  openai_response_id → {id: "..."}
  error → {error: "..."}
  done → {finished: true}
"""

import json
import logging
import uuid
import time
from typing import AsyncGenerator, Dict, Any, List, Optional

import httpx
import cloudscraper

from .base import BaseProvider

logger = logging.getLogger("flashy.chatgptfree")

AJAX_URL = "https://chatgptfree.ai/wp-admin/admin-ajax.php"
REQUEST_TIMEOUT = 180

BOTS = [
    {
        "id": "25871",
        "name": "ChatGPT 5 Nano",
        "provider": "OpenAI",
        "web_search": True,
        "reasoning": False,
    },
    {
        "id": "25874",
        "name": "Gemini",
        "provider": "OpenRouter",
        "web_search": True,
        "reasoning": False,
    },
    {
        "id": "25873",
        "name": "DeepSeek",
        "provider": "OpenRouter",
        "web_search": False,
        "reasoning": False,
    },
    {
        "id": "25875",
        "name": "Claude",
        "provider": "Claude",
        "web_search": True,
        "reasoning": False,
    },
    {
        "id": "25872",
        "name": "Xai Grok",
        "provider": "OpenRouter",
        "web_search": True,
        "reasoning": False,
    },
    {
        "id": "29624",
        "name": "Perplexity Sonar",
        "provider": "OpenRouter",
        "web_search": False,
        "reasoning": False,
    },
    {
        "id": "25870",
        "name": "Meta Llama 4 Maverick",
        "provider": "OpenRouter",
        "web_search": False,
        "reasoning": False,
    },
    {
        "id": "25869",
        "name": "Qwen 3 30B A3B",
        "provider": "OpenRouter",
        "web_search": True,
        "reasoning": False,
    },
]

BOT_ID_MAP = {b["id"]: b for b in BOTS}
MODEL_NAME_MAP = {b["name"].lower().replace(" ", "-"): b["id"] for b in BOTS}


def _parse_messages(messages: List[Dict[str, str]]) -> str:
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
    return "\n".join(parts) if len(parts) == 1 else "\n\n".join(
        f"{'[System]' if m.get('role') == 'system' else '[Assistant]' if m.get('role') == 'assistant' else '[User]'} {m.get('content', '')}"
        for m in messages if m.get("content")
    )


class _SessionManager:
    _instance = None
    _scraper = None
    _last_init = 0
    _nonce = ""
    _nonce_time = 0

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _ensure_scraper(self):
        now = time.time()
        if self._scraper is None or (now - self._last_init > 600):
            self._scraper = cloudscraper.create_scraper(
                browser={"browser": "chrome", "platform": "windows", "mobile": False},
                delay=5,
            )
            try:
                self._scraper.get("https://chatgptfree.ai/")
            except Exception:
                pass
            self._last_init = now

    def get_nonce(self, bot_id: str) -> str:
        now = time.time()
        if self._nonce and (now - self._nonce_time < 300):
            return self._nonce
        self._ensure_scraper()
        try:
            r = self._scraper.post(AJAX_URL, data={
                "action": "aipkit_get_frontend_chat_nonce",
                "bot_id": bot_id,
            })
            data = r.json()
            if data.get("success") and data.get("data", {}).get("nonce"):
                self._nonce = data["data"]["nonce"]
                self._nonce_time = now
                return self._nonce
        except Exception as exc:
            logger.warning("chatgptfree: nonce fetch failed: %s", exc)
        return "d3ab859b92"

    def cache_message(self, message: str, bot_id: str, nonce: str,
                      guest_uuid: str, conversation_uuid: str) -> Optional[str]:
        self._ensure_scraper()
        try:
            r = self._scraper.post(AJAX_URL, data={
                "action": "aipkit_cache_sse_message",
                "message": message,
                "_ajax_nonce": nonce,
                "bot_id": bot_id,
                "session_id": guest_uuid,
                "conversation_uuid": conversation_uuid,
                "post_id": "6",
            })
            data = r.json()
            if data.get("success") and data.get("data", {}).get("cache_key"):
                return data["data"]["cache_key"]
            logger.warning("chatgptfree: cache failed: %s", json.dumps(data)[:300])
        except Exception as exc:
            logger.warning("chatgptfree: cache error: %s", exc)
        return None

    def stream_url(self, cache_key: str, bot_id: str, nonce: str,
                   guest_uuid: str, conversation_uuid: str,
                   web_search: bool = False) -> str:
        from urllib.parse import urlencode
        params = {
            "action": "aipkit_frontend_chat_stream",
            "cache_key": cache_key,
            "bot_id": bot_id,
            "session_id": guest_uuid,
            "conversation_uuid": conversation_uuid,
            "post_id": "6",
            "_ajax_nonce": nonce,
            "_ts": str(int(time.time() * 1000)),
        }
        if web_search:
            params["frontend_web_search_active"] = "true"
        return f"{AJAX_URL}?{urlencode(params)}"

    @property
    def scraper(self):
        self._ensure_scraper()
        return self._scraper


class ChatGPTFreeProvider(BaseProvider):
    """
    Provider for ChatGPTFree.ai (AIPKit WordPress plugin).

    Uses cloudscraper to bypass Cloudflare, then WordPress AJAX with SSE streaming.
    Supports 8 bots: ChatGPT 5 Nano, Gemini, DeepSeek, Claude, Xai, Perplexity, Llama 4, Qwen 3.
    """

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        return [
            {
                "id": b["id"],
                "name": b["name"],
                "capabilities": {
                    "chat": True,
                    "stream": True,
                    "vision": False,
                    "reasoning": b.get("reasoning", False),
                    "tools": b.get("web_search", False),
                },
                "web_search": b.get("web_search", False),
                "provider_name": b.get("provider", ""),
            }
            for b in BOTS
        ]

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "",
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        logger.info("chatgptfree: generate_stream model=%s messages=%d", model, len(messages))

        bot_id = model or "25871"
        if bot_id not in BOT_ID_MAP:
            for b in BOTS:
                if b["name"].lower().replace(" ", "-") == bot_id.lower().replace(" ", "-"):
                    bot_id = b["id"]
                    break
            else:
                yield {"error": f"chatgptfree: unknown model '{model}'. Available: {list(BOT_ID_MAP.keys())}"}
                return

        bot_info = BOT_ID_MAP[bot_id]
        web_search = kwargs.get("web_search", bot_info.get("web_search", False))

        message_text = _parse_messages(messages)
        if not message_text.strip():
            yield {"error": "chatgptfree: no message content to send"}
            return

        session = _SessionManager.get_instance()
        nonce = session.get_nonce(bot_id)
        guest_uuid = str(uuid.uuid4())
        conversation_uuid = kwargs.get("conversation_uuid", str(uuid.uuid4()))

        cache_key = session.cache_message(
            message_text, bot_id, nonce, guest_uuid, conversation_uuid
        )
        if not cache_key:
            yield {"error": "chatgptfree: failed to cache message for streaming"}
            return

        stream_url = session.stream_url(
            cache_key, bot_id, nonce, guest_uuid, conversation_uuid,
            web_search=web_search,
        )

        has_content = False
        try:
            scraper = session.scraper
            r = scraper.get(stream_url, stream=True, timeout=REQUEST_TIMEOUT)

            if r.status_code != 200:
                error_text = r.text[:500] if hasattr(r, 'text') else f"HTTP {r.status_code}"
                yield {"error": f"chatgptfree: HTTP {r.status_code}: {error_text}"}
                return

            event_type = ""
            for line in r.iter_lines(decode_unicode=True):
                if not line:
                    continue

                if line.startswith("event:"):
                    event_type = line[6:].strip()
                    continue

                if line.startswith("data:"):
                    data_str = line[5:].strip()
                elif line.startswith(":"):
                    continue
                else:
                    continue

                if event_type == "error":
                    try:
                        err = json.loads(data_str)
                        yield {"error": f"chatgptfree: {err.get('error', err.get('message', data_str[:200]))}"}
                    except json.JSONDecodeError:
                        yield {"error": f"chatgptfree: {data_str[:200]}"}
                    return

                if event_type == "done":
                    break

                if event_type == "message_start":
                    try:
                        msg_data = json.loads(data_str)
                        msg_id = msg_data.get("message_id", "")
                        if msg_id:
                            yield {"message_id": msg_id}
                    except json.JSONDecodeError:
                        pass

                elif event_type == "status":
                    try:
                        status_data = json.loads(data_str)
                        if "delta" in status_data:
                            delta = status_data["delta"]
                            if delta:
                                has_content = True
                                yield {"text": delta}
                        elif "type" in status_data:
                            status_type = status_data["type"]
                            if status_type == "response.created":
                                resp_id = status_data.get("response_id", "")
                                if resp_id:
                                    yield {"response_id": resp_id}
                    except json.JSONDecodeError:
                        pass

                elif event_type == "openai_response_id":
                    try:
                        resp_data = json.loads(data_str)
                        yield {"openai_response_id": resp_data.get("id", "")}
                    except json.JSONDecodeError:
                        pass

        except Exception as exc:
            logger.exception("chatgptfree: stream error: %s", exc)
            yield {"error": f"chatgptfree: stream error: {exc}"}
            return

        yield {"is_final": True, "finish_reason": "stop"}