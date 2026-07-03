from abc import ABC, abstractmethod
from enum import Enum
from typing import AsyncGenerator, Dict, Any, List, Optional


class ProviderType(Enum):
    OPENAI_COMPATIBLE = "openai"
    REVERSE_ENGINEERED = "reverse"
    PROXY = "proxy"


class BaseProvider(ABC):
    """Base class for LLM providers."""

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.REVERSE_ENGINEERED

    @property
    def supports_native_tools(self) -> bool:
        return self.provider_type == ProviderType.OPENAI_COMPATIBLE

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        pass

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        """Fetch available models for this provider."""
        return []
