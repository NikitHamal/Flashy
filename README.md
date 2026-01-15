# Flashy: Autonomous AI Coding Assistant

Flashy is a powerful, local-first AI coding assistant designed to help developers explore, modify, and manage their codebases with ease. It leverages the Gemini API to provide intelligent reasoning while maintaining direct access to your local file system and Git tools.

## 🚀 Features

- **Autonomous Agent**: Capable of planning and executing multi-step tasks independently.
- **Full File System Access**: Read, write, and surgically patch files within your workspace.
- **Integrated Terminal**: Execute shell commands and view real-time streaming output.
- **Git Management**: Seamlessly handle clones, branches, commits, and pushes directly from the interface.
- **Web Capabilities**: Search the web and browse documentation to stay up to date.
- **Local History**: Automatically saves chat history and workspace configurations locally.
- **Interactive UI**: Modern SPA (Single Page Application) frontend for a smooth user experience.

## 🏗️ Architecture

Flashy is built with a decoupled architecture:

### Backend (Python/FastAPI)
- **FastAPI**: Provides the REST API and WebSocket communication.
- **Gemini Service**: Handles interaction with Google's Gemini models.
- **Tools System**: A robust suite of local operations (File I/O, Git, Terminal).
- **WebSocket Manager**: Facilitates real-time, bi-directional communication for thoughts, tool outputs, and terminal streams.

### Frontend (HTML/JS/CSS)
- **Vanilla JS SPA**: A lightweight, responsive interface.
- **WebSocket Client**: Listens for agent thoughts, tool calls, and execution results.
- **Modular Structure**: Logic is separated into `api.js`, `websocket.js`, `ui.js`, and `app.js`.

## 🛠️ Getting Started

### Prerequisites
- Python 3.8+
- A Google Gemini API Key (configured via the UI or `config.json`)

### Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd flashy
   ```
2. Install dependencies:
   ```bash
   pip install fastapi uvicorn requests-html httpx pydantic
   ```

### Running Flashy
Start the application using the provided entry point:
```bash
python run.py
```
The application will be available at `http://localhost:8000`.

## 📂 Project Structure

```text
.
├── backend/            # FastAPI server and agent logic
│   ├── agent.py        # Core agent reasoning loop
│   ├── app.py          # API endpoints and static file serving
│   ├── tools.py        # File system, Git, and Web tools
│   └── ...
├── frontend/           # SPA frontend files
│   ├── index.html      # Main entry point
│   ├── js/             # Frontend logic (API, WS, UI)
│   └── css/            # Styling
├── data/               # Local storage for chats and settings
├── run.py              # Main startup script
└── config.json         # User configuration (API keys, etc.)
```

## 🛡️ Safety & Security
Flashy operates strictly within the workspace you define. It uses a local configuration file for sensitive keys and never uploads your code to external servers, except for the prompts sent to the Gemini API for processing.