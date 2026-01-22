// App Initialization & State Management
document.addEventListener('DOMContentLoaded', async () => {
    // Initial Load - Always show dashboard first unless specifically reopening
    await refreshState();

    // Event Listeners
    setupEventListeners();
    setupWebSocketHandlers();
    initResizers();

    // Initial Routing
    await handleRouting();
});

window.addEventListener('popstate', () => {
    handleRouting();
});

let currentWorkspaceId = null;
let currentSessionId = null;
let globalData = {
    workspaces: {},
    sessions: []
};

// WebSocket configuration
let useWebSocket = true; // Set to false to use HTTP fallback
let wsConnected = false;

// Setup WebSocket event handlers
function setupWebSocketHandlers() {
    flashyWS.on('connected', () => {
        wsConnected = true;
        console.log('[App] WebSocket connected');
    });

    flashyWS.on('disconnected', () => {
        wsConnected = false;
        console.log('[App] WebSocket disconnected');
    });

    flashyWS.on('thought', (content) => {
        UI.handleStreamChunk({ thought: content });
    });

    flashyWS.on('text', (data) => {
        UI.handleStreamChunk({
            text: data.content,
            images: data.images,
            is_final: data.is_final
        });
    });

    flashyWS.on('tool_call', (data) => {
        UI.handleStreamChunk({ tool_call: data });
    });

    flashyWS.on('tool_result', (content) => {
        UI.handleStreamChunk({ tool_result: content });
    });

    flashyWS.on('stream_end', () => {
        UI.hideLoading();
        UI.setAgentState('idle');
        refreshState(false);
    });

    flashyWS.on('error', (message) => {
        UI.hideLoading();
        UI.setAgentState('idle');
        // Display error in the current message stream context
        UI.handleStreamChunk({
            text: `\n\n**Error:** ${message}`,
            is_final: true
        });
    });

    flashyWS.on('terminal_output', (data) => {
        UI.appendTerminalOutput(data.output, data.is_error);
    });

    flashyWS.on('terminal_exit', (data) => {
        UI.appendTerminalOutput(`\n[Process exited with code ${data.exit_code}]\n`);
    });
}

