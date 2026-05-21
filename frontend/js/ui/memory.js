window.MemoryUI = {
    isOpen: false,
    workspaceId: null,
    initialized: false,

    init(workspaceId) {
        this.workspaceId = workspaceId;

        this.sidebar = document.getElementById('memory-sidebar');
        this.toggleBtn = document.getElementById('btn-toggle-memory');
        this.content = document.getElementById('memory-content');
        this.searchInput = document.getElementById('memory-search-input');
        this.addBtn = document.getElementById('btn-add-memory');
        this.refreshBtn = document.getElementById('btn-refresh-memory');

        if (this.initialized) return;
        this.initialized = true;

        if (this.toggleBtn) {
            this.toggleBtn.addEventListener('click', () => this.toggle());
        }

        if (this.refreshBtn) {
            this.refreshBtn.addEventListener('click', () => this.loadMemories());
        }

        if (this.searchInput) {
            let timeout;
            this.searchInput.addEventListener('input', (e) => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    this.searchMemories(e.target.value);
                }, 300);
            });
        }

        if (this.addBtn) {
            this.addBtn.addEventListener('click', () => this.showAddModal());
        }
    },

    toggle(force) {
        if (!this.sidebar) return;

        const nextState = typeof force === 'boolean' ? force : !this.isOpen;
        this.isOpen = nextState;
        if (this.isOpen) {
            this.sidebar.classList.remove('hidden');
            this.toggleBtn?.classList.add('active');
            UI.hideServerCenter?.();
            UI.hideExplorer?.();
            UI.hideGit?.();
            UI.hidePlan?.();
            document.getElementById('chat-container')?.classList.remove('hidden');
            document.getElementById('workspace-dashboard')?.classList.add('hidden');

            if (this.workspaceId) {
                this.loadMemories();
            }
        } else {
            this.sidebar.classList.add('hidden');
            this.toggleBtn?.classList.remove('active');
        }
    },

    async loadMemories() {
        if (!this.workspaceId || !this.content) return;

        try {
            this.content.innerHTML = '<div class="memory-loading"><span class="material-symbols-outlined spin">refresh</span> Loading memories...</div>';

            const data = await API.getMemories(this.workspaceId);
            this.renderMemories(data.memories || []);
        } catch (error) {
            console.error('Failed to load memories:', error);
            this.content.innerHTML = `<div class="memory-error">Failed to load memories: ${UI.escapeHtml(error.message)}</div>`;
        }
    },

    async searchMemories(query) {
        if (!query.trim()) {
            return this.loadMemories();
        }

        try {
            this.content.innerHTML = '<div class="memory-loading">Searching...</div>';
            const data = await API.searchMemories(this.workspaceId, query);
            this.renderMemories(data.memories || []);
        } catch (error) {
            console.error('Search failed:', error);
        }
    },

    renderMemories(memories) {
        if (!this.content) return;
        if (!memories || memories.length === 0) {
            this.content.innerHTML = '<div class="memory-empty">No project memories found. The Learner agent will auto-save important details here.</div>';
            return;
        }

        memories.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        this.content.innerHTML = memories.map(mem => this.createMemoryCard(mem)).join('');

        this.content.querySelectorAll('.btn-delete-memory').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                this.deleteMemory(id);
            });
        });
    },

    createMemoryCard(memory) {
        const date = new Date(memory.timestamp).toLocaleDateString();
        const importanceClass = memory.importance >= 4 ? 'high' : (memory.importance <= 2 ? 'low' : 'medium');

        return `
            <div class="memory-card importance-${importanceClass}">
                <div class="memory-header">
                    <span class="memory-category tag">${UI.escapeHtml(memory.category || 'memory')}</span>
                    <span class="memory-date">${UI.escapeHtml(date)}</span>
                    <button class="btn-icon-xs btn-delete-memory" data-id="${UI.escapeHtml(memory.id)}" title="Delete">
                        <span class="material-symbols-outlined" style="font-size: 14px;">close</span>
                    </button>
                </div>
                <div class="memory-title">${UI.escapeHtml(memory.title || 'Untitled')}</div>
                <div class="memory-body">${marked.parse(memory.content || '')}</div>
            </div>
        `;
    },

    async deleteMemory(id) {
        if (!confirm('Are you sure you want to delete this memory?')) return;

        try {
            await API.deleteMemory(this.workspaceId, id);
            this.loadMemories();
        } catch (error) {
            alert('Failed to delete memory: ' + error.message);
        }
    },

    showAddModal() {
        const category = prompt('Category (architecture, pattern, decision, etc):', 'decision');
        if (!category) return;

        const title = prompt('Title:');
        if (!title) return;

        const content = prompt('Content:');
        if (!content) return;

        this.addMemory(category, title, content);
    },

    async addMemory(category, title, content) {
        try {
            await API.createMemory(this.workspaceId, category, title, content);
            this.loadMemories();
        } catch (error) {
            alert('Failed to create memory: ' + error.message);
        }
    }
};
