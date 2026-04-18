import json
import re
import uuid
import time
import logging
import asyncio
import hashlib
import hmac
import mimetypes
import os
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, Any, List, Optional
from urllib.parse import quote
from curl_cffi.requests import AsyncSession
from .base import BaseProvider
from .qwen_utils.cookie_generator import generate_cookies, get_cookies
from .qwen_utils.generate_ua import BXUAGenerator
from .response_types import (
    Reasoning, Usage, ImageResponse, FinishReason,
    ToolCall, TextContent, Error,
    reasoning_to_dict, usage_to_dict, finish_reason_to_dict, tool_call_to_dict, error_to_dict
)

logger = logging.getLogger("flashy.qwen")

# ─────────────────────────────────────────────────────────────────────────────
# Tool-call prompt injection for Qwen (chat UI – no native function calling)
# We instruct the model to emit tool calls in a structured XML block, then
# parse them out of the streamed text and convert to the internal tool_call
# dict that the rest of the pipeline already handles.
# ─────────────────────────────────────────────────────────────────────────────

TOOL_SYSTEM_PREFIX = """You are a helpful AI coding assistant with access to tools.
When you need to use a tool, you MUST respond with ONLY the following XML block and nothing else before it:

<tool_call>{"name": "TOOL_NAME", "arguments": {JSON_ARGS}}</tool_call>

Do NOT add any explanation before the tool call. Just emit the XML block.
After the tool result is returned to you inside a <tool_result> block, you may call more tools or give your final answer as plain text.

Available tools:
"""

# Appended to an EXISTING system prompt (e.g. from opencode).
# Does NOT include a persona — only the format instructions.
TOOL_APPEND_SUFFIX = """

---
Tool calling: when you need to use a tool, respond with ONLY this XML block:
<tool_call>{"name": "TOOL_NAME", "arguments": {JSON_ARGS}}</tool_call>
After receiving a <tool_result> block, call another tool or give your final answer.

Available tools:
"""

TOOL_CALL_RE = re.compile(
    r'<tool_call>\s*(\{.*?\})\s*</tool_call>',
    re.DOTALL
)


def build_tool_system_prompt(tools: List[Dict], *, as_suffix: bool = False) -> str:
    """Convert OpenAI-format tool defs to a plain-text system prompt prefix/suffix."""
    base = TOOL_APPEND_SUFFIX if as_suffix else TOOL_SYSTEM_PREFIX
    lines = [base]
    for t in tools:
        fn = t.get("function", t)  # handle both wrapped {type, function} and bare dicts
        name = fn.get("name", "unknown")
        desc = fn.get("description", "")
        params = fn.get("parameters", {})
        lines.append(f"- **{name}**: {desc}")
        if params.get("properties"):
            for pname, pinfo in params["properties"].items():
                req = "required" if pname in params.get("required", []) else "optional"
                pdesc = pinfo.get("description", "")
                ptype = pinfo.get("type", "any")
                lines.append(f"  • {pname} ({ptype}, {req}): {pdesc}")
    lines.append("")
    return "\n".join(lines)



def inject_tools_into_messages(
    messages: List[Dict[str, str]],
    tools: List[Dict]
) -> List[Dict[str, str]]:
    """Inject tool descriptions into the system prompt (or insert one)."""
    if not tools:
        return messages

    out = list(messages)

    if out and out[0].get("role") == "system":
        # Existing system prompt (e.g. from opencode) — APPEND only the minimal
        # format instructions at the end. Do NOT prepend a new persona.
        tool_suffix = build_tool_system_prompt(tools, as_suffix=True)
        out[0] = {**out[0], "content": out[0]["content"] + tool_suffix}
    else:
        # No system prompt — insert our full one including the persona.
        tool_prefix = build_tool_system_prompt(tools, as_suffix=False)
        out.insert(0, {"role": "system", "content": tool_prefix})

    return out


