from .deepinfra import DeepInfraProvider
from .qwen import QwenProvider
from .base import BaseProvider

AVAILABLE_PROVIDERS = [
    {"id": "gemini", "name": "Google Gemini (Web)", "requires_auth": True, "free": False},
    {"id": "qwen", "name": "Qwen (Alibaba)", "requires_auth": False, "free": True},
    {"id": "deepinfra", "name": "DeepInfra", "requires_auth": False, "free": True},
]

def get_provider_service(provider_name: str) -> BaseProvider:
    if provider_name == "deepinfra":
        return DeepInfraProvider()
    elif provider_name == "qwen":
        return QwenProvider()
    else:
        return None

