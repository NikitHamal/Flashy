(function () {
    const state = window.ComputerUseState;
    const api = window.ComputerUseAPI;
    const ui = window.ComputerUseUI;

    function currentPathSessionId() {
        const parts = window.location.pathname.split('/').filter(Boolean);
        return parts[0] === 'computer-use' && parts[1] ? decodeURIComponent(parts[1]) : null;
    }

    function pushSessionRoute(sessionId) {
        const target = `/computer-use/${encodeURIComponent(sessionId)}`;
        if (window.location.pathname !== target) {
            history.pushState({ sessionId }, '', target);
        }
    }

    async function refreshSessions() {
        state.sessions = await api.listSessions();
        ui.renderSessions();
    }

    async function refreshModels(provider = state.session?.provider || ui.els.providerSelect.value || 'airforce') {
        state.models = await api.getModels(provider);
        ui.els.providerSelect.value = provider;
        ui.renderModels();
    }

    async function persistPreferences() {
        try {
            await api.saveComputerUsePreferences(ui.els.providerSelect.value, ui.els.modelSelect.value);
        } catch (error) {
            console.warn('Failed to persist computer-use preferences', error);
        }
    }

    function attachSocket(sessionId) {
        if (state.socket) {
            state.socket.close();
            state.socket = null;
        }
        state.socket = api.connectWebSocket(sessionId, {
            session_snapshot(payload) {
                state.session = payload.session;
                state.sessionId = payload.session.id;
                ui.renderSession();
                refreshSessions().catch(console.error);
            },
            preview() {
            },
            event() {
                refreshSessionData(sessionId).catch(console.error);
            },
            assistant(payload) {
                if (payload?.content) console.log('assistant', payload.content);
                refreshSessionData(sessionId).catch(console.error);
            },
            assistant_thought(payload) {
                console.debug('assistant_thought', payload.content);
            },
            run_state(payload) {
                ui.setRunning(Boolean(payload.running));
            },
            error(payload) {
                ui.setRunning(false);
                alert(payload.message || 'Computer Use error');
            },
            closed() {
                ui.setRunning(false);
            },
        });
    }

    async function refreshSessionData(sessionId) {
        state.session = await api.getSession(sessionId);
        state.sessionId = state.session.id;
        ui.renderSession();
        ui.renderSessions();
        if (state.session.provider) {
            ui.els.providerSelect.value = state.session.provider;
        }
        if (!state.models.length || state.models[0]?.provider !== (state.session.provider || ui.els.providerSelect.value)) {
            await refreshModels(state.session.provider || ui.els.providerSelect.value);
        } else {
            ui.renderModels();
        }
    }

    async function selectSession(sessionId) {
        await refreshSessionData(sessionId);
        attachSocket(sessionId);
    }

    async function createSession() {
        const session = await api.createSession({ provider: ui.els.providerSelect.value || 'airforce', model: ui.els.modelSelect.value || '' });
        await refreshSessions();
        await selectSession(session.id);
        pushSessionRoute(session.id);
    }

    async function ensureSession() {
        if (state.sessionId) return state.sessionId;
        const session = await api.createSession({ provider: ui.els.providerSelect.value || 'airforce', model: ui.els.modelSelect.value || '' });
        await refreshSessions();
        await selectSession(session.id);
        pushSessionRoute(session.id);
        return session.id;
    }

    async function sendTask() {
        const prompt = ui.els.taskInput.value.trim();
        if (!prompt) return;
        const sessionId = await ensureSession();
        if (!state.socket || state.socket.readyState !== WebSocket.OPEN) {
            attachSocket(sessionId);
            await new Promise((resolve) => setTimeout(resolve, 300));
        }
        state.socket.send(JSON.stringify({
            type: 'start_task',
            payload: {
                prompt,
                provider: ui.els.providerSelect.value,
                model: ui.els.modelSelect.value,
            },
        }));
        ui.els.taskInput.value = '';
        ui.els.taskInput.style.height = 'auto';
        ui.setRunning(true);
    }

    async function initialize() {
        ui.els.taskInput.addEventListener('input', () => {
            ui.els.taskInput.style.height = 'auto';
            ui.els.taskInput.style.height = `${ui.els.taskInput.scrollHeight}px`;
        });
        ui.els.taskInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendTask().catch(console.error);
            }
        });
        ui.els.btnSendTask.addEventListener('click', () => sendTask().catch(console.error));
        ui.els.btnNewSession.addEventListener('click', () => createSession().catch(console.error));
        ui.els.btnInterrupt.addEventListener('click', () => {
            if (state.socket && state.socket.readyState === WebSocket.OPEN) {
                state.socket.send(JSON.stringify({ type: 'interrupt', payload: {} }));
            }
        });
        ui.els.providerSelect.addEventListener('change', async () => { await refreshModels(ui.els.providerSelect.value).catch(console.error); await persistPreferences(); });
        ui.els.modelSelect.addEventListener('change', async () => { await persistPreferences(); });
        ui.els.sessionList.addEventListener('click', (event) => {
            const deleteBtn = event.target.closest('[data-delete-id]');
            if (deleteBtn) {
                event.stopPropagation();
                const deleteId = deleteBtn.getAttribute('data-delete-id');
                if (confirm('Delete this session?')) {
                    api.deleteSession(deleteId).then(() => {
                        if (state.sessionId === deleteId) {
                            state.session = null;
                            state.sessionId = null;
                            ui.renderSession();
                            history.pushState({}, '', '/computer-use');
                        }
                        refreshSessions();
                    }).catch(console.error);
                }
                return;
            }
            const card = event.target.closest('[data-session-id]');
            if (!card) return;
            const sessionId = card.getAttribute('data-session-id');
            selectSession(sessionId).then(() => pushSessionRoute(sessionId)).catch(console.error);
        });

        await refreshSessions();
        const config = await api.getConfig().catch(() => ({ computer_use_provider: 'airforce', computer_use_model: '' }));
        await refreshModels(config.computer_use_provider || 'airforce');
        if (config.computer_use_model) {
            ui.els.modelSelect.value = config.computer_use_model;
        }
        const fromRoute = currentPathSessionId();
        if (fromRoute) {
            await selectSession(fromRoute);
        } else if (state.sessions.length) {
            await selectSession(state.sessions[0].id);
            pushSessionRoute(state.sessions[0].id);
        } else {
            ui.renderSession();
        }
    }

    window.addEventListener('popstate', () => {
        const sessionId = currentPathSessionId();
        if (sessionId) selectSession(sessionId).catch(console.error);
    });

    document.addEventListener('DOMContentLoaded', () => initialize().catch(console.error));
})();