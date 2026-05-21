async function refreshState(updateUI = true) {
    try {
        const [workspaces, history] = await Promise.all([
            API.getWorkspaces(),
            API.getHistory()
        ]);
        globalData.workspaces = workspaces;
        globalData.sessions = history;

        if (updateUI) {
            renderSidebarWorkspaces(workspaces);
            renderRecentProjects(workspaces);
            UI.renderSidebarSessions(workspaces, history, currentSessionId, loadSession, deleteSession);
            if (currentWorkspaceId) {
                const workspaceSessions = history.filter((session) => session.workspace_id === currentWorkspaceId);
                UI.renderSessionDropdown(currentWorkspaceId, workspaceSessions, currentSessionId, loadSession, createNewSession);
            }
        }
    } catch (error) {
        console.error('Failed to refresh state', error);
    }
}

function showDashboard() {
    currentWorkspaceId = null;
    currentSessionId = null;
    UI.hideServerCenter?.();
    stopWorkspaceRealtime();
    document.getElementById('home-dashboard').classList.remove('hidden');
    document.getElementById('workspace-view').classList.add('hidden');

    const explorerToggle = document.getElementById('btn-toggle-explorer');
    if (explorerToggle) {
        explorerToggle.classList.add('hidden');
    }

    if (window.location.pathname !== '/') {
        history.pushState({ type: 'dashboard' }, '', '/');
    }

    refreshState();
}

function renderSidebarWorkspaces(workspaces) {
    const list = document.getElementById('workspaces-list');
    if (!list) return;

    list.innerHTML = '';
    Object.values(workspaces).forEach((workspace) => {
        const item = document.createElement('div');
        item.className = `nav-item ${workspace.id === currentWorkspaceId ? 'active' : ''}`;
        item.innerHTML = `
            <span class="material-symbols-outlined icon">folder</span>
            <span class="name">${UI.escapeHtml(workspace.name)}</span>
            <div class="nav-actions">
                <button class="btn-item-action close-workspace" title="Close project">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>
        `;
        item.onclick = (event) => {
            if (event.target.closest('.close-workspace')) {
                event.stopPropagation();
                closeWorkspace(workspace.id);
                return;
            }
            openWorkspace(workspace.id);
        };
        list.appendChild(item);
    });
}

async function closeWorkspace(workspaceId) {
    if (!confirm('Are you sure you want to disconnect this project? All associated chat sessions will also be removed.')) {
        return;
    }

    try {
        await API.deleteWorkspace(workspaceId);
        if (currentWorkspaceId === workspaceId) {
            showDashboard();
        } else {
            refreshState();
        }
    } catch (error) {
        alert('Failed to close workspace');
    }
}

function renderRecentProjects(workspaces) {
    const grid = document.getElementById('recent-projects-grid');
    if (!grid) return;

    grid.innerHTML = '';
    const sortedWorkspaces = Object.values(workspaces);
    if (sortedWorkspaces.length === 0) {
        grid.innerHTML = '<p style="color:var(--text-secondary)">No recent projects.</p>';
        return;
    }

    sortedWorkspaces.forEach((workspace) => {
        const card = document.createElement('div');
        card.className = 'project-card';
        card.innerHTML = `
            <div class="project-name">${UI.escapeHtml(workspace.name)}</div>
            <div class="project-path">${UI.escapeHtml(workspace.path)}</div>
            <div class="project-time">Last opened ${new Date(workspace.last_accessed * 1000).toLocaleDateString()}</div>
        `;
        card.onclick = () => openWorkspace(workspace.id);
        grid.appendChild(card);
    });
}

async function refreshExplorer() {
    if (!currentWorkspaceId) return;

    try {
        const data = await API.getExplorer(currentWorkspaceId);
        workspaceFiles = [];

        const flattenNodes = (nodes) => {
            nodes.forEach((node) => {
                if (node.type === 'file') {
                    workspaceFiles.push({ name: node.name, path: node.path });
                }
                if (node.children) {
                    flattenNodes(node.children);
                }
            });
        };

        if (data.children) {
            flattenNodes(data.children);
        }

        UI.renderExplorer(data, (path) => {
            const fileName = path.split(/[/\\]/).pop();
            UI.addTaggedFile({ name: fileName, path });
        });
    } catch (error) {
        console.error('Failed to refresh explorer', error);
    }
}

async function refreshPlan() {
    if (!currentWorkspaceId) return;
    try {
        const data = await API.getPlan(currentWorkspaceId);
        UI.renderPlan(data.content);
    } catch (error) {
        console.error('Failed to refresh plan', error);
    }
}

