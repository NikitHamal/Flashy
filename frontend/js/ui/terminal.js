// Terminal Logic
Object.assign(UI, {
    showTerminal() {
        if (this.elements.terminalContainer) {
            this.elements.terminalContainer.classList.remove('hidden');
            this.elements.terminalBadge.textContent = '';
            this.elements.terminalBadge.classList.remove('active');
            this.elements.terminalToggleContainer.classList.remove('hidden');
            this.scrollToTerminalBottom();
        }
    },

    hideTerminal() {
        if (this.elements.terminalContainer) {
            this.elements.terminalContainer.classList.add('hidden');
        }
    },

    toggleTerminal() {
        if (this.elements.terminalContainer) {
            const isHidden = this.elements.terminalContainer.classList.toggle('hidden');
            if (!isHidden) {
                this.elements.terminalBadge.textContent = '';
                this.elements.terminalBadge.classList.remove('active');
                this.scrollToTerminalBottom();
            }
        }
    },

    appendTerminalOutput(text, isError = false) {
        if (!this.elements.terminalOutput) return;

        const welcome = this.elements.terminalOutput.querySelector('.terminal-welcome');
        if (welcome) welcome.remove();

        this.elements.terminalToggleContainer.classList.remove('hidden');

        const line = document.createElement('div');
        line.className = `terminal-line ${isError ? 'error' : ''}`;
        line.textContent = text;
        this.elements.terminalOutput.appendChild(line);

        if (this.elements.terminalContainer.classList.contains('hidden')) {
            const count = parseInt(this.elements.terminalBadge.textContent || '0') + 1;
            this.elements.terminalBadge.textContent = count > 99 ? '99+' : count;
            this.elements.terminalBadge.classList.add('active');
        }

        this.scrollToTerminalBottom();

        if (this.elements.terminalStatus) {
            this.elements.terminalStatus.classList.add('active');
            if (this.statusTimeout) clearTimeout(this.statusTimeout);
            this.statusTimeout = setTimeout(() => {
                this.elements.terminalStatus.classList.remove('active');
            }, 2000);
        }
    },

    scrollToTerminalBottom() {
        if (this.elements.terminalOutput) {
            this.elements.terminalOutput.scrollTop = this.elements.terminalOutput.scrollHeight;
        }
    },

    clearTerminal() {
        if (this.elements.terminalOutput) {
            this.elements.terminalOutput.innerHTML = '<div class="terminal-welcome">Waiting for terminal activity...</div>';
            this.elements.terminalBadge.textContent = '';
            this.elements.terminalBadge.classList.remove('active');
        }
    },

    prepareChatSurface() {
        this.hideServerCenter?.();
        document.getElementById('workspace-dashboard')?.classList.add('hidden');
        document.getElementById('chat-container')?.classList.remove('hidden');
    },

    setUtilityButtonActive(id, active) {
        document.getElementById(id)?.classList.toggle('active', Boolean(active));
    },

    // UI Helpers related to sidebars
    toggleExplorer() {
        const sidebar = document.getElementById('explorer-sidebar');
        const resizer = document.getElementById('explorer-resizer');
        if (sidebar) {
            this.prepareChatSurface();
            const isHidden = sidebar.classList.toggle('hidden');
            if (!isHidden) {
                this.hidePlan();
                this.hideGit();
                this.hideMemory();
                this.setUtilityButtonActive('btn-toggle-explorer', true);
            } else {
                this.setUtilityButtonActive('btn-toggle-explorer', false);
            }
            if (resizer) {
                if (isHidden) resizer.classList.add('hidden');
                else resizer.classList.remove('hidden');
            }
        }
    },

    hideExplorer() {
        const sidebar = document.getElementById('explorer-sidebar');
        const resizer = document.getElementById('explorer-resizer');
        if (sidebar) sidebar.classList.add('hidden');
        if (resizer) resizer.classList.add('hidden');
        this.setUtilityButtonActive('btn-toggle-explorer', false);
    },

    showExplorer() {
        const sidebar = document.getElementById('explorer-sidebar');
        const resizer = document.getElementById('explorer-resizer');
        if (sidebar) sidebar.classList.remove('hidden');
        if (resizer) resizer.classList.remove('hidden');
        this.setUtilityButtonActive('btn-toggle-explorer', true);
    },

    togglePlan() {
        const sidebar = document.getElementById('plan-sidebar');
        if (sidebar) {
            this.prepareChatSurface();
            const isHidden = sidebar.classList.toggle('hidden');
            if (!isHidden) {
                this.hideExplorer();
                this.hideGit();
                this.hideMemory();
                this.setUtilityButtonActive('btn-toggle-plan', true);
            } else {
                this.setUtilityButtonActive('btn-toggle-plan', false);
            }
        }
    },

    hidePlan() {
        const sidebar = document.getElementById('plan-sidebar');
        if (sidebar) sidebar.classList.add('hidden');
        this.setUtilityButtonActive('btn-toggle-plan', false);
    },

    toggleGit() {
        const sidebar = document.getElementById('git-sidebar');
        if (sidebar) {
            this.prepareChatSurface();
            const isHidden = sidebar.classList.toggle('hidden');
            if (!isHidden) {
                this.hideExplorer();
                this.hidePlan();
                this.hideMemory();
                this.setUtilityButtonActive('btn-toggle-git', true);
            } else {
                this.setUtilityButtonActive('btn-toggle-git', false);
            }
        }
    },

    hideGit() {
        const sidebar = document.getElementById('git-sidebar');
        if (sidebar) sidebar.classList.add('hidden');
        this.setUtilityButtonActive('btn-toggle-git', false);
    },

    hideMemory() {
        if (window.MemoryUI && MemoryUI.isOpen) {
            MemoryUI.isOpen = false;
        }
        document.getElementById('memory-sidebar')?.classList.add('hidden');
        this.setUtilityButtonActive('btn-toggle-memory', false);
    }
});
