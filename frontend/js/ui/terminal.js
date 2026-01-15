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

    // UI Helpers related to sidebars
    toggleExplorer() {
        const sidebar = document.getElementById('explorer-sidebar');
        const resizer = document.getElementById('explorer-resizer');
        if (sidebar) {
            const isHidden = sidebar.classList.toggle('hidden');
            if (!isHidden) this.hidePlan();
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
    },

    showExplorer() {
        const sidebar = document.getElementById('explorer-sidebar');
        const resizer = document.getElementById('explorer-resizer');
        if (sidebar) sidebar.classList.remove('hidden');
        if (resizer) resizer.classList.remove('hidden');
    },

    togglePlan() {
        const sidebar = document.getElementById('plan-sidebar');
        if (sidebar) {
            const isHidden = sidebar.classList.toggle('hidden');
            if (!isHidden) {
                this.hideExplorer();
                this.hideGit();
            }
        }
    },

    hidePlan() {
        const sidebar = document.getElementById('plan-sidebar');
        if (sidebar) sidebar.classList.add('hidden');
    },

    toggleGit() {
        const sidebar = document.getElementById('git-sidebar');
        if (sidebar) {
            const isHidden = sidebar.classList.toggle('hidden');
            if (!isHidden) {
                this.hideExplorer();
                this.hidePlan();
            }
        }
    },

    hideGit() {
        const sidebar = document.getElementById('git-sidebar');
        if (sidebar) sidebar.classList.add('hidden');
    }
});