function setupEventListeners() {
    // Brand Logo Click - Return to Home
    const brand = document.querySelector('.brand');
    if (brand) {
        brand.style.cursor = 'pointer';
        brand.addEventListener('click', () => {
            showDashboard();
        });
    }

    // Top-bar Dropdown
    const sessSelector = document.getElementById('session-selector');
    const sessMenu = document.getElementById('session-dropdown-menu');
    if (sessSelector && sessMenu) {
        sessSelector.addEventListener('click', (e) => {
            e.stopPropagation();
            sessMenu.classList.toggle('hidden');
        });
    }

    // Workspace selector (crumb) - return to workspace home or dashboard
    const wsSelector = document.getElementById('workspace-selector');
    if (wsSelector) {
        wsSelector.addEventListener('click', () => {
            if (currentWorkspaceId) {
                openWorkspace(currentWorkspaceId);
            } else {
                showDashboard();
            }
        });
    }

    // Close menus on outside click
    document.addEventListener('click', () => {
        if (sessMenu) sessMenu.classList.add('hidden');
    });

    // Sidebar toggle
    const toggleBtn = document.getElementById('toggle-sidebar');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const sidebar = document.querySelector('.sidebar');
            const resizer = document.getElementById('sidebar-resizer');
            sidebar.classList.toggle('collapsed');

            if (resizer) {
                if (sidebar.classList.contains('collapsed')) resizer.classList.add('hidden');
                else resizer.classList.remove('hidden');
            }

            const icon = toggleBtn.querySelector('.material-symbols-outlined');
            if (sidebar.classList.contains('collapsed')) {
                icon.textContent = 'menu';
            } else {
                icon.textContent = 'menu_open';
            }
        });
    }

    // Terminal Listeners
    const terminalToggle = document.getElementById('btn-toggle-terminal');
    const terminalClose = document.getElementById('btn-close-terminal');
    const terminalClear = document.getElementById('btn-clear-terminal');

    if (terminalToggle) {
        terminalToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            UI.toggleTerminal();
        });
    }

    if (terminalClose) {
        terminalClose.addEventListener('click', (e) => {
            e.stopPropagation();
            UI.hideTerminal();
        });
    }

    if (terminalClear) {
        terminalClear.addEventListener('click', (e) => {
            e.stopPropagation();
            UI.clearTerminal();
        });
    }

    // Add Workspace Button (Renamed to Connect Project)
    const addWsBtn = document.getElementById('btn-add-workspace');
    const connectModal = document.getElementById('modal-connect-project');
    const closeConnectBtn = document.getElementById('btn-close-connect');
    const choiceDevice = document.getElementById('choice-open-device');
    const choiceGit = document.getElementById('choice-git-clone');

    if (addWsBtn && connectModal) {
        addWsBtn.addEventListener('click', () => {
            connectModal.classList.remove('hidden');
        });
    }

    if (closeConnectBtn) {
        closeConnectBtn.addEventListener('click', () => {
            connectModal.classList.add('hidden');
        });
    }

    if (choiceDevice) {
        choiceDevice.addEventListener('click', async () => {
            connectModal.classList.add('hidden');
            try {
                const ws = await API.pickWorkspace();
                if (ws && ws.id) {
                    await refreshState();
                    openWorkspace(ws.id);
                }
            } catch (e) {
                alert("Failed to open dialog. Please try entering the path manually below.");
                connectModal.classList.remove('hidden');
                console.error(e);
            }
        });
    }

    const addManualBtn = document.getElementById('btn-add-manual-path');
    if (addManualBtn) {
        addManualBtn.addEventListener('click', async () => {
            const path = document.getElementById('manual-workspace-path').value.trim();
            if (!path) return;

            try {
                const ws = await API.setWorkspace(path);
                if (ws && ws.id) {
                    document.getElementById('manual-workspace-path').value = '';
                    connectModal.classList.add('hidden');
                    await refreshState();
                    openWorkspace(ws.id);
                }
            } catch (e) {
                alert("Error connecting path: " + e.message);
            }
        });
    }

    // Git Clone Modal Logic
    const cloneModal = document.getElementById('modal-git-clone');
    const closeCloneBtn = document.getElementById('btn-close-git-clone');
    const pickCloneParentBtn = document.getElementById('btn-pick-clone-parent');
    const startCloneBtn = document.getElementById('btn-start-clone');

    if (choiceGit) {
        choiceGit.addEventListener('click', () => {
            connectModal.classList.add('hidden');
            cloneModal.classList.remove('hidden');
        });
    }

    if (closeCloneBtn) {
        closeCloneBtn.addEventListener('click', () => {
            cloneModal.classList.add('hidden');
        });
    }

    if (pickCloneParentBtn) {
        pickCloneParentBtn.addEventListener('click', async () => {
            try {
                // Use the new path-only picker
                const res = await API.pickPath();
                if (res && res.path) {
                    document.getElementById('clone-parent-path').value = res.path;
                }
            } catch (e) {
                alert("Failed to open dialog. You can enter the path manually.");
                console.error(e);
            }
        });
    }

    if (startCloneBtn) {
        startCloneBtn.addEventListener('click', async () => {
            const url = document.getElementById('clone-url').value.trim();
            const parentPath = document.getElementById('clone-parent-path').value.trim();
            const name = document.getElementById('clone-name').value.trim();

            if (!url || !parentPath) {
                alert("Please provide both URL and parent path.");
                return;
            }

            try {
                startCloneBtn.disabled = true;
                startCloneBtn.textContent = 'Cloning...';

                const ws = await API.cloneRepo(url, parentPath, name || null);

                cloneModal.classList.add('hidden');
                await refreshState();
                openWorkspace(ws.id);
            } catch (e) {
                alert("Clone failed: " + e.message);
            } finally {
                startCloneBtn.disabled = false;
                startCloneBtn.textContent = 'Clone Repository';
            }
        });
    }

    // Explorer Toggle
    const toggleExplorerBtn = document.getElementById('btn-toggle-explorer');
    if (toggleExplorerBtn) {
        toggleExplorerBtn.addEventListener('click', () => {
            UI.toggleExplorer();
        });
    }

    const refreshExplorerBtn = document.getElementById('btn-refresh-explorer');
    if (refreshExplorerBtn) {
        refreshExplorerBtn.addEventListener('click', () => {
            if (currentWorkspaceId) refreshExplorer();
        });
    }

    // Plan Toggle
    const togglePlanBtn = document.getElementById('btn-toggle-plan');
    if (togglePlanBtn) {
        togglePlanBtn.addEventListener('click', () => {
            UI.togglePlan();
            if (!document.getElementById('plan-sidebar').classList.contains('hidden')) {
                refreshPlan();
            }
        });
    }

    const refreshPlanBtn = document.getElementById('btn-refresh-plan');
    if (refreshPlanBtn) {
        refreshPlanBtn.addEventListener('click', () => {
            if (currentWorkspaceId) refreshPlan();
        });
    }

    // Git Toggle
    const toggleGitBtn = document.getElementById('btn-toggle-git');
    if (toggleGitBtn) {
        toggleGitBtn.addEventListener('click', () => {
            UI.toggleGit();
            if (!document.getElementById('git-sidebar').classList.contains('hidden')) {
                refreshGit();
            }
        });
    }

    const refreshGitBtn = document.getElementById('btn-refresh-git');
    if (refreshGitBtn) {
        refreshGitBtn.addEventListener('click', () => {
            if (currentWorkspaceId) refreshGit();
        });
    }

    const pullBtn = document.getElementById('btn-git-pull');
    if (pullBtn) {
        pullBtn.addEventListener('click', async () => {
            if (!currentWorkspaceId) return;
            try {
                UI.showWorkingIndicator();
                const res = await API.gitPull(currentWorkspaceId);
                await refreshGit();
                UI.hideWorkingIndicator();
                alert(res.message);
            } catch (e) {
                UI.hideWorkingIndicator();
                alert("Pull failed: " + e.message);
            }
        });
    }

    const pushBtn = document.getElementById('btn-git-push');
    if (pushBtn) {
        pushBtn.addEventListener('click', async () => {
            if (!currentWorkspaceId) return;
            try {
                UI.showWorkingIndicator();
                const res = await API.gitPush(currentWorkspaceId);
                await refreshGit();
                UI.hideWorkingIndicator();
                alert(res.message);
            } catch (e) {
                UI.hideWorkingIndicator();
                alert("Push failed: " + e.message);
            }
        });
    }

    // Dashboard New Session
    const dashNewSessBtn = document.getElementById('btn-dashboard-new-session');
    if (dashNewSessBtn) {
        dashNewSessBtn.addEventListener('click', () => {
            if (currentWorkspaceId) createNewSession(currentWorkspaceId);
        });
    }

    // Settings Modal
    const settingsBtn = document.getElementById('btn-settings');
    const settingsModal = document.getElementById('modal-settings');
    const closeSettingsBtn = document.getElementById('btn-close-settings');
    const saveSettingsBtn = document.getElementById('btn-save-settings');

    if (settingsBtn && settingsModal) {
        settingsBtn.addEventListener('click', async () => {
            settingsModal.classList.remove('hidden');
            try {
                const config = await API.getConfig();
                document.getElementById('settings-psid').value = config.Secure_1PSID || '';
                document.getElementById('settings-psidts').value = config.Secure_1PSIDTS || '';
                document.getElementById('settings-psidcc').value = config.Secure_1PSIDCC || '';
                document.getElementById('settings-github-pat').value = config.GITHUB_PAT || '';

                // New Providers
                document.getElementById('settings-active-provider').value = config.active_provider || 'gemini';
                document.getElementById('settings-model').value = config.model || '';

                updateProviderSettingsVisibility(config.active_provider || 'gemini');

            } catch (e) {
                console.error("Failed to load settings", e);
            }
        });

        // Provider Selection Change Event
        const providerSelect = document.getElementById('settings-active-provider');
        if (providerSelect) {
            providerSelect.addEventListener('change', (e) => {
                updateProviderSettingsVisibility(e.target.value);
            });
        }
    }

    function updateProviderSettingsVisibility(provider) {
        document.querySelectorAll('.provider-settings-section').forEach(el => el.classList.add('hidden'));

        const target = document.getElementById(`settings-provider-${provider}`);
        if (target) target.classList.remove('hidden');
    }

    // Toggle Visibility
    document.querySelectorAll('.btn-toggle-visibility').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const input = document.getElementById(targetId);
            const icon = btn.querySelector('.material-symbols-outlined');
            if (input.type === 'password') {
                input.type = 'text';
                icon.textContent = 'visibility_off';
            } else {
                input.type = 'password';
                icon.textContent = 'visibility';
            }
        });
    });

    if (closeSettingsBtn && settingsModal) {
        closeSettingsBtn.addEventListener('click', () => {
            settingsModal.classList.add('hidden');
        });
    }

    if (saveSettingsBtn && settingsModal) {
        saveSettingsBtn.addEventListener('click', async () => {
            const config = {
                Secure_1PSID: document.getElementById('settings-psid').value,
                Secure_1PSIDTS: document.getElementById('settings-psidts').value,
                Secure_1PSIDCC: document.getElementById('settings-psidcc').value,
                GITHUB_PAT: document.getElementById('settings-github-pat').value,
                active_provider: document.getElementById('settings-active-provider').value,
                model: document.getElementById('settings-model').value
            };
            try {
                saveSettingsBtn.disabled = true;
                saveSettingsBtn.textContent = 'Saving...';

                await API.saveConfig(config);

                settingsModal.classList.add('hidden');
                saveSettingsBtn.textContent = 'Save Changes';

                // Refresh models in UI if provider changed
                await refreshModels();
            } catch (e) {
                alert("Failed to save settings: " + e.message);
                saveSettingsBtn.textContent = 'Save Changes';
            } finally {
                saveSettingsBtn.disabled = false;
            }
        });
    }

    // Chat Input Logic
    const input = document.getElementById('message-input');
    const sendBtn = document.getElementById('btn-send');
    const attachBtn = document.getElementById('btn-attach');
    const fileInput = document.getElementById('file-input');

    // File attachment click
    if (attachBtn && fileInput) {
        attachBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                UI.addUploadedFiles(fileInput.files);
                fileInput.value = ''; // Reset to allow adding same file again if removed
            }
        });
    }

    const handleSend = async () => {
        if (UI.isWorking) {
            // Stop logic - use WebSocket if connected
            try {
                if (useWebSocket && flashyWS.connected) {
                    flashyWS.interrupt();
                } else {
                    await API.interruptChat(currentSessionId);
                }
            } catch (e) {
                console.error("Failed to stop agent", e);
            }
            return;
        }

        const text = input.value.trim();
        const uploadedFiles = UI.uploadedFiles;
        const taggedFiles = UI.taggedFiles;

        if (!text && uploadedFiles.length === 0 && taggedFiles.length === 0) return;

        // Construct message structure for AI (mentioning files)
        let finalText = text;
        if (taggedFiles.length > 0) {
            const fileList = taggedFiles.map(f => f.path).join(', ');
            if (!text.includes(fileList)) {
                finalText += `\n\n[Context: User is focusing on these files: ${fileList}]`;
            }
        }

        input.value = '';
        input.style.height = 'auto';

        // Combine both internal tagged files and external uploads for visual display
        const allFilesForDisplay = [...taggedFiles, ...uploadedFiles];
        UI.addMessage(text, 'user', [], allFilesForDisplay);

        UI.clearTaggedFiles();
        UI.clearUploadedFiles();
        UI.showLoading();
        UI.setAgentState('working');

        try {
            // Use WebSocket if enabled and connected
            if (useWebSocket && flashyWS.connected) {
                // Convert files to base64 for WebSocket transfer
                const filesData = [];
                for (const file of uploadedFiles) {
                    const base64 = await fileToBase64(file);
                    filesData.push({
                        name: file.name,
                        content: base64
                    });
                }

                flashyWS.sendChatMessage(finalText, filesData);
                // Note: stream_end handler will call hideLoading and refreshState
            } else {
                // Fallback to HTTP streaming
                await API.sendMessage(finalText, currentSessionId, currentWorkspaceId, uploadedFiles, (chunk) => {
                    UI.handleStreamChunk(chunk);
                });
                await refreshState(false);
                UI.hideLoading();
                UI.setAgentState('idle');
            }
        } catch (e) {
            UI.hideLoading();
            UI.setAgentState('idle');
            UI.addMessage(`Error: ${e.message}`, 'ai');
        }
    };

    // Helper function to convert File to base64
    async function fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                const base64 = reader.result.split(',')[1]; // Remove data:... prefix
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }

    if (sendBtn) sendBtn.addEventListener('click', handleSend);
    if (input) {
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                // Check if mention popup is open
                const mentionPopup = document.getElementById('mention-popup');
                if (mentionPopup && !mentionPopup.classList.contains('hidden')) {
                    const active = mentionPopup.querySelector('.mention-item.active');
                    if (active) {
                        active.click();
                        e.preventDefault();
                        return;
                    }
                }
                e.preventDefault();
                handleSend();
            }

            if (e.key === 'ArrowDown') {
                const mentionPopup = document.getElementById('mention-popup');
                if (mentionPopup && !mentionPopup.classList.contains('hidden')) {
                    e.preventDefault();
                    UI.navigateMention('down');
                }
            }

            if (e.key === 'ArrowUp') {
                const mentionPopup = document.getElementById('mention-popup');
                if (mentionPopup && !mentionPopup.classList.contains('hidden')) {
                    e.preventDefault();
                    UI.navigateMention('up');
                }
            }

            if (e.key === 'Escape') {
                UI.hideMentionPopup();
            }
        });

        input.addEventListener('input', function (e) {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';

            if (UI.isWorking) return; // Don't change button state while working

            const value = this.value;
            const cursorCoords = this.selectionStart;
            const textBeforeCursor = value.substring(0, cursorCoords);
            const words = textBeforeCursor.split(/\s+/);
            const lastWord = words[words.length - 1];

            if (lastWord.startsWith('@')) {
                const query = lastWord.substring(1).toLowerCase();
                const filtered = workspaceFiles.filter(f =>
                    f.name.toLowerCase().includes(query) ||
                    f.path.toLowerCase().includes(query)
                ).slice(0, 10);

                if (filtered.length > 0) {
                    UI.showMentionPopup(filtered, (file) => {
                        // Replace @word with file tag
                        const beforeMention = textBeforeCursor.substring(0, textBeforeCursor.length - lastWord.length);
                        const afterMention = value.substring(cursorCoords);
                        input.value = beforeMention + '@' + file.name + ' ' + afterMention;
                        UI.addTaggedFile(file);
                        input.focus();
                    });
                } else {
                    UI.hideMentionPopup();
                }
            } else {
                UI.hideMentionPopup();
            }
        });
    }
    setupModelSelector();
}

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
                const workspaceSessions = history.filter(s => s.workspace_id === currentWorkspaceId);
                UI.renderSessionDropdown(currentWorkspaceId, workspaceSessions, currentSessionId, loadSession, createNewSession);
            }
        }
    } catch (e) {
        console.error("Failed to refresh state", e);
    }
}

