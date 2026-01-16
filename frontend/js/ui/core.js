const UI = {
    elements: {
        sidebar: document.querySelector('.sidebar'),
        mainContent: document.querySelector('.main-content'),
        toggleSidebarBtn: document.getElementById('toggle-sidebar'),
        homeDashboard: document.getElementById('home-dashboard'),
        workspaceView: document.getElementById('workspace-view'),
        chatHistory: document.getElementById('chat-history'),
        chatHistoryWrapper: document.querySelector('.messages-wrapper'),
        chatInput: document.getElementById('message-input'),
        sendBtn: document.getElementById('btn-send'),
        fileInput: document.getElementById('file-input'),
        attachBtn: document.getElementById('btn-attach'),
        mentionPopup: document.getElementById('mention-popup'),
        taggedFilesContainer: document.getElementById('tagged-files-container'),
        uploadPreviewsContainer: document.getElementById('upload-previews-container'),

        // Terminal elements
        terminalContainer: document.getElementById('terminal-container'),
        terminalOutput: document.getElementById('terminal-output'),
        terminalToggle: document.getElementById('btn-toggle-terminal'),
        terminalToggleContainer: document.getElementById('terminal-toggle-container'),
        terminalBadge: document.getElementById('terminal-badge'),
        terminalStatus: document.getElementById('terminal-status'),
        terminalClose: document.getElementById('btn-close-terminal'),
        terminalClear: document.getElementById('btn-clear-terminal'),
    },

    isWorking: false,
    taggedFiles: [], // Array of { name, path }
    uploadedFiles: [], // Array of File objects

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    showLoading() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message ai loading';
        loadingDiv.id = 'ai-loading';
        loadingDiv.innerHTML = `<div class="message-bubble"><div class="loading-dots"><span></span><span></span><span></span></div></div>`;
        this.elements.chatHistoryWrapper.appendChild(loadingDiv);
        this.scrollToBottom();
    },

    hideLoading() {
        const loadingDiv = document.getElementById('ai-loading');
        if (loadingDiv) loadingDiv.remove();
    },

    scrollToBottom() {
        if (this.elements.chatHistory) {
            this.elements.chatHistory.scrollTop = this.elements.chatHistory.scrollHeight;
        }
    },

    setAgentState(state) {
        const sendBtn = this.elements.sendBtn;
        const chatInput = this.elements.chatInput;
        if (!sendBtn) return;

        if (state === 'working') {
            sendBtn.classList.add('btn-stop');
            sendBtn.innerHTML = '<span class="material-symbols-outlined">stop_circle</span>';
            sendBtn.title = 'Stop Agent';
            if (chatInput) chatInput.placeholder = 'Agent is working...';
        } else {
            sendBtn.classList.remove('btn-stop');
            sendBtn.innerHTML = '<span class="material-symbols-outlined">arrow_upward</span>';
            sendBtn.title = 'Send Message';
            if (chatInput) chatInput.placeholder = "Ask anything... 'Find and fix security vulnerabilities'";
        }
        this.isWorking = (state === 'working');
    }
};
