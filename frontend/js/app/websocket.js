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

    flashyWS.on('ask_user_question', (data) => {
        const modal = document.getElementById('modal-ask-user');
        const textEl = document.getElementById('ask-user-question-text');
        const inputEl = document.getElementById('input-ask-user-response');
        const submitBtn = document.getElementById('btn-submit-user-response');
        const closeBtn = document.getElementById('btn-close-ask-user');

        if (modal && textEl) {
            textEl.textContent = data.question;
            inputEl.value = '';
            modal.classList.remove('hidden');

            const cleanup = () => {
                modal.classList.add('hidden');
                submitBtn.onclick = null;
                closeBtn.onclick = null;
            };

            submitBtn.onclick = () => {
                flashyWS.send({
                    type: 'user_response',
                    question_id: data.question_id,
                    response: inputEl.value.trim()
                });
                cleanup();
            };

            closeBtn.onclick = () => {
                flashyWS.send({
                    type: 'user_response',
                    question_id: data.question_id,
                    response: 'User dismissed the question without answering.'
                });
                cleanup();
            };
        }
    });

    flashyWS.on('stream_end', async () => {
        UI.hideLoading();
        UI.setAgentState('idle');
        await refreshState(true);
        if (currentWorkspaceId) {
            refreshExplorer();
            refreshGit();
            refreshPlan();
            if (window.MemoryUI?.isOpen) MemoryUI.loadMemories();
        }
    });

    flashyWS.on('error', (message) => {
        UI.hideLoading();
        UI.setAgentState('idle');
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
