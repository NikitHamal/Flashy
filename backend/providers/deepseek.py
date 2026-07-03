import base64
import json
import logging
import os
import random
import string
import struct
import time
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

from curl_cffi.requests import AsyncSession
import wasmtime

from .base import BaseProvider

logger = logging.getLogger("flashy.deepseek")

API_BASE = "https://chat.deepseek.com/api"

HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Origin": "https://chat.deepseek.com",
    "Referer": "https://chat.deepseek.com/",
    "Sec-Ch-Ua": '"Not/A)Brand";v="99", "Chromium";v="148"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "X-App-Version": "2.0.0",
    "X-Client-Locale": "en_US",
    "X-Client-Platform": "web",
    "X-Client-Version": "2.0.0",
}

MODELS = [
    {"id": "deepseek/deepseek-v4-flash", "name": "DeepSeek-V4 Flash", "capabilities": {"chat": True, "stream": True, "reasoning": False}},
    {"id": "deepseek/deepseek-v4-pro", "name": "DeepSeek-V4 Pro", "capabilities": {"chat": True, "stream": True, "reasoning": True}},
]


def _random_string(length: int) -> str:
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def _generate_cookie() -> str:
    ts = int(time.time() * 1000)
    fr_id = str(uuid.uuid4()).replace("-", "")
    return (
        f"intercom-HWWAFSESTIME={ts}; "
        f"HWWAFSESID={_random_string(18)}; "
        f"_frid={fr_id}; "
        f"_fr_ssid={fr_id}; "
        f"_fr_pvid={fr_id}"
    )


def _messages_to_prompt(messages: List[Dict[str, Any]]) -> str:
    blocks = []
    system_content = ""
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if not content:
            continue
        if role == "system":
            system_content = content
        elif role == "assistant":
            blocks.append(f"<｜Assistant｜>{content}<｜end of sentence｜>")
        elif role == "user":
            text = content
            if system_content and not blocks:
                text = f"{system_content}\n\n{content}"
                system_content = ""
            blocks.append(f"<｜User｜>{text}")
        else:
            blocks.append(f"<｜User｜>{content}")
    return "".join(blocks)


_token_cache: Dict[str, Dict] = {}
_session_cache: Dict[str, Dict] = {}