function showDashboard() {
    currentWorkspaceId = null;
    currentSessionId = null;
    document.getElementById('home-dashboard').classList.remove('hidden');
    document.getElementById('workspace-view').classList.add('hidden');

    const explorerToggle = document.getElementById('btn-toggle-explorer');
    if (explorerToggle) explorerToggle.classList.add('hidden');

    if (window.location.pathname !== '/') {
        history.pushState({ type: 'dashboard' }, '', '/');
    }

    refreshState();
}

function renderSidebarWorkspaces(workspaces) {
    const list = document.getElementById('workspaces-list');
    if (!list) return;
    list.innerHTML = '';
    Object.values(workspaces).forEach(ws => {
        const item = document.createElement('div');
        item.className = `nav-item ${ws.id === currentWorkspaceId ? 'active' : ''}`;
        item.innerHTML = `
            <span class="material-symbols-outlined icon">folder</span>
            <span class="name">${ws.name}</span>
            <div class="nav-actions">
                <button class="btn-item-action close-workspace" title="Close project">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>
        `;
        item.onclick = (e) => {
            if (e.target.closest('.close-workspace')) {
                e.stopPropagation();
                closeWorkspace(ws.id);
                return;
            }
            openWorkspace(ws.id);
        };
        list.appendChild(item);
    });
}

