"""
DeepAI chat provider for Flashy.

Reverse-engineered from https://deepai.org/ (Deep AI, Inc.).

The site uses a custom chat API at https://api.deepai.org/ with:
  - Chat endpoint: POST /hacking_is_a_serious_crime
  - Auth: api-key header with client-generated "tryit" key (fingerprint-based)
  - Body: FormData with chatHistory, model, session_uuid, chat_style, etc.
  - Anti-abuse flag: hacker_is_stinky = "very_stinky"
  - Streaming: raw byte stream, text before \\x1c delimiter, JSON metadata after
  - Thinking models: return {"task_id": "..."}, poll /check_chat_task_status

Models (free tier):
  standard, deepseek-v3.2, gemma-4, gpt-4.1-nano, gpt-oss-120b,
  gpt-5-nano, llama-3.3-70b-instruct, llama-3.1-8b-instant,
  llama-4-scout, qwen3-30b-a3b, gemini-2.5-flash-lite

Models (Pro only):
  genius, supergenius, gpt-4o-mini, gpt-4.1, o4-mini, o3,
  gemini-3-pro-preview, claude-4.7-opus, grok-4.3, gpt-5.3-chat-latest,
  gpt-5.2, chatgpt-4o-latest

Upload endpoint: POST /chat_attachments/upload (FormData with file field)
  Returns: {success: true, attachment: {uuid, original_filename, content_type, download_url}}
"""

import asyncio
import hashlib
import json
import logging
import math
import random
import uuid
from typing import AsyncGenerator, Dict, Any, List, Optional

import httpx

from .base import BaseProvider

logger = logging.getLogger("flashy.deepai")

DEEPAI_API_BASE = "https://api.deepai.org"
DEEPAI_SITE_URL = "https://deepai.org"
CHAT_ENDPOINT = "/hacking_is_a_serious_crime"
THINKING_STATUS_ENDPOINT = "/check_chat_task_status"
UPLOAD_ENDPOINT = "/chat_attachments/upload"
REQUEST_TIMEOUT = 180
UPLOAD_TIMEOUT = 120

FREE_MODELS = [
    {"id": "standard", "name": "DeepAI Standard", "locked": False, "vision": False, "thinking": False},
    {"id": "deepseek-v3.2", "name": "DeepSeek V3.2", "locked": False, "vision": False, "thinking": False},
    {"id": "gemma-4", "name": "Gemma 4", "locked": False, "vision": True, "thinking": False},
    {"id": "gpt-4.1-nano", "name": "GPT-4.1 Nano", "locked": False, "vision": False, "thinking": False},
    {"id": "gpt-5-nano", "name": "GPT-5 Nano", "locked": False, "vision": True, "thinking": False},
    {"id": "gpt-oss-120b", "name": "GPT OSS 120B", "locked": False, "vision": False, "thinking": True},
    {"id": "gemini-2.5-flash-lite", "name": "Gemini 2.5 Flash Lite", "locked": False, "vision": True, "thinking": False},
    {"id": "llama-3.3-70b-instruct", "name": "Llama 3.3 70B", "locked": False, "vision": False, "thinking": False},
    {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B", "locked": False, "vision": False, "thinking": False},
    {"id": "llama-4-scout", "name": "Llama 4 Scout", "locked": False, "vision": True, "thinking": False},
    {"id": "qwen3-30b-a3b", "name": "Qwen3 30B", "locked": False, "vision": True, "thinking": True},
]

PRO_MODELS = [
    {"id": "genius", "name": "DeepAI Genius", "locked": True, "vision": False, "thinking": False},
    {"id": "supergenius", "name": "DeepAI Super Genius", "locked": True, "vision": False, "thinking": True},
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "locked": True, "vision": True, "thinking": False},
    {"id": "gpt-4.1", "name": "GPT-4.1", "locked": True, "vision": True, "thinking": False},
    {"id": "o4-mini", "name": "o4 Mini", "locked": True, "vision": False, "thinking": True},
    {"id": "o3", "name": "o3", "locked": True, "vision": False, "thinking": True},
    {"id": "gemini-3-pro-preview", "name": "Gemini 3.1 Pro", "locked": True, "vision": True, "thinking": True},
    {"id": "claude-4.7-opus", "name": "Claude Opus 4.7", "locked": True, "vision": True, "thinking": False},
    {"id": "grok-4.3", "name": "Grok 4.3", "locked": True, "vision": False, "thinking": True},
    {"id": "gpt-5.3-chat-latest", "name": "GPT-5.3 Chat", "locked": True, "vision": False, "thinking": False},
    {"id": "gpt-5.2", "name": "GPT-5.2", "locked": True, "vision": True, "thinking": False},
    {"id": "chatgpt-4o-latest", "name": "ChatGPT 4o Latest", "locked": True, "vision": True, "thinking": False},
]

