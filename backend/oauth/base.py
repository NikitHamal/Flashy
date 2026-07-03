import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .types import TokenValidationResult

logger = logging.getLogger("flashy.oauth")


class BaseOAuthAdapter(ABC):
    """Provider authentication adapter base class."""

    def __init__(self, provider_id: str):
        self.provider_id = provider_id

    @abstractmethod
    async def validate_token(self, credentials: Dict[str, str]) -> TokenValidationResult:
        pass

    async def refresh_token(self, credentials: Dict[str, str]) -> Optional[Dict[str, str]]:
        return None

    @staticmethod
    def parse_jwt(token: str) -> Optional[Dict[str, Any]]:
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            import base64
            padding = 4 - len(parts[1]) % 4
            if padding != 4:
                parts[1] += "=" * padding
            decoded = base64.urlsafe_b64decode(parts[1])
            return json.loads(decoded)
        except Exception:
            return None

    @staticmethod
    def is_jwt(token: str) -> bool:
        return token.startswith("eyJ") and len(token.split(".")) == 3
