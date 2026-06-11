"""
SurfSense anon-chat provider for Flashy.

Reverse-engineered from https://www.surfsense.com/free/gpt-5.4-mini-no-login

The site is a Next.js app using a REST API at https://api.surfsense.com/api/v1/public/anon-chat/

API Details:
  - Models: GET /models (returns list of free models)
  - Model info: GET /models/{slug}
  - Chat stream: POST /stream (SSE response)
  - Quota: GET /quota
  - Upload: POST /upload (FormData with file field)
  - Document: GET /document (get uploaded doc metadata)

Auth: No login required. Uses session cookies (credentials: "include").
  Turnstile captcha may be required after quota exhaustion.

Chat stream request body:
  {
    "model_slug": "gpt-5.4-mini-no-login",
    "messages": [{"role": "user", "content": "..."}],
    "disabled_tools": ["web_search"],  // optional
    "turnstile_token": "..."           // optional, for captcha
  }

SSE event types:
  start, start-step, text-start, text-delta, text-end,
  data-thinking-step, data-anon-quota, data-token-usage,
  tool-input-start, tool-input-delta, tool-input-available,
  tool-output-available, finish-step, finish

Models (free, no login):
  gpt-5.4-mini-no-login  (GPT 5.4 Mini, Azure OpenAI)
  gpt-o4-mini-no-login    (GPT O4 Mini, Azure OpenAI, reasoning)
"""

import json
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional

import httpx

from .base import BaseProvider

logger = logging.getLogger("flashy.surfsense")

SURFSENSE_API_BASE = "https://api.surfsense.com/api/v1/public/anon-chat"
REQUEST_TIMEOUT = 180

MODELS = [
    {
        "id": "gpt-5.4-mini-no-login",
        "name": "GPT 5.4 Mini",
        "provider": "AZURE_OPENAI",
        "model_name": "gpt-5.4-mini",
        "is_premium": False,
        "reasoning": False,
        "web_search": True,
    },
    {
        "id": "gpt-o4-mini-no-login",
        "name": "GPT O4 Mini",
        "provider": "AZURE_OPENAI",
        "model_name": "o4-mini",
        "is_premium": False,
        "reasoning": True,
        "web_search": True,
    },
]


