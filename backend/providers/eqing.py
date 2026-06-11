"""
EasyChat / eqing.tech chat provider for Flashy.

Reverse-engineered from https://chat3.eqing.tech/ (EasyChat v2.10.11, based on ChatGPT-Next-Web).

The site is a Next.js app that proxies to a Go backend at easy-api-eo.llm99.com.
It uses an OpenAI-compatible API with:

  - Chat endpoint: POST {apiHost}/v1/chat/completions  (SSE streaming)
  - Models endpoint: GET  {apiHost}/v1/models
  - Auth: guest ID header (x-guest-id) or Supabase Bearer token
  - Captcha: altcha proof-of-work (captchaToken in request body)
  - Anti-abuse: guest ID tracking, rate limiting (429)

Streaming format: OpenAI SSE (data: {"choices":[{"delta":{"content":"..."}}]})
  Plus custom events: [JSON], [ADD], [ORIGIN], [CALLBACK]
  [CALLBACK] CLEAR-CAPTCHA-TOKEN resets the captcha token

Altcha PoW captcha:
  1. Fetch challenge from {apiHost}/v1/altcha (GET)
  2. Challenge: {"algorithm":"SHA-256","challenge":"...","salt":"...","signature":"..."}
  3. Solve: find nonce N where SHA-256(salt + N) starts with challenge prefix
  4. Solution: base64(JSON({algorithm,challenge,salt,signature,nonce}))
  5. Send solution as captchaToken in chat request body
"""

import base64
import hashlib
import json
import logging
import secrets
import time
from typing import AsyncGenerator, Dict, Any, List, Optional

import httpx

from .base import BaseProvider

logger = logging.getLogger("flashy.eqing")

API_BASE = "https://easy-api-eo.llm99.com"
SITE_URL = "https://chat3.eqing.tech"
REQUEST_TIMEOUT = 120

FREE_MODELS = [
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "vision": False, "thinking": False},
    {"id": "gpt-4o-mini-image-free", "name": "GPT-4o Mini Vision", "vision": True, "thinking": False},
    {"id": "gpt-5-free", "name": "GPT-5 Free", "vision": False, "thinking": False},
    {"id": "grok-4.1-fast-free", "name": "Grok 4.1 Fast", "vision": False, "thinking": False},
    {"id": "openrouter-free", "name": "OpenRouter Free", "vision": False, "thinking": False},
    {"id": "gemini-3-flash", "name": "Gemini 3 Flash", "vision": False, "thinking": False},
    {"id": "code-claude-3.5-sonnet-free", "name": "Claude 3.5 Sonnet Free", "vision": True, "thinking": False},
    {"id": "code-claude-3-opus", "name": "Claude 3 Opus Free", "vision": True, "thinking": False},
]

VIP_MODELS = [
    {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "vision": False, "thinking": False},
    {"id": "claude-3.5-sonnet", "name": "Claude 3.5 Sonnet", "vision": True, "thinking": False},
    {"id": "gpt-4o-all", "name": "GPT-4o All", "vision": False, "thinking": False},
    {"id": "gpt-4-all", "name": "GPT-4 All", "vision": True, "thinking": False},
    {"id": "yi-lightning", "name": "Yi Lightning", "vision": False, "thinking": False},
    {"id": "o1-mini", "name": "o1 Mini", "vision": False, "thinking": True},
    {"id": "g-0S5FXLyFN", "name": "G Custom", "vision": True, "thinking": False},
]

SVIP_MODELS = [
    {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "vision": True, "thinking": False},
    {"id": "gpt-4o", "name": "GPT-4o", "vision": True, "thinking": False},
    {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "vision": True, "thinking": False},
]

NEW_MODELS = [
    {"id": "gpt-5-3-all", "name": "GPT-5.3 All", "vision": False, "thinking": False},
    {"id": "gpt-5-2-all", "name": "GPT-5.2 All", "vision": False, "thinking": False},
    {"id": "gpt-5-3-image", "name": "GPT-5.3 Image", "vision": True, "thinking": False},
    {"id": "claude-sonnet-4-6-thinking", "name": "Claude Sonnet 4.6 Thinking", "vision": False, "thinking": True},
    {"id": "claude-opus-4-6-thinking", "name": "Claude Opus 4.6 Thinking", "vision": False, "thinking": True},
    {"id": "gemini-3.1-pro", "name": "Gemini 3.1 Pro", "vision": False, "thinking": False},
    {"id": "gpt-5-2-thinking", "name": "GPT-5.2 Thinking", "vision": False, "thinking": True},
    {"id": "gpt-5-2-thinking-extended", "name": "GPT-5.2 Thinking Ext", "vision": False, "thinking": True},
    {"id": "gpt-5-2-thinking-max", "name": "GPT-5.2 Thinking Max", "vision": False, "thinking": True},
    {"id": "gpt-5-4-thinking", "name": "GPT-5.4 Thinking", "vision": False, "thinking": True},
    {"id": "gpt-5-4-thinking-extended", "name": "GPT-5.4 Thinking Ext", "vision": False, "thinking": True},
    {"id": "gpt-5-4-thinking-max", "name": "GPT-5.4 Thinking Max", "vision": False, "thinking": True},
    {"id": "gpt-5-5-thinking", "name": "GPT-5.5 Thinking", "vision": False, "thinking": True},
    {"id": "gpt-5-5-thinking-extended", "name": "GPT-5.5 Thinking Ext", "vision": False, "thinking": True},
    {"id": "gpt-5-5-thinking-max", "name": "GPT-5.5 Thinking Max", "vision": False, "thinking": True},
    {"id": "gpt-5.5(xhigh)", "name": "GPT-5.5 xHigh", "vision": False, "thinking": False},
    {"id": "gpt-5.3-codex(xhigh)", "name": "GPT-5.3 Codex xHigh", "vision": False, "thinking": False},
    {"id": "gpt-5.2(high)", "name": "GPT-5.2 High", "vision": False, "thinking": False},
    {"id": "o3", "name": "o3", "vision": False, "thinking": True},
]

