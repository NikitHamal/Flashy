import json
import asyncio
import logging
import random
import time
from typing import AsyncGenerator, Dict, Any, List
from curl_cffi.requests import AsyncSession
from .base import BaseProvider

logger = logging.getLogger("flashy.gradient")

BROWSER_HEADERS = [
    {
        "Accept": "application/x-ndjson",
        "Content-Type": "application/json",
        "Origin": "https://chat.gradient.network",
        "Referer": "https://chat.gradient.network/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    },
    {
        "Accept": "application/x-ndjson",
        "Content-Type": "application/json",
        "Origin": "https://chat.gradient.network",
        "Referer": "https://chat.gradient.network/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0",
    },
    {
        "Accept": "application/x-ndjson",
        "Content-Type": "application/json",
        "Origin": "https://chat.gradient.network",
        "Referer": "https://chat.gradient.network/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0",
    },
]

class GradientProvider(BaseProvider):
    URL = "https://chat.gradient.network/api/generate"
    _request_count = 0
    _last_request_time = 0

    async def generate_stream(
        self, messages: List[Dict[str, str]], model: str, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        if not model or "gpt-oss" in model.lower():
            model = "GPT OSS 120B"
        elif "qwen" in model.lower():
            model = "Qwen3 235B"

        GradientProvider._request_count += 1
        now = time.time()
        time_since_last = now - GradientProvider._last_request_time
        GradientProvider._last_request_time = now

        if time_since_last < 2 and GradientProvider._request_count > 1:
            delay = random.uniform(1, 3)
            logger.info(f"[GRADIENT] Local rate limiting: waiting {delay:.1f}s")
            await asyncio.sleep(delay)

        payload = {
            "clusterMode": "nvidia" if "GPT OSS" in model else "hybrid",
            "model": model,
            "messages": messages,
            "enableThinking": True
        }

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
                            logger.warning(f"[GRADIENT] Rate limit hit (429). Retrying attempt {attempt+2}/{max_retries} in {delay:.1f}s...")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            yield {"error": f"Gradient Error: 429 Rate Limit Exceeded after {max_retries} retries."}
                            return

                    if resp.status_code != 200:
                        yield {"error": f"Gradient Error: {resp.status_code} - {resp.text}"}
                        return

                    async for line_bytes in resp.aiter_lines():
                        if not line_bytes:
                            continue
                        
                        try:
                            data = json.loads(line_bytes)
                            msg_type = data.get("type")

                            if msg_type == "reply":
                                reply_data = data.get("data", {})
                                content = reply_data.get("content")
                                reasoning = reply_data.get("reasoningContent")

                                if reasoning:
                                    yield {"thought": reasoning}
                                if content:
                                    yield {"text": content}
                            
                            elif msg_type == "done":
                                break

                        except json.JSONDecodeError:
                            continue
                    
                    yield {"is_final": True}
                    return

                except Exception as e:
                    logger.exception(f"[GRADIENT] Unhandled exception on attempt {attempt+1}: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)
                        continue
                    yield {"error": f"Gradient Connection error: {str(e)}"}
                    return

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        return [
            {"id": "gpt-oss-120b", "name": "GPT OSS 120B (Gradient)"},
            {"id": "qwen3-235b", "name": "Qwen3 235B (Gradient)"}
        ]
