"""Add cost fields to opencode.json config for DeepInfra models."""
import json

PRICING = {
    'nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B': (0.00005, 0.00025),
    'nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning': (0.00002, 0.00008),
    'deepseek-ai/DeepSeek-V4-Flash': (0.00001, 0.00002),
    'deepseek-ai/DeepSeek-V4-Pro': (0.00013, 0.00026),
    'moonshotai/Kimi-K2.6': (0.000075, 0.00035),
    'XiaomiMiMo/MiMo-V2.5': (0.00004, 0.0002),
    'XiaomiMiMo/MiMo-V2.5-Pro': (0.0001, 0.0003),
    'Qwen/Qwen3.6-35B-A3B': (0.000015, 0.000095),
    'zai-org/GLM-5.1': (0.000105, 0.00035),
    'stepfun-ai/Step-3.5-Flash': (0.000009, 0.00003),
    'Qwen/Qwen3.5-397B-A17B': (0.000045, 0.0003),
    'google/gemma-4-26B-A4B-it': (0.000007, 0.000034),
    'google/gemma-4-31B-it': (0.000013, 0.000038),
    'nvidia/NVIDIA-Nemotron-3-Super-120B-A12B': (0.00001, 0.00005),
    'zai-org/GLM-5': (0.00006, 0.000208),
    'MiniMaxAI/MiniMax-M2.5': (0.000015, 0.000115),
    'Qwen/Qwen3-Max': (0.00012, 0.0006),
    'Qwen/Qwen3-Max-Thinking': (0.00012, 0.0006),
    'moonshotai/Kimi-K2.5': (0.000045, 0.000225),
    'zai-org/GLM-4.7-Flash': (0.000006, 0.00004),
    'deepseek-ai/DeepSeek-V3.2': (0.000026, 0.000038),
}

CONFIG_PATH = r'C:\Users\Acer\.config\opencode\opencode.json'

with open(CONFIG_PATH, 'r') as f:
    config = json.loads(f.read())

flashy_models = config.get('provider', {}).get('flashy', {}).get('models', {})
count = 0

for model_id, model_config in flashy_models.items():
    if not model_id.startswith('deepinfra/'):
        continue
    model_path = model_id[len('deepinfra/'):]
    if model_path not in PRICING:
        continue
    ci, co = PRICING[model_path]
    model_config['cost'] = {
        'input': round(ci / 100, 10),
        'output': round(co / 100, 10),
    }
    count += 1

with open(CONFIG_PATH, 'w') as f:
    json.dump(config, f, indent=2)

print(f'Updated {count} models with cost info')
