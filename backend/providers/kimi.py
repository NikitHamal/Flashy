import asyncio
import json
import logging
import struct
import time
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

from curl_cffi.requests import AsyncSession

from .base import BaseProvider

logger = logging.getLogger("flashy.kimi")

MODELS = [
    {"id": "kimi-k2.5", "name": "Kimi K2.5", "context_window": 128000},
]

KIMI_HEADERS = {
    "Content-Type": "application/connect+json",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Origin": "https://www.kimi.com",
    "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not A Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Priority": "u=1, i",
    "R-Timezone": "Asia/Shanghai",
    "X-Msh-Platform": "web",
    "Connect-Protocol-Version": "1",
}


def _encode_grpc_web(payload: bytes) -> bytes:
    return bytes([0x00]) + struct.pack(">I", len(payload)) + payload


def _decode_grpc_web(data: bytes):
    messages = []
    pos = 0
    while pos < len(data):
        if pos + 5 > len(data):
            break
        flag = data[pos]
        length = struct.unpack(">I", data[pos + 1:pos + 5])[0]
        pos += 5
        if pos + length > len(data):
            break
        messages.append(data[pos:pos + length])
        pos += length
    return messages


def _messages_to_kimi_text(messages: List[Dict[str, str]]) -> str:
    parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if not content:
            continue
        if role == "system":
            parts.append(f"system: {content}")
        elif role == "assistant":
            parts.append(f"assistant: {content}")
        elif role == "user":
            parts.append(f"user: {content}")
    return "\n".join(parts)


_token_cache: Dict[str, dict] = {}


class KimiProvider(BaseProvider):
    """Kimi (Moonshot K2.5) Web API provider."""

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        return [{"id": m["id"], "name": m["name"]} for m in MODELS]

    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        token = kwargs.get("token") or kwargs.get("kimi_token", "")
        if not token:
            yield {"type": "error", "error": "Kimi requires a token. Set kimi_token in config."}
            return

        access_token = await self._get_access_token(token)
        if not access_token:
            yield {"type": "error", "error": "Failed to acquire Kimi access token"}
            return

        chat_id = kwargs.get("session_id") or ""
        text = _messages_to_kimi_text(messages)
        if not text.strip():
            yield {"type": "error", "error": "No user message found"}
            return

        payload = {
            "scenario": "SCENARIO_K2D5",
            "chat_id": chat_id,
            "tools": [{"type": "TOOL_TYPE_SEARCH", "search": {}}],
            "message": {
                "parent_id": "",
                "role": "user",
                "blocks": [{"message_id": str(uuid.uuid4()), "text": {"content": text}}],
                "scenario": "SCENARIO_K2D5",
            },
            "options": {"thinking": "r1" in model.lower() or "think" in model.lower()},
        }

        payload_bytes = _encode_grpc_web(json.dumps(payload).encode("utf-8"))
        headers = {**KIMI_HEADERS, "Authorization": f"Bearer {access_token}"}
        headers["X-Msh-Device-Id"] = str(uuid.uuid4())
        headers["X-Msh-Session-Id"] = str(uuid.uuid4())

        try:
            async with AsyncSession(impersonate="chrome") as session:
                resp = await session.post(
                    "https://www.kimi.com/apiv2/kimi.gateway.chat.v1.ChatService/Chat",
                    headers=headers,
                    data=payload_bytes,
                    timeout=120,
                )

                if resp.status_code == 401:
                    yield {"type": "error", "error": "Kimi token invalid or expired"}
                    return
                if resp.status_code != 200:
                    logger.error(f"[KIMI] Non-200 response: {resp.status_code} - {resp.text[:500]}")
                    yield {"type": "error", "error": f"Kimi error: {resp.status_code} - {resp.text[:200]}"}
                    return

                decoded = _decode_grpc_web(resp.content)
                has_content = False
                for msg_bytes in decoded:
                    try:
                        data = json.loads(msg_bytes)
                    except json.JSONDecodeError:
                        continue

                    if data.get("error"):
                        yield {"type": "error", "error": str(data["error"])}
                        return

                    block = data.get("block", {})
                    text_content = ""
                    if isinstance(block, dict):
                        text_obj = block.get("text", {})
                        if isinstance(text_obj, dict):
                            text_content = text_obj.get("content", "")

                    mask = data.get("mask", "")
                    if text_content:
                        has_content = True
                        if "think" in mask.lower() or (isinstance(block, dict) and block.get("text", {}).get("flags") == "thinking"):
                            yield {"type": "thought", "thought": text_content}
                        else:
                            yield {"type": "text", "text": text_content}

                    if data.get("done"):
                        break

                if not has_content:
                    logger.warning(f"[KIMI] No content in response. Raw bytes: {resp.content[:500]}")
                    yield {"type": "error", "error": "Kimi returned no content. The token may be invalid."}

                yield {"type": "final", "finish_reason": "stop", "is_final": True}

        except Exception as e:
            logger.error(f"Kimi error: {e}")
            yield {"type": "error", "error": str(e)}

    async def _get_access_token(self, token: str) -> Optional[str]:
        cache_key = token[:16]
        cached = _token_cache.get(cache_key)
        if cached and cached["expires_at"] > time.time():
            return cached["access_token"]

        if token.startswith("eyJ"):
            _token_cache[cache_key] = {"access_token": token, "expires_at": time.time() + 300}
            return token

        return token