async function closeWorkspace(workspaceId) {
    if (confirm("Are you sure you want to disconnect this project? All associated chat sessions will also be removed.")) {
        try {
            await API.deleteWorkspace(workspaceId);
            if (currentWorkspaceId === workspaceId) {
                showDashboard();
            } else {
                refreshState();
            }
        } catch (e) {
            alert("Failed to close workspace");
        }
    }
}

function renderRecentProjects(workspaces) {
    const grid = document.getElementById('recent-projects-grid');
    if (!grid) return;
    grid.innerHTML = '';
    const sorted = Object.values(workspaces);
    if (sorted.length === 0) {
        grid.innerHTML = '<p style="color:var(--text-secondary)">No recent projects.</p>';
        return;
    }
    sorted.forEach(ws => {
        const card = document.createElement('div');
        card.className = 'project-card';
        card.innerHTML = `
            <div class="project-name">${ws.name}</div>
            <div class="project-path">${ws.path}</div>
            <div class="project-time">Last opened ${new Date(ws.last_accessed * 1000).toLocaleDateString()}</div>
        `;
        card.onclick = () => openWorkspace(ws.id);
        grid.appendChild(card);
    });
}

let workspaceFiles = [];

async function refreshExplorer() {
    if (!currentWorkspaceId) return;
    try {
        const data = await API.getExplorer(currentWorkspaceId);

        // Flatten files for mention popup search
        workspaceFiles = [];
        const flat = (nodes) => {
            nodes.forEach(n => {
                if (n.type === 'file') workspaceFiles.push({ name: n.name, path: n.path });
                if (n.children) flat(n.children);
            });
        };
        if (data.children) flat(data.children);

        UI.renderExplorer(data, (path) => {
            const fileName = path.split(/[/\\]/).pop();
            UI.addTaggedFile({ name: fileName, path: path });
        });
    } catch (e) {
        console.error("Failed to refresh explorer", e);
    }
}

