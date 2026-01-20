const DesignProperties = {
    currentElement: null,

    init() {
        this.bindTabs();
        this.bindTransformInputs();
        this.bindColorInputs();
        this.bindCanvasInputs();
        this.bindOpacitySlider();
        return this;
    },

    bindTabs() {
        document.querySelectorAll('.sidebar-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.switchTab(tab.dataset.tab);
            });
        });

        document.getElementById('btn-toggle-chat')?.addEventListener('click', () => {
            this.switchTab('chat');
        });
        document.getElementById('btn-toggle-properties')?.addEventListener('click', () => {
            this.switchTab('properties');
        });
    },

    switchTab(tabName) {
        document.querySelectorAll('.sidebar-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });
        document.querySelectorAll('.sidebar-panel').forEach(panel => panel.classList.remove('active'));
        document.getElementById(`${tabName}-panel`)?.classList.add('active');
    },

    bindTransformInputs() {
        ['prop-x', 'prop-y', 'prop-width', 'prop-height', 'prop-angle'].forEach(id => {
            const input = document.getElementById(id);
            input?.addEventListener('change', () => this.applyTransform());
        });

        document.getElementById('prop-font-size')?.addEventListener('change', () => this.applyTextStyle());
        document.getElementById('prop-font-family')?.addEventListener('change', () => this.applyTextStyle());
        document.getElementById('prop-font-weight')?.addEventListener('change', () => this.applyTextStyle());
    },

    bindColorInputs() {
        this.bindColor('prop-fill', 'prop-fill-hex', 'fill');
        this.bindColor('prop-stroke', 'prop-stroke-hex', 'stroke');

        document.getElementById('prop-stroke-width')?.addEventListener('change', (event) => {
            this.updateCurrent({ 'stroke-width': event.target.value || 0 });
        });
    },

    bindCanvasInputs() {
        document.getElementById('canvas-width')?.addEventListener('change', (event) => {
            DesignTools.setCanvasSize(parseInt(event.target.value || 1200, 10), DesignCanvas.height);
        });
        document.getElementById('canvas-height')?.addEventListener('change', (event) => {
            DesignTools.setCanvasSize(DesignCanvas.width, parseInt(event.target.value || 800, 10));
        });
        this.bindColor('canvas-bg', 'canvas-bg-hex', 'canvas');
    },

    bindOpacitySlider() {
        const slider = document.getElementById('prop-opacity');
        const label = document.getElementById('prop-opacity-value');
        slider?.addEventListener('input', (event) => {
            const value = event.target.value;
            label.textContent = `${value}%`;
            this.updateCurrent({ opacity: value / 100 });
        });

        const radiusSlider = document.getElementById('prop-radius');
        const radiusValue = document.getElementById('prop-radius-value');
        radiusSlider?.addEventListener('input', (event) => {
            const value = event.target.value;
            radiusValue.textContent = value;
            if (this.currentElement?.tagName.toLowerCase() === 'rect') {
                this.updateCurrent({ rx: value, ry: value });
            }
        });
    },

    bindColor(colorId, hexId, type) {
        const colorInput = document.getElementById(colorId);
        const hexInput = document.getElementById(hexId);

        colorInput?.addEventListener('input', (event) => {
            const color = event.target.value;
            if (hexInput) hexInput.value = color.toUpperCase();
            if (type === 'canvas') {
                DesignTools.setBackground(color);
            } else {
                this.updateCurrent({ [type]: color });
            }
        });

        hexInput?.addEventListener('change', (event) => {
            let color = event.target.value;
            if (!color.startsWith('#')) color = `#${color}`;
            if (colorInput) colorInput.value = color;
            if (type === 'canvas') {
                DesignTools.setBackground(color);
            } else {
                this.updateCurrent({ [type]: color });
            }
        });
    },

    updateFromSelection(element) {
        this.currentElement = element;
        document.getElementById('no-selection')?.classList.toggle('hidden', !!element);
        document.getElementById('object-properties')?.classList.toggle('hidden', !element);

        if (!element) return;

        const tag = element.tagName.toLowerCase();
        document.getElementById('corner-radius-row')?.classList.toggle('hidden', tag !== 'rect');
        document.getElementById('text-properties').style.display = tag === 'text' ? 'block' : 'none';

        document.getElementById('prop-x').value = element.getAttribute('x') || element.getAttribute('cx') || 0;
        document.getElementById('prop-y').value = element.getAttribute('y') || element.getAttribute('cy') || 0;
        document.getElementById('prop-width').value = element.getAttribute('width') || 0;
        document.getElementById('prop-height').value = element.getAttribute('height') || 0;
        document.getElementById('prop-angle').value = 0;

        const fill = element.getAttribute('fill') || '#ffffff';
        const stroke = element.getAttribute('stroke') || '#111111';
        document.getElementById('prop-fill').value = fill;
        document.getElementById('prop-fill-hex').value = fill;
        document.getElementById('prop-stroke').value = stroke;
        document.getElementById('prop-stroke-hex').value = stroke;
        document.getElementById('prop-stroke-width').value = element.getAttribute('stroke-width') || 0;

        const opacity = Math.round((parseFloat(element.getAttribute('opacity') || 1)) * 100);
        document.getElementById('prop-opacity').value = opacity;
        document.getElementById('prop-opacity-value').textContent = `${opacity}%`;

        if (tag === 'rect') {
            const radius = element.getAttribute('rx') || 0;
            document.getElementById('prop-radius').value = radius;
            document.getElementById('prop-radius-value').textContent = radius;
        }

        const fontSize = element.getAttribute('font-size') || 24;
        document.getElementById('prop-font-size').value = fontSize;
    },

    applyTransform() {
        if (!this.currentElement) return;
        const tag = this.currentElement.tagName.toLowerCase();
        const x = document.getElementById('prop-x').value;
        const y = document.getElementById('prop-y').value;
        const width = document.getElementById('prop-width').value;
        const height = document.getElementById('prop-height').value;

        if (tag === 'circle') {
            this.updateCurrent({ cx: x, cy: y });
        } else {
            this.updateCurrent({ x, y, width, height });
        }
    },

    applyTextStyle() {
        if (!this.currentElement || this.currentElement.tagName.toLowerCase() !== 'text') return;
        const fontSize = document.getElementById('prop-font-size').value;
        const fontFamily = document.getElementById('prop-font-family').value;
        const fontWeight = document.getElementById('prop-font-weight').value;
        this.updateCurrent({ 'font-size': fontSize, 'font-family': fontFamily, 'font-weight': fontWeight });
    },

    updateCurrent(attributes) {
        if (!this.currentElement) return;
        Object.entries(attributes || {}).forEach(([key, value]) => {
            if (value === null || value === undefined) return;
            this.currentElement.setAttribute(key, value);
        });
    }
};
