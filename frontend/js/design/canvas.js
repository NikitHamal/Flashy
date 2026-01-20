const DesignCanvas = {
    svgRoot: null,
    svgContainer: null,
    overlayLayer: null,
    zoom: 1,
    panX: 0,
    panY: 0,
    isPanning: false,
    lastPanPoint: null,
    selectedElement: null,
    width: 1200,
    height: 800,
    background: "#FFFFFF",
    history: [],
    historyIndex: -1,
    maxHistory: 50,

    init() {
        this.svgContainer = document.getElementById("svg-canvas");
        this.createBaseSvg();
        this.setupEventListeners();
        this.saveHistory();
        this.updateCanvasInfo();
        return this;
    },

    createBaseSvg() {
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("width", this.width);
        svg.setAttribute("height", this.height);
        svg.setAttribute("viewBox", `0 0 ${this.width} ${this.height}`);
        svg.classList.add("design-svg");

        const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        bg.setAttribute("id", "bg");
        bg.setAttribute("x", "0");
        bg.setAttribute("y", "0");
        bg.setAttribute("width", this.width);
        bg.setAttribute("height", this.height);
        bg.setAttribute("fill", this.background);
        svg.appendChild(bg);

        const artwork = document.createElementNS("http://www.w3.org/2000/svg", "g");
        artwork.setAttribute("id", "artwork");
        svg.appendChild(artwork);

        const overlay = document.createElementNS("http://www.w3.org/2000/svg", "g");
        overlay.setAttribute("id", "overlay");
        svg.appendChild(overlay);
        this.overlayLayer = overlay;

        this.svgContainer.innerHTML = "";
        this.svgContainer.appendChild(svg);
        this.svgRoot = svg;
        this.applyTransform();
    },

    setupEventListeners() {
        this.svgContainer.addEventListener("click", (event) => {
            const target = event.target;
            if (!this.svgRoot || target === this.svgRoot || target.id === "bg") {
                this.clearSelection();
                return;
            }
            if (target.closest("#overlay")) return;
            this.setSelection(target);
        });

        this.svgContainer.addEventListener("wheel", (event) => {
            event.preventDefault();
            const delta = event.deltaY > 0 ? -0.1 : 0.1;
            this.zoom = Math.min(3, Math.max(0.2, this.zoom + delta));
            this.applyTransform();
            this.updateZoomDisplay();
        });

        this.svgContainer.addEventListener("mousedown", (event) => {
            if (event.button !== 1 && !event.altKey) return;
            this.isPanning = true;
            this.lastPanPoint = { x: event.clientX, y: event.clientY };
        });

        window.addEventListener("mousemove", (event) => {
            if (!this.isPanning) return;
            const dx = event.clientX - this.lastPanPoint.x;
            const dy = event.clientY - this.lastPanPoint.y;
            this.panX += dx;
            this.panY += dy;
            this.lastPanPoint = { x: event.clientX, y: event.clientY };
            this.applyTransform();
        });

        window.addEventListener("mouseup", () => {
            this.isPanning = false;
            this.lastPanPoint = null;
        });

        document.getElementById("btn-zoom-in")?.addEventListener("click", () => this.setZoom(this.zoom + 0.1));
        document.getElementById("btn-zoom-out")?.addEventListener("click", () => this.setZoom(this.zoom - 0.1));
        document.getElementById("btn-zoom-fit")?.addEventListener("click", () => this.zoomToFit());
        document.getElementById("btn-toggle-grid")?.addEventListener("click", () => this.toggleGrid());
        document.getElementById("btn-toggle-snap")?.addEventListener("click", () => this.toggleSnap());
        document.getElementById("btn-toggle-guides")?.addEventListener("click", () => this.toggleGuides());
    },

    setZoom(value) {
        this.zoom = Math.min(3, Math.max(0.2, value));
        this.applyTransform();
        this.updateZoomDisplay();
    },

    zoomToFit() {
        this.zoom = 1;
        this.panX = 0;
        this.panY = 0;
        this.applyTransform();
        this.updateZoomDisplay();
    },

    applyTransform() {
        if (!this.svgRoot) return;
        this.svgRoot.style.transformOrigin = "0 0";
        this.svgRoot.style.transform = `translate(${this.panX}px, ${this.panY}px) scale(${this.zoom})`;
    },

    toggleGrid() {
        const grid = document.getElementById("canvas-grid");
        if (!grid) return;
        grid.classList.toggle("hidden");
    },

    toggleSnap() {
        const btn = document.getElementById("btn-toggle-snap");
        btn?.classList.toggle("active");
    },

    toggleGuides() {
        const btn = document.getElementById("btn-toggle-guides");
        btn?.classList.toggle("active");
    },

    updateZoomDisplay() {
        const zoomLabel = document.getElementById("zoom-level");
        if (zoomLabel) zoomLabel.textContent = `${Math.round(this.zoom * 100)}%`;
    },

    updateCanvasInfo() {
        const label = document.getElementById("canvas-dimensions");
        if (label) label.textContent = `${this.width} × ${this.height}`;
    },

    getArtworkLayer() {
        return this.svgRoot?.querySelector("#artwork");
    },

    addElement(tag, attrs = {}, content = "") {
        const artwork = this.getArtworkLayer();
        if (!artwork) return;
        const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
        Object.entries(attrs).forEach(([key, val]) => el.setAttribute(key, val));
        if (content) el.textContent = content;
        if (!el.getAttribute("id")) {
            el.setAttribute("id", `el_${Date.now()}`);
        }
        artwork.appendChild(el);
        this.saveHistory();
        this.setSelection(el);
    },

    setSelection(element) {
        this.clearSelection();
        this.selectedElement = element;
        this.drawSelectionBox();
        if (typeof DesignProperties !== "undefined") {
            DesignProperties.updateFromSelection(element);
        }
    },

    clearSelection() {
        this.selectedElement = null;
        this.clearOverlay();
        if (typeof DesignProperties !== "undefined") {
            DesignProperties.updateFromSelection(null);
        }
    },

    drawSelectionBox() {
        if (!this.selectedElement || !this.overlayLayer) return;
        const box = this.selectedElement.getBBox();
        this.clearOverlay();
        const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        rect.setAttribute("x", box.x - 4);
        rect.setAttribute("y", box.y - 4);
        rect.setAttribute("width", box.width + 8);
        rect.setAttribute("height", box.height + 8);
        rect.setAttribute("fill", "none");
        rect.setAttribute("stroke", "#14120e");
        rect.setAttribute("stroke-width", "2");
        rect.setAttribute("vector-effect", "non-scaling-stroke");
        this.overlayLayer.appendChild(rect);
    },

    clearOverlay() {
        if (!this.overlayLayer) return;
        this.overlayLayer.innerHTML = "";
    },

    updateSelectedAttributes(attrs) {
        if (!this.selectedElement) return;
        Object.entries(attrs).forEach(([key, val]) => {
            if (val === null || val === undefined) return;
            this.selectedElement.setAttribute(key, val);
        });
        this.saveHistory();
        this.drawSelectionBox();
    },

    deleteSelection() {
        if (!this.selectedElement) return;
        this.selectedElement.remove();
        this.clearSelection();
        this.saveHistory();
    },

    duplicateSelection() {
        if (!this.selectedElement) return;
        const clone = this.selectedElement.cloneNode(true);
        clone.setAttribute("id", `el_${Date.now()}`);
        const artwork = this.getArtworkLayer();
        artwork.appendChild(clone);
        this.saveHistory();
        this.setSelection(clone);
    },

    setBackground(color) {
        this.background = color;
        const bg = this.svgRoot?.querySelector("#bg");
        if (bg) bg.setAttribute("fill", color);
        this.saveHistory();
    },

    getState() {
        return {
            width: this.width,
            height: this.height,
            background: this.background,
            svg: this.getSvgString()
        };
    },

    setState(state) {
        if (!state) return;
        this.width = state.width || this.width;
        this.height = state.height || this.height;
        this.background = state.background || this.background;
        this.svgContainer.innerHTML = state.svg || "";
        this.svgRoot = this.svgContainer.querySelector("svg");
        if (!this.svgRoot) {
            this.createBaseSvg();
        } else {
            this.overlayLayer = this.svgRoot.querySelector("#overlay");
            if (!this.overlayLayer) {
                this.overlayLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
                this.overlayLayer.setAttribute("id", "overlay");
                this.svgRoot.appendChild(this.overlayLayer);
            }
        }
        this.applyTransform();
        this.updateCanvasInfo();
        this.saveHistory(false);
    },

    getSvgString() {
        return this.svgRoot ? this.svgRoot.outerHTML : "";
    },

    saveHistory(record = true) {
        if (!record) return;
        const snapshot = this.getSvgString();
        if (this.historyIndex < this.history.length - 1) {
            this.history = this.history.slice(0, this.historyIndex + 1);
        }
        this.history.push(snapshot);
        if (this.history.length > this.maxHistory) {
            this.history.shift();
        } else {
            this.historyIndex += 1;
        }
    },

    undo() {
        if (this.historyIndex <= 0) return;
        this.historyIndex -= 1;
        this.svgContainer.innerHTML = this.history[this.historyIndex];
        this.svgRoot = this.svgContainer.querySelector("svg");
        this.overlayLayer = this.svgRoot.querySelector("#overlay");
        this.applyTransform();
    },

    redo() {
        if (this.historyIndex >= this.history.length - 1) return;
        this.historyIndex += 1;
        this.svgContainer.innerHTML = this.history[this.historyIndex];
        this.svgRoot = this.svgContainer.querySelector("svg");
        this.overlayLayer = this.svgRoot.querySelector("#overlay");
        this.applyTransform();
    },

    async captureScreenshot() {
        const svgData = this.getSvgString();
        if (!svgData) return null;
        const canvas = document.createElement("canvas");
        canvas.width = this.width;
        canvas.height = this.height;
        const ctx = canvas.getContext("2d");
        const img = new Image();
        const svgBlob = new Blob([svgData], { type: "image/svg+xml;charset=utf-8" });
        const url = URL.createObjectURL(svgBlob);
        await new Promise((resolve) => {
            img.onload = () => resolve();
            img.src = url;
        });
        ctx.drawImage(img, 0, 0);
        URL.revokeObjectURL(url);
        return canvas.toDataURL("image/png");
    }
};
