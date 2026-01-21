/**
 * ============================================================================
 * Astro Chat Module
 * ============================================================================
 *
 * Manages the Jyotishi AI chat interface with streaming responses,
 * markdown rendering, and tool call visualization.
 *
 * @module astro/ui/chat
 */

import AstroAPI from './api.js';
import AstroStorage from './storage.js';

class AstroChat {
    constructor() {
        this.elements = {};
        this.isProcessing = false;
        this.currentMessageEl = null;
        this.messageBuffer = '';

        // Callbacks for external integration
        this.onKundaliUpdate = null;
        this.onActiveKundaliUpdate = null;
    }

    /**
     * Initialize chat module
     */
    init() {
        this._cacheElements();
        this._setupEventListeners();
        this._setupMarkdown();
        console.log('[AstroChat] Initialized');
    }

    /**
     * Cache DOM elements
     */
    _cacheElements() {
        this.elements = {
            chatHistory: document.getElementById('jyotishi-chat-history'),
            chatInput: document.getElementById('jyotishi-input'),
            sendBtn: document.getElementById('btn-send-message'),
            clearBtn: document.getElementById('btn-clear-chat'),
            voiceBtn: document.getElementById('btn-voice-input'),
            interruptBtn: document.getElementById('btn-interrupt'),
            thinkingIndicator: document.getElementById('thinking-indicator'),
            statusIndicator: document.getElementById('jyotishi-indicator'),
            statusText: document.getElementById('jyotishi-status-text'),
            suggestionChips: document.querySelectorAll('.suggestion-chip')
        };
    }

    /**
     * Setup event listeners
     */
    _setupEventListeners() {
        // Send button
        this.elements.sendBtn?.addEventListener('click', () => this.sendMessage());

        // Input field - Enter to send, Shift+Enter for newline
        this.elements.chatInput?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize input and enable/disable send button
        this.elements.chatInput?.addEventListener('input', () => {
            this._autoResizeInput();
            this._updateSendButton();
        });

        // Clear chat
        this.elements.clearBtn?.addEventListener('click', () => this.clearChat());

        // Interrupt
        this.elements.interruptBtn?.addEventListener('click', () => this.interrupt());

        // Suggestion chips
        this.elements.suggestionChips?.forEach(chip => {
            chip.addEventListener('click', () => {
                const prompt = chip.dataset.prompt;
                if (prompt) {
                    this.elements.chatInput.value = prompt;
                    this._autoResizeInput();
                    this._updateSendButton();
                    this.elements.chatInput.focus();

                    // If it's a simple command, send immediately
                    if (!prompt.endsWith('on') && !prompt.includes('...')) {
                        this.sendMessage();
                    }
                }
            });
        });
    }

    /**
     * Setup markdown renderer
     */
    _setupMarkdown() {
        if (typeof marked !== 'undefined') {
            marked.setOptions({
                breaks: true,
                gfm: true,
                headerIds: false,
                mangle: false
            });
        }
    }

    /**
     * Send a message to the Jyotishi AI
     */
    async sendMessage() {
        const message = this.elements.chatInput?.value?.trim();
        if (!message || this.isProcessing) return;

        // Clear input
        this.elements.chatInput.value = '';
        this._autoResizeInput();
        this._updateSendButton();

        // Add user message to chat
        this._addUserMessage(message);

        // Hide welcome if visible
        this._hideWelcome();

        // Start processing
        this._setProcessing(true);

        // Get current kundalis and active ID
        const kundalis = AstroStorage.getKundalis();
        const activeId = AstroStorage.getActiveKundaliId();

        // Prepare assistant message container
        this._prepareAssistantMessage();

        try {
            await AstroAPI.streamConsultation(message, kundalis, activeId, {
                onThought: (thought) => this._handleThought(thought),
                onText: (text) => this._handleText(text),
                onToolCall: (toolCall) => this._handleToolCall(toolCall),
                onToolResult: (result) => this._handleToolResult(result),
                onKundaliUpdate: (kundalis) => this._handleKundaliUpdate(kundalis),
                onActiveKundaliUpdate: (active) => this._handleActiveKundaliUpdate(active),
                onError: (error) => this._handleError(error),
                onComplete: (data) => this._handleComplete(data)
            });
        } catch (error) {
            if (error.name !== 'AbortError') {
                this._handleError(error.message);
            }
        }
    }

