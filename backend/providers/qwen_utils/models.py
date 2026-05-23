import logging
import time
from typing import Dict, Any, List, Optional

from .auth import prepare_cookies, generate_bx_ua, build_session_headers


from curl_cffi.requests import AsyncSession

logger = logging.getLogger("flashy.qwen.models")

QWEN_URL = "https://chat.qwen.ai"

# Static fallback models
FALLBACK_MODELS = [
    {
        "id": "qwen3.7-max",
        "name": "Qwen3.7-Max",
        "max_context": 1000000,
        "description": "Frontier Qwen3.7 reasoning flagship model optimized for coding & agent workloads",
    },
    {
        "id": "qwen3.7-plus",
        "name": "Qwen3.7-Plus",
        "max_context": 1000000,
        "description": "Balanced frontier Qwen3.7 model offering high speed and intelligence",
    },
    {
        "id": "qwen3.6-max-preview",
        "name": "Qwen3.6-Max-Preview",
        "max_context": 1000000,
        "description": "High intelligence reasoning preview model in the Qwen3.6 series",
    },
    {
        "id": "qwen3.6-plus",
        "name": "Qwen3.6-Plus",
        "max_context": 1000000,
        "description": "Standard flagship Qwen3.6 series model with multimodal support",
    },
    {
        "id": "qwen3.5-plus",
        "name": "Qwen3.5-Plus",
        "max_context": 1000000,
        "description": "Balanced Qwen3.5 series model with multimodal support",
    },
    {
        "id": "qwen3.5-omni-plus",
        "name": "Qwen3.5-Omni-Plus",
        "max_context": 262144,
        "description": "Native multimodal model with text, image, video, audio support",
    },
    {
        "id": "qwen2.5-coder-32b",
        "name": "Qwen2.5-Coder-32B",
        "max_context": 128000,
        "description": "Specialized open-weight coding model with expert programming skills",
    },
    {
        "id": "qwq-32b",
        "name": "Qwq-32B",
        "max_context": 32768,
        "description": "Advanced reasoning model specializing in mathematical and logical thinking",
    },
]


# Provider-level model cache (mirrors g4f pattern)
_cached_models: List[Dict[str, Any]] = []
_cache_timestamp: float = 0.0
_CACHE_TTL_SECONDS = 300  # 5 minutes


def _parse_model(raw: dict) -> Dict[str, Any]:
    info = raw.get("info", {})
    meta = info.get("meta", {})
    caps = meta.get("capabilities", {})

    return {
        "id": raw.get("id", ""),
        "name": raw.get("name", raw.get("id", "")),
        "description": meta.get("description", ""),
        "max_context": meta.get("max_context_length", 1000000),
        "capabilities": {
            "vision": caps.get("vision", False),
            "document": caps.get("document", False),
            "video": caps.get("video", False),
            "audio": caps.get("audio", False),
            "thinking": caps.get("thinking", False),
            "search": caps.get("search", False),
        },
        "abilities": meta.get("abilities", {}),
        "mcp": meta.get("mcp", []),
        "chat_types": meta.get("chat_type", []),
        "modality": meta.get("modality", []),
        "is_active": info.get("is_active", False),
        "is_visitor_active": info.get("is_visitor_active", False),
    }


def _is_cache_valid() -> bool:
    return bool(_cached_models) and (time.time() - _cache_timestamp) < _CACHE_TTL_SECONDS



def _update_cache(models: List[Dict[str, Any]]) -> None:
    global _cached_models, _cache_timestamp
    _cached_models = models
    _cache_timestamp = time.time()


def get_cached_models() -> List[Dict[str, Any]]:
    return list(_cached_models) if _cached_models else []


def get_model_capabilities(model_id: str) -> Dict[str, Any]:
    for m in _cached_models:
        if m["id"] == model_id:
            return m.get("capabilities", {})
    return {}


async def get_models(token: Optional[str] = None) -> List[Dict[str, Any]]:
    # Return cached models if still fresh
    if _cached_models and (time.time() - _cache_timestamp) < _CACHE_TTL_SECONDS:
        return list(_cached_models)

    try:
        safe_cookies = await prepare_cookies()
        bx_ua = generate_bx_ua(safe_cookies) if safe_cookies else ""
        headers = build_session_headers(bx_ua)

        # Inject token/auth details into session if provided
        if token:
            if ";" in token or "=" in token:
                for part in token.split(";"):
                    part = part.strip()
                    if "=" in part:
                        k, v = part.split("=", 1)
                        safe_cookies[k.strip()] = v.strip()
            else:
                headers["Authorization"] = f"Bearer {token}" if not token.lower().startswith("bearer ") else token

        async with AsyncSession(
            impersonate="chrome",
            headers=headers,
            cookies=safe_cookies if safe_cookies else None,
        ) as session:
            resp = await session.get(f"{QWEN_URL}/api/v2/models")
            if resp.status_code == 200:
                data = resp.json()
                models_data = data.get("data", {}).get("data", [])
                parsed = [
                    _parse_model(m)
                    for m in models_data
                    if m.get("info", {}).get("is_active", False)
                    or m.get("info", {}).get("is_visitor_active", False)
                ]
                
                # Merge parsed models with FALLBACK_MODELS to get a robust model list
                # Keep API dynamically fetched model versions over fallback templates
                merged_map = {m["id"]: m for m in FALLBACK_MODELS}
                for pm in parsed:
                    merged_map[pm["id"]] = pm
                
                merged_list = list(merged_map.values())
                _update_cache(merged_list)
                logger.info(f"[QWEN] Loaded and merged {len(merged_list)} models ({len(parsed)} from API)")
                return merged_list
    except Exception as e:
        logger.warning(f"[QWEN] Error fetching models dynamically: {e}")

    return FALLBACK_MODELS

