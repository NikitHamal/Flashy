from dataclasses import dataclass, field
from typing import Optional, Any, Dict


@dataclass
class Reasoning:
    content: str
    
    def __str__(self) -> str:
        return self.content
    
    def __getitem__(self, key: str) -> Any:
        return {"reasoning": self.content}[key]
    
    def get(self, key: str, default: Any = None) -> Any:
        return {"reasoning": self.content}.get(key, default)


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    def to_dict(self) -> Dict[str, int]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens
        }


@dataclass
class ImageResponse:
    url: str
    prompt: str
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "image_url": self.url,
            "prompt": self.prompt,
            **self.extra
        }


@dataclass  
class FinishReason:
    reason: str
    
    def __str__(self) -> str:
        return self.reason


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments
        }


@dataclass
class TextContent:
    content: str
    is_final: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.content, "is_final": self.is_final}


@dataclass
class Error:
    message: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {"error": self.message}
    
    def __str__(self) -> str:
        return f"Error: {self.message}"


def reasoning_to_dict(reasoning: Reasoning) -> Dict[str, Any]:
    return {"thought": reasoning.content}


def usage_to_dict(usage: Usage) -> Dict[str, Any]:
    return usage.to_dict()


def image_response_to_dict(resp: ImageResponse) -> Dict[str, Any]:
    return resp.to_dict()


def finish_reason_to_dict(fr: FinishReason) -> Dict[str, Any]:
    return {"is_final": True, "finish_reason": fr.reason}


def tool_call_to_dict(tc: ToolCall) -> Dict[str, Any]:
    return {"tool_call": tc.to_dict()}


def text_content_to_dict(tc: TextContent) -> Dict[str, Any]:
    return tc.to_dict()


def error_to_dict(err: Error) -> Dict[str, Any]:
    return err.to_dict()