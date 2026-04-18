import asyncio
import json
import aiohttp
import time
import random

MODELS_TO_TEST = [
    "glm-4.7",
    "glm-4.7-flash",
    "glm-4.6",
    "deepseek-v3-0324",
    "deepseek-v3.2",
    "qwen3.5",
    "qwen3.6-plus",
    "kimi-k2",
    "kimi-k2-0905",
    "minimax-m2.5",
    "minimax-m2.5-sub",
    "minimax-m2.7",
    "grok-4.1-mini:free",
    "grok-3",
    "grok-3-mini",
    "grok-4.1-fast:free",
    "grok-4.1-fast-non-reasoning",
    "grok-4.1-fast-reasoning",
    "grok-4.1-thinking",
    "step-3.5-flash:free",
    "roleplay:free",
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-3-flash",
    "gemini-3-flash-p2g",
    "gemini-3.1-flash-lite",
    "gemini-3.1-flash-lite-p2g",
    "gemini-3.1-pro",
    "gemini-3-pro",
    "claude-haiku-4.5-p2g",
    "claude-sonnet-4.6",
    "claude-opus-4.7",
    "claude-4-ch-exp",
    "claude-3-7-ch-exp",
    "mistral-small-creative",
    "llama-4-scout",
    "sonar-deepresearch",
    "gemma3-270m:free",
    "gpt-4o-mini",
    "gpt-5.1-chat",
]

HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "origin": "https://api.airforce",
    "referer": "https://api.airforce/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
}

async def test_model(session: aiohttp.ClientSession, model: str) -> dict:
    url = "https://api.airforce/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Reply with exactly one word: 'works'. Nothing else."}],
        "stream": True,
        "temperature": 0.7,
    }

    headers = dict(HEADERS)
    fake_ip = f"{random.randint(10,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"
    headers["x-forwarded-for"] = fake_ip
    headers["x-real-ip"] = fake_ip
    headers["client-ip"] = fake_ip

    start = time.time()
    try:
        async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            text = ""
            async for line in resp.content:
                line = line.decode("utf-8", errors="ignore").strip()
                if not line or line.startswith(":"):
                    continue
                if line.startswith("data: "):
                    chunk_str = line[6:]
                    if chunk_str == "[DONE]":
                        break
                    try:
                        data = json.loads(chunk_str)
                        content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        text += content
                    except json.JSONDecodeError:
                        continue
                if "Ratelimit" in line:
                    return {"model": model, "status": "rate_limited", "time": time.time() - start}

            elapsed = time.time() - start
            if resp.status == 200:
                text = text.strip()
                success = text.lower().startswith("works") or "works" in text.lower()
                return {"model": model, "status": "works" if success else f"bad_response: {text[:80]}", "time": elapsed}
            else:
                body = await resp.text()
                return {"model": model, "status": f"http_{resp.status}: {body[:60]}", "time": elapsed}
    except asyncio.TimeoutError:
        return {"model": model, "status": "timeout", "time": time.time() - start}
    except Exception as e:
        return {"model": model, "status": f"error: {str(e)[:80]}", "time": time.time() - start}

async def main():
    print(f"Testing {len(MODELS_TO_TEST)} models...\n")
    results = []
    async with aiohttp.ClientSession() as session:
        for model in MODELS_TO_TEST:
            r = await test_model(session, model)
            results.append(r)
            status = r["status"]
            t = f"{r['time']:.1f}s"
            tag = "[OK]  " if status == "works" else "[RATE]" if "rate" in status else "[BAD] " if "bad" in status else "[FAIL]" if status.startswith("http") or status == "timeout" or "error" in status else "[??]  "
            print(f"{tag} {model:<40} {status:<35} {t}")
            await asyncio.sleep(0.5)

    print(f"\n{'='*70}")
    working = [r for r in results if r["status"] == "works"]
    print(f"\nWORKING ({len(working)}):")
    for r in working:
        print(f"  - {r['model']}")

if __name__ == "__main__":
    asyncio.run(main())