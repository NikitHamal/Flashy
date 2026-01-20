export class AstroChat {
    constructor({ sessionId, getContext, onUpdate }) {
        this.sessionId = sessionId;
        this.getContext = getContext;
        this.onUpdate = onUpdate;
        this.historyEl = document.getElementById("astro-chat-history");
        this.inputEl = document.getElementById("astro-input");
        this.sendBtn = document.getElementById("astro-send");
        this.statusEl = document.getElementById("astro-status");
        this.isSending = false;
    }

    init() {
        this.sendBtn?.addEventListener("click", () => this.send());
        this.inputEl?.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                this.send();
            }
        });
    }

    setStatus(busy) {
        if (!this.statusEl) return;
        this.statusEl.classList.toggle("busy", busy);
    }

    addMessage(content, role) {
        const msg = document.createElement("div");
        msg.className = `chat-msg ${role}`;
        msg.innerHTML = `<div class="chat-bubble">${content}</div>`;
        this.historyEl.appendChild(msg);
        this.historyEl.scrollTop = this.historyEl.scrollHeight;
        return msg;
    }

    async send() {
        if (this.isSending) return;
        const message = this.inputEl.value.trim();
        if (!message) return;

        this.addMessage(message, "user");
        this.inputEl.value = "";
        this.setStatus(true);
        this.isSending = true;

        const aiMsg = this.addMessage("", "ai");
        const bubble = aiMsg.querySelector(".chat-bubble");

        try {
            const context = this.getContext();
            const response = await fetch("/astro/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message,
                    session_id: this.sessionId,
                    kundalis: context.kundalis,
                    active_kundali_id: context.activeId
                })
            });

            if (!response.ok || !response.body) {
                throw new Error(`Astro agent error (${response.status})`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const parts = buffer.split("\n");
                buffer = parts.pop() || "";
                for (const part of parts) {
                    if (!part.trim()) continue;
                    const chunk = JSON.parse(part);
                    if (chunk.text) {
                        bubble.innerHTML += chunk.text;
                    }
                    if (chunk.kundali_updates) {
                        this.onUpdate?.(chunk.kundali_updates);
                    }
                    if (chunk.is_final) {
                        this.isSending = false;
                        this.setStatus(false);
                    }
                }
            }
        } catch (err) {
            bubble.innerHTML = `Error: ${err.message}`;
            this.isSending = false;
            this.setStatus(false);
        }
    }
}
