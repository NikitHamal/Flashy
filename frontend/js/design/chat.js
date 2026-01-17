/**
 * Design Chat Module
 *
 * Handles AI chat interactions for the design agent.
 * Manages streaming responses, tool pill visualization, and canvas state updates.
 */
const DesignChat = {
    chatHistory: null,
    inputElement: null,
    sendButton: null,
    isGenerating: false,
    uploadedImages: [],
    currentToolPill: null,
    currentAIContent: null,
    hasReceivedContent: false,

    /**
     * Initialize the chat module
     */
    init() {
        this.chatHistory = document.getElementById('design-chat-history');
        this.inputElement = document.getElementById('design-input');
        this.sendButton = document.getElementById('btn-send-design');

        this.setupEventListeners();
        this.setupSuggestionChips();
        return this;
    },

    /**
     * Set up all event listeners
     */
    setupEventListeners() {
        // Send button
        this.sendButton?.addEventListener('click', () => this.sendMessage());

        // Enter to send (Shift+Enter for new line)
        this.inputElement?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize and update send button on input
        this.inputElement?.addEventListener('input', () => {
            this.autoResizeInput();
            this.updateSendButton();
        });

        // File attachment
        document.getElementById('btn-attach-image')?.addEventListener('click', () => {
            document.getElementById('design-file-input')?.click();
        });

        document.getElementById('design-file-input')?.addEventListener('change', (e) => {
            this.handleFileUpload(e.target.files);
        });

        // Screenshot review
        document.getElementById('btn-screenshot-review')?.addEventListener('click', () => {
            this.sendScreenshotForReview();
        });

        // Interrupt button
        document.getElementById('btn-interrupt')?.addEventListener('click', () => {
            this.interruptGeneration();
        });

        // Clear chat
        document.getElementById('btn-clear-chat')?.addEventListener('click', () => {
            this.clearChat();
        });
    },

    /**
     * Set up suggestion chip click handlers
     */
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

    /**
     * Auto-resize the input textarea
     */
    autoResizeInput() {
        if (!this.inputElement) return;
        this.inputElement.style.height = 'auto';
        this.inputElement.style.height = Math.min(this.inputElement.scrollHeight, 120) + 'px';
    },

    /**
     * Update send button disabled state
     */
    updateSendButton() {
        if (!this.sendButton || !this.inputElement) return;
        const hasContent = this.inputElement.value.trim().length > 0 || this.uploadedImages.length > 0;
        this.sendButton.disabled = !hasContent || this.isGenerating;
    },

    /**
     * Set generating state and update UI accordingly
     */
    setGenerating(isGenerating) {
        this.isGenerating = isGenerating;
        this.updateSendButton();

        // Update status indicator
        const indicator = document.getElementById('agent-indicator');
        if (indicator) {
            indicator.classList.toggle('working', isGenerating);
            indicator.classList.toggle('idle', !isGenerating);
        }

        // Update status text
        const statusText = document.querySelector('.agent-status span:not(.status-indicator)');
        if (statusText) {
            statusText.textContent = isGenerating ? 'Designing...' : 'Design Agent';
        }

        // Toggle interrupt button
        const interruptBtn = document.getElementById('btn-interrupt');
        if (interruptBtn) {
            interruptBtn.style.display = isGenerating ? 'flex' : 'none';
        }

        // Disable review button while generating
        const reviewBtn = document.getElementById('btn-screenshot-review');
        if (reviewBtn) {
            reviewBtn.disabled = isGenerating;
        }
    },

    /**
     * Handle file upload for image attachments
     */
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

        // Reset file input
        document.getElementById('design-file-input').value = '';
    },

    /**
     * Render upload preview thumbnails
     */
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
                <img src="${img.data}" alt="${this.escapeHtml(img.name)}">
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

    /**
     * Send a message to the design agent
     */
    async sendMessage() {
        const message = this.inputElement?.value.trim();
        if ((!message && this.uploadedImages.length === 0) || this.isGenerating) return;

        // Hide welcome screen
        this.hideWelcome();

        // Add user message to chat
        if (message) {
            this.addMessage(message, 'user');
        }

        // Get current canvas state and screenshot
        const canvasState = DesignCanvas.getState();
        const screenshot = DesignCanvas.captureScreenshot();

        // Clear input and prepare for response
        this.inputElement.value = '';
        this.autoResizeInput();
        this.setGenerating(true);
        this.hasReceivedContent = false;
        this.currentToolPill = null;

        // Create AI message container
        const aiMessage = this.addMessage('', 'ai');
        this.currentAIContent = aiMessage.querySelector('.message-content');
        this.addLoadingDots(this.currentAIContent);

        try {
            const response = await fetch('/design/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: message,
                    session_id: DesignApp.sessionId,
                    canvas_state: canvasState,
                    screenshot_base64: screenshot
                })
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            await this.processStreamResponse(response, this.currentAIContent);

        } catch (error) {
            console.error('Error sending message:', error);
            this.removeLoadingDots(this.currentAIContent);
            this.showError(this.currentAIContent, error.message);
        } finally {
            this.setGenerating(false);
            this.uploadedImages = [];
            this.renderUploadPreviews();
            this.currentAIContent = null;
        }
    },

    /**
     * Process streaming response from the server
     */
    async processStreamResponse(response, container) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        try {
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.trim()) {
                        try {
                            const chunk = JSON.parse(line);
                            this.handleStreamChunk(chunk, container);
                        } catch (e) {
                            console.warn('Error parsing chunk:', e, line);
                        }
                    }
                }
            }

            // Process any remaining buffer
            if (buffer.trim()) {
                try {
                    const chunk = JSON.parse(buffer);
                    this.handleStreamChunk(chunk, container);
                } catch (e) {
                    console.warn('Error parsing final chunk:', e);
                }
            }
        } catch (error) {
            console.error('Stream processing error:', error);
            throw error;
        }
    },

    /**
     * Handle a single stream chunk from the server
     */
    handleStreamChunk(chunk, container) {
        // Remove loading dots on first content
        if (!this.hasReceivedContent) {
            this.removeLoadingDots(container);
            this.hasReceivedContent = true;
        }

        // Handle error
        if (chunk.error) {
            this.showError(container, chunk.error);
            return;
        }

        // Handle thought/thinking content
        if (chunk.thought) {
            this.addThoughtBlock(container, chunk.thought);
        }

        // Handle text content
        if (chunk.text) {
            this.appendTextContent(container, chunk.text);
        }

        // Handle tool call
        if (chunk.tool_call) {
            const toolPill = this.createToolPill(chunk.tool_call);
            container.appendChild(toolPill);
            this.currentToolPill = toolPill;
        }

        // Handle tool result
        if (chunk.tool_result) {
            if (this.currentToolPill) {
                this.updateToolResult(this.currentToolPill, chunk.tool_result);
            }
        }

        // Handle canvas state update - this is the key fix!
        if (chunk.canvas_state) {
            this.applyCanvasState(chunk.canvas_state);
        }

        // Handle legacy canvas_action for backwards compatibility
        if (chunk.canvas_action) {
            this.executeCanvasAction(chunk.canvas_action);
        }

        // Add loading indicator if not final
        if (!chunk.is_final && !container.querySelector('.loading-dots')) {
            this.addLoadingDots(container);
        }

        // Remove loading on final
        if (chunk.is_final) {
            this.removeLoadingDots(container);
        }

        this.scrollToBottom();
    },

    /**
     * Apply canvas state from backend
     */
    applyCanvasState(state) {
        if (!state) return;

        try {
            // Update canvas size if changed
            if (state.width && state.height) {
                if (DesignCanvas.canvas) {
                    const currentWidth = DesignCanvas.canvas.getWidth();
                    const currentHeight = DesignCanvas.canvas.getHeight();
                    if (state.width !== currentWidth || state.height !== currentHeight) {
                        DesignCanvas.setCanvasSize(state.width, state.height);
                    }
                }
            }

            // Update background
            if (state.background && DesignCanvas.canvas) {
                DesignCanvas.canvas.backgroundColor = state.background;
            }

            // Clear and rebuild objects
            if (state.objects && DesignCanvas.canvas) {
                // Clear existing objects
                DesignCanvas.canvas.clear();

                // Reset background after clear
                if (state.background) {
                    DesignCanvas.canvas.backgroundColor = state.background;
                }

                // Add each object from state
                state.objects.forEach(obj => {
                    this.createFabricObject(obj);
                });

                DesignCanvas.canvas.renderAll();
            }
        } catch (error) {
            console.error('Error applying canvas state:', error);
        }
    },

    /**
     * Create a Fabric.js object from state data
     */
    createFabricObject(objData) {
        if (!DesignCanvas.canvas || !objData) return;

        const commonProps = {
            left: objData.x || 0,
            top: objData.y || 0,
            fill: objData.fill || '#000000',
            stroke: objData.stroke || null,
            strokeWidth: objData.strokeWidth || 0,
            opacity: objData.opacity !== undefined ? objData.opacity : 1,
            angle: objData.angle || 0,
            id: objData.id
        };

        let fabricObj = null;

        switch (objData.type) {
            case 'rectangle':
                fabricObj = new fabric.Rect({
                    ...commonProps,
                    width: objData.width || 100,
                    height: objData.height || 100,
                    rx: objData.rx || 0,
                    ry: objData.ry || 0
                });
                break;

            case 'circle':
                fabricObj = new fabric.Circle({
                    ...commonProps,
                    radius: objData.radius || 50
                });
                break;

            case 'ellipse':
                fabricObj = new fabric.Ellipse({
                    ...commonProps,
                    rx: objData.rx || 50,
                    ry: objData.ry || 30
                });
                break;

            case 'triangle':
                fabricObj = new fabric.Triangle({
                    ...commonProps,
                    width: objData.width || 100,
                    height: objData.height || 100
                });
                break;

            case 'line':
                fabricObj = new fabric.Line(
                    [objData.x1 || 0, objData.y1 || 0, objData.x2 || 100, objData.y2 || 100],
                    {
                        stroke: objData.stroke || '#000000',
                        strokeWidth: objData.strokeWidth || 2,
                        opacity: objData.opacity !== undefined ? objData.opacity : 1,
                        id: objData.id
                    }
                );
                break;

            case 'polygon':
                if (objData.points && Array.isArray(objData.points)) {
                    fabricObj = new fabric.Polygon(objData.points, commonProps);
                }
                break;

            case 'path':
                if (objData.path) {
                    fabricObj = new fabric.Path(objData.path, commonProps);
                }
                break;

            case 'text':
                fabricObj = new fabric.IText(objData.text || 'Text', {
                    ...commonProps,
                    fontSize: objData.fontSize || 24,
                    fontFamily: objData.fontFamily || 'Inter',
                    fontWeight: objData.fontWeight || 'normal',
                    textAlign: objData.textAlign || 'left',
                    fill: objData.fill || '#000000'
                });
                break;

            case 'image':
                // Images need async loading
                if (objData.src) {
                    fabric.Image.fromURL(objData.src, (img) => {
                        if (img) {
                            img.set({
                                left: objData.x || 0,
                                top: objData.y || 0,
                                scaleX: objData.scaleX || 1,
                                scaleY: objData.scaleY || 1,
                                opacity: objData.opacity !== undefined ? objData.opacity : 1,
                                angle: objData.angle || 0,
                                id: objData.id
                            });
                            DesignCanvas.canvas.add(img);
                            DesignCanvas.canvas.renderAll();
                        }
                    }, { crossOrigin: 'anonymous' });
                }
                return; // Don't add below, handled in callback

            case 'group':
                // Groups require recursive creation
                if (objData.objects && Array.isArray(objData.objects)) {
                    const groupObjects = [];
                    objData.objects.forEach(childData => {
                        // Recursively create children (simplified)
                        const child = this.createFabricObjectSync(childData);
                        if (child) groupObjects.push(child);
                    });
                    if (groupObjects.length > 0) {
                        fabricObj = new fabric.Group(groupObjects, {
                            left: objData.x || 0,
                            top: objData.y || 0,
                            id: objData.id
                        });
                    }
                }
                break;
        }

        if (fabricObj) {
            DesignCanvas.canvas.add(fabricObj);
        }
    },

    /**
     * Create a Fabric object synchronously (for groups)
     */
    createFabricObjectSync(objData) {
        if (!objData) return null;

        const commonProps = {
            left: objData.x || 0,
            top: objData.y || 0,
            fill: objData.fill || '#000000',
            stroke: objData.stroke || null,
            strokeWidth: objData.strokeWidth || 0,
            opacity: objData.opacity !== undefined ? objData.opacity : 1,
            angle: objData.angle || 0,
            id: objData.id
        };

        switch (objData.type) {
            case 'rectangle':
                return new fabric.Rect({
                    ...commonProps,
                    width: objData.width || 100,
                    height: objData.height || 100,
                    rx: objData.rx || 0,
                    ry: objData.ry || 0
                });

            case 'circle':
                return new fabric.Circle({
                    ...commonProps,
                    radius: objData.radius || 50
                });

            case 'triangle':
                return new fabric.Triangle({
                    ...commonProps,
                    width: objData.width || 100,
                    height: objData.height || 100
                });

            case 'text':
                return new fabric.IText(objData.text || 'Text', {
                    ...commonProps,
                    fontSize: objData.fontSize || 24,
                    fontFamily: objData.fontFamily || 'Inter',
                    fontWeight: objData.fontWeight || 'normal'
                });

            default:
                return null;
        }
    },

    /**
     * Execute a canvas action (legacy support)
     */
    executeCanvasAction(action) {
        const { tool, args } = action;

        try {
            switch (tool) {
                case 'add_rectangle':
                    DesignTools.addRectangle(
                        args.x, args.y, args.width, args.height,
                        args.fill, args.stroke, args.strokeWidth,
                        args.opacity, args.rx, args.ry, args.angle
                    );
                    break;
                case 'add_circle':
                    DesignTools.addCircle(
                        args.x, args.y, args.radius,
                        args.fill, args.stroke, args.strokeWidth, args.opacity
                    );
                    break;
                case 'add_triangle':
                    DesignTools.addTriangle(
                        args.x, args.y, args.width, args.height,
                        args.fill, args.stroke, args.strokeWidth, args.opacity, args.angle
                    );
                    break;
                case 'add_line':
                    DesignTools.addLine(
                        args.x1, args.y1, args.x2, args.y2,
                        args.stroke, args.strokeWidth, args.opacity
                    );
                    break;
                case 'add_text':
                    DesignTools.addText(
                        args.x, args.y, args.text,
                        args.fontSize, args.fontFamily, args.fontWeight,
                        args.fill, args.textAlign, args.opacity, args.angle
                    );
                    break;
                case 'add_polygon':
                    DesignTools.addPolygon(
                        args.x, args.y, args.radius, args.sides,
                        args.fill, args.stroke, args.strokeWidth, args.opacity, args.angle
                    );
                    break;
                case 'add_star':
                    DesignTools.addStar(
                        args.x, args.y, args.outerRadius, args.innerRadius, args.points,
                        args.fill, args.stroke, args.strokeWidth, args.opacity, args.angle
                    );
                    break;
                case 'add_image':
                    DesignTools.addImage(
                        args.url, args.x, args.y,
                        args.width, args.height, args.opacity, args.angle
                    );
                    break;
                case 'modify_object':
                    DesignTools.modifyObject(args.id, args);
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
                    DesignTools.groupObjects(args.ids);
                    break;
                case 'ungroup_objects':
                    DesignTools.ungroupObjects(args.group_id);
                    break;
            }
        } catch (error) {
            console.error('Error executing canvas action:', error);
        }
    },

    /**
     * Add a thought block to the container
     */
    addThoughtBlock(container, thought) {
        const thoughtDiv = document.createElement('div');
        thoughtDiv.className = 'thought-block';

        const thoughtId = 'thought-' + Date.now();
        thoughtDiv.innerHTML = `
            <div class="thought-header" data-thought-id="${thoughtId}">
                <span class="material-symbols-outlined">psychology</span>
                <span>Thinking...</span>
                <span class="material-symbols-outlined chevron">expand_more</span>
            </div>
            <div class="thought-content">${this.escapeHtml(thought)}</div>
        `;

        // Add click handler
        thoughtDiv.querySelector('.thought-header').addEventListener('click', function() {
            this.parentElement.classList.toggle('expanded');
        });

        container.appendChild(thoughtDiv);
    },

    /**
     * Append text content to the AI message
     */
    appendTextContent(container, text) {
        // Find or create text container
        let textDiv = container.querySelector('.ai-text-content:last-of-type');

        // Check if last element is not a text div (e.g., it's a tool pill or thought)
        const lastChild = container.lastElementChild;
        if (lastChild && !lastChild.classList.contains('ai-text-content') && !lastChild.classList.contains('loading-dots')) {
            textDiv = null;
        }

        if (!textDiv) {
            textDiv = document.createElement('div');
            textDiv.className = 'ai-text-content';
            textDiv.dataset.raw = '';
            container.appendChild(textDiv);
        }

        textDiv.dataset.raw += text;

        // Parse markdown if marked library is available
        if (typeof marked !== 'undefined') {
            textDiv.innerHTML = marked.parse(textDiv.dataset.raw);
        } else {
            textDiv.textContent = textDiv.dataset.raw;
        }
    },

    /**
     * Create a tool pill element
     */
    createToolPill(toolCall) {
        const pill = document.createElement('div');
        pill.className = 'design-tool-pill executing';

        const toolIcons = {
            'add_rectangle': 'rectangle',
            'add_circle': 'circle',
            'add_ellipse': 'circle',
            'add_triangle': 'change_history',
            'add_line': 'horizontal_rule',
            'add_text': 'title',
            'add_polygon': 'hexagon',
            'add_star': 'star',
            'add_path': 'gesture',
            'add_image': 'image',
            'modify_object': 'edit',
            'delete_object': 'delete',
            'duplicate_object': 'content_copy',
            'clear_canvas': 'layers_clear',
            'set_background': 'format_color_fill',
            'set_canvas_size': 'aspect_ratio',
            'group_objects': 'group_work',
            'ungroup_objects': 'workspaces',
            'align_objects': 'align_horizontal_left',
            'distribute_objects': 'view_column',
            'move_layer': 'layers',
            'undo': 'undo',
            'redo': 'redo',
            'set_fill': 'format_color_fill',
            'set_stroke': 'border_color',
            'set_opacity': 'opacity',
            'rotate_object': 'rotate_right',
            'scale_object': 'zoom_out_map',
            'flip_object': 'flip'
        };

        const icon = toolIcons[toolCall.name] || 'build';
        const displayName = this.formatToolName(toolCall.name);

        // Format args for display
        let argsDisplay = '';
        if (toolCall.args) {
            const args = toolCall.args;
            if (args.text) {
                const truncatedText = args.text.length > 25 ? args.text.substring(0, 25) + '...' : args.text;
                argsDisplay = `"${truncatedText}"`;
            } else if (args.fill && typeof args.fill === 'string') {
                argsDisplay = args.fill;
            } else if (args.color) {
                argsDisplay = args.color;
            } else if (args.width && args.height) {
                argsDisplay = `${args.width} × ${args.height}`;
            } else if (args.radius) {
                argsDisplay = `r=${args.radius}`;
            } else if (args.id) {
                argsDisplay = `#${args.id}`;
            }
        }

        pill.innerHTML = `
            <div class="tool-icon">
                <span class="material-symbols-outlined">${icon}</span>
            </div>
            <div class="tool-info">
                <div class="tool-name">${displayName}</div>
                ${argsDisplay ? `<div class="tool-args">${this.escapeHtml(argsDisplay)}</div>` : ''}
            </div>
            <div class="tool-status">
                <span class="material-symbols-outlined spinning">sync</span>
            </div>
            <div class="tool-result"></div>
        `;

        // Click to expand/collapse
        pill.addEventListener('click', () => {
            pill.classList.toggle('expanded');
        });

        return pill;
    },

    /**
     * Format tool name for display
     */
    formatToolName(name) {
        return name
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    },

    /**
     * Update tool pill with result
     */
    updateToolResult(pill, result) {
        pill.classList.remove('executing');
        pill.classList.add('completed');

        // Update status icon
        const statusIcon = pill.querySelector('.tool-status .material-symbols-outlined');
        if (statusIcon) {
            statusIcon.classList.remove('spinning');
            statusIcon.textContent = 'check_circle';
        }

        // Update result text
        const resultDiv = pill.querySelector('.tool-result');
        if (resultDiv) {
            // Parse the result to extract meaningful info
            const cleanResult = this.cleanToolResult(result);
            resultDiv.textContent = cleanResult;
        }
    },

    /**
     * Clean tool result for display
     */
    cleanToolResult(result) {
        if (!result) return '';

        // Remove common prefixes
        let cleaned = result
            .replace(/^\[TOOL RESULT: \w+\]\s*/i, '')
            .replace(/^Result:\s*/i, '')
            .trim();

        // Truncate if too long
        if (cleaned.length > 200) {
            cleaned = cleaned.substring(0, 200) + '...';
        }

        return cleaned;
    },

    /**
     * Send screenshot for AI review
     */
    async sendScreenshotForReview(feedback = '') {
        if (this.isGenerating) return;

        this.hideWelcome();

        const screenshot = DesignCanvas.captureScreenshot();
        if (!screenshot) {
            console.error('Failed to capture screenshot');
            return;
        }

        // Add user message
        this.addMessage('Please review my current design and suggest improvements.', 'user');

        this.setGenerating(true);
        this.hasReceivedContent = false;

        const aiMessage = this.addMessage('', 'ai');
        const aiContent = aiMessage.querySelector('.message-content');
        this.addLoadingDots(aiContent);
        this.currentAIContent = aiContent;

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

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            await this.processStreamResponse(response, aiContent);

        } catch (error) {
            console.error('Error sending for review:', error);
            this.removeLoadingDots(aiContent);
            this.showError(aiContent, error.message);
        } finally {
            this.setGenerating(false);
            this.currentAIContent = null;
        }
    },

    /**
     * Interrupt the current generation
     */
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

    /**
     * Add a message to the chat history
     */
    addMessage(content, role) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `design-message ${role}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        if (role === 'user') {
            contentDiv.textContent = content;
        } else if (content) {
            // Parse markdown for AI messages if marked is available
            if (typeof marked !== 'undefined') {
                contentDiv.innerHTML = marked.parse(content);
            } else {
                contentDiv.textContent = content;
            }
        }

        messageDiv.appendChild(contentDiv);
        this.chatHistory?.appendChild(messageDiv);
        this.scrollToBottom();

        return messageDiv;
    },

    /**
     * Show error message
     */
    showError(container, message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <span class="material-symbols-outlined">error</span>
            <span>${this.escapeHtml(message)}</span>
        `;
        container.appendChild(errorDiv);
    },

    /**
     * Add loading dots indicator
     */
    addLoadingDots(container) {
        if (container.querySelector('.loading-dots')) return;

        const dots = document.createElement('div');
        dots.className = 'loading-dots';
        dots.innerHTML = '<span></span><span></span><span></span>';
        container.appendChild(dots);
    },

    /**
     * Remove loading dots indicator
     */
    removeLoadingDots(container) {
        const dots = container.querySelectorAll('.loading-dots');
        dots.forEach(el => el.remove());
    },

    /**
     * Hide the welcome message
     */
    hideWelcome() {
        const welcome = this.chatHistory?.querySelector('.chat-welcome');
        if (welcome) {
            welcome.style.display = 'none';
        }
    },

    /**
     * Clear chat history and show welcome message
     */
    clearChat() {
        if (this.chatHistory) {
            this.chatHistory.innerHTML = `
                <div class="chat-welcome">
                    <div class="welcome-icon">
                        <span class="material-symbols-outlined">palette</span>
                    </div>
                    <h3>AI Design Assistant</h3>
                    <p>Describe what you want to create and I'll build it on the canvas.
                       I can add shapes, text, images, and compose complex designs.</p>
                    <div class="suggestion-chips">
                        <button class="suggestion-chip" data-prompt="Create a modern business card with my name John Doe">Business Card</button>
                        <button class="suggestion-chip" data-prompt="Design a social media banner with gradient background">Social Banner</button>
                        <button class="suggestion-chip" data-prompt="Make a presentation title slide">Title Slide</button>
                        <button class="suggestion-chip" data-prompt="Create a minimalist logo with geometric shapes">Logo Design</button>
                    </div>
                </div>
            `;
            this.setupSuggestionChips();
        }
    },

    /**
     * Scroll chat to bottom
     */
    scrollToBottom() {
        if (this.chatHistory) {
            requestAnimationFrame(() => {
                this.chatHistory.scrollTop = this.chatHistory.scrollHeight;
            });
        }
    },

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};
