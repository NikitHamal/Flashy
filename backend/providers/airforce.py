import json
import asyncio
import logging
import random
import time
from typing import AsyncGenerator, Dict, Any, List
from curl_cffi.requests import AsyncSession
from .base import BaseProvider

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

class AirforceProvider(BaseProvider):
    URL = "https://api.airforce/v1/chat/completions"
    _request_count = 0
    _last_request_time = 0
    
    async def generate_stream(
        self, messages: List[Dict[str, str]], model: str, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        if not model:
            model = "gpt-4o"

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
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens"),
            "top_p": kwargs.get("top_p", 1.0),
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
                            logger.warning(f"[AIRFORCE] Rate limit hit (429). Retrying attempt {attempt+2}/{max_retries} in {delay:.1f}s...")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            yield {"error": f"Airforce Error: 429 Rate Limit Exceeded after {max_retries} retries."}
                            return

                    if resp.status_code != 200:
                        yield {"error": f"Airforce Error: {resp.status_code} - {resp.text}"}
                        return

                    stream_success = True
                    async for chunk_bytes in resp.aiter_content():
                        line = chunk_bytes.decode("utf-8", errors="ignore").strip()
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

                        if line.startswith("data: "):
                            chunk_str = line[6:]
                            if chunk_str == "[DONE]":
                                break
                            
                            try:
                                data = json.loads(chunk_str)
                                if "choices" in data and len(data["choices"]) > 0:
                                    content = data["choices"][0].get("delta", {}).get("content", "")
                                    if content:
                                        yield {"text": content}
                            except json.JSONDecodeError:
                                continue
                    
                    if stream_success:
                        yield {"is_final": True}
                        return
                    else:
                        # Continue to next retry attempt if stream was broken by rate limit
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
                    # Expecting data to be a list or dict containing a list
                    models = data if isinstance(data, list) else data.get("data", [])
                    return [
                        {"id": m["id"], "name": m.get("name", m["id"])}
                        for m in models
                    ]
        except Exception as e:
            logger.warning(f"[AIRFORCE] Error fetching models dynamically: {e}")
            
        # Fallback
        return [
            {"id": "gpt-4o", "name": "GPT-4o (Airforce)"},
            {"id": "claude-3-5-sonnet", "name": "Claude 3.5 Sonnet (Airforce)"},
            {"id": "llama-3-70b-instruct", "name": "Llama 3 70B (Airforce)"},
            {"id": "mixtral-8x7b-instruct", "name": "Mixtral 8x7B (Airforce)"},
            {"id": "gemini-pro", "name": "Gemini Pro (Airforce)"}
        ]
