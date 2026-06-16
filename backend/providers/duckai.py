import json
import logging
import time
import ssl
from typing import AsyncGenerator, Dict, Any, List, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from .base import BaseProvider
from ..vqd_helper import compute_vqd

logger = logging.getLogger("flashy.duckai")

MODELS = [
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "vision": False, "thinking": False},
    {"id": "gpt-5-mini", "name": "GPT-5 Mini", "vision": False, "thinking": False},
    {"id": "claude-3-5-haiku-latest", "name": "Claude 3.5 Haiku", "vision": False, "thinking": False},
    {"id": "meta-llama/Llama-4-Scout-17B-16E-Instruct", "name": "Llama 4 Scout 17B", "vision": False, "thinking": False},
    {"id": "mistralai/Mistral-Small-24B-Instruct-2501", "name": "Mistral Small 24B", "vision": False, "thinking": False},
    {"id": "openai/gpt-oss-120b", "name": "GPT-OSS 120B", "vision": False, "thinking": False},
]

DDG_BASE = "https://duckduckgo.com"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
X_FE_VERSION = "serp_20250401_100419_ET-19d438eb199b2bf7c300"
_VQD_CACHE = {"hash": "", "token": "", "expires": 0}


def _get_vqd():
    now = time.time()
    if _VQD_CACHE["token"] and _VQD_CACHE["expires"] > now:
        return _VQD_CACHE["token"]
    ctx = ssl.create_default_context()
    req = Request(
        f"{DDG_BASE}/duckchat/v1/status",
        headers={"accept": "*/*", "x-vqd-accept": "1", "user-agent": USER_AGENT},
        method="GET",
    )
    resp = urlopen(req, context=ctx, timeout=15)
    raw_hash = resp.headers.get("x-Vqd-hash-1", "")
    if not raw_hash:
        raise RuntimeError("No VQD hash in response")
    token = compute_vqd(raw_hash, USER_AGENT)
    _VQD_CACHE["hash"] = raw_hash
    _VQD_CACHE["token"] = token
    _VQD_CACHE["expires"] = now + 120
    return token


class DuckAIProvider(BaseProvider):

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        return [
            {"id": m["id"], "name": m["name"],
             "capabilities": {"chat": True, "stream": True, "vision": m.get("vision", False),
                              "thinking": m.get("thinking", False), "tools": True}}
            for m in MODELS
        ]

    async def generate_stream(
        self, messages: List[Dict[str, str]], model: str = "gpt-4o-mini", **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        logger.info("duckai: generate_stream model=%s messages=%d", model, len(messages))
        if not model:
            model = "gpt-4o-mini"

        try:
            vqd_token = _get_vqd()
        except Exception as e:
            yield {"error": f"duckai: VQD failed: {e}"}
            return

        body = json.dumps({"model": model, "messages": messages}).encode()
        ctx = ssl.create_default_context()
        req = Request(
            f"{DDG_BASE}/duckchat/v1/chat",
            headers={
                "accept": "text/event-stream",
                "content-type": "application/json",
                "x-vqd-hash-1": vqd_token,
                "x-fe-version": X_FE_VERSION,
                "user-agent": USER_AGENT,
            },
            data=body, method="POST",
        )
        try:
            resp = urlopen(req, context=ctx, timeout=180)
        except HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")[:500]
            yield {"error": f"duckai: HTTP {e.code}: {error_body}"}
            return

        text = resp.read().decode("utf-8")
        for line in text.split("\n"):
            line = line.strip()
            if not line or not line.startswith("data: "):
                continue
            data_str = line[6:]
            try:
                chunk = json.loads(data_str)
            except (json.JSONDecodeError, ValueError):
                continue
            if chunk.get("action") == "error":
                yield {"error": f"duckai: {json.dumps(chunk)}"}
                return
            msg = chunk.get("message", "")
            if msg:
                yield {"text": msg}

        yield {"is_final": True, "finish_reason": "stop"}
