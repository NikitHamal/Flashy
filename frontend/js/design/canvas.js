/**
 * Design Canvas Module
 * Manages fabric.js canvas instance and canvas operations
 */
const DesignCanvas = {
    canvas: null,
    canvasContainer: null,
    zoom: 1,
    minZoom: 0.1,
    maxZoom: 5,
    isPanning: false,
    lastPanPoint: null,
    history: [],
    historyIndex: -1,
    maxHistory: 50,
    isRecordingHistory: true,
    canvasWidth: 1200,
    canvasHeight: 800,
    backgroundColor: '#FFFFFF',

    init() {
        this.canvasContainer = document.getElementById('canvas-container');
        const canvasEl = document.getElementById('design-canvas');

        this.canvas = new fabric.Canvas(canvasEl, {
            width: this.canvasWidth,
            height: this.canvasHeight,
            backgroundColor: this.backgroundColor,
            preserveObjectStacking: true,
            selection: true,
            selectionColor: 'rgba(74, 222, 128, 0.1)',
            selectionBorderColor: '#4ade80',
            selectionLineWidth: 1,
            hoverCursor: 'move',
            moveCursor: 'move',
            defaultCursor: 'default',
            freeDrawingCursor: 'crosshair',
            rotationCursor: 'crosshair',
            containerClass: 'canvas-container'
        });

        this.setupCanvasStyles();
        this.setupEventListeners();
        this.updateCanvasInfo();
        this.saveHistory();

        return this;
    },

    setupCanvasStyles() {
        fabric.Object.prototype.set({
            transparentCorners: false,
            cornerColor: '#4ade80',
            cornerStrokeColor: '#4ade80',
            borderColor: '#4ade80',
            cornerSize: 10,
            cornerStyle: 'circle',
            borderScaleFactor: 1.5,
            padding: 0
        });

        fabric.Object.prototype.controls.mtr.offsetY = -30;
    },

    setupEventListeners() {
        this.canvas.on('object:modified', () => this.saveHistory());
        this.canvas.on('object:added', () => {
            if (this.isRecordingHistory) this.saveHistory();
        });
        this.canvas.on('object:removed', () => {
            if (this.isRecordingHistory) this.saveHistory();
        });

        this.canvas.on('selection:created', () => this.onSelectionChange());
        this.canvas.on('selection:updated', () => this.onSelectionChange());
        this.canvas.on('selection:cleared', () => this.onSelectionChange());

        this.canvas.on('mouse:wheel', (opt) => this.handleMouseWheel(opt));
        this.canvas.on('mouse:down', (opt) => this.handleMouseDown(opt));
        this.canvas.on('mouse:move', (opt) => this.handleMouseMove(opt));
        this.canvas.on('mouse:up', () => this.handleMouseUp());

        document.addEventListener('keydown', (e) => this.handleKeyDown(e));

        document.getElementById('btn-zoom-in')?.addEventListener('click', () => this.zoomIn());
        document.getElementById('btn-zoom-out')?.addEventListener('click', () => this.zoomOut());
        document.getElementById('btn-zoom-fit')?.addEventListener('click', () => this.zoomToFit());
    },

    onSelectionChange() {
        const activeObject = this.canvas.getActiveObject();
        if (typeof DesignProperties !== 'undefined') {
            DesignProperties.updateFromSelection(activeObject);
        }
        this.updateActionButtons();
    },

    updateActionButtons() {
        const hasSelection = !!this.canvas.getActiveObject();
        const btnDelete = document.getElementById('btn-delete');
        const btnDuplicate = document.getElementById('btn-duplicate');

        if (btnDelete) btnDelete.disabled = !hasSelection;
        if (btnDuplicate) btnDuplicate.disabled = !hasSelection;

        const btnUndo = document.getElementById('btn-undo');
        const btnRedo = document.getElementById('btn-redo');
        if (btnUndo) btnUndo.disabled = this.historyIndex <= 0;
        if (btnRedo) btnRedo.disabled = this.historyIndex >= this.history.length - 1;
    },

    handleMouseWheel(opt) {
        const delta = opt.e.deltaY;
        let newZoom = this.zoom * (delta > 0 ? 0.9 : 1.1);
        newZoom = Math.min(Math.max(newZoom, this.minZoom), this.maxZoom);

        const point = new fabric.Point(opt.e.offsetX, opt.e.offsetY);
        this.canvas.zoomToPoint(point, newZoom);
        this.zoom = newZoom;

        this.updateZoomDisplay();
        opt.e.preventDefault();
        opt.e.stopPropagation();
    },

    handleMouseDown(opt) {
        if (opt.e.altKey || this.currentTool === 'hand') {
            this.isPanning = true;
            this.lastPanPoint = { x: opt.e.clientX, y: opt.e.clientY };
            this.canvas.selection = false;
            this.canvas.defaultCursor = 'grabbing';
        }
    },

    handleMouseMove(opt) {
        if (this.isPanning && this.lastPanPoint) {
            const deltaX = opt.e.clientX - this.lastPanPoint.x;
            const deltaY = opt.e.clientY - this.lastPanPoint.y;

            const vpt = this.canvas.viewportTransform;
            vpt[4] += deltaX;
            vpt[5] += deltaY;
            this.canvas.requestRenderAll();

            this.lastPanPoint = { x: opt.e.clientX, y: opt.e.clientY };
        }
    },

    handleMouseUp() {
        this.isPanning = false;
        this.lastPanPoint = null;
        this.canvas.selection = true;
        this.canvas.defaultCursor = 'default';
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
        } else if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
            e.preventDefault();
            this.selectAll();
        } else if (e.key === 'Escape') {
            this.canvas.discardActiveObject();
            this.canvas.requestRenderAll();
        }

        if (!e.ctrlKey && !e.metaKey) {
            switch (e.key.toLowerCase()) {
                case 'v':
                    this.setTool('select');
                    break;
                case 'h':
                    this.setTool('hand');
                    break;
                case 'r':
                    this.setTool('rectangle');
                    break;
                case 'c':
                    this.setTool('circle');
                    break;
                case 't':
                    this.setTool('text');
                    break;
                case 'l':
                    this.setTool('line');
                    break;
            }
        }
    },

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
        const center = this.canvas.getCenter();
        this.canvas.zoomToPoint(new fabric.Point(center.left, center.top), zoom);
        this.updateZoomDisplay();
    },

    zoomToFit() {
        const wrapper = document.querySelector('.canvas-wrapper');
        if (!wrapper) return;

        const padding = 60;
        const wrapperWidth = wrapper.clientWidth - padding * 2;
        const wrapperHeight = wrapper.clientHeight - padding * 2;

        const scaleX = wrapperWidth / this.canvasWidth;
        const scaleY = wrapperHeight / this.canvasHeight;
        const zoom = Math.min(scaleX, scaleY, 1);

        this.setZoom(zoom);
        this.canvas.viewportTransform[4] = (wrapper.clientWidth - this.canvasWidth * zoom) / 2;
        this.canvas.viewportTransform[5] = (wrapper.clientHeight - this.canvasHeight * zoom) / 2;
        this.canvas.requestRenderAll();
    },

    updateZoomDisplay() {
        const zoomDisplay = document.getElementById('zoom-level');
        if (zoomDisplay) {
            zoomDisplay.textContent = Math.round(this.zoom * 100) + '%';
        }
    },

    updateCanvasInfo() {
        const info = document.getElementById('canvas-dimensions');
        if (info) {
            info.textContent = `${this.canvasWidth} × ${this.canvasHeight}`;
        }
    },

    saveHistory() {
        if (!this.isRecordingHistory) return;

        if (this.historyIndex < this.history.length - 1) {
            this.history = this.history.slice(0, this.historyIndex + 1);
        }

        const json = this.canvas.toJSON(['id', 'selectable', 'hasControls']);
        this.history.push(JSON.stringify(json));

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
        const json = JSON.parse(this.history[this.historyIndex]);
        this.canvas.loadFromJSON(json, () => {
            this.canvas.requestRenderAll();
            this.isRecordingHistory = true;
            this.updateActionButtons();
        });
    },

    deleteSelected() {
        const activeObjects = this.canvas.getActiveObjects();
        if (activeObjects.length === 0) return;

        this.canvas.discardActiveObject();
        activeObjects.forEach(obj => this.canvas.remove(obj));
        this.canvas.requestRenderAll();
    },

    duplicateSelected() {
        const activeObject = this.canvas.getActiveObject();
        if (!activeObject) return;

        activeObject.clone((cloned) => {
            cloned.set({
                left: cloned.left + 20,
                top: cloned.top + 20,
                evented: true
            });

            if (cloned.type === 'activeSelection') {
                cloned.canvas = this.canvas;
                cloned.forEachObject((obj) => {
                    this.canvas.add(obj);
                });
                cloned.setCoords();
            } else {
                this.canvas.add(cloned);
            }

            this.canvas.setActiveObject(cloned);
            this.canvas.requestRenderAll();
        });
    },

    selectAll() {
        const allObjects = this.canvas.getObjects();
        if (allObjects.length === 0) return;

        const selection = new fabric.ActiveSelection(allObjects, {
            canvas: this.canvas
        });
        this.canvas.setActiveObject(selection);
        this.canvas.requestRenderAll();
    },

    setCanvasSize(width, height) {
        this.canvasWidth = width;
        this.canvasHeight = height;
        this.canvas.setWidth(width);
        this.canvas.setHeight(height);
        this.canvas.requestRenderAll();
        this.updateCanvasInfo();
        this.saveHistory();
    },

    setBackgroundColor(color) {
        this.backgroundColor = color;
        this.canvas.setBackgroundColor(color, () => {
            this.canvas.requestRenderAll();
            this.saveHistory();
        });
    },

    clear() {
        this.canvas.clear();
        this.canvas.setBackgroundColor(this.backgroundColor);
        this.canvas.requestRenderAll();
        this.saveHistory();
    },

    toDataURL(options = {}) {
        const defaults = {
            format: 'png',
            quality: 1,
            multiplier: 2
        };
        return this.canvas.toDataURL({ ...defaults, ...options });
    },

    toSVG() {
        return this.canvas.toSVG();
    },

    toJSON() {
        return this.canvas.toJSON(['id', 'selectable', 'hasControls']);
    },

    loadFromJSON(json) {
        return new Promise((resolve) => {
            this.canvas.loadFromJSON(json, () => {
                this.canvas.requestRenderAll();
                this.canvasWidth = this.canvas.width;
                this.canvasHeight = this.canvas.height;
                this.backgroundColor = this.canvas.backgroundColor || '#FFFFFF';
                this.updateCanvasInfo();
                this.history = [];
                this.historyIndex = -1;
                this.saveHistory();
                resolve();
            });
        });
    },

    getState() {
        return {
            width: this.canvasWidth,
            height: this.canvasHeight,
            background: this.backgroundColor,
            objects: this.canvas.toJSON(['id', 'selectable', 'hasControls']).objects
        };
    },

    captureScreenshot() {
        return this.canvas.toDataURL({
            format: 'png',
            quality: 0.9,
            multiplier: 1
        });
    },

    setTool(toolName) {
        this.currentTool = toolName;

        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.tool === toolName) {
                btn.classList.add('active');
            }
        });

        this.canvas.isDrawingMode = false;
        this.canvas.selection = true;
        this.canvas.defaultCursor = 'default';

        if (toolName === 'hand') {
            this.canvas.selection = false;
            this.canvas.defaultCursor = 'grab';
        } else if (toolName === 'pencil' || toolName === 'pen') {
            this.canvas.isDrawingMode = true;
            this.canvas.freeDrawingBrush.width = 2;
            this.canvas.freeDrawingBrush.color = '#000000';
        }
    },

    addObject(fabricObject) {
        this.canvas.add(fabricObject);
        this.canvas.setActiveObject(fabricObject);
        this.canvas.requestRenderAll();
    },

    getObjectById(id) {
        return this.canvas.getObjects().find(obj => obj.id === id);
    },

    removeObjectById(id) {
        const obj = this.getObjectById(id);
        if (obj) {
            this.canvas.remove(obj);
            this.canvas.requestRenderAll();
        }
    },

    updateObjectById(id, properties) {
        const obj = this.getObjectById(id);
        if (obj) {
            obj.set(properties);
            obj.setCoords();
            this.canvas.requestRenderAll();
            this.saveHistory();
        }
    },

    bringToFront() {
        const activeObject = this.canvas.getActiveObject();
        if (activeObject) {
            this.canvas.bringToFront(activeObject);
            this.canvas.requestRenderAll();
            this.saveHistory();
        }
    },

    sendToBack() {
        const activeObject = this.canvas.getActiveObject();
        if (activeObject) {
            this.canvas.sendToBack(activeObject);
            this.canvas.requestRenderAll();
            this.saveHistory();
        }
    },

    bringForward() {
        const activeObject = this.canvas.getActiveObject();
        if (activeObject) {
            this.canvas.bringForward(activeObject);
            this.canvas.requestRenderAll();
            this.saveHistory();
        }
    },

    sendBackward() {
        const activeObject = this.canvas.getActiveObject();
        if (activeObject) {
            this.canvas.sendBackwards(activeObject);
            this.canvas.requestRenderAll();
            this.saveHistory();
        }
    }
};
