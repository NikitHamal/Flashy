import json
import os

from .desktop_runtime import data_file

CONFIG_FILE = os.environ.get("FLASHY_CONFIG_FILE", str(data_file("config.json")))

DEFAULT_CONFIG = {
    "model": "qwen3.6-plus",
    "GITHUB_PAT": "",
    "active_provider": "qwen",
    "grok_proxy": "",
    "kimi_token": "",
    "zai_token": "",
    "glm_refresh_token": "",
    "chat2api_base_url": "http://127.0.0.1:8080",
    "chat2api_api_key": "",
    "lmarena_cookies": "",
    "freegpt_access_code": "",
    "freegpt_base_url": "",
    "chatx_cookie": "",
    "chatx_base_url": "https://chatx.ai",
    "gemini_1psid": "",
    "gemini_1psidts": "",
    "gemini_cookies_json": "",
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
