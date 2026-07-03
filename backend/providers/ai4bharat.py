"""
AI4Bharat Arena provider for Flashy.

Reverse-engineered from https://arena.ai4bharat.org/ (Indic LLM Arena).
The arena exposes a Django/DRF backend that:
  - accepts POST /auth/anonymous/ to mint a guest token
  - allows 20 messages / 3 sessions per guest token
  - streams chat completions in a custom newline protocol:
        a0:"<json-stringified-text-chunk>"
        ad:{"finishReason":"stop"|"error"}
  - embeds the model id as `modelId` INSIDE the assistant message object
  - is keyed by X-Anonymous-Token: <uuid>

This provider maintains an in-memory pool of anonymous tokens and round-robins
across them, retiring tokens that hit the message limit.
"""
import asyncio
import json
import logging
import time
import uuid
from typing import AsyncGenerator, Dict, Any, List, Optional

import httpx

# ========================= Tool injection =========================

def _format_tools_xml(tools: List[Dict[str, Any]]) -> str:
    """Convert OpenAI tool format to XML block for prompt injection."""
    parts = ["\n\n## Available Tools"]
    for t in tools:
        fn = t.get("function", t) if isinstance(t, dict) else {}
        name = fn.get("name", "unknown")
        desc = fn.get("description", "")
        params = fn.get("parameters", {})
        parts.append(f'\n<tool name="{name}">')
        if desc:
            parts.append(f"<description>{desc}</description>")
        props = (params or {}).get("properties", {})
        required = set((params or {}).get("required", []))
        if props:
            parts.append("<parameters>")
            for pname, pinfo in props.items():
                ptype = pinfo.get("type", "string")
                req = " required=\"true\"" if pname in required else ""
                pdesc = pinfo.get("description", "")
                parts.append(f'  <param name="{pname}" type="{ptype}"{req}>{pdesc}</param>')
            parts.append("</parameters>")
        parts.append(f"</tool>")
    parts.append("\n\nTo call a tool, respond with XML:\n<tool_call>\n<name>tool_name</name>\n<args>\n<arg_name>value</arg_name>\n</args>\n</tool_call>")
    return "\n".join(parts)

from .base import BaseProvider

logger = logging.getLogger("flashy.ai4bharat")

# ========================= Configuration =========================

AI4BHARAT_API_URL = "https://backend.arena.ai4bharat.co"
GUEST_MSG_LIMIT = 20
GUEST_SESSION_LIMIT = 3
TOKEN_POOL_SIZE = 12
TOKEN_WARN_BUDGET = 15
REQUEST_TIMEOUT = 60
MODELS_CACHE_TTL = 300

# ========================= Token pool =========================

_pool_lock = asyncio.Lock()
_token_pool: List[Dict[str, Any]] = []
_models_cache: List[Dict[str, Any]] = []
_models_cache_time: float = 0


async def _mint_anonymous_token() -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            f"{AI4BHARAT_API_URL}/auth/anonymous/",
            json={"display_name": "FlashyAI"},
        )
    if r.status_code != 200:
        raise RuntimeError(f"anonymous-auth failed: {r.status_code} {r.text[:200]}")
    data = r.json()
    token = data.get("anonymous_token") or (data.get("tokens") or {}).get("access")
    if not token:
        raise RuntimeError(f"anonymous-auth response missing token: {data}")
    return {
        "token": token,
        "message_count": 0,
        "session_count": 0,
        "last_used_ms": 0,
        "is_dead": False,
        "minted_ms": int(time.time() * 1000),
    }


async def _acquire_token(require_low_budget: bool = True) -> Dict[str, Any]:
    async with _pool_lock:
        candidates = [
            e for e in _token_pool
            if not e.get("is_dead")
            and (not require_low_budget or (
                e.get("message_count", 0) < TOKEN_WARN_BUDGET
                and e.get("session_count", 0) < GUEST_SESSION_LIMIT
            ))
        ]
        if candidates:
            candidates.sort(key=lambda e: (e.get("message_count", 0), e.get("session_count", 0)))
            return candidates[0]

        if len(_token_pool) < TOKEN_POOL_SIZE:
            entry = await _mint_anonymous_token()
            _token_pool.append(entry)
            logger.info("ai4bharat: minted new anon token (pool size %d)", len(_token_pool))
            return entry

        raise RuntimeError("All arena anon tokens exhausted; retry after a backoff")


