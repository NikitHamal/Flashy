// Chat Rendering Logic
Object.assign(UI, {
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
                const escaped = this.escapeHtml(part.content);
                textDiv.innerHTML = `<span class="user-text-content">${escaped}</span>`;
                container.appendChild(textDiv);

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
                const cleanedContent = part.content.replace(/https?:\/\/googleusercontent\.com\/youtube_content\/\d+/g, '');
                textDiv.innerHTML = marked.parse(cleanedContent);
                textDiv.querySelectorAll('pre code').forEach(block => hljs.highlightElement(block));
                this._embedMedia(textDiv);
                container.appendChild(textDiv);
            }
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
            container.appendChild(toolPill);
        } else if (part.type === 'tool_result') {
            const lastPill = container.querySelector('.tool-pill:last-of-type');
            if (lastPill) {
                this._updateToolResult(lastPill, part.content);
            }
        }
    },

    _createToolPill(toolCall) {
        const toolPill = document.createElement('div');
        toolPill.className = 'tool-pill';

        const toolMap = {
            'write_file': { icon: 'edit_document', label: 'Write File' },
            'read_file': { icon: 'visibility', label: 'Read File' },
            'patch_file': { icon: 'build', label: 'Patch File' },
            'run_shell_command': { icon: 'terminal', label: 'Run Command' },
            'list_directory': { icon: 'folder', label: 'List Dir' },
            'search_file_content': { icon: 'search', label: 'Search Files' },
            'delegate_to_agent': { icon: 'groups', label: 'Delegate' }
        };

        const info = toolMap[toolCall.name] || { icon: 'code', label: toolCall.name };

        let argsDisplay = '';
        if (toolCall.args) {
            argsDisplay = toolCall.args.file_path || toolCall.args.path || toolCall.args.command || toolCall.args.query || '...';
        }

        toolPill.innerHTML = `
            <div class="tool-pill-header">
                <div class="tool-icon-box ${toolCall.name}">
                    <span class="material-symbols-outlined" style="font-size: 16px;">${info.icon}</span>
                </div>
                <div class="tool-info">
                    <div class="tool-name">${info.label}</div>
                    <div class="tool-args">${this.escapeHtml(argsDisplay)}</div>
                </div>
                <div class="tool-stats"></div>
                <span class="material-symbols-outlined tool-pill-chevron">expand_more</span>
            </div>
            <div class="tool-pill-result">
                <div class="tool-result-loading"><div class="loading-dots"><span></span><span></span><span></span></div></div>
            </div>
        `;

        toolPill.querySelector('.tool-pill-header').onclick = () => toolPill.classList.toggle('expanded');
        return toolPill;
    },

    _updateToolResult(toolPill, content) {
        const resultDiv = toolPill.querySelector('.tool-pill-result');
        const statsDiv = toolPill.querySelector('.tool-stats');

        let htmlContent = '';
        let added = 0;
        let removed = 0;

        if (content.includes('<<<<') || content.includes('>>>>') || content.includes('--- ') || content.includes('+++ ')) {
            htmlContent = '<div class="diff-view">';
            const lines = content.split('\n');
            lines.forEach(line => {
                if (line.startsWith('+') && !line.startsWith('+++')) {
                    added++;
                    htmlContent += `<div class="diff-line added">${this.escapeHtml(line)}</div>`;
                } else if (line.startsWith('-') && !line.startsWith('---')) {
                    removed++;
                    htmlContent += `<div class="diff-line removed">${this.escapeHtml(line)}</div>`;
                } else if (line.startsWith('@@')) {
                    htmlContent += `<div class="diff-line header">${this.escapeHtml(line)}</div>`;
                } else {
                    htmlContent += `<div class="diff-line">${this.escapeHtml(line)}</div>`;
                }
            });
            htmlContent += '</div>';

            if (added > 0 || removed > 0) {
                statsDiv.innerHTML = `
                    ${added > 0 ? `<span class="stat-added">+${added}</span>` : ''}
                    ${removed > 0 ? `<span class="stat-removed">-${removed}</span>` : ''}
                `;
            }
        } else {
            htmlContent = `<pre>${this.escapeHtml(content)}</pre>`;
        }

        resultDiv.innerHTML = htmlContent;
        toolPill.classList.remove('executing');
        toolPill.classList.add('completed');
    },

    handleStreamChunk(chunk) {
        this.hideLoading();
        this.setAgentState('working');

        let lastMsg = this.elements.chatHistoryWrapper.lastElementChild;
        if (!lastMsg || !lastMsg.classList.contains('ai')) {
            lastMsg = this.addMessage([], 'ai');
        }

        const bubble = lastMsg.querySelector('.message-bubble');
        let dots = bubble.querySelector('.loading-dots-container');
        if (!dots) {
            dots = document.createElement('div');
            dots.className = 'loading-dots-container';
            dots.innerHTML = '<div class="loading-dots"><span></span><span></span><span></span></div>';
            bubble.appendChild(dots);
        }

        if (chunk.thought) {
            const thoughtPart = { type: 'thought', content: chunk.thought };
            const tempDiv = document.createElement('div');
            this._renderPart(tempDiv, thoughtPart, 'ai');
            dots.before(tempDiv.firstChild);
        }
        if (chunk.text) {
            let activeText = bubble.querySelector('.message-text.active');
            if (!activeText) {
                activeText = document.createElement('div');
                activeText.className = 'message-text active';
                activeText.dataset.raw = '';
                dots.before(activeText);
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
            dots.before(toolPill);
            lastMsg.dataset.currentToolId = toolPill.id;
        }
        if (chunk.tool_result) {
            const toolPill = document.getElementById(lastMsg.dataset.currentToolId);
            if (toolPill) {
                this._updateToolResult(toolPill, chunk.tool_result);
            }
            if (typeof refreshPlan === 'function') refreshPlan();
            if (typeof refreshGit === 'function') refreshGit();
        }
        if (chunk.images) {
            this._renderImages(bubble, chunk.images);
        }

        if (chunk.is_final) {
            bubble.querySelectorAll('.message-text.active').forEach(el => el.classList.remove('active'));
            this.setAgentState('idle');
            if (dots) dots.remove();
        }
        this.scrollToBottom();
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
            img.className = 'generated-image';
            img.onclick = () => window.open(url, '_blank');
            imgContainer.appendChild(img);
        });
    },

    _embedMedia(container) {
        const links = container.querySelectorAll('a');
        links.forEach(link => {
            const href = link.href;
            let videoId = null;

            try {
                if (href.includes('youtube.com/watch')) {
                    const urlObj = new URL(href);
                    videoId = urlObj.searchParams.get('v');
                } else if (href.includes('youtu.be/')) {
                    const urlObj = new URL(href);
                    videoId = urlObj.pathname.slice(1);
                }
            } catch (e) {
                console.warn('Error parsing video URL:', href);
            }

            if (videoId) {
                const embedDiv = document.createElement('div');
                embedDiv.className = 'media-embed youtube-embed';
                embedDiv.style.marginTop = '10px';
                embedDiv.style.marginBottom = '10px';
                embedDiv.style.borderRadius = '8px';
                embedDiv.style.overflow = 'hidden';
                embedDiv.innerHTML = `
                    <iframe 
                        width="100%" 
                        height="300" 
                        src="https://www.youtube.com/embed/${videoId}" 
                        title="YouTube video player" 
                        frameborder="0" 
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                        allowfullscreen>
                    </iframe>
                `;

                const parentP = link.closest('p');
                if (parentP) {
                    parentP.after(embedDiv);
                } else {
                    link.parentElement.appendChild(embedDiv);
                }
            }
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
                img.src = URL.createObjectURL(file);
                previewItem.appendChild(img);
            } else {
                const icon = document.createElement('span');
                icon.className = 'material-symbols-outlined file-icon';
                icon.textContent = 'description';
                previewItem.appendChild(icon);
            }

            const removeBtn = document.createElement('div');
            removeBtn.className = 'remove-btn';
            removeBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size: 14px;">close</span>';
            removeBtn.onclick = () => this.removeUploadedFile(index);

            const nameLabel = document.createElement('div');
            nameLabel.className = 'file-name';
            nameLabel.textContent = file.name;

            previewItem.appendChild(removeBtn);
            previewItem.appendChild(nameLabel);

            this.elements.uploadPreviewsContainer.appendChild(previewItem);
        });
    },

    addTaggedFile(file) {
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
            const icon = document.createElement('span');
            icon.className = 'material-symbols-outlined';
            icon.textContent = 'description';
            const name = document.createElement('span');
            name.textContent = file.name;
            const closeBtn = document.createElement('span');
            closeBtn.className = 'material-symbols-outlined remove-btn';
            closeBtn.textContent = 'close';
            closeBtn.onclick = () => UI.removeTaggedFile(file.path);
            chip.appendChild(icon);
            chip.appendChild(name);
            chip.appendChild(closeBtn);
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
            if (index === 0) item.classList.add('active');
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
        if (this.elements.mentionPopup) this.elements.mentionPopup.classList.add('hidden');
    },

    navigateMention(direction) {
        if (!this.elements.mentionPopup || this.elements.mentionPopup.classList.contains('hidden')) return;
        const items = Array.from(this.elements.mentionPopup.querySelectorAll('.mention-item'));
        if (items.length === 0) return;
        let activeIndex = items.findIndex(item => item.classList.contains('active'));
        items[activeIndex].classList.remove('active');
        if (direction === 'up') activeIndex = (activeIndex - 1 + items.length) % items.length;
        else activeIndex = (activeIndex + 1) % items.length;
        const nextActive = items[activeIndex];
        nextActive.classList.add('active');
        nextActive.scrollIntoView({ block: 'nearest' });
    },

    initInputAutoResize() {
        if (!this.elements.chatInput) return;
        this.elements.chatInput.addEventListener('input', () => {
            this.elements.chatInput.style.height = 'auto';
            this.elements.chatInput.style.height = (this.elements.chatInput.scrollHeight) + 'px';
            if (this.isWorking) return;
            if (this.elements.chatInput.value.trim().length > 0) this.elements.sendBtn.classList.add('active');
            else this.elements.sendBtn.classList.remove('active');
        });
    }
});
