import logging
from typing import Dict

from fastapi import APIRouter

from ..oauth import (
    MANUAL_TOKEN_CONFIGS,
    oauth_manager,
    TokenValidationResult,
)

logger = logging.getLogger("flashy.oauth")
router = APIRouter()


@router.get("/oauth/providers")
async def oauth_providers():
    """List all OAuth providers and their manual token configurations."""
    return {
        pid: [
            {
                "token_type": cfg.token_type,
                "label": cfg.label,
                "placeholder": cfg.placeholder,
                "description": cfg.description,
                "help_url": cfg.help_url,
                "fields": cfg.fields,
            }
            for cfg in configs
        ]
        for pid, configs in MANUAL_TOKEN_CONFIGS.items()
    }


@router.post("/oauth/validate")
async def validate_token(body: Dict):
    """Validate provider credentials."""
    provider_id = body.get("provider_id", "")
    credentials = body.get("credentials", {})

    if not provider_id or not credentials:
        return {"valid": False, "error": "Missing provider_id or credentials"}

    result = await oauth_manager.validate(provider_id, credentials)
    return {
        "valid": result.valid,
        "token_type": result.token_type,
        "account_info": result.account_info,
        "error": result.error,
    }
