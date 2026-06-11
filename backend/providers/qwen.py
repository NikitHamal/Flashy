import asyncio
import logging
import time
from typing import AsyncGenerator, Dict, Any, List, Optional

from curl_cffi.requests import AsyncSession

from .base import BaseProvider
from .response_types import error_to_dict, Error
from .qwen_utils import (
    QwenConversation,
    get_midtoken,
    build_session_headers,
    prepare_cookies,
    generate_bx_ua,
    upload_file,
    get_models,
    resolve_messages,
    build_prompt,
    build_feature_config,
    build_msg_payload,
    resolve_chat_mode,
    StreamState,
    parse_stream_chunks,
    finalize_stream,
    check_waf_response,
)

logger = logging.getLogger("flashy.qwen")


class QwenProvider(BaseProvider):
    URL = "https://chat.qwen.ai"

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:

        # Standardize / Map generic or agent sub-models to valid active Qwen API model IDs
        original_model = model
        model_lower = (model or "").lower()
        if not model or model == "G_2_5_FLASH" or model == "G_3_0_FLASH" or "flash" in model_lower:
            model = "qwen3.7-plus"
        elif "235b" in model_lower or "max" in model_lower or "qwq" in model_lower:
            if "preview" in model_lower:
                model = "qwen3.6-max-preview"
            else:
                model = "qwen3.7-max"
        elif "coder" in model_lower or "plus" in model_lower:
            model = "qwen3.7-plus"
        else:
            model = "qwen3.7-plus"

        logger.info(f"[QWEN] Model resolved: original={original_model} -> mapped={model}")

        proxy = kwargs.get("proxy")
        tools = kwargs.get("tools")
        file_paths = kwargs.get("files") or []
        conversation: Optional[QwenConversation] = kwargs.get("conversation")
        chat_type = kwargs.get("chat_type", "t2t")
        thinking_enabled = kwargs.get("thinking_enabled", True)
        thinking_mode = kwargs.get("thinking_mode", "Auto")
        reasoning_effort = kwargs.get("reasoning_effort")
        stream = kwargs.get("stream", True)
        token = kwargs.get("token") or kwargs.get("qwen_api_key")
        if not token:
            try:
                from ..config import load_config
                config = load_config()
                token = config.get("qwen_api_token") or config.get("qwen_api_key")
            except Exception:
                token = None

        # Map reasoning_effort to thinking settings if provided
        if reasoning_effort is not None:
            if reasoning_effort in ("medium", "high"):
                thinking_enabled = True
                thinking_mode = "Auto" if reasoning_effort == "medium" else "Thinking"
            else:
                thinking_enabled = False
                thinking_mode = "Fast"

        logger.info(
            f"[QWEN] generate_stream | model={model} | chat_type={chat_type} | "
            f"thinking={thinking_enabled} | files={len(file_paths)} | "
            f"conv={'resume' if conversation else 'new'} | stream={stream}"
        )

        is_openai_pass_through = kwargs.get("is_openai_pass_through", False)
        logger.info(
            f"[QWEN] generate_stream | model={model} | pass_through={is_openai_pass_through} | "
            f"tools={len(tools) if tools else 0} | chat_type={chat_type}"
        )

        safe_cookies = await prepare_cookies()
        bx_ua = generate_bx_ua(safe_cookies) if safe_cookies else ""
        headers = build_session_headers(bx_ua)

        max_attempts = 5
        for attempt in range(max_attempts):
            async with AsyncSession(
                impersonate="chrome",
                headers=headers,
                cookies=safe_cookies if safe_cookies else None,
                proxy=proxy
            ) as session:
                try:
                    # Optional token auth check
                    if token:
                        if ";" in token or "=" in token:
                            for part in token.split(";"):
                                part = part.strip()
                                if "=" in part:
                                    k, v = part.split("=", 1)
                                    session.cookies[k.strip()] = v.strip()
                        else:
                            session.headers["Authorization"] = f"Bearer {token}" if not token.lower().startswith("bearer ") else token

                        try:
                            auth_resp = await session.get(f'{self.URL}/api/v1/auths/')

                            if auth_resp.status_code == 200:
                                logger.info(f"[QWEN] Token auth validated")
                            else:
                                logger.warning(f"[QWEN] Token auth returned {auth_resp.status_code}")
                        except Exception as e:
                            logger.warning(f"[QWEN] Token auth check failed: {e}")

                    midtoken = await get_midtoken(session, proxy, force_refresh=(attempt > 0))
                    if midtoken:
                        session.headers['bx-umidtoken'] = midtoken
                        session.headers['bx-v'] = '2.5.31'

                    uploaded_files = []
                    if file_paths:
                        req_headers = dict(session.headers)
                        for fp in file_paths:
                            file_obj = await upload_file(
                                fp, session, safe_cookies, req_headers, proxy
                            )
                            if file_obj:
                                uploaded_files.append(file_obj)

                    chat_mode = resolve_chat_mode(chat_type)

                    if conversation is None:
                        chat_payload = {
                            "title": "New Chat",
                            "models": [model],
                            "chat_mode": chat_mode,
                            "chat_type": chat_type,
                            "timestamp": int(time.time() * 1000),
                        }

                        resp = await session.post(f'{self.URL}/api/v2/chats/new', json=chat_payload)

                        # Check for WAF/captcha block
                        waf_error = check_waf_response(resp)
                        if waf_error:
                            if attempt >= max_attempts - 1:
                                yield error_to_dict(Error(f"Qwen WAF/Captcha blocked: {waf_error}"))
                                return
                            logger.warning(f"[QWEN] WAF/captcha detected (attempt {attempt+1}), retrying...")
                            get_midtoken._cached = None
                            await asyncio.sleep(2 * (attempt + 1))
                            continue

                        if resp.status_code == 429 or (resp.status_code == 200 and not resp.json().get('success')):
                            if attempt >= max_attempts - 1:
                                yield error_to_dict(Error(f"Qwen Rate Limit: {resp.status_code} - {resp.text}"))
                                return
                            logger.warning(f"[QWEN] Rate limit/Error on chat creation (attempt {attempt+1}). Retrying...")
                            get_midtoken._cached = None
                            await asyncio.sleep(2 * (attempt + 1))
                            continue

                        data = resp.json()
                        chat_id = data['data']['id']
                        conversation = QwenConversation(chat_id=chat_id)
                        yield {"conversation": conversation}
                    else:
                        chat_id = conversation.chat_id

                    tool_system_prompt, source_messages = resolve_messages(messages, tools, conversation, pass_through=is_openai_pass_through)
                    if is_openai_pass_through:
                        logger.info(f"[QWEN] Incoming messages count: {len(messages)}")
                        for i, m in enumerate(messages):
                            role = m.get("role", "?")
                            content_preview = str(m.get("content", ""))[:200] if m.get("content") else "(None)"
                            tc = m.get("tool_calls")
                            tci = m.get("tool_call_id")
                            logger.info(f"[QWEN]   msg[{i}]: role={role} content={content_preview} tool_calls={bool(tc)} tool_call_id={tci}")
                        logger.info(f"[QWEN] source_messages count: {len(source_messages)}")
                        logger.info(f"[QWEN] tool_system_prompt is None: {tool_system_prompt is None}")
                    full_prompt = build_prompt(tool_system_prompt, source_messages, pass_through=is_openai_pass_through)
                    if is_openai_pass_through and tools:
                        logger.info(f"[QWEN] Pass-through mode with {len(tools)} tools. Tool names: {[t.get('function', {}).get('name', t.get('name', 'unknown')) for t in tools]}")
                        logger.info(f"[QWEN] Full prompt (first 1500 chars):\n{full_prompt[:1500]}")
                        logger.info(f"[QWEN] Total prompt length: {len(full_prompt)} chars")
                    feature_config = build_feature_config(thinking_enabled, thinking_mode, chat_type)
                    msg_payload = build_msg_payload(
                        chat_id=chat_id,
                        model=model,
                        full_prompt=full_prompt,
                        parent_id=conversation.parent_id if conversation else None,
                        uploaded_files=uploaded_files,
                        chat_type=chat_type,
                        chat_mode=chat_mode,
                        feature_config=feature_config,
                        stream=stream,
                    )

                    url = f'{self.URL}/api/v2/chat/completions?chat_id={chat_id}'
                    stream_resp = await session.post(url, json=msg_payload, stream=stream)

                    # Check for WAF on stream response
                    waf_error = check_waf_response(stream_resp)
                    if waf_error:
                        if attempt >= max_attempts - 1:
                            yield error_to_dict(Error(f"Qwen WAF/Captcha blocked during stream: {waf_error}"))
                            return
                        logger.warning(f"[QWEN] WAF/captcha on stream (attempt {attempt+1}), retrying...")
                        get_midtoken._cached = None
                        await asyncio.sleep(2 * (attempt + 1))
                        continue

                    if stream_resp.status_code != 200:
                        if stream_resp.status_code == 429 and attempt >= max_attempts - 1:
                            yield error_to_dict(Error(f"Qwen Rate Limit during stream: {stream_resp.status_code}"))
                            return
                        yield error_to_dict(Error(f"Qwen Stream Error: {stream_resp.status_code}"))
                        return

                    if not stream:
                        # Non-streaming path
                        resp_json = stream_resp.json()
                        if resp_json.get("success") is False or resp_json.get("data", {}).get("code"):
                            yield error_to_dict(Error(f"Qwen API error: {resp_json}"))
                            return
                        choices = resp_json.get("choices", [])
                        if choices:
                            content = choices[0].get("message", {}).get("content", "")
                            if content:
                                yield {"text": content}
                        usage = resp_json.get("usage")
                        if usage:
                            yield {"usage": usage}
                        yield {"is_final": True, "finish_reason": "stop"}
                        return

                    # Streaming path
                    state = StreamState()
                    usage = None

                    async for chunk_bytes in stream_resp.aiter_content():
                        events = parse_stream_chunks(chunk_bytes, state, conversation, has_tools=bool(tools))
                        for ev in events:
                            if ev.get("is_final") and not state.has_any_content and attempt >= max_attempts - 1:
                                logger.warning(f"[QWEN] Empty stream with finish_reason={ev.get('finish_reason')}, retrying...")
                                continue
                            yield ev
                            if ev.get("is_final"):
                                return

                    logger.info(f"[QWEN] stream ended (text_len={len(state.full_answer_text)}, yielded={state.has_yielded_content})")

                    if not state.has_any_content and attempt >= max_attempts - 1:
                        logger.warning(f"[QWEN] Empty stream response (attempt {attempt+1}). Retrying with fresh conversation...")
                        conversation = None
                        get_midtoken._cached = None
                        await asyncio.sleep(2 * (attempt + 1))
                        continue

                    for ev in finalize_stream(state, has_tools=bool(tools), conversation=conversation):
                        yield ev
                    return

                except Exception as e:
                    logger.exception(f"[QWEN] Unhandled exception on attempt {attempt+1}: {e}")
                    if attempt >= max_attempts - 1:
                        yield error_to_dict(Error(f"Qwen Connection error: {str(e)}"))
                        return
                    await asyncio.sleep(2)
                    continue

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        from ..config import load_config
        try:
            config = load_config()
            token = config.get("qwen_api_token") or config.get("qwen_api_key")
        except Exception:
            token = None
        return await get_models(token=token)

