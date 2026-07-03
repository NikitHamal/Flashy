import json
import logging
import asyncio
import re
from typing import AsyncGenerator, Dict, Any, List

import httpx

from .base import BaseProvider
from ..model_registry import resolve_context_window

logger = logging.getLogger("flashy.g4f")

G4F_API_BASE = "https://g4f.space/v1"
REQUEST_TIMEOUT = 180
RATE_LIMIT_SLEEP = 61
DEFAULT_MODEL = "openai"

MODELS = [
    # === nectar by pollinations.ai (srv_mkoloq41e34074b6133e) ===
    {"id": "openai", "name": "GPT-5.4 Nano (Fast)", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "openai-fast", "name": "GPT Fast", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "openai-large", "name": "OpenAI Large", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "deepseek", "name": "DeepSeek", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": True},
    {"id": "deepseek-v4", "name": "DeepSeek V4", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": True},
    {"id": "deepseek-lite", "name": "DeepSeek Lite", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "deepseek-flash", "name": "DeepSeek Flash", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "gpt-5.4", "name": "GPT-5.4", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "gpt-5.4-nano", "name": "GPT-5.4 Nano", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "gpt-5.4-reasoning", "name": "GPT-5.4 Reasoning", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": True},
    {"id": "gpt-5.2", "name": "GPT-5.2", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "gpt-5.2-reasoning", "name": "GPT-5.2 Reasoning", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": True},
    {"id": "gpt-5.5", "name": "GPT-5.5", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "grok", "name": "Grok", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "grok-4", "name": "Grok 4", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "grok-4-fast", "name": "Grok 4 Fast", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "grok-fast", "name": "Grok Fast", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "grok-non-reasoning", "name": "Grok (No Reasoning)", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "claude", "name": "Claude", "server": "mkoloq41e34074b6133e", "vision": True, "reasoning": True},
    {"id": "claude-fast", "name": "Claude Fast", "server": "mkoloq41e34074b6133e", "vision": True, "reasoning": False},
    {"id": "kimi", "name": "Kimi", "server": "mkoloq41e34074b6133e", "vision": True, "reasoning": True},
    {"id": "kimi-k2.5", "name": "Kimi K2.5", "server": "mkoloq41e34074b6133e", "vision": True, "reasoning": True},
    {"id": "kimi-thinking", "name": "Kimi Thinking", "server": "mkoloq41e34074b6133e", "vision": True, "reasoning": True},
    {"id": "mistral", "name": "Mistral", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "mistral-small", "name": "Mistral Small", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "mistral-small-3.1", "name": "Mistral Small 3.1", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "qwen3-coder", "name": "Qwen 3 Coder", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": True},
    {"id": "qwen-coder", "name": "Qwen Coder", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": True},
    {"id": "llama-scout", "name": "Llama Scout", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "glm-5", "name": "GLM 5", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": True},
    {"id": "glm-5.1", "name": "GLM 5.1", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": True},
    {"id": "glm-5p1", "name": "GLM 5.1 (Short)", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": True},
    {"id": "glm-4p7", "name": "GLM 4.7", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": True},
    {"id": "gemma", "name": "Gemma", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "perplexity-fast", "name": "Perplexity Fast", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "perplexity-reasoning", "name": "Perplexity Reasoning", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": True},
    {"id": "minimax-m2.7", "name": "MiniMax M2.7", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "minimax-m2p7", "name": "MiniMax M2.7 (Alt)", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "nova-fast", "name": "Nova Fast", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},
    {"id": "grok-4-20-non-reasoning", "name": "Grok 4.20 (No Reasoning)", "server": "mkoloq41e34074b6133e", "vision": False, "reasoning": False},

    # === Google Gemini (srv_mkol5tgcd33cc358ddbc) ===
    {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "server": "mkol5tgcd33cc358ddbc", "vision": True, "reasoning": True},
    {"id": "gemini-2.5-flash-lite", "name": "Gemini 2.5 Flash Lite", "server": "mkol5tgcd33cc358ddbc", "vision": True, "reasoning": False},
    {"id": "gemini-3.1-flash-lite", "name": "Gemini 3.1 Flash Lite", "server": "mkol5tgcd33cc358ddbc", "vision": True, "reasoning": False},
    {"id": "gemini-3.5-flash", "name": "Gemini 3.5 Flash", "server": "mkol5tgcd33cc358ddbc", "vision": True, "reasoning": True},

    # === Google Antigravity (srv_mlv668eaa6d92f50ff10) ===
    {"id": "gemini-3-flash", "name": "Gemini 3 Flash", "server": "mlv668eaa6d92f50ff10", "vision": True, "reasoning": True},
    {"id": "gemini-3-flash-preview", "name": "Gemini 3 Flash Preview", "server": "mlv668eaa6d92f50ff10", "vision": True, "reasoning": True},
    {"id": "claude-opus-4-6-thinking", "name": "Claude Opus 4.6 Thinking", "server": "mlv668eaa6d92f50ff10", "vision": True, "reasoning": True},

    # === Rocket Hosting Gemini (srv_mp77ka5la97d6825b53b) ===
    {"id": "gemini-3.1-pro-preview", "name": "Gemini 3.1 Pro Preview", "server": "mp77ka5la97d6825b53b", "vision": True, "reasoning": True},
    {"id": "gemini-3.1-pro-preview:search", "name": "Gemini 3.1 Pro (Web Search)", "server": "mp77ka5la97d6825b53b", "vision": True, "reasoning": True},
    {"id": "gemini-3.1-flash-lite", "name": "Gemini 3.1 Flash Lite (B)", "server": "mp77ka5la97d6825b53b", "vision": True, "reasoning": False},
    {"id": "gemma-4-31b-it", "name": "Gemma 4 31B", "server": "mp77ka5la97d6825b53b", "vision": False, "reasoning": False},
    {"id": "gemma-4-26b-a4b-it", "name": "Gemma 4 26B", "server": "mp77ka5la97d6825b53b", "vision": False, "reasoning": False},

    # === crowllm.com (srv_mpsmwmt5fa6174293958) ===
    {"id": "deepseek-v4-flash", "name": "DeepSeek V4 Flash", "server": "mpsmwmt5fa6174293958", "vision": False, "reasoning": True},
    {"id": "deepseek-v4-flash-thinking", "name": "DeepSeek V4 Flash Thinking", "server": "mpsmwmt5fa6174293958", "vision": False, "reasoning": True},
    {"id": "grok-4.3", "name": "Grok 4.3", "server": "mpsmwmt5fa6174293958", "vision": False, "reasoning": False},
    {"id": "glm-5.1", "name": "GLM 5.1 (B)", "server": "mpsmwmt5fa6174293958", "vision": False, "reasoning": True},
    {"id": "glm-5.1-thinking", "name": "GLM 5.1 Thinking", "server": "mpsmwmt5fa6174293958", "vision": False, "reasoning": True},
    {"id": "glm-4.7-flash", "name": "GLM 4.7 Flash", "server": "mpsmwmt5fa6174293958", "vision": False, "reasoning": False},
    {"id": "glm-5-thinking", "name": "GLM 5 Thinking", "server": "mpsmwmt5fa6174293958", "vision": False, "reasoning": True},
    {"id": "glm-5v-turbo", "name": "GLM 5V Turbo", "server": "mpsmwmt5fa6174293958", "vision": True, "reasoning": False},

    # === consolidated multi-model (srv_mp2i8rco3148dd85bec1) ===
    {"id": "glm-5.2", "name": "GLM 5.2", "server": "mp2i8rco3148dd85bec1", "vision": False, "reasoning": True},
    {"id": "glm-5.1", "name": "GLM 5.1 (C)", "server": "mp2i8rco3148dd85bec1", "vision": False, "reasoning": True},
    {"id": "glm-5", "name": "GLM 5 (B)", "server": "mp2i8rco3148dd85bec1", "vision": False, "reasoning": True},
    {"id": "glm-4.7", "name": "GLM 4.7 (D)", "server": "mp2i8rco3148dd85bec1", "vision": False, "reasoning": False},
    {"id": "deepseek-v4-pro", "name": "DeepSeek V4 Pro (E)", "server": "mp2i8rco3148dd85bec1", "vision": False, "reasoning": True},
    {"id": "deepseek-v4-flash", "name": "DeepSeek V4 Flash (E)", "server": "mp2i8rco3148dd85bec1", "vision": False, "reasoning": True},
    {"id": "deepseek-v3.2", "name": "DeepSeek V3.2 (F)", "server": "mp2i8rco3148dd85bec1", "vision": False, "reasoning": True},
    {"id": "gemini-3-flash-preview", "name": "Gemini 3 Flash Preview (B)", "server": "mp2i8rco3148dd85bec1", "vision": True, "reasoning": True},
    {"id": "gemma4:31b", "name": "Gemma 4 31B (B)", "server": "mp2i8rco3148dd85bec1", "vision": False, "reasoning": False},
    {"id": "kimi-k2.5", "name": "Kimi K2.5 (C)", "server": "mp2i8rco3148dd85bec1", "vision": True, "reasoning": True},
    {"id": "kimi-k2.6", "name": "Kimi K2.6 (C)", "server": "mp2i8rco3148dd85bec1", "vision": True, "reasoning": True},
    {"id": "kimi-k2.7-code", "name": "Kimi K2.7 Code", "server": "mp2i8rco3148dd85bec1", "vision": True, "reasoning": True},
    {"id": "qwen3-coder-next", "name": "Qwen 3 Coder Next (B)", "server": "mp2i8rco3148dd85bec1", "vision": False, "reasoning": True},
    {"id": "qwen3-coder:480b", "name": "Qwen 3 Coder 480B", "server": "mp2i8rco3148dd85bec1", "vision": False, "reasoning": True},
    {"id": "qwen3.5:397b", "name": "Qwen 3.5 397B (B)", "server": "mp2i8rco3148dd85bec1", "vision": False, "reasoning": True},
    {"id": "minimax-m2.7", "name": "MiniMax M2.7 (B)", "server": "mp2i8rco3148dd85bec1", "vision": False, "reasoning": False},
    {"id": "ministral-3:3b", "name": "Ministral 3 3B (B)", "server": "mp2i8rco3148dd85bec1", "vision": False, "reasoning": False},
    {"id": "nemotron-3-nano:30b", "name": "Nemotron 3 Nano 30B", "server": "mp2i8rco3148dd85bec1", "vision": False, "reasoning": False},
    {"id": "gemma3:4b", "name": "Gemma 3 4B (B)", "server": "mp2i8rco3148dd85bec1", "vision": False, "reasoning": False},
    {"id": "gpt-oss:120b", "name": "GPT OSS 120B (C)", "server": "mp2i8rco3148dd85bec1", "vision": False, "reasoning": True},

    # === api.airforce (srv_mp3lmkuad07322459f47) ===
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "server": "mp3lmkuad07322459f47", "vision": False, "reasoning": False},
    {"id": "step-3.5-flash:free", "name": "Step 3.5 Flash (Free)", "server": "mp3lmkuad07322459f47", "vision": False, "reasoning": True},
    {"id": "claude-haiku-4.5-p2g", "name": "Claude Haiku 4.5", "server": "mp3lmkuad07322459f47", "vision": True, "reasoning": False},
    {"id": "grok-4.1-mini:free", "name": "Grok 4.1 Mini (Free)", "server": "mp3lmkuad07322459f47", "vision": False, "reasoning": False},
    {"id": "kimi-k2.6-thinking", "name": "Kimi K2.6 Thinking", "server": "mp3lmkuad07322459f47", "vision": True, "reasoning": True},

    # === gen.pollinations.ai (srv_mp5miql908c8738d71be) ===
    {"id": "kimi-k2.6", "name": "Kimi K2.6 (B)", "server": "mp5miql908c8738d71be", "vision": True, "reasoning": True},
    {"id": "gpt-5.5", "name": "GPT 5.5 (B)", "server": "mp5miql908c8738d71be", "vision": False, "reasoning": False},
    {"id": "grok-large", "name": "Grok Large", "server": "mp5miql908c8738d71be", "vision": False, "reasoning": False},
    {"id": "mistral-large", "name": "Mistral Large", "server": "mp5miql908c8738d71be", "vision": False, "reasoning": False},
    {"id": "qwen-coder", "name": "Qwen Coder (B)", "server": "mp5miql908c8738d71be", "vision": False, "reasoning": True},
    {"id": "openai-large", "name": "OpenAI Large (B)", "server": "mp5miql908c8738d71be", "vision": False, "reasoning": False},
    {"id": "llama", "name": "Llama (B)", "server": "mp5miql908c8738d71be", "vision": False, "reasoning": False},
    {"id": "deepseek-pro", "name": "DeepSeek Pro", "server": "mp5miql908c8738d71be", "vision": False, "reasoning": True},
    {"id": "deepseek", "name": "DeepSeek (B)", "server": "mp5miql908c8738d71be", "vision": False, "reasoning": True},
    {"id": "glm", "name": "GLM (B)", "server": "mp5miql908c8738d71be", "vision": False, "reasoning": True},

    # === cerebras.ai (srv_mlj8gd8y789d112ec50d) ===
    {"id": "gpt-oss-120b", "name": "GPT OSS 120B", "server": "mlj8gd8y789d112ec50d", "vision": False, "reasoning": True},
    {"id": "zai-glm-4.7", "name": "Z.AI GLM 4.7", "server": "mlj8gd8y789d112ec50d", "vision": False, "reasoning": False},

    # === ollama.com (srv_mnkjel2208cf770e5009) ===
    {"id": "gemma4:31b", "name": "Gemma 4 31B (Ollama)", "server": "mnkjel2208cf770e5009", "vision": False, "reasoning": False},
    {"id": "glm-4.7", "name": "GLM 4.7 (C)", "server": "mnkjel2208cf770e5009", "vision": False, "reasoning": False},
    {"id": "gpt-oss:20b", "name": "GPT OSS 20B", "server": "mnkjel2208cf770e5009", "vision": False, "reasoning": False},
    {"id": "qwen3-coder-next", "name": "Qwen 3 Coder Next", "server": "mnkjel2208cf770e5009", "vision": False, "reasoning": True},
    {"id": "nemotron-3-super", "name": "Nemotron 3 Super", "server": "mnkjel2208cf770e5009", "vision": False, "reasoning": False},
    {"id": "ministral-3:3b", "name": "Ministral 3 3B", "server": "mnkjel2208cf770e5009", "vision": False, "reasoning": False},
    {"id": "ministral-3:8b", "name": "Ministral 3 8B", "server": "mnkjel2208cf770e5009", "vision": False, "reasoning": False},
    {"id": "ministral-3:14b", "name": "Ministral 3 14B", "server": "mnkjel2208cf770e5009", "vision": False, "reasoning": False},
    {"id": "gemma3:27b", "name": "Gemma 3 27B", "server": "mnkjel2208cf770e5009", "vision": False, "reasoning": False},
    {"id": "gemma3:12b", "name": "Gemma 3 12B", "server": "mnkjel2208cf770e5009", "vision": False, "reasoning": False},

    # === openrouter.ai (srv_monk1pkz433a519ff2be) ===
    {"id": "openrouter/free", "name": "OpenRouter Free", "server": "monk1pkz433a519ff2be", "vision": False, "reasoning": False},
    {"id": "openai/gpt-oss-120b:free", "name": "GPT OSS 120B (OpenRouter)", "server": "monk1pkz433a519ff2be", "vision": False, "reasoning": True},
    {"id": "nvidia/nemotron-3-super:free", "name": "Nemotron 3 Super (OpenRouter)", "server": "monk1pkz433a519ff2be", "vision": False, "reasoning": False},

    # === Qwen (srv_mpq6idkk49907f3c4a5b) ===
    {"id": "qwen3.7-max", "name": "Qwen 3.7 Max", "server": "mpq6idkk49907f3c4a5b", "vision": False, "reasoning": True},
    {"id": "qwen3.6-plus", "name": "Qwen 3.6 Plus", "server": "mpq6idkk49907f3c4a5b", "vision": False, "reasoning": True},

    # === ModelScope (srv_mqcs3lw9218274130973) ===
    {"id": "deepseek-v4-flash", "name": "DeepSeek V4 Flash (D)", "server": "mqcs3lw9218274130973", "vision": False, "reasoning": True},
    {"id": "deepseek-v4-pro", "name": "DeepSeek V4 Pro (D)", "server": "mqcs3lw9218274130973", "vision": False, "reasoning": True},
    {"id": "deepseek-v3.2", "name": "DeepSeek V3.2 (D)", "server": "mqcs3lw9218274130973", "vision": False, "reasoning": True},

    # === ollama.swarm (srv_mq7ktfibad45c29f3839) ===
    {"id": "llama3.2:3b", "name": "Llama 3.2 3B", "server": "mq7ktfibad45c29f3839", "vision": False, "reasoning": False},
    {"id": "deepseek-r1:14b", "name": "DeepSeek R1 14B", "server": "mq7ktfibad45c29f3839", "vision": False, "reasoning": True},
    {"id": "qwen2.5:7b", "name": "Qwen 2.5 7B", "server": "mq7ktfibad45c29f3839", "vision": False, "reasoning": False},
    {"id": "gemma3:4b", "name": "Gemma 3 4B", "server": "mq7ktfibad45c29f3839", "vision": False, "reasoning": False},
    {"id": "qwen3:8b", "name": "Qwen 3 8B", "server": "mq7ktfibad45c29f3839", "vision": False, "reasoning": True},

    # === GeminiCLI (srv_mkopnfu316bf4ff43369) ===
    {"id": "gemini-3-pro-preview", "name": "Gemini 3 Pro Preview", "server": "mkopnfu316bf4ff43369", "vision": True, "reasoning": True},

    # === Pollinations AI (srv_mn1y956u9e6cfd0c1b4b) ===
    {"id": "qwen-coder", "name": "Qwen Coder (C)", "server": "mn1y956u9e6cfd0c1b4b", "vision": False, "reasoning": True},
    {"id": "deepseek", "name": "DeepSeek (C)", "server": "mn1y956u9e6cfd0c1b4b", "vision": False, "reasoning": True},
    {"id": "grok", "name": "Grok (C)", "server": "mn1y956u9e6cfd0c1b4b", "vision": False, "reasoning": False},
    {"id": "openai", "name": "OpenAI (C)", "server": "mn1y956u9e6cfd0c1b4b", "vision": False, "reasoning": False},
    {"id": "kimi", "name": "Kimi (C)", "server": "mn1y956u9e6cfd0c1b4b", "vision": True, "reasoning": True},

    # === NovaAI-Gateway (srv_moebwrnl60595ca61368) ===
    {"id": "deepseek-v3.2", "name": "DeepSeek V3.2 (E)", "server": "moebwrnl60595ca61368", "vision": False, "reasoning": True},
    {"id": "gpt-oss-120b", "name": "GPT OSS 120B (E)", "server": "moebwrnl60595ca61368", "vision": False, "reasoning": True},

    # === groq.com (srv_mkom688d57c76d8a3542) ===
    {"id": "llama-4-scout", "name": "Llama 4 Scout", "server": "mkom688d57c76d8a3542", "vision": True, "reasoning": False},
    {"id": "groq/compound", "name": "Groq Compound", "server": "mkom688d57c76d8a3542", "vision": False, "reasoning": False},

    # === OpenaiChat (srv_mkp3v4pj6b8669965b41) ===
    {"id": "gpt-5-2-thinking", "name": "GPT 5.2 Thinking", "server": "mkp3v4pj6b8669965b41", "vision": False, "reasoning": True},
    {"id": "o4-mini-high", "name": "O4 Mini High", "server": "mkp3v4pj6b8669965b41", "vision": False, "reasoning": True},
]

MODEL_MAP = {m["id"]: m for m in MODELS}

_ROTATION_ORDER = [
    "openai", "deepseek", "gpt-5.4-nano", "grok", "claude", "kimi",
    "mistral", "gemini-2.5-flash", "gemini-3.1-flash-lite",
    "deepseek-v4-flash", "glm-5.1", "qwen3-coder", "perplexity-fast",
    "gpt-5.4-reasoning", "grok-4.3", "deepseek-v4-flash-thinking",
    "gemini-3.5-flash", "gpt-4o-mini", "gpt-oss-120b",
    "deepseek-v3.2", "kimi-k2.6", "gemini-3.1-pro-preview",
    "gemma4:31b", "nemotron-3-super", "deepseek-r1:14b",
    "llama-4-scout", "step-3.5-flash:free", "o4-mini-high",
]


class G4FProvider(BaseProvider):
    supports_native_tools = True

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        return [
            {
                "id": m["id"],
                "name": m["name"],
                "context_window": resolve_context_window(m["id"]),
                "capabilities": {
                    "chat": True,
                    "stream": True,
                    "vision": m.get("vision", False),
                    "reasoning": m.get("reasoning", False),
                    "tools": True,
                },
            }
            for m in MODELS
        ]

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "",
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        logger.info("g4f: generate_stream model=%s messages=%d", model, len(messages))

        if not model:
            model = DEFAULT_MODEL

        if model not in MODEL_MAP:
            available = list(MODEL_MAP.keys())[:20]
            yield {"error": f"g4f: unknown model '{model}'. Available: {available}..."}
            return

        requested_server = MODEL_MAP[model].get("server", "")

        rotation = [model]
        for m in _ROTATION_ORDER:
            if m == model:
                continue
            ms = MODEL_MAP.get(m, {}).get("server", "")
            if ms != requested_server:
                rotation.append(m)
        for m in _ROTATION_ORDER:
            if m not in rotation:
                rotation.append(m)

        has_content = False
        last_error = None

        for attempt_idx, model_id in enumerate(rotation):
            if attempt_idx > 0:
                logger.info("g4f: rotating to '%s' (attempt %d)", model_id, attempt_idx + 1)
                if last_error and "rate" in last_error.lower():
                    await asyncio.sleep(RATE_LIMIT_SLEEP)

            tools = kwargs.get("tools")
            tool_choice = kwargs.get("tool_choice")

            flashy_msgs = []
            has_tools = bool(tools)
            if has_tools:
                flashy_msgs.append({
                    "role": "system",
                    "content": "You are a coding agent. Use the provided function tools to accomplish tasks. When you need to explore a project, call the appropriate function instead of describing what you would do.",
                })

            for msg in messages:
                content = msg.get("content", "")
                role = msg.get("role", "user")
                converted = {"role": role, "content": content}
                if has_tools and role == "user" and ("<tool_call>" in content or "<tool_result>" in content):
                    content = re.sub(r'<tool_call>.*?</tool_call>', '', content, flags=re.DOTALL)
                    content = re.sub(r'<tool_result>.*?</tool_result>', '', content, flags=re.DOTALL)
                    content = re.sub(r'## Tool Usage.*?## Rules', '## Rules', content, flags=re.DOTALL)
                    converted["content"] = content.strip()
                if role == "assistant" and "tool_calls" in msg:
                    converted["tool_calls"] = msg["tool_calls"]
                if role == "tool" and "tool_call_id" in msg:
                    converted["tool_call_id"] = msg["tool_call_id"]
                flashy_msgs.append(converted)

            body = {
                "model": model_id,
                "messages": flashy_msgs,
                "stream": True,
            }
            if tools:
                body["tools"] = tools
            if tool_choice:
                body["tool_choice"] = tool_choice

            headers = {
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            try:
                async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                    async with client.stream(
                        "POST",
                        f"{G4F_API_BASE}/chat/completions",
                        json=body,
                        headers=headers,
                    ) as resp:
                        if resp.status_code == 429:
                            last_error = f"rate limited (429) on '{model_id}'"
                            logger.warning("g4f: %s", last_error)
                            continue

                        if resp.status_code != 200:
                            error_body = await resp.aread()
                            last_error = f"HTTP {resp.status_code}: {error_body.decode('utf-8', errors='replace')[:200]}"
                            logger.warning("g4f: %s", last_error)
                            continue

                        content_type = resp.headers.get("content-type", "")

                        if "text/event-stream" in content_type:
                            tc_accumulators = {}
                            async for line in resp.aiter_lines():
                                line = line.strip()
                                if not line:
                                    continue
                                if line == "data: [DONE]":
                                    break
                                if not line.startswith("data: "):
                                    continue
                                data_str = line[6:]
                                try:
                                    event = json.loads(data_str)
                                except json.JSONDecodeError:
                                    continue

                                choices = event.get("choices", [])
                                delta = choices[0].get("delta", {}) if choices else {}
                                finish_reason = choices[0].get("finish_reason") if choices else None

                                text = delta.get("content", "")
                                if text:
                                    has_content = True
                                    yield {"text": text}

                                reasoning = delta.get("reasoning", "") or delta.get("reasoning_content", "")
                                if reasoning:
                                    yield {"reasoning": reasoning}

                                tool_calls_delta = delta.get("tool_calls")
                                if tool_calls_delta:
                                    for tc in tool_calls_delta:
                                        idx = tc.get("index", 0)
                                        if idx not in tc_accumulators:
                                            tc_accumulators[idx] = {
                                                "id": tc.get("id", ""),
                                                "name": tc.get("function", {}).get("name", ""),
                                                "arguments": "",
                                            }
                                        acc = tc_accumulators[idx]
                                        if tc.get("id"):
                                            acc["id"] = tc["id"]
                                        fn = tc.get("function", {})
                                        if fn.get("name"):
                                            acc["name"] = fn["name"]
                                        if fn.get("arguments"):
                                            acc["arguments"] += fn["arguments"]

                                if finish_reason == "tool_calls" or (finish_reason == "stop" and tc_accumulators):
                                    for idx in sorted(tc_accumulators):
                                        yield {"tool_call": dict(tc_accumulators[idx])}
                                    yield {"is_final": True, "finish_reason": "tool_calls"}
                                    return
                                elif finish_reason:
                                    yield {"is_final": True, "finish_reason": finish_reason}
                                    return

                            yield {"is_final": True, "finish_reason": "stop"}
                            return
                        else:
                            data = await resp.aread()
                            try:
                                result = json.loads(data)
                            except json.JSONDecodeError:
                                last_error = f"non-json response: {data.decode('utf-8', errors='replace')[:200]}"
                                continue

                            choices = result.get("choices", [])
                            if choices:
                                msg = choices[0].get("message", {})
                                text = msg.get("content", "")
                                reasoning = msg.get("reasoning", "") or msg.get("reasoning_content", "")
                                if text:
                                    has_content = True
                                    yield {"text": text}
                                if reasoning:
                                    yield {"reasoning": reasoning}
                                yield {"is_final": True, "finish_reason": choices[0].get("finish_reason", "stop")}
                                return
                            else:
                                last_error = f"unexpected response format: {data.decode('utf-8', errors='replace')[:200]}"
                                continue

            except Exception as exc:
                last_error = f"stream error: {exc}"
                logger.exception("g4f: %s on '%s'", exc, model_id)
                continue

        yield {"error": f"g4f: all models exhausted. Last error: {last_error}"}
