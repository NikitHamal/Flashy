import time
import logging
from typing import Any, Dict, List, Optional

from ..providers import get_provider_service

logger = logging.getLogger("flashy.server.catalog")

DEFAULT_PROVIDERS = ("airforce", "deepinfra", "qwen", "gradient")
PROVIDER_ALIASES = {
    "qwen-free": "qwen",
    "deepinfra-free": "deepinfra",
    "airforce-free": "airforce",
    "gradient-free": "gradient",
}


def resolve_provider_alias(provider_name: Optional[str], default: str = "airforce") -> str:
    if not provider_name:
        return default
    provider_name = provider_name.strip().lower()
    return PROVIDER_ALIASES.get(provider_name, provider_name)


def infer_capabilities(model_id: str) -> Dict[str, bool]:
    lower_id = (model_id or "").lower()
    return {
        "chat": True,
        "stream": True,
        "vision": any(token in lower_id for token in ("vl", "vision", "gpt-4o", "omni")),
        "reasoning": any(token in lower_id for token in ("reason", "think", "r1", "o1", "o3", "qwq")),
        "tools": True,
    }


class ProviderCatalog:
    def __init__(self, providers: Optional[List[str]] = None):
        self.providers = providers or list(DEFAULT_PROVIDERS)

    async def list_models(self, providers: Optional[List[str]] = None) -> Dict[str, Any]:
        all_models: List[Dict[str, Any]] = []
        active_providers = [resolve_provider_alias(name) for name in (providers or self.providers)]

        for provider_name in active_providers:
            service = get_provider_service(provider_name)
            if not service:
                logger.warning("Unknown provider requested in catalog: %s", provider_name)
                continue

            try:
                models = await service.get_models()
            except Exception as exc:
                logger.warning("Failed to fetch models for %s: %s", provider_name, exc)
                continue

            for model in models:
                model_id = model.get("id", "")
                display_name = model.get("name") or model_id
                all_models.append(
                    {
                        "id": f"{provider_name}/{model_id}",
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": provider_name,
                        "name": display_name,
                        "provider": provider_name,
                        "context_window": model.get("context_window", 128000 if provider_name == "qwen" else 32000),
                        "capabilities": infer_capabilities(model_id),
                    }
                )

        return {"object": "list", "data": all_models}
