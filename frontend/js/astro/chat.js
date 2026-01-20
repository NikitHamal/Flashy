const AstroChat = {
    init() {
        this.chatHistory = document.getElementById('astro-chat-history');
        this.input = document.getElementById('astro-input');
        this.sendBtn = document.getElementById('btn-send-astro');
        this.statusDot = document.getElementById('astro-status');

        this.sendBtn?.addEventListener('click', () => this.sendMessage());
        this.input?.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                this.sendMessage();
            }
        });
        this.input?.addEventListener('input', () => this.autoResize());

        document.querySelectorAll('.chip').forEach(chip => {
            chip.addEventListener('click', () => {
                this.input.value = chip.dataset.prompt || '';
                this.sendMessage();
            });
        });

        document.getElementById('btn-clear-astro')?.addEventListener('click', () => this.clearChat());
    },

    autoResize() {
        this.input.style.height = 'auto';
        this.input.style.height = `${Math.min(this.input.scrollHeight, 160)}px`;
    },

    async sendMessage() {
        const prompt = this.input.value.trim();
        if (!prompt) return;

        this.addMessage(prompt, 'user');
        this.input.value = '';
        this.autoResize();

        const aiMessage = this.addMessage('', 'ai');
        const aiContent = aiMessage.querySelector('.message-content');

        this.setStatus(true);
        try {
            const response = await fetch('/astro/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt,
                    session_id: AstroApp.sessionId,
                    kundalis_state: AstroStorage.load()
                })
            });

            if (!response.ok || !response.body) {
                throw new Error(`Astro agent error (${response.status})`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();
                for (const line of lines) {
                    if (!line.trim()) continue;
                    const chunk = JSON.parse(line);
                    this.handleChunk(chunk, aiContent);
                }
            }
        } catch (error) {
            aiContent.innerHTML += `<p class="error">${error.message}</p>`;
        } finally {
            this.setStatus(false);
        }
    },

    handleChunk(chunk, container) {
        if (chunk.thought) {
            const thought = document.createElement('div');
            thought.className = 'thought-block';
            thought.innerHTML = `
                <div class="thought-header">
                    <span class="material-symbols-outlined">psychology</span>
                    <span>Insight</span>
                </div>
                <div class="thought-content">${this.escape(chunk.thought)}</div>
            `;
            container.appendChild(thought);
        }

        if (chunk.text) {
            const block = document.createElement('p');
            block.textContent = chunk.text;
            container.appendChild(block);
        }

        if (chunk.tool_call) {
            const pill = document.createElement('div');
            pill.className = 'tool-pill';
            pill.innerHTML = `<span class="material-symbols-outlined">construction</span>${chunk.tool_call.name}`;
            container.appendChild(pill);
        }

        if (chunk.tool_result) {
            const result = document.createElement('pre');
            result.textContent = chunk.tool_result;
            container.appendChild(result);
        }

        if (chunk.kundalis_state) {
            AstroStorage.setAll(chunk.kundalis_state);
            AstroUI.render();
            AstroApp.syncKundalis();
        }

        this.scrollToBottom();
    },

    setStatus(isWorking) {
        this.statusDot.classList.toggle('active', isWorking);
    },

    addMessage(content, role) {
        const wrapper = document.createElement('div');
        wrapper.className = `message ${role}`;
        wrapper.innerHTML = `
            <div class="message-content">${role === 'user' ? this.escape(content) : ''}</div>
            <span class="message-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        `;
        this.chatHistory.appendChild(wrapper);
        this.scrollToBottom();
        return wrapper;
    },

    clearChat() {
        this.chatHistory.innerHTML = document.querySelector('.chat-welcome')?.outerHTML || '';
    },

    scrollToBottom() {
        this.chatHistory.scrollTop = this.chatHistory.scrollHeight;
    },

    escape(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }
};
