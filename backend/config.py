import json
import os

from .desktop_runtime import data_file

CONFIG_FILE = os.environ.get("FLASHY_CONFIG_FILE", str(data_file("config.json")))

DEFAULT_CONFIG = {
    "model": "gpt-5.4-nano",
    "GITHUB_PAT": "",
    "active_provider": "g4f",
    "grok_proxy": "",

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
    "minimax_token": "",
    "minimax_real_user_id": "",
    "mimo_service_token": "",
    "mimo_user_id": "",
    "mimo_ph_token": "",
    "perplexity_session_token": "",
    "deepseek_token": "",
    "reasoning_effort": "medium",
    "max_agent_iterations": 25,
    "unimodel_api_key": "",
    "unimodel_base_url": "https://unimodel.ai/v1",
    "deepinfra_api_key": "",
    "bai_api_key": "",
    "bai_base_url": "https://api.b.ai/v1",
    "openmodel_api_key": "",
    "openmodel_base_url": "https://api.openmodel.app/v1",
    "atomesus_api_keys": "",
    "atomesus_base_url": "https://api.atomesus.com",
    "paxsenix_api_key": "",
    "paxsenix_base_url": "https://api.paxsenix.org/v1",
    "zenmux_api_key": "",
    "zenmux_base_url": "https://zenmux.ai/api/v1",
    "mistral_api_key": "",
    "mistral_base_url": "https://api.mistral.ai/v1",
    "babestown_api_key": "",
    "babestown_base_url": "https://api.babel.town/v1",
}


def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
            f.write("\n")
        return dict(DEFAULT_CONFIG)

    with open(CONFIG_FILE, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    merged = dict(DEFAULT_CONFIG)
    merged.update(data)
    if merged != data:
        save_config(merged)
    return merged


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
        f.write("\n")