async def _commit_token_use(token: str, *, message_used: bool = True, session_opened: bool = False):
    async with _pool_lock:
        for e in _token_pool:
            if e["token"] == token:
                if message_used:
                    e["message_count"] = e.get("message_count", 0) + 1
                if session_opened:
                    e["session_count"] = e.get("session_count", 0) + 1
                e["last_used_ms"] = int(time.time() * 1000)
                if e.get("message_count", 0) >= GUEST_MSG_LIMIT:
                    e["is_dead"] = True
                break


def _mark_token_dead(token: str):
    for e in _token_pool:
        if e["token"] == token:
            e["is_dead"] = True
            e["last_used_ms"] = int(time.time() * 1000)
            break


def pool_stats() -> Dict[str, Any]:
    live = [e for e in _token_pool if not e.get("is_dead")]
    return {
        "total": len(_token_pool),
        "live": len(live),
        "dead": len(_token_pool) - len(live),
        "total_messages_used": sum(e.get("message_count", 0) for e in _token_pool),
        "total_sessions_used": sum(e.get("session_count", 0) for e in _token_pool),
    }


# ========================= Low-level API client =========================

def _headers(token: str) -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-Anonymous-Token": token,
    }


async def _fetch_models_raw(token: str) -> List[Dict[str, Any]]:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"{AI4BHARAT_API_URL}/models/type/?model_type=LLM",
            headers=_headers(token),
        )
    if r.status_code == 401:
        _mark_token_dead(token)
        raise RuntimeError("anon token rejected on list_models")
    if r.status_code != 200:
        raise RuntimeError(f"list_models failed: {r.status_code}")
    return r.json()


async def _create_session(token: str, model_id: str) -> Dict[str, Any]:
    payload = {
        "mode": "direct",
        "model_a_id": model_id,
        "model_b_id": None,
        "session_type": "LLM",
        "metadata": {},
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            f"{AI4BHARAT_API_URL}/sessions/",
            headers=_headers(token),
            json=payload,
        )
    if r.status_code in (401, 403):
        _mark_token_dead(token)
        raise RuntimeError(f"arena auth rejected on create_session: {r.status_code}")
    if r.status_code == 400 and "limit" in r.text.lower():
        raise RuntimeError("session limit reached for this anon token")
    if r.status_code not in (200, 201):
        raise RuntimeError(f"create_session failed: {r.status_code} {r.text[:200]}")
    return r.json()


