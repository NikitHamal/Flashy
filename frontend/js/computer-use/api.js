window.ComputerUseAPI = {
    baseUrl: window.location.origin,

    async listSessions() {
        const response = await fetch(`${this.baseUrl}/api/computer-use/sessions`);
        if (!response.ok) throw new Error('Failed to load computer-use sessions');
        return response.json();
    },

    async createSession(payload = {}) {
        const response = await fetch(`${this.baseUrl}/api/computer-use/sessions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (!response.ok) throw new Error('Failed to create session');
        return response.json();
    },

    async getSession(sessionId) {
        const response = await fetch(`${this.baseUrl}/api/computer-use/sessions/${encodeURIComponent(sessionId)}`);
        if (!response.ok) throw new Error('Failed to load session');
        return response.json();
    },

    async deleteSession(sessionId) {
        const response = await fetch(`${this.baseUrl}/api/computer-use/sessions/${encodeURIComponent(sessionId)}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Failed to delete session');
        return response.json();
    },


    async getConfig() {
        const response = await fetch(`${this.baseUrl}/config`);
        if (!response.ok) throw new Error('Failed to load config');
        return response.json();
    },

    async saveComputerUsePreferences(provider, model) {
        const response = await fetch(`${this.baseUrl}/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ computer_use_provider: provider, computer_use_model: model }),
        });
        if (!response.ok) throw new Error('Failed to save computer-use preferences');
        return response.json();
    },

    async getModels(provider) {
        const query = provider ? `?provider=${encodeURIComponent(provider)}` : '';
        const response = await fetch(`${this.baseUrl}/api/computer-use/models${query}`);
        if (!response.ok) throw new Error('Failed to load models');
        return response.json();
    },

    connectWebSocket(sessionId, handlers = {}) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const ws = new WebSocket(`${protocol}//${window.location.host}/api/computer-use/ws/${encodeURIComponent(sessionId)}`);
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                const handler = handlers[data.type];
                if (handler) handler(data.payload || {});
            } catch (error) {
                console.error('Computer Use WS parse error', error);
            }
        };
        ws.onclose = () => handlers.closed && handlers.closed();
        ws.onerror = (error) => handlers.error && handlers.error(error);
        return ws;
    },
};
