# Flashy: Autonomous AI Coding Assistant

Flashy is a powerful, local-first AI coding assistant designed to help developers explore, modify, and manage their codebases with ease. It leverages multiple LLM providers (Gemini, Qwen, DeepInfra) to provide intelligent reasoning while maintaining direct access to your local file system and Git tools.

## 🚀 Features

- **Autonomous Agent**: Capable of planning and executing multi-step tasks independently.
- **Full File System Access**: Read, write, and surgically patch files within your workspace.
- **Integrated Terminal**: Execute shell commands and view real-time streaming output.
- **Git Management**: Seamlessly handle clones, branches, commits, and pushes directly from the interface.
- **Web Capabilities**: Search the web and browse documentation to stay up to date.
- **Local History**: Automatically saves chat history and workspace configurations locally.
- **Interactive UI**: Modern SPA (Single Page Application) frontend for a smooth user experience.
- **Free AI Providers**: Qwen and DeepInfra providers work for free without API keys!
- **Qwen Code Integration**: Full Qwen Code CLI tool with free provider support built in.

## 🆓 Free Providers (No API Key Needed!)

Flashy includes free AI providers that work without any API keys:

### Free Qwen
- **Qwen 3.6 Plus** — Latest flagship model
- **Qwen 3.5 Plus** — Powerful reasoning model  
- **Qwen 3.5 Flash** — Fast and efficient
- **Qwen 3 Coder Plus** — Coding specialist
- Works via chat.qwen.ai web interface emulation

### Free DeepInfra
- **Llama 3 8B/70B** — Meta's flagship models
- **Mistral 7B** — Fast and capable
- **Phi-3 Mini** — Microsoft's compact model
- **Gemma 2 9B** — Google's open model
- Works via unauthenticated DeepInfra API

## 🤖 Qwen Code Integration

This repo includes a modified version of [Qwen Code](https://github.com/QwenLM/qwen-code) with free provider support:

```bash
# Use Qwen Code for free (no API key)
cd qwen-code
npm install
npm run build && npm run bundle
qwen --auth-type free-qwen --model qwen3.6-plus

# Or use DeepInfra for free
qwen --auth-type free-deepinfra --model meta-llama/Meta-Llama-3-8B-Instruct
```

Access the Qwen Code terminal UI at: `http://localhost:8000/qwen-code`

## 🏗️ Architecture

Flashy is built with a decoupled architecture:

### Backend (Python/FastAPI)
- **FastAPI**: Provides the REST API and WebSocket communication.
- **Multi-Provider LLM Service**: Handles interaction with Gemini, Qwen, and DeepInfra models.
- **Modular Routers**: API endpoints are organized into specialized routers for Chat, Git, Workspaces, Configuration, and Qwen Code.
- **Tools System**: A robust suite of local operations (File I/O, Git, Terminal).
- **WebSocket Manager**: Facilitates real-time, bi-directional communication for thoughts, tool outputs, and terminal streams.

### Frontend (HTML/JS/CSS)
- **Vanilla JS SPA**: A lightweight, responsive interface.
- **WebSocket Client**: Listens for agent thoughts, tool calls, and execution results.
- **Qwen Code Terminal**: Standalone xterm.js-based terminal for the Qwen Code CLI.
- **Modular Structure**: Logic is separated into `api.js`, `websocket.js`, `ui.js`, and `app.js`.

### Qwen Code (TypeScript/Node.js)
- **Modified Qwen Code CLI**: With Free Qwen and Free DeepInfra provider support.
- **Free Content Generators**: Custom TypeScript implementations of the free providers.
- **Cookie/Fingerprint Generation**: Browser emulation for unauthenticated Qwen access.
- **Model Registry**: Hard-coded free model lists always available.

## 🛠️ Getting Started

### Prerequisites
- Python 3.8+
- Node.js 20+ (for Qwen Code)

### Quick Start (No API Key Needed!)
```bash
# Start Flashy with free providers
pip install fastapi uvicorn curl_cffi httpx pydantic
python run.py
```
The application will be available at `http://localhost:8000`.

### Full Installation (with Qwen Code)
```bash
# Install Python dependencies
pip install fastapi uvicorn curl_cffi httpx pydantic

# Install and build Qwen Code
cd qwen-code
npm install
npm run build && npm run bundle
cd ..

# Start Flashy
python run.py
```

### Running Qwen Code Standalone
```bash
cd qwen-code
# Free Qwen (no API key)
npx qwen --auth-type free-qwen --model qwen3.6-plus

# Free DeepInfra (no API key)
npx qwen --auth-type free-deepinfra --model meta-llama/Meta-Llama-3-8B-Instruct
```

## 📂 Project Structure

```text
.
├── backend/            # FastAPI server and agent logic
│   ├── agent.py        # Core agent reasoning loop
│   ├── app.py          # API endpoints and static file serving
│   ├── providers/      # LLM providers (Qwen, DeepInfra)
│   │   ├── qwen.py     # Free Qwen provider (cookie/fingerprint based)
│   │   ├── deepinfra.py # Free DeepInfra provider (unauthenticated API)
│   │   └── qwen_utils/ # Cookie generation & fingerprint utilities
│   ├── routers/        # API routers
│   │   ├── qwen_code.py # Qwen Code terminal route
│   │   └── ...
│   └── ...
├── frontend/           # SPA frontend files
│   ├── index.html      # Main entry point
│   ├── qwen-code/      # Qwen Code terminal UI
│   │   └── index.html  # Standalone terminal interface
│   ├── js/             # Frontend logic (API, WS, UI)
│   └── css/            # Styling
├── qwen-code/          # Modified Qwen Code with free providers
│   ├── packages/core/  # Core SDK with free provider generators
│   │   └── src/core/
│   │       ├── freeQwenContentGenerator/    # Free Qwen TS implementation
│   │       └── freeDeepInfraContentGenerator/ # Free DeepInfra TS implementation
│   └── packages/cli/   # CLI with free provider auth support
├── data/               # Local storage for chats and settings
├── run.py              # Main startup script
└── config.json         # User configuration
```

## 🛡️ Safety & Security

Flashy operates strictly within the workspace you define. It uses a local configuration file for sensitive keys and never uploads your code to external servers, except for the prompts sent to the LLM providers for processing.

The free providers (Qwen, DeepInfra) use browser emulation techniques to access public web interfaces without requiring authentication tokens.