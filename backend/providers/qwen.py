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

        if not model or model == "G_2_5_FLASH":
            model = "qwen3.6-plus"

        proxy = kwargs.get("proxy")
        tools = kwargs.get("tools")
        file_paths = kwargs.get("files") or []
        conversation: Optional[QwenConversation] = kwargs.get("conversation")
        chat_type = kwargs.get("chat_type", "t2t")
        thinking_enabled = kwargs.get("thinking_enabled", True)
        thinking_mode = kwargs.get("thinking_mode", "Auto")

        logger.info(
            f"[QWEN] generate_stream | model={model} | chat_type={chat_type} | "
            f"thinking={thinking_enabled} | files={len(file_paths)} | "
            f"conv={'resume' if conversation else 'new'}"
        )

        is_openai_pass_through = kwargs.get("is_openai_pass_through", False)
        logger.info(
            f"[QWEN] generate_stream | model={model} | pass_through={is_openai_pass_through} | "
            f"tools={len(tools) if tools else 0} | chat_type={chat_type}"
        )

        safe_cookies = await prepare_cookies()
        bx_ua = generate_bx_ua(safe_cookies) if safe_cookies else ""
        headers = build_session_headers(bx_ua)

        max_attempts = 3
        for attempt in range(max_attempts):
            async with AsyncSession(
                impersonate="chrome",
                headers=headers,
                cookies=safe_cookies if safe_cookies else None,
                proxy=proxy
            ) as session:
                try:
                    auth_resp = await session.get(f'{self.URL}/api/v1/auths/')

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

                        if resp.status_code == 429 or (resp.status_code == 200 and not resp.json().get('success')):
                            if attempt < max_attempts - 1:
                                logger.warning(f"[QWEN] Rate limit/Error on chat creation (attempt {attempt+1}). Retrying...")
                                get_midtoken._cached = None
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

                    tool_system_prompt, source_messages = resolve_messages(messages, tools, conversation)
                    full_prompt = build_prompt(tool_system_prompt, source_messages)
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
                    )

                    url = f'{self.URL}/api/v2/chat/completions?chat_id={chat_id}'
                    stream_resp = await session.post(url, json=msg_payload, stream=True)

                    if stream_resp.status_code != 200:
                        if stream_resp.status_code == 429 and attempt < max_attempts - 1:
                            await asyncio.sleep(1.5 * (attempt + 1))
                            continue
                        yield error_to_dict(Error(f"Qwen Stream Error: {stream_resp.status_code}"))
                        return

                    state = StreamState()

                    async for chunk_bytes in stream_resp.aiter_content():
                        events = parse_stream_chunks(chunk_bytes, state, conversation, has_tools=bool(tools))
                        for ev in events:
                            if ev.get("is_final") and not state.has_any_content and attempt < max_attempts - 1:
                                logger.warning(f"[QWEN] Empty stream with finish_reason={ev.get('finish_reason')}, retrying...")
                                continue
                            yield ev
                            if ev.get("is_final"):
                                return

                    logger.info(f"[QWEN] stream ended (text_len={len(state.full_answer_text)}, yielded={state.has_yielded_content})")

                    if not state.has_any_content and attempt < max_attempts - 1:
                        logger.warning(f"[QWEN] Empty stream response (attempt {attempt+1}). Retrying with fresh conversation...")
                        conversation = None
                        get_midtoken._cached = None
                        await asyncio.sleep(1.5 * (attempt + 1))
                        continue

                    for ev in finalize_stream(state, has_tools=bool(tools), conversation=conversation):
                        yield ev
                    return

                except Exception as e:
                    logger.exception(f"[QWEN] Unhandled exception on attempt {attempt+1}: {e}")
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(1)
                        continue
                    yield error_to_dict(Error(f"Qwen Connection error: {str(e)}"))
                    return

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        return await get_models()