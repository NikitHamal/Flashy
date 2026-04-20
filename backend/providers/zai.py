import hashlib
import hmac
import json
import logging
import math
import time
import uuid
from base64 import b64encode, b64decode
from typing import Any, AsyncGenerator, Dict, List, Optional
from urllib.parse import urlencode

from curl_cffi.requests import AsyncSession

from .base import BaseProvider

logger = logging.getLogger("flashy.zai")

MODELS = [
    {"id": "GLM-5.1", "name": "GLM-5.1", "context_window": 128000},
    {"id": "GLM-5-Turbo", "name": "GLM-5 Turbo", "context_window": 128000},
    {"id": "glm-5", "name": "GLM-5", "context_window": 128000},
    {"id": "glm-4.7", "name": "GLM-4.7", "context_window": 128000},
    {"id": "glm-4.6v", "name": "GLM-4.6V", "context_window": 128000},
    {"id": "glm-4.5-air", "name": "GLM-4.5 Air", "context_window": 128000},
]

ZAI_API_BASE = "https://chat.z.ai"
X_FE_VERSION = "prod-fe-1.0.241"

ZAI_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Cache-Control": "no-cache",
    "Origin": ZAI_API_BASE,
    "Pragma": "no-cache",
    "Sec-Ch-Ua": '"Chromium";v="144", "Not(A:Brand";v="8", "Google Chrome";v="144"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "X-FE-Version": X_FE_VERSION,
    "Priority": "u=1, i",
}

SIGN_SECRET = "key-@@@@)))()((9))-xxxx&&&%%%%%"


def _extract_user_id(token: str) -> str:
    try:
        parts = token.split(".")
        if len(parts) >= 2:
            payload = parts[1]
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding
            decoded = b64decode(payload)
            data = json.loads(decoded)
            return data.get("id", data.get("user_id", data.get("uid", data.get("sub", "guest"))))
    except Exception:
        pass
    return "guest"


def _generate_signature(message_text: str, request_id: str, timestamp_ms: int, user_id: str) -> str:
    timestamp_str = str(timestamp_ms)
    b64_msg = b64encode(message_text.encode("utf-8")).decode("ascii")
    canonical = f"requestId,{request_id},timestamp,{timestamp_str},user_id,{user_id}|{b64_msg}|{timestamp_str}"
    window_index = math.floor(timestamp_ms / (5 * 60 * 1000))
    derived_key = hmac.new(SIGN_SECRET.encode(), str(window_index).encode(), hashlib.sha256).hexdigest()
    signature = hmac.new(derived_key.encode(), canonical.encode(), hashlib.sha256).hexdigest()
    return signature


