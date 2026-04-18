window.ComputerUseUI = {
    els: {
        sessionList: document.getElementById('session-list'),
        feed: document.getElementById('feed'),
        taskInput: document.getElementById('task-input'),
        providerSelect: document.getElementById('provider-select'),
        modelSelect: document.getElementById('model-select'),
        btnSendTask: document.getElementById('btn-send-task'),
        btnInterrupt: document.getElementById('btn-interrupt'),
        btnNewSession: document.getElementById('btn-new-session'),
        sessionTitle: document.getElementById('session-title'),
        sessionStatusPill: document.getElementById('session-status-pill'),
    },

    formatDate(ts) {
        if (!ts) return '—';
        return new Date(ts * 1000).toLocaleString();
    },

    escape(text) {
        const div = document.createElement('div');
        div.textContent = text ?? '';
        return div.innerHTML;
    },

    setRunning(running) {
        ComputerUseState.running = running;
        this.els.btnInterrupt.classList.toggle('hidden', !running);
        const btn = this.els.btnSendTask;
        if (running) {
            btn.innerHTML = '<span class="material-symbols-outlined">hourglass_top</span>';
            btn.disabled = true;
        } else {
            btn.innerHTML = '<span class="material-symbols-outlined">arrow_upward</span>';
            btn.disabled = false;
        }
    },

    renderSessions() {
        const sessions = ComputerUseState.sessions || [];
        if (!sessions.length) {
            this.els.sessionList.innerHTML = '<div style="padding:16px; color:var(--text-secondary); font-size:13px; text-align:center;">No sessions yet</div>';
            return;
        }
        this.els.sessionList.innerHTML = sessions.map((session) => `
            <div class="cu-session-item ${session.id === ComputerUseState.sessionId ? 'active' : ''}" data-session-id="${session.id}">
                <div style="display:flex; align-items:start; justify-content:space-between; gap:4px;">
                    <div style="min-width:0; flex:1;">
                        <div class="cu-session-item-title">${this.escape(session.title)}</div>
                        <div class="cu-session-item-meta">
                            <span class="cu-status-pill ${session.status}">${this.escape(session.status)}</span>
                            <span>${new Date(session.updated_at * 1000).toLocaleDateString()}</span>
                        </div>
                        <div class="cu-session-item-prompt">${this.escape(session.last_prompt || session.last_summary || 'Ready')}</div>
                    </div>
                    <button class="cu-session-delete" data-delete-id="${session.id}" title="Delete session">
                        <span class="material-symbols-outlined">delete</span>
                    </button>
                </div>
            </div>
        `).join('');
    },

    renderSession() {
        const session = ComputerUseState.session;
        if (!session) {
            this.els.sessionTitle.textContent = 'Select or create a session';
            this.els.sessionStatusPill.className = 'cu-status-pill idle';
            this.els.sessionStatusPill.textContent = 'idle';
            this.els.feed.innerHTML = '<div class="cu-feed-empty">Create a session and send a task like "Open Notepad and type Hello World." The assistant will plan and execute actions on your desktop.</div>';
            return;
        }

        this.els.sessionTitle.textContent = session.title;
        this.els.sessionStatusPill.className = `cu-status-pill ${session.status}`;
        this.els.sessionStatusPill.textContent = session.status;

        const items = [
            ...(session.messages || []).map((msg) => ({
                ts: msg.timestamp,
                html: `
                <div class="cu-message ${msg.role}">
                    <div class="cu-message-meta"><span>${this.escape(msg.role)}</span><span>${this.formatDate(msg.timestamp)}</span></div>
                    <div class="cu-message-bubble"><div class="cu-message-content">${this.escape(msg.content)}</div></div>
                </div>`
            })),
            ...(session.events || []).map((evt) => ({
                ts: evt.timestamp,
                html: `
                <div class="cu-message event">
                    <div class="cu-event-card">
                        <div class="cu-event-meta"><span>${this.escape(evt.kind)}</span><span>${this.formatDate(evt.timestamp)}</span></div>
                        <div class="cu-event-title">${this.escape(evt.title)}</div>
                        ${evt.detail ? `<div class="cu-event-detail">${this.escape(evt.detail)}</div>` : ''}
                        ${evt.action_args ? `<div class="cu-event-json">${this.escape(JSON.stringify(evt.action_args, null, 2))}</div>` : ''}
                    </div>
                </div>`
            })),
        ];
        if (!items.length) {
            this.els.feed.innerHTML = '<div class="cu-feed-empty">This session is ready. Send a desktop task to start.</div>';
        } else {
            this.els.feed.innerHTML = items.sort((a, b) => a.ts - b.ts).map((item) => item.html).join('');
        }
        this.els.feed.scrollTop = this.els.feed.scrollHeight;
    },

    renderModels() {
        const models = ComputerUseState.models || [];
        const current = this.els.modelSelect.value || ComputerUseState.session?.model || models[0]?.id || '';
        if (!models.length) {
            this.els.modelSelect.innerHTML = '<option value="">No models found</option>';
            return;
        }
        this.els.modelSelect.innerHTML = models.map((model) => `
            <option value="${this.escape(model.id)}" ${model.id === current ? 'selected' : ''}>${this.escape(model.name)}${model.vision ? ' • vision' : ''}</option>
        `).join('');
        this.els.modelSelect.value = current || models[0].id;
    },
};