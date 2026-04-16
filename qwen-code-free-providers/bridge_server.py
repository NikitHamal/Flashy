#!/usr/bin/env python3
"""
Qwen Code Free Providers Bridge Server
A lightweight HTTP server that exposes free AI providers for qwen-code.
Based on the flashy agent's free provider implementations.
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, List, Optional
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Add the current directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

app = FastAPI(title="Qwen Code Free Providers Bridge")

# Enable CORS for qwen-code to communicate with this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== Models ==============

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: str = Field(default="qwen3.5-plus")
    stream: bool = Field(default=True)
    temperature: Optional[float] = Field(default=None)
    max_tokens: Optional[int] = Field(default=None)

class ModelInfo(BaseModel):
    id: str
    name: str
    description: str = ""
    context_window: int = 8192

# ============== Provider Implementations ==============

class FreeQwenProvider:
    """Free Qwen provider using cookie-based authentication."""
    
    URL = "https://chat.qwen.ai"
    _midtoken: Optional[str] = None
    _midtoken_uses: int = 0
    _instance: Optional['FreeQwenProvider'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._import_deps()
    
    def _import_deps(self):
        """Import dependencies from local qwen_utils."""
        try:
            from qwen_utils.cookie_generator import generate_cookies
            from qwen_utils.fingerprint import generate_fingerprint
            from curl_cffi.requests import AsyncSession
            self.generate_cookies = generate_cookies
            self.generate_fingerprint = generate_fingerprint
            self.AsyncSession = AsyncSession
        except ImportError as e:
            print(f"Warning: Could not import qwen_utils dependencies: {e}")
            # Fallback implementations
            self.generate_cookies = self._fallback_generate_cookies
            self.generate_fingerprint = None
            self.AsyncSession = None
    
    def _fallback_generate_cookies(self) -> Dict[str, Any]:
        """Fallback cookie generation if flashy deps not available."""
        import time
        import random
        
        timestamp = int(time.time() * 1000)
        device_id = ''.join(random.choices('0123456789abcdef', k=20))
        
        # Generate simple ssxmod cookies
        return {
            "ssxmod_itna": f"1-{device_id}{timestamp}",
            "ssxmod_itna2": f"1-{timestamp}",
            "timestamp": timestamp,
        }
    
    async def get_midtoken(self, session, proxy: str = None) -> Optional[str]:
        if self._midtoken and self._midtoken_uses < 50:
            self._midtoken_uses += 1
            return self._midtoken
        
        try:
            import re
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
        
        if not model:
            model = "qwen3.5-plus"
        
        proxy = kwargs.get("proxy")
        
        # Generate cookies
        cookies_data = self.generate_cookies()
        
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
        
        # Ensure all cookie values are strings
        safe_cookies = {k: str(v) if not isinstance(v, str) else v 
                        for k, v in cookies_data.items()}
        
        if self.AsyncSession is None:
            yield {"error": "Curl-cffi not available for free Qwen provider"}
            return
        
        async with self.AsyncSession(
            impersonate="chrome",
            headers=headers,
            cookies=safe_cookies if safe_cookies else None,
            proxy=proxy
        ) as session:
            try:
                import uuid
                import time
                
                # Initial Auth Call
                await session.get(f'{self.URL}/api/v1/auths/')
                
                # Get midtoken
                midtoken = await self.get_midtoken(session, proxy)
                if midtoken:
                    session.headers['bx-umidtoken'] = midtoken
                    session.headers['bx-v'] = '2.5.31'
                
                # Create Chat
                chat_payload = {
                    "title": "New Chat",
                    "models": [model],
                    "chat_mode": "normal",
                    "chat_type": "t2t",
                    "timestamp": int(time.time() * 1000)
                }
                
                resp = await session.post(f'{self.URL}/api/v2/chats/new', json=chat_payload)
                if resp.status_code != 200:
                    yield {"error": f"Qwen Create Chat Error: {resp.status_code}"}
                    return
                
                data = resp.json()
                if not data.get('success') or not data['data'].get('id'):
                    yield {"error": "Qwen Create Chat Failed"}
                    return
                
                chat_id = data['data']['id']
                
                # Send Message
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
                
                # Streaming
                stream_resp = await session.post(url, json=msg_payload, stream=True)
                
                if stream_resp.status_code != 200:
                    yield {"error": f"Qwen Send Message Error: {stream_resp.status_code}"}
                    return
                
                async for chunk_bytes in stream_resp.aiter_content():
                    text = chunk_bytes.decode('utf-8', errors='ignore')
                    for line in text.split('\n'):
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
                                if not choices:
                                    continue
                                delta = choices[0].get("delta", {})
                                phase = delta.get("phase")
                                content = delta.get("content")
                                
                                if phase == "think" and content:
                                    yield {"thought": content}
                                elif phase == "answer" and content:
                                    yield {"text": content}
                                
                                if choices[0].get("finish_reason"):
                                    yield {"is_final": True}
                            except json.JSONDecodeError:
                                pass
                                
            except Exception as e:
                yield {"error": f"Qwen Error: {str(e)}"}


class FreeDeepInfraProvider:
    """Free DeepInfra provider using unauthenticated access."""
    
    URL = "https://api.deepinfra.com/v1/openai/chat/completions"
    _instance: Optional['FreeDeepInfraProvider'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        try:
            from curl_cffi.requests import AsyncSession
            self.AsyncSession = AsyncSession
        except ImportError:
            self.AsyncSession = None
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        if not model:
            model = "meta-llama/Meta-Llama-3-8B-Instruct"
        
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
        
        if self.AsyncSession is None:
            yield {"error": "Curl-cffi not available for DeepInfra provider"}
            return
        
        async with self.AsyncSession(impersonate="chrome", headers=headers, proxy=proxy) as session:
            try:
                stream_resp = await session.post(self.URL, json=payload, stream=True)
                
                if stream_resp.status_code != 200:
                    error_text = await stream_resp.aread()
                    yield {"error": f"DeepInfra Error: {stream_resp.status_code} - {error_text}"}
                    return
                
                async for chunk_bytes in stream_resp.aiter_content():
                    buffer = chunk_bytes.decode('utf-8', errors='ignore')
                    for line in buffer.split('\n'):
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


# ============== API Endpoints ==============

qwen_provider = FreeQwenProvider()
deepinfra_provider = FreeDeepInfraProvider()

QWEN_MODELS = [
    {"id": "qwen3.6-plus", "name": "Qwen3.6-Plus (Free)", "description": "Latest Qwen 3.6 model - FREE", "context_window": 32000},
    {"id": "qwen3.5-plus", "name": "Qwen3.5-Plus (Free)", "description": "Qwen 3.5 with thinking - FREE", "context_window": 32000},
    {"id": "qwen3.5-flash", "name": "Qwen3.5-Flash (Free)", "description": "Fast Qwen 3.5 model - FREE", "context_window": 32000},
    {"id": "qwen3-coder-plus", "name": "Qwen3-Coder-Plus (Free)", "description": "Coding optimized - FREE", "context_window": 32000},
]

DEEPINFRA_MODELS = [
    {"id": "meta-llama/Meta-Llama-3-8B-Instruct", "name": "Llama 3 8B (Free)", "description": "Meta Llama 3 8B - FREE", "context_window": 8192},
    {"id": "meta-llama/Meta-Llama-3-70B-Instruct", "name": "Llama 3 70B (Free)", "description": "Meta Llama 3 70B - FREE", "context_window": 8192},
    {"id": "mistralai/Mistral-7B-Instruct-v0.3", "name": "Mistral 7B (Free)", "description": "Mistral 7B - FREE", "context_window": 8192},
    {"id": "Qwen/Qwen2.5-72B-Instruct", "name": "Qwen2.5-72B (Free)", "description": "Qwen 2.5 72B on DeepInfra - FREE", "context_window": 32000},
    {"id": "Qwen/Qwen2.5-Coder-32B-Instruct", "name": "Qwen2.5-Coder-32B (Free)", "description": "Qwen 2.5 Coder - FREE", "context_window": 32000},
]


@app.get("/health")
async def health_check():
    return {"status": "ok", "providers": ["free-qwen", "free-deepinfra"]}


@app.get("/v1/models")
async def list_models():
    """List all available free models."""
    all_models = []
    for m in QWEN_MODELS:
        all_models.append({**m, "provider": "free-qwen"})
    for m in DEEPINFRA_MODELS:
        all_models.append({**m, "provider": "free-deepinfra"})
    return {"object": "list", "data": all_models}


@app.get("/v1/models/{provider}")
async def list_provider_models(provider: str):
    """List models for a specific provider."""
    if provider == "free-qwen":
        return {"object": "list", "data": QWEN_MODELS}
    elif provider == "free-deepinfra":
        return {"object": "list", "data": DEEPINFRA_MODELS}
    else:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """Chat completions endpoint compatible with OpenAI API."""
    
    # Determine which provider to use based on model
    model = request.model
    provider = None
    
    # Check if model belongs to a specific provider
    if any(m["id"] == model for m in QWEN_MODELS):
        provider = qwen_provider
    elif any(m["id"] == model for m in DEEPINFRA_MODELS):
        provider = deepinfra_provider
    
    # Default to qwen if not found
    if provider is None:
        provider = qwen_provider
    
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    
    if request.stream:
        async def generate():
            full_content = ""
            async for chunk in provider.generate_stream(messages, model):
                if "error" in chunk:
                    yield f"data: {json.dumps({'error': chunk['error']})}\n\n"
                    break
                if "text" in chunk:
                    full_content += chunk["text"]
                    data = {
                        "id": "chatcmpl-free",
                        "object": "chat.completion.chunk",
                        "created": int(asyncio.get_event_loop().time()),
                        "model": model,
                        "choices": [{"index": 0, "delta": {"content": chunk["text"]}}]
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                if "is_final" in chunk:
                    yield "data: [DONE]\n\n"
            
        return StreamingResponse(generate(), media_type="text/plain")
    else:
        # Non-streaming response
        full_content = ""
        async for chunk in provider.generate_stream(messages, model):
            if "error" in chunk:
                raise HTTPException(status_code=500, detail=chunk["error"])
            if "text" in chunk:
                full_content += chunk["text"]
        
        return {
            "id": "chatcmpl-free",
            "object": "chat.completion",
            "created": int(asyncio.get_event_loop().time()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": full_content},
                "finish_reason": "stop"
            }]
        }


@app.post("/v1/providers/{provider}/chat/completions")
async def provider_chat_completions(provider: str, request: ChatRequest):
    """Provider-specific chat completions."""
    if provider == "free-qwen":
        prov = qwen_provider
    elif provider == "free-deepinfra":
        prov = deepinfra_provider
    else:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")
    
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    
    if request.stream:
        async def generate():
            async for chunk in prov.generate_stream(messages, request.model):
                if "error" in chunk:
                    yield f"data: {json.dumps({'error': chunk['error']})}\n\n"
                    break
                if "text" in chunk:
                    data = {
                        "id": "chatcmpl-free",
                        "object": "chat.completion.chunk",
                        "created": int(asyncio.get_event_loop().time()),
                        "model": request.model,
                        "choices": [{"index": 0, "delta": {"content": chunk["text"]}}]
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                if "thought" in chunk:
                    # Include thinking content as a special format
                    data = {
                        "id": "chatcmpl-free",
                        "object": "chat.completion.chunk",
                        "created": int(asyncio.get_event_loop().time()),
                        "model": request.model,
                        "choices": [{"index": 0, "delta": {"content": f"<thinking>{chunk['thought']}</thinking>"}}]
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                if "is_final" in chunk:
                    yield "data: [DONE]\n\n"
        
        return StreamingResponse(generate(), media_type="text/plain")
    else:
        full_content = ""
        thinking_content = ""
        async for chunk in prov.generate_stream(messages, request.model):
            if "error" in chunk:
                raise HTTPException(status_code=500, detail=chunk["error"])
            if "text" in chunk:
                full_content += chunk["text"]
            if "thought" in chunk:
                thinking_content += chunk["thought"]
        
        final_content = full_content
        if thinking_content:
            final_content = f"<thinking>{thinking_content}</thinking>\n\n{full_content}"
        
        return {
            "id": "chatcmpl-free",
            "object": "chat.completion",
            "created": int(asyncio.get_event_loop().time()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": final_content},
                "finish_reason": "stop"
            }]
        }


def main():
    """Run the bridge server."""
    port = int(os.environ.get("QWEN_BRIDGE_PORT", "8787"))
    host = os.environ.get("QWEN_BRIDGE_HOST", "127.0.0.1")
    
    print(f"""
╔════════════════════════════════════════════════════════════╗
║     Qwen Code Free Providers Bridge Server                 ║
║                                                            ║
║  Providing FREE access to:                                 ║
║  • Qwen models (3.6-plus, 3.5-plus, 3.5-flash, etc.)      ║
║  • DeepInfra models (Llama 3, Mistral, Qwen, etc.)        ║
║                                                            ║
║  Server: http://{host}:{port}                            ║
║  Health: http://{host}:{port}/health                       ║
║                                                            ║
║  No API keys required!                                     ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
