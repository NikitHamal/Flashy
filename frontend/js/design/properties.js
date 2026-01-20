/**
 * Design Properties Module (SVG-based)
 * Handles property panel updates and SVG element property editing
 */
const DesignProperties = {
    currentElement: null,
    lockRatio: false,
    aspectRatio: 1,

    /**
     * Show a brief success flash on an input element
     */
    flashSuccess(inputId) {
        const input = document.getElementById(inputId);
        if (!input) return;

        input.classList.add('success');
        setTimeout(() => {
            input.classList.remove('success');
        }, 400);
    },

    init() {
        this.setupPropertyInputs();
        this.setupColorInputs();
        this.setupSliders();
        this.setupCanvasProperties();
        this.setupTabs();
        this.loadTemplates();
        return this;
    },

    setupTabs() {
        document.querySelectorAll('.sidebar-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const tabName = tab.dataset.tab;
                this.switchTab(tabName);
            });
        });

        document.getElementById('btn-toggle-chat')?.addEventListener('click', () => {
            document.getElementById('btn-toggle-chat').classList.add('active');
            document.getElementById('btn-toggle-properties')?.classList.remove('active');
            this.switchTab('chat');
        });

        document.getElementById('btn-toggle-properties')?.addEventListener('click', () => {
            document.getElementById('btn-toggle-properties').classList.add('active');
            document.getElementById('btn-toggle-chat')?.classList.remove('active');
            this.switchTab('properties');
        });
    },

    switchTab(tabName) {
        document.querySelectorAll('.sidebar-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });

        document.querySelectorAll('.sidebar-panel').forEach(panel => {
            panel.classList.remove('active');
        });

        const panel = document.getElementById(`${tabName}-panel`);
        if (panel) {
            panel.classList.add('active');
        }
    },

    setupPropertyInputs() {
        const inputs = ['prop-x', 'prop-y', 'prop-width', 'prop-height', 'prop-angle'];
        inputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.addEventListener('change', () => this.applyTransformProperty(id));
                input.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter') this.applyTransformProperty(id);
                });
            }
        });

        document.getElementById('btn-lock-ratio')?.addEventListener('click', () => {
            this.lockRatio = !this.lockRatio;
            const btn = document.getElementById('btn-lock-ratio');
            btn.classList.toggle('locked', this.lockRatio);
            btn.querySelector('.material-symbols-outlined').textContent =
                this.lockRatio ? 'lock' : 'lock_open';
        });

        const textInputs = ['prop-font-size'];
        textInputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.addEventListener('change', () => this.applyTextProperty(id));
            }
        });

        document.getElementById('prop-font-family')?.addEventListener('change', () => {
            this.applyTextProperty('prop-font-family');
        });

        document.getElementById('prop-font-weight')?.addEventListener('change', () => {
            this.applyTextProperty('prop-font-weight');
        });

        document.querySelectorAll('.align-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.align-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.applyTextAlign(btn.dataset.align);
            });
        });

        document.querySelectorAll('.arrange-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const alignment = btn.dataset.align;
                const distribution = btn.dataset.distribute;
                if (alignment) {
                    this.applyAlignment(alignment);
                } else if (distribution) {
                    this.applyDistribution(distribution);
                }
            });
        });
    },

    setupColorInputs() {
        this.setupColorPair('prop-fill', 'prop-fill-hex', 'fill');
        this.setupColorPair('prop-stroke', 'prop-stroke-hex', 'stroke');
        this.setupColorPair('canvas-bg', 'canvas-bg-hex', 'canvas-bg');

        document.getElementById('prop-stroke-width')?.addEventListener('change', (e) => {
            if (this.currentElement) {
                this.currentElement.setAttribute('stroke-width', parseInt(e.target.value) || 0);
                DesignCanvas.saveHistory();
            }
        });
    },

    setupColorPair(colorId, hexId, property) {
        const colorInput = document.getElementById(colorId);
        const hexInput = document.getElementById(hexId);

        if (colorInput) {
            colorInput.addEventListener('input', (e) => {
                const color = e.target.value;
                if (hexInput) hexInput.value = color.toUpperCase();
                this.applyColor(property, color);
            });
        }

        if (hexInput) {
            hexInput.addEventListener('change', (e) => {
                let color = e.target.value;
                if (!color.startsWith('#')) color = '#' + color;
                if (/^#[0-9A-Fa-f]{6}$/.test(color)) {
                    if (colorInput) colorInput.value = color;
                    this.applyColor(property, color, hexId);
                }
            });
        }
    },

    applyColor(property, color, hexInputId = null) {
        if (property === 'canvas-bg') {
            DesignCanvas.setBackground(color);
            if (hexInputId) this.flashSuccess(hexInputId);
        } else if (this.currentElement) {
            this.currentElement.setAttribute(property, color);
            DesignCanvas.saveHistory();
            if (hexInputId) this.flashSuccess(hexInputId);
        }
    },

    setupSliders() {
        const opacitySlider = document.getElementById('prop-opacity');
        const opacityValue = document.getElementById('prop-opacity-value');

        if (opacitySlider) {
            opacitySlider.addEventListener('input', (e) => {
                const value = parseInt(e.target.value);
                if (opacityValue) opacityValue.textContent = value + '%';
                if (this.currentElement) {
                    this.currentElement.setAttribute('opacity', value / 100);
                }
            });

            opacitySlider.addEventListener('change', () => {
                DesignCanvas.saveHistory();
            });
        }

        const radiusSlider = document.getElementById('prop-radius');
        const radiusValue = document.getElementById('prop-radius-value');

        if (radiusSlider) {
            radiusSlider.addEventListener('input', (e) => {
                const value = parseInt(e.target.value);
                if (radiusValue) radiusValue.textContent = value;
                if (this.currentElement && this.currentElement.tagName.toLowerCase() === 'rect') {
                    this.currentElement.setAttribute('rx', value);
                    this.currentElement.setAttribute('ry', value);
                }
            });

            radiusSlider.addEventListener('change', () => {
                DesignCanvas.saveHistory();
            });
        }
    },

    setupCanvasProperties() {
        const widthInput = document.getElementById('canvas-width');
        const heightInput = document.getElementById('canvas-height');

        if (widthInput) {
            widthInput.addEventListener('change', () => {
                const width = parseInt(widthInput.value) || 1200;
                const height = parseInt(heightInput?.value) || 800;
                DesignCanvas.updateCanvasSize(width, height);
            });
        }

        if (heightInput) {
            heightInput.addEventListener('change', () => {
                const width = parseInt(widthInput?.value) || 1200;
                const height = parseInt(heightInput.value) || 800;
                DesignCanvas.updateCanvasSize(width, height);
            });
        }
    },

    loadTemplates() {
        fetch('/design/templates')
            .then(res => res.json())
            .then(data => {
                const container = document.getElementById('template-list');
                if (!container) return;

                container.innerHTML = '';
                data.templates.forEach(template => {
                    const item = document.createElement('div');
                    item.className = 'template-item';
                    item.innerHTML = `
                        <div class="template-icon">
                            <span class="material-symbols-outlined">dashboard</span>
                        </div>
                        <div class="template-info">
                            <div class="template-name">${template.name}</div>
                            <div class="template-size">${template.size.width} × ${template.size.height}</div>
                        </div>
                    `;
                    item.addEventListener('click', () => this.applyTemplate(template.id));
                    container.appendChild(item);
                });
            })
            .catch(err => console.error('Failed to load templates:', err));
    },

    applyTemplate(templateId) {
        fetch('/design/template/apply', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: DesignCanvas.sessionId,
                template_id: templateId
            })
        })
            .then(res => res.json())
            .then(data => {
                if (data.canvas_state) {
                    const state = data.canvas_state;
                    DesignCanvas.updateCanvasSize(state.width, state.height);
                    DesignCanvas.setBackground(state.background);
                    DesignCanvas.clear();

                    document.getElementById('canvas-width').value = state.width;
                    document.getElementById('canvas-height').value = state.height;
                    document.getElementById('canvas-bg').value = state.background;
                    document.getElementById('canvas-bg-hex').value = state.background;
                }
            })
            .catch(err => console.error('Failed to apply template:', err));
    },

    /**
     * Update from SVG element (called by DesignCanvas on selection)
     */
    updateFromElement(element) {
        this.currentElement = element;

        const noSelection = document.getElementById('no-selection');
        const objectProps = document.getElementById('object-properties');
        const canvasProps = document.getElementById('canvas-properties');
        const textProps = document.getElementById('text-properties');
        const cornerRow = document.getElementById('corner-radius-row');

        if (!element) {
            noSelection?.classList.remove('hidden');
            objectProps?.classList.add('hidden');
            canvasProps?.classList.remove('hidden');
            return;
        }

        noSelection?.classList.add('hidden');
        objectProps?.classList.remove('hidden');
        canvasProps?.classList.add('hidden');

        this.updateTransformProperties(element);
        this.updateAppearanceProperties(element);

        const isText = element.tagName.toLowerCase() === 'text';
        if (textProps) textProps.style.display = isText ? 'block' : 'none';
        if (isText) this.updateTextProperties(element);

        const isRect = element.tagName.toLowerCase() === 'rect';
        if (cornerRow) cornerRow.style.display = isRect ? 'flex' : 'none';
        if (isRect) {
            const rx = parseFloat(element.getAttribute('rx')) || 0;
            document.getElementById('prop-radius').value = rx;
            document.getElementById('prop-radius-value').textContent = Math.round(rx);
        }
    },

    /**
     * Clear selection state
     */
    clearSelection() {
        this.currentElement = null;

        const noSelection = document.getElementById('no-selection');
        const objectProps = document.getElementById('object-properties');
        const canvasProps = document.getElementById('canvas-properties');

        noSelection?.classList.remove('hidden');
        objectProps?.classList.add('hidden');
        canvasProps?.classList.remove('hidden');
    },

    updateTransformProperties(element) {
        const bbox = element.getBBox();
        const tagName = element.tagName.toLowerCase();

        let x, y, width, height;

        // Get position based on element type
        if (tagName === 'circle') {
            const cx = parseFloat(element.getAttribute('cx')) || 0;
            const cy = parseFloat(element.getAttribute('cy')) || 0;
            const r = parseFloat(element.getAttribute('r')) || 0;
            x = cx - r;
            y = cy - r;
            width = r * 2;
            height = r * 2;
        } else if (tagName === 'ellipse') {
            const cx = parseFloat(element.getAttribute('cx')) || 0;
            const cy = parseFloat(element.getAttribute('cy')) || 0;
            const rx = parseFloat(element.getAttribute('rx')) || 0;
            const ry = parseFloat(element.getAttribute('ry')) || 0;
            x = cx - rx;
            y = cy - ry;
            width = rx * 2;
            height = ry * 2;
        } else if (tagName === 'line') {
            const x1 = parseFloat(element.getAttribute('x1')) || 0;
            const y1 = parseFloat(element.getAttribute('y1')) || 0;
            const x2 = parseFloat(element.getAttribute('x2')) || 0;
            const y2 = parseFloat(element.getAttribute('y2')) || 0;
            x = Math.min(x1, x2);
            y = Math.min(y1, y2);
            width = Math.abs(x2 - x1);
            height = Math.abs(y2 - y1);
        } else {
            // rect, text, image, polygon, path
            x = bbox.x;
            y = bbox.y;
            width = bbox.width;
            height = bbox.height;
        }

        document.getElementById('prop-x').value = Math.round(x);
        document.getElementById('prop-y').value = Math.round(y);
        document.getElementById('prop-width').value = Math.round(width);
        document.getElementById('prop-height').value = Math.round(height);

        // Get rotation from transform
        const transform = element.getAttribute('transform') || '';
        const rotateMatch = transform.match(/rotate\(([^)]+)\)/);
        const angle = rotateMatch ? parseFloat(rotateMatch[1]) : 0;
        document.getElementById('prop-angle').value = Math.round(angle);

        this.aspectRatio = width / height;
    },

    updateAppearanceProperties(element) {
        const fill = element.getAttribute('fill') || '#000000';
        const stroke = element.getAttribute('stroke') || '#000000';
        const strokeWidth = element.getAttribute('stroke-width') || 0;
        const opacity = parseFloat(element.getAttribute('opacity') || 1) * 100;

        // Handle gradients - show as solid color for picker
        const fillColor = fill.startsWith('url(') ? '#000000' : fill;
        const strokeColor = stroke.startsWith('url(') ? '#000000' : stroke;

        document.getElementById('prop-fill').value = fillColor === 'none' ? '#000000' : fillColor;
        document.getElementById('prop-fill-hex').value = fillColor === 'none' ? 'none' : fillColor.toUpperCase();
        document.getElementById('prop-stroke').value = strokeColor === 'none' ? '#000000' : strokeColor;
        document.getElementById('prop-stroke-hex').value = strokeColor === 'none' ? 'none' : strokeColor.toUpperCase();
        document.getElementById('prop-stroke-width').value = strokeWidth;
        document.getElementById('prop-opacity').value = Math.round(opacity);
        document.getElementById('prop-opacity-value').textContent = Math.round(opacity) + '%';
    },

    updateTextProperties(element) {
        const fontFamily = element.getAttribute('font-family') || 'Inter';
        const fontSize = element.getAttribute('font-size') || 24;
        const fontWeight = element.getAttribute('font-weight') || '400';
        const textAnchor = element.getAttribute('text-anchor') || 'start';

        // Clean font family for select
        const cleanFontFamily = fontFamily.split(',')[0].trim().replace(/['"]/g, '');
        
        document.getElementById('prop-font-family').value = cleanFontFamily;
        document.getElementById('prop-font-size').value = parseInt(fontSize);
        document.getElementById('prop-font-weight').value = fontWeight;

        // Map text-anchor to align buttons
        const alignMap = { 'start': 'left', 'middle': 'center', 'end': 'right' };
        const align = alignMap[textAnchor] || 'left';
        
        document.querySelectorAll('.align-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.align === align);
        });
    },

    applyTransformProperty(inputId) {
        if (!this.currentElement) return;

        const value = parseFloat(document.getElementById(inputId).value) || 0;
        const tagName = this.currentElement.tagName.toLowerCase();
        const bbox = this.currentElement.getBBox();

        switch (inputId) {
            case 'prop-x':
                this.setElementX(this.currentElement, value);
                break;
            case 'prop-y':
                this.setElementY(this.currentElement, value);
                break;
            case 'prop-width':
                this.setElementWidth(this.currentElement, value);
                if (this.lockRatio) {
                    const newHeight = value / this.aspectRatio;
                    this.setElementHeight(this.currentElement, newHeight);
                    document.getElementById('prop-height').value = Math.round(newHeight);
                }
                break;
            case 'prop-height':
                this.setElementHeight(this.currentElement, value);
                if (this.lockRatio) {
                    const newWidth = value * this.aspectRatio;
                    this.setElementWidth(this.currentElement, newWidth);
                    document.getElementById('prop-width').value = Math.round(newWidth);
                }
                break;
            case 'prop-angle':
                this.setElementRotation(this.currentElement, value);
                break;
        }

        DesignCanvas.saveHistory();
        DesignCanvas.showSelectionHandles(this.currentElement);
        this.flashSuccess(inputId);
    },

    setElementX(element, x) {
        const tagName = element.tagName.toLowerCase();
        const bbox = element.getBBox();

        if (tagName === 'rect' || tagName === 'image' || tagName === 'text') {
            element.setAttribute('x', x);
        } else if (tagName === 'circle') {
            const r = parseFloat(element.getAttribute('r')) || 0;
            element.setAttribute('cx', x + r);
        } else if (tagName === 'ellipse') {
            const rx = parseFloat(element.getAttribute('rx')) || 0;
            element.setAttribute('cx', x + rx);
        } else if (tagName === 'line') {
            const x1 = parseFloat(element.getAttribute('x1')) || 0;
            const x2 = parseFloat(element.getAttribute('x2')) || 0;
            const dx = x - Math.min(x1, x2);
            element.setAttribute('x1', x1 + dx);
            element.setAttribute('x2', x2 + dx);
        } else {
            // For polygon, polyline, path - use transform
            const dx = x - bbox.x;
            DesignTools.translateElement(element, dx, 0);
        }
    },

    setElementY(element, y) {
        const tagName = element.tagName.toLowerCase();
        const bbox = element.getBBox();

        if (tagName === 'rect' || tagName === 'image' || tagName === 'text') {
            element.setAttribute('y', y);
        } else if (tagName === 'circle') {
            const r = parseFloat(element.getAttribute('r')) || 0;
            element.setAttribute('cy', y + r);
        } else if (tagName === 'ellipse') {
            const ry = parseFloat(element.getAttribute('ry')) || 0;
            element.setAttribute('cy', y + ry);
        } else if (tagName === 'line') {
            const y1 = parseFloat(element.getAttribute('y1')) || 0;
            const y2 = parseFloat(element.getAttribute('y2')) || 0;
            const dy = y - Math.min(y1, y2);
            element.setAttribute('y1', y1 + dy);
            element.setAttribute('y2', y2 + dy);
        } else {
            // For polygon, polyline, path - use transform
            const dy = y - bbox.y;
            DesignTools.translateElement(element, 0, dy);
        }
    },

    setElementWidth(element, width) {
        const tagName = element.tagName.toLowerCase();

        if (tagName === 'rect' || tagName === 'image') {
            element.setAttribute('width', width);
        } else if (tagName === 'circle') {
            element.setAttribute('r', width / 2);
        } else if (tagName === 'ellipse') {
            element.setAttribute('rx', width / 2);
        } else if (tagName === 'line') {
            const x1 = parseFloat(element.getAttribute('x1')) || 0;
            element.setAttribute('x2', x1 + width);
        }
        // For text, polygon, path - width scaling would require transform
    },

    setElementHeight(element, height) {
        const tagName = element.tagName.toLowerCase();

        if (tagName === 'rect' || tagName === 'image') {
            element.setAttribute('height', height);
        } else if (tagName === 'circle') {
            element.setAttribute('r', height / 2);
        } else if (tagName === 'ellipse') {
            element.setAttribute('ry', height / 2);
        } else if (tagName === 'line') {
            const y1 = parseFloat(element.getAttribute('y1')) || 0;
            element.setAttribute('y2', y1 + height);
        }
        // For text, polygon, path - height scaling would require transform
    },

    setElementRotation(element, angle) {
        const bbox = element.getBBox();
        const centerX = bbox.x + bbox.width / 2;
        const centerY = bbox.y + bbox.height / 2;

        // Get existing transform without rotation
        let transform = element.getAttribute('transform') || '';
        transform = transform.replace(/rotate\([^)]+\)/g, '').trim();

        if (angle !== 0) {
            transform = `${transform} rotate(${angle}, ${centerX}, ${centerY})`.trim();
        }

        if (transform) {
            element.setAttribute('transform', transform);
        } else {
            element.removeAttribute('transform');
        }
    },

    applyTextProperty(inputId) {
        if (!this.currentElement) return;
        if (this.currentElement.tagName.toLowerCase() !== 'text') return;

        const input = document.getElementById(inputId);
        if (!input) return;

        switch (inputId) {
            case 'prop-font-family':
                this.currentElement.setAttribute('font-family', input.value + ', sans-serif');
                break;
            case 'prop-font-size':
                this.currentElement.setAttribute('font-size', parseInt(input.value) || 24);
                break;
            case 'prop-font-weight':
                this.currentElement.setAttribute('font-weight', input.value);
                break;
        }

        DesignCanvas.saveHistory();
        this.flashSuccess(inputId);
    },

    applyAlignment(alignment) {
        // Single element - align to canvas
        if (this.currentElement) {
            const bbox = this.currentElement.getBBox();
            const canvasWidth = DesignCanvas.width;
            const canvasHeight = DesignCanvas.height;

            switch (alignment) {
                case 'left':
                    this.setElementX(this.currentElement, 0);
                    break;
                case 'center':
                    this.setElementX(this.currentElement, (canvasWidth - bbox.width) / 2);
                    break;
                case 'right':
                    this.setElementX(this.currentElement, canvasWidth - bbox.width);
                    break;
                case 'top':
                    this.setElementY(this.currentElement, 0);
                    break;
                case 'middle':
                    this.setElementY(this.currentElement, (canvasHeight - bbox.height) / 2);
                    break;
                case 'bottom':
                    this.setElementY(this.currentElement, canvasHeight - bbox.height);
                    break;
            }

            DesignCanvas.saveHistory();
            DesignCanvas.showSelectionHandles(this.currentElement);
        }
    },

    applyDistribution(direction) {
        // Would need multi-selection support
        console.log('Distribution requires multiple selection');
    },

    applyTextAlign(align) {
        if (!this.currentElement) return;
        if (this.currentElement.tagName.toLowerCase() !== 'text') return;

        // Map align to text-anchor
        const anchorMap = { 'left': 'start', 'center': 'middle', 'right': 'end' };
        this.currentElement.setAttribute('text-anchor', anchorMap[align] || 'start');
        
        DesignCanvas.saveHistory();
    }
};
