const API_BASE = "http://localhost:8000";

const API = {
    baseUrl: API_BASE,
    async sendMessage(text, sessionId, workspaceId, files = [], onChunk) {
        const formData = new FormData();
        formData.append('message', text);
        if (sessionId) formData.append('session_id', sessionId);
        if (workspaceId) formData.append('workspace_id', workspaceId);

        if (files && files.length > 0) {
            files.forEach(file => {
                formData.append('files', file);
            });
        }

        const response = await fetch(`${this.baseUrl}/chat`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to get response from Flashy");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (line.trim()) {
                    try {
                        const chunk = JSON.parse(line);
                        if (onChunk) onChunk(chunk);
                    } catch (e) {
                        console.error("Error parsing stream line:", e);
                    }
                }
            }
        }
    },

    async getConfig() {
        const response = await fetch(`${this.baseUrl}/config`);
        return await response.json();
    },

    async saveConfig(config) {
        const response = await fetch(`${this.baseUrl}/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        return await response.json();
    },

    async getHistory() {
        const response = await fetch(`${this.baseUrl}/history`);
        return await response.json();
    },

    async getChatHistory(sessionId) {
        const response = await fetch(`${this.baseUrl}/history/${sessionId}`);
        return await response.json();
    },

    async deleteChat(sessionId) {
        const response = await fetch(`${this.baseUrl}/history/${sessionId}`, {
            method: 'DELETE'
        });
        return await response.json();
    },

    async getWorkspace() {
        const response = await fetch(`${this.baseUrl}/workspace`);
        return await response.json();
    },

    async getWorkspaces() {
        const response = await fetch(`${this.baseUrl}/workspaces`);
        if (!response.ok) throw new Error('Failed to load workspaces');
        return response.json();
    },

    async deleteWorkspace(workspaceId) {
        const response = await fetch(`${this.baseUrl}/workspaces/${workspaceId}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to delete workspace');
        return response.json();
    },

    async getWorkspaceSessions(workspaceId) {
        const response = await fetch(`${this.baseUrl}/workspaces/${workspaceId}/sessions`);
        if (!response.ok) throw new Error('Failed to load sessions');
        return response.json();
    },

    async setWorkspace(path) {
        const response = await fetch(`${this.baseUrl}/workspaces`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: path })
        });
        if (!response.ok) throw new Error('Failed to set workspace');
        return response.json();
    },

    async pickWorkspace() {
        const response = await fetch(`${this.baseUrl}/workspace/pick`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to pick workspace');
        return response.json();
    },

    async pickPath() {
        const response = await fetch(`${this.baseUrl}/path/pick`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to pick path');
        return response.json();
    },

    async getExplorer(workspaceId) {
        const response = await fetch(`${this.baseUrl}/workspace/${workspaceId}/explorer`);
        if (!response.ok) throw new Error('Failed to load explorer');
        return await response.json();
    },

    async getPlan(workspaceId) {
        const response = await fetch(`${this.baseUrl}/workspace/${workspaceId}/plan`);
        if (!response.ok) throw new Error('Failed to load plan');
        return await response.json();
    },

    async getGitInfo(workspaceId) {
        const response = await fetch(`${this.baseUrl}/workspace/${workspaceId}/git`);
        if (!response.ok) throw new Error('Failed to load git info');
        return await response.json();
    },

    async interruptChat(sessionId) {
        const response = await fetch(`${this.baseUrl}/chat/interrupt`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        return await response.json();
    },

    async cloneRepo(url, parentPath, name = null) {
        const response = await fetch(`${this.baseUrl}/git/clone`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, parent_path: parentPath, name })
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Clone failed");
        }
        return await response.json();
    }
};
