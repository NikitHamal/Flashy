import time
import logging
from typing import Any, Dict, List, Optional

from ..providers import get_provider_service

logger = logging.getLogger("flashy.server.catalog")

DEFAULT_PROVIDERS = ("qwen", "deepinfra", "grok", "zai-free", "kimi", "zai", "glm", "airforce", "gradient", "lmarena", "chat2api")
PROVIDER_ALIASES = {
    "qwen-free": "qwen",
    "deepinfra-free": "deepinfra",
    "airforce-free": "airforce",
    "gradient-free": "gradient",
    "lmarena-free": "lmarena",
}


def resolve_provider_alias(provider_name: Optional[str], default: str = "qwen") -> str:
    if not provider_name:
        return default
    provider_name = provider_name.strip().lower()
    return PROVIDER_ALIASES.get(provider_name, provider_name)


def infer_capabilities(model_id: str) -> Dict[str, bool]:
    lower_id = (model_id or "").lower()
    vision_tokens = (
        "vl", "vision", "gpt-4o", "omni",
        "gemma-4", "gemma4",
        "qwen3.5", "qwen3.6", "qwen3-vl", "qwen2-vl",
        "glm-4.5v", "glm-5", "glm-4.7",
        "gemini", "claude",
        "kimi-k2", "kimi-k2.5",
        "llama-4",
        "deepseek-v4",
    )
    return {
        "chat": True,
        "stream": True,
        "vision": any(token in lower_id for token in vision_tokens),
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
                model_capabilities = model.get("capabilities", {})
                model_max_context = model.get("max_context") or model.get("context_window", 128000 if provider_name == "qwen" else 32000)

                if model_capabilities:
                    caps = {
                        "chat": True,
                        "stream": True,
                        "vision": model_capabilities.get("vision", False),
                        "reasoning": model_capabilities.get("thinking", False),
                        "tools": True,
                    }
                else:
                    caps = infer_capabilities(model_id)

                all_models.append(
                    {
                        "id": f"{provider_name}/{model_id}",
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": provider_name,
                        "name": display_name,
                        "provider": provider_name,
                        "context_window": model_max_context,
                        "capabilities": caps,
                    }
                )

        return {"object": "list", "data": all_models}
