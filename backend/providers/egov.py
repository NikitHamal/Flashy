"""
eGov Chat AI provider for Flashy.

Reverse-engineered from https://egov-chat-ai.e.gov.ph/ (Philippine government AI chat).
The site is a Next.js App Router app using React Server Actions:

  Chat action (hash: e9cdae80f2464df764330696f476c324ccbfd7cb):
    POST /chat?model=<model>&scope=<scope>
    Headers: Next-Action, Content-Type: text/plain;charset=UTF-8
    Body: JSON array [scope, model, sessionId, userMessage, conversationHistory]

  Upload action (hash: 75c980102f4a31e2fc1369cda63e30e9f538a02c):
    POST /chat?model=<model>&scope=<scope>
    Headers: Next-Action, Content-Type: multipart/form-data
    Body: FormData with fields: 0=["$K1"], 1_files=<file>, 1_model=<model>
    Returns: file_data object {filename, original_filename, mime_type, cdnUrl}

  Streaming format: RSC (React Server Components) NDJSON-like stream
    Lines like: <id>:{"curr":"<text>","next":"$@<nextId>"}
    Final line: <id>:{}

  Models:
    AI1 - accepts jpeg/jpg/png/heif/pdf (scope: ph = "Juan" Philippine AI, global = Google model)
    AI2 - accepts jpeg/jpg/png/gif (different model)

  Scopes: "ph" (Philippines-specific), "global" (general knowledge)
"""

import asyncio
import json
import logging
import re
import secrets
import time
import uuid
from typing import AsyncGenerator, Dict, Any, List, Optional
from dataclasses import dataclass

import httpx

from .base import BaseProvider

logger = logging.getLogger("flashy.egov")

# ========================= Configuration =========================

EGOV_BASE_URL = "https://egov-chat-ai.e.gov.ph"
CHAT_ACTION_HASH = "e9cdae80f2464df764330696f476c324ccbfd7cb"
UPLOAD_ACTION_HASH = "75c980102f4a31e2fc1369cda63e30e9f538a02c"
REQUEST_TIMEOUT = 120
UPLOAD_TIMEOUT = 60
UPLOAD_ACCEPT_TYPES_AI1 = {"image/jpeg", "image/jpg", "image/png", "image/heif", "application/pdf"}
UPLOAD_ACCEPT_TYPES_AI2 = {"image/jpeg", "image/jpg", "image/png", "image/gif"}
CDN_BASE = "https://storage.googleapis.com/egovai-bucket/"

# ========================= RSC Stream Parser =========================

def parse_rsc_stream(text: str) -> str:
    """
    Parse React Server Components streaming format and extract accumulated text.

    The stream consists of lines in the format:
        <id>:<json>
    Where JSON objects have "curr" (current text chunk) and "next" (reference to next chunk).

    We accumulate all "curr" values to build the full response text.
    """
    chunks: Dict[str, str] = {}
    next_refs: Dict[str, str] = {}

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        colon_idx = line.find(":")
        if colon_idx < 0:
            continue

        line_id = line[:colon_idx]
        payload = line[colon_idx + 1:]

        if not payload or payload.startswith('"$'):
            continue

        try:
            data = json.loads(payload)
        except (json.JSONDecodeError, ValueError):
            continue

        if isinstance(data, dict):
            if "curr" in data:
                chunks[line_id] = data.get("curr", "")
                next_id = data.get("next", "")
                if next_id and next_id.startswith("$@"):
                    next_refs[line_id] = next_id[2:]
            elif "streamValue" in data:
                sv = data["streamValue"]
                if isinstance(sv, dict) and "next" in sv:
                    next_val = sv["next"]
                    if isinstance(next_val, str) and next_val.startswith("$@"):
                        pass

    # Sort chunks by their line IDs (they come in order) and concatenate
    ordered_ids = sorted(chunks.keys(), key=lambda x: int(x) if x.isdigit() else float('inf'))
    result = ""
    for cid in ordered_ids:
        result += chunks[cid]

    return result


async def parse_rsc_stream_async(response: httpx.Response) -> str:
    """
    Parse an RSC streaming response in real-time, yielding text chunks as they arrive.

    Yields incremental text deltas.
    """
    prev_text = ""
    accumulated = ""

    async for line in response.aiter_lines():
        line = line.strip()
        if not line:
            continue

        colon_idx = line.find(":")
        if colon_idx < 0:
            continue

        payload = line[colon_idx + 1:]

        if not payload or payload.startswith('"$'):
            # Handle special RSC references like "$Sui.streamable.value"
            continue

        try:
            data = json.loads(payload)
        except (json.JSONDecodeError, ValueError):
            continue

        if not isinstance(data, dict):
            continue

        if "curr" in data:
            curr_text = data.get("curr", "")
            if curr_text:
                # Yield only the new delta
                new_text = accumulated + curr_text
                delta = new_text[len(accumulated):]
                accumulated = new_text
                if delta:
                    yield delta


