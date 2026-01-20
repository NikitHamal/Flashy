const DesignChat = {
    chatHistory: null,
    inputElement: null,
    sendButton: null,
    isGenerating: false,
    currentToolPill: null,

    init() {
        this.chatHistory = document.getElementById('design-chat-history');
        this.inputElement = document.getElementById('design-input');
        this.sendButton = document.getElementById('btn-send-design');

        this.setupEventListeners();
        this.setupSuggestionChips();
        return this;
    },

    setupEventListeners() {
        this.sendButton?.addEventListener('click', () => this.sendMessage());
        this.inputElement?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        this.inputElement?.addEventListener('input', () => this.updateSendButton());

        document.getElementById('btn-screenshot-review')?.addEventListener('click', () => {
            this.sendScreenshotForReview();
        });
        document.getElementById('btn-interrupt')?.addEventListener('click', () => this.interruptGeneration());
        document.getElementById('btn-clear-chat')?.addEventListener('click', () => this.clearChat());
    },

    setupSuggestionChips() {
        document.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const prompt = chip.dataset.prompt;
                if (prompt) {
                    this.inputElement.value = prompt;
                    this.updateSendButton();
                    this.inputElement.focus();
                }
            });
        });
    },

    updateSendButton() {
        const hasContent = this.inputElement?.value.trim().length > 0;
        this.sendButton.disabled = !hasContent || this.isGenerating;
    },

    setGenerating(isGenerating) {
        this.isGenerating = isGenerating;
        this.updateSendButton();
        document.getElementById('agent-indicator')?.classList.toggle('working', isGenerating);
        document.getElementById('agent-indicator')?.classList.toggle('idle', !isGenerating);
        document.getElementById('btn-interrupt')?.classList.toggle('hidden', !isGenerating);
    },

    async sendMessage() {
        const message = this.inputElement?.value.trim();
        if (!message || this.isGenerating) return;

        this.hideWelcome();
        this.addMessage(message, 'user');

        this.inputElement.value = '';
        this.setGenerating(true);
        this.currentToolPill = null;

        const aiMessage = this.addMessage('', 'ai');
        const aiContent = aiMessage.querySelector('.message-content');
        this.addLoadingDots(aiContent);

        try {
            const response = await fetch('/design/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: message,
                    session_id: DesignApp.sessionId,
                    canvas_state: DesignCanvas.getState()
                })
            });

            if (!response.ok || !response.body) {
                throw new Error(`Design agent error (${response.status})`);
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
                    this.handleStreamChunk(chunk, aiContent);
                }
            }
        } catch (error) {
            this.removeLoadingDots(aiContent);
            aiContent.innerHTML += `<p class="error">Error: ${error.message}</p>`;
        } finally {
            this.setGenerating(false);
        }
    },

    handleStreamChunk(chunk, container) {
        this.removeLoadingDots(container);

        if (chunk.thought) {
            const thoughtDiv = document.createElement('div');
            thoughtDiv.className = 'thought-block';
            thoughtDiv.innerHTML = `
                <div class="thought-header">
                    <span class="material-symbols-outlined">psychology</span>
                    <span>Thinking...</span>
                </div>
                <div class="thought-content">${this.escapeHtml(chunk.thought)}</div>
            `;
            container.appendChild(thoughtDiv);
        }

        if (chunk.text) {
            let textDiv = container.querySelector('.ai-text-content:last-child');
            if (!textDiv) {
                textDiv = document.createElement('div');
                textDiv.className = 'ai-text-content';
                textDiv.dataset.raw = '';
                container.appendChild(textDiv);
            }
            textDiv.dataset.raw += chunk.text;
            textDiv.textContent = textDiv.dataset.raw;
        }

        if (chunk.tool_call) {
            const toolPill = this.createToolPill(chunk.tool_call);
            container.appendChild(toolPill);
            this.currentToolPill = toolPill;
        }

        if (chunk.tool_result) {
            if (this.currentToolPill) {
                this.updateToolResult(this.currentToolPill, chunk.tool_result);
            }
        }

        if (chunk.canvas_state) {
            DesignCanvas.setState(chunk.canvas_state);
        }

        if (chunk.canvas_action) {
            this.executeCanvasAction(chunk.canvas_action);
        }

        this.scrollToBottom();
    },

    executeCanvasAction(action) {
        const { tool, args } = action;
        switch (tool) {
            case 'set_svg':
                DesignCanvas.setState({
                    svg: args.svg,
                    width: args.width || DesignCanvas.width,
                    height: args.height || DesignCanvas.height,
                    background: args.background || DesignCanvas.background
                });
                break;
            case 'add_svg_element':
                this.appendSvg(args.svg);
                break;
            case 'update_svg_element':
                DesignCanvas.updateElement(args.element_id, args.attributes);
                break;
            case 'remove_svg_element':
                DesignCanvas.removeElement(args.element_id);
                break;
            case 'set_canvas_size':
                DesignCanvas.applyCanvasSize(args.width, args.height);
                break;
            case 'set_background':
                DesignCanvas.setBackground(args.color);
                break;
            case 'clear_canvas':
                DesignCanvas.clearCanvas();
                break;
        }
    },

    appendSvg(svgSnippet) {
        if (!svgSnippet) return;
        const parser = new DOMParser();
        const doc = parser.parseFromString(`<svg xmlns="http://www.w3.org/2000/svg">${svgSnippet}</svg>`, 'image/svg+xml');
        Array.from(doc.documentElement.children).forEach(child => {
            DesignCanvas.addElement(child);
        });
    },

    createToolPill(toolCall) {
        const pill = document.createElement('div');
        pill.className = 'design-tool-pill executing';
        pill.innerHTML = `
            <div class="tool-icon">
                <span class="material-symbols-outlined">construction</span>
            </div>
            <div class="tool-info">
                <div class="tool-name">${toolCall.name}</div>
                <div class="tool-args">SVG Tool</div>
            </div>
            <div class="tool-result"></div>
        `;
        return pill;
    },

    updateToolResult(pill, result) {
        pill.classList.remove('executing');
        pill.classList.add('completed');
        const resultDiv = pill.querySelector('.tool-result');
        if (resultDiv) resultDiv.textContent = result;
    },

    async sendScreenshotForReview() {
        const svgData = DesignCanvas.getState().svg;
        const svgBase64 = btoa(unescape(encodeURIComponent(svgData)));
        const dataUrl = `data:image/svg+xml;base64,${svgBase64}`;

        this.addMessage('Review this SVG layout and refine it.', 'user');
        this.setGenerating(true);

        const aiMessage = this.addMessage('', 'ai');
        const aiContent = aiMessage.querySelector('.message-content');
        this.addLoadingDots(aiContent);

        try {
            const response = await fetch('/design/review', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: DesignApp.sessionId,
                    screenshot_base64: dataUrl
                })
            });

            if (!response.ok || !response.body) {
                throw new Error(`Design review error (${response.status})`);
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
                    this.handleStreamChunk(chunk, aiContent);
                }
            }
        } catch (error) {
            this.removeLoadingDots(aiContent);
            aiContent.innerHTML += `<p class="error">${error.message}</p>`;
        } finally {
            this.setGenerating(false);
        }
    },

    async interruptGeneration() {
        await fetch('/design/interrupt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: DesignApp.sessionId })
        });
        this.setGenerating(false);
    },

    addMessage(content, role) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `design-message ${role}`;
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        if (role === 'user') {
            contentDiv.textContent = content;
        }
        messageDiv.appendChild(contentDiv);
        this.chatHistory.appendChild(messageDiv);
        return messageDiv;
    },

    addLoadingDots(container) {
        if (container.querySelector('.loading-dots')) return;
        const dots = document.createElement('div');
        dots.className = 'loading-dots';
        dots.innerHTML = '<span></span><span></span><span></span>';
        container.appendChild(dots);
    },

    removeLoadingDots(container) {
        container.querySelectorAll('.loading-dots').forEach(el => el.remove());
    },

    hideWelcome() {
        const welcome = this.chatHistory?.querySelector('.chat-welcome');
        if (welcome) welcome.style.display = 'none';
    },

    clearChat() {
        if (this.chatHistory) {
            this.chatHistory.innerHTML = '<div class="chat-welcome"><h3>AI Design Assistant</h3><p>Describe what you want to create.</p></div>';
        }
    },

    scrollToBottom() {
        this.chatHistory.scrollTop = this.chatHistory.scrollHeight;
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }
};
