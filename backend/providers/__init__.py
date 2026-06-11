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
    elif provider_name == "ai4bharat":
        from .ai4bharat import AI4BharatProvider
        return AI4BharatProvider()
    elif provider_name == "egov":
        from .egov import EGovProvider
        return EGovProvider()
    elif provider_name == "deepai":
        from .deepai import DeepAIProvider
        return DeepAIProvider()
    elif provider_name == "eqing":
        from .eqing import EQingProvider
        return EQingProvider()
    elif provider_name == "freegpt":
        from .freegpt import FreeGPTProvider
        config = {}
        try:
            from ..config import load_config
            config = load_config()
        except Exception:
            pass
        return FreeGPTProvider(
            access_code=config.get("freegpt_access_code", ""),
            base_url=config.get("freegpt_base_url", ""),
        )
    elif provider_name == "deepseekai":
        from .deepseekai import DeepSeekAIProvider
        return DeepSeekAIProvider()
    elif provider_name == "surfsense":
        from .surfsense import SurfSenseProvider
        return SurfSenseProvider()
    else:
        return None

