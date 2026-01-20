const DesignChat = {
    chatHistory: null,
    inputElement: null,
    sendButton: null,
    isGenerating: false,

    init() {
        this.chatHistory = document.getElementById("design-chat-history");
        this.inputElement = document.getElementById("design-input");
        this.sendButton = document.getElementById("btn-send-design");
        this.setupEventListeners();
        return this;
    },

    setupEventListeners() {
        this.sendButton?.addEventListener("click", () => this.sendMessage());
        this.inputElement?.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        document.getElementById("btn-screenshot-review")?.addEventListener("click", () => {
            this.sendScreenshotForReview();
        });

        document.getElementById("btn-clear-chat")?.addEventListener("click", () => {
            if (this.chatHistory) this.chatHistory.innerHTML = "";
        });

        document.getElementById("btn-interrupt")?.addEventListener("click", () => {
            fetch("/design/interrupt", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: DesignApp.sessionId })
            });
            this.setGenerating(false);
        });
    },

    addMessage(content, role) {
        const msg = document.createElement("div");
        msg.className = `chat-message ${role}`;
        msg.innerHTML = `<div class="message-content">${content}</div>`;
        this.chatHistory.appendChild(msg);
        this.chatHistory.scrollTop = this.chatHistory.scrollHeight;
        return msg;
    },

    setGenerating(state) {
        this.isGenerating = state;
        const indicator = document.getElementById("agent-indicator");
        if (indicator) {
            indicator.classList.toggle("working", state);
            indicator.classList.toggle("idle", !state);
        }
    },

    async sendMessage() {
        const message = this.inputElement?.value.trim();
        if (!message || this.isGenerating) return;
        this.addMessage(message, "user");
        this.inputElement.value = "";
        this.setGenerating(true);

        const aiMessage = this.addMessage("", "ai");
        const aiContent = aiMessage.querySelector(".message-content");

        const canvasState = DesignCanvas.getState();
        const screenshot = await DesignCanvas.captureScreenshot();

        try {
            const response = await fetch("/design/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    prompt: message,
                    session_id: DesignApp.sessionId,
                    canvas_state: canvasState,
                    screenshot_base64: screenshot,
                    images: []
                })
            });

            if (!response.ok || !response.body) {
                throw new Error(`Design agent error (${response.status})`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";
                for (const line of lines) {
                    if (!line.trim()) continue;
                    const chunk = JSON.parse(line);
                    if (chunk.text) aiContent.innerHTML += chunk.text;
                    if (chunk.tool_call) {
                        aiContent.innerHTML += `<div class="tool-pill">Tool: ${chunk.tool_call.name}</div>`;
                    }
                    if (chunk.tool_result) {
                        aiContent.innerHTML += `<div class="tool-result">${chunk.tool_result}</div>`;
                    }
                    if (chunk.canvas_state) {
                        DesignCanvas.setState(chunk.canvas_state);
                    }
                    if (chunk.is_final) {
                        this.setGenerating(false);
                    }
                }
            }
        } catch (error) {
            aiContent.innerHTML = `Error: ${error.message}`;
            this.setGenerating(false);
        }
    },

    async sendScreenshotForReview() {
        if (this.isGenerating) return;
        this.setGenerating(true);
        const aiMessage = this.addMessage("", "ai");
        const aiContent = aiMessage.querySelector(".message-content");
        const screenshot = await DesignCanvas.captureScreenshot();

        try {
            const response = await fetch("/design/review", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: DesignApp.sessionId,
                    screenshot_base64: screenshot,
                    feedback: ""
                })
            });
            if (!response.ok || !response.body) {
                throw new Error(`Review error (${response.status})`);
            }
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";
                for (const line of lines) {
                    if (!line.trim()) continue;
                    const chunk = JSON.parse(line);
                    if (chunk.text) aiContent.innerHTML += chunk.text;
                    if (chunk.canvas_state) DesignCanvas.setState(chunk.canvas_state);
                    if (chunk.is_final) this.setGenerating(false);
                }
            }
        } catch (error) {
            aiContent.innerHTML = `Error: ${error.message}`;
            this.setGenerating(false);
        }
    }
};
