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
            try {
                let workspace;
                if (window.__TAURI__?.dialog?.open) {
                    const path = await window.__TAURI__.dialog.open({
                        directory: true,
                        multiple: false,
                        title: 'Select a project folder'
                    });
                    if (!path) return;
                    connectModal.classList.add('hidden');
                    workspace = await connectWorkspacePath(path);
                } else if (window.flashyDesktop?.selectDirectory) {
                    const path = await window.flashyDesktop.selectDirectory();
                    if (!path) return;
                    connectModal.classList.add('hidden');
                    workspace = await connectWorkspacePath(path);
                } else {
                    // In-browser fallback: keep modal open while Tkinter picker displays
                    workspace = await API.pickWorkspace();
                    if (workspace && workspace.id) {
                        connectModal.classList.add('hidden');
                        await refreshState();
                        openWorkspace(workspace.id);
                    } else if (workspace && workspace.message === "Cancelled") {
                        console.log("Workspace picker cancelled by user.");
                    } else {
                        throw new Error(workspace?.message || "Failed to connect to workspace.");
                    }
                }
            } catch (error) {
                alert(`Failed to open folder picker: ${error.message || error}. Please try entering the path manually below.`);
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
                if (window.__TAURI__?.dialog?.open) {
                    const path = await window.__TAURI__.dialog.open({
                        directory: true,
                        multiple: false,
                        title: 'Select parent folder'
                    });
                    if (path) document.getElementById('clone-parent-path').value = path;
                } else if (window.flashyDesktop?.selectDirectory) {
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

    const toggleServerButton = document.getElementById('btn-toggle-server');
    if (toggleServerButton) {
        toggleServerButton.addEventListener('click', () => UI.toggleServerCenter());
    }

    const serverBackButton = document.getElementById('btn-server-back');
    if (serverBackButton) {
        serverBackButton.addEventListener('click', () => {
            UI.hideServerCenter();
            const wsView = document.getElementById('workspace-view');
            const dashboard = document.getElementById('home-dashboard');
            if (wsView && !wsView.classList.contains('hidden')) {
                document.getElementById('chat-container')?.classList.remove('hidden');
            } else if (dashboard) {
                dashboard.classList.remove('hidden');
            }
        });
    }

    const serverRefreshButton = document.getElementById('btn-server-refresh');
    if (serverRefreshButton) {
        serverRefreshButton.addEventListener('click', () => UI.refreshServerCenter());
    }

    const serverStartButton = document.getElementById('btn-server-start');
    if (serverStartButton) {
        serverStartButton.addEventListener('click', async () => {
            try {
                serverStartButton.disabled = true;
                serverStartButton.innerHTML = '<span class="material-symbols-outlined">hourglass_empty</span> Starting...';
                await API.startServer();
                await UI.refreshServerCenter();
            } catch (error) {
                alert(`Failed to start server: ${error.message}`);
            } finally {
                serverStartButton.innerHTML = '<span class="material-symbols-outlined">play_arrow</span> Start Server';
            }
        });
    }

    const serverStopButton = document.getElementById('btn-server-stop');
    if (serverStopButton) {
        serverStopButton.addEventListener('click', async () => {
            try {
                serverStopButton.disabled = true;
                await API.stopServer();
                await UI.refreshServerCenter();
            } catch (error) {
                alert(`Failed to stop server: ${error.message}`);
            } finally {
                serverStopButton.disabled = false;
            }
        });
    }

    const serverRestartButton = document.getElementById('btn-server-restart');
    if (serverRestartButton) {
        serverRestartButton.addEventListener('click', async () => {
            try {
                serverRestartButton.disabled = true;
                await API.restartServer();
                await UI.refreshServerCenter();
            } catch (error) {
                alert(`Failed to restart server: ${error.message}`);
            } finally {
                serverRestartButton.disabled = false;
            }
        });
    }

    const serverCopyLogButton = document.getElementById('btn-server-copy-log-path');
    if (serverCopyLogButton) {
        serverCopyLogButton.addEventListener('click', async () => {
            const path = UI.serverLogPath || '';
            if (!path) return;
            try {
                await navigator.clipboard.writeText(path);
                serverCopyLogButton.textContent = 'Copied';
                setTimeout(() => serverCopyLogButton.textContent = 'Copy log path', 1200);
            } catch (_) {
                alert(path);
            }
        });
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
                
                const githubPatInput = document.getElementById('settings-github-pat');
                if (githubPatInput) githubPatInput.value = config.GITHUB_PAT || '';
                
                const activeProviderInput = document.getElementById('settings-active-provider');
                if (activeProviderInput) activeProviderInput.value = config.active_provider || 'qwen';
                const modelInput = document.getElementById('settings-model');
                if (modelInput) modelInput.value = config.model || '';
                const reasoningEffortInput = document.getElementById('settings-reasoning-effort');
                if (reasoningEffortInput) reasoningEffortInput.value = config.reasoning_effort || 'medium';
                
                const grokProxyInput = document.getElementById('settings-grok-proxy');
                if (grokProxyInput) grokProxyInput.value = config.grok_proxy || '';
                
                const glmTokenInput = document.getElementById('settings-glm-refresh-token');
                if (glmTokenInput) glmTokenInput.value = config.glm_refresh_token || '';
                
                const chat2apiBaseUrlInput = document.getElementById('settings-chat2api-base-url');
                if (chat2apiBaseUrlInput) chat2apiBaseUrlInput.value = config.chat2api_base_url || 'http://127.0.0.1:8080';
                
                const chat2apiApiKeyInput = document.getElementById('settings-chat2api-api-key');
                if (chat2apiApiKeyInput) chat2apiApiKeyInput.value = config.chat2api_api_key || '';
                
                const lmarenaCookiesInput = document.getElementById('settings-lmarena-cookies');
                if (lmarenaCookiesInput) lmarenaCookiesInput.value = config.lmarena_cookies || '';
                
                const freegptAccessCodeInput = document.getElementById('settings-freegpt-access-code');
                if (freegptAccessCodeInput) freegptAccessCodeInput.value = config.freegpt_access_code || '';
                
                const freegptBaseUrlInput = document.getElementById('settings-freegpt-base-url');
                if (freegptBaseUrlInput) freegptBaseUrlInput.value = config.freegpt_base_url || '';
                
                const chatxCookieInput = document.getElementById('settings-chatx-cookie');
                if (chatxCookieInput) chatxCookieInput.value = config.chatx_cookie || '';
                
                const chatxBaseUrlInput = document.getElementById('settings-chatx-base-url');
                if (chatxBaseUrlInput) chatxBaseUrlInput.value = config.chatx_base_url || 'https://chatx.ai';

                const gemini1psidInput = document.getElementById('settings-gemini-1psid');
                if (gemini1psidInput) gemini1psidInput.value = config.gemini_1psid || '';
                const gemini1psidtsInput = document.getElementById('settings-gemini-1psidts');
                if (gemini1psidtsInput) gemini1psidtsInput.value = config.gemini_1psidts || '';
                const geminiCookiesJsonInput = document.getElementById('settings-gemini-cookies-json');
                if (geminiCookiesJsonInput) geminiCookiesJsonInput.value = config.gemini_cookies_json || '';

                const deepseekTokenInput = document.getElementById('settings-deepseek-token');
                if (deepseekTokenInput) deepseekTokenInput.value = config.deepseek_token || '';

                const minimaxTokenInput = document.getElementById('settings-minimax-token');
                if (minimaxTokenInput) minimaxTokenInput.value = config.minimax_token || '';
                const minimaxRealUserIdInput = document.getElementById('settings-minimax-real-user-id');
                if (minimaxRealUserIdInput) minimaxRealUserIdInput.value = config.minimax_real_user_id || '';

                const mimoServiceTokenInput = document.getElementById('settings-mimo-service-token');
                if (mimoServiceTokenInput) mimoServiceTokenInput.value = config.mimo_service_token || '';
                const mimoUserIdInput = document.getElementById('settings-mimo-user-id');
                if (mimoUserIdInput) mimoUserIdInput.value = config.mimo_user_id || '';
                const mimoPhTokenInput = document.getElementById('settings-mimo-ph-token');
                if (mimoPhTokenInput) mimoPhTokenInput.value = config.mimo_ph_token || '';

                const perplexitySessionTokenInput = document.getElementById('settings-perplexity-session-token');
                if (perplexitySessionTokenInput) perplexitySessionTokenInput.value = config.perplexity_session_token || '';

                const unimodelApiKeyInput = document.getElementById('settings-unimodel-api-key');
                if (unimodelApiKeyInput) unimodelApiKeyInput.value = config.unimodel_api_key || '';
                const unimodelBaseUrlInput = document.getElementById('settings-unimodel-base-url');
                if (unimodelBaseUrlInput) unimodelBaseUrlInput.value = config.unimodel_base_url || 'https://unimodel.ai/v1';

                const deepinfraApiKeyInput = document.getElementById('settings-deepinfra-api-key');
                if (deepinfraApiKeyInput) deepinfraApiKeyInput.value = config.deepinfra_api_key || '';

                const baiApiKeyInput = document.getElementById('settings-bai-api-key');
                if (baiApiKeyInput) baiApiKeyInput.value = config.bai_api_key || '';
                const baiBaseUrlInput = document.getElementById('settings-bai-base-url');
                if (baiBaseUrlInput) baiBaseUrlInput.value = config.bai_base_url || 'https://api.b.ai/v1';

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
                GITHUB_PAT: document.getElementById('settings-github-pat')?.value || '',
                active_provider: document.getElementById('settings-active-provider')?.value || 'qwen',
                model: document.getElementById('settings-model')?.value || '',
                reasoning_effort: document.getElementById('settings-reasoning-effort')?.value || 'medium',
                grok_proxy: document.getElementById('settings-grok-proxy')?.value || '',
                glm_refresh_token: document.getElementById('settings-glm-refresh-token')?.value || '',
                chat2api_base_url: document.getElementById('settings-chat2api-base-url')?.value || 'http://127.0.0.1:8080',
                chat2api_api_key: document.getElementById('settings-chat2api-api-key')?.value || '',
                lmarena_cookies: document.getElementById('settings-lmarena-cookies')?.value || '',
                freegpt_access_code: document.getElementById('settings-freegpt-access-code')?.value || '',
                freegpt_base_url: document.getElementById('settings-freegpt-base-url')?.value || '',
                chatx_cookie: document.getElementById('settings-chatx-cookie')?.value || '',
                chatx_base_url: document.getElementById('settings-chatx-base-url')?.value || 'https://chatx.ai',
                gemini_1psid: document.getElementById('settings-gemini-1psid')?.value || '',
                gemini_1psidts: document.getElementById('settings-gemini-1psidts')?.value || '',
                gemini_cookies_json: document.getElementById('settings-gemini-cookies-json')?.value || '',
                deepseek_token: document.getElementById('settings-deepseek-token')?.value || '',
                minimax_token: document.getElementById('settings-minimax-token')?.value || '',
                minimax_real_user_id: document.getElementById('settings-minimax-real-user-id')?.value || '',
                mimo_service_token: document.getElementById('settings-mimo-service-token')?.value || '',
                mimo_user_id: document.getElementById('settings-mimo-user-id')?.value || '',
                mimo_ph_token: document.getElementById('settings-mimo-ph-token')?.value || '',
                perplexity_session_token: document.getElementById('settings-perplexity-session-token')?.value || '',
                unimodel_api_key: document.getElementById('settings-unimodel-api-key')?.value || '',
                unimodel_base_url: document.getElementById('settings-unimodel-base-url')?.value || 'https://unimodel.ai/v1',
                deepinfra_api_key: document.getElementById('settings-deepinfra-api-key')?.value || '',
                bai_api_key: document.getElementById('settings-bai-api-key')?.value || '',
                bai_base_url: document.getElementById('settings-bai-base-url')?.value || 'https://api.b.ai/v1',
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
