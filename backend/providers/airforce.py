import json
import asyncio
import logging
import random
import time
from typing import AsyncGenerator, Dict, Any, List, Optional
from curl_cffi.requests import AsyncSession
from .base import BaseProvider, ProviderType

logger = logging.getLogger("flashy.airforce")

BROWSER_HEADERS = [
    {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://api.airforce",
        "referer": "https://api.airforce/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    },
    {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://api.airforce",
        "referer": "https://api.airforce/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0",
    },
    {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://api.airforce",
        "referer": "https://api.airforce/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0",
    },
]

# Verified free models on Airforce (no pay-as-you-go required)
# Format: (model_id, display_name, capabilities)
FREE_MODELS = [
    ("roleplay:free", "Roleplay (Free)", {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": False}),
    ("step-3.5-flash:free", "Step 3.5 Flash (Free)", {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": True}),
    ("gemma3-270m:free", "Gemma 3 270M (Free)", {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": False}),
    ("grok-4.1-mini:free", "Grok 4.1 Mini (Free)", {"chat": True, "stream": True, "vision": False, "reasoning": True, "tools": True}),
    ("nemotron-3-super", "Nemotron 3 Super", {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": True}),
    ("unmoderated-gpt", "Unmoderated GPT", {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": True}),
    ("venice", "Venice", {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": True}),
    ("plutotext-r3-emotional", "PlutoText R3 Emotional", {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": False}),
    ("bard", "Bard", {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": False}),
    ("grok-3", "Grok 3", {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": True}),
    ("glm-4.7-flash", "GLM 4.7 Flash", {"chat": True, "stream": True, "vision": True, "reasoning": False, "tools": True}),
    ("glm-4.5-air", "GLM 4.5 Air", {"chat": True, "stream": True, "vision": True, "reasoning": False, "tools": True}),
    ("glm-5.1", "GLM 5.1", {"chat": True, "stream": True, "vision": True, "reasoning": True, "tools": True}),
    ("gemini-3-flash", "Gemini 3 Flash", {"chat": True, "stream": True, "vision": True, "reasoning": False, "tools": True}),
    ("gemini-3.1-flash-lite", "Gemini 3.1 Flash Lite", {"chat": True, "stream": True, "vision": True, "reasoning": False, "tools": True}),
    ("gemini-2.0-flash", "Gemini 2.0 Flash", {"chat": True, "stream": True, "vision": True, "reasoning": False, "tools": True}),
    ("gemini-2.5-flash", "Gemini 2.5 Flash", {"chat": True, "stream": True, "vision": True, "reasoning": False, "tools": True}),
    ("deepseek-v3-0324", "DeepSeek V3 0324", {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": True}),
    ("deepseek-v3.2", "DeepSeek V3.2", {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": True}),
    ("kimi-k2", "Kimi K2", {"chat": True, "stream": True, "vision": True, "reasoning": False, "tools": True}),
    ("kimi-k2.5", "Kimi K2.5", {"chat": True, "stream": True, "vision": True, "reasoning": True, "tools": True}),
    ("qwen3.5", "Qwen 3.5", {"chat": True, "stream": True, "vision": True, "reasoning": False, "tools": True}),
    ("llama-4-scout", "Llama 4 Scout", {"chat": True, "stream": True, "vision": True, "reasoning": False, "tools": True}),
    ("gpt-4o-mini", "GPT-4o Mini", {"chat": True, "stream": True, "vision": True, "reasoning": False, "tools": True}),
    ("claude-sonnet-4.6", "Claude Sonnet 4.6", {"chat": True, "stream": True, "vision": True, "reasoning": False, "tools": True}),
    ("claude-sonnet-4.5-uncensored", "Claude Sonnet 4.5 Uncensored", {"chat": True, "stream": True, "vision": True, "reasoning": False, "tools": True}),
    ("gpt-oss-20b", "GPT-OSS 20B", {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": True}),
    ("gpt-5.1-chat", "GPT 5.1 Chat", {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": True}),
    ("minimax-m2.5", "MiniMax M2.5", {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": True}),
    ("minimax-m2.7", "MiniMax M2.7", {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": True}),
]

# Models confirmed as pay-as-you-go only (excluded from free list)
PAID_MODELS = {
    "gpt-5.4-mini-p2g", "gemini-3.1-flash-lite-p2g", "claude-opus-4.5-uncensored",
    "claude-opus-4.6-uncensored", "claude-sonnet-4.6-uncensored", "nano-banana-2-search",
    "sonar-deepresearch", "gemini-2.5-pro", "claude-opus-4.5-p2g", "claude-haiku-4.5-p2g",
    "claude-sonnet-4.5-p2g", "claude-sonnet-4.6-p2g", "gpt-5.4-p2g", "gpt-5.4-nano-p2g",
    "gpt-5.3-codex-p2g", "gpt-5.1-codex-mini-p2g", "gemini-3-flash-p2g",
}

# Whitelist-only models (restricted access)
WHITELIST_ONLY = {"gemini-3.1-pro", "gemini-3-pro", "gpt-5.2-chat"}


class AirforceProvider(BaseProvider):
    URL = "https://api.airforce/v1/chat/completions"
    _request_count = 0
    _last_request_time = 0

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OPENAI_COMPATIBLE

    async def generate_stream(
        self, messages: List[Dict[str, str]], model: str, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        if not model:
            model = "nemotron-3-super"

        AirforceProvider._request_count += 1
        now = time.time()
        time_since_last = now - AirforceProvider._last_request_time
        AirforceProvider._last_request_time = now

        if time_since_last < 2 and AirforceProvider._request_count > 1:
            delay = random.uniform(1, 3)
            logger.info(f"[AIRFORCE] Local rate limiting: waiting {delay:.1f}s")
            await asyncio.sleep(delay)

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "stream_options": {"include_usage": True},
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens") or 16384,
            "top_p": kwargs.get("top_p", 1.0),
        }

        tools = kwargs.get("tools")
        if tools:
            payload["tools"] = tools
            tool_choice = kwargs.get("tool_choice")
            if tool_choice and tool_choice not in ("required",):
                payload["tool_choice"] = tool_choice
            else:
                payload["tool_choice"] = "auto"

        proxy_arg = kwargs.get("proxy")
        proxies = []
        if isinstance(proxy_arg, str) and proxy_arg:
            proxies = [p.strip() for p in proxy_arg.split(",") if p.strip()]
        elif isinstance(proxy_arg, list):
            proxies = proxy_arg

        max_retries = 5
        
        for attempt in range(max_retries):
            headers = random.choice(BROWSER_HEADERS).copy()
            # Spoof IP to bypass basic free-tier rate limits
            fake_ip = f"{random.randint(10, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"
            headers["x-forwarded-for"] = fake_ip
            headers["x-real-ip"] = fake_ip
            headers["client-ip"] = fake_ip

            # Rotate proxy if multiple are available
            current_proxy = None
            if proxies:
                current_proxy = proxies[attempt % len(proxies)]

            async with AsyncSession(impersonate="chrome", headers=headers, proxy=current_proxy) as session:
                try:
                    # Small delay between attempts
                    if attempt > 0:
                        await asyncio.sleep(random.uniform(0.5, 1.5))
                    
                    resp = await session.post(self.URL, json=payload, stream=True)
                    
                    if resp.status_code == 429:
                        if attempt < max_retries - 1:
                            delay = random.uniform(1.5, 4.0) * (attempt + 1)
                            logger.warning(f"[AIRFORCE] Rate limit hit (429). Retrying attempt {attempt+2}/{max_retries} in {delay:.1f}s...")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            yield {"error": f"Airforce Error: 429 Rate Limit Exceeded after {max_retries} retries."}
                            return

                    if resp.status_code != 200:
                        error_text = resp.text[:500]
                        if "pay-as-you-go" in error_text.lower() or "pay as you go" in error_text.lower():
                            yield {"error": f"Airforce Error: Model '{model}' requires pay-as-you-go. Use a free model instead."}
                            return
                        if "whitelist" in error_text.lower():
                            yield {"error": f"Airforce Error: Model '{model}' is whitelist-only and not available."}
                            return
                        yield {"error": f"Airforce Error: {resp.status_code} - {error_text}"}
                        return

                    stream_success = True
                    buffer = ""
                    tool_calls_acc: Dict[int, Dict] = {}
                    raw_chunk_count = 0
                    pending_finish: Optional[str] = None
                    pending_usage: Optional[Dict[str, Any]] = None

                    async for chunk_bytes in resp.aiter_content():
                        buffer += chunk_bytes.decode("utf-8", errors="ignore")

                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()

                            if not line:
                                continue

                            if "Ratelimit Exceeded!" in line:
                                if attempt < max_retries - 1:
                                    logger.warning(f"[AIRFORCE] 'Ratelimit Exceeded!' in stream. Retrying attempt {attempt+2}/{max_retries}...")
                                    stream_success = False
                                    break
                                else:
                                    yield {"error": "Airforce Error: Ratelimit Exceeded!"}
                                    return

                            if "Not enough requests remaining" in line:
                                yield {"error": f"Airforce Error: Model '{model}' costs too many requests for free tier. Try a lighter model."}
                                return

                            if "pay-as-you-go" in line.lower() or "pay as you go" in line.lower():
                                yield {"error": f"Airforce Error: Model '{model}' requires pay-as-you-go."}
                                return

                            if "whitelist" in line.lower():
                                yield {"error": f"Airforce Error: Model '{model}' is whitelist-only."}
                                return

                            if line == "data: [DONE]":
                                for idx in sorted(tool_calls_acc.keys()):
                                    tc = tool_calls_acc[idx]
                                    yield {
                                        "tool_call": {
                                            "id": tc.get("id") or f"call_{idx}",
                                            "name": tc.get("function", {}).get("name", ""),
                                            "arguments": tc.get("function", {}).get("arguments", "{}"),
                                        }
                                    }
                                tool_calls_acc = {}
                                # Yield deferred final event with any usage seen after finish
                                if pending_finish:
                                    final_event = {
                                        "is_final": True,
                                        "finish_reason": pending_finish,
                                    }
                                    if pending_usage:
                                        final_event["usage"] = pending_usage
                                        logger.info(
                                            f"[AIRFORCE] usage (at DONE): prompt={pending_usage.get('prompt_tokens', 0)} completion={pending_usage.get('completion_tokens', 0)}"
                                        )
                                    yield final_event
                                    pending_finish = None
                                continue

                            if line.startswith("data: "):
                                chunk_str = line[6:]

                                try:
                                    data = json.loads(chunk_str)
                                    raw_chunk_count += 1
                                    usage_data = data.get("usage")

                                    if usage_data and isinstance(usage_data, dict):
                                        prompt_tokens = usage_data.get("prompt_tokens", 0) or 0
                                        completion_tokens = usage_data.get("completion_tokens", 0) or 0
                                        total_tokens = usage_data.get("total_tokens", 0) or (prompt_tokens + completion_tokens)
                                        logger.info(
                                            f"[AIRFORCE] usage: prompt={prompt_tokens} completion={completion_tokens} total={total_tokens}"
                                        )
                                        usage_dict = {
                                            "prompt_tokens": prompt_tokens,
                                            "completion_tokens": completion_tokens,
                                            "total_tokens": total_tokens,
                                        }
                                        if pending_finish:
                                            pending_usage = usage_dict
                                        else:
                                            yield {"usage": usage_dict}

                                    choices = data.get("choices", [])
                                    if choices:
                                        choice = choices[0]
                                        delta = choice.get("delta", {})
                                        content = delta.get("content")
                                        reasoning = delta.get("reasoning_content") or delta.get("reasoning")
                                        finish_reason = choice.get("finish_reason")
                                        delta_tool_calls = delta.get("tool_calls")

                                        if delta_tool_calls:
                                            for tc_delta in delta_tool_calls:
                                                idx = tc_delta.get("index", 0)
                                                if idx not in tool_calls_acc:
                                                    tool_calls_acc[idx] = {
                                                        "id": "",
                                                        "function": {"name": "", "arguments": ""},
                                                    }
                                                acc = tool_calls_acc[idx]
                                                if tc_delta.get("id"):
                                                    acc["id"] = tc_delta["id"]
                                                fn = tc_delta.get("function", {})
                                                if fn.get("name"):
                                                    acc["function"]["name"] += fn["name"]
                                                if fn.get("arguments"):
                                                    acc["function"]["arguments"] += fn["arguments"]

                                        if reasoning:
                                            yield {"thought": reasoning}

                                        elif content:
                                            yield {"text": content}

                                        if finish_reason:
                                            for tidx in sorted(tool_calls_acc.keys()):
                                                tc = tool_calls_acc[tidx]
                                                yield {
                                                    "tool_call": {
                                                        "id": tc.get("id", f"call_{tidx}"),
                                                        "name": tc.get("function", {}).get("name", ""),
                                                        "arguments": tc.get("function", {}).get("arguments", "{}"),
                                                    }
                                                }
                                            tool_calls_acc = {}

                                            # Defer the final event — AirForce sends usage in a
                                            # separate chunk after finish_reason.
                                            pending_finish = finish_reason
                                            finish_usage = data.get("usage")
                                            if finish_usage and isinstance(finish_usage, dict):
                                                fp = finish_usage.get("prompt_tokens", 0) or 0
                                                fc = finish_usage.get("completion_tokens", 0) or 0
                                                ft = finish_usage.get("total_tokens", 0) or (fp + fc)
                                                pending_usage = {
                                                    "prompt_tokens": fp,
                                                    "completion_tokens": fc,
                                                    "total_tokens": ft,
                                                }

                                except json.JSONDecodeError:
                                    continue
                    
                    if stream_success:
                        if pending_finish:
                            final_event = {
                                "is_final": True,
                                "finish_reason": pending_finish,
                            }
                            if pending_usage:
                                final_event["usage"] = pending_usage
                                logger.info(
                                    f"[AIRFORCE] usage (at stream end): prompt={pending_usage.get('prompt_tokens', 0)} completion={pending_usage.get('completion_tokens', 0)}"
                                )
                            yield final_event
                            pending_finish = None
                        else:
                            yield {"is_final": True}
                        return
                    else:
                        delay = random.uniform(1.0, 3.0)
                        await asyncio.sleep(delay)
                        continue

                except Exception as e:
                    logger.exception(f"[AIRFORCE] Unhandled exception on attempt {attempt+1}: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)
                        continue
                    yield {"error": f"Airforce Connection error: {str(e)}"}
                    return

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        url = "https://api.airforce/v1/models"
        try:
            async with AsyncSession(impersonate="chrome") as session:
                resp = await session.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    models = data if isinstance(data, list) else data.get("data", [])
                    all_ids = {m["id"] for m in models if isinstance(m, dict) and "id" in m}
                    result = []
                    for mid, name, caps in FREE_MODELS:
                        if mid in all_ids or mid.endswith(":free"):
                            result.append({"id": mid, "name": name, "capabilities": caps})
                    return result
        except Exception as e:
            logger.warning(f"[AIRFORCE] Error fetching models dynamically: {e}")

        return [{"id": mid, "name": name, "capabilities": caps} for mid, name, caps in FREE_MODELS]
