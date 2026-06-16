MODEL_METADATA = {
    # Qwen
    ("qwen", "qwen3.7-plus"): {"context_window": 1000000, "max_output": 8192},
    ("qwen", "qwen3.7-max"): {"context_window": 1000000, "max_output": 8192},
    ("qwen", "qwen3.6-plus"): {"context_window": 1000000, "max_output": 8192},
    ("qwen", "qwen3.6-max"): {"context_window": 1000000, "max_output": 8192},
    ("qwen", "qwen3.6-max-preview"): {"context_window": 1000000, "max_output": 8192},
    ("qwen", "qwen3.5-plus"): {"context_window": 1000000, "max_output": 8192},
    ("qwen", "qwen3.5-omni-plus"): {"context_window": 262144, "max_output": 8192},
    ("qwen", "qwen2.5-coder-32b"): {"context_window": 128000, "max_output": 8192},
    ("qwen", "qwq-32b"): {"context_window": 32768, "max_output": 4096},
    ("qwen", "qwq-plus"): {"context_window": 131072, "max_output": 8192},
    # DeepInfra (varies by model; use generous default)
    ("deepinfra", "*"): {"context_window": 32768, "max_output": 16384},
    # Kimi
    ("kimi", "*"): {"context_window": 128000, "max_output": 8192},
    # Grok
    ("grok", "*"): {"context_window": 131072, "max_output": 8192},
    # Airforce
    ("airforce", "*"): {"context_window": 65536, "max_output": 8192},
    # LM Arena
    ("lmarena", "*"): {"context_window": 65536, "max_output": 4096},
    # Chat2API (passthrough — depends on upstream)
    ("chat2api", "*"): {"context_window": 65536, "max_output": 8192},
    # GLM / ZAI / Gradient / FreeGPT / etc
    ("glm", "*"): {"context_window": 128000, "max_output": 4096},
    ("zai", "*"): {"context_window": 32000, "max_output": 4096},
    ("gradient", "*"): {"context_window": 32000, "max_output": 4096},
    ("freegpt", "*"): {"context_window": 32000, "max_output": 4096},
    ("deepseekai", "*"): {"context_window": 65536, "max_output": 4096},
}

DEFAULT_METADATA = {"context_window": 32000, "max_output": 4096}


def get_model_info(provider: str, model: str) -> dict:
    key = (provider, model)
    if key in MODEL_METADATA:
        return MODEL_METADATA[key]
    wildcard = (provider, "*")
    if wildcard in MODEL_METADATA:
        return MODEL_METADATA[wildcard]
    return DEFAULT_METADATA


def get_context_window(provider: str, model: str) -> int:
    return get_model_info(provider, model)["context_window"]


def get_max_output(provider: str, model: str) -> int:
    return get_model_info(provider, model)["max_output"]


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)