async function refreshPlan() {
    if (!currentWorkspaceId) return;
    try {
        const data = await API.getPlan(currentWorkspaceId);
        UI.renderPlan(data.content);
    } catch (e) {
        console.error("Failed to refresh plan", e);
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
            } catch (e) {
                UI.hideWorkingIndicator();
                alert("Failed to switch branch: " + e.message);
            }
        });
    } catch (e) {
        console.error("Failed to refresh git", e);
    }
}

async function openWorkspace(workspaceId, pushState = true, autoLoadLastSession = false) {
    currentWorkspaceId = workspaceId;
    localStorage.setItem('lastWorkspaceId', workspaceId);

    document.getElementById('home-dashboard').classList.add('hidden');
    document.getElementById('workspace-view').classList.remove('hidden');

    const ws = globalData.workspaces[workspaceId];
    if (ws) {
        document.getElementById('current-workspace-name').textContent = ws.name;
        if (pushState) {
            const url = `/${encodeURIComponent(ws.name)}`;
            history.pushState({ workspaceId, type: 'workspace' }, '', url);
        }
    }

    // Highight active workspace in sidebar immediately
    renderSidebarWorkspaces(globalData.workspaces);

    // Filter sessions for this workspace
    const workspaceSessions = globalData.sessions.filter(s => s.workspace_id === workspaceId);

    // UI Updates
    UI.renderSidebarSessions(globalData.workspaces, globalData.sessions, currentSessionId, loadSession, deleteSession);
    UI.renderSessionDropdown(workspaceId, workspaceSessions, currentSessionId, loadSession, createNewSession);
    refreshExplorer();
    refreshPlan();
    refreshGit();

    if (autoLoadLastSession && workspaceSessions.length > 0) {
        loadSession(workspaceSessions[0], pushState);
    } else if (workspaceSessions.length > 0) {
        // Show Workspace Dashboard (Recent Sessions)
        renderWorkspaceDashboard(workspaceSessions);
    } else {
        // No sessions, start new one
        createNewSession(workspaceId, pushState);
    }
}

