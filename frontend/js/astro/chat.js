/**
 * Astro Chat Module
 * 
 * Handles the AI chat interface for the Flashy Astro agent.
 */

const AstroChat = {
    messagesContainer: null,
    inputElement: null,
    sendButton: null,
    isStreaming: false,
    currentAssistantMessage: null,
    
    /**
     * Initialize the chat module
     */
    init() {
        this.messagesContainer = document.getElementById('chat-messages');
        this.inputElement = document.getElementById('chat-input');
        this.sendButton = document.getElementById('btn-send');
        
        // Setup event listeners
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        this.inputElement.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize textarea
        this.inputElement.addEventListener('input', () => {
            this.inputElement.style.height = 'auto';
            this.inputElement.style.height = Math.min(this.inputElement.scrollHeight, 120) + 'px';
        });
        
        // Clear chat button
        document.getElementById('btn-clear-chat')?.addEventListener('click', () => {
            this.clearChat();
        });
        
        // Load chat history
        this.loadHistory();
    },
    
    /**
     * Send a message to the Astro AI
     */
    async sendMessage() {
        const message = this.inputElement.value.trim();
        if (!message || this.isStreaming) return;
        
        // Clear input
        this.inputElement.value = '';
        this.inputElement.style.height = 'auto';
        
        // Add user message
        this.addUserMessage(message);
        AstroStorage.addChatMessage({ role: 'user', content: message });
        
        // Start streaming
        this.isStreaming = true;
        this.sendButton.disabled = true;
        
        // Create assistant message container
        this.currentAssistantMessage = this.createAssistantMessage();
        
        try {
            const sessionId = AstroStorage.getSessionId();
            const profiles = AstroStorage.getProfiles();
            
            const reader = await AstroAPI.chat(message, sessionId, profiles);
            
            let fullText = '';
            let thoughts = '';
            
            for await (const chunk of AstroAPI.parseStream(reader)) {
                if (chunk.thought) {
                    thoughts += chunk.thought;
                    this.updateThought(thoughts);
                }
                
                if (chunk.text) {
                    fullText += chunk.text;
                    this.updateAssistantMessage(fullText);
                }
                
                if (chunk.tool_call) {
                    this.addToolCall(chunk.tool_call);
                }
                
                if (chunk.tool_result) {
                    this.updateToolResult(chunk.tool_result);
                }
                
                if (chunk.profiles_update) {
                    AstroStorage.syncFromBackend(chunk.profiles_update);
                    // Trigger UI refresh
                    if (window.AstroApp) {
                        window.AstroApp.renderKundaliList();
                    }
                }
                
                if (chunk.error) {
                    this.addErrorMessage(chunk.error);
                }
                
                if (chunk.is_final) {
                    AstroStorage.addChatMessage({ role: 'assistant', content: fullText });
                }
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.addErrorMessage('Failed to get response. Please try again.');
        } finally {
            this.isStreaming = false;
            this.sendButton.disabled = false;
            this.currentAssistantMessage = null;
            this.scrollToBottom();
        }
    },
    
    /**
     * Add a user message to the chat
     */
    addUserMessage(content) {
        const message = document.createElement('div');
        message.className = 'chat-message user';
        message.innerHTML = `
            <div class="message-bubble">${this.escapeHtml(content)}</div>
        `;
        this.messagesContainer.appendChild(message);
        this.scrollToBottom();
    },
    
    /**
     * Create an assistant message container
     */
    createAssistantMessage() {
        const message = document.createElement('div');
        message.className = 'chat-message assistant';
        message.innerHTML = `
            <div class="avatar">
                <span class="material-symbols-outlined">auto_awesome</span>
            </div>
            <div class="message-bubble">
                <div class="thought-block hidden"></div>
                <div class="message-text"></div>
                <div class="tool-calls"></div>
            </div>
        `;
        this.messagesContainer.appendChild(message);
        this.scrollToBottom();
        return message;
    },
    
    /**
     * Update the current assistant message text
     */
    updateAssistantMessage(text) {
        if (!this.currentAssistantMessage) return;
        
        const textEl = this.currentAssistantMessage.querySelector('.message-text');
        if (textEl) {
            // Parse markdown
            textEl.innerHTML = marked.parse(text);
        }
        this.scrollToBottom();
    },
    
    /**
     * Update the thought block
     */
    updateThought(thought) {
        if (!this.currentAssistantMessage) return;
        
        const thoughtEl = this.currentAssistantMessage.querySelector('.thought-block');
        if (thoughtEl) {
            thoughtEl.classList.remove('hidden');
            thoughtEl.textContent = thought;
        }
    },
    
    /**
     * Add a tool call indicator
     */
    addToolCall(toolCall) {
        if (!this.currentAssistantMessage) return;
        
        const toolsEl = this.currentAssistantMessage.querySelector('.tool-calls');
        if (toolsEl) {
            const pill = document.createElement('div');
            pill.className = 'tool-call-pill';
            pill.dataset.tool = toolCall.name;
            pill.innerHTML = `
                <span class="material-symbols-outlined" style="font-size:14px;">construction</span>
                <span>${toolCall.name}</span>
                <span class="tool-status">...</span>
            `;
            toolsEl.appendChild(pill);
        }
        this.scrollToBottom();
    },
    
    /**
     * Update the last tool call with result
     */
    updateToolResult(result) {
        if (!this.currentAssistantMessage) return;
        
        const toolsEl = this.currentAssistantMessage.querySelector('.tool-calls');
        const lastPill = toolsEl?.querySelector('.tool-call-pill:last-child');
        
        if (lastPill) {
            const statusEl = lastPill.querySelector('.tool-status');
            if (statusEl) {
                const isError = result.toLowerCase().includes('error');
                statusEl.textContent = isError ? '!' : '✓';
                statusEl.style.color = isError ? 'var(--color-danger)' : 'var(--color-success)';
            }
        }
    },
    
    /**
     * Add an error message
     */
    addErrorMessage(error) {
        const message = document.createElement('div');
        message.className = 'chat-message assistant';
        message.innerHTML = `
            <div class="avatar" style="background:var(--color-danger);">
                <span class="material-symbols-outlined" style="color:white;">error</span>
            </div>
            <div class="message-bubble" style="border-color:var(--color-danger);">
                <div class="message-text" style="color:var(--color-danger);">
                    ${this.escapeHtml(error)}
                </div>
            </div>
        `;
        this.messagesContainer.appendChild(message);
        this.scrollToBottom();
    },
    
    /**
     * Clear chat messages (keep welcome message)
     */
    clearChat() {
        const welcomeMessage = this.messagesContainer.querySelector('.welcome-message');
        this.messagesContainer.innerHTML = '';
        if (welcomeMessage) {
            this.messagesContainer.appendChild(welcomeMessage);
        }
        AstroStorage.clearChatHistory();
    },
    
    /**
     * Load chat history
     */
    loadHistory() {
        const history = AstroStorage.getChatHistory();
        
        for (const msg of history) {
            if (msg.role === 'user') {
                this.addUserMessage(msg.content);
            } else if (msg.role === 'assistant') {
                const container = this.createAssistantMessage();
                const textEl = container.querySelector('.message-text');
                if (textEl) {
                    textEl.innerHTML = marked.parse(msg.content);
                }
            }
        }
        
        this.scrollToBottom();
    },
    
    /**
     * Add a system message (for context about selected kundali)
     */
    addSystemMessage(content) {
        const message = document.createElement('div');
        message.className = 'chat-message system';
        message.innerHTML = `
            <div class="system-message">
                <span class="material-symbols-outlined">info</span>
                <span>${this.escapeHtml(content)}</span>
            </div>
        `;
        message.style.cssText = `
            display: flex;
            justify-content: center;
            margin: 8px 0;
        `;
        message.querySelector('.system-message').style.cssText = `
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: var(--color-bg);
            border: 2px solid var(--border-color);
            font-size: 12px;
            color: var(--color-text-muted);
        `;
        this.messagesContainer.appendChild(message);
        this.scrollToBottom();
    },
    
    /**
     * Scroll chat to bottom
     */
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    },
    
    /**
     * Escape HTML entities
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};
