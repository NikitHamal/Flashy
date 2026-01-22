import json
import asyncio
from typing import AsyncGenerator, Dict, Any, List
from curl_cffi.requests import AsyncSession
from .base import BaseProvider

class DeepInfraProvider(BaseProvider):
    URL = "https://api.deepinfra.com/v1/openai/chat/completions"
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        if not model or model == "G_2_5_FLASH":
            model = "meta-llama/Meta-Llama-3-8B-Instruct"
            
        # Using headers from g4f defaults and common browser patterns
        headers = {
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
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": True
        }
        
        proxy = kwargs.get("proxy")
        
        # Use impersonate="chrome" for the latest fingerprint
        async with AsyncSession(impersonate="chrome", headers=headers, proxy=proxy) as session:
            try:
                # Mirroring g4f's unauthenticated approach
                stream_resp = await session.post(self.URL, json=payload, stream=True)
                
                if stream_resp.status_code != 200:
                    error_text = stream_resp.text
                    yield {"error": f"DeepInfra Error: {stream_resp.status_code} - {error_text}"}
                    return
                
                buffer = ""
                async for chunk_bytes in stream_resp.aiter_content():
                    buffer += chunk_bytes.decode('utf-8', errors='ignore')
                    
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        
                        if not line or line == 'data: [DONE]':
                            continue
                            
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])
                                choices = data.get('choices', [])
                                if choices:
                                    delta = choices[0].get('delta', {})
                                    content = delta.get('content')
                                    if content:
                                        yield {"text": content}
                                    
                                    if choices[0].get('finish_reason'):
                                        yield {"is_final": True}
                            except json.JSONDecodeError:
                                pass
            except Exception as e:
                yield {"error": f"DeepInfra Connection error: {str(e)}"}

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        url = 'https://api.deepinfra.com/models/featured'
        try:
            async with AsyncSession(impersonate="chrome") as session:
                resp = await session.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    return [
                        {"id": m["model_name"], "name": m["model_name"].split("/")[-1]}
                        for m in data if m.get("type") == "text-generation"
                    ]
        except Exception:
            pass
        return [
            {"id": "meta-llama/Meta-Llama-3-8B-Instruct", "name": "Llama 3 (8B)"},
            {"id": "meta-llama/Meta-Llama-3-70B-Instruct", "name": "Llama 3 (70B)"},
            {"id": "mistralai/Mistral-7B-Instruct-v0.1", "name": "Mistral 7B"}
        ]
