import json
import re
import uuid
import time
import asyncio
from typing import AsyncGenerator, Dict, Any, List, Optional
from curl_cffi.requests import AsyncSession
from .base import BaseProvider
from .qwen_utils.cookie_generator import generate_cookies

class QwenProvider(BaseProvider):
    URL = "https://chat.qwen.ai"
    _midtoken: Optional[str] = None
    _midtoken_uses: int = 0
    
    async def get_midtoken(self, session: AsyncSession, proxy: str = None):
        if self._midtoken and self._midtoken_uses < 50:
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
                    return self._midtoken
        except Exception as e:
            print(f"Error fetching midtoken: {e}")
        return None

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        
        if not model or model == "G_2_5_FLASH":
            model = "qwen3-235b-a22b"
            
        proxy = kwargs.get("proxy")
        
        # Cookie generation
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
        
        async with AsyncSession(impersonate="chrome", headers=headers, proxy=proxy) as session:
            try:
                # 0. Initial Auth Call
                await session.get(f'{self.URL}/api/v1/auths/')
                
                # 1. Get midtoken
                midtoken = await self.get_midtoken(session, proxy)
                if midtoken:
                    session.headers['bx-umidtoken'] = midtoken
                    session.headers['bx-v'] = '2.5.31'
                
                # 2. Create Chat
                chat_payload = {
                    "title": "New Chat",
                    "models": [model],
                    "chat_mode": "normal",
                    "chat_type": "t2t",
                    "timestamp": int(time.time() * 1000)
                }
                
                resp = await session.post(f'{self.URL}/api/v2/chats/new', json=chat_payload)
                if resp.status_code != 200:
                    yield {"error": f"Qwen Create Chat Error: {resp.status_code} - {resp.text}"}
                    return
                    
                data = resp.json()
                if not data.get('success') or not data['data'].get('id'):
                    yield {"error": f"Qwen Create Chat Failed: {data}"}
                    return
                    
                chat_id = data['data']['id']
                
                # 3. Send Message
                prompt = messages[-1]['content'] if messages else ""
                msg_id = str(uuid.uuid4())
                
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
                            "content": prompt,
                            "user_action": "chat",
                            "files": [],
                            "models": [model],
                            "chat_type": "t2t",
                            "feature_config": {
                                "thinking_enabled": True,
                                "output_schema": "phase",
                                "thinking_budget": 81920
                            },
                            "sub_chat_type": "t2t"
                        }
                    ]
                }
                
                url = f'{self.URL}/api/v2/chat/completions?chat_id={chat_id}'
                
                # Streaming with curl_cffi
                stream_resp = await session.post(url, json=msg_payload, stream=True)
                
                if stream_resp.status_code != 200:
                    yield {"error": f"Qwen Send Message Error: {stream_resp.status_code} - {stream_resp.text}"}
                    return
                
                thinking_started = False
                buffer = ""
                
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
                                choices = chunk_data.get("choices", [])
                                if not choices: continue
                                
                                delta = choices[0].get("delta", {})
                                phase = delta.get("phase")
                                content = delta.get("content")
                                
                                if phase == "think":
                                    thinking_started = True
                                    if content:
                                        yield {"thought": content}
                                elif phase == "answer":
                                    thinking_started = False
                                    if content:
                                        yield {"text": content}
                                
                                if choices[0].get("finish_reason"):
                                    yield {"is_final": True}
                                    
                            except json.JSONDecodeError:
                                pass
                                
            except Exception as e:
                yield {"error": f"Qwen Error: {str(e)}"}

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        models_url = "https://chat.qwen.ai/api/models"
        try:
            async with AsyncSession(impersonate="chrome") as session:
                resp = await session.get(models_url)
                if resp.status_code == 200:
                    data = resp.json()
                    models_list = data.get("data", [])
                    return [
                        {"id": m.get("id"), "name": m.get("id")}
                        for m in models_list
                    ]
        except Exception:
            pass
            
        return [
            {"id": "qwen3-235b-a22b", "name": "Qwen 3 (235B)"},
            {"id": "qwen3-max-preview", "name": "Qwen 3 Max Preview"},
            {"id": "qwen-max-latest", "name": "Qwen Max Latest"}
        ]
