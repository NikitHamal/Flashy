/**
 * Design Chat Module
 * Handles AI chat interactions for the design agent
 */
const DesignChat = {
    chatHistory: null,
    inputElement: null,
    sendButton: null,
    isGenerating: false,
    uploadedImages: [],
    currentToolPill: null,

    init() {
        this.chatHistory = document.getElementById('design-chat-history');
        this.inputElement = document.getElementById('design-input');
        this.sendButton = document.getElementById('btn-send-design');

        this.setupEventListeners();
        this.setupSuggestionChips();
        return this;
    },

    setupEventListeners() {
        this.sendButton?.addEventListener('click', () => this.sendMessage());

        this.inputElement?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        this.inputElement?.addEventListener('input', () => {
            this.autoResizeInput();
            this.updateSendButton();
        });

        document.getElementById('btn-attach-image')?.addEventListener('click', () => {
            document.getElementById('design-file-input')?.click();
        });

        document.getElementById('design-file-input')?.addEventListener('change', (e) => {
            this.handleFileUpload(e.target.files);
        });

        document.getElementById('btn-screenshot-review')?.addEventListener('click', () => {
            this.sendScreenshotForReview();
        });

        document.getElementById('btn-interrupt')?.addEventListener('click', () => {
            this.interruptGeneration();
        });

        document.getElementById('btn-clear-chat')?.addEventListener('click', () => {
            this.clearChat();
        });
    },

    setupSuggestionChips() {
        document.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const prompt = chip.dataset.prompt;
                if (prompt) {
                    this.inputElement.value = prompt;
                    this.updateSendButton();
                    this.inputElement.focus();
                }
            });
        });
    },

    autoResizeInput() {
        if (!this.inputElement) return;
        this.inputElement.style.height = 'auto';
        this.inputElement.style.height = Math.min(this.inputElement.scrollHeight, 120) + 'px';
    },

    updateSendButton() {
        if (!this.sendButton || !this.inputElement) return;
        const hasContent = this.inputElement.value.trim().length > 0 || this.uploadedImages.length > 0;
        this.sendButton.disabled = !hasContent || this.isGenerating;
    },

    setGenerating(isGenerating) {
        this.isGenerating = isGenerating;
        this.updateSendButton();

        const indicator = document.getElementById('agent-indicator');
        if (indicator) {
            indicator.classList.toggle('working', isGenerating);
            indicator.classList.toggle('idle', !isGenerating);
        }

        const interruptBtn = document.getElementById('btn-interrupt');
        if (interruptBtn) {
            interruptBtn.classList.toggle('hidden', !isGenerating);
        }

        const reviewBtn = document.getElementById('btn-screenshot-review');
        if (reviewBtn) {
            reviewBtn.disabled = isGenerating;
        }

        // Add sending state to send button for animation
        if (this.sendButton) {
            this.sendButton.classList.toggle('sending', isGenerating);
        }
    },

    handleFileUpload(files) {
        Array.from(files).forEach(file => {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    this.uploadedImages.push({
                        name: file.name,
                        data: e.target.result
                    });
                    this.renderUploadPreviews();
                    this.updateSendButton();
                };
                reader.readAsDataURL(file);
            }
        });

        document.getElementById('design-file-input').value = '';
    },

    renderUploadPreviews() {
        const container = document.getElementById('design-upload-previews');
        if (!container) return;

        if (this.uploadedImages.length === 0) {
            container.classList.add('hidden');
            return;
        }

        container.classList.remove('hidden');
        container.innerHTML = '';

        this.uploadedImages.forEach((img, index) => {
            const item = document.createElement('div');
            item.className = 'upload-preview-item';
            item.innerHTML = `
                <img src="${img.data}" alt="${img.name}">
                <div class="remove-btn" data-index="${index}">
                    <span class="material-symbols-outlined">close</span>
                </div>
            `;
            item.querySelector('.remove-btn').addEventListener('click', () => {
                this.uploadedImages.splice(index, 1);
                this.renderUploadPreviews();
                this.updateSendButton();
            });
            container.appendChild(item);
        });
    },

    async sendMessage() {
        const message = this.inputElement?.value.trim();
        if ((!message && this.uploadedImages.length === 0) || this.isGenerating) return;

        this.hideWelcome();

        if (message) {
            this.addMessage(message, 'user');
        }

        const canvasState = DesignCanvas.getState();
        const screenshot = DesignCanvas.captureScreenshot();

        this.inputElement.value = '';
        this.autoResizeInput();
        this.setGenerating(true);
        this.currentToolPill = null;

        const aiMessage = this.addMessage('', 'ai');
        const aiContent = aiMessage.querySelector('.message-content');
        this.addLoadingDots(aiContent);

        try {
            const response = await fetch('/design/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: message,
                    session_id: DesignApp.sessionId,
                    canvas_state: canvasState,
                    screenshot_base64: screenshot,
                    images: this.uploadedImages
                })
            });

            if (!response.ok || !response.body) {
                throw new Error(`Design agent error (${response.status})`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (line.trim()) {
                        try {
                            const chunk = JSON.parse(line);
                            this.handleStreamChunk(chunk, aiContent);
                        } catch (e) {
                            console.error('Error parsing chunk:', e);
                        }
                    }
                }
            }

            if (aiContent && aiContent.children.length === 0) {
                aiContent.innerHTML = '<p>Design updated.</p>';
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.removeLoadingDots(aiContent);
            aiContent.innerHTML += `<p class="error">Error: ${error.message}</p>`;
        } finally {
            this.setGenerating(false);
            this.uploadedImages = [];
            this.renderUploadPreviews();
        }
    },

    handleStreamChunk(chunk, container) {
        this.removeLoadingDots(container);

        if (chunk.error) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error';
            errorDiv.textContent = `Error: ${chunk.error}`;
            container.appendChild(errorDiv);
            this.scrollToBottom();
            return;
        }

        if (chunk.thought) {
            const thoughtDiv = document.createElement('div');
            thoughtDiv.className = 'thought-block';
            thoughtDiv.innerHTML = `
                <div class="thought-header" onclick="this.parentElement.classList.toggle('expanded')">
                    <span class="material-symbols-outlined">psychology</span>
                    <span>Thinking...</span>
                    <span class="material-symbols-outlined chevron">expand_more</span>
                </div>
                <div class="thought-content">${this.escapeHtml(chunk.thought)}</div>
            `;
            container.appendChild(thoughtDiv);
        }

        if (chunk.text) {
            let textDiv = container.querySelector('.ai-text-content:last-child');
            if (!textDiv) {
                textDiv = document.createElement('div');
                textDiv.className = 'ai-text-content';
                textDiv.dataset.raw = '';
                container.appendChild(textDiv);
            }
            textDiv.dataset.raw += chunk.text;
            textDiv.innerHTML = marked.parse(textDiv.dataset.raw);
        }

        if (chunk.tool_call) {
            const toolPill = this.createToolPill(chunk.tool_call);
            container.appendChild(toolPill);
            this.currentToolPill = toolPill;
        }

        if (chunk.tool_result) {
            if (this.currentToolPill) {
                this.updateToolResult(this.currentToolPill, chunk.tool_result);
            }
        }

        if (chunk.canvas_action) {
            this.executeCanvasAction(chunk.canvas_action);
        }

        if (!chunk.is_final) {
            this.addLoadingDots(container);
        }

        this.scrollToBottom();
    },

    executeCanvasAction(action) {
        const { tool, args, result } = action;

        try {
            switch (tool) {
                case 'add_rectangle':
                    DesignTools.addRectangle(
                        args.x, args.y, args.width, args.height,
                        args.fill, args.stroke, args.strokeWidth,
                        args.opacity, args.rx, args.ry, args.angle,
                        args.id
                    );
                    break;
                case 'add_circle':
                    DesignTools.addCircle(
                        args.x, args.y, args.radius,
                        args.fill, args.stroke, args.strokeWidth, args.opacity,
                        args.id
                    );
                    break;
                case 'add_ellipse':
                    DesignTools.addEllipse(
                        args.x, args.y, args.rx, args.ry,
                        args.fill, args.stroke, args.strokeWidth, args.opacity,
                        args.angle, args.id
                    );
                    break;
                case 'add_triangle':
                    DesignTools.addTriangle(
                        args.x, args.y, args.width, args.height,
                        args.fill, args.stroke, args.strokeWidth, args.opacity, args.angle,
                        args.id
                    );
                    break;
                case 'add_line':
                    DesignTools.addLine(
                        args.x1, args.y1, args.x2, args.y2,
                        args.stroke, args.strokeWidth, args.opacity,
                        args.id
                    );
                    break;
                case 'add_text':
                    DesignTools.addText(
                        args.x, args.y, args.text,
                        args.fontSize, args.fontFamily, args.fontWeight,
                        args.fill, args.textAlign, args.opacity, args.angle,
                        args.id
                    );
                    break;
                case 'add_polygon':
                    if (args.points) {
                        DesignTools.addPolygonFromPoints(
                            args.points,
                            args.fill, args.stroke, args.strokeWidth, args.opacity,
                            args.angle, args.id
                        );
                    } else {
                        DesignTools.addPolygon(
                            args.x, args.y, args.radius, args.sides,
                            args.fill, args.stroke, args.strokeWidth, args.opacity, args.angle,
                            args.id
                        );
                    }
                    break;
                case 'add_star':
                    DesignTools.addStar(
                        args.x, args.y, args.outerRadius, args.innerRadius, args.points,
                        args.fill, args.stroke, args.strokeWidth, args.opacity, args.angle,
                        args.id
                    );
                    break;
                case 'add_path':
                    DesignTools.addPath(
                        args.path, args.fill, args.stroke, args.strokeWidth, args.opacity,
                        args.angle, args.id
                    );
                    break;
                case 'add_image':
                    DesignTools.addImage(
                        args.url || args.src, args.x, args.y,
                        args.width, args.height, args.opacity, args.angle,
                        args.id
                    );
                    break;
                case 'update_text':
                    DesignTools.modifyObject(args.id, { text: args.text });
                    break;
                case 'modify_object':
                    DesignTools.modifyObject(args.id, args);
                    break;
                case 'move_object':
                    DesignTools.modifyObject(args.id, { x: args.x, y: args.y });
                    break;
                case 'resize_object':
                    DesignTools.modifyObject(args.id, { width: args.width, height: args.height });
                    break;
                case 'rotate_object':
                    DesignTools.modifyObject(args.id, { angle: args.angle });
                    break;
                case 'scale_object':
                    DesignTools.modifyObject(args.id, { scaleX: args.scaleX, scaleY: args.scaleY });
                    break;
                case 'set_fill':
                    DesignTools.modifyObject(args.id, { fill: args.color || args.fill });
                    break;
                case 'set_stroke':
                    DesignTools.modifyObject(args.id, { stroke: args.color, strokeWidth: args.width });
                    break;
                case 'set_opacity':
                    DesignTools.modifyObject(args.id, { opacity: args.opacity });
                    break;
                case 'delete_object':
                    DesignTools.deleteObject(args.id);
                    break;
                case 'clear_canvas':
                    DesignTools.clearCanvas();
                    break;
                case 'set_background':
                    DesignTools.setBackground(args.color);
                    break;
                case 'set_canvas_size':
                    DesignCanvas.setCanvasSize(args.width, args.height);
                    break;
                case 'group_objects':
                    DesignTools.groupObjects(args.ids, args.group_id);
                    break;
                case 'ungroup_objects':
                    DesignTools.ungroupObjects(args.group_id || args.id);
                    break;
                case 'ungroup_object':
                    DesignTools.ungroupObjects(args.id || args.group_id);
                    break;
                case 'bring_to_front':
                    DesignTools.bringToFront(args.id);
                    break;
                case 'send_to_back':
                    DesignTools.sendToBack(args.id);
                    break;
                case 'bring_forward':
                    DesignTools.bringForward(args.id);
                    break;
                case 'send_backward':
                    DesignTools.sendBackward(args.id);
                    break;
                case 'duplicate_object':
                    DesignTools.duplicateObject(args.id, args.new_id);
                    break;
                case 'align_objects':
                    DesignTools.alignObjects(args.ids, args.alignment);
                    break;
                case 'distribute_objects':
                    DesignTools.distributeObjects(args.ids, args.direction);
                    break;
                case 'undo':
                    DesignCanvas.undo();
                    break;
                case 'redo':
                    DesignCanvas.redo();
                    break;

                // Advanced effect tools
                case 'add_shadow':
                    DesignTools.addShadow(
                        args.id,
                        args.offset_x ?? args.offsetX,
                        args.offset_y ?? args.offsetY,
                        args.blur,
                        args.color,
                        args.spread,
                        args.inset
                    );
                    break;
                case 'remove_shadow':
                    DesignTools.removeShadow(args.id);
                    break;
                case 'set_gradient':
                    DesignTools.setGradient(
                        args.id,
                        args.gradient_type ?? args.gradientType ?? 'linear',
                        args.colors,
                        args.angle,
                        args.stops,
                        args.cx,
                        args.cy,
                        args.preset
                    );
                    break;
                case 'remove_gradient':
                    DesignTools.removeGradient(args.id, args.restore_color ?? args.restoreColor);
                    break;
                case 'set_border_radius':
                    DesignTools.setBorderRadius(args.id, args.radius);
                    break;
                case 'style_text':
                    DesignTools.styleText(args.id, {
                        letterSpacing: args.letter_spacing ?? args.letterSpacing,
                        lineHeight: args.line_height ?? args.lineHeight,
                        textDecoration: args.text_decoration ?? args.textDecoration,
                        textTransform: args.text_transform ?? args.textTransform,
                        textShadowX: args.text_shadow_x ?? args.textShadowX,
                        textShadowY: args.text_shadow_y ?? args.textShadowY,
                        textShadowBlur: args.text_shadow_blur ?? args.textShadowBlur,
                        textShadowColor: args.text_shadow_color ?? args.textShadowColor
                    });
                    break;
                case 'set_blend_mode':
                    DesignTools.setBlendMode(args.id, args.mode);
                    break;
                case 'set_backdrop_blur':
                    DesignTools.setBackdropBlur(args.id, args.blur);
                    break;
                case 'apply_effect_preset':
                    DesignTools.applyEffectPreset(args.id, args.preset);
                    break;
                case 'add_filter':
                    DesignTools.addFilter(args.id, args.filter_type ?? args.filterType, args.value);
                    break;
                case 'remove_filters':
                    DesignTools.removeFilters(args.id, args.filter_type ?? args.filterType);
                    break;
                case 'set_gradient_background':
                    DesignTools.setGradientBackground(
                        args.gradient_type ?? args.gradientType ?? 'linear',
                        args.colors,
                        args.angle
                    );
                    break;
            }
        } catch (error) {
            console.error('Error executing canvas action:', error);
        }
    },

    createToolPill(toolCall) {
        const pill = document.createElement('div');
        pill.className = 'design-tool-pill executing';

        const toolIcons = {
            'add_rectangle': 'rectangle',
            'add_circle': 'circle',
            'add_ellipse': 'ellipse',
            'add_triangle': 'change_history',
            'add_line': 'horizontal_rule',
            'add_text': 'title',
            'add_polygon': 'hexagon',
            'add_star': 'star',
            'add_path': 'polyline',
            'add_image': 'image',
            'update_text': 'edit_note',
            'modify_object': 'edit',
            'move_object': 'open_with',
            'resize_object': 'open_in_full',
            'rotate_object': 'rotate_right',
            'scale_object': 'aspect_ratio',
            'set_fill': 'format_color_fill',
            'set_stroke': 'border_color',
            'set_opacity': 'opacity',
            'delete_object': 'delete',
            'clear_canvas': 'layers_clear',
            'set_background': 'format_color_fill',
            'set_canvas_size': 'aspect_ratio',
            'group_objects': 'group_work',
            'ungroup_objects': 'workspaces',
            'ungroup_object': 'workspaces',
            'bring_to_front': 'flip_to_front',
            'send_to_back': 'flip_to_back',
            'bring_forward': 'move_up',
            'send_backward': 'move_down',
            'duplicate_object': 'content_copy',
            'align_objects': 'align_horizontal_center',
            'distribute_objects': 'view_week',
            // Advanced effect tools
            'add_shadow': 'blur_on',
            'remove_shadow': 'blur_off',
            'set_gradient': 'gradient',
            'remove_gradient': 'format_color_reset',
            'set_border_radius': 'rounded_corner',
            'style_text': 'text_format',
            'set_blend_mode': 'blend_on',
            'set_backdrop_blur': 'blur_linear',
            'apply_effect_preset': 'auto_awesome',
            'add_filter': 'filter',
            'remove_filters': 'filter_alt_off',
            'set_gradient_background': 'wallpaper'
        };

        const icon = toolIcons[toolCall.name] || 'build';
        const displayName = toolCall.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

        let argsDisplay = '';
        if (toolCall.args) {
            const args = toolCall.args;
            if (args.text) argsDisplay = `"${args.text.substring(0, 20)}..."`;
            else if (args.fill) argsDisplay = args.fill;
            else if (args.width && args.height) argsDisplay = `${args.width}×${args.height}`;
            else if (args.id) argsDisplay = args.id;
        }

        pill.innerHTML = `
            <div class="tool-icon">
                <span class="material-symbols-outlined">${icon}</span>
            </div>
            <div class="tool-info">
                <div class="tool-name">${displayName}</div>
                <div class="tool-args">${this.escapeHtml(argsDisplay)}</div>
            </div>
            <div class="tool-result"></div>
        `;

        pill.addEventListener('click', () => {
            pill.classList.toggle('expanded');
        });

        return pill;
    },

    updateToolResult(pill, result) {
        pill.classList.remove('executing');
        pill.classList.add('completed');

        const resultDiv = pill.querySelector('.tool-result');
        if (resultDiv) {
            resultDiv.textContent = result;
        }
    },

    async sendScreenshotForReview(feedback = '') {
        if (this.isGenerating) return;

        this.hideWelcome();

        const screenshot = DesignCanvas.captureScreenshot();

        this.addMessage('Please review my current design and suggest improvements.', 'user');

        this.setGenerating(true);
        const aiMessage = this.addMessage('', 'ai');
        const aiContent = aiMessage.querySelector('.message-content');
        this.addLoadingDots(aiContent);

        try {
            const response = await fetch('/design/review', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: DesignApp.sessionId,
                    screenshot_base64: screenshot,
                    feedback: feedback
                })
            });

            if (!response.ok || !response.body) {
                throw new Error(`Design review error (${response.status})`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (line.trim()) {
                        try {
                            const chunk = JSON.parse(line);
                            this.handleStreamChunk(chunk, aiContent);
                        } catch (e) {
                            console.error('Error parsing chunk:', e);
                        }
                    }
                }
            }

            if (aiContent && aiContent.children.length === 0) {
                aiContent.innerHTML = '<p>Review complete.</p>';
            }
        } catch (error) {
            console.error('Error sending for review:', error);
            this.removeLoadingDots(aiContent);
            aiContent.innerHTML += `<p class="error">Error: ${error.message}</p>`;
        } finally {
            this.setGenerating(false);
        }
    },

    async interruptGeneration() {
        try {
            await fetch('/design/interrupt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: DesignApp.sessionId })
            });
        } catch (error) {
            console.error('Error interrupting:', error);
        }
        this.setGenerating(false);
    },

    addMessage(content, role) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `design-message ${role}`;

        // Add avatar for AI messages
        if (role === 'ai') {
            const avatarDiv = document.createElement('div');
            avatarDiv.className = 'message-avatar';
            avatarDiv.innerHTML = '<span class="material-symbols-outlined">auto_awesome</span>';
            messageDiv.appendChild(avatarDiv);
        }

        const contentWrapper = document.createElement('div');
        contentWrapper.className = 'message-wrapper';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        if (role === 'user') {
            contentDiv.textContent = content;
        } else {
            if (content) {
                contentDiv.innerHTML = marked.parse(content);
            }
        }

        contentWrapper.appendChild(contentDiv);

        // Add timestamp
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = this.formatTime(new Date());
        contentWrapper.appendChild(timeDiv);

        messageDiv.appendChild(contentWrapper);
        this.chatHistory?.appendChild(messageDiv);
        this.scrollToBottom();

        return messageDiv;
    },

    formatTime(date) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    },

    addLoadingDots(container) {
        if (container.querySelector('.loading-dots')) return;

        const dots = document.createElement('div');
        dots.className = 'loading-dots';
        dots.innerHTML = '<span></span><span></span><span></span>';
        container.appendChild(dots);
    },

    removeLoadingDots(container) {
        container.querySelectorAll('.loading-dots').forEach(el => el.remove());
    },

    hideWelcome() {
        const welcome = this.chatHistory?.querySelector('.chat-welcome');
        if (welcome) {
            welcome.style.display = 'none';
        }
    },

    clearChat() {
        if (this.chatHistory) {
            this.chatHistory.innerHTML = `
                <div class="chat-welcome">
                    <div class="welcome-icon">
                        <span class="material-symbols-outlined">palette</span>
                    </div>
                    <h3>AI Design Assistant</h3>
                    <p>Describe what you want to create and I'll build it on the canvas. I can add shapes, text, images, and compose complex designs.</p>
                    <div class="suggestion-chips">
                        <button class="suggestion-chip" data-prompt="Create a modern business card with my name John Doe">Business Card</button>
                        <button class="suggestion-chip" data-prompt="Design a social media banner with gradient background">Social Banner</button>
                        <button class="suggestion-chip" data-prompt="Make a presentation title slide">Title Slide</button>
                    </div>
                </div>
            `;
            this.setupSuggestionChips();
        }
    },

    scrollToBottom() {
        if (this.chatHistory) {
            this.chatHistory.scrollTop = this.chatHistory.scrollHeight;
        }
    },

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};
