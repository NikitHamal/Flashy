from .base import BaseProvider

def get_provider_service(provider_name: str) -> BaseProvider:
    if provider_name == "deepinfra":
        from .deepinfra import DeepInfraProvider
        return DeepInfraProvider()
    elif provider_name == "qwen":
        from .qwen import QwenProvider
        return QwenProvider()
    elif provider_name == "airforce":
        from .airforce import AirforceProvider
        return AirforceProvider()
    elif provider_name == "gradient":
        from .gradient import GradientProvider
        return GradientProvider()
    elif provider_name == "gemini":
        from .gemini import GeminiProvider
        return GeminiProvider()
    elif provider_name == "grok":
        from .grok import GrokProvider
        return GrokProvider()
    elif provider_name == "kimi":
        from .kimi import KimiProvider
        return KimiProvider()
    elif provider_name == "zai":
        from .zai import ZAIProvider
        return ZAIProvider()
    elif provider_name == "zai-free":
        from .zai_free import ZAIFreeProvider
        return ZAIFreeProvider()
    elif provider_name == "glm":
        from .glm import GLMProvider
        return GLMProvider()
    elif provider_name == "chat2api":
        from .chat2api import Chat2APIProvider
        return Chat2APIProvider()
    elif provider_name == "lmarena":
        from .lmarena import LmarenaProvider
        return LmarenaProvider()
    else:
        return None