    /**
     * Interrupt current AI generation
     */
    async interrupt() {
        if (!this.isProcessing) return;

        await AstroAPI.interrupt();
        this._finishAssistantMessage();
        this._setProcessing(false);
    }

    /**
     * Clear chat history
     */
    clearChat() {
        if (!this.elements.chatHistory) return;

        // Keep the welcome message, remove everything else
        const welcome = this.elements.chatHistory.querySelector('.chat-welcome');
        this.elements.chatHistory.innerHTML = '';

        if (welcome) {
            this.elements.chatHistory.appendChild(welcome);
            welcome.style.display = '';
        }

        // Reset API session
        AstroAPI.resetSession();
    }

    /**
     * Add a user message to the chat
     */
    _addUserMessage(text) {
        const messageEl = document.createElement('div');
        messageEl.className = 'chat-message user';
        messageEl.innerHTML = `<div class="message-content">${this._escapeHtml(text)}</div>`;

        this.elements.chatHistory?.appendChild(messageEl);
        this._scrollToBottom();
    }

    /**
     * Prepare container for assistant message
     */
    _prepareAssistantMessage() {
        this.messageBuffer = '';

        const messageEl = document.createElement('div');
        messageEl.className = 'chat-message assistant';
        messageEl.innerHTML = '<div class="message-content"></div>';

        this.currentMessageEl = messageEl;
        this.elements.chatHistory?.appendChild(messageEl);
        this._scrollToBottom();
    }

    /**
     * Handle incoming text chunk
     */
    _handleText(text) {
        this.messageBuffer += text;
        this._updateAssistantMessage();
    }

    /**
     * Handle thought/reasoning from AI
     */
    _handleThought(thought) {
        // Only show thoughts if setting enabled
        const settings = AstroStorage.getSettings();
        if (!settings.thinkingVisible) return;

        // Add thought in a collapsible section
        const thoughtEl = document.createElement('div');
        thoughtEl.className = 'chat-thought';
        thoughtEl.innerHTML = `
            <details>
                <summary><span class="material-symbols-outlined">psychology</span> AI Reasoning</summary>
                <pre>${this._escapeHtml(thought)}</pre>
            </details>
        `;

        if (this.currentMessageEl) {
            this.currentMessageEl.insertBefore(thoughtEl, this.currentMessageEl.firstChild);
        }
    }

    /**
     * Handle tool call notification
     */
    _handleToolCall(toolCall) {
        const toolEl = document.createElement('div');
        toolEl.className = 'chat-tool-call';
        toolEl.innerHTML = `
            <div class="tool-indicator">
                <span class="material-symbols-outlined">build</span>
                <span class="tool-name">${this._formatToolName(toolCall.name)}</span>
                <span class="tool-status">Running...</span>
            </div>
        `;

        if (this.currentMessageEl) {
            const content = this.currentMessageEl.querySelector('.message-content');
            content?.appendChild(toolEl);
            this._scrollToBottom();
        }
    }

    /**
     * Handle tool result
     */
    _handleToolResult(result) {
        // Update the last tool call indicator to show completion
        if (this.currentMessageEl) {
            const lastToolCall = this.currentMessageEl.querySelector('.chat-tool-call:last-child');
            if (lastToolCall) {
                const status = lastToolCall.querySelector('.tool-status');
                if (status) {
                    status.textContent = 'Complete';
                    status.classList.add('complete');
                }
            }
        }
    }

    /**
     * Handle kundali list update
     */
    _handleKundaliUpdate(kundalis) {
        // Update localStorage
        AstroStorage.saveKundalis(kundalis);

        // Notify external handler
        if (this.onKundaliUpdate) {
            this.onKundaliUpdate(kundalis);
        }
    }

    /**
     * Handle active kundali update
     */
    _handleActiveKundaliUpdate(active) {
        if (active?.id) {
            AstroStorage.setActiveKundaliId(active.id);
        }

        // Notify external handler
        if (this.onActiveKundaliUpdate) {
            this.onActiveKundaliUpdate(active);
        }
    }

    /**
     * Handle error
     */
    _handleError(error) {
        const errorEl = document.createElement('div');
        errorEl.className = 'chat-error';
        errorEl.innerHTML = `
            <span class="material-symbols-outlined">error</span>
            <span>${this._escapeHtml(error)}</span>
        `;

        if (this.currentMessageEl) {
            const content = this.currentMessageEl.querySelector('.message-content');
            content?.appendChild(errorEl);
        }

        this._setProcessing(false);
    }

