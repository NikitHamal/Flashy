import hashlib
import logging
from typing import Any, AsyncGenerator, Dict, List

from ..llm_runtime import helpers
from ..storage import get_chat_metadata
from .base import BaseProvider

logger = logging.getLogger("flashy.gemini")

MODELS = [
    {
        "id": "gemini-3.0-flash",
        "name": "Gemini 3.0 Flash",
        "context_window": 1000000,
        "capabilities": {"vision": True, "thinking": True, "tools": True},
    },
    {
        "id": "gemini-3.0-flash-thinking",
        "name": "Gemini 3.0 Flash Thinking",
        "context_window": 1000000,
        "capabilities": {"vision": True, "thinking": True, "tools": True},
    },
    {
        "id": "gemini-3.1-pro",
        "name": "Gemini 3.1 Pro",
        "context_window": 1000000,
        "capabilities": {"vision": True, "thinking": True, "tools": True},
    },
    {
        "id": "gemini-3.0-pro",
        "name": "Gemini 3.0 Pro",
        "context_window": 1000000,
        "capabilities": {"vision": True, "thinking": True, "tools": True},
    },
    {
        "id": "gemini-2.5-flash",
        "name": "Gemini 2.5 Flash",
        "context_window": 1000000,
        "capabilities": {"vision": True, "thinking": True, "tools": True},
    },
    {
        "id": "gemini-2.5-pro",
        "name": "Gemini 2.5 Pro",
        "context_window": 1000000,
        "capabilities": {"vision": True, "thinking": True, "tools": True},
    },
]

MODEL_ALIASES = {
    "gemini-3.0-flash": "G_3_0_FLASH",
    "gemini-3.0-flash-thinking": "G_3_0_FLASH_THINKING",
    "gemini-3.1-pro": "G_3_1_PRO",
    "gemini-3.0-pro": "G_3_0_PRO",
    "gemini-2.5-flash": "G_2_5_FLASH",
    "gemini-2.5-pro": "G_2_5_PRO",
}

_service = None


async def _get_service():
    global _service
    if _service is None:
        from ..llm_runtime.service import LLMService
        from ..llm_runtime.gemini import get_gemini_client

        _service = LLMService()
        await get_gemini_client(_service)
    return _service


def _build_prompt(messages: List[Dict[str, str]]) -> str:
    parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if not content:
            continue
        if role == "system":
            parts.append(f"[System Instructions]\n{content}\n[/System Instructions]")
        elif role == "assistant":
            parts.append(f"[Assistant]\n{content}\n[/Assistant]")
        elif role == "user":
            parts.append(content)

    if len(parts) == 1:
        return parts[0]

    system_parts = []
    conversation_parts = []
    for part in parts:
        if part.startswith("[System Instructions]"):
            system_parts.append(part)
        else:
            conversation_parts.append(part)

    combined = []
    if system_parts:
        combined.extend(system_parts)
    combined.extend(conversation_parts)
    return "\n\n".join(combined)


class GeminiProvider(BaseProvider):
    """Gemini Web API provider."""

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        return MODELS

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        service = await _get_service()

        import json
        msg_hash = hashlib.md5(json.dumps(messages[-1:], separators=(',', ':')).encode()).hexdigest()[:12]
        session_id = kwargs.get("session_id") or f"openai-{msg_hash}"
        resolved_model = helpers.resolve_gemini_model(MODEL_ALIASES.get(model, model))

        if session_id not in service.sessions:
            chat = service.gemini_client.start_chat(model=resolved_model)
            service.sessions[session_id] = chat
        else:
            chat = service.sessions[session_id]

        prompt = _build_prompt(messages)

        if not prompt.strip():
            yield {"type": "error", "error": "No user message found"}
            return

        try:
            async for chunk in chat.send_message_stream(prompt):
                text_delta = chunk.text_delta or ""
                thoughts_delta = chunk.thoughts_delta or ""

                if thoughts_delta:
                    yield {"type": "thought", "thought": thoughts_delta}
                if text_delta:
                    yield {"type": "text", "text": text_delta}

            yield {"type": "final", "finish_reason": "stop", "is_final": True}

        except Exception as e:
            logger.error(f"Gemini stream error: {e}")
            yield {"type": "error", "error": str(e)}