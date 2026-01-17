/**
 * Design Properties Module
 * Handles property panel updates and object property editing
 */
const DesignProperties = {
    currentObject: null,
    lockRatio: false,
    aspectRatio: 1,

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
    },

    setupColorInputs() {
        this.setupColorPair('prop-fill', 'prop-fill-hex', 'fill');
        this.setupColorPair('prop-stroke', 'prop-stroke-hex', 'stroke');
        this.setupColorPair('canvas-bg', 'canvas-bg-hex', 'canvas-bg');

        document.getElementById('prop-stroke-width')?.addEventListener('change', (e) => {
            if (this.currentObject) {
                this.currentObject.set('strokeWidth', parseInt(e.target.value) || 0);
                DesignCanvas.canvas.requestRenderAll();
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
                    this.applyColor(property, color);
                }
            });
        }
    },

    applyColor(property, color) {
        if (property === 'canvas-bg') {
            DesignCanvas.setBackgroundColor(color);
        } else if (this.currentObject) {
            this.currentObject.set(property, color);
            DesignCanvas.canvas.requestRenderAll();
            DesignCanvas.saveHistory();
        }
    },

    setupSliders() {
        const opacitySlider = document.getElementById('prop-opacity');
        const opacityValue = document.getElementById('prop-opacity-value');

        if (opacitySlider) {
            opacitySlider.addEventListener('input', (e) => {
                const value = parseInt(e.target.value);
                if (opacityValue) opacityValue.textContent = value + '%';
                if (this.currentObject) {
                    this.currentObject.set('opacity', value / 100);
                    DesignCanvas.canvas.requestRenderAll();
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
                if (this.currentObject && this.currentObject.type === 'rect') {
                    this.currentObject.set({ rx: value, ry: value });
                    DesignCanvas.canvas.requestRenderAll();
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
                DesignCanvas.setCanvasSize(width, height);
            });
        }

        if (heightInput) {
            heightInput.addEventListener('change', () => {
                const width = parseInt(widthInput?.value) || 1200;
                const height = parseInt(heightInput.value) || 800;
                DesignCanvas.setCanvasSize(width, height);
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
                session_id: DesignApp.sessionId,
                template_id: templateId
            })
        })
            .then(res => res.json())
            .then(data => {
                if (data.canvas_state) {
                    const state = data.canvas_state;
                    DesignCanvas.setCanvasSize(state.width, state.height);
                    DesignCanvas.setBackgroundColor(state.background);
                    DesignCanvas.clear();

                    document.getElementById('canvas-width').value = state.width;
                    document.getElementById('canvas-height').value = state.height;
                    document.getElementById('canvas-bg').value = state.background;
                    document.getElementById('canvas-bg-hex').value = state.background;
                }
            })
            .catch(err => console.error('Failed to apply template:', err));
    },

    updateFromSelection(object) {
        this.currentObject = object;

        const noSelection = document.getElementById('no-selection');
        const objectProps = document.getElementById('object-properties');
        const canvasProps = document.getElementById('canvas-properties');
        const textProps = document.getElementById('text-properties');
        const cornerRow = document.getElementById('corner-radius-row');

        if (!object) {
            noSelection?.classList.remove('hidden');
            objectProps?.classList.add('hidden');
            canvasProps?.classList.remove('hidden');
            return;
        }

        noSelection?.classList.add('hidden');
        objectProps?.classList.remove('hidden');
        canvasProps?.classList.add('hidden');

        this.updateTransformProperties(object);
        this.updateAppearanceProperties(object);

        const isText = object.type === 'i-text' || object.type === 'text' || object.type === 'textbox';
        if (textProps) textProps.style.display = isText ? 'block' : 'none';
        if (isText) this.updateTextProperties(object);

        const isRect = object.type === 'rect';
        if (cornerRow) cornerRow.style.display = isRect ? 'flex' : 'none';
        if (isRect) {
            document.getElementById('prop-radius').value = object.rx || 0;
            document.getElementById('prop-radius-value').textContent = object.rx || 0;
        }
    },

    updateTransformProperties(object) {
        const bounds = object.getBoundingRect();

        document.getElementById('prop-x').value = Math.round(object.left);
        document.getElementById('prop-y').value = Math.round(object.top);

        let width, height;
        if (object.type === 'circle') {
            width = height = object.radius * 2 * object.scaleX;
        } else if (object.type === 'line') {
            width = Math.abs(object.x2 - object.x1);
            height = Math.abs(object.y2 - object.y1);
        } else {
            width = (object.width || 0) * (object.scaleX || 1);
            height = (object.height || 0) * (object.scaleY || 1);
        }

        document.getElementById('prop-width').value = Math.round(width);
        document.getElementById('prop-height').value = Math.round(height);
        document.getElementById('prop-angle').value = Math.round(object.angle || 0);

        this.aspectRatio = width / height;
    },

    updateAppearanceProperties(object) {
        const fill = object.fill || '#000000';
        const stroke = object.stroke || '#000000';
        const strokeWidth = object.strokeWidth || 0;
        const opacity = Math.round((object.opacity || 1) * 100);

        document.getElementById('prop-fill').value = fill.startsWith('#') ? fill : '#000000';
        document.getElementById('prop-fill-hex').value = fill.toUpperCase();
        document.getElementById('prop-stroke').value = stroke.startsWith('#') ? stroke : '#000000';
        document.getElementById('prop-stroke-hex').value = stroke.toUpperCase();
        document.getElementById('prop-stroke-width').value = strokeWidth;
        document.getElementById('prop-opacity').value = opacity;
        document.getElementById('prop-opacity-value').textContent = opacity + '%';
    },

    updateTextProperties(object) {
        document.getElementById('prop-font-family').value = object.fontFamily || 'Inter';
        document.getElementById('prop-font-size').value = object.fontSize || 24;
        document.getElementById('prop-font-weight').value = object.fontWeight || '400';

        document.querySelectorAll('.align-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.align === (object.textAlign || 'left'));
        });
    },

    applyTransformProperty(inputId) {
        if (!this.currentObject) return;

        const value = parseInt(document.getElementById(inputId).value) || 0;

        switch (inputId) {
            case 'prop-x':
                this.currentObject.set('left', value);
                break;
            case 'prop-y':
                this.currentObject.set('top', value);
                break;
            case 'prop-width':
                if (this.currentObject.type === 'circle') {
                    this.currentObject.set('radius', value / 2);
                    if (this.lockRatio) {
                        document.getElementById('prop-height').value = value;
                    }
                } else {
                    const scaleX = value / this.currentObject.width;
                    this.currentObject.set('scaleX', scaleX);
                    if (this.lockRatio) {
                        this.currentObject.set('scaleY', scaleX);
                        const newHeight = this.currentObject.height * scaleX;
                        document.getElementById('prop-height').value = Math.round(newHeight);
                    }
                }
                break;
            case 'prop-height':
                if (this.currentObject.type !== 'circle') {
                    const scaleY = value / this.currentObject.height;
                    this.currentObject.set('scaleY', scaleY);
                    if (this.lockRatio) {
                        this.currentObject.set('scaleX', scaleY);
                        const newWidth = this.currentObject.width * scaleY;
                        document.getElementById('prop-width').value = Math.round(newWidth);
                    }
                }
                break;
            case 'prop-angle':
                this.currentObject.set('angle', value);
                break;
        }

        this.currentObject.setCoords();
        DesignCanvas.canvas.requestRenderAll();
        DesignCanvas.saveHistory();
    },

    applyTextProperty(inputId) {
        if (!this.currentObject) return;

        const input = document.getElementById(inputId);
        if (!input) return;

        switch (inputId) {
            case 'prop-font-family':
                this.currentObject.set('fontFamily', input.value);
                break;
            case 'prop-font-size':
                this.currentObject.set('fontSize', parseInt(input.value) || 24);
                break;
            case 'prop-font-weight':
                this.currentObject.set('fontWeight', input.value);
                break;
        }

        DesignCanvas.canvas.requestRenderAll();
        DesignCanvas.saveHistory();
    },

    applyTextAlign(align) {
        if (!this.currentObject) return;
        this.currentObject.set('textAlign', align);
        DesignCanvas.canvas.requestRenderAll();
        DesignCanvas.saveHistory();
    }
};