    /**
     * Handle completion
     */
    _handleComplete(data) {
        this._finishAssistantMessage();
        this._setProcessing(false);

        // Final updates if provided
        if (data.kundalis) {
            this._handleKundaliUpdate(data.kundalis);
        }
        if (data.active_kundali) {
            this._handleActiveKundaliUpdate(data.active_kundali);
        }
    }

    /**
     * Update assistant message content with buffered text
     */
    _updateAssistantMessage() {
        if (!this.currentMessageEl) return;

        const content = this.currentMessageEl.querySelector('.message-content');
        if (!content) return;

        // Get text content (excluding tool calls)
        const toolCalls = content.querySelectorAll('.chat-tool-call, .chat-error');
        const toolCallsHtml = Array.from(toolCalls).map(el => el.outerHTML).join('');

        // Render markdown
        const renderedContent = this._renderMarkdown(this.messageBuffer);

        // Rebuild content: rendered markdown + tool calls
        content.innerHTML = renderedContent + toolCallsHtml;

        this._scrollToBottom();
    }

    /**
     * Finish assistant message rendering
     */
    _finishAssistantMessage() {
        if (this.messageBuffer && this.currentMessageEl) {
            this._updateAssistantMessage();
        }

        // Apply syntax highlighting
        if (this.currentMessageEl && typeof hljs !== 'undefined') {
            this.currentMessageEl.querySelectorAll('pre code').forEach(block => {
                hljs.highlightElement(block);
            });
        }

        this.currentMessageEl = null;
        this.messageBuffer = '';
    }

    /**
     * Render markdown to HTML
     */
    _renderMarkdown(text) {
        if (typeof marked !== 'undefined') {
            return marked.parse(text);
        }
        // Fallback: basic text with line breaks
        return `<p>${this._escapeHtml(text).replace(/\n/g, '<br>')}</p>`;
    }

    /**
     * Set processing state
     */
    _setProcessing(processing) {
        this.isProcessing = processing;

        // Update UI elements
        if (this.elements.sendBtn) {
            this.elements.sendBtn.disabled = processing;
        }

        if (this.elements.chatInput) {
            this.elements.chatInput.disabled = processing;
        }

        // Show/hide interrupt button
        if (this.elements.interruptBtn) {
            this.elements.interruptBtn.classList.toggle('hidden', !processing);
        }

        // Show/hide thinking indicator
        if (this.elements.thinkingIndicator) {
            this.elements.thinkingIndicator.classList.toggle('hidden', !processing);
        }

        // Update status
        this._updateStatus(processing ? 'working' : 'idle');
    }

    /**
     * Update status indicator
     */
    _updateStatus(state) {
        if (this.elements.statusIndicator) {
            this.elements.statusIndicator.className = `status-indicator ${state}`;
        }

        if (this.elements.statusText) {
            const texts = {
                idle: 'Ready to consult',
                working: 'Consulting the stars...'
            };
            this.elements.statusText.textContent = texts[state] || 'Ready';
        }
    }

    /**
     * Auto-resize textarea input
     */
    _autoResizeInput() {
        const input = this.elements.chatInput;
        if (!input) return;

        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 120) + 'px';
    }

    /**
     * Update send button state
     */
    _updateSendButton() {
        const hasText = this.elements.chatInput?.value?.trim();
        if (this.elements.sendBtn) {
            this.elements.sendBtn.disabled = !hasText || this.isProcessing;
        }
    }

    /**
     * Hide welcome message
     */
    _hideWelcome() {
        const welcome = this.elements.chatHistory?.querySelector('.chat-welcome');
        if (welcome) {
            welcome.style.display = 'none';
        }
    }

    /**
     * Scroll chat to bottom
     */
    _scrollToBottom() {
        if (this.elements.chatHistory) {
            this.elements.chatHistory.scrollTop = this.elements.chatHistory.scrollHeight;
        }
    }

    /**
     * Format tool name for display
     */
    _formatToolName(name) {
        return name
            .replace(/_/g, ' ')
            .replace(/\b\w/g, c => c.toUpperCase());
    }

    /**
     * Escape HTML special characters
     */
    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Send a message programmatically (for external use)
     */
    sendPrompt(prompt) {
        if (this.elements.chatInput) {
            this.elements.chatInput.value = prompt;
            this.sendMessage();
        }
    }
}

// Export singleton instance
export default new AstroChat();
