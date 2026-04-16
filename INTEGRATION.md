# Qwen Code Free Providers Integration

This repository now contains a complete integration between **flashy** (the autonomous agent) and **qwen-code** (the CLI coding tool), providing **FREE** access to Qwen and DeepInfra AI models with **no API keys required**.

## 🎯 What You Get

### Free Models Available

**Qwen Models (via free cookie-based auth):**
- `qwen3.6-plus` - Latest Qwen 3.6 model
- `qwen3.5-plus` - Qwen 3.5 with thinking capabilities  
- `qwen3.5-flash` - Fast Qwen 3.5
- `qwen3-coder-plus` - Code-optimized model

**DeepInfra Models (unauthenticated free tier):**
- `meta-llama/Meta-Llama-3-8B-Instruct`
- `meta-llama/Meta-Llama-3-70B-Instruct`  
- `mistralai/Mistral-7B-Instruct-v0.3`
- `Qwen/Qwen2.5-72B-Instruct`
- `Qwen/Qwen2.5-Coder-32B-Instruct`

## 📁 Repository Structure

```
repo/
├── backend/
│   ├── qwen_code_tool.py          # Flashy integration for qwen-code
│   └── tools.py                   # Updated with qwen_code tool
├── qwen-code-free-providers/      # NEW: Bridge server and CLI
│   ├── bridge_server.py           # FastAPI server with free providers
│   ├── qwen-free                  # CLI wrapper for easy setup
│   ├── qwen_utils/                # Cookie/fingerprint utilities
│   │   ├── cookie_generator.py
│   │   └── fingerprint.py
│   ├── start.sh                   # Quick start script
│   ├── requirements.txt           # Python dependencies
│   └── README.md                  # Detailed usage guide
└── qwen-code/                     # Cloned qwen-code repo
    └── packages/core/             # Core TypeScript code
```

## 🚀 Quick Start

### Method 1: Using the CLI Wrapper (Easiest)

```bash
# Navigate to the free providers directory
cd qwen-code-free-providers

# Setup qwen-code with free providers
./qwen-free setup

# Start the bridge server (in one terminal)
./qwen-free server

# In another terminal, run qwen-code
qwen
```

### Method 2: Using Flashy's qwen_code Tool

From within flashy, you can now use the `qwen_code` tool:

```python
# Use qwen-code with free models
await qwen_code(
    prompt="Analyze this codebase and explain the architecture",
    working_dir="./my-project",
    model="qwen3.6-plus"
)
```

### Method 3: Manual Configuration

1. Start the bridge server:
```bash
cd qwen-code-free-providers
pip install -r requirements.txt
python bridge_server.py
```

2. Add this to `~/.qwen/settings.json`:
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
  "env": {
    "NO_KEY_NEEDED": "free-mode"
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

3. Run `qwen` and enjoy free access!

## 🔧 How It Works

### Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   qwen-code CLI │────▶│  Bridge Server   │────▶│  Free Providers │
│   (TypeScript)  │     │  (Python/FastAPI)│     │  (Qwen/DeepInf) │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                      │
        ▼                      ▼
┌─────────────────┐     ┌──────────────────┐
│  flashy agent   │────▶│  qwen_code tool  │
│  (this repo)    │     │  (sub-agent)     │
└─────────────────┘     └──────────────────┘
```

### Provider Implementations

**Free Qwen Provider:**
- Generates browser-like cookies using LZW compression and fingerprinting
- Obtains midtokens from Alibaba's auth endpoints
- Creates temporary chat sessions via Qwen's API
- Streams responses with thinking and answer phases

**Free DeepInfra Provider:**
- Uses browser impersonation (curl_cffi)
- Makes unauthenticated requests to DeepInfra's API
- Supports streaming responses

## 🔄 Switching Models

Once running, you can switch models using:

```bash
# Inside qwen-code interactive mode
/model
# Then select from the list of free models
```

Or specify when running headless:
```bash
qwen -p "Your question" --model qwen3.5-flash
```

## 📋 Available Commands

### qwen-free CLI

```bash
./qwen-free setup     # Configure qwen-code with free providers
./qwen-free server    # Start bridge server (foreground)
./qwen-free run       # Start server and run qwen-code
./qwen-free status    # Check bridge server status
./qwen-free stop      # Stop the bridge server
```

### Flashy Tool

```python
# From within flashy agent
await qwen_code(prompt, working_dir, model)
```

## 🛡️ Security Notes

- The bridge server runs locally on `127.0.0.1:8787`
- No API keys are transmitted over the network
- Cookie generation is done locally
- This is a community solution, not officially supported

## 📝 Requirements

- Python 3.8+
- Node.js 20+ (for qwen-code)
- curl_cffi Python package (for browser impersonation)
- fastapi + uvicorn
- qwen-code installed: `npm install -g @qwen-code/qwen-code`

## 🤝 Credits

- **flashy** - Original autonomous agent with free provider implementations
- **qwen-code** - Alibaba's open-source CLI coding tool
- **curl_cffi** - Browser impersonation library

## ⚠️ Disclaimer

This is a community integration to help developers who cannot afford paid API tiers. The free providers:
- May have rate limits
- May be less reliable than paid APIs
- Could change or stop working if the providers update their systems
- Are not intended for production workloads

Use at your own risk and always have a backup plan for important work.

## 🎁 For Developers with No Income

This integration was specifically created to help developers who:
- Have no income or are between jobs
- Are working on their first client projects but haven't been paid yet
- Need AI coding assistance but cannot afford API keys
- Want to learn and build without financial barriers

**You're not alone, and you deserve access to great tools too!** 💪

---

*Keep building, keep learning, keep growing!*
