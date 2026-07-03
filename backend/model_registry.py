import logging

logger = logging.getLogger("flashy.model_registry")

CONTEXT_WINDOWS = {
    "gpt-5": 128000, "gpt-5.2": 128000, "gpt-5.4": 128000,
    "gpt-5.4-nano": 128000, "gpt-5.4-reasoning": 128000,
    "gpt-5.5": 128000, "gpt-5-2-thinking": 128000,
    "gpt-4o": 128000, "gpt-4o-mini": 128000,
    "gpt-oss": 262144, "gpt-oss-120b": 262144, "gpt-oss-20b": 262144,
    "gpt-oss:120b": 262144, "gpt-oss:20b": 262144,
    "openai": 128000, "openai-fast": 128000, "openai-large": 128000,
    "openai-audio": 128000,
    "o4-mini-high": 200000,
    "deepseek": 1048576, "deepseek-v4": 1048576,
    "deepseek-v4-flash": 1048576, "deepseek-v4-pro": 1048576,
    "deepseek-v4-flash-thinking": 1048576, "deepseek-v4-lite": 1048576,
    "deepseek-flash": 1048576, "deepseek-pro": 1048576,
    "deepseek-v3": 163840, "deepseek-v3.2": 163840,
    "deepseek-v3.1:671b": 163840, "deepseek-r1": 131072,
    "deepseek-ai": 1048576,
    "claude": 200000, "claude-fast": 200000, "claude-haiku": 200000,
    "claude-opus": 200000,
    "gemini": 1048576, "gemini-2.5": 1048576, "gemini-3": 1048576,
    "gemini-3.5": 1048576, "gemini-3.1": 1048576, "gemini-flash": 1048576,
    "grok": 131072, "grok-4": 131072, "grok-4.1": 131072,
    "grok-4.3": 131072, "grok-fast": 131072, "grok-large": 131072,
    "mistral": 128000, "mistral-large": 128000, "mistral-small": 128000,
    "mistral-small-3.1": 128000, "mistral-medium": 128000,
    "ministral": 131072, "ministral-3": 131072,
    "llama": 131072, "llama-3": 131072, "llama-4": 131072,
    "llama-scout": 131072, "llama-3.1": 131072, "llama-3.2": 131072,
    "llama-3.3": 131072, "meta-llama": 131072, "meta/llama": 131072,
    "qwen": 131072, "qwen3": 131072, "qwen3-coder": 131072,
    "qwen3.5": 131072, "qwen3.6": 131072, "qwen3.7": 131072,
    "qwen-coder": 131072, "qwen-large": 131072, "qwen-safety": 131072,
    "qwen3-next": 131072,
    "glm": 202752, "glm-4": 202752, "glm-5": 202752,
    "glm-4.7": 202752, "glm-5.1": 202752, "glm-5.2": 202752,
    "glm-4p7": 202752, "glm-5p1": 202752, "glm-5v": 202752,
    "z-ai": 202752, "zai": 202752, "zai-org": 202752,
    "kimi": 262144, "kimi-k2": 262144, "kimi-k2.5": 262144,
    "kimi-k2.6": 262144, "kimi-k2.7": 262144,
    "gemma": 32768, "gemma3": 32768, "gemma4": 262144,
    "gemma-4": 262144, "google/gemma": 262144,
    "nemotron": 262144, "nemotron-3": 262144, "nvidia/nemotron": 262144,
    "perplexity": 131072,
    "minimax": 196608, "minimax-m2": 196608, "minimax-m2.1": 196608,
    "minimax-m2.5": 196608, "minimax-m2.7": 196608,
    "minimax-m3": 196608, "minimax-m2p5": 196608, "minimax-m2p7": 196608,
    "minimaxai": 196608, "MiniMaxAI": 196608, "MiniMax/MiniMax": 196608,
    "xiaomimimo": 262144, "MiMo": 262144,
    "step": 262144, "step-3.5": 262144, "step-3.7": 262144,
    "stepfun-ai": 262144,
    "devstral": 131072,
    "rnj-1": 131072,
    "midijourney": 4096,
    "turbo": 4096,
    "polly": 4096,
    "nova": 128000, "nova-fast": 128000,
    "sarvam": 32768, "sarvamai": 32768,
    "stockmark": 131072,
    "liquid/lfm": 4096,
    "poolside": 131072,
    "huihui_ai": 262144,
    "smollm2": 2048,
    "unmoderated-gpt": 128000,
    "openrouter/free": 128000,
    "groq/compound": 131072,
    "google/diffusiongemma": 4096,
    "microsoft/phi": 131072,
}

def resolve_context_window(model_id: str, provider_default: int = 32000) -> int:
    if not model_id:
        return provider_default
    lower = model_id.lower().strip()
    matched_prefixes = []
    for prefix, ctx in CONTEXT_WINDOWS.items():
        if lower.startswith(prefix.lower()):
            matched_prefixes.append((len(prefix), ctx))
    if matched_prefixes:
        matched_prefixes.sort(key=lambda x: -x[0])
        return matched_prefixes[0][1]
    return provider_default

def resolve_context_windows(model_ids: list) -> dict:
    return {mid: resolve_context_window(mid) for mid in model_ids}
