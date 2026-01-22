from .deepinfra import DeepInfraProvider
from .qwen import QwenProvider
from .base import BaseProvider

def get_provider_service(provider_name: str) -> BaseProvider:
    if provider_name == "deepinfra":
        return DeepInfraProvider()
    elif provider_name == "qwen":
        return QwenProvider()
    else:
        return None