async def _stream_chat(
    token: str,
    session_id: str,
    user_content: str,
    model_id: str,
    user_message_id: str,
    assistant_message_id: str,
    parent_message_ids: List[str],
    language: str = "en",
) -> AsyncGenerator[Dict[str, Any], None]:
    payload = {
        "session_id": session_id,
        "messages": [
            {
                "id": user_message_id,
                "role": "user",
                "content": user_content,
                "parent_message_ids": parent_message_ids or [],
                "status": "pending",
                "language": language,
            },
            {
                "id": assistant_message_id,
                "role": "assistant",
                "content": "",
                "parent_message_ids": [user_message_id],
                "modelId": model_id,
                "status": "pending",
            },
        ],
    }

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        async with client.stream(
            "POST",
            f"{AI4BHARAT_API_URL}/messages/stream/",
            headers=_headers(token),
            json=payload,
        ) as resp:
            if resp.status_code in (401, 403):
                _mark_token_dead(token)
                yield {"error": f"arena auth rejected ({resp.status_code})"}
                return
            if resp.status_code != 200:
                body = await resp.aread()
                yield {"error": f"arena stream http {resp.status_code}: {body.decode('utf-8', errors='replace')[:300]}"}
                return

            async for raw_line in resp.aiter_lines():
                line = raw_line.strip()
                if not line:
                    continue
                if line.startswith("a0:"):
                    inner = line[3:]
                    try:
                        yield {"text": json.loads(inner)}
                    except json.JSONDecodeError:
                        try:
                            yield {"text": inner.encode().decode("unicode_escape")}
                        except Exception:
                            logger.warning("ai4bharat: undecodable a0: chunk: %r", inner[:200])
                elif line.startswith("ag:"):
                    inner = line[3:]
                    try:
                        yield {"thought": json.loads(inner)}
                    except json.JSONDecodeError:
                        yield {"thought": inner}
                elif line.startswith("ad:"):
                    inner = line[3:]
                    try:
                        meta = json.loads(inner)
                    except json.JSONDecodeError:
                        meta = {"finishReason": "stop"}
                    if meta.get("finishReason") == "error":
                        yield {"error": meta.get("error", "arena returned finishReason=error")}
                    else:
                        yield {"is_final": True, "finish_reason": meta.get("finishReason", "stop")}
                    return
                elif line.startswith("a3:"):
                    inner = line[3:]
                    try:
                        err = json.loads(inner)
                        yield {"error": f"arena error: {err}"}
                    except json.JSONDecodeError:
                        yield {"error": f"arena error: {inner[:200]}"}
                    return


# ========================= Provider =========================

# Curated model list (real UUIDs from the arena API, fetched 2025-06).
# These are the non-random-only LLM models available for direct chat.
# Used as fallback when live model fetch fails.
_CURATED_MODELS: List[Dict[str, Any]] = [
    {"id": "fadda998-e440-4c44-81b4-b0ecae27a0c5", "name": "Gemini 3.5 Flash", "provider": "google"},
    {"id": "7927d963-5444-4330-8bea-28d4b35694e5", "name": "Nemotron 3 Nano Omni 30B", "provider": "nvidia"},
    {"id": "d95f1077-9bd0-46e4-8dcd-c43227e87885", "name": "Nemotron 3 Super 120B", "provider": "nvidia"},
    {"id": "bb89dfa2-1b8e-4075-9567-0c6f4c6f621e", "name": "Gemma 4 26B A4B", "provider": "google"},
    {"id": "860f13ee-b21b-4508-a12f-7f5ac184df58", "name": "Gemma 4 31B", "provider": "google"},
    {"id": "ca7565b7-eee6-4503-9c26-cf5655d61f82", "name": "Gemini 3.1 Flash Lite", "provider": "google"},
    {"id": "a3581540-b86b-402f-b3d3-bdbc95e572ee", "name": "Sarvam 105B", "provider": "sarvam"},
    {"id": "8087217e-f01f-41b0-9d3a-885154d3d8e8", "name": "Sarvam 30B", "provider": "sarvam"},
    {"id": "1f228a49-deed-4660-9301-d149efe8b068", "name": "Gemini 3 Flash", "provider": "google"},
    {"id": "318878b7-c6a6-4c98-b228-b36ae505250c", "name": "Gemini 2.5 Flash", "provider": "google"},
    {"id": "864608e8-c05d-4ad0-bf46-ecc00b2045b6", "name": "Gemini 2.5 Flash Lite", "provider": "google"},
    {"id": "6783ab68-3b4b-42d2-b172-9a2d5076699b", "name": "GPT 5.5", "provider": "openai"},
    {"id": "2457f66a-e273-4d7c-8355-c14ee717f12a", "name": "GPT 5.4 Mini", "provider": "openai"},
    {"id": "c47fba6b-08b1-4b01-a5e6-af5d8ab8a7c0", "name": "GPT 5.4 Nano", "provider": "openai"},
    {"id": "a9f12d7e-7b08-4e1c-98ff-db4e82821b6d", "name": "GPT 5.4", "provider": "openai"},
]


