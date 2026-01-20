/**
 * Design Canvas Module (SVG-based)
 * Manages native SVG canvas and element interactions
 */
const DesignCanvas = {
    svgElement: null,
    canvasContainer: null,
    selectionOverlay: null,
    
    // Canvas state
    width: 1200,
    height: 800,
    background: '#FFFFFF',
    
    // Zoom & Pan
    zoom: 1,
    minZoom: 0.1,
    maxZoom: 5,
    panX: 0,
    panY: 0,
    isPanning: false,
    lastPanPoint: null,
    
    // Selection
    selectedElement: null,
    selectedId: null,
    
    // History
    history: [],
    historyIndex: -1,
    maxHistory: 50,
    isRecordingHistory: true,
    
    // Grid & Snap
    showGrid: false,
    snapToGrid: false,
    gridSize: 24,
    
    // Current tool
    currentTool: 'select',
    
    // Session
    sessionId: null,

    init() {
        this.canvasContainer = document.getElementById('canvas-container');
        this.svgElement = document.getElementById('design-svg');
        this.selectionOverlay = document.getElementById('selection-overlay');
        
        if (!this.svgElement) {
            console.error('SVG element not found');
            return this;
        }
        
        this.sessionId = 'design_' + Date.now();
        
        this.setupEventListeners();
        this.updateCanvasSize(this.width, this.height);
        this.updateCanvasInfo();
        this.saveHistory();
        
        return this;
    },

    setupEventListeners() {
        // SVG click events
        this.svgElement.addEventListener('click', (e) => this.handleSvgClick(e));
        this.svgElement.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        document.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        document.addEventListener('mouseup', () => this.handleMouseUp());
        
        // Wheel for zoom
        this.canvasContainer.addEventListener('wheel', (e) => this.handleWheel(e));
        
        // Keyboard
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // Tool buttons
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.addEventListener('click', () => this.setTool(btn.dataset.tool));
        });
        
        // Action buttons
        document.getElementById('btn-undo')?.addEventListener('click', () => this.undo());
        document.getElementById('btn-redo')?.addEventListener('click', () => this.redo());
        document.getElementById('btn-delete')?.addEventListener('click', () => this.deleteSelected());
        document.getElementById('btn-duplicate')?.addEventListener('click', () => this.duplicateSelected());
        
        // Zoom controls
        document.getElementById('btn-zoom-in')?.addEventListener('click', () => this.zoomIn());
        document.getElementById('btn-zoom-out')?.addEventListener('click', () => this.zoomOut());
        document.getElementById('btn-zoom-fit')?.addEventListener('click', () => this.zoomToFit());
        
        // Grid/snap toggles
        document.getElementById('btn-toggle-grid')?.addEventListener('click', () => this.toggleGrid());
        document.getElementById('btn-toggle-snap')?.addEventListener('click', () => this.toggleSnap());
    },

    handleSvgClick(e) {
        if (this.currentTool !== 'select') return;
        
        const target = e.target;
        
        // Check if clicked on an element with ID
        if (target !== this.svgElement && target.id) {
            this.selectElement(target.id);
        } else if (target === this.svgElement) {
            this.clearSelection();
        }
    },

    handleMouseDown(e) {
        if (e.altKey || this.currentTool === 'pan') {
            this.isPanning = true;
            this.lastPanPoint = { x: e.clientX, y: e.clientY };
            this.canvasContainer.style.cursor = 'grabbing';
            e.preventDefault();
        }
    },

    handleMouseMove(e) {
        if (this.isPanning && this.lastPanPoint) {
            const deltaX = e.clientX - this.lastPanPoint.x;
            const deltaY = e.clientY - this.lastPanPoint.y;
            
            this.panX += deltaX;
            this.panY += deltaY;
            this.updateTransform();
            
            this.lastPanPoint = { x: e.clientX, y: e.clientY };
        }
    },

    handleMouseUp() {
        this.isPanning = false;
        this.lastPanPoint = null;
        this.canvasContainer.style.cursor = '';
    },

    handleWheel(e) {
        e.preventDefault();
        
        const delta = e.deltaY;
        let newZoom = this.zoom * (delta > 0 ? 0.9 : 1.1);
        newZoom = Math.min(Math.max(newZoom, this.minZoom), this.maxZoom);
        
        // Zoom towards cursor position
        const rect = this.canvasContainer.getBoundingClientRect();
        const cursorX = e.clientX - rect.left;
        const cursorY = e.clientY - rect.top;
        
        const scale = newZoom / this.zoom;
        this.panX = cursorX - scale * (cursorX - this.panX);
        this.panY = cursorY - scale * (cursorY - this.panY);
        
        this.zoom = newZoom;
        this.updateTransform();
        this.updateZoomDisplay();
    },

    handleKeyDown(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        
        if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
            e.preventDefault();
            if (e.shiftKey) {
                this.redo();
            } else {
                this.undo();
            }
        } else if ((e.ctrlKey || e.metaKey) && e.key === 'y') {
            e.preventDefault();
            this.redo();
        } else if (e.key === 'Delete' || e.key === 'Backspace') {
            if (document.activeElement === document.body) {
                e.preventDefault();
                this.deleteSelected();
            }
        } else if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
            e.preventDefault();
            this.duplicateSelected();
        } else if (e.key === 'Escape') {
            this.clearSelection();
        }
        
        // Tool shortcuts
        if (!e.ctrlKey && !e.metaKey) {
            switch (e.key.toLowerCase()) {
                case 'v': this.setTool('select'); break;
                case 'h': this.setTool('pan'); break;
                case 'r': this.setTool('rect'); break;
                case 'c': this.setTool('circle'); break;
                case 't': this.setTool('text'); break;
                case 'l': this.setTool('line'); break;
            }
        }
    },

    updateTransform() {
        const wrapper = this.canvasContainer.querySelector('.svg-canvas');
        if (wrapper) {
            wrapper.style.transform = `translate(${this.panX}px, ${this.panY}px) scale(${this.zoom})`;
            wrapper.style.transformOrigin = '0 0';
        }
    },

    // Selection
    selectElement(elementId) {
        this.clearSelection();
        
        const element = this.svgElement.getElementById(elementId);
        if (!element) return;
        
        this.selectedElement = element;
        this.selectedId = elementId;
        
        // Add selection outline
        element.classList.add('selected');
        
        // Show selection handles
        this.showSelectionHandles(element);
        
        // Update properties panel
        if (typeof DesignProperties !== 'undefined') {
            DesignProperties.updateFromElement(element);
        }
        
        this.updateActionButtons();
    },

    clearSelection() {
        if (this.selectedElement) {
            this.selectedElement.classList.remove('selected');
        }
        
        this.selectedElement = null;
        this.selectedId = null;
        
        // Clear selection handles
        if (this.selectionOverlay) {
            this.selectionOverlay.innerHTML = '';
        }
        
        // Update properties panel
        if (typeof DesignProperties !== 'undefined') {
            DesignProperties.clearSelection();
        }
        
        this.updateActionButtons();
    },

    showSelectionHandles(element) {
        if (!this.selectionOverlay) return;
        
        this.selectionOverlay.innerHTML = '';
        
        const bbox = element.getBBox();
        const ctm = element.getScreenCTM();
        const svgCtm = this.svgElement.getScreenCTM().inverse();
        
        // Transform bbox to screen coordinates
        const pt1 = this.svgElement.createSVGPoint();
        pt1.x = bbox.x;
        pt1.y = bbox.y;
        const screenPt1 = pt1.matrixTransform(ctm).matrixTransform(svgCtm);
        
        const pt2 = this.svgElement.createSVGPoint();
        pt2.x = bbox.x + bbox.width;
        pt2.y = bbox.y + bbox.height;
        const screenPt2 = pt2.matrixTransform(ctm).matrixTransform(svgCtm);
        
        const x = Math.min(screenPt1.x, screenPt2.x);
        const y = Math.min(screenPt1.y, screenPt2.y);
        const width = Math.abs(screenPt2.x - screenPt1.x);
        const height = Math.abs(screenPt2.y - screenPt1.y);
        
        // Create selection box
        const box = document.createElement('div');
        box.className = 'selection-box';
        box.style.left = x + 'px';
        box.style.top = y + 'px';
        box.style.width = width + 'px';
        box.style.height = height + 'px';
        this.selectionOverlay.appendChild(box);
        
        // Create resize handles
        const handles = ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'];
        handles.forEach(pos => {
            const handle = document.createElement('div');
            handle.className = `selection-handle ${pos}`;
            box.appendChild(handle);
        });
    },

    updateActionButtons() {
        const hasSelection = !!this.selectedElement;
        
        const btnDelete = document.getElementById('btn-delete');
        const btnDuplicate = document.getElementById('btn-duplicate');
        
        if (btnDelete) btnDelete.disabled = !hasSelection;
        if (btnDuplicate) btnDuplicate.disabled = !hasSelection;
        
        const btnUndo = document.getElementById('btn-undo');
        const btnRedo = document.getElementById('btn-redo');
        if (btnUndo) btnUndo.disabled = this.historyIndex <= 0;
        if (btnRedo) btnRedo.disabled = this.historyIndex >= this.history.length - 1;
    },

    // Canvas operations
    updateCanvasSize(width, height) {
        this.width = width;
        this.height = height;
        
        this.svgElement.setAttribute('width', width);
        this.svgElement.setAttribute('height', height);
        this.svgElement.setAttribute('viewBox', `0 0 ${width} ${height}`);
        
        this.canvasContainer.style.width = width + 'px';
        this.canvasContainer.style.height = height + 'px';
        
        this.updateCanvasInfo();
    },

    setBackground(color) {
        this.background = color;
        this.svgElement.style.background = color;
    },

    updateCanvasInfo() {
        const info = document.getElementById('canvas-dimensions');
        if (info) {
            info.textContent = `${this.width} x ${this.height}`;
        }
    },

    updateZoomDisplay() {
        const display = document.getElementById('zoom-level');
        if (display) {
            display.textContent = Math.round(this.zoom * 100) + '%';
        }
    },

    // Zoom
    zoomIn() {
        const newZoom = Math.min(this.zoom * 1.2, this.maxZoom);
        this.setZoom(newZoom);
    },

    zoomOut() {
        const newZoom = Math.max(this.zoom / 1.2, this.minZoom);
        this.setZoom(newZoom);
    },

    setZoom(zoom) {
        this.zoom = zoom;
        this.updateTransform();
        this.updateZoomDisplay();
    },

    zoomToFit() {
        const wrapper = document.querySelector('.canvas-wrapper');
        if (!wrapper) return;
        
        const padding = 60;
        const wrapperWidth = wrapper.clientWidth - padding * 2;
        const wrapperHeight = wrapper.clientHeight - padding * 2;
        
        const scaleX = wrapperWidth / this.width;
        const scaleY = wrapperHeight / this.height;
        const zoom = Math.min(scaleX, scaleY, 1);
        
        this.panX = (wrapper.clientWidth - this.width * zoom) / 2;
        this.panY = (wrapper.clientHeight - this.height * zoom) / 2;
        this.zoom = zoom;
        
        this.updateTransform();
        this.updateZoomDisplay();
    },

    // Grid & Snap
    toggleGrid() {
        this.showGrid = !this.showGrid;
        const btn = document.getElementById('btn-toggle-grid');
        if (btn) btn.classList.toggle('active', this.showGrid);
        // TODO: Implement grid overlay
    },

    toggleSnap() {
        this.snapToGrid = !this.snapToGrid;
        const btn = document.getElementById('btn-toggle-snap');
        if (btn) btn.classList.toggle('active', this.snapToGrid);
    },

    // Tool selection
    setTool(toolName) {
        this.currentTool = toolName;
        
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tool === toolName);
        });
        
        this.canvasContainer.style.cursor = toolName === 'pan' ? 'grab' : '';
    },

    // History
    saveHistory() {
        if (!this.isRecordingHistory) return;
        
        if (this.historyIndex < this.history.length - 1) {
            this.history = this.history.slice(0, this.historyIndex + 1);
        }
        
        const svgContent = this.svgElement.innerHTML;
        this.history.push({
            svg: svgContent,
            width: this.width,
            height: this.height,
            background: this.background
        });
        
        if (this.history.length > this.maxHistory) {
            this.history.shift();
        } else {
            this.historyIndex++;
        }
        
        this.updateActionButtons();
    },

    undo() {
        if (this.historyIndex <= 0) return;
        this.historyIndex--;
        this.loadFromHistory();
    },

    redo() {
        if (this.historyIndex >= this.history.length - 1) return;
        this.historyIndex++;
        this.loadFromHistory();
    },

    loadFromHistory() {
        this.isRecordingHistory = false;
        const state = this.history[this.historyIndex];
        
        this.svgElement.innerHTML = state.svg;
        this.updateCanvasSize(state.width, state.height);
        this.setBackground(state.background);
        
        this.clearSelection();
        this.isRecordingHistory = true;
        this.updateActionButtons();
    },

    // Element operations
    deleteSelected() {
        if (!this.selectedElement) return;
        
        this.selectedElement.remove();
        this.clearSelection();
        this.saveHistory();
    },

    duplicateSelected() {
        if (!this.selectedElement) return;
        
        const clone = this.selectedElement.cloneNode(true);
        const newId = 'el_' + Math.random().toString(36).substr(2, 8);
        clone.id = newId;
        
        // Offset the clone
        const x = parseFloat(clone.getAttribute('x') || clone.getAttribute('cx') || 0);
        const y = parseFloat(clone.getAttribute('y') || clone.getAttribute('cy') || 0);
        
        if (clone.hasAttribute('x')) {
            clone.setAttribute('x', x + 20);
        } else if (clone.hasAttribute('cx')) {
            clone.setAttribute('cx', x + 20);
        }
        
        if (clone.hasAttribute('y')) {
            clone.setAttribute('y', y + 20);
        } else if (clone.hasAttribute('cy')) {
            clone.setAttribute('cy', y + 20);
        }
        
        this.svgElement.appendChild(clone);
        this.selectElement(newId);
        this.saveHistory();
    },

    // Get element by ID
    getElementById(id) {
        return this.svgElement.getElementById(id);
    },

    // Update SVG content from server
    updateSVG(svgContent) {
        if (!svgContent) return;
        
        // Extract content from full SVG if needed
        const parser = new DOMParser();
        const doc = parser.parseFromString(svgContent, 'image/svg+xml');
        const svg = doc.querySelector('svg');
        
        if (svg) {
            // Update dimensions if present
            const width = svg.getAttribute('width');
            const height = svg.getAttribute('height');
            if (width && height) {
                this.updateCanvasSize(parseInt(width), parseInt(height));
            }
            
            // Update background from style
            const bgMatch = svg.getAttribute('style')?.match(/background-color:\s*([^;]+)/);
            if (bgMatch) {
                this.setBackground(bgMatch[1]);
            }
            
            // Update content
            this.svgElement.innerHTML = svg.innerHTML;
        } else {
            // Just set as inner content
            this.svgElement.innerHTML = svgContent;
        }
        
        this.clearSelection();
        this.saveHistory();
    },

    // Set complete state from server
    setState(state) {
        if (!state) return;
        
        if (state.width && state.height) {
            this.updateCanvasSize(state.width, state.height);
        }
        
        if (state.background) {
            this.setBackground(state.background);
        }
        
        if (state.svg) {
            this.updateSVG(state.svg);
        }
    },

    // Get current state
    getState() {
        return {
            width: this.width,
            height: this.height,
            background: this.background,
            svg: this.getSVG()
        };
    },

    // Get SVG content
    getSVG() {
        const svg = this.svgElement.cloneNode(true);
        svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
        return svg.outerHTML;
    },

    // Get inner SVG content (without wrapper)
    getInnerSVG() {
        return this.svgElement.innerHTML;
    },

    // Clear canvas
    clear() {
        this.svgElement.innerHTML = '';
        this.clearSelection();
        this.saveHistory();
    },

    // Export to data URL
    toDataURL(format = 'png', scale = 2) {
        return new Promise((resolve, reject) => {
            const svg = this.svgElement;
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            canvas.width = this.width * scale;
            canvas.height = this.height * scale;
            
            // Draw background
            ctx.fillStyle = this.background;
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Convert SVG to image
            const svgData = new XMLSerializer().serializeToString(svg);
            const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
            const url = URL.createObjectURL(svgBlob);
            
            const img = new Image();
            img.onload = () => {
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                URL.revokeObjectURL(url);
                
                const mimeType = format === 'jpg' ? 'image/jpeg' : 'image/png';
                resolve(canvas.toDataURL(mimeType, 0.9));
            };
            img.onerror = reject;
            img.src = url;
        });
    },

    // Capture screenshot for AI review
    captureScreenshot() {
        return this.toDataURL('png', 1);
    },

    // Layer operations
    bringToFront() {
        if (!this.selectedElement) return;
        this.svgElement.appendChild(this.selectedElement);
        this.saveHistory();
    },

    sendToBack() {
        if (!this.selectedElement) return;
        this.svgElement.insertBefore(this.selectedElement, this.svgElement.firstChild);
        this.saveHistory();
    },

    bringForward() {
        if (!this.selectedElement) return;
        const next = this.selectedElement.nextElementSibling;
        if (next) {
            this.svgElement.insertBefore(next, this.selectedElement);
            this.saveHistory();
        }
    },

    sendBackward() {
        if (!this.selectedElement) return;
        const prev = this.selectedElement.previousElementSibling;
        if (prev) {
            this.svgElement.insertBefore(this.selectedElement, prev);
            this.saveHistory();
        }
    }
};