def parse_tool_calls_from_text(text: str):
    """
    Scan completed text for <tool_call>...</tool_call> blocks.
    Returns (clean_text, list_of_tool_call_dicts).
    """
    tool_calls = []
    clean = TOOL_CALL_RE.sub("", text)

    for m in TOOL_CALL_RE.finditer(text):
        json_str = m.group(1).strip()

        # Strip markdown fences if the AI erroneously wrapped the JSON inside the XML
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        elif json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]

        json_str = json_str.strip()

        try:
            payload = json.loads(json_str)
            tc = {
                "id": f"call_{uuid.uuid4().hex[:8]}",
                "name": payload.get("name", ""),
                "arguments": json.dumps(payload.get("arguments", {}))
            }
            logger.info(f"[QWEN] Parsed tool call: name={tc['name']} args={tc['arguments'][:200]}")
            tool_calls.append(tc)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"[QWEN] Failed to parse tool call JSON: {e}\nRaw: {json_str[:500]}")
            clean += f"\n\n[System: Failed to parse tool call JSON: {e}]\n{json_str}"

    return clean.strip(), tool_calls


class QwenConversation:
    __slots__ = ("chat_id", "parent_id")

    def __init__(self, chat_id: str, parent_id: Optional[str] = None):
        self.chat_id = chat_id
        self.parent_id = parent_id