ALL_MODELS = FREE_MODELS + VIP_MODELS + SVIP_MODELS + NEW_MODELS
_THINKING_MODELS = set(m["id"] for m in ALL_MODELS if m.get("thinking"))


def _generate_guest_id() -> str:
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(secrets.choice(chars) for _ in range(24))


def _is_thinking_model(model: str) -> bool:
    return model in _THINKING_MODELS or "thinking" in model.lower() or "deepseek-r" in model.lower()


def _solve_altcha_challenge(challenge_data: dict, max_iterations: int = 1000000) -> Optional[str]:
    algorithm = challenge_data.get("algorithm", "SHA-256")
    challenge = challenge_data.get("challenge", "")
    salt = challenge_data.get("salt", "")
    signature = challenge_data.get("signature", "")

    if not challenge or not salt:
        logger.warning("eqing: altcha challenge missing required fields")
        return None

    if algorithm != "SHA-256":
        logger.warning("eqing: unsupported altcha algorithm: %s", algorithm)
        return None

    for nonce in range(max_iterations):
        message = f"{salt}{nonce}"
        hash_result = hashlib.sha256(message.encode()).hexdigest()
        if hash_result.startswith(challenge):
            solution = {
                "algorithm": algorithm,
                "challenge": challenge,
                "salt": salt,
                "signature": signature,
                "nonce": nonce,
            }
            return base64.b64encode(json.dumps(solution).encode()).decode()

    logger.warning("eqing: altcha challenge not solved within %d iterations", max_iterations)
    return None


