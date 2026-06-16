// Server Center UI
Object.assign(UI, {
    serverPollingTimer: null,
    serverLogPath: '',

    showServerCenter() {
        document.getElementById('home-dashboard')?.classList.add('hidden');
        document.getElementById('workspace-view')?.classList.add('hidden');
        document.getElementById('server-center')?.classList.remove('hidden');
        document.getElementById('btn-toggle-server')?.classList.add('active');
        this.refreshServerCenter();
        this.startServerPolling();
    },

    hideServerCenter() {
        document.getElementById('server-center')?.classList.add('hidden');
        document.getElementById('btn-toggle-server')?.classList.remove('active');
        this.stopServerPolling();
    },

    toggleServerCenter() {
        const center = document.getElementById('server-center');
        if (!center) return;
        if (center.classList.contains('hidden')) {
            this.showServerCenter();
        } else {
            this.hideServerCenter();
            const wsView = document.getElementById('workspace-view');
            const dashboard = document.getElementById('home-dashboard');
            if (wsView && !wsView.classList.contains('hidden')) {
                document.getElementById('chat-container')?.classList.remove('hidden');
            } else if (dashboard) {
                dashboard.classList.remove('hidden');
            }
        }
    },

    startServerPolling() {
        this.stopServerPolling();
        this.serverPollingTimer = setInterval(() => {
            const center = document.getElementById('server-center');
            if (center && !center.classList.contains('hidden')) {
                this.refreshServerCenter({ quiet: true });
            }
        }, 2500);
    },

    stopServerPolling() {
        if (this.serverPollingTimer) {
            clearInterval(this.serverPollingTimer);
            this.serverPollingTimer = null;
        }
    },

    async refreshServerCenter(options = {}) {
        try {
            const [status, logs, events, duckai] = await Promise.all([
                API.getServerStatus(),
                API.getServerLogs(240),
                API.getServerEvents(100),
                API.getDuckAIStatus().catch(() => null)
            ]);
            this.renderServerStatus(status);
            this.renderServerLogs(logs);
            this.renderServerEvents(events.events || []);
            if (duckai) this.renderDuckAIStatus(duckai);
        } catch (error) {
            if (!options.quiet) {
                alert(`Server Center refresh failed: ${error.message}`);
            }
            console.error(error);
        }
    },

    renderServerStatus(status) {
        const online = Boolean(status.running && status.health && status.health.ok);
        const pill = document.getElementById('server-state-pill');
        if (pill) {
            pill.classList.toggle('online', online);
            pill.classList.toggle('offline', !online);
            const label = pill.querySelector('span:last-child');
            if (label) label.textContent = online ? 'Online' : 'Offline';
        }
        const setText = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        };
        this.serverLogPath = status.log_path || '';
        setText('server-url', status.url || '—');
        setText('server-pid', status.pid ? String(status.pid) : (status.managed ? 'starting' : '—'));
        setText('server-health', online ? 'OK' : (status.health?.error || 'Not running'));
        setText('server-uptime', this.formatDuration(status.uptime_seconds));
        document.getElementById('btn-server-start')?.toggleAttribute('disabled', online);
        document.getElementById('btn-server-stop')?.toggleAttribute('disabled', !status.managed);
    },

    renderServerLogs(payload) {
        const output = document.getElementById('server-log-output');
        if (!output) return;
        this.serverLogPath = payload.path || this.serverLogPath || '';
        const lines = payload.lines || [];
        output.textContent = lines.length ? lines.join('\n') : 'No server log entries yet.';
        output.scrollTop = output.scrollHeight;
    },

    renderServerEvents(events) {
        const container = document.getElementById('server-events');
        if (!container) return;
        if (!events.length) {
            container.innerHTML = '<div class="server-empty">No provider requests yet.</div>';
            return;
        }
        const recent = events.slice(-32).reverse();
        container.innerHTML = recent.map((event) => {
            const status = Number(event.status || 0);
            const statusClass = status >= 500 ? 'error' : (status >= 200 && status < 400 ? 'ok' : '');
            const path = `${event.path || '/'}${event.query ? `?${event.query}` : ''}`;
            const time = event.duration_ms != null ? `${event.duration_ms} ms` : '—';
            return `
                <div class="server-event-row" title="${this.escapeHtml(event.error || path)}">
                    <span class="server-event-method">${this.escapeHtml(event.method || 'GET')}</span>
                    <span class="server-event-path">${this.escapeHtml(path)}</span>
                    <span class="server-event-status ${statusClass}">${status || '—'}</span>
                    <span class="server-event-duration">${this.escapeHtml(time)}</span>
                </div>`;
        }).join('');
    },

    formatDuration(seconds) {
        if (!seconds && seconds !== 0) return '—';
        const total = Math.max(0, Math.floor(seconds));
        const hours = Math.floor(total / 3600);
        const minutes = Math.floor((total % 3600) / 60);
        const secs = total % 60;
        if (hours) return `${hours}h ${minutes}m`;
        if (minutes) return `${minutes}m ${secs}s`;
        return `${secs}s`;
    },

    // DuckAI Control
    async refreshDuckAI(options = {}) {
        try {
            const status = await API.getDuckAIStatus();
            this.renderDuckAIStatus(status);
        } catch (error) {
            if (!options.quiet) console.error(error);
        }
    },

    renderDuckAIStatus(status) {
        const online = Boolean(status.running && status.health && status.health.ok);
        const pill = document.getElementById('duckai-state-pill');
        if (pill) {
            pill.classList.toggle('online', online);
            pill.classList.toggle('offline', !online);
            const label = pill.querySelector('span:last-child');
            if (label) label.textContent = online ? 'Online' : 'Offline';
        }
        const setText = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        };
        setText('duckai-url', status.url || '—');
        setText('duckai-pid', status.pid ? String(status.pid) : (status.managed ? 'starting' : '—'));
        setText('duckai-health', online ? 'OK' : (status.health?.error || 'Not running'));
        setText('duckai-uptime', this.formatDuration(status.uptime_seconds));
        document.getElementById('btn-duckai-start')?.toggleAttribute('disabled', online);
        document.getElementById('btn-duckai-stop')?.toggleAttribute('disabled', !status.managed);
    },

    async startDuckAI() {
        try {
            const status = await API.startDuckAI();
            this.renderDuckAIStatus(status);
        } catch (error) {
            alert(`Failed to start DuckAI: ${error.message}`);
        }
    },

    async stopDuckAI() {
        try {
            const status = await API.stopDuckAI();
            this.renderDuckAIStatus(status);
        } catch (error) {
            alert(`Failed to stop DuckAI: ${error.message}`);
        }
    },

    async restartDuckAI() {
        try {
            const status = await API.restartDuckAI();
            this.renderDuckAIStatus(status);
        } catch (error) {
            alert(`Failed to restart DuckAI: ${error.message}`);
        }
    }
});
