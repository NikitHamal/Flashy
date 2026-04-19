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
    else:
        return None

