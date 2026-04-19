import logging
from typing import Dict, Any, List

from curl_cffi.requests import AsyncSession

logger = logging.getLogger("flashy.qwen.models")

QWEN_URL = "https://chat.qwen.ai"

FALLBACK_MODELS = [
    {
        "id": "qwen3.6-plus",
        "name": "Qwen3.6-Plus",
        "max_context": 1000000,
        "description": "Latest Qwen3.6 series model with multimodal support",
    },
    {
        "id": "qwen3.5-plus",
        "name": "Qwen3.5-Plus",
        "max_context": 1000000,
        "description": "Latest Qwen3.5 series model with multimodal support",
    },
    {
        "id": "qwen3.5-omni-plus",
        "name": "Qwen3.5-Omni-Plus",
        "max_context": 262144,
        "description": "Native multimodal model with text, image, video, audio support",
    },
]


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


async def get_models() -> List[Dict[str, Any]]:
    try:
        async with AsyncSession(
            impersonate="chrome",
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json",
                "Origin": QWEN_URL,
                "Referer": f"{QWEN_URL}/",
            },
        ) as session:
            resp = await session.get(f"{QWEN_URL}/api/v2/models")
            if resp.status_code == 200:
                data = resp.json()
                models_data = data.get("data", {}).get("data", [])
                return [
                    _parse_model(m)
                    for m in models_data
                    if m.get("info", {}).get("is_active", False)
                    or m.get("info", {}).get("is_visitor_active", False)
                ]
    except Exception as e:
        logger.warning(f"[QWEN] Error fetching models dynamically: {e}")

    return FALLBACK_MODELS