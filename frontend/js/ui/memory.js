window.MemoryUI = {
    isOpen: false,
    workspaceId: null,

    init(workspaceId) {
        this.workspaceId = workspaceId;

        // Cache DOM elements
        this.sidebar = document.getElementById('memory-sidebar');
        this.toggleBtn = document.getElementById('btn-toggle-memory');
        this.content = document.getElementById('memory-content');
        this.searchInput = document.getElementById('memory-search-input');
        this.addBtn = document.getElementById('btn-add-memory');
        this.refreshBtn = document.getElementById('btn-refresh-memory');

        // Event Listeners
        if (this.toggleBtn) {
            this.toggleBtn.addEventListener('click', () => this.toggle());
        }

        if (this.refreshBtn) {
            this.refreshBtn.addEventListener('click', () => this.loadMemories());
        }

        if (this.searchInput) {
            // Local debounce implementation
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

    toggle() {
        if (!this.sidebar) return;

        this.isOpen = !this.isOpen;
        if (this.isOpen) {
            this.sidebar.classList.remove('hidden');
            this.toggleBtn.classList.add('active');

            // Close other sidebars if needed (implement logic if exclusive)
            document.getElementById('git-sidebar')?.classList.add('hidden');
            document.getElementById('plan-sidebar')?.classList.add('hidden');
            document.getElementById('btn-toggle-git')?.classList.remove('active');
            document.getElementById('btn-toggle-plan')?.classList.remove('active');

            if (this.workspaceId) {
                this.loadMemories();
            }
        } else {
            this.sidebar.classList.add('hidden');
            this.toggleBtn.classList.remove('active');
        }
    },

    async loadMemories() {
        if (!this.workspaceId) return;

        try {
            this.content.innerHTML = '<div class="memory-loading"><span class="material-symbols-outlined spin">refresh</span> Loading memories...</div>';

            const data = await API.getMemories(this.workspaceId);
            this.renderMemories(data.memories || []);
        } catch (error) {
            console.error('Failed to load memories:', error);
            this.content.innerHTML = `<div class="memory-error">Failed to load memories: ${error.message}</div>`;
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
        if (!memories || memories.length === 0) {
            this.content.innerHTML = '<div class="memory-empty">No project memories found. The Learner agent will auto-save important details here.</div>';
            return;
        }

        // Sort by timestamp desc
        memories.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

        const html = memories.map(mem => this.createMemoryCard(mem)).join('');
        this.content.innerHTML = html;

        // Add delete listeners
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
                    <span class="memory-category tag">${memory.category}</span>
                    <span class="memory-date">${date}</span>
                    <button class="btn-icon-xs btn-delete-memory" data-id="${memory.id}" title="Delete">
                        <span class="material-symbols-outlined" style="font-size: 14px;">close</span>
                    </button>
                </div>
                <div class="memory-title">${memory.title}</div>
                <div class="memory-body">${marked.parse(memory.content || '')}</div>
            </div>
        `;
    },

    async deleteMemory(id) {
        if (!confirm('Are you sure you want to delete this memory?')) return;

        try {
            await API.deleteMemory(this.workspaceId, id);
            this.loadMemories(); // Refresh
        } catch (error) {
            alert('Failed to delete memory: ' + error.message);
        }
    },

    showAddModal() {
        // Simple prompt for now, could be a nicer modal later
        const category = prompt("Category (architecture, pattern, decision, etc):", "decision");
        if (!category) return;

        const title = prompt("Title:");
        if (!title) return;

        const content = prompt("Content:");
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