async function refreshGit() {
    if (!currentWorkspaceId) return;

    try {
        const data = await API.getGitInfo(currentWorkspaceId);
        UI.renderGit(data, async (branchName) => {
            try {
                UI.showWorkingIndicator();
                await API.switchBranch(currentWorkspaceId, branchName);
                await refreshGit();
                await refreshExplorer();
                UI.hideWorkingIndicator();
            } catch (error) {
                UI.hideWorkingIndicator();
                alert(`Failed to switch branch: ${error.message}`);
            }
        });
    } catch (error) {
        console.error('Failed to refresh git', error);
    }
}

async function openWorkspace(workspaceId, pushState = true, autoLoadLastSession = false) {
    currentWorkspaceId = workspaceId;
    localStorage.setItem('lastWorkspaceId', workspaceId);

    UI.hideServerCenter?.();
    document.getElementById('home-dashboard').classList.add('hidden');
    document.getElementById('workspace-view').classList.remove('hidden');

    const workspace = globalData.workspaces[workspaceId];
    if (workspace) {
        document.getElementById('current-workspace-name').textContent = workspace.name;
        if (pushState) {
            history.pushState({ workspaceId, type: 'workspace' }, '', `/${encodeURIComponent(workspace.name)}`);
        }
    }

    renderSidebarWorkspaces(globalData.workspaces);
    const workspaceSessions = globalData.sessions.filter((session) => session.workspace_id === workspaceId);

    UI.renderSidebarSessions(globalData.workspaces, globalData.sessions, currentSessionId, loadSession, deleteSession);
    UI.renderSessionDropdown(workspaceId, workspaceSessions, currentSessionId, loadSession, createNewSession);
    refreshExplorer();
    refreshPlan();
    refreshGit();

    if (autoLoadLastSession && workspaceSessions.length > 0) {
        loadSession(workspaceSessions[0], pushState);
    } else if (workspaceSessions.length > 0) {
        renderWorkspaceDashboard(workspaceSessions);
    } else {
        createNewSession(workspaceId, pushState);
    }

    if (window.MemoryUI) {
        MemoryUI.init(workspaceId);
    }
    startWorkspaceRealtime();
}

function renderWorkspaceDashboard(sessions) {
    const chatContainer = document.getElementById('chat-container');
    const dashboard = document.getElementById('workspace-dashboard');
    const grid = document.getElementById('recent-sessions-grid');
    const explorerToggle = document.getElementById('btn-toggle-explorer');

    UI.hideServerCenter?.();
    chatContainer.classList.add('hidden');
    dashboard.classList.remove('hidden');
    if (explorerToggle) {
        explorerToggle.classList.add('hidden');
    }
    UI.hideExplorer();

    if (!grid) return;
    grid.innerHTML = '';

    sessions.forEach((session) => {
        const card = document.createElement('div');
        card.className = 'project-card';
        card.innerHTML = `
            <div class="project-name">${UI.escapeHtml(session.title || 'Untitled Session')}</div>
            <div class="project-path">${session.messages ? session.messages.length : 0} messages</div>
            <div class="project-time">ID: ${session.id.slice(0, 12)}...</div>
        `;
        card.onclick = () => loadSession(session);
        grid.appendChild(card);
    });

    document.getElementById('current-session-name').textContent = 'Workspace';
}

function createNewSession(workspaceId, pushState = true) {
    currentWorkspaceId = workspaceId;
    currentSessionId = `session_${Date.now()}`;

    UI.hideServerCenter?.();
    document.getElementById('workspace-dashboard').classList.add('hidden');
    document.getElementById('chat-container').classList.remove('hidden');

    const explorerToggle = document.getElementById('btn-toggle-explorer');
    if (explorerToggle) {
        explorerToggle.classList.remove('hidden');
    }

    const wrapper = document.querySelector('.messages-wrapper');
    if (wrapper) {
        wrapper.innerHTML = '';
    }
    document.getElementById('current-session-name').textContent = 'New Session';

    if (pushState) {
        const workspace = globalData.workspaces[workspaceId];
        if (workspace) {
            history.pushState(
                { sessionId: currentSessionId, workspaceId, type: 'session' },
                '',
                `/${encodeURIComponent(workspace.name)}/${currentSessionId}`
            );
        }
    }

    if (useWebSocket) {
        flashyWS.connect(currentSessionId, currentWorkspaceId).catch((error) => {
            console.warn('[App] WebSocket connection failed, using HTTP fallback', error);
        });
    }

    UI.addMessage('Ready to code in this workspace!', 'ai');
    refreshState();
}

