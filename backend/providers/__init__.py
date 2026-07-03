from .base import BaseProvider

def get_provider_service(provider_name: str) -> BaseProvider:
    if provider_name == "deepinfra":
        from .deepinfra import DeepInfraProvider
        config = {}
        try:
            from ..config import load_config
            config = load_config()
        except Exception:
            pass
        return DeepInfraProvider(
            api_key=config.get("deepinfra_api_key", ""),
        )
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
    elif provider_name == "deepseek":
        from .deepseek import DeepSeekProvider
        if not hasattr(get_provider_service, "_deepseek_instance"):
            get_provider_service._deepseek_instance = DeepSeekProvider()
        return get_provider_service._deepseek_instance
    elif provider_name == "deepseekai":
        from .deepseekai import DeepSeekAIProvider
        return DeepSeekAIProvider()
    elif provider_name == "surfsense":
        from .surfsense import SurfSenseProvider
        return SurfSenseProvider()
    elif provider_name == "chatgptfree":
        from .chatgptfree import ChatGPTFreeProvider
        return ChatGPTFreeProvider()
    elif provider_name == "rsk":
        from .rsk import RSKProvider
        return RSKProvider()
    elif provider_name == "duckai":
        from .duckai import DuckAIProvider
        return DuckAIProvider()
    elif provider_name == "chatx":
        from .chatx import ChatXProvider
        config = {}
        try:
            from ..config import load_config
            config = load_config()
        except Exception:
            pass
        return ChatXProvider(
            cookie=config.get("chatx_cookie", ""),
            base_url=config.get("chatx_base_url", ""),
        )
    elif provider_name == "gemini":
        from .gemini import GeminiProvider
        config = {}
        try:
            from ..config import load_config
            config = load_config()
        except Exception:
            pass
        return GeminiProvider(
            cookie=config.get("gemini_1psid", ""),
            cookie_ts=config.get("gemini_1psidts", ""),
            cookies_json=config.get("gemini_cookies_json", ""),
        )
    elif provider_name == "minimax":
        from .minimax import MiniMaxProvider
        return MiniMaxProvider()
    elif provider_name == "mimo":
        from .mimo import MimoProvider
        return MimoProvider()
    elif provider_name == "perplexity":
        from .perplexity import PerplexityProvider
        return PerplexityProvider()
    elif provider_name == "unimodel":
        from .unimodel import UniModelProvider
        config = {}
        try:
            from ..config import load_config
            config = load_config()
        except Exception:
            pass
        return UniModelProvider(
            api_key=config.get("unimodel_api_key", ""),
            base_url=config.get("unimodel_base_url", "https://unimodel.ai/v1"),
        )
    elif provider_name == "bai":
        from .bai import BaiProvider
        config = {}
        try:
            from ..config import load_config
            config = load_config()
        except Exception:
            pass
        return BaiProvider(
            api_key=config.get("bai_api_key", ""),
            base_url=config.get("bai_base_url", "https://api.b.ai/v1"),
        )
    elif provider_name == "openmodel":
        from .openmodel import OpenModelProvider
        config = {}
        try:
            from ..config import load_config
            config = load_config()
        except Exception:
            pass
        return OpenModelProvider(
            api_key=config.get("openmodel_api_key", ""),
            base_url=config.get("openmodel_base_url", "https://api.openmodel.app/v1"),
        )
    elif provider_name == "atomesus":
        from .atomesus import AtomesusProvider
        config = {}
        try:
            from ..config import load_config
            config = load_config()
        except Exception:
            pass
        return AtomesusProvider(
            api_keys=config.get("atomesus_api_keys", ""),
            base_url=config.get("atomesus_base_url", "https://api.atomesus.com"),
        )
    elif provider_name == "paxsenix":
        from .paxsenix import PaxSenixProvider
        config = {}
        try:
            from ..config import load_config
            config = load_config()
        except Exception:
            pass
        return PaxSenixProvider(
            api_key=config.get("paxsenix_api_key", ""),
            base_url=config.get("paxsenix_base_url", "https://api.paxsenix.org/v1"),
        )
    elif provider_name == "mistral":
        from .mistral import MistralProvider
        config = {}
        try:
            from ..config import load_config
            config = load_config()
        except Exception:
            pass
        return MistralProvider(
            api_key=config.get("mistral_api_key", ""),
            base_url=config.get("mistral_base_url", "https://api.mistral.ai/v1"),
        )
    elif provider_name == "babestown":
        from .babestown import BabelTownProvider
        config = {}
        try:
            from ..config import load_config
            config = load_config()
        except Exception:
            pass
        return BabelTownProvider(
            api_key=config.get("babestown_api_key", ""),
            base_url=config.get("babestown_base_url", "https://api.babel.town/v1"),
        )
    elif provider_name == "zenmux":
        from .zenmux import ZenMuxProvider
        config = {}
        try:
            from ..config import load_config
            config = load_config()
        except Exception:
            pass
        return ZenMuxProvider(
            api_key=config.get("zenmux_api_key", ""),
            base_url=config.get("zenmux_base_url", "https://zenmux.ai/api/v1"),
        )
    elif provider_name == "g4f":
        from .g4f import G4FProvider
        return G4FProvider()
    else:
        return None

