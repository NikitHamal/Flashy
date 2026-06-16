"""
FreeGPT chat provider for Flashy.

Reverse-engineered from https://standalone.freegpt.win:3001/ (EasyChat v2.16.1,
based on ChatGPT-Next-Web, backed by OneAPI).

The site is a Next.js static export that proxies to a OneAPI backend.
It uses an OpenAI-compatible API with:

  - Chat endpoint: POST {base}/v1/chat/completions  (SSE streaming)
  - Models endpoint: GET  {base}/v1/models           (no auth required)
  - Auth: Bearer token with "nk-" prefix (shared access code)
  - Anti-bot: WASM PoW challenge headers (x-secure-*)
  - Cloudflare Turnstile for registration

WASM PoW challenge system:
  1. Fetch challenge from GET /api/challenge (with uuid + x-origin headers)
  2. Response: {challengeId, challenge, difficulty, issuedAt, expiresAt, version}
  3. Solve: find nonce N where SHA-256(challenge + N) starts with difficulty zero hex chars
  4. Send x-secure-* headers with chat requests

Access code auth:
  - The site requires a shared access code (entered by user in UI)
  - Sent as: Authorization: Bearer nk-{accessCode}
  - Without auth: 401 "未提供令牌" (no token provided)
  - The access code is a site-wide password, not per-user

Two routes available:
  - Domestic:  https://standalone.freegpt.win:3001
  - International: https://7fa179251cde.freegpt.tech
"""

import hashlib
import json
import logging
import secrets
import time
from typing import AsyncGenerator, Dict, Any, List, Optional

import httpx

from .base import BaseProvider

logger = logging.getLogger("flashy.freegpt")

DOMESTIC_BASE = "https://standalone.freegpt.win:3001"
INTERNATIONAL_BASE = "https://7fa179251cde.freegpt.tech"
DEFAULT_BASE = DOMESTIC_BASE
REQUEST_TIMEOUT = 120

POPULAR_MODELS = [
    {"id": "gpt-5-nano", "name": "GPT-5 Nano", "vision": False, "thinking": False},
    {"id": "gpt-5.4", "name": "GPT-5.4", "vision": False, "thinking": False},
    {"id": "gpt-5.4-nano", "name": "GPT-5.4 Nano", "vision": False, "thinking": False},
    {"id": "gpt-5.4-mini", "name": "GPT-5.4 Mini", "vision": False, "thinking": False},
    {"id": "gpt-4o", "name": "GPT-4o", "vision": True, "thinking": False},
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "vision": False, "thinking": False},
    {"id": "gpt-4.1", "name": "GPT-4.1", "vision": False, "thinking": False},
    {"id": "gpt-4.1-mini", "name": "GPT-4.1 Mini", "vision": False, "thinking": False},
    {"id": "gpt-4.1-nano", "name": "GPT-4.1 Nano", "vision": False, "thinking": False},
    {"id": "claude-sonnet-4-6", "name": "Claude Sonnet 4.6", "vision": True, "thinking": False},
    {"id": "claude-sonnet-4-6-thinking", "name": "Claude Sonnet 4.6 Thinking", "vision": True, "thinking": True},
    {"id": "claude-opus-4-6", "name": "Claude Opus 4.6", "vision": True, "thinking": False},
    {"id": "claude-opus-4-6-thinking", "name": "Claude Opus 4.6 Thinking", "vision": True, "thinking": True},
    {"id": "claude-haiku-4-5", "name": "Claude Haiku 4.5", "vision": True, "thinking": False},
    {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "vision": False, "thinking": False},
    {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "vision": False, "thinking": False},
    {"id": "deepseek-chat", "name": "DeepSeek Chat", "vision": False, "thinking": False},
    {"id": "deepseek-reasoner", "name": "DeepSeek Reasoner", "vision": False, "thinking": True},
    {"id": "grok-4.2", "name": "Grok 4.2", "vision": False, "thinking": False},
    {"id": "o3-mini", "name": "o3 Mini", "vision": False, "thinking": True},
    {"id": "o4-mini", "name": "o4 Mini", "vision": False, "thinking": True},
    {"id": "chatgpt-4o-latest", "name": "ChatGPT-4o Latest", "vision": True, "thinking": False},
    {"id": "gpt-5.5", "name": "GPT-5.5", "vision": False, "thinking": False},
    {"id": "gpt-5.5-pro", "name": "GPT-5.5 Pro", "vision": False, "thinking": False},
    {"id": "gpt-5-mini", "name": "GPT-5 Mini", "vision": False, "thinking": False},
    {"id": "gpt-5", "name": "GPT-5", "vision": False, "thinking": False},
    {"id": "kimi-k2.6", "name": "Kimi K2.6", "vision": False, "thinking": False},
    {"id": "kimi-k2.5", "name": "Kimi K2.5", "vision": False, "thinking": False},
    {"id": "qwen3.6-plus", "name": "Qwen 3.6 Plus", "vision": False, "thinking": False},
    {"id": "glm5", "name": "GLM-5", "vision": False, "thinking": False},
    {"id": "mimo-v2.5", "name": "MiMo V2.5", "vision": False, "thinking": False},
    {"id": "hunyuan-turbo", "name": "Hunyuan Turbo", "vision": False, "thinking": False},
    {"id": "moonshot-v1-128k", "name": "Moonshot V1 128K", "vision": False, "thinking": False},
    {"id": "gpt-image-2", "name": "GPT Image 2", "vision": True, "thinking": False},
    {"id": "flux", "name": "Flux", "vision": False, "thinking": False},
]


