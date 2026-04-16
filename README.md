# 🆓 Qwen Code + Flashy — Free AI Coding, Unstoppable

A combined repository containing **qwen-code** (the CLI coding agent by QwenLM) enhanced with **free providers from Flashy**, plus the original **Flashy** web-based coding agent.

## 🚀 What's New: Free Providers!

The Qwen Code CLI now works **completely free** — no API keys, no tokens, no login required!

### Two Free Provider Options:

#### 1. 🟢 Qwen Free (`qwen-free`)
- **No API key needed!**
- Access to latest Qwen models including **Qwen3.6-Plus**, **Qwen3.5-Plus**, **Qwen3-Coder-Plus** and more
- Uses `chat.qwen.ai` directly with browser fingerprinting
- Includes thinking/reasoning support

#### 2. 🔵 DeepInfra Free (`deepinfra-free`)
- **No API key needed!**
- Access to models like **Llama 3 (70B)**, **Qwen 2.5 Coder 32B**, **Mistral 7B**, **WizardLM-2 8x22B**
- Uses `deepinfra.com` API without authentication
- Great for variety and experimentation

## 🏁 Quick Start (Zero Config!)

```bash
# Start with Qwen Free (recommended for coding):
qwen --auth-type=qwen-free

# Start with DeepInfra Free:
qwen --auth-type=deepinfra-free

# Start with a specific model:
qwen --auth-type=qwen-free --model=qwen3-coder-plus
qwen --auth-type=deepinfra-free --model=Qwen/Qwen2.5-Coder-32B-Instruct
```

Or use the interactive setup:
```bash
qwen auth
# Then select "Qwen Free 🆓" or "DeepInfra Free 🆓"
```

## 📋 Available Free Models

### Qwen Free Models
| Model ID | Name | Description |
|---|---|---|
| `qwen3.6-plus` | Qwen3.6-Plus | Latest flagship model |
| `qwen3.5-plus` | Qwen3.5-Plus | Hybrid MoE model (default) |
| `qwen3.5-flash` | Qwen3.5-Flash | Fast and efficient |
| `qwen3.5-397b-a17b` | Qwen3.5-397B-A17B | Large MoE model |
| `qwen3-coder-plus` | Qwen3-Coder | Coding specialist |
| `qwen-max-latest` | Qwen2.5-Max | Legacy model |

### DeepInfra Free Models
| Model ID | Name | Description |
|---|---|---|
| `meta-llama/Meta-Llama-3-8B-Instruct` | Llama 3 (8B) | Fast (default) |
| `meta-llama/Meta-Llama-3-70B-Instruct` | Llama 3 (70B) | Powerful |
| `Qwen/Qwen2.5-72B-Instruct` | Qwen 2.5 72B | Qwen via DeepInfra |
| `Qwen/Qwen2.5-Coder-32B-Instruct` | Qwen 2.5 Coder 32B | Coding focused |
| `microsoft/WizardLM-2-8x22B` | WizardLM-2 8x22B | Large MoE |
| `mistralai/Mistral-7B-Instruct-v0.1` | Mistral 7B | Fast |

## 🔄 Switching Providers & Models

### Environment Variables
```bash
# Switch Qwen Free model:
export QWEN_FREE_MODEL=qwen3-coder-plus
qwen --auth-type=qwen-free

# Switch DeepInfra Free model:
export DEEPINFRA_FREE_MODEL=Qwen/Qwen2.5-Coder-32B-Instruct
qwen --auth-type=deepinfra-free
```

### Settings File
Edit `~/.qwen/settings.json`:
```json
{
  "security": {
    "auth": {
      "selectedType": "qwen-free"
    }
  },
  "model": {
    "name": "qwen3-coder-plus"
  }
}
```

### CLI Flags
```bash
qwen --auth-type=qwen-free --model=qwen3.6-plus
qwen --auth-type=deepinfra-free --model=meta-llama/Meta-Llama-3-70B-Instruct
```

## 🏗️ Repository Structure

```
├── qwen-code/          # Enhanced qwen-code CLI with free providers
│   └── packages/
│       └── core/
│           └── src/
│               └── freeProviders/    # ← NEW: Free provider implementations
│                   ├── qwen/         # Qwen free via chat.qwen.ai
│                   │   ├── cookieGenerator.ts   # Browser fingerprint generation
│                   │   └── qwenFreeProvider.ts   # Qwen free streaming API
│                   ├── deepinfra/    # DeepInfra free via API
│                   │   └── deepInfraFreeProvider.ts
│                   ├── qwenFreeContentGenerator.ts      # ContentGenerator bridge
│                   └── deepInfraFreeContentGenerator.ts  # ContentGenerator bridge
├── backend/            # Flashy backend (Python)
│   └── providers/      # Original Flashy providers (Python)
├── frontend/           # Flashy frontend
└── README.md
```

## 🛠️ Building qwen-code

```bash
cd qwen-code
npm install
npm run build
npm run bundle
```

Then run:
```bash
npm start -- --auth-type=qwen-free
```

## 💡 How It Works

The free providers use the same techniques as the Flashy agent:

- **Qwen Free**: Generates browser-like cookies/fingerprints using the same LZW compression and field structure that `chat.qwen.ai` expects. Creates a chat session, then streams responses via SSE — including thinking/reasoning tokens.

- **DeepInfra Free**: Uses the DeepInfra API's free tier which allows unauthenticated requests with browser-like headers. Streams responses via standard OpenAI-compatible SSE format.

These are the exact same methods used in the Flashy web agent, ported from Python to TypeScript and integrated into the qwen-code architecture.

## 📜 License

- **qwen-code**: Apache-2.0 (Copyright 2025 Qwen Team)
- **Flashy providers**: Apache-2.0
