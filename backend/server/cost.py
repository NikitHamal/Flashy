import logging

logger = logging.getLogger("flashy.cost")

_DEEPINFRA_PRICING_CENTS = {}

def _init_pricing():
    global _DEEPINFRA_PRICING_CENTS
    _DEEPINFRA_PRICING_CENTS = {
        "nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B": (0.00005, 0.00025),
        "nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning": (0.00002, 0.00008),
        "deepseek-ai/DeepSeek-V4-Flash": (0.00001, 0.00002),
        "deepseek-ai/DeepSeek-V4-Pro": (0.00013, 0.00026),
        "moonshotai/Kimi-K2.6": (0.000075, 0.00035),
        "XiaomiMiMo/MiMo-V2.5": (0.00004, 0.0002),
        "XiaomiMiMo/MiMo-V2.5-Pro": (0.0001, 0.0003),
        "Qwen/Qwen3.6-35B-A3B": (0.000015, 0.000095),
        "zai-org/GLM-5.1": (0.000105, 0.00035),
        "stepfun-ai/Step-3.5-Flash": (0.000009, 0.00003),
        "Qwen/Qwen3.5-397B-A17B": (0.000045, 0.0003),
        "google/gemma-4-26B-A4B-it": (0.000007, 0.000034),
        "google/gemma-4-31B-it": (0.000013, 0.000038),
        "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B": (0.00001, 0.00005),
        "zai-org/GLM-5": (0.00006, 0.000208),
        "MiniMaxAI/MiniMax-M2.5": (0.000015, 0.000115),
        "Qwen/Qwen3-Max": (0.00012, 0.0006),
        "Qwen/Qwen3-Max-Thinking": (0.00012, 0.0006),
        "moonshotai/Kimi-K2.5": (0.000045, 0.000225),
        "zai-org/GLM-4.7-Flash": (0.000006, 0.00004),
        "deepseek-ai/DeepSeek-V3.2": (0.000026, 0.000038),
    }

_init_pricing()


def calculate_cost_cents(model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
    key = model_id.split("/", 1)[-1] if "/" in model_id else model_id
    prices = _DEEPINFRA_PRICING_CENTS.get(key)
    if not prices:
        return 0.0
    input_price, output_price = prices
    return (prompt_tokens * input_price) + (completion_tokens * output_price)


def format_cost_log(provider: str, model_id: str, prompt_tokens: int, completion_tokens: int, total_tokens: int) -> str:
    cost_cents = calculate_cost_cents(model_id, prompt_tokens, completion_tokens)
    if cost_cents > 0:
        cost_str = f"${cost_cents / 100:.6f}"
    else:
        cost_str = "free/unknown"
    return (
        f"[COST] provider={provider} model={model_id} "
        f"prompt={prompt_tokens} completion={completion_tokens} total={total_tokens} "
        f"cost={cost_str}"
    )
