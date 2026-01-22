from .deepinfra import DeepInfraProvider
from .qwen import QwenProvider
from .gradient import GradientProvider
from .base import BaseProvider

def get_provider_service(provider_name: str) -> BaseProvider:
    if provider_name == "deepinfra":
        return DeepInfraProvider()
    elif provider_name == "qwen":
        return QwenProvider()
    elif provider_name == "gradient":
        return GradientProvider()
    else:
        return None
