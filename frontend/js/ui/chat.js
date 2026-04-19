// Chat Rendering Logic
Object.assign(UI, {
    addMessage(textOrParts, role, images = [], attachedFiles = [], legacyToolOutputs = []) {
        if (!this.elements.chatHistory) return;
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';
        messageDiv.appendChild(bubbleDiv);

        const parts = [];
        if (Array.isArray(textOrParts)) {
            parts.push(...textOrParts);
        } else {
            parts.push({ type: 'text', content: textOrParts });
            if (role !== 'user' && legacyToolOutputs && legacyToolOutputs.length > 0) {
                legacyToolOutputs.forEach((output) => {
                    parts.push({ type: 'tool_call', content: { name: output.tool, args: output.args } });
                    parts.push({ type: 'tool_result', content: output.result });
                });
            }
        }

        if (attachedFiles && attachedFiles.length > 0) {
            this._renderAttachedFiles(bubbleDiv, attachedFiles);
        }

        parts.forEach((part) => {
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
                textDiv.querySelectorAll('pre code').forEach((block) => hljs.highlightElement(block));
                this._embedMedia(textDiv);
                container.appendChild(textDiv);
            }
        } else if (part.type === 'thought') {
            const thoughtDiv = document.createElement('div');
            thoughtDiv.className = 'thought-block';
            thoughtDiv.innerHTML = `
                <div class="thought-header">
                    <span class="material-symbols-outlined">psychology</span>
                    <span class="thought-status">Thinking...</span>
                    <span class="material-symbols-outlined chevron">expand_more</span>
                </div>
                <div class="thought-content">${marked.parse(part.content)}</div>
            `;
            thoughtDiv.querySelector('.thought-header').onclick = () => thoughtDiv.classList.toggle('expanded');
            thoughtDiv.dataset.startTime = Date.now();
            container.appendChild(thoughtDiv);
        } else if (part.type === 'tool_call') {
            const toolPill = this._createToolPill(part.content);
            toolPill.classList.add('executing');
            container.appendChild(toolPill);
        } else if (part.type === 'tool_result') {
            const lastPill = container.querySelector('.tool-pill.executing:last-of-type');
            if (lastPill) {
                this._updateToolResult(lastPill, part.content);
            }
        }
    },

    _createToolPill(toolCall) {
        const toolPill = document.createElement('div');
        toolPill.className = 'tool-pill';

        const toolMap = {
            read_file: { icon: 'visibility', label: 'Read File' },
            read_files: { icon: 'library_books', label: 'Read Files' },
            write_file: { icon: 'edit_document', label: 'Write File' },
            write_files: { icon: 'file_copy', label: 'Write Files' },
            patch_file: { icon: 'build', label: 'Patch File' },
            apply_patch: { icon: 'difference', label: 'Apply Patch' },
            list_dir: { icon: 'folder', label: 'List Dir' },
            get_file_tree: { icon: 'account_tree', label: 'File Tree' },
            get_explorer_data: { icon: 'schema', label: 'Explorer Data' },
            search_files: { icon: 'find_in_page', label: 'Find Files' },
            grep_search: { icon: 'search', label: 'Grep Search' },
            run_command: { icon: 'terminal', label: 'Run Command' },
            delete_path: { icon: 'delete', label: 'Delete Path' },
            get_dependencies: { icon: 'inventory', label: 'Dependencies' },
            get_symbol_info: { icon: 'code', label: 'Symbol Info' },
            web_browse: { icon: 'travel_explore', label: 'Web Browse' },
            git_status: { icon: 'fact_check', label: 'Git Status' },
            git_commit: { icon: 'commit', label: 'Git Commit' },
            git_push: { icon: 'cloud_upload', label: 'Git Push' },
            git_pull: { icon: 'cloud_download', label: 'Git Pull' },
            git_branches: { icon: 'fork_right', label: 'Git Branches' },
            git_checkout: { icon: 'call_split', label: 'Git Checkout' },
            git_log: { icon: 'history', label: 'Git Log' },
            git_clone: { icon: 'download', label: 'Git Clone' },
            git_init: { icon: 'auto_fix_high', label: 'Git Init' },
            delegate_task: { icon: 'groups', label: 'Delegate' },
            generate_image: { icon: 'image', label: 'Generate Image' },
            save_image: { icon: 'save', label: 'Save Image' },
            save_generated_images: { icon: 'photo_library', label: 'Save Images' }
        };

        const info = toolMap[toolCall.name] || { icon: 'code', label: toolCall.name };
        let argsDisplay = '';
        if (toolCall.args) {
            argsDisplay = toolCall.args.path || toolCall.args.command || toolCall.args.query || toolCall.args.symbol_name || toolCall.args.url || '...';
            if (toolCall.args.paths && Array.isArray(toolCall.args.paths)) {
                argsDisplay = toolCall.args.paths.slice(0, 2).join(', ') + (toolCall.args.paths.length > 2 ? '…' : '');
            }
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
        const isShellCommand = toolPill.querySelector('.run_shell_command') !== null;

        let htmlContent = '';
        let added = 0;
        let removed = 0;

        if (isShellCommand) {
            htmlContent = `<div class="terminal-output-block"><pre><code>${this.escapeHtml(content)}</code></pre></div>`;
            resultDiv.style.backgroundColor = '#000';
            resultDiv.style.color = '#00ff00';
            resultDiv.style.padding = '10px';
            resultDiv.style.borderRadius = '0 0 4px 4px';
            resultDiv.style.fontFamily = "'Consolas', 'Courier New', monospace";
        } else if (content.includes('<<<<') || content.includes('>>>>') || content.includes('--- ') || content.includes('+++ ')) {
            htmlContent = '<div class="diff-view">';
            content.split('\n').forEach((line) => {
                if (line.startsWith('+') && !line.startsWith('+++')) {
                    added += 1;
                    htmlContent += `<div class="diff-line added">${this.escapeHtml(line)}</div>`;
                } else if (line.startsWith('-') && !line.startsWith('---')) {
                    removed += 1;
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
            let thoughtBlock = bubble.querySelector('.thought-block.active');
            if (!thoughtBlock) {
                thoughtBlock = document.createElement('div');
                thoughtBlock.className = 'thought-block active expanded';
                thoughtBlock.innerHTML = `
                    <div class="thought-header">
                        <span class="material-symbols-outlined">psychology</span>
                        <span>Thought Process</span>
                        <span class="material-symbols-outlined chevron">expand_more</span>
                    </div>
                    <div class="thought-content"></div>
                `;
                thoughtBlock.querySelector('.thought-header').onclick = () => thoughtBlock.classList.toggle('expanded');
                dots.before(thoughtBlock);
            }
            const contentDiv = thoughtBlock.querySelector('.thought-content');
            thoughtBlock.dataset.raw = `${thoughtBlock.dataset.raw || ''}${chunk.thought}`;
            contentDiv.innerHTML = marked.parse(thoughtBlock.dataset.raw);
        }

        if (chunk.text) {
            let activeText = bubble.querySelector('.message-text.active');
            if (!activeText) {
                bubble.querySelectorAll('.thought-block.active').forEach((element) => element.classList.remove('active'));
                activeText = document.createElement('div');
                activeText.className = 'message-text active';
                activeText.dataset.raw = '';
                dots.before(activeText);
            }
            activeText.dataset.raw += chunk.text;
            let displayRaw = activeText.dataset.raw;
            if (displayRaw.includes('```json')) {
                const beforeJson = displayRaw.split('```json')[0];
                displayRaw = beforeJson.trim() ? beforeJson : displayRaw;
            }
            activeText.innerHTML = marked.parse(displayRaw);
            activeText.querySelectorAll('pre code').forEach((block) => hljs.highlightElement(block));
        }

        if (chunk.tool_call) {
            bubble.querySelectorAll('.message-text.active, .thought-block.active').forEach((element) => element.classList.remove('active'));
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
            bubble.querySelectorAll('.message-text.active').forEach((element) => element.classList.remove('active'));
            bubble.querySelectorAll('.thought-block.active').forEach((element) => {
                element.classList.remove('active');
                const startTime = element.dataset.startTime;
                if (startTime) {
                    const elapsed = Math.round((Date.now() - parseInt(startTime, 10)) / 1000);
                    const status = element.querySelector('.thought-status');
                    if (status) status.textContent = `Thought for ${elapsed}s`;
                }
            });
            this.setAgentState('idle');
            if (dots) dots.remove();

            if (!bubble.textContent.trim() && (!chunk.images || !chunk.images.length) && !lastMsg.querySelector('.tool-pill') && !lastMsg.querySelector('.thought-block') && !lastMsg.querySelector('.generated-images')) {
                lastMsg.remove();
            }
        }

        this.scrollToBottom();
    },

    _renderImages(container, images) {
        let imageContainer = container.querySelector('.generated-images');
        if (!imageContainer) {
            imageContainer = document.createElement('div');
            imageContainer.className = 'generated-images';
            container.appendChild(imageContainer);
        }
        images.forEach((url) => {
            const img = document.createElement('img');
            img.src = url;
            img.className = 'generated-image';
            img.onclick = () => window.open(url, '_blank');
            imageContainer.appendChild(img);
        });
    },

    _embedMedia(container) {
        const links = container.querySelectorAll('a');
        links.forEach((link) => {
            const href = link.href;
            let videoId = null;

            try {
                if (href.includes('youtube.com/watch')) {
                    videoId = new URL(href).searchParams.get('v');
                } else if (href.includes('youtu.be/')) {
                    videoId = new URL(href).pathname.slice(1);
                }
            } catch (error) {
                console.warn('Error parsing video URL:', href, error);
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
                const parentParagraph = link.closest('p');
                if (parentParagraph) {
                    parentParagraph.after(embedDiv);
                } else {
                    link.parentElement.appendChild(embedDiv);
                }
            }
        });
    },

    _renderAttachedFiles(container, files) {
        const fileContainer = document.createElement('div');
        fileContainer.className = 'file-previews-container';
        files.forEach((file) => {
            const chip = document.createElement('div');
            chip.className = 'file-chip';
            chip.innerHTML = `<span class="material-symbols-outlined">description</span><span>${file instanceof File ? file.name : (file.name || 'document')}</span>`;
            fileContainer.appendChild(chip);
        });
        container.appendChild(fileContainer);
    }
});