class EQingProvider(BaseProvider):
    """Provider for EasyChat / eqing.tech (https://chat3.eqing.tech/)."""

    def __init__(self):
        self._guest_id = _generate_guest_id()
        self._captcha_token: Optional[str] = None
        self._captcha_token_time: float = 0
        self._captcha_token_ttl: float = 300

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(
                    f"{API_BASE}/v1/models",
                    headers={
                        "Content-Type": "application/json",
                        "x-requested-with": "XMLHttpRequest",
                        "x-guest-id": _generate_guest_id(),
                    },
                )
                if r.status_code == 200:
                    data = r.json()
                    models = data.get("data", [])
                    locked_ids = (
                        set(m["id"] for m in VIP_MODELS)
                        | set(m["id"] for m in SVIP_MODELS)
                        | set(m["id"] for m in NEW_MODELS)
                    )
                    return [
                        {
                            "id": m.get("id", ""),
                            "name": m.get("id", ""),
                            "capabilities": {
                                "chat": True,
                                "stream": True,
                                "vision": any(
                                    v in m.get("id", "").lower()
                                    for v in ["image", "vision", "4o", "gpt-5-3-image"]
                                ),
                                "reasoning": _is_thinking_model(m.get("id", "")),
                                "tools": False,
                            },
                            "locked": m.get("id", "") in locked_ids,
                        }
                        for m in models
                    ]
        except Exception as exc:
            logger.warning("eqing: failed to fetch models: %s", exc)

        return [
            {
                "id": m["id"],
                "name": m["name"],
                "capabilities": {
                    "chat": True,
                    "stream": True,
                    "vision": m.get("vision", False),
                    "reasoning": m.get("thinking", False),
                    "tools": False,
                },
                "locked": m in VIP_MODELS or m in SVIP_MODELS or m in NEW_MODELS,
            }
            for m in ALL_MODELS
        ]

    async def _fetch_captcha_token(self, client: httpx.AsyncClient) -> Optional[str]:
        if self._captcha_token and (time.time() - self._captcha_token_time) < self._captcha_token_ttl:
            return self._captcha_token

        try:
            r = await client.get(
                f"{API_BASE}/v1/altcha",
                headers={
                    "Accept": "application/json",
                    "x-requested-with": "XMLHttpRequest",
                    "x-guest-id": self._guest_id,
                },
            )
            if r.status_code != 200:
                logger.warning("eqing: altcha challenge failed with status %d", r.status_code)
                return self._captcha_token

            content_type = r.headers.get("content-type", "")
            if "json" not in content_type:
                logger.warning("eqing: altcha challenge returned non-JSON: %s", content_type)
                return self._captcha_token

            challenge_data = r.json()
            token = _solve_altcha_challenge(challenge_data)
            if token:
                self._captcha_token = token
                self._captcha_token_time = time.time()
                return token

        except Exception as exc:
            logger.warning("eqing: altcha challenge error: %s", exc)

        return self._captcha_token

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "",
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        logger.info("eqing: generate_stream model=%s messages=%d", model, len(messages))

        if not model:
            model = "gpt-4o-mini"

        headers = {
            "Content-Type": "application/json",
            "x-requested-with": "XMLHttpRequest",
            "x-guest-id": self._guest_id,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Origin": SITE_URL,
            "Referer": f"{SITE_URL}/",
        }

        openai_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                content = "\n".join(text_parts)
            openai_messages.append({"role": role, "content": content})

        body: Dict[str, Any] = {
            "model": model,
            "messages": openai_messages,
            "stream": True,
        }

        if not _is_thinking_model(model):
            body["temperature"] = kwargs.get("temperature", 0.5)
            body["presence_penalty"] = kwargs.get("presence_penalty", 0)
            body["frequency_penalty"] = kwargs.get("frequency_penalty", 0)
            body["top_p"] = kwargs.get("top_p", 1)

        if kwargs.get("max_tokens"):
            body["max_tokens"] = kwargs["max_tokens"]

        total_chars = sum(
            len(m.get("content", ""))
            for m in openai_messages
            if isinstance(m.get("content"), str)
        )
        body["chat_token"] = max(1, total_chars // 4)

        has_content = False
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
                captcha_token = await self._fetch_captcha_token(client)
                if captcha_token:
                    body["captchaToken"] = captcha_token

                async with client.stream(
                    "POST",
                    f"{API_BASE}/v1/chat/completions",
                    json=body,
                    headers=headers,
                ) as resp:
                    if resp.status_code == 403:
                        error_body = await resp.aread()
                        try:
                            error_data = json.loads(error_body.decode("utf-8", errors="replace"))
                            msg = error_data.get("message", "")
                            choices = error_data.get("choices", [])
                            if choices and choices[0].get("message", {}).get("content"):
                                msg = choices[0]["message"]["content"]
                            callback = error_data.get("callback", "")
                            if callback == "CLEAR-CAPTCHA-TOKEN":
                                self._captcha_token = None
                                self._captcha_token_time = 0
                            if msg:
                                yield {"error": f"eqing: 403: {msg}"}
                            else:
                                yield {"error": f"eqing: 403 Forbidden — API may require login or captcha has changed"}
                        except (json.JSONDecodeError, ValueError):
                            yield {"error": f"eqing: 403 Forbidden — API may require login or captcha has changed"}
                        return

                    if resp.status_code == 429:
                        yield {"error": "eqing: rate limited (429), please try again later"}
                        return

                    if resp.status_code != 200:
                        error_body = await resp.aread()
                        yield {"error": f"eqing: HTTP {resp.status_code}: {error_body.decode('utf-8', errors='replace')[:300]}"}
                        return

                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue

                        if line.startswith("event: "):
                            event_type = line[7:].strip()
                            if event_type == "[CALLBACK]":
                                async for nl in resp.aiter_lines():
                                    nl = nl.strip()
                                    if nl.startswith("data: "):
                                        callback_data = nl[6:].strip()
                                        if callback_data == "CLEAR-CAPTCHA-TOKEN":
                                            self._captcha_token = None
                                            self._captcha_token_time = 0
                                    break
                            continue

                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break

                            try:
                                data = json.loads(data_str)
                            except (json.JSONDecodeError, ValueError):
                                continue

                            choices = data.get("choices", [])
                            if not choices:
                                callback = data.get("callback")
                                if callback == "CLEAR-CAPTCHA-TOKEN":
                                    self._captcha_token = None
                                    self._captcha_token_time = 0
                                continue

                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            reasoning = delta.get("reasoning_content", "")

                            if reasoning:
                                has_content = True
                                yield {"text": f"\n"}

                            if content:
                                has_content = True
                                yield {"text": content}

        except httpx.TimeoutException:
            yield {"error": "eqing: request timed out"}
            return
        except Exception as exc:
            logger.exception("eqing: stream error: %s", exc)
            yield {"error": f"eqing: stream error: {exc}"}
            return

        yield {"is_final": True, "finish_reason": "stop"}