import json
import asyncio
import logging
import random
import socket
import time
from typing import AsyncGenerator, Dict, Any, List, Optional
from curl_cffi.requests import AsyncSession
from curl_cffi import CurlOpt
from .base import BaseProvider, ProviderType

logger = logging.getLogger("flashy.deepinfra")

DEEPINFRA_FALLBACK_MODELS = [
    ("Qwen/Qwen2.5-Coder-32B-Instruct", "Qwen 2.5 Coder 32B", {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": True}),
    ("Qwen/Qwen2.5-72B-Instruct", "Qwen 2.5 72B", {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": True}),
    ("meta-llama/Meta-Llama-3.1-8B-Instruct", "Llama 3.1 (8B)", {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": True}),
    ("meta-llama/Meta-Llama-3.3-70B-Instruct", "Llama 3.3 (70B)", {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": True}),
    ("deepseek-ai/DeepSeek-V3.2", "DeepSeek V3.2", {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": True}),
    ("meta-llama/Llama-3.1-8B-Instruct", "Llama 3.1 (8B)", {"chat": True, "stream": True, "vision": False, "reasoning": False, "tools": True}),
]

CAPTCHA_BROWSER_HEADERS = [
    {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://deepinfra.com",
        "referer": "https://deepinfra.com/",
        "sec-ch-ua": '"Google Chrome";v="136", "Chromium";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    },
    {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://deepinfra.com",
        "referer": "https://deepinfra.com/",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="132", "Microsoft Edge";v="132", "OPR";v="12"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0",
    },
    {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://deepinfra.com",
        "referer": "https://deepinfra.com/",
        "sec-ch-ua": '"Firefox";v="136", "Chromium";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0",
    },
]


def _resolve_host(host: str, port: int = 443) -> str:
    """Resolve hostname using the system DNS resolver (works on Windows).
    
    curl_cffi bundles libcurl with c-ares which can fail to resolve
    some domains on Windows. We pre-resolve using Python's socket
    (which uses the system resolver) and feed the IP to curl via
    the CURLOPT_RESOLVE option.
    """
    try:
        addrs = socket.getaddrinfo(host, port)
        for addr in addrs:
            ip = addr[4][0]
            if ip:
                return ip
    except Exception as exc:
        logger.warning("[DEEPINFRA] DNS pre-resolution failed for %s: %s", host, exc)
    return host


class DeepInfraProvider(BaseProvider):
    URL = "https://api.deepinfra.com/v1/openai/chat/completions"
    _request_count = 0
    _last_request_time = 0
    _resolved_ip: Optional[str] = None

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OPENAI_COMPATIBLE

    async def generate_stream(
        self, messages: List[Dict[str, str]], model: str, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        if not model or model == "G_2_5_FLASH":
            model = "Qwen/Qwen2.5-Coder-32B-Instruct"

        DeepInfraProvider._request_count += 1
        now = time.time()
        time_since_last = now - DeepInfraProvider._last_request_time
        DeepInfraProvider._last_request_time = now

        if time_since_last < 2 and DeepInfraProvider._request_count > 1:
            delay = random.uniform(1, 3)
            logger.info("[DEEPINFRA] rate limiting: waiting %.1fs", delay)
            await asyncio.sleep(delay)

        headers = random.choice(CAPTCHA_BROWSER_HEADERS).copy()

        if self.api_key:
            headers.pop("origin", None)
            headers.pop("referer", None)
            headers["authorization"] = f"Bearer {self.api_key}"

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
            payload["tool_choice"] = kwargs.get("tool_choice", "auto")

        logger.info("[DEEPINFRA] generate_stream | model=%s | messages=%d", model, len(messages))

        # Pre-resolve DNS using system resolver to bypass curl_cffi c-ares issues
        if not DeepInfraProvider._resolved_ip:
            DeepInfraProvider._resolved_ip = _resolve_host("api.deepinfra.com")
        resolved_ip = DeepInfraProvider._resolved_ip

        proxy_arg = kwargs.get("proxy")
        proxies = []
        if isinstance(proxy_arg, str) and proxy_arg:
            proxies = [p.strip() for p in proxy_arg.split(",") if p.strip()]
        elif isinstance(proxy_arg, list):
            proxies = proxy_arg

        max_retries = 5
        for attempt in range(max_retries):
            fake_ip = f"{random.randint(10, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"
            headers["x-forwarded-for"] = fake_ip
            headers["x-real-ip"] = fake_ip
            headers["client-ip"] = fake_ip

            current_proxy = None
            if proxies:
                current_proxy = proxies[attempt % len(proxies)]

            async with AsyncSession(impersonate="chrome", headers=headers, proxy=current_proxy) as session:
                try:
                    # Pre-resolve to bypass curl's internal DNS (c-ares) on Windows
                    resolve_entry = f"api.deepinfra.com:443:{resolved_ip}"
                    session.curl_options[CurlOpt.RESOLVE] = [resolve_entry]

                    stream_resp = await session.post(self.URL, json=payload, stream=True)
                    logger.info("[DEEPINFRA] response status: %d (attempt %d/%d)", stream_resp.status_code, attempt + 1, max_retries)

                    if stream_resp.status_code == 422:
                        error_text = stream_resp.text
                        logger.error("[DEEPINFRA] 422 captcha needed: %s", error_text[:200])
                        if not self.api_key:
                            yield {"error": "DeepInfra requires captcha verification for anonymous access. Try again or set a 'deepinfra_api_key' in config."}
                        else:
                            yield {"error": f"DeepInfra 422: {error_text[:500]}"}
                        return

                    if stream_resp.status_code == 429:
                        if attempt < max_retries - 1:
                            delay = random.uniform(1.5, 4.0) * (attempt + 1)
                            logger.warning("[DEEPINFRA] rate limit 429, retrying in %.1fs...", delay)
                            await asyncio.sleep(delay)
                            continue
                        yield {"error": "DeepInfra rate limited (429) after retries."}
                        return

                    if stream_resp.status_code == 403:
                        if attempt < max_retries - 1:
                            delay = random.uniform(1.5, 4.0) * (attempt + 1)
                            logger.warning("[DEEPINFRA] 403, retrying in %.1fs...", delay)
                            await asyncio.sleep(delay)
                            continue
                        error_text = stream_resp.text
                        yield {"error": f"DeepInfra blocked (403): {error_text[:300]}"}
                        return

                    if stream_resp.status_code != 200:
                        error_text = stream_resp.text
                        logger.error("[DEEPINFRA] Error %d: %s", stream_resp.status_code, error_text[:500])
                        yield {"error": f"DeepInfra Error {stream_resp.status_code}: {error_text[:500]}"}
                        return

                    buffer = ""
                    tool_calls_acc: Dict[int, Dict] = {}
                    raw_chunk_count = 0
                    pending_finish: Optional[str] = None
                    pending_usage: Optional[Dict[str, Any]] = None

                    async for chunk_bytes in stream_resp.aiter_content():
                        buffer += chunk_bytes.decode("utf-8", errors="ignore")

                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()

                            if not line:
                                continue

                            if line == "data: [DONE]":
                                if tool_calls_acc:
                                    for idx in sorted(tool_calls_acc.keys()):
                                        tc = tool_calls_acc[idx]
                                        yield {"tool_call": {"id": tc.get("id") or f"call_{idx}", "name": tc.get("function", {}).get("name", ""), "arguments": tc.get("function", {}).get("arguments", "{}")}}
                                    tool_calls_acc = {}
                                if pending_finish:
                                    final_event = {"is_final": True, "finish_reason": pending_finish}
                                    if pending_usage:
                                        final_event["usage"] = pending_usage
                                    yield final_event
                                    pending_finish = None
                                continue

                            if line.startswith("data: "):
                                raw_chunk_count += 1
                                try:
                                    data = json.loads(line[6:])
                                    choices = data.get("choices", [])
                                    usage_data = data.get("usage")

                                    if usage_data and isinstance(usage_data, dict):
                                        usage_dict = {
                                            "prompt_tokens": usage_data.get("prompt_tokens", 0) or 0,
                                            "completion_tokens": usage_data.get("completion_tokens", 0) or 0,
                                            "total_tokens": usage_data.get("total_tokens", 0) or 0,
                                        }
                                        if pending_finish:
                                            pending_usage = usage_dict
                                        else:
                                            yield {"usage": usage_dict}

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
                                                    tool_calls_acc[idx] = {"id": "", "function": {"name": "", "arguments": ""}}
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
                                            if tool_calls_acc:
                                                for tidx in sorted(tool_calls_acc.keys()):
                                                    tc = tool_calls_acc[tidx]
                                                    yield {"tool_call": {"id": tc.get("id") or f"call_{tidx}", "name": tc.get("function", {}).get("name", ""), "arguments": tc.get("function", {}).get("arguments", "{}")}}
                                                tool_calls_acc = {}
                                            pending_finish = finish_reason
                                            usage = data.get("usage")
                                            if usage and isinstance(usage, dict):
                                                pending_usage = {
                                                    "prompt_tokens": usage.get("prompt_tokens", 0) or 0,
                                                    "completion_tokens": usage.get("completion_tokens", 0) or 0,
                                                    "total_tokens": usage.get("total_tokens", 0) or 0,
                                                }

                                except json.JSONDecodeError:
                                    pass

                    if pending_finish:
                        final_event = {"is_final": True, "finish_reason": pending_finish}
                        if pending_usage:
                            final_event["usage"] = pending_usage
                        yield final_event
                    return

                except Exception as e:
                    logger.exception("[DEEPINFRA] attempt %d/%d failed: %s", attempt + 1, max_retries, e)
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)
                        # Re-resolve DNS on retry in case IP changed
                        DeepInfraProvider._resolved_ip = _resolve_host("api.deepinfra.com")
                        resolved_ip = DeepInfraProvider._resolved_ip
                        continue
                    yield {"error": f"DeepInfra error: {e}"}
                    return

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        url = "https://api.deepinfra.com/models/featured"
        try:
            resolved_ip = _resolve_host("api.deepinfra.com")
            async with AsyncSession(impersonate="chrome") as session:
                resolve_entry = f"api.deepinfra.com:443:{resolved_ip}"
                session.session.set_opt(CurlOpt.RESOLVE, [resolve_entry])
                resp = await session.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    result = []
                    for m in data:
                        if m.get("type") != "text-generation":
                            continue
                        model_id = m.get("model_name", "")
                        pricing = m.get("pricing", {}) or {}
                        ci = float(pricing.get("cents_per_input_token") or 0)
                        co = float(pricing.get("cents_per_output_token") or 0)
                        max_ctx = m.get("max_tokens") or m.get("context_window", 32768)
                        max_output = max_ctx - 1024
                        max_output = min(max_output, 131072)
                        max_output = max(max_output, 8192)
                        lower = model_id.lower()
                        caps = {
                            "chat": True, "stream": True,
                            "vision": any(t in lower for t in ("vl", "vision", "omni", "gemma-4", "gemma4", "qwen3", "glm-4", "glm-5", "kimi-k2")),
                            "reasoning": any(t in lower for t in ("reason", "think", "r1", "o1", "o3", "qwq")),
                            "tools": True,
                        }
                        display = model_id.split("/")[-1] if "/" in model_id else model_id
                        result.append({"id": model_id, "name": display, "capabilities": caps, "context_window": max_ctx, "max_output": max_output, "pricing": {"cents_per_input_token": ci, "cents_per_output_token": co}})
                    return result
        except Exception:
            pass
        return [{"id": mid, "name": name, "capabilities": caps, "context_window": 32768, "max_output": 16384} for mid, name, caps in DEEPINFRA_FALLBACK_MODELS]