class QwenProvider(BaseProvider):
    URL = "https://chat.qwen.ai"
    _midtoken: Optional[str] = None
    _midtoken_uses: int = 0
    _ua_generator = BXUAGenerator()
    _file_cache: Dict[str, dict] = {}

    @staticmethod
    def _get_oss_headers(method: str, date_str: str, sts_data: dict, content_type: str) -> dict:
        bucket_name = sts_data.get('bucketname', 'qwen-webui-prod')
        file_path = sts_data.get('file_path', '')
        access_key_id = sts_data.get('access_key_id')
        access_key_secret = sts_data.get('access_key_secret')
        security_token = sts_data.get('security_token')
        headers = {
            'Content-Type': content_type,
            'x-oss-content-sha256': 'UNSIGNED-PAYLOAD',
            'x-oss-date': date_str,
            'x-oss-security-token': security_token,
            'x-oss-user-agent': 'aliyun-sdk-js/6.23.0 Chrome 132.0.0.0 on Windows 10 64-bit'
        }
        headers_lower = {k.lower(): v for k, v in headers.items()}
        canonical_headers_list = []
        signed_headers_list = []
        required_headers = ['content-md5', 'content-type', 'x-oss-content-sha256', 'x-oss-date',
                            'x-oss-security-token', 'x-oss-user-agent']
        for header_name in sorted(required_headers):
            if header_name in headers_lower:
                canonical_headers_list.append(f"{header_name}:{headers_lower[header_name]}")
                signed_headers_list.append(header_name)
        canonical_headers = '\n'.join(canonical_headers_list) + '\n'
        canonical_uri = f"/{bucket_name}/{quote(file_path, safe='/')}"
        canonical_request = f"{method}\n{canonical_uri}\n\n{canonical_headers}\n\nUNSIGNED-PAYLOAD"
        date_parts = date_str.split('T')
        date_scope = f"{date_parts[0]}/ap-southeast-1/oss/aliyun_v4_request"
        string_to_sign = f"OSS4-HMAC-SHA256\n{date_str}\n{date_scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"

        def sign(key, msg):
            return hmac.new(key, msg.encode() if isinstance(msg, str) else msg, hashlib.sha256).digest()

        date_key = sign(f"aliyun_v4{access_key_secret}".encode(), date_parts[0])
        region_key = sign(date_key, "ap-southeast-1")
        service_key = sign(region_key, "oss")
        signing_key = sign(service_key, "aliyun_v4_request")
        signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()
        headers['authorization'] = f"OSS4-HMAC-SHA256 Credential={access_key_id}/{date_scope},Signature={signature}"
        return headers

    @classmethod
    async def upload_file(
        cls,
        file_path: str,
        session: AsyncSession,
        cookies: dict,
        headers: dict,
        proxy: str = None
    ) -> Optional[dict]:
        if not os.path.isfile(file_path):
            logger.warning(f"[QWEN] File not found: {file_path}")
            return None

        file_data = open(file_path, 'rb').read()
        file_size = len(file_data)
        file_name = os.path.basename(file_path)

        mime_type, _ = mimetypes.guess_type(file_name)
        if not mime_type:
            mime_type = "application/octet-stream"

        content_hash = hashlib.md5(file_data).hexdigest()
        if content_hash in cls._file_cache:
            logger.info(f"[QWEN] Using cached file: {file_name}")
            return cls._file_cache[content_hash]

        ext = os.path.splitext(file_name)[1].lower()
        if ext in ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg'):
            file_type = "image"
            show_type = "image"
            file_class = "vision"
        elif ext in ('.mp4', '.avi', '.mov', '.mkv', '.webm'):
            file_type = "video"
            show_type = "video"
            file_class = "video"
        elif ext in ('.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a'):
            file_type = "audio"
            show_type = "audio"
            file_class = "audio"
        else:
            file_type = mime_type
            show_type = "file"
            file_class = "document"

        try:
            sts_resp = await session.post(
                f'{cls.URL}/api/v2/files/getstsToken',
                json={
                    "filename": file_name,
                    "filesize": file_size,
                    "filetype": mime_type
                },
                headers=headers,
                proxy=proxy
            )
            if sts_resp.status_code != 200:
                logger.warning(f"[QWEN] STS token request failed: {sts_resp.status_code}")
                return None

            sts_data = sts_resp.json()
            if not sts_data.get('success'):
                logger.warning(f"[QWEN] STS token error: {sts_data}")
                return None

            data = sts_data.get('data', {})
            file_url = data.get('file_url', '')
            file_id = data.get('file_id', '')

            date_str = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
            oss_headers = cls._get_oss_headers('PUT', date_str, data, mime_type)

            upload_resp = await session.put(
                file_url.split('?')[0],
                data=file_data,
                headers=oss_headers,
                proxy=proxy
            )
            if upload_resp.status_code not in (200, 204):
                logger.warning(f"[QWEN] File upload failed: {upload_resp.status_code}")
                return None

            now_ms = int(time.time() * 1000)
            file_obj = {
                "type": file_type,
                "file": {
                    "created_at": now_ms,
                    "data": {},
                    "filename": file_name,
                    "hash": None,
                    "id": file_id,
                    "meta": {
                        "name": file_name,
                        "size": file_size,
                        "content_type": mime_type
                    },
                    "update_at": now_ms,
                },
                "id": file_id,
                "url": file_url,
                "name": file_name,
                "collection_name": "",
                "progress": 0,
                "status": "uploaded",
                "greenNet": "success",
                "size": file_size,
                "error": "",
                "itemId": str(uuid.uuid4()),
                "file_type": mime_type,
                "showType": show_type,
                "file_class": file_class,
                "uploadTaskId": str(uuid.uuid4())
            }

            cls._file_cache[content_hash] = file_obj
            logger.info(f"[QWEN] File uploaded: {file_name} ({file_size} bytes, id={file_id})")
            return file_obj

        except Exception as e:
            logger.warning(f"[QWEN] File upload error: {e}")
            return None

    async def get_midtoken(self, session: AsyncSession, proxy: str = None, force_refresh: bool = False):
        if self._midtoken and self._midtoken_uses < 50 and not force_refresh:
            self._midtoken_uses += 1
            return self._midtoken

        try:
            r = await session.get("https://sg-wum.alibaba.com/w/wu.json", proxy=proxy)
            if r.status_code == 200:
                text = r.text
                match = re.search(r"(?:umx\.wu|__fycb)\('([^']+)'\)", text)
                if match:
                    self._midtoken = match.group(1)
                    self._midtoken_uses = 1
                    logger.info(f"[QWEN] New midtoken obtained: {self._midtoken[:20]}...")
                    return self._midtoken
        except Exception as e:
            logger.warning(f"[QWEN] Error fetching midtoken: {e}")
        return None

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:

        if not model or model == "G_2_5_FLASH":
            model = "qwen3.5-plus"

        proxy = kwargs.get("proxy")
        tools = kwargs.get("tools")
        file_paths = kwargs.get("files") or []
        conversation: Optional[QwenConversation] = kwargs.get("conversation")
        
        # Advanced Features from kwargs
        chat_type = kwargs.get("chat_type", "t2t") # t2t, search, deep_research
        thinking_enabled = kwargs.get("thinking_enabled", True)
        thinking_mode = kwargs.get("thinking_mode", "Auto") # Auto, Thinking, Fast

        logger.info(f"[QWEN] generate_stream | model={model} | chat_type={chat_type} | thinking={thinking_enabled} | files={len(file_paths)} | conv={'resume' if conversation else 'new'}")

        is_openai_pass_through = kwargs.get("is_openai_pass_through", False)

        if tools:
            effective_messages = inject_tools_into_messages(messages, tools)
        else:
            effective_messages = messages

        # Cookie generation — use async manager if initialized, else generate fresh
        try:
            cookies_data = await get_cookies()
            if not cookies_data.get("ssxmod_itna"):
                raise ValueError("empty cache")
        except Exception:
            cookies_data = generate_cookies()

        # Generate bx-ua header from fingerprint
        raw_fingerprint = cookies_data.get("rawData") or ""
        bx_ua = ""
        if raw_fingerprint:
            try:
                bx_ua = self._ua_generator.generate(raw_fingerprint)
            except Exception as e:
                logger.warning(f"[QWEN] Failed to generate bx-ua: {e}")

        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": self.URL,
            "referer": f"{self.URL}/",
            "sec-ch-ua": '"Google Chrome";v="136", "Chromium";v="136", "Not.A/Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
            "x-source": "web"
        }

        if bx_ua:
            headers["bx-ua"] = bx_ua

        safe_cookies = {}
        if cookies_data:
            for k, v in cookies_data.items():
                safe_cookies[k] = str(v) if not isinstance(v, str) else v

        max_attempts = 3
        for attempt in range(max_attempts):
            async with AsyncSession(
                impersonate="chrome",
                headers=headers,
                cookies=safe_cookies if safe_cookies else None,
                proxy=proxy
            ) as session:
                try:
                    # 0. Initial Auth Call
                    auth_resp = await session.get(f'{self.URL}/api/v1/auths/')
                    
                    # 1. Get midtoken (Force refresh on retry)
                    midtoken = await self.get_midtoken(session, proxy, force_refresh=(attempt > 0))
                    if midtoken:
                        session.headers['bx-umidtoken'] = midtoken
                        session.headers['bx-v'] = '2.5.31'

                    # 1.5 Upload files if any
                    uploaded_files = []
                    if file_paths:
                        req_headers = dict(session.headers)
                        for fp in file_paths:
                            file_obj = await self.upload_file(
                                fp, session, safe_cookies, req_headers, proxy
                            )
                            if file_obj:
                                uploaded_files.append(file_obj)

                    # 2. Determine chat_mode
                    effective_chat_mode = "normal"
                    if chat_type == "search":
                        effective_chat_mode = "search"
                    elif chat_type == "deep_research":
                        effective_chat_mode = "deep_research"

                    # 3. Create Chat (only if no existing conversation)
                    if conversation is None:
                        chat_payload = {
                            "title": "New Chat",
                            "models": [model],
                            "chat_mode": effective_chat_mode,
                            "chat_type": chat_type,
                            "timestamp": int(time.time() * 1000)
                        }

                        resp = await session.post(f'{self.URL}/api/v2/chats/new', json=chat_payload)
                        
                        if resp.status_code == 429 or (resp.status_code == 200 and not resp.json().get('success')):
                            if attempt < max_attempts - 1:
                                logger.warning(f"[QWEN] Rate limit/Error on chat creation (attempt {attempt+1}). Retrying...")
                                self._midtoken = None
                                await asyncio.sleep(1.5 * (attempt + 1))
                                continue
                            else:
                                yield error_to_dict(Error(f"Qwen Rate Limit: {resp.status_code} - {resp.text}"))
                                return

                        data = resp.json()
                        chat_id = data['data']['id']
                        conversation = QwenConversation(chat_id=chat_id)
                        yield {"conversation": conversation}
                    else:
                        chat_id = conversation.chat_id

                    # 4. Build prompt
                    # When resuming a conversation, Qwen already has the history via parent_id.
                    # Only send the latest user message to avoid duplication.
                    if conversation and conversation.parent_id:
                        source_messages = [m for m in effective_messages if m.get("role") == "user"][-1:]
                        if not source_messages:
                            source_messages = effective_messages[-1:]
                    else:
                        source_messages = effective_messages

                    prompt_parts = []
                    for msg in source_messages:
                        role = msg.get("role", "user")
                        raw_content = msg.get("content")

                        if isinstance(raw_content, list):
                            content = "\n".join(
                                item.get("text", "")
                                for item in raw_content
                                if isinstance(item, dict) and item.get("type") == "text"
                            )
                        else:
                            content = raw_content or ""

                        if role == "system":
                            prompt_parts.append(f"[System Instructions]\n{content}\n")
                        elif role == "user":
                            prompt_parts.append(content)
                        elif role == "assistant":
                            tool_calls = msg.get("tool_calls")
                            if tool_calls:
                                for tc in tool_calls:
                                    fn = tc.get("function", {})
                                    tc_name = fn.get("name", "unknown")
                                    tc_args = fn.get("arguments", "{}")
                                    tc_json = json.dumps({"name": tc_name, "arguments": json.loads(tc_args) if isinstance(tc_args, str) else tc_args})
                                    prompt_parts.append(
                                        f'<tool_call>' + tc_json + '</tool_call>'
                                    )
                            if content:
                                prompt_parts.append(f"[Assistant]\n{content}")
                        elif role == "tool":
                            tool_name = msg.get("name", "") or msg.get("tool_call_id", "tool")
                            prompt_parts.append(f'<tool_result name="{tool_name}">\n{content}\n</tool_result>')

                    full_prompt = "\n\n".join(p for p in prompt_parts if p)
                    msg_id = str(uuid.uuid4())

                    # Feature Config — two distinct structures depending on thinking state
                    # Qwen API expects different fields when thinking is on vs off
                    if thinking_enabled:
                        feature_config = {
                            "auto_thinking": thinking_mode == "Auto",
                            "thinking_mode": thinking_mode,
                            "thinking_enabled": True,
                            "output_schema": "phase",
                            "research_mode": "normal" if chat_type != "deep_research" else "deep",
                            "auto_search": chat_type in ("search", "deep_research")
                        }
                    else:
                        feature_config = {
                            "thinking_enabled": False,
                            "output_schema": "phase",
                            "thinking_budget": 81920
                        }

                    msg_payload = {
                        "stream": True,
                        "incremental_output": True,
                        "chat_id": chat_id,
                        "chat_mode": effective_chat_mode,
                        "model": model,
                        "parent_id": conversation.parent_id if conversation else None,
                        "messages": [
                            {
                                "fid": msg_id,
                                "parentId": conversation.parent_id if conversation else None,
                                "childrenIds": [],
                                "role": "user",
                                "content": full_prompt,
                                "user_action": "chat",
                                "files": uploaded_files,
                                "models": [model],
                                "chat_type": chat_type,
                                "feature_config": feature_config,
                                "sub_chat_type": chat_type
                            }
                        ]
                    }

                    url = f'{self.URL}/api/v2/chat/completions?chat_id={chat_id}'
                    stream_resp = await session.post(url, json=msg_payload, stream=True)

                    if stream_resp.status_code != 200:
                        if stream_resp.status_code == 429 and attempt < max_attempts - 1:
                            self._midtoken = None
                            continue
                        yield error_to_dict(Error(f"Qwen Stream Error: {stream_resp.status_code}"))
                        return

                    buffer = ""
                    full_answer_text = ""
                    raw_chunk_count = 0
                    has_yielded_content = False

                    async for chunk_bytes in stream_resp.aiter_content():
                        buffer += chunk_bytes.decode('utf-8', errors='ignore')

                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()

                            if not line or line.startswith(':'):
                                continue

                            if line.startswith('data: '):
                                chunk_str = line[6:]

                                if chunk_str == '[DONE]':
                                    break

                                try:
                                    chunk_data = json.loads(chunk_str)
                                    raw_chunk_count += 1
                                    # Track parent_id for conversation continuity
                                    if "response.created" in chunk_data:
                                        resp_id = chunk_data.get("response.created", {}).get("response_id")
                                        if resp_id and conversation:
                                            conversation.parent_id = resp_id

                                    choices = chunk_data.get("choices", [])
                                    if not choices: continue

                                    choice = choices[0]
                                    delta = choice.get("delta", {})
                                    phase = delta.get("phase")
                                    content = delta.get("content")
                                    finish_reason = choice.get("finish_reason")

                                    if phase == "think":
                                        if content:
                                            yield reasoning_to_dict(Reasoning(content))

                                    elif phase == "answer":
                                        if content:
                                            full_answer_text += content
                                            if not tools:
                                                yield {"text": content}
                                            else:
                                                if "<tool_call" not in full_answer_text:
                                                    yield {"text": content}
                                                    has_yielded_content = True

                                        if finish_reason:
                                            if tools and full_answer_text:
                                                clean_text, parsed_tool_calls = parse_tool_calls_from_text(full_answer_text)
                                                if parsed_tool_calls:
                                                    for tc in parsed_tool_calls:
                                                        tc_obj = ToolCall(
                                                            id=tc["id"],
                                                            name=tc["name"],
                                                            arguments=tc["arguments"]
                                                        )
                                                        yield tool_call_to_dict(tc_obj)
                                                    yield finish_reason_to_dict(FinishReason("tool_calls"))
                                                    return
                                                elif not has_yielded_content:
                                                    if clean_text:
                                                        yield {"text": clean_text}
                                            yield finish_reason_to_dict(FinishReason("stop"))
                                except json.JSONDecodeError:
                                    continue
                    
                    # Successfully finished a stream
                    return

                except Exception as e:
                    logger.exception(f"[QWEN] Unhandled exception on attempt {attempt+1}: {e}")
                    if attempt < max_attempts - 1:
                        self._midtoken = None
                        await asyncio.sleep(1)
                        continue
                    yield error_to_dict(Error(f"Qwen Connection error: {str(e)}"))
                    return

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        """Fetch available models dynamically from Qwen API."""
        try:
            async with AsyncSession(
                impersonate="chrome",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
                    "Accept": "application/json",
                    "Origin": cls.URL,
                    "Referer": f"{cls.URL}/"
                }
            ) as session:
                resp = await session.get(f"{cls.URL}/api/models")
                if resp.status_code == 200:
                    data = resp.json()
                    models_data = data.get("data", [])
                    return [
                        {
                            "id": m["id"],
                            "name": m.get("name", m["id"]),
                            "description": m.get("info", {}).get("meta", {}).get("short_description", ""),
                            "max_context": m.get("info", {}).get("meta", {}).get("max_context_length", 0)
                        }
                        for m in models_data
                        if m.get("info", {}).get("is_active", False)
                    ]
        except Exception as e:
            logger.warning(f"[QWEN] Error fetching models dynamically: {e}")

        # Fallback to hardcoded list if API fails
        return [
            {"id": "qwen3.6-plus", "name": "Qwen3.6-Plus"},
            {"id": "qwen3.5-plus", "name": "Qwen3.5-Plus"},
            {"id": "qwen3.5-flash", "name": "Qwen3.5-Flash"},
            {"id": "qwen3.5-397b-a17b", "name": "Qwen3.5-397B-A17B"},
            {"id": "qwen3.5-122b-a10b", "name": "Qwen3.5-122B-A10B"},
            {"id": "qwen3.5-27b", "name": "Qwen3.5-27B"},
            {"id": "qwen3.5-35b-a3b", "name": "Qwen3.5-35B-A3B"},
            {"id": "qwen3.5-omni-plus", "name": "Qwen3.5-Omni-Plus"},
            {"id": "qwen-max-latest", "name": "Qwen2.5-Max"},
            {"id": "qwen3-coder-plus", "name": "Qwen3-Coder"}
        ]
