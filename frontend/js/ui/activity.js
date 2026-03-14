window.ActivityUI = {
    init() {
        this.container = document.getElementById('agent-activity-panel');
        if (!this.container) return; // Must be added to HTML first

        this.content = document.getElementById('agent-activity-content');
        this.toggleBtn = document.getElementById('btn-toggle-activity');

        if (this.toggleBtn) {
            this.toggleBtn.addEventListener('click', () => {
                this.container.classList.toggle('hidden');
                if (!this.container.classList.contains('hidden')) {
                    this.loadActivity();
                    this.startPolling();
                } else {
                    this.stopPolling();
                }
            });
        }
    },

    pollInterval: null,

    startPolling() {
        this.stopPolling();
        this.pollInterval = setInterval(() => this.loadActivity(), 3000);
    },

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    },

    async loadActivity() {
        try {
            const status = await API.getAgentStatus(); // Method to be added to API
            this.render(status);
        } catch (e) {
            console.error('Failed to load activity:', e);
        }
    },

    render(agents) {
        if (!agents || agents.length === 0) {
            this.content.innerHTML = '<div class="activity-empty">No active agents</div>';
            return;
        }

        const html = agents.map(agent => `
            <div class="agent-card">
                <div class="agent-header">
                    <span class="agent-type">${agent.type}</span>
                    <span class="agent-provider">${agent.provider}</span>
                </div>
                <div class="agent-details">
                    <span class="agent-model">${agent.model}</span>
                    <span class="agent-tasks">Tasks: ${agent.task_count}</span>
                </div>
            </div>
        `).join('');

        this.content.innerHTML = html;
    }
};
