import json
import asyncio
import logging
import random
import time
from typing import AsyncGenerator, Dict, Any, List
from curl_cffi.requests import AsyncSession
from .base import BaseProvider

logger = logging.getLogger("flashy.deepinfra")

BROWSER_HEADERS = [
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
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
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


class DeepInfraProvider(BaseProvider):
    URL = "https://api.deepinfra.com/v1/openai/chat/completions"
    _request_count = 0
    _last_request_time = 0

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
            logger.info(f"[DEEPINFRA] Rate limiting: waiting {delay:.1f}s")
            await asyncio.sleep(delay)

        headers = random.choice(BROWSER_HEADERS).copy()

        logger.info(
            f"[DEEPINFRA] generate_stream | model={model} | messages={len(messages)} | tools={len(kwargs.get('tools') or [])}"
        )

        for i, msg in enumerate(messages):
            role = msg.get("role", "?")
            content = str(msg.get("content") or "")[:150]
            logger.debug(f"[DEEPINFRA]   msg[{i}] role={role} content={content!r}")

        tools = kwargs.get("tools")
        payload = {
            "model": model, 
            "messages": messages, 
            "stream": True,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens"),
            "top_p": kwargs.get("top_p", 1.0),
        }
        # Only include valid OpenAI fields that DeepInfra supports
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
            logger.info(f"[DEEPINFRA] Passing {len(tools)} tools to API")

        proxy_arg = kwargs.get("proxy")
        proxies = []
        if isinstance(proxy_arg, str) and proxy_arg:
            proxies = [p.strip() for p in proxy_arg.split(",") if p.strip()]
        elif isinstance(proxy_arg, list):
            proxies = proxy_arg

        max_retries = 5
        for attempt in range(max_retries):
            # Try to spoof IP to bypass basic free-tier rate limits
            fake_ip = f"{random.randint(10, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"
            headers["x-forwarded-for"] = fake_ip
            headers["x-real-ip"] = fake_ip
            headers["client-ip"] = fake_ip
            
            # Rotate proxy if multiple are available
            current_proxy = None
            if proxies:
                current_proxy = proxies[attempt % len(proxies)]

            async with AsyncSession(
                impersonate="chrome", headers=headers, proxy=current_proxy
            ) as session:
                try:
                    stream_resp = await session.post(self.URL, json=payload, stream=True)
                    logger.info(
                        f"[DEEPINFRA] Stream response status: {stream_resp.status_code} (Attempt {attempt+1})"
                    )
                    
                    if stream_resp.status_code == 429:
                        if attempt < max_retries - 1:
                            delay = random.uniform(1.5, 4.0) * (attempt + 1)
                            logger.warning(f"[DEEPINFRA] Rate limit hit (429). Retrying with new IP in {delay:.1f}s...")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            yield {"error": f"DeepInfra Error: 429 Rate Limit Exceeded after {max_retries} retries. Please try again later or configure a proxy."}
                            return

                    if stream_resp.status_code != 200:
                        error_text = stream_resp.text
                        logger.error(
                            f"[DEEPINFRA] Error: {stream_resp.status_code} - {error_text[:500]}"
                        )
                        yield {
                            "error": f"DeepInfra Error: {stream_resp.status_code} - {error_text}"
                        }
                        return

                    buffer = ""
                    tool_calls_acc: Dict[int, Dict] = {}
                    raw_chunk_count = 0

                    async for chunk_bytes in stream_resp.aiter_content():
                        buffer += chunk_bytes.decode("utf-8", errors="ignore")

                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()

                            if not line:
                                continue

                            if line == "data: [DONE]":
                                logger.info(
                                    f"[DEEPINFRA] [DONE] received after {raw_chunk_count} chunks"
                                )
                                # Flush any accumulated tool calls
                                if tool_calls_acc:
                                    for idx in sorted(tool_calls_acc.keys()):
                                        tc = tool_calls_acc[idx]
                                        logger.info(
                                            f"[DEEPINFRA] Flushing tool_call at [DONE]: {tc.get('function', {}).get('name')}"
                                        )
                                        yield {
                                            "tool_call": {
                                                "id": tc.get("id", f"call_{idx}"),
                                                "name": tc.get("function", {}).get(
                                                    "name", ""
                                                ),
                                                "arguments": tc.get("function", {}).get(
                                                    "arguments", "{}"
                                                ),
                                            }
                                        }
                                    tool_calls_acc = {}
                                continue

                            if line.startswith("data: "):
                                try:
                                    data = json.loads(line[6:])
                                    raw_chunk_count += 1
                                    choices = data.get("choices", [])
                                    if choices:
                                        choice = choices[0]
                                        delta = choice.get("delta", {})
                                        content = delta.get("content")
                                        finish_reason = choice.get("finish_reason")
                                        delta_tool_calls = delta.get("tool_calls")

                                        logger.debug(
                                            f"[DEEPINFRA] chunk#{raw_chunk_count} finish={finish_reason} content={str(content)[:80]!r} tool_calls={bool(delta_tool_calls)}"
                                        )

                                        # Handle streaming tool_calls deltas
                                        if delta_tool_calls:
                                            for tc_delta in delta_tool_calls:
                                                idx = tc_delta.get("index", 0)
                                                if idx not in tool_calls_acc:
                                                    tool_calls_acc[idx] = {
                                                        "id": "",
                                                        "function": {
                                                            "name": "",
                                                            "arguments": "",
                                                        },
                                                    }
                                                acc = tool_calls_acc[idx]
                                                if tc_delta.get("id"):
                                                    acc["id"] = tc_delta["id"]
                                                fn = tc_delta.get("function", {})
                                                if fn.get("name"):
                                                    acc["function"]["name"] += fn["name"]
                                                if fn.get("arguments"):
                                                    acc["function"]["arguments"] += fn[
                                                        "arguments"
                                                    ]

                                        if content:
                                            yield {"text": content}

                                        if finish_reason:
                                            logger.info(
                                                f"[DEEPINFRA] finish_reason={finish_reason!r}"
                                            )
                                            # Flush accumulated tool calls before finish
                                            if tool_calls_acc:
                                                for tidx in sorted(tool_calls_acc.keys()):
                                                    tc = tool_calls_acc[tidx]
                                                    logger.info(
                                                        f"[DEEPINFRA] Yielding tool_call: {tc.get('function', {}).get('name')}"
                                                    )
                                                    yield {
                                                        "tool_call": {
                                                            "id": tc.get(
                                                                "id", f"call_{tidx}"
                                                            ),
                                                            "name": tc.get(
                                                                "function", {}
                                                            ).get("name", ""),
                                                            "arguments": tc.get(
                                                                "function", {}
                                                            ).get("arguments", "{}"),
                                                        }
                                                    }
                                                tool_calls_acc = {}
                                            yield {
                                                "is_final": True,
                                                "finish_reason": finish_reason,
                                            }

                                except json.JSONDecodeError as e:
                                    logger.warning(
                                        f"[DEEPINFRA] JSONDecodeError: {e} | line={line[:200]}"
                                    )
                    
                    # If we reached here, the stream finished successfully
                    return

                except Exception as e:
                    logger.exception(f"[DEEPINFRA] Unhandled exception: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)
                        continue
                    yield {"error": f"DeepInfra Connection error: {str(e)}"}
                    return

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        url = "https://api.deepinfra.com/models/featured"
        try:
            async with AsyncSession(impersonate="chrome") as session:
                resp = await session.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    return [
                        {"id": m["model_name"], "name": m["model_name"].split("/")[-1]}
                        for m in data
                        if m.get("type") == "text-generation"
                    ]
        except Exception:
            pass
        return [
            {"id": "Qwen/Qwen2.5-Coder-32B-Instruct", "name": "Qwen 2.5 Coder 32B"},
            {"id": "Qwen/Qwen2.5-72B-Instruct", "name": "Qwen 2.5 72B"},
            {"id": "meta-llama/Meta-Llama-3.3-70B-Instruct", "name": "Llama 3.3 (70B)"},
            {"id": "meta-llama/Meta-Llama-3.1-8B-Instruct", "name": "Llama 3.1 (8B)"},
            {"id": "mistralai/Mistral-7B-Instruct-v0.3", "name": "Mistral 7B v0.3"},
        ]
