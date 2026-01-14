# Flashy | Autonomous AI Coding Agent ⚡

Flashy is a high-performance, autonomous AI coding agent designed to live within your local development environment. Built for speed, precision, and deep integration, Flashy doesn't just suggest code—it executes tasks, manages repositories, and explores complex codebases on its own.

## 🚀 Key Features

- **Autonomous Agent Loop**: Uses the Think -> Act -> Observe cycle to solve complex programming tasks independently.
- **Rich Toolset**: Equipped with a variety of local tools including:
    - **FileSystem**: Read, write, and surgically patch files.
    - **Shell Access**: Execute terminal commands to run builds, tests, or search.
    - **Git Integration**: Clone, commit, push, pull, and branch management directly from the UI.
    - **Intelligent Search**: Deep `grep` search and symbol discovery.
    - **Web Search**: DuckDuckGo integration for real-time documentation and research.
- **Real-time WebSocket Communication**: Bidirectional streaming for instant responses and live terminal output.
- **Modern Dashboard**: A premium, minimalist UI/UX for managing multiple workspaces and chat sessions.
- **Dynamic Context**: Sidebars for real-time File Explorer, Git status, and Agent Planning (`plan.md`).
- **File Tagging**: Support for `@` mentions in chat to provide specific file context to the agent.
- **Local Persistence**: All chat history and workspace configurations are stored locally in the `data/` directory.

## 🛠️ Technology Stack

- **Backend**: Python with [FastAPI](https://fastapi.tiangolo.com/) + WebSockets.
- **AI Engine**: [Google Gemini](https://ai.google.dev/) (via `gemini-webapi`).
- **Frontend**: Vanilla HTML5, Modern CSS (system-level variables), and Interactive JavaScript.
- **Design**: Material Symbols, Poppins/Inter typography, and Atom One Dark syntax highlighting.

## 📂 Project Structure

```text
Flashy/
├── backend/                # Python FastAPI app and Agent logic
│   ├── agent.py            # Core Reasoning Engine
│   ├── app.py              # API + WebSocket Endpoints
│   ├── gemini_service.py   # Gemini API Integration
│   ├── git_manager.py      # Git Operations
│   ├── prompts.py          # System Prompts & Tool Definitions
│   ├── storage.py          # Local JSON Persistence
│   ├── tools.py            # Local system tools (FS, Shell, Search)
│   └── websocket_manager.py # WebSocket connection & terminal streaming
├── frontend/               # Web-based UI
│   ├── css/                # Modern CSS Layouts
│   ├── js/
│   │   ├── api.js          # HTTP API client
│   │   ├── websocket.js    # WebSocket client with auto-reconnect
│   │   ├── ui.js           # UI rendering & interactions
│   │   └── app.js          # App state & routing
│   └── index.html          # Main SPA Entry point
├── data/                   # Local persistence (Chats & Workspaces)
├── run.py                  # Application Entry Point
└── config.json             # API Keys & Configuration
```

## 🚦 Getting Started

### Prerequisites

- Python 3.9+
- Chrome/Edge browser for Gemini authentication cookies.

### Installation

1. Clone or download the Flashy repository.
2. Install dependencies:
   ```bash
   pip install fastapi uvicorn requests-html gemini-webapi pydantic httpx
   ```
3. Copy `config-example.json` to `config.json` and provide your Gemini session cookies (`__Secure-1PSID` and `__Secure-1PSIDTS`).
4. Optionally add your `GITHUB_PAT` for git operations.

### Running Flashy

```bash
python run.py
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

## 🧠 How it Works

Flashy operates on a **Chain of Thought** basis. When you give it a task:
1. It **Analyzes** the objective and **Explores** your workspace using `list_dir`.
2. It **Creates a Plan** (`plan.md`) to track progress.
3. It **Executes** tool calls (JSON-based) to modify files, run commands, or search the web.
4. It **Updates** the UI in real-time so you can watch its progress through the Plan sidebar.

## 🐛 Known Issues Fixed

- **Tool Mapping Bug (Jan 2026)**: The `execute()` function in `tools.py` only mapped 10 of the 22 advertised tools. Git, web search, and symbol lookup tools were promised in the system prompt but returned "Unknown tool" errors. This has been fixed.

- **Thoughts Display Bug (Jan 2026)**: AI thoughts (internal reasoning) were only displayed on the first iteration. On subsequent tool call loops, thoughts were incorrectly shown as regular AI answers. Now thoughts are properly yielded on EVERY iteration.

- **Raw JSON Leakage (Jan 2026)**: Sometimes raw JSON tool call blocks would appear in the chat output. Added `_clean_response_text()` to strip JSON artifacts before displaying.

- **Tool Call False Positives (Jan 2026)**: The tool parser was too aggressive, sometimes parsing JSON from thoughts or explanations as tool calls. Now validates against known tool names before executing.

## 🏗️ Future Roadmap

### High Priority
- [ ] **Official API Support**: Add support for Gemini API Key, OpenAI, and Anthropic APIs to eliminate cookie dependency.
- [x] **Async Terminal Streaming**: ~~Use WebSockets to stream `run_command` output in real-time.~~ ✅ Implemented!
- [ ] **Error Recovery**: Detect build/test failures and automatically attempt fixes.

### Medium Priority
- [ ] **LSP Integration**: Connect to Language Servers for Go-to-Definition and type checking.
- [ ] **Semantic Search (RAG)**: Index the codebase with embeddings for smarter file discovery.
- [ ] **Multi-Agent Orchestration**: Specialized sub-agents for UI, backend, and testing.

### Low Priority / Ideas
- [ ] **Voice Input**: Use Web Speech API for hands-free coding.
- [ ] **Browser Automation**: Add Playwright/Puppeteer tool for UI testing.
- [ ] **Code Review Mode**: Compare branches and summarize changes.

---
*Built with ❤️ for the future of agentic coding.*