def _parse_messages(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    result = []
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
            result.append({"role": role, "content": content})
    return result


class SurfSenseProvider(BaseProvider):
    """
    Provider for SurfSense free anonymous chat (https://surfsense.com/).

    Uses the /api/v1/public/anon-chat/ REST API with SSE streaming.
    No login required. Supports web search and document upload.
    """

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(f"{SURFSENSE_API_BASE}/models")
                if r.status_code == 200:
                    data = r.json()
                    if isinstance(data, list):
                        return [
                            {
                                "id": m.get("seo_slug") or m.get("id", ""),
                                "name": m.get("name", ""),
                                "capabilities": {
                                    "chat": True,
                                    "stream": True,
                                    "vision": False,
                                    "reasoning": m.get("model_name", "").startswith("o"),
                                    "tools": True,
                                },
                                "locked": m.get("is_premium", False),
                                "web_search": True,
                                "provider_name": m.get("provider", ""),
                                "model_name": m.get("model_name", ""),
                            }
                            for m in data
                        ]
        except Exception as exc:
            logger.warning("surfsense: failed to fetch models: %s", exc)

        return [
            {
                "id": m["id"],
                "name": m["name"],
                "capabilities": {
                    "chat": True,
                    "stream": True,
                    "vision": False,
                    "reasoning": m.get("reasoning", False),
                    "tools": True,
                },
                "locked": m.get("is_premium", False),
                "web_search": True,
                "provider_name": m.get("provider", ""),
                "model_name": m.get("model_name", ""),
            }
            for m in MODELS
        ]

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "",
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        logger.info("surfsense: generate_stream model=%s messages=%d", model, len(messages))

        if not model:
            model = "gpt-5.4-mini-no-login"

        parsed_messages = _parse_messages(messages)
        if not parsed_messages:
            yield {"error": "surfsense: no messages to send"}
            return

        body = {
            "model_slug": model,
            "messages": parsed_messages,
        }

        web_search = kwargs.get("web_search", True)
        if not web_search:
            body["disabled_tools"] = ["web_search"]

        turnstile_token = kwargs.get("turnstile_token")
        if turnstile_token:
            body["turnstile_token"] = turnstile_token

        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Origin": "https://www.surfsense.com",
            "Referer": "https://www.surfsense.com/",
        }

        has_content = False
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                async with client.stream(
                    "POST",
                    f"{SURFSENSE_API_BASE}/stream",
                    json=body,
                    headers=headers,
                ) as resp:
                    if resp.status_code == 404:
                        error_body = await resp.aread()
                        yield {"error": f"surfsense: model not found (404): {error_body.decode('utf-8', errors='replace')[:300]}"}
                        return

                    if resp.status_code == 403:
                        error_body = await resp.aread()
                        try:
                            err_data = json.loads(error_body.decode("utf-8", errors="replace"))
                            code = err_data.get("detail", {}).get("code") or err_data.get("error", {}).get("code", "")
                            msg = err_data.get("detail", {}).get("message") or err_data.get("error", {}).get("message", "")
                            if code in ("CAPTCHA_REQUIRED", "CAPTCHA_INVALID"):
                                yield {"error": "surfsense: daily quota exhausted — captcha required. Try again later or use a different provider."}
                                return
                            if msg:
                                yield {"error": f"surfsense: forbidden (403): {msg}"}
                                return
                        except (json.JSONDecodeError, ValueError):
                            pass
                        yield {"error": f"surfsense: forbidden (403): {error_body.decode('utf-8', errors='replace')[:300]}"}
                        return

                    if resp.status_code == 429:
                        error_body = await resp.aread()
                        yield {"error": f"surfsense: rate limited (429): {error_body.decode('utf-8', errors='replace')[:300]}"}
                        return

                    if resp.status_code != 200:
                        error_body = await resp.aread()
                        yield {"error": f"surfsense: HTTP {resp.status_code}: {error_body.decode('utf-8', errors='replace')[:300]}"}
                        return

                    current_tool_call_id = None
                    current_tool_name = None
                    current_tool_input = ""
                    reasoning_text = ""

                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue

                        if line.startswith("data: "):
                            data_str = line[6:]
                        elif line.startswith("data:"):
                            data_str = line[5:].strip()
                        else:
                            continue

                        if data_str == "[DONE]":
                            break

                        try:
                            event = json.loads(data_str)
                        except (json.JSONDecodeError, ValueError):
                            continue

                        event_type = event.get("type", "")

                        if event_type == "text-delta":
                            delta = event.get("delta", "")
                            if delta:
                                has_content = True
                                yield {"text": delta}

                        elif event_type == "reasoning-delta":
                            delta = event.get("delta", "")
                            if delta:
                                reasoning_text += delta
                                yield {"thinking": delta}

                        elif event_type == "reasoning-end":
                            pass

                        elif event_type == "tool-input-start":
                            current_tool_call_id = event.get("toolCallId")
                            current_tool_name = event.get("toolName", "")
                            current_tool_input = ""

                        elif event_type == "tool-input-delta":
                            current_tool_input += event.get("inputTextDelta", "")

                        elif event_type == "tool-input-available":
                            tool_input = event.get("input", {})
                            if isinstance(tool_input, str):
                                try:
                                    tool_input = json.loads(tool_input)
                                except (json.JSONDecodeError, ValueError):
                                    pass
                            if current_tool_call_id and current_tool_name:
                                yield {
                                    "tool_call": {
                                        "id": current_tool_call_id,
                                        "name": current_tool_name,
                                        "arguments": tool_input if isinstance(tool_input, dict) else {},
                                    }
                                }

                        elif event_type == "tool-output-available":
                            output = event.get("output", {})
                            if current_tool_call_id:
                                yield {
                                    "tool_result": {
                                        "id": current_tool_call_id,
                                        "output": output,
                                    }
                                }
                            current_tool_call_id = None
                            current_tool_name = None
                            current_tool_input = ""

                        elif event_type == "data-token-usage":
                            usage = event.get("data", {}).get("usage", {})
                            if usage:
                                yield {
                                    "usage": {
                                        "prompt_tokens": usage.get("prompt_tokens", 0),
                                        "completion_tokens": usage.get("completion_tokens", 0),
                                        "total_tokens": usage.get("total_tokens", 0),
                                    }
                                }

                        elif event_type == "data-anon-quota":
                            pass

                        elif event_type == "error":
                            yield {"error": event.get("errorText", "surfsense: unknown error")}
                            return

                        elif event_type == "finish":
                            break

        except Exception as exc:
            logger.exception("surfsense: stream error: %s", exc)
            yield {"error": f"surfsense: stream error: {exc}"}
            return

        yield {"is_final": True, "finish_reason": "stop"}

    async def upload_file(
        self,
        file_data: bytes,
        filename: str,
        content_type: str = "application/pdf",
        client: Optional[httpx.AsyncClient] = None,
    ) -> Optional[Dict[str, Any]]:
        own_client = client is None
        if own_client:
            client = httpx.AsyncClient(timeout=120)

        try:
            files = {"file": (filename, file_data, content_type)}
            r = await client.post(
                f"{SURFSENSE_API_BASE}/upload",
                files=files,
            )

            if r.status_code == 409:
                logger.warning("surfsense: upload quota exceeded")
                return None

            if r.status_code != 200:
                logger.warning("surfsense: upload failed with status %d: %s", r.status_code, r.text[:300])
                return None

            data = r.json()
            return data

        except Exception as exc:
            logger.warning("surfsense: upload exception: %s", exc)
            return None
        finally:
            if own_client:
                await client.aclose()