ALL_MODELS = FREE_MODELS + PRO_MODELS

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
_SALT = "hackers_become_a_little_stinkier_every_time_they_hack"


def _generate_tryit_key() -> str:
    random_num = str(math.floor(random.random() * 100000000000))

    def _h(s: str) -> str:
        return hashlib.sha256(s.encode()).hexdigest()[:64]

    inner = _h(USER_AGENT + _h(USER_AGENT + _h(USER_AGENT + random_num + _SALT)))
    return f"tryit-{random_num}-{inner}"


def _build_chat_history(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    history = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            content = "\n".join(text_parts)
        if role == "system":
            role = "user"
        if content:
            history.append({"role": role, "content": content})
    return history


def _model_info(model: str) -> Optional[Dict[str, Any]]:
    for m in ALL_MODELS:
        if m["id"] == model:
            return m
    return None


def _is_thinking_model(model: str) -> bool:
    info = _model_info(model)
    return info.get("thinking", False) if info else False


def _is_vision_model(model: str) -> bool:
    info = _model_info(model)
    return info.get("vision", False) if info else False


class DeepAIProvider(BaseProvider):
    """
    Provider for DeepAI Chat (https://deepai.org/).

    Uses the undocumented chat streaming endpoint with tryit key auth.
    Supports both standard streaming and thinking-model polling flows.
    """

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
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
                "locked": m.get("locked", False),
            }
            for m in ALL_MODELS
        ]

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "",
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        logger.info("deepai: generate_stream model=%s messages=%d", model, len(messages))

        if not model:
            model = "standard"

        chat_history = _build_chat_history(messages)
        session_uuid = str(uuid.uuid4())
        sensitivity_id = str(uuid.uuid4())
        api_key = _generate_tryit_key()

        form_fields = {
            "chatHistory": json.dumps(chat_history),
            "model": model,
            "session_uuid": session_uuid,
            "chat_style": "chat",
            "sensitivity_request_id": sensitivity_id,
            "hacker_is_stinky": "very_stinky",
        }

        if _is_thinking_model(model):
            form_fields["thinking_support"] = "1"

        attachment_uuids = kwargs.get("attachment_uuids")
        if attachment_uuids:
            form_fields["attachment_uuids"] = json.dumps(attachment_uuids)

        enabled_tools = kwargs.get("enabled_tools")
        if enabled_tools:
            form_fields["enabled_tools"] = json.dumps(enabled_tools)

        headers = {
            "api-key": api_key,
            "User-Agent": USER_AGENT,
            "Origin": DEEPAI_SITE_URL,
            "Referer": f"{DEEPAI_SITE_URL}/chat/",
        }

        has_content = False
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
                async with client.stream(
                    "POST",
                    f"{DEEPAI_API_BASE}{CHAT_ENDPOINT}",
                    data=form_fields,
                    headers=headers,
                ) as resp:
                    if resp.status_code == 401:
                        error_body = await resp.aread()
                        yield {"error": f"deepai: unauthorized (401): {error_body.decode('utf-8', errors='replace')[:200]}"}
                        return

                    if resp.status_code == 402:
                        error_body = await resp.aread()
                        yield {"error": f"deepai: quota exceeded (402): {error_body.decode('utf-8', errors='replace')[:200]}"}
                        return

                    if resp.status_code != 200:
                        error_body = await resp.aread()
                        yield {"error": f"deepai: HTTP {resp.status_code}: {error_body.decode('utf-8', errors='replace')[:300]}"}
                        return

                    content_type = resp.headers.get("content-type", "")

                    if _is_thinking_model(model) and "application/json" in content_type:
                        body = await resp.aread()
                        try:
                            data = json.loads(body)
                        except (json.JSONDecodeError, ValueError):
                            yield {"error": "deepai: thinking model returned invalid JSON"}
                            return

                        task_id = data.get("task_id")
                        if not task_id:
                            yield {"error": "deepai: thinking model returned no task_id"}
                            return

                        async for chunk in self._poll_thinking_task(client, task_id, api_key):
                            if chunk.get("type") == "content":
                                has_content = True
                                yield {"text": chunk["text"]}
                            elif chunk.get("type") == "done":
                                break
                            elif chunk.get("type") == "error":
                                yield {"error": chunk["message"]}
                                return
                        yield {"is_final": True, "finish_reason": "stop"}
                        return

                    text_buffer = ""
                    json_buffer = ""
                    in_json_payload = False
                    async for raw_chunk in resp.aiter_text():
                        text_buffer += raw_chunk

                        while True:
                            if in_json_payload:
                                newline_idx = text_buffer.find("\n")
                                if newline_idx == -1:
                                    json_buffer += text_buffer
                                    text_buffer = ""
                                    break
                                json_buffer += text_buffer[:newline_idx]
                                text_buffer = text_buffer[newline_idx + 1:]
                                in_json_payload = False
                                if json_buffer.strip():
                                    try:
                                        payload = json.loads(json_buffer.strip())
                                        if isinstance(payload, dict) and "function_call" in payload:
                                            yield {"tool_call": payload["function_call"]}
                                    except (json.JSONDecodeError, ValueError):
                                        pass
                                json_buffer = ""
                                continue

                            sep_idx = text_buffer.find("\x1c")
                            if sep_idx != -1:
                                text_part = text_buffer[:sep_idx]
                                text_buffer = text_buffer[sep_idx + 1:]
                                if text_part:
                                    has_content = True
                                    yield {"text": text_part}
                                in_json_payload = True
                                json_buffer = ""
                                continue

                            yield_len = max(0, len(text_buffer) - 256)
                            if yield_len > 0:
                                to_yield = text_buffer[:yield_len]
                                text_buffer = text_buffer[yield_len:]
                                has_content = True
                                yield {"text": to_yield}
                            break

                    if text_buffer:
                        has_content = True
                        yield {"text": text_buffer}

        except Exception as exc:
            logger.exception("deepai: stream error: %s", exc)
            yield {"error": f"deepai: stream error: {exc}"}
            return

        yield {"is_final": True, "finish_reason": "stop"}

    async def _poll_thinking_task(
        self,
        client: httpx.AsyncClient,
        task_id: str,
        api_key: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        poll_url = f"{DEEPAI_API_BASE}{THINKING_STATUS_ENDPOINT}"
        headers = {"api-key": api_key, "User-Agent": USER_AGENT}
        max_attempts = 300
        interval = 2

        for _ in range(max_attempts):
            try:
                r = await client.get(
                    poll_url,
                    params={"type": "thinking-task", "task_id": task_id},
                    headers=headers,
                )
                if r.status_code != 200:
                    yield {"type": "error", "message": f"deepai: thinking poll HTTP {r.status_code}"}
                    return

                data = r.json()
                status = data.get("status", "")

                if status in ("complete", "completed", "done"):
                    result_text = data.get("result", data.get("text", ""))
                    if result_text:
                        yield {"type": "content", "text": result_text}
                    yield {"type": "done"}
                    return

                if status in ("failed", "error"):
                    yield {"type": "error", "message": data.get("error", "thinking task failed")}
                    return

            except Exception as exc:
                yield {"type": "error", "message": f"deepai: thinking poll error: {exc}"}
                return

            await asyncio.sleep(interval)

        yield {"type": "error", "message": "deepai: thinking task timed out"}

    async def upload_file(
        self,
        file_data: bytes,
        filename: str,
        content_type: str = "image/png",
        client: Optional[httpx.AsyncClient] = None,
    ) -> Optional[Dict[str, Any]]:
        own_client = client is None
        if own_client:
            client = httpx.AsyncClient(timeout=UPLOAD_TIMEOUT, follow_redirects=True)

        try:
            api_key = _generate_tryit_key()
            files = {"file": (filename, file_data, content_type)}
            headers = {"api-key": api_key, "User-Agent": USER_AGENT, "Origin": DEEPAI_SITE_URL}

            r = await client.post(
                f"{DEEPAI_API_BASE}{UPLOAD_ENDPOINT}",
                files=files,
                headers=headers,
            )

            if r.status_code != 200:
                logger.warning("deepai: upload failed with status %d: %s", r.status_code, r.text[:300])
                return None

            data = r.json()
            if data.get("success"):
                return data.get("attachment")
            logger.warning("deepai: upload response not success: %s", r.text[:300])
            return None

        except Exception as exc:
            logger.warning("deepai: upload exception: %s", exc)
            return None
        finally:
            if own_client:
                await client.aclose()