class AI4BharatProvider(BaseProvider):

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        global _models_cache, _models_cache_time

        now = time.time()
        if _models_cache and (now - _models_cache_time) < MODELS_CACHE_TTL:
            return _models_cache

        try:
            entry = await _acquire_token(require_low_budget=False)
            raw = await _fetch_models_raw(entry["token"])
            models = []
            for m in raw:
                if not m.get("is_active", True):
                    continue
                if m.get("random_only", False):
                    continue
                model_id = m.get("id", "")
                display_name = m.get("display_name") or m.get("model_code") or model_id
                is_thinking = bool(m.get("is_thinking_model", False))
                models.append({
                    "id": model_id,
                    "name": display_name,
                    "capabilities": {
                        "chat": True,
                        "stream": True,
                        "vision": False,
                        "reasoning": is_thinking,
                        "tools": False,
                    },
                })
            if models:
                _models_cache = models
                _models_cache_time = now
                return models
        except Exception as exc:
            logger.warning("ai4bharat: failed to fetch live models: %s", exc)

        if _models_cache:
            return _models_cache

        return _CURATED_MODELS

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "",
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        logger.info("ai4bharat: generate_stream model=%s messages=%d", model, len(messages))

        try:
            entry = await _acquire_token(require_low_budget=False)
        except Exception as exc:
            yield {"error": f"ai4bharat: failed to acquire token: {exc}"}
            return

        token = entry["token"]

        models_list = await self.get_models()
        model_id = model
        if model_id:
            match = next((m for m in models_list if m["id"] == model_id), None)
            if not match:
                match = next((m for m in models_list if m["name"] == model_id), None)
                if match:
                    model_id = match["id"]
        if not model_id and models_list:
            model_id = models_list[0]["id"]

        if not model_id:
            yield {"error": "ai4bharat: no model available"}
            return

        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        parts.append(item.get("text", ""))
                content = "\n".join(parts)
            if not content:
                continue
            if role == "system":
                prompt_parts.append(f"[System]\n{content}")
            elif role == "assistant":
                prompt_parts.append(f"[Assistant]\n{content}")
            else:
                prompt_parts.append(content)

        prompt = "\n\n".join(prompt_parts)
        if not prompt.strip():
            prompt = messages[-1].get("content", "") if messages else "Hello"
            if isinstance(prompt, list):
                prompt = " ".join(
                    item.get("text", "") for item in prompt
                    if isinstance(item, dict) and item.get("type") == "text"
                )

        tools = kwargs.get("tools")
        if tools:
            prompt += _format_tools_xml(tools)

        try:
            sess = await _create_session(token, model_id)
        except Exception as exc:
            yield {"error": f"ai4bharat: failed to create session: {exc}"}
            return

        session_id = sess.get("id") or sess.get("session_id") or sess.get("uuid", "")
        if not session_id:
            yield {"error": f"ai4bharat: session creation returned no id: {sess}"}
            return

        user_msg_id = str(uuid.uuid4())
        asst_msg_id = str(uuid.uuid4())

        has_content = False
        try:
            async for chunk in _stream_chat(
                token=token,
                session_id=session_id,
                user_content=prompt,
                model_id=model_id,
                user_message_id=user_msg_id,
                assistant_message_id=asst_msg_id,
                parent_message_ids=[],
            ):
                if "error" in chunk:
                    yield chunk
                    return
                if "text" in chunk:
                    has_content = True
                    yield {"text": chunk["text"]}
                elif "thought" in chunk:
                    yield {"thought": chunk["thought"]}
                elif "is_final" in chunk:
                    await _commit_token_use(token, message_used=True, session_opened=True)
                    yield {"is_final": True, "finish_reason": chunk.get("finish_reason", "stop")}
                    return
        except Exception as exc:
            logger.exception("ai4bharat: stream error: %s", exc)
            yield {"error": f"ai4bharat: stream error: {exc}"}
            return

        if not has_content:
            await _commit_token_use(token, message_used=True, session_opened=True)
            yield {"is_final": True, "finish_reason": "stop"}