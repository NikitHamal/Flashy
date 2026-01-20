import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "Secure_1PSID": "",
    "Secure_1PSIDTS": "",
    "Secure_1PSIDCC": "",
    "model": "G_2_0_PRO",
    "GITHUB_PAT": "",
    "proxy": ""
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG
    
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
