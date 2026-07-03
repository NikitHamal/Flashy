import json
import logging
import uuid
from typing import Any, AsyncGenerator, Dict, List

from curl_cffi.requests import AsyncSession

from .base import BaseProvider

logger = logging.getLogger("flashy.mimo")

MODELS = [
    {"id": "MiMo-V2.5-Pro", "name": "MiMo V2.5 Pro", "context_window": 128000},
    {"id": "MiMo-V2.5", "name": "MiMo V2.5", "context_window": 128000},
    {"id": "MiMo-V2-Flash", "name": "MiMo V2 Flash", "context_window": 128000},
]

MIMO_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Origin": "https://aistudio.xiaomimimo.com",
    "Referer": "https://aistudio.xiaomimimo.com/",
    "Sec-Ch-Ua": '"Chromium";v="144", "Not(A:Brand";v="8", "Google Chrome";v="144"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "X-Timezone": "Asia/Shanghai",
}


def _messages_to_query(messages: List[Dict[str, Any]]) -> str:
    parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if not content:
            continue
        if role == "system":
            parts.append(f"[System]\n{content}")
        elif role == "user":
            parts.append(f"[User]\n{content}")
        elif role == "assistant":
            parts.append(f"[Assistant]\n{content}")
        elif role == "tool":
            parts.append(f"[Tool]\n{content}")
    return "\n\n".join(parts)


def _extract_think(text: str) -> tuple[str, str]:
    thinking = ""
    content = text
    while "​```thinking" in content:
        start = content.find("​```thinking")
        end = content.find("​```", start + 12)
        if end == -1:
            break
        thinking += content[start + 12:end].strip() + "\n"
        content = content[:start] + content[end + 3:]
    while "```thinking" in content:
        start = content.find("```thinking")
        end = content.find("```", start + 11)
        if end == -1:
            break
        thinking += content[start + 11:end].strip() + "\n"
        content = content[:start] + content[end + 3:]
    while "<thinking>" in content:
        start = content.find("<thinking>")
        end = content.find("</thinking>", start)
        if end == -1:
            break
        thinking += content[start + 10:end].strip() + "\n"
        content = content[:start] + content[end + 11:]
    return content.strip(), thinking.strip()


class MimoProvider(BaseProvider):
    """Mimo (Xiaomi AI Studio) provider from aistudio.xiaomimimo.com."""

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        return [{"id": m["id"], "name": m["name"]} for m in MODELS]

    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        service_token = kwargs.get("service_token") or kwargs.get("mimo_service_token", "")
        user_id = kwargs.get("user_id") or kwargs.get("mimo_user_id", "")
        ph_token = kwargs.get("ph_token") or kwargs.get("mimo_ph_token", "")

        if not service_token or not user_id or not ph_token:
            yield {"error": "Mimo requires service_token, user_id, and ph_token. See Mimo settings."}
            return

        cookie_str = f"serviceToken={service_token}; userId={user_id}; xiaomichatbot_ph={ph_token}"
        headers = {
            **MIMO_HEADERS,
            "Cookie": cookie_str,
        }

        conversation_id = str(uuid.uuid4())
        msg_id = str(uuid.uuid4())

        query = _messages_to_query(messages)
        if not query.strip():
            yield {"error": "No user message found"}
            return

        payload = {
            "msgId": msg_id,
            "conversationId": conversation_id,
            "query": query,
            "modelConfig": {
                "enableThinking": "think" in model.lower() or "reason" in model.lower(),
                "webSearchStatus": 0,
                "model": "MiMo",
                "temperature": kwargs.get("temperature", 0.7),
                "topP": kwargs.get("top_p", 1.0),
            },
            "multiMedias": [],
        }

        try:
            async with AsyncSession(impersonate="chrome") as session:
                resp = await session.post(
                    f"https://aistudio.xiaomimimo.com/open-apis/bot/chat?xiaomichatbot_ph={ph_token}",
                    headers=headers,
                    json=payload,
                    stream=True,
                    timeout=120,
                )

                if resp.status_code == 403:
                    yield {"error": "Mimo: 403 Forbidden — tokens may be invalid or expired."}
                    return
                if resp.status_code != 200:
                    error_text = resp.text[:300]
                    yield {"error": f"Mimo error ({resp.status_code}): {error_text}"}
                    return

                buffer = ""
                accumulated_text = ""
                accumulated_thought = ""
                has_content = False

                async for chunk_bytes in resp.aiter_content():
                    buffer += chunk_bytes.decode("utf-8", errors="ignore")

                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue

                        if line.startswith("data:"):
                            data_str = line[5:].strip()
                            if data_str == "[DONE]":
                                yield {"is_final": True, "finish_reason": "stop"}
                                return

                            try:
                                data = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue

                            event_type = data.get("type") or data.get("event", "")

                            if event_type == "message" or event_type == "text":
                                text = data.get("text") or data.get("content") or ""
                                if text:
                                    has_content = True
                                    clean, think = _extract_think(text)

                                    if think:
                                        new_think = think
                                        if accumulated_thought:
                                            if not think.startswith(accumulated_thought):
                                                new_think = think
                                        delta_think = new_think[len(accumulated_thought):] if new_think.startswith(accumulated_thought) else new_think
                                        if delta_think:
                                            accumulated_thought = think
                                            yield {"thought": delta_think}

                                    if clean:
                                        new_text = clean
                                        if accumulated_text:
                                            if not clean.startswith(accumulated_text):
                                                new_text = clean
                                        delta_text = new_text[len(accumulated_text):] if new_text.startswith(accumulated_text) else new_text
                                        if delta_text:
                                            accumulated_text = clean
                                            yield {"text": delta_text}

                            elif event_type == "usage" or "usage" in data:
                                usage = data.get("usage", {})
                                if isinstance(usage, dict) and usage.get("totalTokens"):
                                    yield {"usage": {
                                        "prompt_tokens": usage.get("promptTokens", 0),
                                        "completion_tokens": usage.get("completionTokens", 0),
                                        "total_tokens": usage.get("totalTokens", 0),
                                    }}

                            elif event_type == "finish" or event_type == "done":
                                yield {"is_final": True, "finish_reason": "stop"}
                                return

                if not has_content:
                    yield {"error": "Mimo returned no content."}
                else:
                    yield {"is_final": True, "finish_reason": "stop"}

        except Exception as e:
            logger.exception(f"[MIMO] Error: {e}")
            yield {"error": f"Mimo error: {str(e)}"}
