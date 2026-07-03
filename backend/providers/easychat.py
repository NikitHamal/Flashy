import asyncio
import base64
import hashlib
import json
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional

import aiohttp
import httpx

from .base import BaseProvider, ProviderType

logger = logging.getLogger("flashy.easychat")

URL = "https://chat3.eqing.tech"
BASE_URL = f"{URL}/api/openai/v1"
API_ENDPOINT = f"{BASE_URL}/chat/completions"
ALTCHA_CHALLENGE_URL = f"{URL}/api/altcaptcha/challenge"

FALLBACK_MODELS = [
    {"id": "gpt-5-free", "name": "GPT 5 Free"},
    {"id": "grok-4.1-fast-free", "name": "Grok 4.1 Fast Free"},
    {"id": "openrouter-free", "name": "OpenRouter Free"},
]

MODEL_ALIASES = {
    "gpt-5": "gpt-5-free",
    "grok-4.1-fast": "grok-4.1-fast-free",
    "grok": "grok-4.1-fast-free",
    "openrouter": "openrouter-free",
}

ALL_MODEL_IDS = [m["id"] for m in FALLBACK_MODELS] + list(MODEL_ALIASES.keys())


def _resolve_model(model: str) -> str:
    if model in MODEL_ALIASES:
        return MODEL_ALIASES[model]
    if model in [m["id"] for m in FALLBACK_MODELS]:
        return model
    return model


class EasyChatProvider(BaseProvider):
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.REVERSE_ENGINEERED

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(
                    f"{BASE_URL}/models",
                    headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    models_data = data if isinstance(data, list) else data.get("data", data.get("models", []))
                    if isinstance(models_data, list):
                        result = []
                        for m in models_data:
                            if isinstance(m, dict):
                                mid = m.get("name", "")
                                available = m.get("available", False)
                                role = m.get("role", "")
                                if available and role == "free":
                                    name = mid.replace("-free", "").replace("-", " ").title()
                                    result.append({
                                        "id": mid,
                                        "name": name,
                                        "capabilities": {"chat": True, "stream": True, "vision": False, "reasoning": "thinking" in mid, "tools": False},
                                    })
                        if result:
                            return result
            except Exception:
                pass
        return [
            {
                "id": m["id"],
                "name": m["name"],
                "capabilities": {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": False},
            }
            for m in FALLBACK_MODELS
        ]

    async def _solve_altcha(self, session: aiohttp.ClientSession) -> Optional[str]:
        try:
            async with session.get(
                ALTCHA_CHALLENGE_URL,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
                    "Accept": "application/json",
                },
                timeout=aiohttp.ClientTimeout(15),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()

            salt = data["salt"]
            challenge = data["challenge"]
            maxnumber = data["maxnumber"]
            algorithm = data["algorithm"]
            signature = data["signature"]

            for n in range(maxnumber + 1):
                text = f"{salt}{n}".encode("utf-8")
                if algorithm == "SHA-512":
                    h = hashlib.sha512(text).hexdigest()
                elif algorithm == "SHA-256":
                    h = hashlib.sha256(text).hexdigest()
                else:
                    raise ValueError(f"Unknown Altcha algorithm: {algorithm}")

                if h == challenge:
                    payload = {
                        "algorithm": algorithm,
                        "challenge": challenge,
                        "number": n,
                        "salt": salt,
                        "signature": signature,
                    }
                    token = base64.b64encode(json.dumps(payload).encode()).decode()
                    logger.debug("easychat: Altcha solved (n=%d)", n)
                    return token

            raise ValueError("Failed to solve Altcha")
        except Exception as exc:
            logger.warning("easychat: Altcha solve failed: %s", exc)
            return None

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "",
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        model = _resolve_model(model) if model else "gpt-5-free"

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(120)) as session:
            captcha_token = await self._solve_altcha(session)
            if not captcha_token:
                yield {"error": "easychat: failed to solve Altcha captcha"}
                return

            payload = {
                "model": model,
                "messages": messages,
                "stream": True,
                "captchaToken": captcha_token,
            }

            tools = kwargs.get("tools")
            if tools:
                payload["tools"] = tools
            tool_choice = kwargs.get("tool_choice")
            if tool_choice:
                payload["tool_choice"] = tool_choice

            temperature = kwargs.get("temperature")
            if temperature is not None:
                payload["temperature"] = temperature
            max_tokens = kwargs.get("max_tokens")
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            top_p = kwargs.get("top_p")
            if top_p is not None:
                payload["top_p"] = top_p

            headers = {
                "Accept": "text/event-stream",
                "Content-Type": "application/json",
                "Origin": URL,
                "Referer": f"{URL}/",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            }

            try:
                async with session.post(API_ENDPOINT, json=payload, headers=headers) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        yield {"error": f"easychat: HTTP {resp.status}: {body[:300]}"}
                        return

                    buffer = ""
                    tc_accumulators: dict = {}
                    async for raw_chunk in resp.content:
                        buffer += raw_chunk.decode("utf-8", errors="replace")
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.rstrip("\r")
                            if not line.startswith("data: "):
                                continue
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                if tc_accumulators:
                                    for idx in sorted(tc_accumulators):
                                        yield {"tool_call": dict(tc_accumulators[idx])}
                                    yield {"is_final": True, "finish_reason": "tool_calls"}
                                else:
                                    yield {"is_final": True, "finish_reason": "stop"}
                                return
                            try:
                                chunk = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue

                            choices = chunk.get("choices", [])
                            if not choices:
                                continue
                            delta = choices[0].get("delta", {})
                            finish = choices[0].get("finish_reason")

                            content = delta.get("content", "")
                            if content:
                                yield {"text": content}
                            reasoning = delta.get("reasoning_content", "") or delta.get("reasoning", "")
                            if reasoning:
                                yield {"thought": reasoning}

                            tool_calls_delta = delta.get("tool_calls")
                            if tool_calls_delta:
                                for tc in tool_calls_delta:
                                    idx = tc.get("index", 0)
                                    if idx not in tc_accumulators:
                                        tc_accumulators[idx] = {
                                            "id": tc.get("id", ""),
                                            "name": tc.get("function", {}).get("name", ""),
                                            "arguments": "",
                                        }
                                    acc = tc_accumulators[idx]
                                    if tc.get("id"):
                                        acc["id"] = tc["id"]
                                    fn = tc.get("function", {})
                                    if fn.get("name"):
                                        acc["name"] = fn["name"]
                                    if fn.get("arguments"):
                                        acc["arguments"] += fn["arguments"]

                            if finish == "tool_calls" or (finish == "stop" and tc_accumulators):
                                for idx in sorted(tc_accumulators):
                                    yield {"tool_call": dict(tc_accumulators[idx])}
                                usage = chunk.get("usage")
                                final = {"is_final": True, "finish_reason": "tool_calls"}
                                if usage:
                                    final["usage"] = {
                                        "prompt_tokens": usage.get("prompt_tokens", 0),
                                        "completion_tokens": usage.get("completion_tokens", 0),
                                        "total_tokens": usage.get("total_tokens", 0),
                                    }
                                yield final
                                return
                            elif finish:
                                yield {"is_final": True, "finish_reason": finish}
                                return

            except asyncio.TimeoutError:
                yield {"error": "easychat: request timed out"}
            except Exception as exc:
                logger.exception("easychat: error: %s", exc)
                yield {"error": f"easychat: {exc}"}
