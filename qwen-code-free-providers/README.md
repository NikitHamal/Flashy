# Qwen Code Free Providers

This module provides **FREE** access to Qwen and DeepInfra AI models for qwen-code CLI, with **no API keys required**!

## 🎁 What You Get

- **Qwen Models (FREE)**: qwen3.6-plus, qwen3.5-plus, qwen3.5-flash, qwen3-coder-plus
- **DeepInfra Models (FREE)**: Llama 3 8B/70B, Mistral 7B, Qwen2.5 72B, Qwen2.5 Coder

All models work without authentication, bypassing the 100 request/day limit!

## 🚀 Quick Start

### Option 1: Use the CLI Wrapper (Recommended)

```bash
# Setup qwen-code with free providers
./qwen-free setup

# Start the bridge server
./qwen-free server

# In another terminal, run qwen-code
qwen
```

### Option 2: Manual Configuration

1. Start the bridge server:
```bash
pip install -r requirements.txt
python bridge_server.py
```

2. Add this to your `~/.qwen/settings.json`:
```json
{
  "modelProviders": {
    "openai": [
      {
        "id": "qwen3.6-plus",
        "name": "Qwen3.6-Plus (FREE)",
        "baseUrl": "http://127.0.0.1:8787/v1",
        "description": "Qwen3.6-Plus via Free Bridge",
        "envKey": "NO_KEY_NEEDED"
      }
    ]
  },
  "security": {
    "auth": {
      "selectedType": "openai"
    }
  },
  "model": {
    "name": "qwen3.6-plus"
  }
}
```

3. Run `qwen` and enjoy free unlimited access!

## 📋 Commands

```bash
# Setup and configure
./qwen-free setup

# Start the bridge server (foreground)
./qwen-free server

# Start server and run qwen-code in one command
./qwen-free run

# Check bridge status
./qwen-free status

# Stop the bridge server
./qwen-free stop
```

## 🔄 Switching Models

Use the `/model` command inside qwen-code to switch between all configured free models.

## 🛠️ How It Works

1. **Bridge Server**: A Python FastAPI server that implements the OpenAI-compatible API
2. **Free Qwen Provider**: Uses cookie-based authentication (no OAuth/API key needed)
3. **Free DeepInfra Provider**: Uses unauthenticated access to DeepInfra's free tier
4. **Integration**: qwen-code connects to the local bridge server as if it were an OpenAI-compatible API

## 📁 Files

- `bridge_server.py` - Main bridge server with free provider implementations
- `qwen-free` - CLI wrapper for easy setup and usage
- `qwen_utils/` - Cookie generation and fingerprinting utilities
- `start.sh` - Quick start script
- `requirements.txt` - Python dependencies

## 🔧 Requirements

- Python 3.8+
- curl_cffi (for browser impersonation)
- fastapi + uvicorn
- qwen-code installed globally (`npm install -g @qwen-code/qwen-code`)

## ⚠️ Notes

- The bridge server must be running for qwen-code to work with free providers
- Free providers may have rate limits or be less reliable than paid APIs
- This is a community solution and not officially supported by Alibaba/DeepInfra
- Use at your own risk for production work

## 🤝 Credits

Based on the provider implementations from the **flashy** autonomous agent project.