# ========================= Upload Client =========================

async def upload_file(
    file_path: str,
    model: str = "AI1",
    client: Optional[httpx.AsyncClient] = None,
) -> Optional[Dict[str, Any]]:
    """
    Upload a file to eGov's GCS bucket via the Next.js server action.

    Returns file_data dict with: filename, original_filename, mime_type, cdnUrl
    or None on failure.
    """
    import os
    import mimetypes

    filename = os.path.basename(file_path)
    mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

    with open(file_path, "rb") as f:
        file_data = f.read()

    boundary = secrets.token_hex(16)

    body = b""
    # Required closure field for Next.js server actions
    body += f"------{boundary}\r\nContent-Disposition: form-data; name=\"0\"\r\n\r\n[\"$K1\"]\r\n".encode()
    # File field (prefixed with "1_" per Next.js convention)
    body += f"------{boundary}\r\nContent-Disposition: form-data; name=\"1_files\"; filename=\"{filename}\"\r\nContent-Type: {mime_type}\r\n\r\n".encode()
    body += file_data
    body += f"\r\n------{boundary}\r\nContent-Disposition: form-data; name=\"1_model\"\r\n\r\n{model}\r\n".encode()
    body += f"------{boundary}--\r\n".encode()

    headers = {
        "Next-Action": UPLOAD_ACTION_HASH,
        "Accept": "text/x-component",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "Origin": EGOV_BASE_URL,
        "Referer": f"{EGOV_BASE_URL}/chat?model={model}&scope=global",
        "Content-Type": f"multipart/form-data; boundary=----{boundary}",
    }

    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=UPLOAD_TIMEOUT, follow_redirects=True)

    try:
        r = await client.post(
            f"{EGOV_BASE_URL}/chat?model={model}&scope=global",
            content=body,
            headers=headers,
        )

        if r.status_code != 200:
            logger.warning("egov: upload failed with status %d: %s", r.status_code, r.text[:500])
            return None

        # Parse the RSC response for file data
        text = r.text
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            colon_idx = line.find(":")
            if colon_idx < 0:
                continue
            payload = line[colon_idx + 1:]
            if not payload:
                continue
            try:
                data = json.loads(payload)
                if isinstance(data, dict) and "file_data" in data:
                    return data["file_data"]
                if isinstance(data, list) and len(data) > 0:
                    for item in data:
                        if isinstance(item, dict) and "file_data" in item:
                            return item["file_data"]
            except (json.JSONDecodeError, ValueError):
                continue

        # If we got a 200 but no file_data in response, the upload might still
        # have succeeded - construct CDN URL from expected pattern
        # The server stores files at: https://storage.googleapis.com/egovai-bucket/<hash>.<ext>
        # Since we can't get the hash from the empty response, log a warning
        logger.warning("egov: upload returned 200 but no file_data in response: %s", text[:500])
        return None

    except Exception as exc:
        logger.warning("egov: upload exception: %s", exc)
        return None
    finally:
        if own_client:
            await client.aclose()


# ========================= Provider =========================

