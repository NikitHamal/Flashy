import re
from typing import Any

from gemini_webapi.constants import Model


def clean_response_text(service, text: str, tool_call_raw: str = None) -> str:
    if not text:
        return ""

    cleaned = text
    if tool_call_raw:
        cleaned = cleaned.replace(tool_call_raw, "").strip()

    json_block_pattern = r'```json\s*\{[^`]*?"(?:action|tool|name)"\s*:[^`]*?\}\s*```'
    cleaned = re.sub(json_block_pattern, "", cleaned, flags=re.DOTALL).strip()

    incomplete_pattern = r'```json\s*\{[^`]*$'
    cleaned = re.sub(incomplete_pattern, "", cleaned, flags=re.DOTALL).strip()

    standalone_pattern = r'(?<![`\w])\{\s*"(?:action|tool)"\s*:\s*"[^"]+"\s*,\s*"args"\s*:\s*\{[^}]*\}\s*\}(?![`\w])'
    cleaned = re.sub(standalone_pattern, "", cleaned).strip()

    return service.response_filter.filter(cleaned)


def default_gemini_model() -> Model:
    for attr in (
        "G_3_0_FLASH",
        "G_3_0_FLASH_THINKING",
        "G_3_1_PRO",
        "G_3_0_PRO",
        "G_2_5_FLASH",
        "G_2_5_PRO",
    ):
        if hasattr(Model, attr):
            return getattr(Model, attr)
    if hasattr(Model, "UNSPECIFIED"):
        return getattr(Model, "UNSPECIFIED")
    return next(iter(Model))


def resolve_gemini_model(model_name: Any) -> Model:
    if isinstance(model_name, Model):
        return model_name

    if isinstance(model_name, dict):
        if hasattr(Model, "from_dict"):
            try:
                return Model.from_dict(model_name)
            except Exception:
                pass
        return default_gemini_model()

    if not model_name:
        return default_gemini_model()

    if isinstance(model_name, str):
        if hasattr(Model, model_name):
            return getattr(Model, model_name)

        legacy_enum_aliases = {
            "G_2_5_FLASH": ["G_3_0_FLASH", "G_3_0_FLASH_THINKING", "G_2_5_FLASH"],
            "G_2_0_FLASH": ["G_3_0_FLASH", "G_3_0_FLASH_THINKING", "G_2_0_FLASH"],
            "G_2_5_PRO": ["G_3_1_PRO", "G_3_0_PRO", "G_2_5_PRO"],
            "G_2_0_PRO": ["G_3_1_PRO", "G_3_0_PRO", "G_2_0_PRO"],
        }
        if model_name in legacy_enum_aliases:
            for attr in legacy_enum_aliases[model_name]:
                if hasattr(Model, attr):
                    return getattr(Model, attr)

        legacy_name_aliases = {
            "gemini-2.5-flash": "gemini-3.0-flash",
            "gemini-2.5-pro": "gemini-3.0-pro",
            "gemini-1.5-flash": "gemini-3.0-flash",
            "gemini-1.5-pro": "gemini-3.0-pro",
        }
        candidate_names = [model_name]
        if model_name in legacy_name_aliases:
            candidate_names.insert(0, legacy_name_aliases[model_name])

        if hasattr(Model, "from_name"):
            for name in candidate_names:
                try:
                    return Model.from_name(name)
                except Exception:
                    continue

    return default_gemini_model()


def separate_thinking(service, text: str) -> tuple:
    if not text:
        return None, ""
    return service.thought_filter.extract_thoughts(text)
