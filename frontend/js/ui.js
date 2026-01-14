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
            // Simple double-check for duplicates if needed
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
                previewItem.innerHTML = `
                    <span class="material-symbols-outlined file-icon">description</span>
                `;
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

    addMessage(text, role, images = [], attachedFiles = [], toolOutputs = []) {
        if (!this.elements.chatHistory) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';

        // Render attached files if any
        if (attachedFiles && attachedFiles.length > 0) {
            const fileContainer = document.createElement('div');
            fileContainer.className = 'file-previews-container';
            attachedFiles.forEach(file => {
                const isFileObj = file instanceof File;
                const isImage = isFileObj && file.type.startsWith('image/');
                const fileName = isFileObj ? file.name : (file.name || 'document');

                const chip = document.createElement('div');
                chip.className = 'file-chip';

                if (isImage) {
                    const img = document.createElement('img');
                    img.src = URL.createObjectURL(file);
                    img.style.width = '24px';
                    img.style.height = '24px';
                    img.style.objectFit = 'cover';
                    img.style.borderRadius = '4px';
                    img.style.marginRight = '6px';
                    chip.appendChild(img);
                    const span = document.createElement('span');
                    span.textContent = fileName;
                    chip.appendChild(span);
                } else {
                    chip.innerHTML = `
                        <span class="material-symbols-outlined">description</span>
                        <span>${fileName}</span>
                    `;
                }
                fileContainer.appendChild(chip);
            });
            bubbleDiv.appendChild(fileContainer);
        }

        // Render text
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';

        if (role === 'user') {
            // User messages: No formatting, simple text with "Show More" if too long
            const escaped = this.escapeHtml(text);
            textDiv.innerHTML = `<span class="user-text-content">${escaped}</span>`;

            // Wait for a tick to check overflow
            setTimeout(() => {
                if (textDiv.scrollHeight > 120) {
                    textDiv.classList.add('collapsible');
                    const expandBtn = document.createElement('button');
                    expandBtn.className = 'btn-expand-message';
                    expandBtn.innerHTML = 'Show More <span class="material-symbols-outlined">expand_more</span>';
                    expandBtn.onclick = () => {
                        textDiv.classList.toggle('expanded');
                        expandBtn.innerHTML = textDiv.classList.contains('expanded')
                            ? 'Show Less <span class="material-symbols-outlined">expand_less</span>'
                            : 'Show More <span class="material-symbols-outlined">expand_more</span>';
                    };
                    textDiv.after(expandBtn);
                }
            }, 0);
        } else {
            // AI messages: Full Markdown
            textDiv.innerHTML = marked.parse(text);
        }
        bubbleDiv.appendChild(textDiv);

        // Render tool outputs if any (for AI messages)
        if (toolOutputs && toolOutputs.length > 0) {
            toolOutputs.forEach(output => {
                const toolPill = document.createElement('div');
                toolPill.className = 'tool-pill';

                const toolConfig = {
                    'read_file': { icon: 'visibility', label: 'Read' },
                    'write_file': { icon: 'edit', label: 'Write' },
                    'patch_file': { icon: 'build', label: 'Patch' },
                    'list_dir': { icon: 'folder', label: 'List' },
                    'get_file_tree': { icon: 'account_tree', label: 'Tree' },
                    'search_files': { icon: 'search', label: 'Search' },
                    'grep_search': { icon: 'manage_search', label: 'Grep' },
                    'run_command': { icon: 'terminal', label: 'Run' },
                    'delete_path': { icon: 'delete', label: 'Delete' }
                };

                const config = toolConfig[output.tool] || { icon: 'terminal', label: output.tool };

                let argsSummary = '';
                if (output.args) {
                    if (output.args.path) argsSummary = output.args.path;
                    else if (output.args.query) argsSummary = `query="${output.args.query}"`;
                    else if (output.args.pattern) argsSummary = `pattern="${output.args.pattern}"`;
                    else if (output.args.command) argsSummary = output.args.command;
                    else argsSummary = Object.values(output.args).join(', ');
                }

                toolPill.innerHTML = `
                    <div class="tool-pill-header">
                        <span class="material-symbols-outlined tool-pill-icon">${config.icon}</span>
                        <span class="tool-pill-name">${config.label}</span>
                        <span class="tool-pill-args">${argsSummary}</span>
                        <span class="material-symbols-outlined tool-pill-chevron">expand_more</span>
                    </div>
                    <div class="tool-pill-result">
                        <pre>${this.escapeHtml(output.result)}</pre>
                    </div>
                `;

                const header = toolPill.querySelector('.tool-pill-header');
                header.addEventListener('click', () => {
                    toolPill.classList.toggle('expanded');
                });

                bubbleDiv.appendChild(toolPill);
            });
        }

        // Apply code highlighting for AI messages
        if (role === 'ai') {
            bubbleDiv.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        }

        // Add generated images if any
        if (images && images.length > 0) {
            const imgContainer = document.createElement('div');
            imgContainer.className = 'generated-images';
            images.forEach(url => {
                const img = document.createElement('img');
                img.src = url;
                img.onclick = () => this.openImageModal(url);
                imgContainer.appendChild(img);
            });
            bubbleDiv.appendChild(imgContainer);
        }

        messageDiv.appendChild(bubbleDiv);
        this.elements.chatHistoryWrapper.appendChild(messageDiv);
        this.scrollToBottom();
    },

    handleStreamChunk(chunk) {
        this.hideLoading();

        let lastMsg = this.elements.chatHistoryWrapper.lastElementChild;

        // Ensure we have an AI message to append to
        if (!lastMsg || !lastMsg.classList.contains('ai')) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ai streaming';
            const bubbleDiv = document.createElement('div');
            bubbleDiv.className = 'message-bubble';
            messageDiv.appendChild(bubbleDiv);
            this.elements.chatHistoryWrapper.appendChild(messageDiv);
            lastMsg = messageDiv;
        }

        const bubble = lastMsg.querySelector('.message-bubble');

        // Get or create the current text segment
        let currentTextDiv = bubble.querySelector('.text-segment.active');
        if (!currentTextDiv) {
            currentTextDiv = document.createElement('div');
            currentTextDiv.className = 'message-text text-segment active';
            currentTextDiv.dataset.rawText = '';
            bubble.appendChild(currentTextDiv);
        }

        if (chunk.text) {
            // Append text to current segment
            const newText = (currentTextDiv.dataset.rawText || '') + chunk.text;
            currentTextDiv.dataset.rawText = newText;
            currentTextDiv.innerHTML = marked.parse(newText);

            // Re-highlight codes
            currentTextDiv.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        }

        if (chunk.tool_call) {
            // Finalize the current text segment
            if (currentTextDiv) {
                currentTextDiv.classList.remove('active');
            }

            // Create tool pill
            const toolPill = document.createElement('div');
            toolPill.className = 'tool-pill executing';
            toolPill.id = `tool-${Date.now()}`;

            const toolConfig = {
                'read_file': { icon: 'visibility', label: 'Reading', verb: 'Read' },
                'write_file': { icon: 'edit', label: 'Writing', verb: 'Wrote' },
                'patch_file': { icon: 'build', label: 'Patching', verb: 'Patched' },
                'list_dir': { icon: 'folder', label: 'Listing', verb: 'Listed' },
                'get_file_tree': { icon: 'account_tree', label: 'Exploring', verb: 'Explored' },
                'search_files': { icon: 'search', label: 'Searching', verb: 'Searched' },
                'grep_search': { icon: 'manage_search', label: 'Searching', verb: 'Searched' },
                'run_command': { icon: 'terminal', label: 'Running', verb: 'Ran' },
                'delete_path': { icon: 'delete', label: 'Deleting', verb: 'Deleted' }
            };

            const config = toolConfig[chunk.tool_call.name] || { icon: 'code', label: chunk.tool_call.name, verb: 'Called' };

            let argsSummary = '';
            if (chunk.tool_call.args) {
                if (chunk.tool_call.args.path) argsSummary = chunk.tool_call.args.path;
                else if (chunk.tool_call.args.command) argsSummary = chunk.tool_call.args.command;
                else if (chunk.tool_call.args.query) argsSummary = `"${chunk.tool_call.args.query}"`;
                else if (chunk.tool_call.args.pattern) argsSummary = chunk.tool_call.args.pattern;
                else argsSummary = JSON.stringify(chunk.tool_call.args).slice(0, 50);
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
                    <div class="tool-result-loading">
                        <div class="loading-dots"><span></span><span></span><span></span></div>
                    </div>
                </div>
            `;

            bubble.appendChild(toolPill);
            lastMsg.dataset.currentToolId = toolPill.id;
            lastMsg.dataset.currentToolConfig = JSON.stringify(config);

            // Attach expand listener
            toolPill.querySelector('.tool-pill-header').addEventListener('click', () => {
                toolPill.classList.toggle('expanded');
            });
        }

        if (chunk.tool_result) {
            const toolId = lastMsg.dataset.currentToolId;
            const toolPill = document.getElementById(toolId);
            const config = JSON.parse(lastMsg.dataset.currentToolConfig || '{}');

            if (toolPill) {
                toolPill.classList.remove('executing');
                toolPill.classList.add('completed');

                // Update icon and label
                const iconEl = toolPill.querySelector('.tool-pill-icon');
                iconEl.classList.remove('rotating');
                iconEl.textContent = 'check_circle';

                const labelEl = toolPill.querySelector('.tool-pill-label');
                labelEl.textContent = config.verb || 'Done';

                // Populate result
                const resultDiv = toolPill.querySelector('.tool-pill-result');
                resultDiv.innerHTML = `<pre>${this.escapeHtml(chunk.tool_result)}</pre>`;
                
                // If it was a write or patch to plan.md, refresh the plan UI
                if (typeof refreshPlan === 'function') {
                    refreshPlan();
                }
            }

            // Create a new text segment for content after tool call
            const newTextDiv = document.createElement('div');
            newTextDiv.className = 'message-text text-segment active';
            newTextDiv.dataset.rawText = '';
            bubble.appendChild(newTextDiv);
        }

        if (chunk.images && chunk.images.length > 0) {
            let imgContainer = bubble.querySelector('.generated-images');
            if (!imgContainer) {
                imgContainer = document.createElement('div');
                imgContainer.className = 'generated-images';
                bubble.appendChild(imgContainer);
            }
            chunk.images.forEach(url => {
                const img = document.createElement('img');
                img.src = url;
                img.onclick = () => this.openImageModal(url);
                imgContainer.appendChild(img);
            });
        }

        if (chunk.is_final) {
            lastMsg.classList.remove('streaming');
        }

        this.scrollToBottom();
    },

    updateStatus(text, type) {
        const loadingDiv = document.getElementById('ai-loading');
        if (!loadingDiv) return;

        const bubble = loadingDiv.querySelector('.message-bubble');
        if (text) {
            bubble.innerHTML = `
                <div class="status-indicator ${type}">
                    <span class="material-symbols-outlined ${type === 'tool' ? 'rotating' : 'pulse'}">
                        ${type === 'tool' ? 'settings' : 'brain'}
                    </span>
                    <span>${text}</span>
                </div>
            `;
        } else {
            bubble.innerHTML = `<div class="loading-dots"><span></span><span></span><span></span></div>`;
        }
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
        loadingDiv.innerHTML = `
            <div class="message-bubble">
                <div class="loading-dots"><span></span><span></span><span></span></div>
            </div>
        `;
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
            groupDiv.innerHTML = `
                <div class="sidebar-group-title">
                    <span class="material-symbols-outlined icon">folder</span>
                    <span>${ws.name}</span>
                </div>
            `;

            sessions.forEach(s => {
                const item = document.createElement('div');
                item.className = `nav-item sidebar-session-item ${s.id === currentSessionId ? 'active' : ''}`;
                item.innerHTML = `
                    <span class="name">${s.title || 'Untitled'}</span>
                    <div class="nav-actions">
                        <button class="btn-item-action delete-session" title="Delete session">
                            <span class="material-symbols-outlined">delete</span>
                        </button>
                    </div>
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
        newSessItem.innerHTML = `
            <div class="item-info"><div class="item-title">New Session</div></div>
            <span class="material-symbols-outlined">add</span>
        `;
        newSessItem.onclick = () => { onNew(currentWorkspaceId); menu.classList.add('hidden'); };
        menu.appendChild(newSessItem);

        sessions.forEach(s => {
            const item = document.createElement('div');
            item.className = `dropdown-item ${s.id === currentSessionId ? 'active' : ''}`;
            item.innerHTML = `
                <div class="item-info">
                    <div class="item-title">${s.title || 'Untitled'}</div>
                    <div class="item-meta">${new Date(s.created_at * 1000).toLocaleString()}</div>
                </div>
            `;
            item.onclick = () => { onSelect(s); menu.classList.add('hidden'); };
            menu.appendChild(item);
        });
    },

    toggleExplorer() {
        const sidebar = document.getElementById('explorer-sidebar');
        const resizer = document.getElementById('explorer-resizer');
        if (sidebar) {
            const isHidden = sidebar.classList.toggle('hidden');
            if (!isHidden) this.hidePlan(); // Hide plan if explorer is shown
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
            if (!isHidden) this.hideExplorer(); // Hide explorer if plan is shown
        }
    },

    hidePlan() {
        const sidebar = document.getElementById('plan-sidebar');
        if (sidebar) sidebar.classList.add('hidden');
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

            item.innerHTML = `
                ${arrow}
                <span class="material-symbols-outlined icon">${icon}</span>
                <span class="name">${node.name}</span>
            `;

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

        // If root is directory and has children, render its children instead of the root itself for better view
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
