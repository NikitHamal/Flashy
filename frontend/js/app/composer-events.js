function setupComposerEventListeners() {
    const input = document.getElementById('message-input');
    const sendButton = document.getElementById('btn-send');
    const attachButton = document.getElementById('btn-attach');
    const fileInput = document.getElementById('file-input');

    if (attachButton && fileInput) {
        attachButton.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                UI.addUploadedFiles(fileInput.files);
                fileInput.value = '';
            }
        });
    }

    const fileToBase64 = async (file) => new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result.split(',')[1]);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });

    const handleSend = async () => {
        if (UI.isWorking) {
            try {
                if (useWebSocket && flashyWS.connected) {
                    flashyWS.interrupt();
                } else {
                    await API.interruptChat(currentSessionId);
                }
            } catch (error) {
                console.error('Failed to stop agent', error);
            }
            return;
        }

        const text = input.value.trim();
        const uploadedFiles = UI.uploadedFiles;
        const taggedFiles = UI.taggedFiles;
        if (!text && uploadedFiles.length === 0 && taggedFiles.length === 0) {
            return;
        }

        let finalText = text;
        if (taggedFiles.length > 0) {
            const fileList = taggedFiles.map((file) => file.path).join(', ');
            if (!text.includes(fileList)) {
                finalText += `\n\n[Context: User is focusing on these files: ${fileList}]`;
            }
        }

        input.value = '';
        input.style.height = 'auto';

        const allFilesForDisplay = [...taggedFiles, ...uploadedFiles];
        UI.addMessage(text, 'user', [], allFilesForDisplay);
        UI.clearTaggedFiles();
        UI.clearUploadedFiles();
        UI.showLoading();
        UI.setAgentState('working');

        try {
            if (useWebSocket && flashyWS.connected) {
                const filesData = [];
                for (const file of uploadedFiles) {
                    filesData.push({
                        name: file.name,
                        content: await fileToBase64(file)
                    });
                }
                flashyWS.sendChatMessage(finalText, filesData);
            } else {
                await API.sendMessage(finalText, currentSessionId, currentWorkspaceId, uploadedFiles, (chunk) => {
                    UI.handleStreamChunk(chunk);
                });
                await refreshState(false);
                UI.hideLoading();
                UI.setAgentState('idle');
            }
        } catch (error) {
            UI.hideLoading();
            UI.setAgentState('idle');
            UI.addMessage(`Error: ${error.message}`, 'ai');
        }
    };

    if (sendButton) {
        sendButton.addEventListener('click', handleSend);
    }

    if (!input) return;

    input.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            const mentionPopup = document.getElementById('mention-popup');
            if (mentionPopup && !mentionPopup.classList.contains('hidden')) {
                const active = mentionPopup.querySelector('.mention-item.active');
                if (active) {
                    active.click();
                    event.preventDefault();
                    return;
                }
            }
            event.preventDefault();
            handleSend();
        }

        if (event.key === 'ArrowDown') {
            const mentionPopup = document.getElementById('mention-popup');
            if (mentionPopup && !mentionPopup.classList.contains('hidden')) {
                event.preventDefault();
                UI.navigateMention('down');
            }
        }

        if (event.key === 'ArrowUp') {
            const mentionPopup = document.getElementById('mention-popup');
            if (mentionPopup && !mentionPopup.classList.contains('hidden')) {
                event.preventDefault();
                UI.navigateMention('up');
            }
        }

        if (event.key === 'Escape') {
            UI.hideMentionPopup();
        }
    });

    input.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = `${this.scrollHeight}px`;

        if (UI.isWorking) return;

        const value = this.value;
        const cursor = this.selectionStart;
        const textBeforeCursor = value.substring(0, cursor);
        const words = textBeforeCursor.split(/\s+/);
        const lastWord = words[words.length - 1];

        if (lastWord.startsWith('@')) {
            const query = lastWord.substring(1).toLowerCase();
            const filtered = workspaceFiles.filter((file) => (
                file.name.toLowerCase().includes(query) ||
                file.path.toLowerCase().includes(query)
            )).slice(0, 10);

            if (filtered.length > 0) {
                UI.showMentionPopup(filtered, (file) => {
                    const beforeMention = textBeforeCursor.substring(0, textBeforeCursor.length - lastWord.length);
                    const afterMention = value.substring(cursor);
                    input.value = `${beforeMention}@${file.name} ${afterMention}`;
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
