const UI = {
    elements: {
        sidebar: document.querySelector('.sidebar'),
        mainContent: document.querySelector('.main-content'),
        toggleSidebarBtn: document.getElementById('toggle-sidebar'),
        homeDashboard: document.getElementById('home-dashboard'),
        workspaceView: document.getElementById('workspace-view'),
        chatHistory: document.getElementById('chat-history'),
        chatHistoryWrapper: document.querySelector('.messages-wrapper'),
        chatInput: document.getElementById('message-input'),
        sendBtn: document.getElementById('btn-send'),
        fileInput: document.getElementById('file-input'),
        attachBtn: document.getElementById('btn-attach'),
        mentionPopup: document.getElementById('mention-popup'),
        taggedFilesContainer: document.getElementById('tagged-files-container'),
        uploadPreviewsContainer: document.getElementById('upload-previews-container'),
    },

    taggedFiles: [], // Array of { name, path }
    uploadedFiles: [], // Array of File objects

    addUploadedFiles(files) {
        Array.from(files).forEach(file => {
            this.uploadedFiles.push(file);
        });
        this.renderUploadedFiles();
    },

    removeUploadedFile(index) {
        this.uploadedFiles.splice(index, 1);
        this.renderUploadedFiles();
    },

    clearUploadedFiles() {
        this.uploadedFiles = [];
        this.renderUploadedFiles();
    },

    renderUploadedFiles() {
        if (!this.elements.uploadPreviewsContainer) return;
        if (this.uploadedFiles.length === 0) {
            this.elements.uploadPreviewsContainer.classList.add('hidden');
            return;
        }
        this.elements.uploadPreviewsContainer.classList.remove('hidden');
        this.elements.uploadPreviewsContainer.innerHTML = '';
        this.uploadedFiles.forEach((file, index) => {
            const previewItem = document.createElement('div');
            previewItem.className = 'preview-item';
            const isImage = file.type.startsWith('image/');
            if (isImage) {
                const img = document.createElement('img');
                img.src = URL.createObjectURL(file); // Note: Should ideally revoke this later
                previewItem.appendChild(img);
            } else {
                previewItem.innerHTML = `<span class="material-symbols-outlined file-icon">description</span>`;
            }
            previewItem.innerHTML += `
                <div class="remove-btn" onclick="UI.removeUploadedFile(${index})">
                    <span class="material-symbols-outlined" style="font-size: 14px;">close</span>
                </div>
                <div class="file-name">${file.name}</div>
            `;
            this.elements.uploadPreviewsContainer.appendChild(previewItem);
        });
    },

    addTaggedFile(file) {
        // Prevent duplicates
        if (this.taggedFiles.find(f => f.path === file.path)) return;

        this.taggedFiles.push(file);
        this.renderTaggedFiles();
    },

    removeTaggedFile(path) {
        this.taggedFiles = this.taggedFiles.filter(f => f.path !== path);
        this.renderTaggedFiles();
    },

    clearTaggedFiles() {
        this.taggedFiles = [];
        this.renderTaggedFiles();
    },

    renderTaggedFiles() {
        if (!this.elements.taggedFilesContainer) return;

        if (this.taggedFiles.length === 0) {
            this.elements.taggedFilesContainer.classList.add('hidden');
            return;
        }

        this.elements.taggedFilesContainer.classList.remove('hidden');
        this.elements.taggedFilesContainer.innerHTML = '';

        this.taggedFiles.forEach(file => {
            const chip = document.createElement('div');
            chip.className = 'file-chip';
            chip.innerHTML = `
                <span class="material-symbols-outlined">description</span>
                <span>${file.name}</span>
                <span class="material-symbols-outlined remove-btn" onclick="UI.removeTaggedFile('${file.path.replace(/\\/g, '\\\\')}')">close</span>
            `;
            this.elements.taggedFilesContainer.appendChild(chip);
        });
    },

    showMentionPopup(files, onSelect) {
        if (!this.elements.mentionPopup) return;

        this.elements.mentionPopup.classList.remove('hidden');
        this.elements.mentionPopup.innerHTML = '';

        if (files.length === 0) {
            this.elements.mentionPopup.innerHTML = '<div class="mention-item">No files found</div>';
            return;
        }

        files.forEach((file, index) => {
            const item = document.createElement('div');
            item.className = 'mention-item';
            if (index === 0) item.classList.add('active'); // Focus first item

            item.innerHTML = `
                <span class="material-symbols-outlined icon">description</span>
                <span class="name">${file.name}</span>
                <span class="path">${file.path}</span>
            `;

            item.onclick = (e) => {
                e.stopPropagation();
                onSelect(file);
                this.hideMentionPopup();
            };

            this.elements.mentionPopup.appendChild(item);
        });
    },

    hideMentionPopup() {
        if (this.elements.mentionPopup) {
            this.elements.mentionPopup.classList.add('hidden');
        }
    },

    navigateMention(direction) {
        if (!this.elements.mentionPopup || this.elements.mentionPopup.classList.contains('hidden')) return;

        const items = Array.from(this.elements.mentionPopup.querySelectorAll('.mention-item'));
        if (items.length === 0) return;

        let activeIndex = items.findIndex(item => item.classList.contains('active'));

        items[activeIndex].classList.remove('active');

        if (direction === 'up') {
            activeIndex = (activeIndex - 1 + items.length) % items.length;
        } else {
            activeIndex = (activeIndex + 1) % items.length;
        }

        const nextActive = items[activeIndex];
        nextActive.classList.add('active');
        nextActive.scrollIntoView({ block: 'nearest' });
    },

    initInputAutoResize() {
        if (!this.elements.chatInput) return;
        this.elements.chatInput.addEventListener('input', () => {
            this.elements.chatInput.style.height = 'auto';
            this.elements.chatInput.style.height = (this.elements.chatInput.scrollHeight) + 'px';

            if (this.elements.chatInput.value.trim().length > 0) {
                this.elements.sendBtn.classList.add('active');
            } else {
                this.elements.sendBtn.classList.remove('active');
            }
        });
    },

    addMessage(textOrParts, role, images = [], attachedFiles = [], legacyToolOutputs = []) {
        if (!this.elements.chatHistory) return;
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';
        messageDiv.appendChild(bubbleDiv);

        let parts = [];
        if (Array.isArray(textOrParts)) {
            parts = textOrParts;
        } else {
            if (role === 'user') {
                parts.push({ type: 'text', content: textOrParts });
            } else {
                parts.push({ type: 'text', content: textOrParts });
                if (legacyToolOutputs && legacyToolOutputs.length > 0) {
                    legacyToolOutputs.forEach(out => {
                        parts.push({ type: 'tool_call', content: { name: out.tool, args: out.args } });
                        parts.push({ type: 'tool_result', content: out.result });
                    });
                }
            }
        }

        if (attachedFiles && attachedFiles.length > 0) {
            this._renderAttachedFiles(bubbleDiv, attachedFiles);
        }

        parts.forEach(part => {
            this._renderPart(bubbleDiv, part, role);
        });

        if (images && images.length > 0) {
            this._renderImages(bubbleDiv, images);
        }

        this.elements.chatHistoryWrapper.appendChild(messageDiv);
        this.scrollToBottom();
        return messageDiv;
    },

    _renderPart(container, part, role) {
        if (part.type === 'text') {
            const textDiv = document.createElement('div');
            textDiv.className = 'message-text';
            if (role === 'user') {
                textDiv.innerHTML = `<span class="user-text-content">${this.escapeHtml(part.content)}</span>`;
            } else {
                textDiv.innerHTML = marked.parse(part.content);
                textDiv.querySelectorAll('pre code').forEach(block => hljs.highlightElement(block));
            }
            container.appendChild(textDiv);
        } else if (part.type === 'thought') {
            const thoughtDiv = document.createElement('div');
            thoughtDiv.className = 'thought-block';
            thoughtDiv.innerHTML = `
                <div class="thought-header">
                    <span class="material-symbols-outlined">psychology</span>
                    <span>Thought Process</span>
                    <span class="material-symbols-outlined chevron">expand_more</span>
                </div>
                <div class="thought-content">${marked.parse(part.content)}</div>
            `;
            thoughtDiv.querySelector('.thought-header').onclick = () => thoughtDiv.classList.toggle('expanded');
            container.appendChild(thoughtDiv);
        } else if (part.type === 'tool_call') {
            const toolPill = this._createToolPill(part.content);
            toolPill.classList.add('completed');
            toolPill.querySelector('.tool-pill-icon').textContent = 'check_circle';
            toolPill.querySelector('.tool-pill-label').textContent = 'Called';
            container.appendChild(toolPill);
        } else if (part.type === 'tool_result') {
            const lastPill = container.querySelector('.tool-pill:last-of-type');
            if (lastPill) {
                const resultDiv = lastPill.querySelector('.tool-pill-result');
                resultDiv.innerHTML = `<pre>${this.escapeHtml(part.content)}</pre>`;
            }
        }
    },

    _createToolPill(toolCall) {
        const toolPill = document.createElement('div');
        toolPill.className = 'tool-pill';
        const toolConfig = {
            'read_file': { icon: 'visibility', label: 'Reading', verb: 'Read' },
            'write_file': { icon: 'edit', label: 'Writing', verb: 'Wrote' },
            'patch_file': { icon: 'build', label: 'Patching', verb: 'Patched' },
            'list_dir': { icon: 'folder', label: 'Listing', verb: 'Listed' },
            'get_file_tree': { icon: 'account_tree', label: 'Exploring', verb: 'Explored' },
            'search_files': { icon: 'search', label: 'Searching', verb: 'Searched' },
            'grep_search': { icon: 'manage_search', label: 'Searching', verb: 'Searched' },
            'run_command': { icon: 'terminal', label: 'Running', verb: 'Ran' },
            'delete_path': { icon: 'delete', label: 'Deleting', verb: 'Deleted' },
            'web_search': { icon: 'search', label: 'Searching', verb: 'Searched' },
            'web_browse': { icon: 'language', label: 'Browsing', verb: 'Browsed' },
            'delegate_task': { icon: 'groups', label: 'Delegating', verb: 'Delegated' },
            'get_symbol_info': { icon: 'info', label: 'Informing', verb: 'Informed' }
        };
        const config = toolConfig[toolCall.name] || { icon: 'code', label: toolCall.name, verb: 'Called' };
        let argsSummary = '';
        if (toolCall.args) {
            argsSummary = toolCall.args.path || toolCall.args.command || toolCall.args.query || toolCall.args.task || JSON.stringify(toolCall.args).slice(0, 50);
        }
        toolPill.innerHTML = `
            <div class="tool-pill-header">
                <div class="tool-pill-status">
                    <span class="material-symbols-outlined tool-pill-icon rotating">${config.icon}</span>
                    <span class="tool-pill-label">${config.label}</span>
                </div>
                <span class="tool-pill-target">${this.escapeHtml(argsSummary)}</span>
                <span class="material-symbols-outlined tool-pill-chevron">expand_more</span>
            </div>
            <div class="tool-pill-result">
                <div class="tool-result-loading"><div class="loading-dots"><span></span><span></span><span></span></div></div>
            </div>
        `;
        toolPill.querySelector('.tool-pill-header').onclick = () => toolPill.classList.toggle('expanded');
        return toolPill;
    },

    handleStreamChunk(chunk) {
        this.hideLoading();
        this.showWorkingIndicator();
        let lastMsg = this.elements.chatHistoryWrapper.lastElementChild;
        if (!lastMsg || !lastMsg.classList.contains('ai')) {
            lastMsg = this.addMessage([], 'ai');
        }
        const bubble = lastMsg.querySelector('.message-bubble');

        if (chunk.thought) {
            this._renderPart(bubble, { type: 'thought', content: chunk.thought }, 'ai');
        }
        if (chunk.text) {
            let activeText = bubble.querySelector('.message-text.active');
            if (!activeText) {
                activeText = document.createElement('div');
                activeText.className = 'message-text active';
                activeText.dataset.raw = '';
                bubble.appendChild(activeText);
            }
            activeText.dataset.raw += chunk.text;
            activeText.innerHTML = marked.parse(activeText.dataset.raw);
            activeText.querySelectorAll('pre code').forEach(block => hljs.highlightElement(block));
        }
        if (chunk.tool_call) {
            bubble.querySelectorAll('.message-text.active').forEach(el => el.classList.remove('active'));
            const toolPill = this._createToolPill(chunk.tool_call);
            toolPill.classList.add('executing');
            toolPill.id = `tool-${Date.now()}`;
            bubble.appendChild(toolPill);
            lastMsg.dataset.currentToolId = toolPill.id;
        }
        if (chunk.tool_result) {
            const toolPill = document.getElementById(lastMsg.dataset.currentToolId);
            if (toolPill) {
                toolPill.classList.remove('executing');
                toolPill.classList.add('completed');
                toolPill.querySelector('.tool-pill-icon').classList.remove('rotating');
                toolPill.querySelector('.tool-pill-icon').textContent = 'check_circle';
                toolPill.querySelector('.tool-pill-label').textContent = 'Done';
                toolPill.querySelector('.tool-pill-result').innerHTML = `<pre>${this.escapeHtml(chunk.tool_result)}</pre>`;
            }
            if (typeof refreshPlan === 'function') refreshPlan();
        }
        if (chunk.images) {
            this._renderImages(bubble, chunk.images);
        }
        if (chunk.is_final) {
            bubble.querySelectorAll('.message-text.active').forEach(el => el.classList.remove('active'));
            this.hideWorkingIndicator();
        }
        this.scrollToBottom();
    },

    showWorkingIndicator() {
        let indicator = document.getElementById('working-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'working-indicator';
            indicator.className = 'working-indicator';
            indicator.innerHTML = `
                <div class="working-content">
                    <span class="material-symbols-outlined rotating">sync</span>
                    <span>Agent is working...</span>
                    <button id="btn-stop-agent" class="btn-stop">
                        <span class="material-symbols-outlined">stop_circle</span> Stop
                    </button>
                </div>
            `;
            document.body.appendChild(indicator);
            document.getElementById('btn-stop-agent').onclick = () => {
                if (typeof currentSessionId !== 'undefined') {
                    API.interruptChat(currentSessionId);
                }
            };
        }
        indicator.classList.remove('hidden');
    },

    hideWorkingIndicator() {
        const indicator = document.getElementById('working-indicator');
        if (indicator) indicator.classList.add('hidden');
    },

    _renderImages(container, images) {
        let imgContainer = container.querySelector('.generated-images');
        if (!imgContainer) {
            imgContainer = document.createElement('div');
            imgContainer.className = 'generated-images';
            container.appendChild(imgContainer);
        }
        images.forEach(url => {
            const img = document.createElement('img');
            img.src = url;
            img.onclick = () => this.openImageModal(url);
            imgContainer.appendChild(img);
        });
    },

    _renderAttachedFiles(container, files) {
        const fileContainer = document.createElement('div');
        fileContainer.className = 'file-previews-container';
        files.forEach(file => {
            const isFileObj = file instanceof File;
            const fileName = isFileObj ? file.name : (file.name || 'document');
            const chip = document.createElement('div');
            chip.className = 'file-chip';
            chip.innerHTML = `<span class="material-symbols-outlined">description</span><span>${fileName}</span>`;
            fileContainer.appendChild(chip);
        });
        container.appendChild(fileContainer);
    },

    scrollToBottom() {
        if (this.elements.chatHistory) {
            this.elements.chatHistory.scrollTop = this.elements.chatHistory.scrollHeight;
        }
    },

    showLoading() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message ai loading';
        loadingDiv.id = 'ai-loading';
        loadingDiv.innerHTML = `<div class="message-bubble"><div class="loading-dots"><span></span><span></span><span></span></div></div>`;
        this.elements.chatHistoryWrapper.appendChild(loadingDiv);
        this.scrollToBottom();
    },

    hideLoading() {
        const loadingDiv = document.getElementById('ai-loading');
        if (loadingDiv) loadingDiv.remove();
    },

    renderSidebarSessions(workspaces, allSessions, currentSessionId, onSelect, onDelete) {
        const list = document.getElementById('sidebar-sessions-list');
        if (!list) return;
        list.innerHTML = '';
        const grouped = {};
        allSessions.forEach(s => {
            if (!grouped[s.workspace_id]) grouped[s.workspace_id] = [];
            grouped[s.workspace_id].push(s);
        });
        Object.entries(workspaces).forEach(([wsId, ws]) => {
            const sessions = grouped[wsId] || [];
            if (sessions.length === 0) return;
            const groupDiv = document.createElement('div');
            groupDiv.innerHTML = `<div class="sidebar-group-title"><span class="material-symbols-outlined icon">folder</span><span>${ws.name}</span></div>`;
            sessions.forEach(s => {
                const item = document.createElement('div');
                item.className = `nav-item sidebar-session-item ${s.id === currentSessionId ? 'active' : ''}`;
                item.innerHTML = `
                    <span class="name">${s.title || 'Untitled'}</span>
                    <div class="nav-actions"><button class="btn-item-action delete-session" title="Delete session"><span class="material-symbols-outlined">delete</span></button></div>
                `;
                item.onclick = (e) => {
                    if (e.target.closest('.delete-session')) {
                        e.stopPropagation();
                        onDelete(s.id);
                        return;
                    }
                    onSelect(s);
                };
                groupDiv.appendChild(item);
            });
            list.appendChild(groupDiv);
        });
    },

    renderSessionDropdown(currentWorkspaceId, sessions, currentSessionId, onSelect, onNew) {
        const menu = document.getElementById('session-dropdown-menu');
        if (!menu) return;
        menu.innerHTML = '';
        const newSessItem = document.createElement('div');
        newSessItem.className = 'dropdown-item';
        newSessItem.innerHTML = `<div class="item-info"><div class="item-title">New Session</div></div><span class="material-symbols-outlined">add</span>`;
        newSessItem.onclick = () => { onNew(currentWorkspaceId); menu.classList.add('hidden'); };
        menu.appendChild(newSessItem);
        sessions.forEach(s => {
            const item = document.createElement('div');
            item.className = `dropdown-item ${s.id === currentSessionId ? 'active' : ''}`;
            item.innerHTML = `<div class="item-info"><div class="item-title">${s.title || 'Untitled'}</div><div class="item-meta">${new Date(s.created_at * 1000).toLocaleString()}</div></div>`;
            item.onclick = () => { onSelect(s); menu.classList.add('hidden'); };
            menu.appendChild(item);
        });
    },

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
    },

    renderGit(data, onBranchClick) {
        const container = document.getElementById('git-repo-status');
        const branchesList = document.getElementById('git-branches-list');
        const logList = document.getElementById('git-log-list');
        
        if (!data.is_repo) {
            container.innerHTML = '<div class="git-empty">No git repository detected.</div>';
            branchesList.innerHTML = '';
            logList.innerHTML = '';
            return;
        }

        container.innerHTML = `
            <div style="font-size: 12px; color: var(--text-primary); font-weight: 500;">Status</div>
            <pre style="font-size: 10px; margin-top: 4px; color: var(--text-secondary); background: rgba(0,0,0,0.2); padding: 8px; border-radius: 4px; border: 1px solid var(--border);">${this.escapeHtml(data.status || 'Clean')}</pre>
        `;

        branchesList.innerHTML = '';
        data.branches.forEach(b => {
            const item = document.createElement('div');
            item.className = `git-branch-item ${b.current ? 'active' : ''}`;
            item.innerHTML = `
                <span class="material-symbols-outlined" style="font-size: 14px;">${b.current ? 'radio_button_checked' : 'radio_button_unchecked'}</span>
                <span>${b.name}</span>
            `;
            if (!b.current) {
                item.onclick = () => onBranchClick(b.name);
            }
            branchesList.appendChild(item);
        });

        logList.innerHTML = `<div class="git-log-item">${this.escapeHtml(data.log)}</div>`;
    },

    renderPlan(content) {
        const container = document.getElementById('plan-content');
        if (!container) return;
        if (!content) {
            container.innerHTML = '<div class="plan-empty">No active plan found (plan.md)</div>';
            return;
        }
        container.innerHTML = marked.parse(content);
    },

    renderExplorer(data, onFileSelect) {
        const treeContainer = document.getElementById('explorer-tree');
        if (!treeContainer) return;
        treeContainer.innerHTML = '';
        if (data.error) {
            treeContainer.innerHTML = `<div class="explorer-error">${this.escapeHtml(data.error)}</div>`;
            return;
        }
        const getFileIcon = (fileName) => {
            const ext = fileName.split('.').pop().toLowerCase();
            const MAP = {
                'js': 'javascript', 'ts': 'typescript', 'py': 'python',
                'html': 'html', 'css': 'css', 'json': 'settings',
                'md': 'description', 'txt': 'description', 'png': 'image',
                'jpg': 'image', 'svg': 'image', 'pdf': 'picture_as_pdf'
            };
            return MAP[ext] || 'description';
        };
        const renderNode = (node) => {
            const container = document.createElement('div');
            container.className = 'tree-node';
            const item = document.createElement('div');
            item.className = `tree-item ${node.type}`;
            const icon = node.type === 'directory' ? 'folder' : getFileIcon(node.name);
            const arrow = node.type === 'directory' ? '<span class="material-symbols-outlined directory-icon">expand_more</span>' : '';
            item.innerHTML = `${arrow}<span class="material-symbols-outlined icon">${icon}</span><span class="name">${node.name}</span>`;
            container.appendChild(item);
            if (node.type === 'directory' && node.children) {
                const childrenContainer = document.createElement('div');
                childrenContainer.className = 'tree-item-children';
                node.children.forEach(child => {
                    childrenContainer.appendChild(renderNode(child));
                });
                container.appendChild(childrenContainer);
                item.onclick = (e) => {
                    e.stopPropagation();
                    container.classList.toggle('collapsed');
                };
            } else if (node.type === 'file') {
                item.onclick = (e) => {
                    e.stopPropagation();
                    if (onFileSelect) onFileSelect(node.path);
                };
            }
            return container;
        };
        if (data.type === 'directory' && data.children) {
            data.children.forEach(child => {
                treeContainer.appendChild(renderNode(child));
            });
        } else {
            treeContainer.appendChild(renderNode(data));
        }
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};