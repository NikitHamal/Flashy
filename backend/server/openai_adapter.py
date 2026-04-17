import json
import time
import uuid
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from .gateway import ProviderCompletion, ProviderRequest, ProviderGateway


class ChatMessage(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]], None] = None
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: bool = False
    temperature: float = 0.7
    top_p: float = 1.0
    max_tokens: Optional[int] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    chat_type: str = "t2t"
    thinking_enabled: bool = True
    thinking_mode: str = "Auto"


class OpenAIAdapter:
    def __init__(self, gateway: Optional[ProviderGateway] = None):
        self.gateway = gateway or ProviderGateway()

    def build_provider_request(self, request: ChatCompletionRequest) -> ProviderRequest:
        provider_name, actual_model = self.gateway.resolve_model(request.model)

        return ProviderRequest(
            provider=provider_name,
            model=actual_model,
            messages=[message.model_dump() for message in request.messages],
            stream=request.stream,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
            tools=request.tools,
            tool_choice=request.tool_choice,
            chat_type=request.chat_type,
            thinking_enabled=request.thinking_enabled,
            thinking_mode=request.thinking_mode,
            pass_through=True,
        )

    def to_openai_response(self, request: ChatCompletionRequest, completion: ProviderCompletion) -> Dict[str, Any]:
        response: Dict[str, Any] = {
            "id": f"chatcmpl-{uuid.uuid4().hex}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": completion.text if not completion.tool_calls else None,
                    },
                    "finish_reason": "tool_calls" if completion.tool_calls else completion.finish_reason,
                }
            ],
        }
        if completion.tool_calls:
            response["choices"][0]["message"]["tool_calls"] = [
                {
                    "id": tool_call.get("id", f"call_{uuid.uuid4().hex[:16]}"),
                    "type": "function",
                    "function": {
                        "name": tool_call.get("name", "unknown"),
                        "arguments": tool_call.get("arguments", "{}"),
                    },
                }
                for tool_call in completion.tool_calls
            ]
        return response

    async def stream_openai_events(self, request: ChatCompletionRequest, provider_request: ProviderRequest):
        completion_id = f"chatcmpl-{uuid.uuid4().hex}"
        created_time = int(time.time())
        tool_call_index = 0
        emitted_tool_calls = False

        def _make_chunk(delta: Dict[str, Any], finish_reason) -> str:
            payload = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": request.model,
                "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
            }
            return f"data: {json.dumps(payload)}\n\n"

        try:
            async for event in self.gateway.stream(provider_request):
                event_type = event.get("type")

                if event_type == "error":
                    payload = {
                        "error": {
                            "message": event["error"],
                            "type": "provider_error",
                            "param": None,
                            "code": None,
                        }
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                    break

                if event_type == "text":
                    yield _make_chunk({"content": event["text"]}, None)

                elif event_type == "tool_call":
                    tool_call = event["tool_call"]
                    arguments = tool_call.get("arguments", "{}")
                    if not isinstance(arguments, str):
                        arguments = json.dumps(arguments)
                    # Chunk 1: tool call content (finish_reason = null, matching OpenAI format)
                    yield _make_chunk(
                        {
                            "tool_calls": [
                                {
                                    "index": tool_call_index,
                                    "id": tool_call.get("id", f"call_{uuid.uuid4().hex[:16]}"),
                                    "type": "function",
                                    "function": {
                                        "name": tool_call.get("name", "unknown"),
                                        "arguments": arguments,
                                    },
                                }
                            ]
                        },
                        None,  # finish_reason is null on the content chunk
                    )
                    tool_call_index += 1
                    emitted_tool_calls = True

                elif event_type == "final":
                    # Use "tool_calls" as finish_reason if we emitted any tool calls,
                    # regardless of what the provider reported (it may say "stop").
                    final_finish = "tool_calls" if emitted_tool_calls else event.get("finish_reason", "stop")
                    yield _make_chunk({}, final_finish)
                    break

        finally:
            yield "data: [DONE]\n\n"
