from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List, Optional

class BaseProvider(ABC):
    """Base class for LLM providers."""
    
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