function loadSession(session, pushState = true) {
    currentSessionId = session.id;
    currentWorkspaceId = session.workspace_id;

    UI.hideServerCenter?.();
    document.getElementById('home-dashboard').classList.add('hidden');
    document.getElementById('workspace-view').classList.remove('hidden');
    document.getElementById('workspace-dashboard').classList.add('hidden');
    document.getElementById('chat-container').classList.remove('hidden');

    const explorerToggle = document.getElementById('btn-toggle-explorer');
    if (explorerToggle) {
        explorerToggle.classList.remove('hidden');
    }

    document.getElementById('current-session-name').textContent = session.title || 'Untitled Session';
    const workspace = globalData.workspaces[currentWorkspaceId];
    if (workspace) {
        document.getElementById('current-workspace-name').textContent = workspace.name;
        if (pushState) {
            history.pushState(
                { sessionId: session.id, workspaceId: workspace.id, type: 'session' },
                '',
                `/${encodeURIComponent(workspace.name)}/${session.id}`
            );
        }
    }

    const wrapper = document.querySelector('.messages-wrapper');
    if (wrapper) {
        wrapper.innerHTML = '';
        if (session.messages) {
            session.messages.forEach((message) => {
                const content = message.parts || message.text;
                if (!content || (Array.isArray(content) && content.length === 0)) {
                    return;
                }
                UI.addMessage(content, message.role, message.images, [], message.tool_outputs || []);
            });
        }
    }

    if (useWebSocket) {
        flashyWS.connect(currentSessionId, currentWorkspaceId).catch((error) => {
            console.warn('[App] WebSocket connection failed, using HTTP fallback', error);
        });
    }

    refreshState();
    refreshExplorer();
}

async function deleteSession(sessionId) {
    if (!confirm('Are you sure you want to delete this session?')) {
        return;
    }

    try {
        await API.deleteChat(sessionId);
        if (currentSessionId === sessionId) {
            if (currentWorkspaceId) {
                openWorkspace(currentWorkspaceId);
            } else {
                showDashboard();
            }
        } else {
            refreshState();
        }
    } catch (error) {
        alert('Failed to delete session');
    }
}


let workspaceRealtimeTimer = null;
let workspaceRealtimePending = false;

async function refreshVisibleWorkspaceSurfaces() {
    if (!currentWorkspaceId || workspaceRealtimePending) return;
    workspaceRealtimePending = true;
    try {
        await refreshState(true);
        if (!document.getElementById('explorer-sidebar')?.classList.contains('hidden')) {
            await refreshExplorer();
        }
        if (!document.getElementById('plan-sidebar')?.classList.contains('hidden')) {
            await refreshPlan();
        }
        if (!document.getElementById('git-sidebar')?.classList.contains('hidden')) {
            await refreshGit();
        }
        if (window.MemoryUI?.isOpen) {
            await MemoryUI.loadMemories();
        }
    } catch (error) {
        console.warn('[Realtime] Workspace refresh failed', error);
    } finally {
        workspaceRealtimePending = false;
    }
}

function startWorkspaceRealtime() {
    stopWorkspaceRealtime();
    workspaceRealtimeTimer = setInterval(refreshVisibleWorkspaceSurfaces, 6000);
}

function stopWorkspaceRealtime() {
    if (workspaceRealtimeTimer) {
        clearInterval(workspaceRealtimeTimer);
        workspaceRealtimeTimer = null;
    }
}

window.addEventListener('focus', () => {
    if (currentWorkspaceId) refreshVisibleWorkspaceSurfaces();
});

function initResizers() {
    const sidebar = document.querySelector('.sidebar');
    const explorer = document.querySelector('.explorer-sidebar');
    const sidebarResizer = document.getElementById('sidebar-resizer');
    const explorerResizer = document.getElementById('explorer-resizer');

    if (sidebarResizer) {
        let startX = 0;
        let startWidth = 0;
        const onMouseMove = (event) => {
            const delta = event.clientX - startX;
            sidebar.style.width = `${Math.max(160, Math.min(450, startWidth + delta))}px`;
        };
        const onMouseUp = () => {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            sidebarResizer.classList.remove('active');
            document.body.style.cursor = 'default';
        };
        sidebarResizer.addEventListener('mousedown', (event) => {
            startX = event.clientX;
            startWidth = sidebar.offsetWidth;
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
            sidebarResizer.classList.add('active');
            document.body.style.cursor = 'col-resize';
        });
    }

    if (explorerResizer) {
        let startX = 0;
        let startWidth = 0;
        const onMouseMove = (event) => {
            const delta = startX - event.clientX;
            explorer.style.width = `${Math.max(200, Math.min(500, startWidth + delta))}px`;
        };
        const onMouseUp = () => {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            explorerResizer.classList.remove('active');
            document.body.style.cursor = 'default';
        };
        explorerResizer.addEventListener('mousedown', (event) => {
            startX = event.clientX;
            startWidth = explorer.offsetWidth;
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
            explorerResizer.classList.add('active');
            document.body.style.cursor = 'col-resize';
        });
    }
}
