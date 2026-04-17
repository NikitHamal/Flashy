async function handleRouting() {
    const parts = window.location.pathname.split('/').filter(Boolean);

    if (parts.length === 0) {
        showDashboard();
        return;
    }

    if (Object.keys(globalData.workspaces).length === 0) {
        await refreshState(false);
    }

    const workspaceName = decodeURIComponent(parts[0]);
    const sessionId = parts[1];
    const workspace = Object.values(globalData.workspaces).find((entry) => entry.name === workspaceName);

    if (!workspace) {
        showDashboard();
        return;
    }

    if (sessionId) {
        const session = globalData.sessions.find((entry) => entry.id === sessionId);
        if (session) {
            loadSession(session, false);
        } else {
            openWorkspace(workspace.id, false, false);
        }
        return;
    }

    openWorkspace(workspace.id, false, false);
}
