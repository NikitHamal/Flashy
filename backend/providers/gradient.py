import json
import asyncio
from typing import AsyncGenerator, Dict, Any, List
from curl_cffi.requests import AsyncSession
from .base import BaseProvider

class GradientProvider(BaseProvider):
    URL = "https://chat.gradient.network/api/generate"
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        if not model or model == "G_2_5_FLASH":
            model = "GPT OSS 120B"
            
        headers = {
            "Accept": "application/x-ndjson",
            "Content-Type": "application/json",
            "Origin": "https://chat.gradient.network",
            "Referer": "https://chat.gradient.network/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Google Chrome";v="136", "Chromium";v="136", "Not.A/Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }
        
        payload = {
            "clusterMode": "nvidia" if "GPT OSS" in model else "hybrid",
            "model": model,
            "messages": messages,
            "enableThinking": True
        }
        
        proxy = kwargs.get("proxy")
        
        async with AsyncSession(impersonate="chrome", headers=headers, proxy=proxy) as session:
            try:
                stream_resp = await session.post(self.URL, json=payload, stream=True)
                
                if stream_resp.status_code != 200:
                    yield {"error": f"Gradient Error: {stream_resp.status_code} - {stream_resp.text}"}
                    return
                
                buffer = ""
                async for chunk_bytes in stream_resp.aiter_content():
                    buffer += chunk_bytes.decode('utf-8', errors='ignore')
                    
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        
                        if not line:
                            continue
                            
                        try:
                            data = json.loads(line)
                            msg_type = data.get("type")
                            
                            if msg_type == "reply":
                                reply_data = data.get("data", {})
                                reasoning = reply_data.get("reasoningContent")
                                content = reply_data.get("content")
                                
                                if reasoning:
                                    yield {"thought": reasoning}
                                if content:
                                    yield {"text": content}
                            
                            elif msg_type == "finish":
                                yield {"is_final": True}
                                
                        except json.JSONDecodeError:
                            pass
            except Exception as e:
                yield {"error": f"Gradient Connection error: {str(e)}"}

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        # Static list based on g4f and common availability
        return [
            {"id": "GPT OSS 120B", "name": "GPT OSS 120B"},
            {"id": "Qwen3 235B", "name": "Qwen3 235B"}
        ]
