function setupShellEventListeners() {
    const brand = document.querySelector('.brand');
    if (brand) {
        brand.style.cursor = 'pointer';
        brand.addEventListener('click', () => showDashboard());
    }

    const sessionSelector = document.getElementById('session-selector');
    const sessionMenu = document.getElementById('session-dropdown-menu');
    if (sessionSelector && sessionMenu) {
        sessionSelector.addEventListener('click', (event) => {
            event.stopPropagation();
            sessionMenu.classList.toggle('hidden');
        });
    }

    if (window.ActivityUI) {
        ActivityUI.init();
    }

    const workspaceSelector = document.getElementById('workspace-selector');
    if (workspaceSelector) {
        workspaceSelector.addEventListener('click', () => {
            if (currentWorkspaceId) {
                openWorkspace(currentWorkspaceId);
            } else {
                showDashboard();
            }
        });
    }

    document.addEventListener('click', () => {
        if (sessionMenu) {
            sessionMenu.classList.add('hidden');
        }
    });

    const toggleSidebarButton = document.getElementById('toggle-sidebar');
    if (toggleSidebarButton) {
        toggleSidebarButton.addEventListener('click', () => {
            const sidebar = document.querySelector('.sidebar');
            const resizer = document.getElementById('sidebar-resizer');
            sidebar.classList.toggle('collapsed');

            if (resizer) {
                resizer.classList.toggle('hidden', sidebar.classList.contains('collapsed'));
            }

            const icon = toggleSidebarButton.querySelector('.material-symbols-outlined');
            icon.textContent = sidebar.classList.contains('collapsed') ? 'menu' : 'menu_open';
        });
    }

    const terminalToggle = document.getElementById('btn-toggle-terminal');
    const terminalClose = document.getElementById('btn-close-terminal');
    const terminalClear = document.getElementById('btn-clear-terminal');

    if (terminalToggle) {
        terminalToggle.addEventListener('click', (event) => {
            event.stopPropagation();
            UI.toggleTerminal();
        });
    }
    if (terminalClose) {
        terminalClose.addEventListener('click', (event) => {
            event.stopPropagation();
            UI.hideTerminal();
        });
    }
    if (terminalClear) {
        terminalClear.addEventListener('click', (event) => {
            event.stopPropagation();
            UI.clearTerminal();
        });
    }

    const connectModal = document.getElementById('modal-connect-project');
    const addWorkspaceButton = document.getElementById('btn-add-workspace');
    const closeConnectButton = document.getElementById('btn-close-connect');
    const choiceDevice = document.getElementById('choice-open-device');
    const choiceGit = document.getElementById('choice-git-clone');

    if (addWorkspaceButton && connectModal) {
        addWorkspaceButton.addEventListener('click', () => connectModal.classList.remove('hidden'));
    }
    if (closeConnectButton) {
        closeConnectButton.addEventListener('click', () => connectModal.classList.add('hidden'));
    }
    async function connectWorkspacePath(path) {
        const workspace = await API.setWorkspace(path);
        if (workspace && workspace.id) {
            await refreshState();
            openWorkspace(workspace.id);
        }
        return workspace;
    }

    window.addEventListener('flashy:native-folder-picked', async (event) => {
        if (!event.detail) return;
        try {
            await connectWorkspacePath(event.detail);
        } catch (error) {
            alert(`Error connecting path: ${error.message}`);
        }
    });

    if (choiceDevice) {
        choiceDevice.addEventListener('click', async () => {
            connectModal.classList.add('hidden');
            try {
                let workspace;
                if (window.flashyDesktop?.selectDirectory) {
                    const path = await window.flashyDesktop.selectDirectory();
                    if (!path) return;
                    workspace = await connectWorkspacePath(path);
                } else {
                    workspace = await API.pickWorkspace();
                    if (workspace && workspace.id) {
                        await refreshState();
                        openWorkspace(workspace.id);
                    }
                }
            } catch (error) {
                alert('Failed to open dialog. Please try entering the path manually below.');
                connectModal.classList.remove('hidden');
                console.error(error);
            }
        });
    }

    const addManualPathButton = document.getElementById('btn-add-manual-path');
    if (addManualPathButton) {
        addManualPathButton.addEventListener('click', async () => {
            const path = document.getElementById('manual-workspace-path').value.trim();
            if (!path) return;
            try {
                const workspace = await API.setWorkspace(path);
                if (workspace && workspace.id) {
                    document.getElementById('manual-workspace-path').value = '';
                    connectModal.classList.add('hidden');
                    await refreshState();
                    openWorkspace(workspace.id);
                }
            } catch (error) {
                alert(`Error connecting path: ${error.message}`);
            }
        });
    }

    const cloneModal = document.getElementById('modal-git-clone');
    const closeCloneButton = document.getElementById('btn-close-git-clone');
    const pickCloneParentButton = document.getElementById('btn-pick-clone-parent');
    const startCloneButton = document.getElementById('btn-start-clone');

    if (choiceGit) {
        choiceGit.addEventListener('click', () => {
            connectModal.classList.add('hidden');
            cloneModal.classList.remove('hidden');
        });
    }
    if (closeCloneButton) {
        closeCloneButton.addEventListener('click', () => cloneModal.classList.add('hidden'));
    }
    if (pickCloneParentButton) {
        pickCloneParentButton.addEventListener('click', async () => {
            try {
                if (window.flashyDesktop?.selectDirectory) {
                    const path = await window.flashyDesktop.selectDirectory();
                    if (path) document.getElementById('clone-parent-path').value = path;
                } else {
                    const result = await API.pickPath();
                    if (result && result.path) {
                        document.getElementById('clone-parent-path').value = result.path;
                    }
                }
            } catch (error) {
                alert('Failed to open dialog. You can enter the path manually.');
                console.error(error);
            }
        });
    }
    if (startCloneButton) {
        startCloneButton.addEventListener('click', async () => {
            const url = document.getElementById('clone-url').value.trim();
            const parentPath = document.getElementById('clone-parent-path').value.trim();
            const name = document.getElementById('clone-name').value.trim();
            if (!url || !parentPath) {
                alert('Please provide both URL and parent path.');
                return;
            }
            try {
                startCloneButton.disabled = true;
                startCloneButton.textContent = 'Cloning...';
                const workspace = await API.cloneRepo(url, parentPath, name || null);
                cloneModal.classList.add('hidden');
                await refreshState();
                openWorkspace(workspace.id);
            } catch (error) {
                alert(`Clone failed: ${error.message}`);
            } finally {
                startCloneButton.disabled = false;
                startCloneButton.textContent = 'Clone Repository';
            }
        });
    }

    const toggleExplorerButton = document.getElementById('btn-toggle-explorer');
    if (toggleExplorerButton) {
        toggleExplorerButton.addEventListener('click', () => UI.toggleExplorer());
    }

    const refreshExplorerButton = document.getElementById('btn-refresh-explorer');
    if (refreshExplorerButton) {
        refreshExplorerButton.addEventListener('click', () => {
            if (currentWorkspaceId) refreshExplorer();
        });
    }

    const togglePlanButton = document.getElementById('btn-toggle-plan');
    if (togglePlanButton) {
        togglePlanButton.addEventListener('click', () => {
            UI.togglePlan();
            if (!document.getElementById('plan-sidebar').classList.contains('hidden')) {
                refreshPlan();
            }
        });
    }

    const refreshPlanButton = document.getElementById('btn-refresh-plan');
    if (refreshPlanButton) {
        refreshPlanButton.addEventListener('click', () => {
            if (currentWorkspaceId) refreshPlan();
        });
    }

    const toggleGitButton = document.getElementById('btn-toggle-git');
    if (toggleGitButton) {
        toggleGitButton.addEventListener('click', () => {
            UI.toggleGit();
            if (!document.getElementById('git-sidebar').classList.contains('hidden')) {
                refreshGit();
            }
        });
    }

    const refreshGitButton = document.getElementById('btn-refresh-git');
    if (refreshGitButton) {
        refreshGitButton.addEventListener('click', () => {
            if (currentWorkspaceId) refreshGit();
        });
    }

    const pullButton = document.getElementById('btn-git-pull');
    if (pullButton) {
        pullButton.addEventListener('click', async () => {
            if (!currentWorkspaceId) return;
            try {
                UI.showWorkingIndicator();
                const result = await API.gitPull(currentWorkspaceId);
                await refreshGit();
                UI.hideWorkingIndicator();
                alert(result.message);
            } catch (error) {
                UI.hideWorkingIndicator();
                alert(`Pull failed: ${error.message}`);
            }
        });
    }

    const pushButton = document.getElementById('btn-git-push');
    if (pushButton) {
        pushButton.addEventListener('click', async () => {
            if (!currentWorkspaceId) return;
            try {
                UI.showWorkingIndicator();
                const result = await API.gitPush(currentWorkspaceId);
                await refreshGit();
                UI.hideWorkingIndicator();
                alert(result.message);
            } catch (error) {
                UI.hideWorkingIndicator();
                alert(`Push failed: ${error.message}`);
            }
        });
    }

    const dashboardNewSessionButton = document.getElementById('btn-dashboard-new-session');
    if (dashboardNewSessionButton) {
        dashboardNewSessionButton.addEventListener('click', () => {
            if (currentWorkspaceId) createNewSession(currentWorkspaceId);
        });
    }

    const settingsButton = document.getElementById('btn-settings');
    const settingsModal = document.getElementById('modal-settings');
    const closeSettingsButton = document.getElementById('btn-close-settings');
    const saveSettingsButton = document.getElementById('btn-save-settings');

    const updateProviderSettingsVisibility = (provider) => {
        document.querySelectorAll('.provider-settings-section').forEach((element) => element.classList.add('hidden'));
        const target = document.getElementById(`settings-provider-${provider}`);
        if (target) target.classList.remove('hidden');
    };

    if (settingsButton && settingsModal) {
        settingsButton.addEventListener('click', async () => {
            settingsModal.classList.remove('hidden');
            try {
                const config = await API.getConfig();
                document.getElementById('settings-psid').value = config.Secure_1PSID || '';
                document.getElementById('settings-psidts').value = config.Secure_1PSIDTS || '';
                document.getElementById('settings-github-pat').value = config.GITHUB_PAT || '';
                document.getElementById('settings-active-provider').value = config.active_provider || 'qwen';
                const modelInput = document.getElementById('settings-model');
                if (modelInput) modelInput.value = config.model || '';
                const grokProxyInput = document.getElementById('settings-grok-proxy');
                if (grokProxyInput) grokProxyInput.value = config.grok_proxy || '';
                const kimiTokenInput = document.getElementById('settings-kimi-token');
                if (kimiTokenInput) kimiTokenInput.value = config.kimi_token || '';
                const zaiTokenInput = document.getElementById('settings-zai-token');
                if (zaiTokenInput) zaiTokenInput.value = config.zai_token || '';
                const glmTokenInput = document.getElementById('settings-glm-refresh-token');
                if (glmTokenInput) glmTokenInput.value = config.glm_refresh_token || '';
                const chat2apiBaseUrlInput = document.getElementById('settings-chat2api-base-url');
                if (chat2apiBaseUrlInput) chat2apiBaseUrlInput.value = config.chat2api_base_url || 'http://127.0.0.1:8080';
                const chat2apiApiKeyInput = document.getElementById('settings-chat2api-api-key');
                if (chat2apiApiKeyInput) chat2apiApiKeyInput.value = config.chat2api_api_key || '';
                const lmarenaCookiesInput = document.getElementById('settings-lmarena-cookies');
                if (lmarenaCookiesInput) lmarenaCookiesInput.value = config.lmarena_cookies || '';
                updateProviderSettingsVisibility(config.active_provider || 'qwen');
            } catch (error) {
                console.error('Failed to load settings', error);
            }
        });

        const providerSelect = document.getElementById('settings-active-provider');
        if (providerSelect) {
            providerSelect.addEventListener('change', (event) => updateProviderSettingsVisibility(event.target.value));
        }
    }

    const initializeSettingsTabs = () => {
        const tabs = document.querySelectorAll('.settings-tab');
        const sections = document.querySelectorAll('.settings-section');

        tabs.forEach((tab) => {
            tab.addEventListener('click', (event) => {
                event.preventDefault();
                const tabId = tab.getAttribute('data-tab');
                tabs.forEach((button) => button.classList.remove('active'));
                tab.classList.add('active');
                sections.forEach((section) => section.classList.remove('active'));
                const targetSection = document.getElementById(`tab-${tabId}`);
                if (targetSection) {
                    targetSection.classList.add('active');
                }
            });
        });
    };
    initializeSettingsTabs();

    document.addEventListener('click', (event) => {
        const toggleButton = event.target.closest('.btn-toggle-visibility');
        if (!toggleButton) return;
        const targetId = toggleButton.getAttribute('data-target');
        const input = document.getElementById(targetId);
        const icon = toggleButton.querySelector('.material-symbols-outlined');
        if (!input || !icon) return;
        if (input.type === 'password') {
            input.type = 'text';
            icon.textContent = 'visibility_off';
        } else {
            input.type = 'password';
            icon.textContent = 'visibility';
        }
    });

    if (closeSettingsButton && settingsModal) {
        closeSettingsButton.addEventListener('click', () => settingsModal.classList.add('hidden'));
    }

    if (saveSettingsButton && settingsModal) {
        saveSettingsButton.addEventListener('click', async () => {
            const config = {
                Secure_1PSID: document.getElementById('settings-psid').value,
                Secure_1PSIDTS: document.getElementById('settings-psidts').value,
                GITHUB_PAT: document.getElementById('settings-github-pat').value,
                active_provider: document.getElementById('settings-active-provider').value,
                model: document.getElementById('settings-model')?.value || '',
                grok_proxy: document.getElementById('settings-grok-proxy')?.value || '',
                kimi_token: document.getElementById('settings-kimi-token')?.value || '',
                zai_token: document.getElementById('settings-zai-token')?.value || '',
                glm_refresh_token: document.getElementById('settings-glm-refresh-token')?.value || '',
                chat2api_base_url: document.getElementById('settings-chat2api-base-url')?.value || 'http://127.0.0.1:8080',
                chat2api_api_key: document.getElementById('settings-chat2api-api-key')?.value || '',
                lmarena_cookies: document.getElementById('settings-lmarena-cookies')?.value || '',
            };
            try {
                saveSettingsButton.disabled = true;
                saveSettingsButton.textContent = 'Saving...';
                await API.saveConfig(config);
                settingsModal.classList.add('hidden');
                saveSettingsButton.textContent = 'Save Changes';
                await refreshModels();
            } catch (error) {
                alert(`Failed to save settings: ${error.message}`);
                saveSettingsButton.textContent = 'Save Changes';
            } finally {
                saveSettingsButton.disabled = false;
            }
        });
    }

    const agentTypeSelector = document.getElementById('agent-type-selector');
    const agentProviderSelector = document.getElementById('agent-provider-selector');
    const agentModelInput = document.getElementById('agent-model-input');
    const saveAgentConfigButton = document.getElementById('btn-save-agent-config');

    if (agentTypeSelector) {
        agentTypeSelector.addEventListener('change', async () => {
            try {
                const config = await API.getAgentConfig(agentTypeSelector.value);
                if (agentProviderSelector) agentProviderSelector.value = config.provider || 'qwen';
                if (agentModelInput) agentModelInput.value = config.model || '';
            } catch (error) {
                console.error('Failed to load agent config:', error);
            }
        });
        agentTypeSelector.dispatchEvent(new Event('change'));
    }

    if (saveAgentConfigButton) {
        saveAgentConfigButton.addEventListener('click', async () => {
            const agentType = agentTypeSelector?.value;
            if (!agentType) return;
            try {
                saveAgentConfigButton.disabled = true;
                saveAgentConfigButton.innerHTML = '<span class="material-symbols-outlined">hourglass_empty</span> Saving...';
                await API.updateAgentConfig(agentType, agentProviderSelector?.value, agentModelInput?.value);
                saveAgentConfigButton.innerHTML = '<span class="material-symbols-outlined">check</span> Saved!';
                setTimeout(() => {
                    saveAgentConfigButton.innerHTML = '<span class="material-symbols-outlined">save</span> Save Agent Config';
                    saveAgentConfigButton.disabled = false;
                }, 1500);
            } catch (error) {
                alert(`Failed to save agent config: ${error.message}`);
                saveAgentConfigButton.innerHTML = '<span class="material-symbols-outlined">save</span> Save Agent Config';
                saveAgentConfigButton.disabled = false;
            }
        });
    }

    setupModelSelector();
}