class DeepSeekProvider(BaseProvider):
    """Official DeepSeek Chat provider (chat.deepseek.com).

    Session management:
    - Creates a session once and reuses it for subsequent messages
    - Uses parent_message_id to maintain conversation continuity
    - Creates a new session when context window is exceeded (error recovery)
    """

    def __init__(self):
        self._access_token: Optional[str] = None
        self._session_id: Optional[str] = None
        self._last_message_id: Optional[str] = None
        self._user_token: str = ""
        self._model_type: str = "chat"

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        return [{"id": m["id"], "name": m["name"], "capabilities": m["capabilities"]} for m in MODELS]

    async def _acquire_token(self, user_token: str) -> str:
        if self._access_token:
            return self._access_token
        logger.info("[DEEPSEEK] Acquiring access token...")
        async with AsyncSession(impersonate="chrome") as session:
            resp = await session.get(
                f"{API_BASE}/v0/users/current",
                headers={**HEADERS, "Authorization": f"Bearer {user_token}"},
                timeout=15,
            )
            if resp.status_code in (401, 403):
                raise RuntimeError("DeepSeek token invalid or expired")
            if resp.status_code != 200:
                raise RuntimeError(f"DeepSeek token acquisition failed: HTTP {resp.status_code}")
            data = resp.json()
            biz = data.get("data", {}).get("biz_data", {})
            access = biz.get("token", "")
            if not access:
                raise RuntimeError("DeepSeek: no access token in response")
            self._access_token = access
            logger.info("[DEEPSEEK] Access token acquired")
            return access

    async def _create_session(self, user_token: str, force: bool = False) -> str:
        if self._session_id and not force:
            return self._session_id

        token = await self._acquire_token(user_token)
        logger.info("[DEEPSEEK] Creating new session...")
        async with AsyncSession(impersonate="chrome") as session:
            resp = await session.post(
                f"{API_BASE}/v0/chat_session/create",
                headers={**HEADERS, "Authorization": f"Bearer {token}", "Cookie": _generate_cookie()},
                json={},
                timeout=15,
            )
            if resp.status_code != 200:
                raise RuntimeError(f"DeepSeek session creation failed: HTTP {resp.status_code}")
            data = resp.json()
            biz = data.get("data", {}).get("biz_data", {})
            sid = biz.get("id", "") or biz.get("chat_session", {}).get("id", "")
            if not sid:
                raise RuntimeError(f"DeepSeek: no session id in response: {json.dumps(biz)[:200]}")
            self._session_id = sid
            self._last_message_id = None
            logger.info(f"[DEEPSEEK] Session created: {sid}")
            return sid

    def reset_session(self) -> None:
        self._session_id = None
        self._last_message_id = None
        logger.info("[DEEPSEEK] Session reset for compaction")

    async def _solve_challenge(self, user_token: str) -> str:
        token = await self._acquire_token(user_token)
        async with AsyncSession(impersonate="chrome") as session:
            resp = await session.post(
                f"{API_BASE}/v0/chat/create_pow_challenge",
                headers={**HEADERS, "Authorization": f"Bearer {token}"},
                json={"target_path": "/api/v0/chat/completion"},
                timeout=15,
            )
            if resp.status_code != 200:
                raise RuntimeError(f"DeepSeek challenge failed: HTTP {resp.status_code}")
            data = resp.json()
            biz = data.get("data", {}).get("biz_data", {})
            challenge = biz.get("challenge", {})
            if not challenge:
                raise RuntimeError("DeepSeek: no challenge in response")

            algorithm = challenge.get("algorithm", "")
            challenge_str = challenge.get("challenge", "")
            salt = challenge.get("salt", "")
            difficulty = challenge.get("difficulty", 0)
            expire_at = challenge.get("expire_at", 0)
            signature = challenge.get("signature", "")

            answer = await self._calculate_hash(algorithm, challenge_str, salt, difficulty, expire_at)

            payload = {
                "algorithm": algorithm,
                "challenge": challenge_str,
                "salt": salt,
                "answer": int(answer) if answer == int(answer) else answer,
                "signature": signature,
                "target_path": "/api/v0/chat/completion",
            }
            return base64.b64encode(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()).decode()

    async def _calculate_hash(self, algorithm: str, challenge: str, salt: str, difficulty: int, expire_at: int) -> float:
        if algorithm != "DeepSeekHashV1":
            raise RuntimeError(f"Unsupported algorithm: {algorithm}")

        logger.info(f"[DEEPSEEK] Solving PoW: {algorithm}, difficulty={difficulty}")
        prefix = f"{salt}_{expire_at}_"

        store = wasmtime.Store()
        wasm_path = os.path.join(os.path.dirname(__file__), "deepseek_pow.wasm")
        with open(wasm_path, "rb") as f:
            wasm_bytes = f.read()
        module = wasmtime.Module(store.engine, wasm_bytes)
        instance = wasmtime.Instance(store, module, [])
        exports = instance.exports(store)

        wasm_solve = exports["wasm_solve"]
        add_to_stack = exports["__wbindgen_add_to_stack_pointer"]
        malloc = exports["__wbindgen_export_0"]
        start_fn = exports.get("__wbindgen_export_2")
        memory = exports["memory"]

        if start_fn:
            start_fn(store, 0, 0, 0)

        def encode_string(text: str) -> tuple[int, int]:
            encoded = text.encode("utf-8")
            ptr = int(malloc(store, len(encoded), 1))
            mem = memory.data_ptr(store)
            for i, b in enumerate(encoded):
                mem[ptr + i] = b
            return ptr, len(encoded)

        retptr = int(add_to_stack(store, -16))
        try:
            ptr0, len0 = encode_string(challenge)
            ptr1, len1 = encode_string(prefix)
            wasm_solve(store, retptr, ptr0, len0, ptr1, len1, float(difficulty))

            mem = memory.data_ptr(store)
            status_data = bytes(mem[retptr:retptr+4])
            value_data = bytes(mem[retptr+8:retptr+16])
            status = int.from_bytes(status_data, "little", signed=True)
            value = struct.unpack("<d", value_data)[0]

            logger.info(f"[DEEPSEEK] PoW solved: status={status} answer={value} (difficulty={difficulty})")

            if status == 0:
                raise RuntimeError("DeepSeek PoW: solver returned status 0 (no solution)")
            return value
        finally:
            add_to_stack(store, 16)

    def _determine_model_type(self, model: str, messages: List[Dict]) -> str:
        ml = model.lower()
        if "pro" in ml or "reason" in ml or "r1" in ml:
            return "expert"
        return "default"

    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        user_token = kwargs.get("token") or kwargs.get("deepseek_token", "")
        if not user_token:
            yield {"error": "DeepSeek requires a token. Add deepseek_token to config."}
            return

        self._user_token = user_token
        self._model_type = self._determine_model_type(model, messages)

        try:
            token = await self._acquire_token(user_token)
            session_id = await self._create_session(user_token)
            challenge_answer = await self._solve_challenge(user_token)

            prompt = _messages_to_prompt(messages)
            if not prompt.strip():
                yield {"error": "No user message found"}
                return

            payload = {
                "chat_session_id": session_id,
                "parent_message_id": self._last_message_id,
                "prompt": prompt,
                "model_type": self._model_type,
                "ref_file_ids": [],
                "search_enabled": kwargs.get("search_enabled", False),
                "thinking_enabled": kwargs.get("thinking_enabled", self._model_type == "expert"),
                "preempt": False,
            }

            headers = {
                **HEADERS,
                "Authorization": f"Bearer {token}",
                "Cookie": _generate_cookie(),
                "X-Ds-Pow-Response": challenge_answer,
                "Content-Type": "application/json",
            }

            async with AsyncSession(impersonate="chrome") as session:
                resp = await session.post(
                    f"{API_BASE}/v0/chat/completion",
                    headers=headers,
                    json=payload,
                    stream=True,
                    timeout=180,
                )

                if resp.status_code == 401:
                    self._access_token = None
                    yield {"error": "DeepSeek token expired. Please provide a new one."}
                    return
                if resp.status_code == 429:
                    yield {"error": "DeepSeek rate limited. Try again later."}
                    return
                if resp.status_code != 200:
                    error_text = resp.text[:300]
                    yield {"error": f"DeepSeek error ({resp.status_code}): {error_text}"}
                    return

                buffer = ""
                response_msg_id = None
                accumulated_text = ""
                accumulated_thought = ""
                current_path = ""
                search_results: List[Dict] = []
                has_content = False

                async for chunk_bytes in resp.aiter_content():
                    buffer += chunk_bytes.decode("utf-8", errors="ignore")
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
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

                        if data.get("response_message_id") and not response_msg_id:
                            response_msg_id = data["response_message_id"]

                        v = data.get("v")
                        p = data.get("p")

                        if isinstance(v, dict) and v.get("response"):
                            response_data = v["response"]
                            if response_data.get("thinking_enabled") is not None:
                                current_path = "thinking" if response_data.get("thinking_enabled") else "content"

                            fragments = response_data.get("fragments", [])
                            for frag in fragments:
                                if isinstance(frag, dict):
                                    if frag.get("results"):
                                        for r in frag["results"]:
                                            if r not in search_results:
                                                search_results.append(r)
                                    frag_content = frag.get("content", "")
                                    frag_type = frag.get("type", "")
                                    if frag_content:
                                        text = frag_content.replace("FINISHED", "")
                                        if frag_type == "THINK":
                                            if text != accumulated_thought:
                                                delta = text[len(accumulated_thought):] if text.startswith(accumulated_thought) else text
                                                if delta:
                                                    accumulated_thought = text
                                                    yield {"thought": delta}
                                        elif frag_type in ("ANSWER", "RESPONSE"):
                                            has_content = True
                                            if text != accumulated_text:
                                                delta = text[len(accumulated_text):] if text.startswith(accumulated_text) else text
                                                if delta:
                                                    accumulated_text = text
                                                    yield {"text": delta}

                        elif p == "response/fragments":
                            if isinstance(v, list):
                                for frag in v:
                                    if isinstance(frag, dict):
                                        frag_content = frag.get("content", "")
                                        frag_type = frag.get("type", "")
                                        if frag_content:
                                            text = frag_content.replace("FINISHED", "")
                                            if frag_type == "THINK":
                                                if text != accumulated_thought:
                                                    delta = text[len(accumulated_thought):] if text.startswith(accumulated_thought) else text
                                                    if delta:
                                                        accumulated_thought = text
                                                        yield {"thought": delta}
                                            elif frag_type in ("ANSWER", "RESPONSE"):
                                                has_content = True
                                                if text != accumulated_text:
                                                    delta = text[len(accumulated_text):] if text.startswith(accumulated_text) else text
                                                    if delta:
                                                        accumulated_text = text
                                                        yield {"text": delta}

                        elif isinstance(v, str):
                            text = v.replace("FINISHED", "")
                            if text:
                                if current_path == "thinking":
                                    if text != accumulated_thought:
                                        delta = text[len(accumulated_thought):] if text.startswith(accumulated_thought) else text
                                        if delta:
                                            accumulated_thought = text
                                            yield {"thought": delta}
                                else:
                                    has_content = True
                                    if text != accumulated_text:
                                        delta = text[len(accumulated_text):] if text.startswith(accumulated_text) else text
                                        if delta:
                                            accumulated_text = text
                                            yield {"text": delta}

                        if data.get("p") == "accumulated_token_usage" or (isinstance(v, (int, float)) and p == "accumulated_token_usage"):
                            yield {"usage": {"completion_tokens": int(v)}}

                if response_msg_id:
                    self._last_message_id = response_msg_id
                    logger.info(f"[DEEPSEEK] Updated last_message_id: {response_msg_id}")

                yield {"is_final": True, "finish_reason": "stop"}

        except RuntimeError as e:
            logger.error(f"[DEEPSEEK] Runtime error: {e}")
            self._access_token = None
            self._session_id = None
            yield {"error": str(e)}
        except Exception as e:
            logger.exception(f"[DEEPSEEK] Error: {e}")
            yield {"error": f"DeepSeek error: {str(e)}"}
