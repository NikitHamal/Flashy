import json
import logging
import itertools
from typing import AsyncGenerator, Dict, Any, List, Optional
import aiohttp
from .base import BaseProvider, ProviderType

logger = logging.getLogger("flashy.atomesus")

MODELS = [
    {"id": "cipher", "name": "Cipher", "capabilities": {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": False}, "context_window": 130024, "max_output": 16384},
]


class AtomesusProvider(BaseProvider):
    """Atomesus provider with round-robin multi-key routing.

    Pass multiple API keys comma-separated (e.g. "key1,key2,key3") in the
    ``api_keys`` constructor argument or ``atomesus_api_keys`` config key.
    Each request picks the next key in rotation.
    """

    def __init__(self, api_keys: str = "", base_url: str = "https://api.atomesus.com"):
        self.base_url = base_url.rstrip("/")
        keys = [k.strip() for k in api_keys.split(",") if k.strip()]
        if not keys:
            keys = [""]
        self._key_cycle = itertools.cycle(keys)

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OPENAI_COMPATIBLE

    def _next_key(self) -> str:
        return next(self._key_cycle)

    async def generate_stream(
        self, messages: List[Dict[str, str]], model: str, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        if not model:
            model = "cipher"

        api_key = kwargs.get("api_key") or self._next_key()
        base_url = self.base_url.rstrip("/")
        url = f"{base_url}/v1/chat/completions"

        # Strip system messages — Atomesus gateway ignores them and
        # may reject if present.
        filtered = [m for m in messages if m.get("role") != "system"]

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {api_key}",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        payload = {
            "model": model,
            "messages": filtered,
            "stream": True,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 16384),
            "top_p": kwargs.get("top_p", 1.0),
        }

        tools = kwargs.get("tools")
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = kwargs.get("tool_choice", "auto")

        logger.info("[ATOMESUS] generate_stream | model=%s | messages=%d | keys=%s", model, len(messages), self._key_count())

        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.post(url, json=payload) as stream_resp:
                    if stream_resp.status != 200:
                        try:
                            error_text = await stream_resp.text()
                        except Exception:
                            error_text = "(no error body)"
                        logger.error("[ATOMESUS] Error %d: %s", stream_resp.status, error_text[:500])
                        yield {"error": f"Atomesus Error {stream_resp.status}: {error_text[:500]}"}
                        return

                    buffer = ""
                    tool_calls_acc: Dict[int, Dict] = {}
                    pending_finish: Optional[str] = None
                    pending_usage: Optional[Dict[str, Any]] = None
                    raw_chunk_count = 0

                    async for chunk_bytes in stream_resp.content.iter_any():
                        buffer += chunk_bytes.decode("utf-8", errors="ignore")

                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()

                            if not line:
                                continue

                            if line == "data: [DONE]":
                                if pending_finish:
                                    final_event = {"is_final": True, "finish_reason": pending_finish}
                                    if pending_usage:
                                        final_event["usage"] = pending_usage
                                    yield final_event
                                    pending_finish = None
                                continue

                            if line.startswith("data: "):
                                try:
                                    data = json.loads(line[6:])
                                    raw_chunk_count += 1
                                    choices = data.get("choices", [])
                                    usage_data = data.get("usage")

                                    if usage_data:
                                        pending_usage = usage_data

                                    if choices:
                                        choice = choices[0]
                                        delta = choice.get("delta", {})
                                        content = delta.get("content")
                                        reasoning = delta.get("reasoning_content") or delta.get("reasoning")
                                        finish_reason = choice.get("finish_reason")
                                        delta_tool_calls = delta.get("tool_calls")

                                        if delta_tool_calls:
                                            for tc_delta in delta_tool_calls:
                                                idx = tc_delta.get("index", 0)
                                                if idx not in tool_calls_acc:
                                                    tool_calls_acc[idx] = {"id": "", "function": {"name": "", "arguments": ""}}
                                                acc = tool_calls_acc[idx]
                                                if tc_delta.get("id"):
                                                    acc["id"] = tc_delta["id"]
                                                fn = tc_delta.get("function", {})
                                                if fn.get("name"):
                                                    acc["function"]["name"] += fn["name"]
                                                if fn.get("arguments"):
                                                    acc["function"]["arguments"] += fn["arguments"]

                                        if reasoning:
                                            yield {"thought": reasoning}
                                        elif content:
                                            yield {"text": content}

                                        if finish_reason:
                                            if tool_calls_acc:
                                                for tidx in sorted(tool_calls_acc.keys()):
                                                    tc = tool_calls_acc[tidx]
                                                    yield {"tool_call": {"id": tc.get("id") or f"call_{tidx}", "name": tc.get("function", {}).get("name", ""), "arguments": tc.get("function", {}).get("arguments", "{}")}}
                                                tool_calls_acc = {}
                                            pending_finish = finish_reason

                                except json.JSONDecodeError:
                                    pass

                    if pending_finish:
                        final_event = {"is_final": True, "finish_reason": pending_finish}
                        if pending_usage:
                            final_event["usage"] = pending_usage
                        yield final_event

            except Exception as e:
                logger.exception("[ATOMESUS] Error: %s", e)
                yield {"error": f"Atomesus Error: {str(e)}"}

    def _key_count(self) -> int:
        """Return the number of configured API keys (for logging)."""
        import os
        raw = os.environ.get("ATOMESUS_API_KEYS", "") or os.environ.get("atomesus_api_keys", "")
        if not raw:
            return 1
        return len([k for k in raw.split(",") if k.strip()])

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        return list(MODELS)
