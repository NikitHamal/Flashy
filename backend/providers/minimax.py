import hashlib
import json
import logging
import time
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

from curl_cffi.requests import AsyncSession

from .base import BaseProvider

logger = logging.getLogger("flashy.minimax")

MODELS = [
    {"id": "MiniMax-M2.7", "name": "MiniMax M2.7", "context_window": 128000},
    {"id": "MiniMax-M2.5", "name": "MiniMax M2.5", "context_window": 128000},
]

MINIMAX_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Origin": "https://agent.minimaxi.com",
    "Referer": "https://agent.minimaxi.com/",
    "Sec-Ch-Ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
}


def _md5(data: str) -> str:
    return hashlib.md5(data.encode("utf-8")).hexdigest()


def _generate_signatures(
    method: str,
    uri: str,
    jwt_token: str,
    data_json: str = "",
    timestamp: Optional[int] = None,
) -> Dict[str, str]:
    ts = str(timestamp or int(time.time()))
    full_uri = f"https://agent.minimaxi.com{uri}"

    x_signature = _md5(ts + jwt_token + data_json)

    yy = _md5(
        __import__("urllib.parse").quote(full_uri, safe="")
        + "_"
        + data_json
        + _md5(ts)
        + "ooui"
    )

    return {
        "x-signature": x_signature,
        "yy": yy,
        "x-ts": ts,
    }


def _extract_jwt_parts(token: str) -> tuple[str, str]:
    if "+" in token:
        parts = token.split("+", 1)
        return parts[0], parts[1]
    return "", token


def _messages_to_text(messages: List[Dict[str, Any]]) -> str:
    parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if not content:
            continue
        if role == "system":
            parts.append(f"System: {content}")
        elif role == "assistant":
            parts.append(f"Assistant: {content}")
        elif role == "user":
            parts.append(f"User: {content}")
        elif role == "tool":
            parts.append(f"Tool: {content}")
    return "\n".join(parts)


class MiniMaxProvider(BaseProvider):
    """MiniMax (Hailuo AI) provider from agent.minimaxi.com."""

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        return [{"id": m["id"], "name": m["name"]} for m in MODELS]

    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        token = kwargs.get("token") or kwargs.get("minimax_token", "")
        if not token:
            yield {"error": "MiniMax requires a JWT token. Set minimax_token in config."}
            return

        real_user_id = kwargs.get("real_user_id") or kwargs.get("realUserID", "")
        user_id, jwt_token = _extract_jwt_parts(token)
        if not user_id and real_user_id:
            user_id = real_user_id
        if not user_id:
            parsed = self._parse_jwt(jwt_token or token)
            if parsed and "user" in parsed:
                user_id = parsed["user"].get("id", "")
        if not user_id:
            yield {"error": "MiniMax: could not determine user_id. Provide realUserID or use 'userID+JWTtoken' format."}
            return

        final_jwt = jwt_token or token

        device_id = str(uuid.uuid4())
        headers = {**MINIMAX_HEADERS, "Authorization": f"Bearer {final_jwt}"}

        try:
            async with AsyncSession(impersonate="chrome") as session:
                await self._register_device(session, headers, device_id, user_id, final_jwt)

                chat_id = str(uuid.uuid4())
                text = _messages_to_text(messages)
                if not text.strip():
                    yield {"error": "No user message found"}
                    return

                msg_id = str(uuid.uuid4())
                send_payload = {
                    "msg_id": msg_id,
                    "msg_type": 1,
                    "text": text,
                    "chat_id": chat_id,
                    "chat_type": 1,
                    "selected_mcp_tools": [],
                }

                send_uri = "/matrix/api/v1/chat/send_msg"
                send_data = json.dumps(send_payload, separators=(",", ":"), ensure_ascii=False)
                sigs = _generate_signatures("POST", send_uri, final_jwt, send_data)

                resp = await session.post(
                    f"https://agent.minimaxi.com{send_uri}",
                    headers={**headers, **sigs},
                    data=send_data,
                    timeout=30,
                )

                if resp.status_code != 200:
                    error_text = resp.text[:300]
                    yield {"error": f"MiniMax send_msg failed ({resp.status_code}): {error_text}"}
                    return

                result = resp.json()
                msg_id = result.get("msg_id", msg_id)

                last_text = ""
                last_thinking = ""
                has_content = False

                for poll in range(120):
                    await asyncio.sleep(0.5)
                    detail_uri = "/matrix/api/v1/chat/get_chat_detail"
                    detail_payload = json.dumps({"chat_id": chat_id}, separators=(",", ":"), ensure_ascii=False)
                    detail_sigs = _generate_signatures("POST", detail_uri, final_jwt, detail_payload)

                    detail_resp = await session.post(
                        f"https://agent.minimaxi.com{detail_uri}",
                        headers={**headers, **detail_sigs},
                        data=detail_payload,
                        timeout=30,
                    )

                    if detail_resp.status_code != 200:
                        continue

                    detail = detail_resp.json()
                    messages_list = detail.get("data", {}).get("messages", [])
                    if not messages_list:
                        continue

                    last_msg = messages_list[-1]
                    if last_msg.get("msg_id") != msg_id and last_msg.get("role") != "assistant":
                        continue

                    msg_content = last_msg.get("text", "")
                    if not msg_content:
                        continue

                    content = msg_content
                    thinking = ""
                    has_content = True

                    think_start = content.rfind("​```thinking")
                    think_end = content.rfind("​```")
                    if think_start != -1 and think_end != -1 and think_end > think_start:
                        thinking = content[think_start + 12:think_end].strip()
                        content = content[:think_start] + content[think_end + 3:]

                    new_text = content[len(last_text):]
                    new_thinking = thinking[len(last_thinking):]

                    if new_thinking:
                        logger.debug(f"[MINIMAX] thinking delta: {new_thinking[:100]}")
                        yield {"thought": new_thinking}
                        last_thinking = thinking
                    if new_text:
                        logger.debug(f"[MINIMAX] text delta: {new_text[:100]}")
                        yield {"text": new_text}
                        last_text = content

                    if last_msg.get("status") == "done" or last_msg.get("is_final"):
                        yield {"is_final": True, "finish_reason": "stop"}
                        return

                if has_content:
                    yield {"is_final": True, "finish_reason": "stop"}
                else:
                    yield {"error": "MiniMax: no response content after polling"}

        except Exception as e:
            logger.exception(f"[MINIMAX] Error: {e}")
            yield {"error": f"MiniMax error: {str(e)}"}

    async def _register_device(
        self,
        session: AsyncSession,
        headers: Dict[str, str],
        device_id: str,
        user_id: str,
        jwt_token: str,
    ):
        uri = "/v1/api/user/device/register"
        payload = json.dumps({
            "device_id": device_id,
            "user_id": user_id,
            "token": jwt_token,
            "device_name": "Chrome",
            "device_type": "web",
            "app_version": "1.0.0",
        }, separators=(",", ":"), ensure_ascii=False)

        sigs = _generate_signatures("POST", uri, jwt_token, payload)
        resp = await session.post(
            f"https://agent.minimaxi.com{uri}",
            headers={**headers, **sigs},
            data=payload,
            timeout=15,
        )
        logger.info(f"[MINIMAX] device register: {resp.status_code}")

    def _parse_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            import base64
            padding = 4 - len(parts[1]) % 4
            if padding != 4:
                parts[1] += "=" * padding
            decoded = base64.urlsafe_b64decode(parts[1])
            return json.loads(decoded)
        except Exception:
            return None