function renderWorkspaceDashboard(sessions) {
    const chatContainer = document.getElementById('chat-container');
    const workspaceDash = document.getElementById('workspace-dashboard');
    const grid = document.getElementById('recent-sessions-grid');
    const explorerToggle = document.getElementById('btn-toggle-explorer');

    chatContainer.classList.add('hidden');
    workspaceDash.classList.remove('hidden');
    if (explorerToggle) explorerToggle.classList.add('hidden');
    UI.hideExplorer(); // Force close explorer when entering dashboard

    if (!grid) return;
    grid.innerHTML = '';

    // Sort by created/updated time if available, or just use as is
    sessions.forEach(session => {
        const card = document.createElement('div');
        card.className = 'project-card';
        card.innerHTML = `
            <div class="project-name">${session.title || 'Untitled Session'}</div>
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

    // Switch view to chat
    document.getElementById('workspace-dashboard').classList.add('hidden');
    document.getElementById('chat-container').classList.remove('hidden');

    const explorerToggle = document.getElementById('btn-toggle-explorer');
    if (explorerToggle) explorerToggle.classList.remove('hidden');

    const wrapper = document.querySelector('.messages-wrapper');
    if (wrapper) wrapper.innerHTML = '';
    document.getElementById('current-session-name').textContent = 'New Session';

    if (pushState) {
        const ws = globalData.workspaces[workspaceId];
        if (ws) {
            const url = `/${encodeURIComponent(ws.name)}/${currentSessionId}`;
            history.pushState({ sessionId: currentSessionId, workspaceId, type: 'session' }, '', url);
        }
    }

    // Connect WebSocket for this session
    if (useWebSocket) {
        flashyWS.connect(currentSessionId, currentWorkspaceId).catch(err => {
            console.warn('[App] WebSocket connection failed, using HTTP fallback', err);
        });
    }

    UI.addMessage("Ready to code in this workspace!", 'ai');
    refreshState();
}

function loadSession(session, pushState = true) {
    currentSessionId = session.id;
    currentWorkspaceId = session.workspace_id;

    document.getElementById('home-dashboard').classList.add('hidden');
    document.getElementById('workspace-view').classList.remove('hidden');
    document.getElementById('workspace-dashboard').classList.add('hidden');
    document.getElementById('chat-container').classList.remove('hidden');

    const explorerToggle = document.getElementById('btn-toggle-explorer');
    if (explorerToggle) explorerToggle.classList.remove('hidden');

    document.getElementById('current-session-name').textContent = session.title || 'Untitled Session';
    const ws = globalData.workspaces[currentWorkspaceId];
    if (ws) {
        document.getElementById('current-workspace-name').textContent = ws.name;
        if (pushState) {
            const url = `/${encodeURIComponent(ws.name)}/${session.id}`;
            history.pushState({ sessionId: session.id, workspaceId: ws.id, type: 'session' }, '', url);
        }
    }

    const wrapper = document.querySelector('.messages-wrapper');
    if (wrapper) {
        wrapper.innerHTML = '';
        if (session.messages) {
            session.messages.forEach(msg => {
                // Pass parts if available (new format), else pass text (old format)
                const content = msg.parts || msg.text;
                if (!content) return; // Skip empty messages

                // If parts is an empty array, it might be a corrupted message
                if (Array.isArray(content) && content.length === 0) return;

                UI.addMessage(content, msg.role, msg.images, [], msg.tool_outputs || []);
            });
        }
    }

    // Connect WebSocket for this session
    if (useWebSocket) {
        flashyWS.connect(currentSessionId, currentWorkspaceId).catch(err => {
            console.warn('[App] WebSocket connection failed, using HTTP fallback', err);
        });
    }

    refreshState();
    refreshExplorer();
}

async function handleRouting() {
    const path = window.location.pathname;
    const parts = path.split('/').filter(p => p);

    if (parts.length === 0) {
        showDashboard();
        return;
    }

    // Wait for state to be ready if it's not
    if (Object.keys(globalData.workspaces).length === 0) {
        await refreshState(false);
    }

    const workspaceName = decodeURIComponent(parts[0]);
    const sessionId = parts[1];

    const ws = Object.values(globalData.workspaces).find(w => w.name === workspaceName);
    if (!ws) {
        showDashboard();
        return;
    }

    if (sessionId) {
        const session = globalData.sessions.find(s => s.id === sessionId);
        if (session) {
            loadSession(session, false);
        } else {
            // Specified session ID not found, treat as workspace home
            openWorkspace(ws.id, false, false);
        }
    } else {
        // Workspace URL opened - show dashboard or new session
        openWorkspace(ws.id, false, false);
    }
}

async function deleteSession(sessionId) {
    if (confirm("Are you sure you want to delete this session?")) {
        try {
            await API.deleteChat(sessionId);
            if (currentSessionId === sessionId) {
                if (currentWorkspaceId) openWorkspace(currentWorkspaceId);
                else showDashboard();
            } else {
                refreshState();
            }
        } catch (e) {
            alert("Failed to delete session");
        }
    }
}

function initResizers() {
    const sidebar = document.querySelector('.sidebar');
    const explorer = document.querySelector('.explorer-sidebar');
    const sbResizer = document.getElementById('sidebar-resizer');
    const exResizer = document.getElementById('explorer-resizer');

    if (sbResizer) {
        let x = 0;
        let w = 0;
        const onMouseMove = (e) => {
            const dx = e.clientX - x;
            const newW = Math.max(160, Math.min(450, w + dx));
            sidebar.style.width = `${newW}px`;
        };
        const onMouseUp = () => {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            sbResizer.classList.remove('active');
            document.body.style.cursor = 'default';
        };
        sbResizer.addEventListener('mousedown', (e) => {
            x = e.clientX;
            w = sidebar.offsetWidth;
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
            sbResizer.classList.add('active');
            document.body.style.cursor = 'col-resize';
        });
    }

    if (exResizer) {
        let x = 0;
        let w = 0;
        const onMouseMove = (e) => {
            const dx = x - e.clientX;
            const newW = Math.max(200, Math.min(500, w + dx));
            explorer.style.width = `${newW}px`;
        };
        const onMouseUp = () => {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            exResizer.classList.remove('active');
            document.body.style.cursor = 'default';
        };
        exResizer.addEventListener('mousedown', (e) => {
            x = e.clientX;
            w = explorer.offsetWidth;
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
            exResizer.classList.add('active');
            document.body.style.cursor = 'col-resize';
        });
    }
}

// Add CSS class for hidden state if not present
const style = document.createElement('style');
style.textContent = '.hidden { display: none !important; }';
document.head.appendChild(style);
let cachedModels = [];

async function setupModelSelector() {
    const selectorBtn = document.getElementById('btn-model-selector');
    const modelMenu = document.getElementById('model-dropdown-menu');

    if (!selectorBtn || !modelMenu) return;

    selectorBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        modelMenu.classList.toggle('hidden');
    });

    // Initial load
    await refreshModels();
}

async function refreshModels() {
    try {
        const config = await API.getConfig();
        const activeProvider = config.active_provider;
        const cacheKey = `models_${activeProvider}`;

        // Try to load from cache first
        const cached = localStorage.getItem(cacheKey);
        if (cached) {
            cachedModels = JSON.parse(cached);
            renderModelDropdown();
        }

        // Fetch fresh models
        const models = await API.getModels();
        cachedModels = models;
        localStorage.setItem(cacheKey, JSON.stringify(models));
        renderModelDropdown();

        // Update current model name display
        const activeModelId = config.model;

        if (activeProvider === 'gemini') {
            document.getElementById('current-model-name').textContent = 'Agent Flashy';
        } else {
            const model = cachedModels.find(m => m.id === activeModelId);
            document.getElementById('current-model-name').textContent = model ? model.name : (activeModelId || 'Select Model');
        }
    } catch (e) {
        console.error("Failed to refresh models", e);
    }
}

function renderModelDropdown() {
    const modelMenu = document.getElementById('model-dropdown-menu');
    if (!modelMenu) return;

    if (cachedModels.length === 0) {
        modelMenu.innerHTML = '<div class="dropdown-item">No models available</div>';
        return;
    }

    modelMenu.innerHTML = cachedModels.map(m => `
        <div class="dropdown-item" data-id="${m.id}" data-name="${m.name}">
            <div class="item-info">
                <span class="item-title">${m.name}</span>
                <span class="item-meta">${m.id}</span>
            </div>
        </div>
    `).join('');

    modelMenu.querySelectorAll('.dropdown-item').forEach(item => {
        item.addEventListener('click', async () => {
            const id = item.getAttribute('data-id');
            const name = item.getAttribute('data-name');
            await selectModel(id, name);
        });
    });
}

async function selectModel(id, name) {
    try {
        const config = await API.getConfig();
        config.model = id;
        await API.saveConfig(config);

        const activeProvider = config.active_provider;
        if (activeProvider === 'gemini') {
            document.getElementById('current-model-name').textContent = 'Agent Flashy';
        } else {
            document.getElementById('current-model-name').textContent = name;
        }

        document.getElementById('model-dropdown-menu').classList.add('hidden');
        console.log(`Model selected: ${name} (${id})`);
    } catch (e) {
        alert("Failed to save model selection: " + e.message);
    }
}
