const DesignCanvas = {
    svg: null,
    container: null,
    zoom: 1,
    panX: 0,
    panY: 0,
    width: 1200,
    height: 800,
    background: '#FFFFFF',
    selectedElement: null,

    init() {
        this.container = document.getElementById('canvas-container');
        this.svg = document.getElementById('design-svg');
        this.applyCanvasSize(this.width, this.height);
        this.setBackground(this.background);
        this.bindEvents();
        return this;
    },

    bindEvents() {
        this.svg.addEventListener('click', (event) => {
            const target = event.target.closest('svg > *');
            if (!target || target.id === 'svg-background') {
                this.clearSelection();
                return;
            }
            this.setSelection(target);
        });

        document.getElementById('btn-zoom-in')?.addEventListener('click', () => this.setZoom(this.zoom * 1.1));
        document.getElementById('btn-zoom-out')?.addEventListener('click', () => this.setZoom(this.zoom / 1.1));
        document.getElementById('btn-zoom-fit')?.addEventListener('click', () => this.zoomToFit());
    },

    setZoom(zoom) {
        this.zoom = Math.min(Math.max(zoom, 0.2), 3);
        this.applyTransform();
    },

    zoomToFit() {
        const wrapper = document.querySelector('.canvas-wrapper');
        if (!wrapper) return;
        const padding = 60;
        const scaleX = (wrapper.clientWidth - padding * 2) / this.width;
        const scaleY = (wrapper.clientHeight - padding * 2) / this.height;
        this.zoom = Math.min(scaleX, scaleY, 1);
        this.panX = 0;
        this.panY = 0;
        this.applyTransform();
    },

    applyTransform() {
        this.svg.style.transform = `translate(${this.panX}px, ${this.panY}px) scale(${this.zoom})`;
        const zoomDisplay = document.getElementById('zoom-level');
        if (zoomDisplay) {
            zoomDisplay.textContent = `${Math.round(this.zoom * 100)}%`;
        }
    },

    applyCanvasSize(width, height) {
        this.width = width;
        this.height = height;
        this.svg.setAttribute('width', width);
        this.svg.setAttribute('height', height);
        this.svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
        document.getElementById('canvas-dimensions').textContent = `${width} × ${height}`;
        this.setBackground(this.background);
    },

    setBackground(color) {
        this.background = color;
        let bg = document.getElementById('svg-background');
        if (!bg) {
            bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            bg.setAttribute('id', 'svg-background');
            this.svg.insertBefore(bg, this.svg.firstChild);
        }
        bg.setAttribute('x', '0');
        bg.setAttribute('y', '0');
        bg.setAttribute('width', this.width);
        bg.setAttribute('height', this.height);
        bg.setAttribute('fill', color);
    },

    setState(state) {
        if (!state || !state.svg) return;
        const parser = new DOMParser();
        const doc = parser.parseFromString(state.svg, 'image/svg+xml');
        const newSvg = doc.documentElement;
        if (newSvg.tagName.toLowerCase() !== 'svg') return;
        newSvg.setAttribute('id', 'design-svg');
        newSvg.classList.add('design-svg');
        this.svg.replaceWith(newSvg);
        this.svg = newSvg;
        this.applyCanvasSize(state.width || this.width, state.height || this.height);
        this.background = state.background || this.background;
        this.setBackground(this.background);
        this.bindEvents();
        this.zoomToFit();
    },

    getState() {
        return {
            width: this.width,
            height: this.height,
            background: this.background,
            svg: this.svg.outerHTML
        };
    },

    addElement(element) {
        this.svg.appendChild(element);
    },

    updateElement(id, attributes) {
        const element = document.getElementById(id);
        if (!element) return;
        Object.entries(attributes || {}).forEach(([key, value]) => {
            if (value === null || value === undefined) return;
            element.setAttribute(key, value);
        });
    },

    removeElement(id) {
        const element = document.getElementById(id);
        element?.remove();
    },

    clearCanvas() {
        Array.from(this.svg.children).forEach(child => {
            if (child.id !== 'svg-background') child.remove();
        });
    },

    setSelection(element) {
        this.clearSelection();
        this.selectedElement = element;
        element.classList.add('selected');
        if (typeof DesignProperties !== 'undefined') {
            DesignProperties.updateFromSelection(element);
        }
        document.getElementById('btn-delete').disabled = false;
        document.getElementById('btn-duplicate').disabled = false;
    },

    clearSelection() {
        if (this.selectedElement) {
            this.selectedElement.classList.remove('selected');
        }
        this.selectedElement = null;
        if (typeof DesignProperties !== 'undefined') {
            DesignProperties.updateFromSelection(null);
        }
        document.getElementById('btn-delete').disabled = true;
        document.getElementById('btn-duplicate').disabled = true;
    },

    getSelectedId() {
        return this.selectedElement?.id || null;
    }
};
