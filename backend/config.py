import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "Secure_1PSID": "",
    "Secure_1PSIDTS": "",
    "model": "G_3_0_FLASH",
    "GITHUB_PAT": "",
    "active_provider": "gemini",
    "computer_use_provider": "airforce",
    "computer_use_model": "",
    "grok_proxy": "",
    "kimi_token": "",
    "zai_token": "",
    "glm_refresh_token": "",
    "chat2api_base_url": "http://127.0.0.1:8080",
    "chat2api_api_key": "",
    "lmarena_cookies": "",
}


def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return dict(DEFAULT_CONFIG)

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    merged = dict(DEFAULT_CONFIG)
    merged.update(data)
    if merged != data:
        save_config(merged)
    return merged


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