class EGovProvider(BaseProvider):
    """
    Provider for eGov Chat AI (https://egov-chat-ai.e.gov.ph/).

    Supports two models:
      - AI1: Philippine AI (scope=ph) / Google model (scope=global), supports images & PDFs
      - AI2: Alternative model, supports images including GIFs

    Two scopes:
      - "ph": Philippines-specific knowledge (AI1 becomes "Juan")
      - "global": General knowledge
    """

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        return [
            {
                "id": "AI1",
                "name": "eGov AI1",
                "capabilities": {
                    "chat": True,
                    "stream": True,
                    "vision": True,
                    "reasoning": False,
                    "tools": False,
                },
            },
            {
                "id": "AI1-ph",
                "name": "eGov AI1 (Philippines)",
                "capabilities": {
                    "chat": True,
                    "stream": True,
                    "vision": True,
                    "reasoning": False,
                    "tools": False,
                },
            },
            {
                "id": "AI2",
                "name": "eGov AI2",
                "capabilities": {
                    "chat": True,
                    "stream": True,
                    "vision": True,
                    "reasoning": False,
                    "tools": False,
                },
            },
            {
                "id": "AI2-ph",
                "name": "eGov AI2 (Philippines)",
                "capabilities": {
                    "chat": True,
                    "stream": True,
                    "vision": True,
                    "reasoning": False,
                    "tools": False,
                },
            },
        ]

    def _resolve_scope_and_model(self, model: str) -> tuple:
        """
        Resolve model string to (scope, model_id).

        Models:
          - "AI1" or "AI1-global" -> ("global", "AI1")
          - "AI1-ph" -> ("ph", "AI1")
          - "AI2" or "AI2-global" -> ("global", "AI2")
          - "AI2-ph" -> ("ph", "AI2")
          - Default -> ("global", "AI1")
        """
        model_lower = (model or "").lower().strip()

        if model_lower.endswith("-ph"):
            scope = "ph"
            model_id = model_lower[:-3].upper()
            if model_id not in ("AI1", "AI2"):
                model_id = "AI1"
            return scope, model_id

        if model_lower.endswith("-global"):
            model_id = model_lower[:-7].upper()
            if model_id not in ("AI1", "AI2"):
                model_id = "AI1"
            return "global", model_id

        if model_lower in ("ai1", "ai2"):
            return "global", model_lower.upper()

        return "global", "AI1"

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "",
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        logger.info("egov: generate_stream model=%s messages=%d", model, len(messages))

        scope, model_id = self._resolve_scope_and_model(model)
        session_id = secrets.token_hex(16)

        # Build user message content parts
        content_parts: List[Dict[str, Any]] = []

        # Process messages into a single prompt
        system_text = ""
        conversation_history: List[Dict[str, Any]] = []
        user_text = ""

        for i, msg in enumerate(messages):
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        elif item.get("type") == "image_url":
                            url = item.get("image_url", {})
                            if isinstance(url, dict):
                                url = url.get("url", "")
                            if url:
                                content_parts.append({"type": "image", "image": url})
                content = "\n".join(text_parts)

            if not content and not any(
                isinstance(msg.get("content"), list) and
                any(it.get("type") == "image_url" for it in msg.get("content", []) if isinstance(it, dict))
                for m in [msg]
            ):
                continue

            if role == "system":
                system_text += content + "\n"
            elif role == "assistant":
                conversation_history.append({
                    "role": "assistant",
                    "content": [{"type": "text", "text": content}],
                })
            else:
                if i == len(messages) - 1:
                    # Last user message - use as the current message
                    user_text = content
                else:
                    conversation_history.append({
                        "role": "user",
                        "content": [{"type": "text", "text": content}],
                    })

        # Build the current user message
        if user_text:
            content_parts.append({"type": "text", "text": user_text})

        if not content_parts:
            yield {"error": "egov: no content to send"}
            return

        # Prepend system text to user message if present
        if system_text.strip():
            for i, part in enumerate(content_parts):
                if part.get("type") == "text":
                    content_parts[i] = {"type": "text", "text": f"[System Instructions]\n{system_text.strip()}\n\n{part['text']}"}
                    break
            else:
                content_parts.insert(0, {"type": "text", "text": f"[System Instructions]\n{system_text.strip()}"})

        user_message = {
            "role": "user",
            "content": content_parts,
        }

        # Handle file uploads if files kwarg is provided
        files = kwargs.get("files", [])
        if files:
            async with httpx.AsyncClient(timeout=UPLOAD_TIMEOUT, follow_redirects=True) as upload_client:
                for file_path in files:
                    file_data = await upload_file(file_path, model=model_id, client=upload_client)
                    if file_data and file_data.get("cdnUrl"):
                        content_parts.insert(0, {
                            "type": "image",
                            "image": file_data["cdnUrl"],
                        })
                    elif file_data and file_data.get("filename"):
                        content_parts.insert(0, {
                            "type": "image",
                            "image": f"{CDN_BASE}{file_data['filename']}",
                        })

        # Build the request body
        body = json.dumps([scope, model_id, session_id, user_message, conversation_history])

        headers = {
            "Content-Type": "text/plain;charset=UTF-8",
            "Next-Action": CHAT_ACTION_HASH,
            "Accept": "text/x-component",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
            "Origin": EGOV_BASE_URL,
            "Referer": f"{EGOV_BASE_URL}/chat?model={model_id}&scope={scope}",
        }

        has_content = False
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
                async with client.stream(
                    "POST",
                    f"{EGOV_BASE_URL}/chat?model={model_id}&scope={scope}",
                    content=body,
                    headers=headers,
                ) as resp:
                    if resp.status_code != 200:
                        error_body = await resp.aread()
                        yield {"error": f"egov: HTTP {resp.status_code}: {error_body.decode('utf-8', errors='replace')[:300]}"}
                        return

                    async for delta in parse_rsc_stream_async(resp):
                        if delta:
                            has_content = True
                            yield {"text": delta}

        except Exception as exc:
            logger.exception("egov: stream error: %s", exc)
            yield {"error": f"egov: stream error: {exc}"}
            return

        if not has_content:
            yield {"is_final": True, "finish_reason": "stop"}
        else:
            yield {"is_final": True, "finish_reason": "stop"}