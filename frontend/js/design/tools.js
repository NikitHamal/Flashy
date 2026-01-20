/**
 * Design Tools Module (SVG-based)
 * Handles shape creation, drawing tools, and tool interactions for native SVG
 */
const DesignTools = {
    currentTool: 'select',
    isDrawing: false,
    startPoint: null,
    tempElement: null,
    
    // Default styling
    defaultFill: '#4ade80',
    defaultStroke: '#000000',
    defaultStrokeWidth: 3,
    
    // SVG namespace
    svgNS: 'http://www.w3.org/2000/svg',

    init() {
        this.setupToolButtons();
        this.setupCanvasDrawing();
        this.setupQuickActions();
        return this;
    },

    setupToolButtons() {
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tool = btn.dataset.tool;
                if (tool) {
                    this.setTool(tool);
                }
            });
        });
    },

    setTool(toolName) {
        this.currentTool = toolName;
        
        // Update UI
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tool === toolName);
        });
        
        // Update cursor
        const container = document.getElementById('canvas-container');
        if (container) {
            container.style.cursor = toolName === 'pan' ? 'grab' : 
                                     toolName === 'select' ? 'default' : 'crosshair';
        }
        
        // Trigger image upload for image tool
        if (toolName === 'image') {
            this.triggerImageUpload();
        }
    },

    setupCanvasDrawing() {
        const svg = document.getElementById('design-svg');
        if (!svg) return;
        
        svg.addEventListener('mousedown', (e) => this.onMouseDown(e));
        svg.addEventListener('mousemove', (e) => this.onMouseMove(e));
        svg.addEventListener('mouseup', (e) => this.onMouseUp(e));
        svg.addEventListener('mouseleave', (e) => this.onMouseUp(e));
    },

    getMousePosition(e) {
        const svg = document.getElementById('design-svg');
        if (!svg) return { x: 0, y: 0 };
        
        const rect = svg.getBoundingClientRect();
        const zoom = DesignCanvas?.zoom || 1;
        
        return {
            x: (e.clientX - rect.left) / zoom,
            y: (e.clientY - rect.top) / zoom
        };
    },

    onMouseDown(e) {
        // Skip for select, pan tools or when clicking on existing elements
        if (this.currentTool === 'select' || this.currentTool === 'pan') return;
        if (e.target !== document.getElementById('design-svg')) return;
        
        const point = this.getMousePosition(e);
        this.isDrawing = true;
        this.startPoint = point;
        
        this.createTempElement(point);
    },

    onMouseMove(e) {
        if (!this.isDrawing || !this.tempElement) return;
        
        const point = this.getMousePosition(e);
        this.updateTempElement(point);
    },

    onMouseUp(e) {
        if (!this.isDrawing) return;
        
        this.isDrawing = false;
        
        if (this.tempElement) {
            // Check if shape is too small (click without drag)
            const bbox = this.tempElement.getBBox();
            
            if (bbox.width < 5 && bbox.height < 5) {
                // Remove tiny temp element
                this.tempElement.remove();
                
                // Create default-sized shape at click position
                if (this.currentTool === 'text') {
                    this.createText(this.startPoint.x, this.startPoint.y);
                } else {
                    this.createDefaultShape(this.startPoint.x, this.startPoint.y);
                }
            } else {
                // Keep the drawn shape and select it
                DesignCanvas.selectElement(this.tempElement.id);
                DesignCanvas.saveHistory();
            }
        }
        
        this.tempElement = null;
        this.startPoint = null;
        
        // Return to select tool
        this.setTool('select');
    },

    createTempElement(point) {
        const svg = document.getElementById('design-svg');
        if (!svg) return;
        
        const id = this.generateId();
        let element = null;
        
        switch (this.currentTool) {
            case 'rect':
            case 'rectangle':
                element = document.createElementNS(this.svgNS, 'rect');
                element.setAttribute('x', point.x);
                element.setAttribute('y', point.y);
                element.setAttribute('width', 0);
                element.setAttribute('height', 0);
                element.setAttribute('fill', this.defaultFill);
                element.setAttribute('stroke', this.defaultStroke);
                element.setAttribute('stroke-width', this.defaultStrokeWidth);
                break;
                
            case 'circle':
                element = document.createElementNS(this.svgNS, 'circle');
                element.setAttribute('cx', point.x);
                element.setAttribute('cy', point.y);
                element.setAttribute('r', 0);
                element.setAttribute('fill', this.defaultFill);
                element.setAttribute('stroke', this.defaultStroke);
                element.setAttribute('stroke-width', this.defaultStrokeWidth);
                break;
                
            case 'ellipse':
                element = document.createElementNS(this.svgNS, 'ellipse');
                element.setAttribute('cx', point.x);
                element.setAttribute('cy', point.y);
                element.setAttribute('rx', 0);
                element.setAttribute('ry', 0);
                element.setAttribute('fill', this.defaultFill);
                element.setAttribute('stroke', this.defaultStroke);
                element.setAttribute('stroke-width', this.defaultStrokeWidth);
                break;
                
            case 'line':
                element = document.createElementNS(this.svgNS, 'line');
                element.setAttribute('x1', point.x);
                element.setAttribute('y1', point.y);
                element.setAttribute('x2', point.x);
                element.setAttribute('y2', point.y);
                element.setAttribute('stroke', this.defaultStroke);
                element.setAttribute('stroke-width', this.defaultStrokeWidth || 2);
                break;
                
            case 'triangle':
                element = document.createElementNS(this.svgNS, 'polygon');
                element.setAttribute('points', `${point.x},${point.y} ${point.x},${point.y} ${point.x},${point.y}`);
                element.setAttribute('fill', this.defaultFill);
                element.setAttribute('stroke', this.defaultStroke);
                element.setAttribute('stroke-width', this.defaultStrokeWidth);
                break;
                
            case 'polygon':
                element = document.createElementNS(this.svgNS, 'polygon');
                element.setAttribute('points', this.createPolygonPoints(point, 0, 6));
                element.setAttribute('fill', this.defaultFill);
                element.setAttribute('stroke', this.defaultStroke);
                element.setAttribute('stroke-width', this.defaultStrokeWidth);
                break;
                
            case 'star':
                element = document.createElementNS(this.svgNS, 'polygon');
                element.setAttribute('points', this.createStarPoints(point, 0, 0, 5));
                element.setAttribute('fill', this.defaultFill);
                element.setAttribute('stroke', this.defaultStroke);
                element.setAttribute('stroke-width', this.defaultStrokeWidth);
                break;
                
            case 'text':
                // Don't create temp element for text, will create on mouse up
                return;
                
            default:
                return;
        }
        
        if (element) {
            element.id = id;
            this.tempElement = element;
            svg.appendChild(element);
        }
    },

    updateTempElement(point) {
        if (!this.tempElement || !this.startPoint) return;
        
        const dx = point.x - this.startPoint.x;
        const dy = point.y - this.startPoint.y;
        
        switch (this.currentTool) {
            case 'rect':
            case 'rectangle':
                this.tempElement.setAttribute('x', dx > 0 ? this.startPoint.x : point.x);
                this.tempElement.setAttribute('y', dy > 0 ? this.startPoint.y : point.y);
                this.tempElement.setAttribute('width', Math.abs(dx));
                this.tempElement.setAttribute('height', Math.abs(dy));
                break;
                
            case 'circle':
                const radius = Math.sqrt(dx * dx + dy * dy) / 2;
                this.tempElement.setAttribute('cx', this.startPoint.x + dx / 2);
                this.tempElement.setAttribute('cy', this.startPoint.y + dy / 2);
                this.tempElement.setAttribute('r', radius);
                break;
                
            case 'ellipse':
                this.tempElement.setAttribute('cx', this.startPoint.x + dx / 2);
                this.tempElement.setAttribute('cy', this.startPoint.y + dy / 2);
                this.tempElement.setAttribute('rx', Math.abs(dx) / 2);
                this.tempElement.setAttribute('ry', Math.abs(dy) / 2);
                break;
                
            case 'line':
                this.tempElement.setAttribute('x2', point.x);
                this.tempElement.setAttribute('y2', point.y);
                break;
                
            case 'triangle':
                // Equilateral-ish triangle
                const width = Math.abs(dx);
                const height = Math.abs(dy);
                const baseX = dx > 0 ? this.startPoint.x : point.x;
                const baseY = dy > 0 ? this.startPoint.y + height : this.startPoint.y;
                const topX = baseX + width / 2;
                const topY = dy > 0 ? this.startPoint.y : this.startPoint.y + height;
                this.tempElement.setAttribute('points', 
                    `${topX},${topY} ${baseX},${baseY} ${baseX + width},${baseY}`);
                break;
                
            case 'polygon':
                const polyRadius = Math.sqrt(dx * dx + dy * dy) / 2;
                const polyCenter = { x: this.startPoint.x + dx / 2, y: this.startPoint.y + dy / 2 };
                this.tempElement.setAttribute('points', this.createPolygonPoints(polyCenter, polyRadius, 6));
                break;
                
            case 'star':
                const starOuterRadius = Math.sqrt(dx * dx + dy * dy) / 2;
                const starInnerRadius = starOuterRadius * 0.4;
                const starCenter = { x: this.startPoint.x + dx / 2, y: this.startPoint.y + dy / 2 };
                this.tempElement.setAttribute('points', this.createStarPoints(starCenter, starOuterRadius, starInnerRadius, 5));
                break;
        }
    },

    createDefaultShape(x, y) {
        const svg = document.getElementById('design-svg');
        if (!svg) return null;
        
        const id = this.generateId();
        let element = null;
        
        switch (this.currentTool) {
            case 'rect':
            case 'rectangle':
                element = document.createElementNS(this.svgNS, 'rect');
                element.setAttribute('x', x);
                element.setAttribute('y', y);
                element.setAttribute('width', 100);
                element.setAttribute('height', 100);
                element.setAttribute('fill', this.defaultFill);
                element.setAttribute('stroke', this.defaultStroke);
                element.setAttribute('stroke-width', this.defaultStrokeWidth);
                break;
                
            case 'circle':
                element = document.createElementNS(this.svgNS, 'circle');
                element.setAttribute('cx', x + 50);
                element.setAttribute('cy', y + 50);
                element.setAttribute('r', 50);
                element.setAttribute('fill', this.defaultFill);
                element.setAttribute('stroke', this.defaultStroke);
                element.setAttribute('stroke-width', this.defaultStrokeWidth);
                break;
                
            case 'ellipse':
                element = document.createElementNS(this.svgNS, 'ellipse');
                element.setAttribute('cx', x + 60);
                element.setAttribute('cy', y + 40);
                element.setAttribute('rx', 60);
                element.setAttribute('ry', 40);
                element.setAttribute('fill', this.defaultFill);
                element.setAttribute('stroke', this.defaultStroke);
                element.setAttribute('stroke-width', this.defaultStrokeWidth);
                break;
                
            case 'line':
                element = document.createElementNS(this.svgNS, 'line');
                element.setAttribute('x1', x);
                element.setAttribute('y1', y);
                element.setAttribute('x2', x + 100);
                element.setAttribute('y2', y);
                element.setAttribute('stroke', this.defaultStroke);
                element.setAttribute('stroke-width', this.defaultStrokeWidth || 2);
                break;
                
            case 'triangle':
                element = document.createElementNS(this.svgNS, 'polygon');
                element.setAttribute('points', `${x + 50},${y} ${x},${y + 100} ${x + 100},${y + 100}`);
                element.setAttribute('fill', this.defaultFill);
                element.setAttribute('stroke', this.defaultStroke);
                element.setAttribute('stroke-width', this.defaultStrokeWidth);
                break;
                
            case 'polygon':
                element = document.createElementNS(this.svgNS, 'polygon');
                element.setAttribute('points', this.createPolygonPoints({ x: x + 50, y: y + 50 }, 50, 6));
                element.setAttribute('fill', this.defaultFill);
                element.setAttribute('stroke', this.defaultStroke);
                element.setAttribute('stroke-width', this.defaultStrokeWidth);
                break;
                
            case 'star':
                element = document.createElementNS(this.svgNS, 'polygon');
                element.setAttribute('points', this.createStarPoints({ x: x + 50, y: y + 50 }, 50, 20, 5));
                element.setAttribute('fill', this.defaultFill);
                element.setAttribute('stroke', this.defaultStroke);
                element.setAttribute('stroke-width', this.defaultStrokeWidth);
                break;
        }
        
        if (element) {
            element.id = id;
            svg.appendChild(element);
            DesignCanvas.selectElement(id);
            DesignCanvas.saveHistory();
            return id;
        }
        
        return null;
    },

    createText(x, y, text = 'Text') {
        const svg = document.getElementById('design-svg');
        if (!svg) return null;
        
        const id = this.generateId();
        const element = document.createElementNS(this.svgNS, 'text');
        
        element.id = id;
        element.setAttribute('x', x);
        element.setAttribute('y', y);
        element.setAttribute('font-family', 'Inter, sans-serif');
        element.setAttribute('font-size', '32');
        element.setAttribute('fill', '#000000');
        element.textContent = text;
        
        svg.appendChild(element);
        DesignCanvas.selectElement(id);
        DesignCanvas.saveHistory();
        
        return id;
    },

    createPolygonPoints(center, radius, sides) {
        if (radius <= 0) return `${center.x},${center.y}`;
        
        const points = [];
        const angle = (2 * Math.PI) / sides;
        const startAngle = -Math.PI / 2;
        
        for (let i = 0; i < sides; i++) {
            const x = center.x + radius * Math.cos(startAngle + i * angle);
            const y = center.y + radius * Math.sin(startAngle + i * angle);
            points.push(`${x},${y}`);
        }
        
        return points.join(' ');
    },

    createStarPoints(center, outerRadius, innerRadius, points) {
        if (outerRadius <= 0) return `${center.x},${center.y}`;
        if (innerRadius <= 0) innerRadius = outerRadius * 0.4;
        
        const starPoints = [];
        const angle = Math.PI / points;
        const startAngle = -Math.PI / 2;
        
        for (let i = 0; i < points * 2; i++) {
            const radius = i % 2 === 0 ? outerRadius : innerRadius;
            const x = center.x + radius * Math.cos(startAngle + i * angle);
            const y = center.y + radius * Math.sin(startAngle + i * angle);
            starPoints.push(`${x},${y}`);
        }
        
        return starPoints.join(' ');
    },

    triggerImageUpload() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                this.addImageFromFile(file);
            }
        };
        input.click();
        
        // Return to select after triggering
        setTimeout(() => this.setTool('select'), 100);
    },

    addImageFromFile(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            this.addImageFromURL(e.target.result);
        };
        reader.readAsDataURL(file);
    },

    addImageFromURL(url, options = {}) {
        const svg = document.getElementById('design-svg');
        if (!svg) return null;
        
        const id = this.generateId();
        const element = document.createElementNS(this.svgNS, 'image');
        
        element.id = id;
        element.setAttributeNS('http://www.w3.org/1999/xlink', 'href', url);
        element.setAttribute('x', options.x || 100);
        element.setAttribute('y', options.y || 100);
        element.setAttribute('width', options.width || 200);
        element.setAttribute('height', options.height || 200);
        element.setAttribute('preserveAspectRatio', 'xMidYMid meet');
        
        svg.appendChild(element);
        DesignCanvas.selectElement(id);
        DesignCanvas.saveHistory();
        
        return id;
    },

    setupQuickActions() {
        document.getElementById('btn-undo')?.addEventListener('click', () => DesignCanvas.undo());
        document.getElementById('btn-redo')?.addEventListener('click', () => DesignCanvas.redo());
        document.getElementById('btn-delete')?.addEventListener('click', () => DesignCanvas.deleteSelected());
        document.getElementById('btn-duplicate')?.addEventListener('click', () => DesignCanvas.duplicateSelected());
        
        document.getElementById('btn-bring-front')?.addEventListener('click', () => DesignCanvas.bringToFront());
        document.getElementById('btn-bring-forward')?.addEventListener('click', () => DesignCanvas.bringForward());
        document.getElementById('btn-send-backward')?.addEventListener('click', () => DesignCanvas.sendBackward());
        document.getElementById('btn-send-back')?.addEventListener('click', () => DesignCanvas.sendToBack());
    },

    generateId() {
        return 'el_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    },

    // =========================================================================
    // PROGRAMMATIC SHAPE CREATION (for AI tools)
    // =========================================================================

    addRectangle(x, y, width, height, fill, stroke, strokeWidth, opacity, rx, ry, id) {
        const svg = document.getElementById('design-svg');
        if (!svg) return null;
        
        const element = document.createElementNS(this.svgNS, 'rect');
        element.id = id || this.generateId();
        element.setAttribute('x', x);
        element.setAttribute('y', y);
        element.setAttribute('width', width);
        element.setAttribute('height', height);
        element.setAttribute('fill', fill || this.defaultFill);
        if (stroke) element.setAttribute('stroke', stroke);
        if (strokeWidth) element.setAttribute('stroke-width', strokeWidth);
        if (opacity !== undefined) element.setAttribute('opacity', opacity);
        if (rx) element.setAttribute('rx', rx);
        if (ry) element.setAttribute('ry', ry);
        
        svg.appendChild(element);
        return element.id;
    },

    addCircle(x, y, radius, fill, stroke, strokeWidth, opacity, id) {
        const svg = document.getElementById('design-svg');
        if (!svg) return null;
        
        const element = document.createElementNS(this.svgNS, 'circle');
        element.id = id || this.generateId();
        element.setAttribute('cx', x);
        element.setAttribute('cy', y);
        element.setAttribute('r', radius);
        element.setAttribute('fill', fill || this.defaultFill);
        if (stroke) element.setAttribute('stroke', stroke);
        if (strokeWidth) element.setAttribute('stroke-width', strokeWidth);
        if (opacity !== undefined) element.setAttribute('opacity', opacity);
        
        svg.appendChild(element);
        return element.id;
    },

    addEllipse(x, y, rx, ry, fill, stroke, strokeWidth, opacity, id) {
        const svg = document.getElementById('design-svg');
        if (!svg) return null;
        
        const element = document.createElementNS(this.svgNS, 'ellipse');
        element.id = id || this.generateId();
        element.setAttribute('cx', x);
        element.setAttribute('cy', y);
        element.setAttribute('rx', rx);
        element.setAttribute('ry', ry);
        element.setAttribute('fill', fill || this.defaultFill);
        if (stroke) element.setAttribute('stroke', stroke);
        if (strokeWidth) element.setAttribute('stroke-width', strokeWidth);
        if (opacity !== undefined) element.setAttribute('opacity', opacity);
        
        svg.appendChild(element);
        return element.id;
    },

    addLine(x1, y1, x2, y2, stroke, strokeWidth, opacity, id) {
        const svg = document.getElementById('design-svg');
        if (!svg) return null;
        
        const element = document.createElementNS(this.svgNS, 'line');
        element.id = id || this.generateId();
        element.setAttribute('x1', x1);
        element.setAttribute('y1', y1);
        element.setAttribute('x2', x2);
        element.setAttribute('y2', y2);
        element.setAttribute('stroke', stroke || '#000000');
        element.setAttribute('stroke-width', strokeWidth || 2);
        if (opacity !== undefined) element.setAttribute('opacity', opacity);
        
        svg.appendChild(element);
        return element.id;
    },

    addTextElement(x, y, text, fontSize, fontFamily, fontWeight, fill, textAnchor, opacity, id) {
        const svg = document.getElementById('design-svg');
        if (!svg) return null;
        
        const element = document.createElementNS(this.svgNS, 'text');
        element.id = id || this.generateId();
        element.setAttribute('x', x);
        element.setAttribute('y', y);
        element.setAttribute('font-size', fontSize || 24);
        element.setAttribute('font-family', fontFamily || 'Inter, sans-serif');
        if (fontWeight) element.setAttribute('font-weight', fontWeight);
        element.setAttribute('fill', fill || '#000000');
        if (textAnchor) element.setAttribute('text-anchor', textAnchor);
        if (opacity !== undefined) element.setAttribute('opacity', opacity);
        element.textContent = text;
        
        svg.appendChild(element);
        return element.id;
    },

    addPolygon(points, fill, stroke, strokeWidth, opacity, id) {
        const svg = document.getElementById('design-svg');
        if (!svg) return null;
        
        const element = document.createElementNS(this.svgNS, 'polygon');
        element.id = id || this.generateId();
        element.setAttribute('points', points);
        element.setAttribute('fill', fill || this.defaultFill);
        if (stroke) element.setAttribute('stroke', stroke);
        if (strokeWidth) element.setAttribute('stroke-width', strokeWidth);
        if (opacity !== undefined) element.setAttribute('opacity', opacity);
        
        svg.appendChild(element);
        return element.id;
    },

    addPath(d, fill, stroke, strokeWidth, opacity, id) {
        const svg = document.getElementById('design-svg');
        if (!svg) return null;
        
        const element = document.createElementNS(this.svgNS, 'path');
        element.id = id || this.generateId();
        element.setAttribute('d', d);
        element.setAttribute('fill', fill || 'none');
        if (stroke) element.setAttribute('stroke', stroke);
        if (strokeWidth) element.setAttribute('stroke-width', strokeWidth);
        if (opacity !== undefined) element.setAttribute('opacity', opacity);
        
        svg.appendChild(element);
        return element.id;
    },

    // =========================================================================
    // ELEMENT MODIFICATION
    // =========================================================================

    modifyElement(id, properties) {
        const svg = document.getElementById('design-svg');
        if (!svg) return false;
        
        const element = svg.getElementById(id);
        if (!element) return false;
        
        Object.entries(properties).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
                // Handle special cases
                if (key === 'text' && element.tagName === 'text') {
                    element.textContent = value;
                } else {
                    // Convert camelCase to kebab-case for SVG attributes
                    const attrName = key.replace(/([A-Z])/g, '-$1').toLowerCase();
                    element.setAttribute(attrName, value);
                }
            }
        });
        
        return true;
    },

    deleteElement(id) {
        const svg = document.getElementById('design-svg');
        if (!svg) return false;
        
        const element = svg.getElementById(id);
        if (element) {
            element.remove();
            return true;
        }
        return false;
    },

    clearCanvas() {
        const svg = document.getElementById('design-svg');
        if (svg) {
            svg.innerHTML = '';
        }
        return true;
    },

    setBackground(color) {
        DesignCanvas.setBackground(color);
        return true;
    },

    // =========================================================================
    // LAYER OPERATIONS
    // =========================================================================

    bringToFront(id) {
        const svg = document.getElementById('design-svg');
        if (!svg) return false;
        
        const element = svg.getElementById(id);
        if (element) {
            svg.appendChild(element);
            return true;
        }
        return false;
    },

    sendToBack(id) {
        const svg = document.getElementById('design-svg');
        if (!svg) return false;
        
        const element = svg.getElementById(id);
        if (element) {
            svg.insertBefore(element, svg.firstChild);
            return true;
        }
        return false;
    },

    bringForward(id) {
        const svg = document.getElementById('design-svg');
        if (!svg) return false;
        
        const element = svg.getElementById(id);
        if (element && element.nextElementSibling) {
            svg.insertBefore(element.nextElementSibling, element);
            return true;
        }
        return false;
    },

    sendBackward(id) {
        const svg = document.getElementById('design-svg');
        if (!svg) return false;
        
        const element = svg.getElementById(id);
        if (element && element.previousElementSibling) {
            svg.insertBefore(element, element.previousElementSibling);
            return true;
        }
        return false;
    },

    // =========================================================================
    // DUPLICATION
    // =========================================================================

    duplicateElement(id, newId, offsetX = 20, offsetY = 20) {
        const svg = document.getElementById('design-svg');
        if (!svg) return null;
        
        const element = svg.getElementById(id);
        if (!element) return null;
        
        const clone = element.cloneNode(true);
        clone.id = newId || this.generateId();
        
        // Offset the clone based on element type
        const tagName = clone.tagName.toLowerCase();
        
        if (tagName === 'rect' || tagName === 'image' || tagName === 'text') {
            const x = parseFloat(clone.getAttribute('x') || 0);
            const y = parseFloat(clone.getAttribute('y') || 0);
            clone.setAttribute('x', x + offsetX);
            clone.setAttribute('y', y + offsetY);
        } else if (tagName === 'circle' || tagName === 'ellipse') {
            const cx = parseFloat(clone.getAttribute('cx') || 0);
            const cy = parseFloat(clone.getAttribute('cy') || 0);
            clone.setAttribute('cx', cx + offsetX);
            clone.setAttribute('cy', cy + offsetY);
        } else if (tagName === 'line') {
            const x1 = parseFloat(clone.getAttribute('x1') || 0);
            const y1 = parseFloat(clone.getAttribute('y1') || 0);
            const x2 = parseFloat(clone.getAttribute('x2') || 0);
            const y2 = parseFloat(clone.getAttribute('y2') || 0);
            clone.setAttribute('x1', x1 + offsetX);
            clone.setAttribute('y1', y1 + offsetY);
            clone.setAttribute('x2', x2 + offsetX);
            clone.setAttribute('y2', y2 + offsetY);
        } else if (tagName === 'polygon' || tagName === 'polyline') {
            const points = clone.getAttribute('points');
            if (points) {
                const newPoints = points.split(/\s+/).map(p => {
                    const [x, y] = p.split(',').map(Number);
                    return `${x + offsetX},${y + offsetY}`;
                }).join(' ');
                clone.setAttribute('points', newPoints);
            }
        } else if (tagName === 'path') {
            // For paths, use transform instead
            const transform = clone.getAttribute('transform') || '';
            clone.setAttribute('transform', `${transform} translate(${offsetX}, ${offsetY})`);
        }
        
        svg.appendChild(clone);
        return clone.id;
    },

    // =========================================================================
    // ALIGNMENT
    // =========================================================================

    alignElements(ids, alignment) {
        const svg = document.getElementById('design-svg');
        if (!svg || ids.length < 2) return false;
        
        const elements = ids.map(id => svg.getElementById(id)).filter(Boolean);
        if (elements.length < 2) return false;
        
        // Get bounding boxes
        const bboxes = elements.map(el => el.getBBox());
        
        // Calculate alignment bounds
        const minX = Math.min(...bboxes.map(b => b.x));
        const maxX = Math.max(...bboxes.map(b => b.x + b.width));
        const minY = Math.min(...bboxes.map(b => b.y));
        const maxY = Math.max(...bboxes.map(b => b.y + b.height));
        const centerX = (minX + maxX) / 2;
        const centerY = (minY + maxY) / 2;
        
        elements.forEach((element, i) => {
            const bbox = bboxes[i];
            let dx = 0, dy = 0;
            
            switch (alignment) {
                case 'left':
                    dx = minX - bbox.x;
                    break;
                case 'center':
                    dx = centerX - (bbox.x + bbox.width / 2);
                    break;
                case 'right':
                    dx = maxX - (bbox.x + bbox.width);
                    break;
                case 'top':
                    dy = minY - bbox.y;
                    break;
                case 'middle':
                    dy = centerY - (bbox.y + bbox.height / 2);
                    break;
                case 'bottom':
                    dy = maxY - (bbox.y + bbox.height);
                    break;
            }
            
            if (dx !== 0 || dy !== 0) {
                this.translateElement(element, dx, dy);
            }
        });
        
        return true;
    },

    distributeElements(ids, direction) {
        const svg = document.getElementById('design-svg');
        if (!svg || ids.length < 3) return false;
        
        const elements = ids.map(id => svg.getElementById(id)).filter(Boolean);
        if (elements.length < 3) return false;
        
        const bboxes = elements.map(el => ({ el, bbox: el.getBBox() }));
        
        if (direction === 'horizontal') {
            bboxes.sort((a, b) => a.bbox.x - b.bbox.x);
            const leftMost = bboxes[0].bbox.x;
            const rightMost = bboxes[bboxes.length - 1].bbox.x + bboxes[bboxes.length - 1].bbox.width;
            const totalWidth = bboxes.reduce((sum, b) => sum + b.bbox.width, 0);
            const spacing = (rightMost - leftMost - totalWidth) / (bboxes.length - 1);
            
            let current = leftMost;
            bboxes.forEach(({ el, bbox }) => {
                const dx = current - bbox.x;
                if (dx !== 0) this.translateElement(el, dx, 0);
                current += bbox.width + spacing;
            });
        } else {
            bboxes.sort((a, b) => a.bbox.y - b.bbox.y);
            const topMost = bboxes[0].bbox.y;
            const bottomMost = bboxes[bboxes.length - 1].bbox.y + bboxes[bboxes.length - 1].bbox.height;
            const totalHeight = bboxes.reduce((sum, b) => sum + b.bbox.height, 0);
            const spacing = (bottomMost - topMost - totalHeight) / (bboxes.length - 1);
            
            let current = topMost;
            bboxes.forEach(({ el, bbox }) => {
                const dy = current - bbox.y;
                if (dy !== 0) this.translateElement(el, 0, dy);
                current += bbox.height + spacing;
            });
        }
        
        return true;
    },

    translateElement(element, dx, dy) {
        const tagName = element.tagName.toLowerCase();
        
        if (tagName === 'rect' || tagName === 'image' || tagName === 'text') {
            const x = parseFloat(element.getAttribute('x') || 0);
            const y = parseFloat(element.getAttribute('y') || 0);
            element.setAttribute('x', x + dx);
            element.setAttribute('y', y + dy);
        } else if (tagName === 'circle' || tagName === 'ellipse') {
            const cx = parseFloat(element.getAttribute('cx') || 0);
            const cy = parseFloat(element.getAttribute('cy') || 0);
            element.setAttribute('cx', cx + dx);
            element.setAttribute('cy', cy + dy);
        } else if (tagName === 'line') {
            const x1 = parseFloat(element.getAttribute('x1') || 0);
            const y1 = parseFloat(element.getAttribute('y1') || 0);
            const x2 = parseFloat(element.getAttribute('x2') || 0);
            const y2 = parseFloat(element.getAttribute('y2') || 0);
            element.setAttribute('x1', x1 + dx);
            element.setAttribute('y1', y1 + dy);
            element.setAttribute('x2', x2 + dx);
            element.setAttribute('y2', y2 + dy);
        } else if (tagName === 'polygon' || tagName === 'polyline') {
            const points = element.getAttribute('points');
            if (points) {
                const newPoints = points.split(/\s+/).map(p => {
                    const [x, y] = p.split(',').map(Number);
                    return `${x + dx},${y + dy}`;
                }).join(' ');
                element.setAttribute('points', newPoints);
            }
        } else {
            // Use transform for complex elements
            const transform = element.getAttribute('transform') || '';
            element.setAttribute('transform', `${transform} translate(${dx}, ${dy})`);
        }
    },

    // =========================================================================
    // EFFECTS
    // =========================================================================

    addDropShadow(id, dx = 4, dy = 4, blur = 4, color = 'rgba(0,0,0,0.3)') {
        const svg = document.getElementById('design-svg');
        if (!svg) return false;
        
        const element = svg.getElementById(id);
        if (!element) return false;
        
        // Get or create defs
        let defs = svg.querySelector('defs');
        if (!defs) {
            defs = document.createElementNS(this.svgNS, 'defs');
            svg.insertBefore(defs, svg.firstChild);
        }
        
        // Create filter
        const filterId = `shadow_${id}`;
        let filter = svg.getElementById(filterId);
        
        if (!filter) {
            filter = document.createElementNS(this.svgNS, 'filter');
            filter.id = filterId;
            filter.setAttribute('x', '-50%');
            filter.setAttribute('y', '-50%');
            filter.setAttribute('width', '200%');
            filter.setAttribute('height', '200%');
            
            const feDropShadow = document.createElementNS(this.svgNS, 'feDropShadow');
            feDropShadow.setAttribute('dx', dx);
            feDropShadow.setAttribute('dy', dy);
            feDropShadow.setAttribute('stdDeviation', blur);
            feDropShadow.setAttribute('flood-color', color);
            
            filter.appendChild(feDropShadow);
            defs.appendChild(filter);
        }
        
        element.setAttribute('filter', `url(#${filterId})`);
        return true;
    },

    removeFilter(id) {
        const svg = document.getElementById('design-svg');
        if (!svg) return false;
        
        const element = svg.getElementById(id);
        if (element) {
            element.removeAttribute('filter');
            return true;
        }
        return false;
    },

    // =========================================================================
    // GRADIENTS
    // =========================================================================

    addLinearGradient(id, colors, angle = 0) {
        const svg = document.getElementById('design-svg');
        if (!svg || !colors || colors.length < 2) return false;
        
        const element = svg.getElementById(id);
        if (!element) return false;
        
        // Get or create defs
        let defs = svg.querySelector('defs');
        if (!defs) {
            defs = document.createElementNS(this.svgNS, 'defs');
            svg.insertBefore(defs, svg.firstChild);
        }
        
        // Create gradient
        const gradientId = `gradient_${id}`;
        let gradient = svg.getElementById(gradientId);
        
        if (gradient) gradient.remove();
        
        gradient = document.createElementNS(this.svgNS, 'linearGradient');
        gradient.id = gradientId;
        
        // Set angle via x1, y1, x2, y2
        const rad = (angle * Math.PI) / 180;
        gradient.setAttribute('x1', `${50 - 50 * Math.cos(rad)}%`);
        gradient.setAttribute('y1', `${50 - 50 * Math.sin(rad)}%`);
        gradient.setAttribute('x2', `${50 + 50 * Math.cos(rad)}%`);
        gradient.setAttribute('y2', `${50 + 50 * Math.sin(rad)}%`);
        
        // Add stops
        colors.forEach((color, i) => {
            const stop = document.createElementNS(this.svgNS, 'stop');
            stop.setAttribute('offset', `${(i / (colors.length - 1)) * 100}%`);
            stop.setAttribute('stop-color', color);
            gradient.appendChild(stop);
        });
        
        defs.appendChild(gradient);
        element.setAttribute('fill', `url(#${gradientId})`);
        
        return true;
    },

    addRadialGradient(id, colors, cx = 50, cy = 50) {
        const svg = document.getElementById('design-svg');
        if (!svg || !colors || colors.length < 2) return false;
        
        const element = svg.getElementById(id);
        if (!element) return false;
        
        // Get or create defs
        let defs = svg.querySelector('defs');
        if (!defs) {
            defs = document.createElementNS(this.svgNS, 'defs');
            svg.insertBefore(defs, svg.firstChild);
        }
        
        // Create gradient
        const gradientId = `radial_${id}`;
        let gradient = svg.getElementById(gradientId);
        
        if (gradient) gradient.remove();
        
        gradient = document.createElementNS(this.svgNS, 'radialGradient');
        gradient.id = gradientId;
        gradient.setAttribute('cx', `${cx}%`);
        gradient.setAttribute('cy', `${cy}%`);
        
        // Add stops
        colors.forEach((color, i) => {
            const stop = document.createElementNS(this.svgNS, 'stop');
            stop.setAttribute('offset', `${(i / (colors.length - 1)) * 100}%`);
            stop.setAttribute('stop-color', color);
            gradient.appendChild(stop);
        });
        
        defs.appendChild(gradient);
        element.setAttribute('fill', `url(#${gradientId})`);
        
        return true;
    }
};
