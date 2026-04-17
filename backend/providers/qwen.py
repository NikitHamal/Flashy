import json
import re
import uuid
import time
import logging
import asyncio
from typing import AsyncGenerator, Dict, Any, List, Optional
from curl_cffi.requests import AsyncSession
from .base import BaseProvider
from .qwen_utils.cookie_generator import generate_cookies
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

TOOL_CALL_RE = re.compile(
    r'<tool_call>\s*(\{.*?\})\s*</tool_call>',
    re.DOTALL
)


def build_tool_system_prompt(tools: List[Dict]) -> str:
    """Convert OpenAI-format tool defs to a plain-text system prompt prefix."""
    lines = [TOOL_SYSTEM_PREFIX]
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
    """Prepend tool descriptions into the system prompt (or insert one)."""
    if not tools:
        return messages

    tool_prefix = build_tool_system_prompt(tools)
    out = list(messages)

    if out and out[0].get("role") == "system":
        out[0] = {**out[0], "content": tool_prefix + "\n\n" + out[0]["content"]}
    else:
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


class QwenProvider(BaseProvider):
    URL = "https://chat.qwen.ai"
    _midtoken: Optional[str] = None
    _midtoken_uses: int = 0

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
        tools = kwargs.get("tools")  # OpenAI-format tool defs or None
        
        # Advanced Features from kwargs
        chat_type = kwargs.get("chat_type", "t2t") # t2t, search, deep_research
        thinking_enabled = kwargs.get("thinking_enabled", True)
        thinking_mode = kwargs.get("thinking_mode", "Auto") # Auto, Thinking, Fast

        logger.info(f"[QWEN] generate_stream | model={model} | chat_type={chat_type} | thinking={thinking_enabled}")

        is_openai_pass_through = kwargs.get("is_openai_pass_through", False)

        # Qwen uses prompt-based tool calling — always inject tool descriptions
        # into the system prompt so the model knows what tools are available,
        # regardless of whether we're in OpenAI pass-through mode or not.
        if tools:
            effective_messages = inject_tools_into_messages(messages, tools)
        else:
            effective_messages = messages

        # Cookie generation and attachment
        cookies_data = generate_cookies()

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

                    # 2. Create Chat
                    chat_payload = {
                        "title": "New Chat",
                        "models": [model],
                        "chat_mode": "normal",
                        "chat_type": chat_type,
                        "timestamp": int(time.time() * 1000)
                    }

                    resp = await session.post(f'{self.URL}/api/v2/chats/new', json=chat_payload)
                    
                    if resp.status_code == 429 or (resp.status_code == 200 and not resp.json().get('success')):
                        if attempt < max_attempts - 1:
                            logger.warning(f"[QWEN] Rate limit/Error on chat creation (attempt {attempt+1}). Retrying...")
                            self._midtoken = None # Invalidate token
                            await asyncio.sleep(1.5 * (attempt + 1))
                            continue
                        else:
                            yield error_to_dict(Error(f"Qwen Rate Limit: {resp.status_code} - {resp.text}"))
                            return

                    data = resp.json()
                    chat_id = data['data']['id']

                    # 3. Build Prompt — handle all OpenAI message types
                    prompt_parts = []
                    for msg in effective_messages:
                        role = msg.get("role", "user")
                        raw_content = msg.get("content")

                        # Flatten list-format content (e.g. [{type:text, text:...}])
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
                            # May have tool_calls instead of (or in addition to) content
                            tool_calls = msg.get("tool_calls")
                            if tool_calls:
                                for tc in tool_calls:
                                    fn = tc.get("function", {})
                                    tc_name = fn.get("name", "unknown")
                                    tc_args = fn.get("arguments", "{}")
                                    prompt_parts.append(
                                        f'<tool_call>{{"name": "{tc_name}", "arguments": {tc_args}}}</tool_call>'
                                    )
                            if content:
                                prompt_parts.append(f"[Assistant]\n{content}")
                        elif role == "tool":
                            # tool_call_id links this to the assistant's tool_call above
                            tool_name = msg.get("name", "") or msg.get("tool_call_id", "tool")
                            prompt_parts.append(f'<tool_result name="{tool_name}">\n{content}\n</tool_result>')

                    full_prompt = "\n\n".join(p for p in prompt_parts if p)
                    msg_id = str(uuid.uuid4())

                    # Feature Config based on UI settings
                    feature_config = {
                        "auto_thinking": "Auto" == thinking_mode,
                        "thinking_mode": thinking_mode,
                        "thinking_enabled": thinking_enabled,
                        "output_schema": "phase",
                        "research_mode": "normal",
                        "auto_search": True if chat_type == "search" else False
                    }
                    
                    if not thinking_enabled:
                         feature_config["thinking_budget"] = 81920

                    msg_payload = {
                        "stream": True,
                        "incremental_output": True,
                        "chat_id": chat_id,
                        "chat_mode": "normal",
                        "model": model,
                        "parent_id": None,
                        "messages": [
                            {
                                "fid": msg_id,
                                "parentId": None,
                                "childrenIds": [],
                                "role": "user",
                                "content": full_prompt,
                                "user_action": "chat",
                                "files": [],
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