class ZAIProvider(BaseProvider):
    """Z.ai (GLM International) Web API provider."""

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        return [{"id": m["id"], "name": m["name"]} for m in MODELS]

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        token = kwargs.get("token") or kwargs.get("zai_token", "")
        if not token:
            yield {"type": "error", "error": "Z.ai requires a JWT token. Set zai_token in config."}
            return

        user_id = _extract_user_id(token)
        request_id = str(uuid.uuid4())
        message_id = str(uuid.uuid4())
        timestamp_ms = int(time.time() * 1000)

        raw = kwargs.get("is_openai_pass_through", False)
        chat_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if not content:
                continue
            if not raw and role == "user" and ("## User Request" in content or "FOLLOW THESE" in content or "You are " in content[:50]):
                parts = content.split("## User Request", 1)
                if len(parts) == 2:
                    system_text = parts[0].strip()
                    user_text = parts[1].strip()
                    if user_text.startswith("\n"):
                        user_text = user_text[1:]
                    if system_text:
                        chat_messages.append({"role": "system", "content": system_text})
                    if user_text:
                        chat_messages.append({"role": "user", "content": user_text})
                    continue
            chat_messages.append({"role": role, "content": content})

        if not chat_messages:
            yield {"type": "error", "error": "No user message found"}
            return

        last_user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break

        signature = _generate_signature(last_user_msg, request_id, timestamp_ms, user_id)

        enable_thinking = "think" in model.lower() or "turbo" in model.lower()

        try:
            async with AsyncSession(impersonate="chrome") as session:
                chat_id = await self._create_chat(session, token, model, last_user_msg)
                if not chat_id:
                    yield {"type": "error", "error": "Failed to create Z.ai chat session"}
                    return

                body = {
                    "stream": True,
                    "model": model,
                    "messages": chat_messages,
                    "signature_prompt": last_user_msg,
                    "params": {},
                    "extra": {},
                    "features": {
                        "image_generation": False,
                        "web_search": False,
                        "auto_web_search": False,
                        "preview_mode": True,
                        "flags": [],
                        "vlm_tools_enable": False,
                        "vlm_web_search_enable": False,
                        "vlm_website_mode": False,
                        "enable_thinking": enable_thinking,
                    },
                    "variables": {
                        "{{USER_NAME}}": "User",
                        "{{USER_LOCATION}}": "Unknown",
                        "{{CURRENT_DATETIME}}": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "{{CURRENT_DATE}}": time.strftime("%Y-%m-%d"),
                        "{{CURRENT_TIME}}": time.strftime("%H:%M:%S"),
                        "{{CURRENT_WEEKDAY}}": time.strftime("%A"),
                        "{{CURRENT_TIMEZONE}}": "UTC",
                        "{{USER_LANGUAGE}}": "en-US",
                    },
                    "chat_id": chat_id,
                    "id": request_id,
                    "current_user_message_id": message_id,
                    "current_user_message_parent_id": None,
                    "background_tasks": {"title_generation": True, "tags_generation": True},
                }

                query_params = urlencode({
                    "timestamp": str(timestamp_ms),
                    "requestId": request_id,
                    "user_id": user_id,
                    "version": "0.0.1",
                    "platform": "web",
                    "token": token[:20] + "...",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
                    "language": "zh-CN",
                    "languages": "zh-CN,zh",
                    "timezone": "Asia/Shanghai",
                    "cookie_enabled": "true",
                    "screen_width": "1920",
                    "screen_height": "1080",
                    "screen_resolution": "1920x1080",
                    "viewport_height": "945",
                    "viewport_width": "923",
                    "viewport_size": "923x945",
                    "color_depth": "24",
                    "pixel_ratio": "1",
                    "current_url": f"{ZAI_API_BASE}/c/{chat_id}",
                    "pathname": f"/c/{chat_id}",
                    "search": "",
                    "hash": "",
                    "host": "chat.z.ai",
                    "hostname": "chat.z.ai",
                    "protocol": "https:",
                    "referrer": "",
                    "title": "Z.ai - Free AI Chatbot",
                    "timezone_offset": "-480",
                    "local_time": time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "utc_time": time.strftime("%a, %d %b %Y %H:%M:%S GMT"),
                    "is_mobile": "false",
                    "is_touch": "false",
                    "max_touch_points": "0",
                    "browser_name": "Chrome",
                    "os_name": "Windows",
                    "signature_timestamp": str(timestamp_ms),
                })

                headers = {
                    **ZAI_HEADERS,
                    "Authorization": f"Bearer {token}",
                    "Cookie": f"token={token}",
                    "X-Signature": signature,
                    "Referer": f"{ZAI_API_BASE}/c/{chat_id}",
                }

                resp = await session.post(
                    f"{ZAI_API_BASE}/api/v2/chat/completions?{query_params}",
                    headers=headers,
                    json=body,
                    timeout=120,
                )

                logger.debug(f"[ZAI] Completion status: {resp.status_code}")

                if resp.status_code == 401:
                    yield {"type": "error", "error": "Z.ai token invalid or expired"}
                    return
                if resp.status_code != 200:
                    logger.error(f"[ZAI] Non-200 response: {resp.status_code} - {resp.text[:500]}")
                    yield {"type": "error", "error": f"Z.ai error: {resp.status_code} - {resp.text[:200]}"}
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

                    if isinstance(data, dict) and data.get("error"):
                        err = data["error"]
                        if isinstance(err, dict):
                            yield {"type": "error", "error": f"Z.ai error: {err.get('detail', err.get('message', str(err)))}"}
                        else:
                            yield {"type": "error", "error": str(err)}
                        return

                    event_data = data.get("data", data) if isinstance(data, dict) else data
                    if not isinstance(event_data, dict):
                        continue

                    phase = event_data.get("phase", "")
                    delta = event_data.get("delta_content", "")

                    if delta:
                        has_content = True
                        if phase == "thinking":
                            yield {"type": "thought", "thought": delta}
                        else:
                            yield {"type": "text", "text": delta}

                    if event_data.get("done"):
                        break

                if not has_content:
                    logger.warning(f"[ZAI] No content in response. First 500 chars: {resp.text[:500]}")
                    yield {"type": "error", "error": "Z.ai returned no content. The token may be invalid or the model may be unavailable."}

                yield {"type": "final", "finish_reason": "stop", "is_final": True}

        except Exception as e:
            logger.error(f"Z.ai error: {e}")
            yield {"type": "error", "error": str(e)}

    async def _create_chat(self, session: AsyncSession, token: str, model: str, first_message: str) -> Optional[str]:
        message_id = str(uuid.uuid4())
        timestamp = int(time.time())

        body = {
            "chat": {
                "id": "",
                "title": "New Chat",
                "models": [model],
                "params": {},
                "history": {
                    "messages": {
                        message_id: {
                            "id": message_id,
                            "parentId": None,
                            "childrenIds": [],
                            "role": "user",
                            "content": first_message[:200] if first_message else "",
                            "timestamp": timestamp,
                            "models": [model],
                        },
                    } if first_message else {},
                    "currentId": message_id if first_message else "",
                },
                "tags": [],
                "flags": [],
                "features": [{"type": "tool_selector", "server": "tool_selector_h", "status": "hidden"}],
                "mcp_servers": [],
                "enable_thinking": False,
                "auto_web_search": False,
                "message_version": 1,
                "extra": {},
                "timestamp": int(time.time() * 1000),
            },
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-FE-Version": X_FE_VERSION,
            "Cookie": f"token={token}",
            "Origin": ZAI_API_BASE,
            "Referer": f"{ZAI_API_BASE}/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        }

        try:
            resp = await session.post(
                f"{ZAI_API_BASE}/api/v1/chats/new",
                headers=headers,
                json=body,
                timeout=30,
            )
            logger.debug(f"[ZAI] Create chat status: {resp.status_code}")
            if resp.status_code in (200, 201):
                data = resp.json()
                chat_id = data.get("id", data.get("data", {}).get("id", ""))
                if chat_id:
                    return chat_id
            logger.warning(f"[ZAI] Create chat failed: {resp.status_code} - {resp.text[:300]}")
            return ""
        except Exception as e:
            logger.error(f"[ZAI] Create chat error: {e}")
            return ""