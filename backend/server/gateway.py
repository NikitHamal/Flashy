import base64
import json
import os
import tempfile
import uuid
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
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


WEB_SCRAPER_PROVIDERS = {"qwen", "kimi", "grok", "zai", "zai-free", "glm", "chat2api", "lmarena", "ai4bharat", "egov", "deepai", "eqing", "freegpt", "deepseekai", "surfsense", "chatgptfree", "duckai", "chatx", "gemini", "rsk"}

_UPLOAD_DIR = os.path.join(os.getenv("TEMP", tempfile.gettempdir()), "flashy_uploads")

_IMAGE_MIME_EXT = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
    "image/svg+xml": ".svg",
}


class ProviderGateway:
    def __init__(self):
        self.default_provider = "airforce"

    @staticmethod
    def _extract_images_from_messages(messages: List[Dict[str, Any]]) -> List[str]:
        file_paths: List[str] = []
        for message in messages:
            content = message.get("content")
            if not isinstance(content, list):
                continue
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("type") != "image_url":
                    continue
                image_url = item.get("image_url", {})
                url = image_url.get("url", "") if isinstance(image_url, dict) else ""
                if not url:
                    continue

                if url.startswith("data:"):
                    header, _, data = url.partition(",")
                    if not data:
                        continue
                    mime = header.split(";")[0].split(":")[-1] if ":" in header else "image/png"
                    ext = _IMAGE_MIME_EXT.get(mime, ".png")
                    try:
                        raw = base64.b64decode(data, validate=True)
                    except Exception:
                        continue
                elif url.startswith(("http://", "https://")):
                    continue
                else:
                    continue

                os.makedirs(_UPLOAD_DIR, exist_ok=True)
                fpath = os.path.join(_UPLOAD_DIR, f"vision_{uuid.uuid4().hex[:8]}{ext}")
                try:
                    with open(fpath, "wb") as f:
                        f.write(raw)
                    file_paths.append(fpath)
                except Exception:
                    continue
        return file_paths

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

    def _provider_kwargs(self, request: ProviderRequest, provider_name: str = "") -> Dict[str, Any]:
        is_scraper = provider_name in WEB_SCRAPER_PROVIDERS
        resolved_name = resolve_provider_alias(request.provider, self.default_provider) if not provider_name else provider_name
        kwargs = {
            "tools": request.tools,
            "tool_choice": request.tool_choice,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "chat_type": request.chat_type,
            "thinking_enabled": request.thinking_enabled,
            "thinking_mode": request.thinking_mode,
            "is_openai_pass_through": False if is_scraper else request.pass_through,
            **request.metadata,
        }
        config = load_config()
        if resolved_name == "kimi":
            kwargs["token"] = config.get("kimi_token", "")
        elif resolved_name == "zai":
            kwargs["token"] = config.get("zai_token", "")
        elif resolved_name == "zai-free":
            pass
        elif resolved_name == "glm":
            kwargs["token"] = config.get("glm_refresh_token", "")
        elif resolved_name == "grok":
            kwargs["proxy"] = config.get("grok_proxy") or kwargs.get("proxy")
        elif resolved_name == "qwen":
            kwargs["token"] = config.get("qwen_api_token") or config.get("qwen_api_key") or ""
        elif resolved_name == "freegpt":
            kwargs["access_code"] = config.get("freegpt_access_code", "")
            kwargs["base_url"] = config.get("freegpt_base_url", "")
        return kwargs

    async def stream(self, request: ProviderRequest) -> AsyncGenerator[Dict[str, Any], None]:
        provider_name = resolve_provider_alias(request.provider, self.default_provider)
        provider_service = get_provider_service(provider_name)
        if not provider_service:
            yield {"type": "error", "error": f"Provider '{provider_name}' not found"}
            return

        is_scraper = provider_name in WEB_SCRAPER_PROVIDERS
        normalize_passthrough = False if is_scraper else request.pass_through
        normalized_messages = self.normalize_messages(request.messages, pass_through=normalize_passthrough)

        kwargs = self._provider_kwargs(request, provider_name=provider_name)

        if is_scraper:
            image_paths = self._extract_images_from_messages(request.messages)
            if image_paths:
                kwargs["files"] = image_paths

        async for chunk in provider_service.generate_stream(
            normalized_messages,
            request.model,
            **kwargs,
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
            if "usage" in chunk:
                yield {"type": "usage", "usage": chunk["usage"]}
            if chunk.get("is_final"):
                event = {
                    "type": "final",
                    "finish_reason": chunk.get("finish_reason", "stop"),
                }
                if "usage" in chunk:
                    event["usage"] = chunk["usage"]
                yield event
                return

        yield {"type": "final", "finish_reason": "stop"}

    async def complete(self, request: ProviderRequest) -> ProviderCompletion:
        text_parts: List[str] = []
        thought_parts: List[str] = []
        tool_calls: List[Dict[str, Any]] = []
        finish_reason = "stop"
        input_tokens = None
        output_tokens = None

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
            elif event_type == "usage":
                usage = event.get("usage", {})
                if usage.get("prompt_tokens") is not None:
                    input_tokens = usage["prompt_tokens"]
                if usage.get("completion_tokens") is not None:
                    output_tokens = usage["completion_tokens"]
            elif event_type == "final":
                finish_reason = event.get("finish_reason", "stop")
                usage = event.get("usage")
                if usage:
                    if usage.get("prompt_tokens") is not None:
                        input_tokens = usage["prompt_tokens"]
                    if usage.get("completion_tokens") is not None:
                        output_tokens = usage["completion_tokens"]

        return ProviderCompletion(
            text="".join(text_parts),
            thoughts="".join(thought_parts),
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            model=request.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
