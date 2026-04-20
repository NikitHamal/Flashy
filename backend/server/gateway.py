import json
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List, Optional

from ..config import load_config
from ..providers import get_provider_service
from .catalog import resolve_provider_alias


@dataclass(slots=True)
class ProviderRequest:
    provider: str
    model: str
    messages: List[Dict[str, Any]]
    stream: bool = False
    temperature: float = 0.7
    top_p: float = 1.0
    max_tokens: Optional[int] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Any] = None
    chat_type: str = "t2t"
    thinking_enabled: bool = True
    thinking_mode: str = "Auto"
    pass_through: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProviderCompletion:
    text: str = ""
    thoughts: str = ""
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    finish_reason: str = "stop"
    model: str = ""


class ProviderGateway:
    def __init__(self):
        self.default_provider = "airforce"

    @staticmethod
    def _stringify_content(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: List[str] = []
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
            return "\n".join(part for part in parts if part)
        if content is None:
            return ""
        return str(content)

    def normalize_messages(self, messages: List[Dict[str, Any]], pass_through: bool = False) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for message in messages:
            role = str(message.get("role", "user"))
            content = message.get("content")

            if pass_through:
                # Preserve the full message structure for OpenAI-compatible providers
                msg: Dict[str, Any] = {"role": role}
                # content can be None for assistant tool_call messages — keep it as-is
                if content is not None:
                    msg["content"] = content
                else:
                    msg["content"] = None
                # Pass through tool_calls on assistant messages
                if message.get("tool_calls"):
                    msg["tool_calls"] = message["tool_calls"]
                # Pass through tool_call_id on tool messages
                if message.get("tool_call_id"):
                    msg["tool_call_id"] = message["tool_call_id"]
                # Pass through name if present
                if message.get("name"):
                    msg["name"] = message["name"]
                normalized.append(msg)
            else:
                normalized.append(
                    {
                        "role": role,
                        "content": self._stringify_content(content),
                    }
                )
        return normalized

    def resolve_model(self, model_name: str) -> tuple[str, str]:
        if not model_name:
            return self.default_provider, ""
        if "/" in model_name:
            provider_name, actual_model = model_name.split("/", 1)
            return resolve_provider_alias(provider_name, self.default_provider), actual_model
        return self.default_provider, model_name

    def _provider_kwargs(self, request: ProviderRequest) -> Dict[str, Any]:
        kwargs = {
            "tools": request.tools,
            "tool_choice": request.tool_choice,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "chat_type": request.chat_type,
            "thinking_enabled": request.thinking_enabled,
            "thinking_mode": request.thinking_mode,
            "is_openai_pass_through": request.pass_through,
            **request.metadata,
        }
        provider_name = resolve_provider_alias(request.provider, self.default_provider)
        config = load_config()
        if provider_name == "kimi":
            kwargs["token"] = config.get("kimi_token", "")
        elif provider_name == "zai":
            kwargs["token"] = config.get("zai_token", "")
        elif provider_name == "zai-free":
            pass  # no token needed
        elif provider_name == "glm":
            kwargs["token"] = config.get("glm_refresh_token", "")
        elif provider_name == "grok":
            kwargs["proxy"] = config.get("grok_proxy") or kwargs.get("proxy")
        return kwargs

    async def stream(self, request: ProviderRequest) -> AsyncGenerator[Dict[str, Any], None]:
        provider_name = resolve_provider_alias(request.provider, self.default_provider)
        provider_service = get_provider_service(provider_name)
        if not provider_service:
            yield {"type": "error", "error": f"Provider '{provider_name}' not found"}
            return

        normalized_messages = self.normalize_messages(request.messages, pass_through=request.pass_through)

        async for chunk in provider_service.generate_stream(
            normalized_messages,
            request.model,
            **self._provider_kwargs(request),
        ):
            if "error" in chunk:
                yield {"type": "error", "error": chunk["error"]}
                return
            if "thought" in chunk:
                yield {"type": "thought", "thought": chunk["thought"]}
            if "text" in chunk:
                yield {"type": "text", "text": chunk["text"]}
            if "tool_call" in chunk:
                yield {"type": "tool_call", "tool_call": chunk["tool_call"]}
            if chunk.get("is_final"):
                yield {
                    "type": "final",
                    "finish_reason": chunk.get("finish_reason", "stop"),
                }
                return

        yield {"type": "final", "finish_reason": "stop"}

    async def complete(self, request: ProviderRequest) -> ProviderCompletion:
        text_parts: List[str] = []
        thought_parts: List[str] = []
        tool_calls: List[Dict[str, Any]] = []
        finish_reason = "stop"

        async for event in self.stream(request):
            event_type = event.get("type")
            if event_type == "error":
                raise RuntimeError(event["error"])
            if event_type == "thought":
                thought_parts.append(event["thought"])
            elif event_type == "text":
                text_parts.append(event["text"])
            elif event_type == "tool_call":
                tool_call = dict(event["tool_call"])
                tool_call.setdefault("id", f"call_{len(tool_calls) + 1}")
                arguments = tool_call.get("arguments", "{}")
                if not isinstance(arguments, str):
                    tool_call["arguments"] = json.dumps(arguments)
                tool_calls.append(tool_call)
            elif event_type == "final":
                finish_reason = event.get("finish_reason", "stop")

        return ProviderCompletion(
            text="".join(text_parts),
            thoughts="".join(thought_parts),
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            model=request.model,
        )