def _generate_uuid() -> str:
    shortid_chars = "123456789ABCDEFGHIJKLMNPQRSTUVWXYZ"
    now = time.localtime()
    date_str = f"{now.tm_year % 100:02d}{now.tm_mon:02d}{now.tm_mday:02d}"
    random_part = "".join(secrets.choice(shortid_chars) for _ in range(16))
    full = f"R5{date_str}{random_part}"
    checksum = sum(ord(c) for c in full) % 10
    return f"{full}{checksum}"


def _solve_pow(challenge: str, difficulty: int) -> tuple:
    nonce = 0
    target = "0" * difficulty
    while nonce < 10_000_000:
        payload = f"{challenge}{nonce}"
        h = hashlib.sha256(payload.encode()).hexdigest()
        if h.startswith(target):
            return nonce, h
        nonce += 1
    raise ValueError(f"Could not solve PoW with difficulty {difficulty}")


class FreeGPTProvider(BaseProvider):
    def __init__(self, access_code: str = "", base_url: str = ""):
        self.access_code = access_code
        self.base_url = base_url or DEFAULT_BASE
        self._uuid = _generate_uuid()
        self._challenge_cache = None
        self._challenge_ts = 0

    async def _get_pow_headers(self, client: httpx.AsyncClient, base_url: str = "") -> Dict[str, str]:
        now = time.time()
        if self._challenge_cache and now - self._challenge_ts < 240:
            return self._challenge_cache

        url = base_url or self.base_url
        try:
            resp = await client.get(
                f"{url}/api/challenge",
                headers={
                    "Accept": "application/json",
                    "uuid": self._uuid,
                    "x-origin": self.base_url,
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(f"Failed to get PoW challenge: {e}")
            return {}

        challenge = data["challenge"]
        difficulty = data["difficulty"]
        challenge_id = data["challengeId"]
        expires_at = str(data["expiresAt"])
        version = data["version"]

        nonce, hash_result = _solve_pow(challenge, difficulty)
        timestamp = str(int(time.time() * 1000))

        headers = {
            "x-secure-challenge-id": challenge_id,
            "x-secure-challenge-expires-at": expires_at,
            "x-secure-challenge-version": version,
            "x-secure-signature": hash_result,
            "x-secure-fingerprint": self._uuid,
            "x-secure-pow-seed-nonce": "0",
            "x-secure-pow-nonce": str(nonce),
            "x-secure-pow-hash": hash_result,
            "x-secure-pow-difficulty": str(difficulty),
            "x-secure-timestamp": timestamp,
            "x-secure-nonce": str(nonce),
            "x-secure-version": version,
        }

        self._challenge_cache = headers
        self._challenge_ts = now
        return headers

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        access_code = kwargs.get("access_code") or self.access_code
        base_url = kwargs.get("base_url") or self.base_url
        async with httpx.AsyncClient(verify=False, timeout=REQUEST_TIMEOUT) as client:
            headers = {
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
                "uuid": self._uuid,
                "x-origin": base_url,
                "model": model,
            }

            if access_code:
                headers["Authorization"] = f"Bearer nk-{access_code}"

            pow_headers = await self._get_pow_headers(client, base_url)
            headers.update(pow_headers)

            payload = {
                "messages": messages,
                "stream": True,
                "model": model,
            }

            temperature = kwargs.get("temperature")
            if temperature is not None:
                payload["temperature"] = temperature
            max_tokens = kwargs.get("max_tokens")
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            top_p = kwargs.get("top_p")
            if top_p is not None:
                payload["top_p"] = top_p

            async with client.stream(
                "POST",
                f"{base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                if resp.status_code == 401:
                    body = await resp.aread()
                    error_msg = body.decode("utf-8", errors="replace")
                    if not access_code:
                        yield {"error": "freegpt: access code required — configure freegpt_access_code in settings"}
                    else:
                        yield {"error": f"freegpt: invalid access code (401): {error_msg[:200]}"}
                    return
                if resp.status_code == 403:
                    body = await resp.aread()
                    error_msg = body.decode("utf-8", errors="replace")
                    yield {"error": f"freegpt: forbidden (403): {error_msg[:200]}"}
                    return
                if resp.status_code == 429:
                    yield {"error": "freegpt: rate limited (429). Please try again later."}
                    return
                if resp.status_code != 200:
                    body = await resp.aread()
                    error_msg = body.decode("utf-8", errors="replace")
                    yield {"error": f"freegpt: HTTP {resp.status_code}: {error_msg[:200]}"}
                    return

                buffer = ""
                async for line_bytes in resp.aiter_lines():
                    line = line_bytes.decode("utf-8", errors="replace")
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        return
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    choices = chunk.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield {"text": content}
                    reasoning = delta.get("reasoning_content", "")
                    if reasoning:
                        yield {"thinking": reasoning}

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(verify=False, timeout=30) as client:
            try:
                resp = await client.get(
                    f"{DEFAULT_BASE}/v1/models",
                    headers={"Accept": "application/json"},
                )
                resp.raise_for_status()
                data = resp.json()
                models = []
                for m in data.get("data", []):
                    mid = m.get("id", "")
                    mname = mid.replace("-", " ").replace("_", " ").title()
                    models.append({
                        "id": mid,
                        "name": mname,
                        "vision": any(v in mid.lower() for v in ["vision", "vl", "image", "-4o", "4.1", "opus", "sonnet"]),
                        "thinking": any(t in mid.lower() for t in ["thinking", "reasoner", "think"]),
                    })
                return models
            except Exception as e:
                logger.warning(f"Failed to fetch models: {e}")
                return POPULAR_MODELS