import hashlib
import json
import logging
import time
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

from curl_cffi.requests import AsyncSession

from .base import BaseProvider

logger = logging.getLogger("flashy.glm")

MODELS = [
    {"id": "glm-5", "name": "GLM-5", "context_window": 128000},
]

GLM_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "text/event-stream",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "App-Name": "chatglm",
    "Cache-Control": "no-cache",
    "Origin": "https://chatglm.cn",
    "Pragma": "no-cache",
    "Priority": "u=1, i",
    "Sec-Ch-Ua": '"Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "X-App-Fr": "browser_extension",
    "X-App-Platform": "pc",
    "X-App-Version": "0.0.1",
    "X-Device-Brand": "",
    "X-Device-Model": "",
    "X-Lang": "zh",
}

SIGN_SECRET = "8a1317a7468aa3ad86e997d08f3f31cb"

_token_cache: Dict[str, dict] = {}


def _generate_sign(timestamp: str, nonce: str) -> str:
    raw = f"{timestamp}-{nonce}-{SIGN_SECRET}"
    return hashlib.md5(raw.encode()).hexdigest()


class GLMProvider(BaseProvider):
    """GLM (Zhipu Qingyan) Web API provider."""

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        return [{"id": m["id"], "name": m["name"]} for m in MODELS]

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        refresh_token = kwargs.get("token") or kwargs.get("glm_refresh_token", "")
        if not refresh_token:
            yield {"type": "error", "error": "GLM requires a refresh token. Set glm_refresh_token in config."}
            return

        access_token = await self._get_access_token(refresh_token)
        if not access_token:
            yield {"type": "error", "error": "Failed to acquire GLM access token"}
            return

        chat_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if not content:
                continue
            if role == "system":
                chat_messages.append({"role": "user", "content": [{"type": "text", "text": content}]})
                chat_messages.append({"role": "assistant", "content": [{"type": "text", "text": "Understood."}]})
            else:
                chat_messages.append({"role": role, "content": [{"type": "text", "text": content}]})

        if not chat_messages:
            yield {"type": "error", "error": "No user message found"}
            return

        timestamp = str(int(time.time() * 1000))
        nonce = str(uuid.uuid4())
        sign = _generate_sign(timestamp, nonce)

        body = {
            "assistant_id": "65940acff94777010aa6b796",
            "conversation_id": "",
            "project_id": "",
            "chat_type": "user_chat",
            "messages": chat_messages,
            "meta_data": {
                "channel": "",
                "chat_mode": "zero",
                "draft_id": "",
                "if_plus_model": True,
                "input_question_type": "xxxx",
                "is_networking": False,
                "is_test": False,
                "platform": "pc",
                "quote_log_id": "",
                "cogview": {"rm_label_watermark": False},
            },
        }

        headers = {
            **GLM_HEADERS,
            "Authorization": f"Bearer {access_token}",
            "X-Device-Id": str(uuid.uuid4()),
            "X-Request-Id": str(uuid.uuid4()),
            "X-Sign": sign,
            "X-Timestamp": timestamp,
            "X-Nonce": nonce,
        }

        try:
            async with AsyncSession(impersonate="chrome") as session:
                resp = await session.post(
                    "https://chatglm.cn/chatglm/backend-api/assistant/stream",
                    headers=headers,
                    json=body,
                    timeout=120,
                )

                if resp.status_code == 401:
                    yield {"type": "error", "error": "GLM token invalid or expired"}
                    return
                if resp.status_code != 200:
                    logger.error(f"[GLM] Non-200 response: {resp.status_code} - {resp.text[:500]}")
                    yield {"type": "error", "error": f"GLM error: {resp.status_code} - {resp.text[:200]}"}
                    return

                has_content = False

                for line in resp.text.split("\n"):
                    line = line.strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    parts = data.get("parts", [])
                    for part in parts:
                        for content_item in part.get("content", []):
                            content_type = content_item.get("type", "")
                            text = content_item.get("text", "")
                            if content_type == "think" and text:
                                has_content = True
                                yield {"type": "thought", "thought": text}
                            elif content_type == "text" and text:
                                has_content = True
                                yield {"type": "text", "text": text}

                    if data.get("status") in ("finish", "intervene"):
                        break

                if not has_content:
                    logger.warning(f"[GLM] No content in response. First 500 chars: {resp.text[:500]}")
                    yield {"type": "error", "error": "GLM returned no content. The token may be invalid or expired."}

                yield {"type": "final", "finish_reason": "stop", "is_final": True}

        except Exception as e:
            logger.error(f"GLM error: {e}")
            yield {"type": "error", "error": str(e)}

    async def _get_access_token(self, refresh_token: str) -> Optional[str]:
        cache_key = refresh_token[:16]
        cached = _token_cache.get(cache_key)
        if cached and cached["expires_at"] > time.time():
            return cached["access_token"]

        try:
            async with AsyncSession(impersonate="chrome") as session:
                resp = await session.post(
                    "https://chatglm.cn/chatglm/user-api/user/refresh",
                    headers={**GLM_HEADERS, "Authorization": f"Bearer {refresh_token}"},
                    json={},
                    timeout=30,
                )
                if resp.status_code != 200:
                    logger.error(f"GLM token refresh error: {resp.status_code}")
                    return None

                data = resp.json()
                result = data.get("result", {})
                access_token = result.get("access_token", "")
                new_refresh_token = result.get("refresh_token", "")

                if new_refresh_token and new_refresh_token != refresh_token:
                    _token_cache[cache_key + "_new_rt"] = {"refresh_token": new_refresh_token}

                if access_token:
                    _token_cache[cache_key] = {"access_token": access_token, "expires_at": time.time() + 3500}
                    return access_token

        except Exception as e:
            logger.error(f"GLM token refresh error: {e}")
        return None