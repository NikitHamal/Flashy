/**
 * Design Chat Module (SVG-based)
 * Handles AI chat interactions for the SVG design agent
 */
const DesignChat = {
    chatMessages: null,
    inputElement: null,
    sendButton: null,
    isGenerating: false,
    uploadedImages: [],
    currentToolPill: null,

    init() {
        this.chatMessages = document.getElementById('chat-messages');
        this.inputElement = document.getElementById('chat-input');
        this.sendButton = document.getElementById('btn-send');

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

        this.inputElement?.addEventListener('input', () => {
            this.autoResizeInput();
            this.updateSendButton();
        });

        document.getElementById('btn-attach')?.addEventListener('click', () => {
            document.getElementById('file-input')?.click();
        });

        document.getElementById('file-input')?.addEventListener('change', (e) => {
            this.handleFileUpload(e.target.files);
        });

        document.getElementById('btn-review')?.addEventListener('click', () => {
            this.sendScreenshotForReview();
        });

        document.getElementById('btn-stop')?.addEventListener('click', () => {
            this.interruptGeneration();
        });

        document.getElementById('btn-clear-chat')?.addEventListener('click', () => {
            this.clearChat();
        });
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

    autoResizeInput() {
        if (!this.inputElement) return;
        this.inputElement.style.height = 'auto';
        this.inputElement.style.height = Math.min(this.inputElement.scrollHeight, 120) + 'px';
    },

    updateSendButton() {
        if (!this.sendButton || !this.inputElement) return;
        const hasContent = this.inputElement.value.trim().length > 0 || this.uploadedImages.length > 0;
        this.sendButton.disabled = !hasContent || this.isGenerating;
    },

    setGenerating(isGenerating) {
        this.isGenerating = isGenerating;
        this.updateSendButton();

        const indicator = document.getElementById('agent-indicator');
        if (indicator) {
            indicator.classList.toggle('busy', isGenerating);
        }

        const stopBtn = document.getElementById('btn-stop');
        if (stopBtn) {
            stopBtn.classList.toggle('hidden', !isGenerating);
        }

        const reviewBtn = document.getElementById('btn-review');
        if (reviewBtn) {
            reviewBtn.disabled = isGenerating;
        }
    },

    handleFileUpload(files) {
        Array.from(files).forEach(file => {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    this.uploadedImages.push({
                        name: file.name,
                        data: e.target.result
                    });
                    this.renderUploadPreviews();
                    this.updateSendButton();
                };
                reader.readAsDataURL(file);
            }
        });

        document.getElementById('file-input').value = '';
    },

    renderUploadPreviews() {
        const container = document.getElementById('upload-previews');
        if (!container) return;

        if (this.uploadedImages.length === 0) {
            container.classList.add('hidden');
            return;
        }

        container.classList.remove('hidden');
        container.innerHTML = '';

        this.uploadedImages.forEach((img, index) => {
            const item = document.createElement('div');
            item.className = 'upload-preview';
            item.innerHTML = `
                <img src="${img.data}" alt="${img.name}">
                <button class="remove-btn" data-index="${index}">×</button>
            `;
            item.querySelector('.remove-btn').addEventListener('click', () => {
                this.uploadedImages.splice(index, 1);
                this.renderUploadPreviews();
                this.updateSendButton();
            });
            container.appendChild(item);
        });
    },

    async sendMessage() {
        const message = this.inputElement?.value.trim();
        if ((!message && this.uploadedImages.length === 0) || this.isGenerating) return;

        this.hideWelcome();

        if (message) {
            this.addMessage(message, 'user');
        }

        const canvasState = DesignCanvas.getState();

        this.inputElement.value = '';
        this.autoResizeInput();
        this.setGenerating(true);
        this.currentToolPill = null;

        const aiMessage = this.addMessage('', 'assistant');
        const aiContent = aiMessage.querySelector('.message-content');
        this.addLoadingDots(aiContent);

        try {
            const response = await fetch('/design/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: message,
                    session_id: DesignCanvas.sessionId,
                    canvas_state: canvasState,
                    images: this.uploadedImages
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
                    if (line.trim()) {
                        try {
                            const chunk = JSON.parse(line);
                            this.handleStreamChunk(chunk, aiContent);
                        } catch (e) {
                            console.error('Error parsing chunk:', e);
                        }
                    }
                }
            }

            if (aiContent && aiContent.children.length === 0) {
                aiContent.innerHTML = '<p>Design updated.</p>';
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.removeLoadingDots(aiContent);
            aiContent.innerHTML += `<div class="error">Error: ${error.message}</div>`;
        } finally {
            this.setGenerating(false);
            this.uploadedImages = [];
            this.renderUploadPreviews();
        }
    },

    handleStreamChunk(chunk, container) {
        this.removeLoadingDots(container);

        if (chunk.error) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error';
            errorDiv.textContent = `Error: ${chunk.error}`;
            container.appendChild(errorDiv);
            this.scrollToBottom();
            return;
        }

        if (chunk.thought) {
            const thoughtDiv = document.createElement('div');
            thoughtDiv.className = 'thinking-display';
            thoughtDiv.textContent = chunk.thought;
            container.appendChild(thoughtDiv);
        }

        if (chunk.text) {
            let textDiv = container.querySelector('.text-content:last-child');
            if (!textDiv) {
                textDiv = document.createElement('div');
                textDiv.className = 'text-content';
                textDiv.dataset.raw = '';
                container.appendChild(textDiv);
            }
            textDiv.dataset.raw += chunk.text;
            textDiv.innerHTML = marked.parse(textDiv.dataset.raw);
        }

        if (chunk.tool_call) {
            const toolDiv = document.createElement('div');
            toolDiv.className = 'tool-call-display';
            toolDiv.innerHTML = `<span class="tool-name">${chunk.tool_call.name}</span>`;
            container.appendChild(toolDiv);
            this.currentToolPill = toolDiv;
        }

        if (chunk.tool_result) {
            const resultDiv = document.createElement('div');
            resultDiv.className = 'tool-result-display';
            resultDiv.textContent = chunk.tool_result;
            container.appendChild(resultDiv);
        }

        // Update SVG from response
        if (chunk.svg) {
            DesignCanvas.updateSVG(chunk.svg);
        }

        // Update canvas state from response
        if (chunk.canvas_state) {
            DesignCanvas.setState(chunk.canvas_state);
        }

        if (!chunk.is_final) {
            this.addLoadingDots(container);
        }

        this.scrollToBottom();
    },

    async sendScreenshotForReview(feedback = '') {
        if (this.isGenerating) return;

        this.hideWelcome();

        const screenshot = await DesignCanvas.captureScreenshot();

        this.addMessage('Please review my current design and suggest improvements.', 'user');

        this.setGenerating(true);
        const aiMessage = this.addMessage('', 'assistant');
        const aiContent = aiMessage.querySelector('.message-content');
        this.addLoadingDots(aiContent);

        try {
            const response = await fetch('/design/review', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: DesignCanvas.sessionId,
                    screenshot_base64: screenshot,
                    feedback: feedback
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
                    if (line.trim()) {
                        try {
                            const chunk = JSON.parse(line);
                            this.handleStreamChunk(chunk, aiContent);
                        } catch (e) {
                            console.error('Error parsing chunk:', e);
                        }
                    }
                }
            }

            if (aiContent && aiContent.children.length === 0) {
                aiContent.innerHTML = '<p>Review complete.</p>';
            }
        } catch (error) {
            console.error('Error sending for review:', error);
            this.removeLoadingDots(aiContent);
            aiContent.innerHTML += `<div class="error">Error: ${error.message}</div>`;
        } finally {
            this.setGenerating(false);
        }
    },

    async interruptGeneration() {
        try {
            await fetch('/design/interrupt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: DesignCanvas.sessionId })
            });
        } catch (error) {
            console.error('Error interrupting:', error);
        }
        this.setGenerating(false);
    },

    addMessage(content, role) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        if (role === 'user') {
            contentDiv.textContent = content;
        } else {
            if (content) {
                contentDiv.innerHTML = marked.parse(content);
            }
        }

        messageDiv.appendChild(contentDiv);
        this.chatMessages?.appendChild(messageDiv);
        this.scrollToBottom();

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
        const welcome = this.chatMessages?.querySelector('.chat-welcome');
        if (welcome) {
            welcome.style.display = 'none';
        }
    },

    clearChat() {
        if (this.chatMessages) {
            this.chatMessages.innerHTML = `
                <div class="chat-welcome">
                    <div class="welcome-icon">&#x1F3A8;</div>
                    <h3>AI Design Assistant</h3>
                    <p>Describe what you want to create and I'll generate SVG graphics on the canvas. I can add shapes, text, gradients, and compose complex designs.</p>
                    <div class="suggestion-chips">
                        <button class="suggestion-chip" data-prompt="Create a modern business card for John Doe, Software Engineer">
                            Business Card
                        </button>
                        <button class="suggestion-chip" data-prompt="Design a social media banner with a gradient background and bold text">
                            Social Banner
                        </button>
                        <button class="suggestion-chip" data-prompt="Create a minimalist logo with geometric shapes">
                            Logo Design
                        </button>
                    </div>
                </div>
            `;
            this.setupSuggestionChips();
        }
    },

    scrollToBottom() {
        if (this.chatMessages) {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
    },

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};
