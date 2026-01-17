/**
 * Design Tools Module
 * Handles shape creation, drawing tools, and tool interactions
 */
const DesignTools = {
    currentTool: 'select',
    isDrawing: false,
    startPoint: null,
    tempShape: null,
    defaultFill: '#4ade80',
    defaultStroke: '#000000',
    defaultStrokeWidth: 0,
    clipboard: null,
    shiftPressed: false,

    init() {
        this.setupToolButtons();
        this.setupCanvasDrawing();
        this.setupQuickActions();
        this.setupModifierKeys();
        return this;
    },

    /**
     * Track modifier keys for constrained drawing
     */
    setupModifierKeys() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Shift') this.shiftPressed = true;
        });
        document.addEventListener('keyup', (e) => {
            if (e.key === 'Shift') this.shiftPressed = false;
        });
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
        DesignCanvas.setTool(toolName);

        if (toolName === 'image') {
            this.triggerImageUpload();
        }
    },

    setupCanvasDrawing() {
        const canvas = DesignCanvas.canvas;
        if (!canvas) return;

        canvas.on('mouse:down', (opt) => this.onMouseDown(opt));
        canvas.on('mouse:move', (opt) => this.onMouseMove(opt));
        canvas.on('mouse:up', (opt) => this.onMouseUp(opt));
    },

    onMouseDown(opt) {
        if (this.currentTool === 'select' || this.currentTool === 'hand') return;
        if (opt.target) return;

        const canvas = DesignCanvas.canvas;
        const pointer = canvas.getPointer(opt.e);

        this.isDrawing = true;
        this.startPoint = { x: pointer.x, y: pointer.y };

        this.createTempShape(pointer);
    },

    onMouseMove(opt) {
        if (!this.isDrawing || !this.tempShape) return;

        const canvas = DesignCanvas.canvas;
        const pointer = canvas.getPointer(opt.e);

        this.updateTempShape(pointer);
    },

    onMouseUp(opt) {
        if (!this.isDrawing) return;

        this.isDrawing = false;

        if (this.tempShape) {
            const width = Math.abs(this.tempShape.width || this.tempShape.radius * 2 || 0);
            const height = Math.abs(this.tempShape.height || this.tempShape.radius * 2 || 0);

            if (width < 5 && height < 5) {
                DesignCanvas.canvas.remove(this.tempShape);

                if (this.currentTool === 'text') {
                    this.createText(this.startPoint.x, this.startPoint.y);
                } else {
                    this.createDefaultShape(this.startPoint.x, this.startPoint.y);
                }
            } else {
                this.tempShape.setCoords();
                DesignCanvas.canvas.setActiveObject(this.tempShape);
                DesignCanvas.saveHistory();
            }
        }

        this.tempShape = null;
        this.startPoint = null;

        this.setTool('select');
    },

    createTempShape(pointer) {
        const canvas = DesignCanvas.canvas;
        let shape = null;

        const commonProps = {
            left: pointer.x,
            top: pointer.y,
            fill: this.defaultFill,
            stroke: this.defaultStroke,
            strokeWidth: this.defaultStrokeWidth,
            originX: 'left',
            originY: 'top',
            id: this.generateId()
        };

        switch (this.currentTool) {
            case 'rectangle':
                shape = new fabric.Rect({
                    ...commonProps,
                    width: 0,
                    height: 0,
                    rx: 0,
                    ry: 0
                });
                break;

            case 'circle':
                shape = new fabric.Circle({
                    ...commonProps,
                    radius: 0,
                    originX: 'center',
                    originY: 'center'
                });
                break;

            case 'ellipse':
                shape = new fabric.Ellipse({
                    ...commonProps,
                    rx: 0,
                    ry: 0,
                    originX: 'center',
                    originY: 'center'
                });
                break;

            case 'triangle':
                shape = new fabric.Triangle({
                    ...commonProps,
                    width: 0,
                    height: 0
                });
                break;

            case 'line':
                shape = new fabric.Line([pointer.x, pointer.y, pointer.x, pointer.y], {
                    stroke: this.defaultStroke || '#000000',
                    strokeWidth: this.defaultStrokeWidth || 2,
                    id: this.generateId()
                });
                break;

            case 'polygon':
                shape = new fabric.Polygon(this.createPolygonPoints(pointer, 0, 6), {
                    ...commonProps,
                    originX: 'center',
                    originY: 'center'
                });
                break;

            case 'star':
                shape = new fabric.Polygon(this.createStarPoints(pointer, 0, 0, 5), {
                    ...commonProps,
                    originX: 'center',
                    originY: 'center'
                });
                break;

            case 'text':
                return;

            default:
                return;
        }

        if (shape) {
            this.tempShape = shape;
            canvas.add(shape);
            canvas.requestRenderAll();
        }
    },

    updateTempShape(pointer) {
        if (!this.tempShape || !this.startPoint) return;

        const canvas = DesignCanvas.canvas;
        const dx = pointer.x - this.startPoint.x;
        const dy = pointer.y - this.startPoint.y;

        switch (this.currentTool) {
            case 'rectangle':
            case 'triangle':
                this.tempShape.set({
                    width: Math.abs(dx),
                    height: Math.abs(dy),
                    left: dx > 0 ? this.startPoint.x : pointer.x,
                    top: dy > 0 ? this.startPoint.y : pointer.y
                });
                break;

            case 'circle':
                const radius = Math.sqrt(dx * dx + dy * dy) / 2;
                this.tempShape.set({
                    radius: radius,
                    left: this.startPoint.x + dx / 2,
                    top: this.startPoint.y + dy / 2
                });
                break;

            case 'ellipse':
                // Hold Shift to constrain to circle
                const rx = Math.abs(dx) / 2;
                const ry = this.shiftPressed ? rx : Math.abs(dy) / 2;
                this.tempShape.set({
                    rx: rx,
                    ry: ry,
                    left: this.startPoint.x + dx / 2,
                    top: this.startPoint.y + dy / 2
                });
                break;

            case 'line':
                this.tempShape.set({
                    x2: pointer.x,
                    y2: pointer.y
                });
                break;

            case 'polygon':
                const polyRadius = Math.sqrt(dx * dx + dy * dy) / 2;
                this.tempShape.set({
                    points: this.createPolygonPoints({ x: this.startPoint.x, y: this.startPoint.y }, polyRadius, 6),
                    left: this.startPoint.x,
                    top: this.startPoint.y
                });
                break;

            case 'star':
                const outerRadius = Math.sqrt(dx * dx + dy * dy) / 2;
                const innerRadius = outerRadius * 0.4;
                this.tempShape.set({
                    points: this.createStarPoints({ x: this.startPoint.x, y: this.startPoint.y }, outerRadius, innerRadius, 5),
                    left: this.startPoint.x,
                    top: this.startPoint.y
                });
                break;
        }

        this.tempShape.setCoords();
        canvas.requestRenderAll();
    },

    createDefaultShape(x, y) {
        const canvas = DesignCanvas.canvas;
        let shape = null;

        const commonProps = {
            left: x,
            top: y,
            fill: this.defaultFill,
            stroke: this.defaultStroke,
            strokeWidth: this.defaultStrokeWidth,
            id: this.generateId()
        };

        switch (this.currentTool) {
            case 'rectangle':
                shape = new fabric.Rect({
                    ...commonProps,
                    width: 100,
                    height: 100,
                    rx: 0,
                    ry: 0
                });
                break;

            case 'circle':
                shape = new fabric.Circle({
                    ...commonProps,
                    radius: 50
                });
                break;

            case 'ellipse':
                shape = new fabric.Ellipse({
                    ...commonProps,
                    rx: 60,
                    ry: 40
                });
                break;

            case 'triangle':
                shape = new fabric.Triangle({
                    ...commonProps,
                    width: 100,
                    height: 100
                });
                break;

            case 'line':
                shape = new fabric.Line([x, y, x + 100, y], {
                    stroke: this.defaultStroke || '#000000',
                    strokeWidth: 2,
                    id: this.generateId()
                });
                break;

            case 'polygon':
                shape = new fabric.Polygon(this.createPolygonPoints({ x: x + 50, y: y + 50 }, 50, 6), {
                    ...commonProps
                });
                break;

            case 'star':
                shape = new fabric.Polygon(this.createStarPoints({ x: x + 50, y: y + 50 }, 50, 20, 5), {
                    ...commonProps
                });
                break;
        }

        if (shape) {
            canvas.add(shape);
            canvas.setActiveObject(shape);
            canvas.requestRenderAll();
            DesignCanvas.saveHistory();
        }
    },

    createText(x, y, text = 'Text') {
        const canvas = DesignCanvas.canvas;
        const textObj = new fabric.IText(text, {
            left: x,
            top: y,
            fontFamily: 'Inter',
            fontSize: 32,
            fill: '#000000',
            id: this.generateId()
        });

        canvas.add(textObj);
        canvas.setActiveObject(textObj);
        textObj.enterEditing();
        textObj.selectAll();
        canvas.requestRenderAll();
        DesignCanvas.saveHistory();
    },

    createPolygonPoints(center, radius, sides) {
        const points = [];
        const angle = (2 * Math.PI) / sides;
        const startAngle = -Math.PI / 2;

        for (let i = 0; i < sides; i++) {
            points.push({
                x: center.x + radius * Math.cos(startAngle + i * angle),
                y: center.y + radius * Math.sin(startAngle + i * angle)
            });
        }

        return points;
    },

    createStarPoints(center, outerRadius, innerRadius, points) {
        const starPoints = [];
        const angle = Math.PI / points;
        const startAngle = -Math.PI / 2;

        for (let i = 0; i < points * 2; i++) {
            const radius = i % 2 === 0 ? outerRadius : innerRadius;
            starPoints.push({
                x: center.x + radius * Math.cos(startAngle + i * angle),
                y: center.y + radius * Math.sin(startAngle + i * angle)
            });
        }

        return starPoints;
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
    },

    addImageFromFile(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            this.addImageFromURL(e.target.result);
        };
        reader.readAsDataURL(file);
    },

    addImageFromURL(url, options = {}) {
        fabric.Image.fromURL(url, (img) => {
            const maxSize = Math.min(DesignCanvas.canvasWidth, DesignCanvas.canvasHeight) * 0.5;
            const scale = Math.min(maxSize / img.width, maxSize / img.height, 1);

            img.set({
                left: options.x || DesignCanvas.canvasWidth / 2,
                top: options.y || DesignCanvas.canvasHeight / 2,
                originX: 'center',
                originY: 'center',
                scaleX: options.scaleX || scale,
                scaleY: options.scaleY || scale,
                id: this.generateId()
            });

            DesignCanvas.canvas.add(img);
            DesignCanvas.canvas.setActiveObject(img);
            DesignCanvas.canvas.requestRenderAll();
            DesignCanvas.saveHistory();

            this.setTool('select');
        }, { crossOrigin: 'anonymous' });
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
        return 'obj_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    },

    addRectangle(x, y, width, height, fill, stroke, strokeWidth, opacity, rx, ry, angle) {
        const rect = new fabric.Rect({
            left: x,
            top: y,
            width: width,
            height: height,
            fill: fill || this.defaultFill,
            stroke: stroke || null,
            strokeWidth: strokeWidth || 0,
            opacity: opacity !== undefined ? opacity : 1,
            rx: rx || 0,
            ry: ry || 0,
            angle: angle || 0,
            id: this.generateId()
        });

        DesignCanvas.addObject(rect);
        return rect.id;
    },

    addCircle(x, y, radius, fill, stroke, strokeWidth, opacity) {
        const circle = new fabric.Circle({
            left: x,
            top: y,
            radius: radius,
            fill: fill || this.defaultFill,
            stroke: stroke || null,
            strokeWidth: strokeWidth || 0,
            opacity: opacity !== undefined ? opacity : 1,
            id: this.generateId()
        });

        DesignCanvas.addObject(circle);
        return circle.id;
    },

    addTriangle(x, y, width, height, fill, stroke, strokeWidth, opacity, angle) {
        const triangle = new fabric.Triangle({
            left: x,
            top: y,
            width: width,
            height: height,
            fill: fill || this.defaultFill,
            stroke: stroke || null,
            strokeWidth: strokeWidth || 0,
            opacity: opacity !== undefined ? opacity : 1,
            angle: angle || 0,
            id: this.generateId()
        });

        DesignCanvas.addObject(triangle);
        return triangle.id;
    },

    addLine(x1, y1, x2, y2, stroke, strokeWidth, opacity) {
        const line = new fabric.Line([x1, y1, x2, y2], {
            stroke: stroke || '#000000',
            strokeWidth: strokeWidth || 2,
            opacity: opacity !== undefined ? opacity : 1,
            id: this.generateId()
        });

        DesignCanvas.addObject(line);
        return line.id;
    },

    addText(x, y, text, fontSize, fontFamily, fontWeight, fill, textAlign, opacity, angle) {
        const textObj = new fabric.IText(text, {
            left: x,
            top: y,
            text: text,
            fontSize: fontSize || 24,
            fontFamily: fontFamily || 'Inter',
            fontWeight: fontWeight || 'normal',
            fill: fill || '#000000',
            textAlign: textAlign || 'left',
            opacity: opacity !== undefined ? opacity : 1,
            angle: angle || 0,
            id: this.generateId()
        });

        DesignCanvas.addObject(textObj);
        return textObj.id;
    },

    addPolygon(x, y, radius, sides, fill, stroke, strokeWidth, opacity, angle) {
        const points = this.createPolygonPoints({ x: 0, y: 0 }, radius, sides);
        const polygon = new fabric.Polygon(points, {
            left: x,
            top: y,
            fill: fill || this.defaultFill,
            stroke: stroke || null,
            strokeWidth: strokeWidth || 0,
            opacity: opacity !== undefined ? opacity : 1,
            angle: angle || 0,
            id: this.generateId()
        });

        DesignCanvas.addObject(polygon);
        return polygon.id;
    },

    addStar(x, y, outerRadius, innerRadius, points, fill, stroke, strokeWidth, opacity, angle) {
        const starPoints = this.createStarPoints({ x: 0, y: 0 }, outerRadius, innerRadius || outerRadius * 0.4, points || 5);
        const star = new fabric.Polygon(starPoints, {
            left: x,
            top: y,
            fill: fill || this.defaultFill,
            stroke: stroke || null,
            strokeWidth: strokeWidth || 0,
            opacity: opacity !== undefined ? opacity : 1,
            angle: angle || 0,
            id: this.generateId()
        });

        DesignCanvas.addObject(star);
        return star.id;
    },

    addImage(url, x, y, width, height, opacity, angle) {
        return new Promise((resolve) => {
            fabric.Image.fromURL(url, (img) => {
                const props = {
                    left: x,
                    top: y,
                    opacity: opacity !== undefined ? opacity : 1,
                    angle: angle || 0,
                    id: this.generateId()
                };

                if (width && height) {
                    props.scaleX = width / img.width;
                    props.scaleY = height / img.height;
                } else if (width) {
                    const scale = width / img.width;
                    props.scaleX = scale;
                    props.scaleY = scale;
                } else if (height) {
                    const scale = height / img.height;
                    props.scaleX = scale;
                    props.scaleY = scale;
                }

                img.set(props);
                DesignCanvas.addObject(img);
                resolve(img.id);
            }, { crossOrigin: 'anonymous' });
        });
    },

    modifyObject(id, properties) {
        const obj = DesignCanvas.getObjectById(id);
        if (!obj) return false;

        const mappedProps = {};

        if (properties.x !== undefined) mappedProps.left = properties.x;
        if (properties.y !== undefined) mappedProps.top = properties.y;
        if (properties.width !== undefined) {
            if (obj.type === 'circle') {
                mappedProps.radius = properties.width / 2;
            } else {
                mappedProps.width = properties.width;
            }
        }
        if (properties.height !== undefined) mappedProps.height = properties.height;
        if (properties.fill !== undefined) mappedProps.fill = properties.fill;
        if (properties.stroke !== undefined) mappedProps.stroke = properties.stroke;
        if (properties.strokeWidth !== undefined) mappedProps.strokeWidth = properties.strokeWidth;
        if (properties.opacity !== undefined) mappedProps.opacity = properties.opacity;
        if (properties.angle !== undefined) mappedProps.angle = properties.angle;
        if (properties.text !== undefined) mappedProps.text = properties.text;
        if (properties.fontSize !== undefined) mappedProps.fontSize = properties.fontSize;
        if (properties.fontFamily !== undefined) mappedProps.fontFamily = properties.fontFamily;
        if (properties.fontWeight !== undefined) mappedProps.fontWeight = properties.fontWeight;

        DesignCanvas.updateObjectById(id, mappedProps);
        return true;
    },

    deleteObject(id) {
        DesignCanvas.removeObjectById(id);
        return true;
    },

    clearCanvas() {
        DesignCanvas.clear();
        return true;
    },

    setBackground(color) {
        DesignCanvas.setBackgroundColor(color);
        return true;
    },

    groupObjects(ids) {
        const canvas = DesignCanvas.canvas;
        const objects = ids.map(id => DesignCanvas.getObjectById(id)).filter(Boolean);

        if (objects.length < 2) return null;

        const group = new fabric.Group(objects, {
            id: this.generateId()
        });

        objects.forEach(obj => canvas.remove(obj));
        canvas.add(group);
        canvas.setActiveObject(group);
        canvas.requestRenderAll();
        DesignCanvas.saveHistory();

        return group.id;
    },

    ungroupObjects(groupId) {
        const canvas = DesignCanvas.canvas;
        const group = DesignCanvas.getObjectById(groupId);

        if (!group || group.type !== 'group') return [];

        const items = group._objects;
        group._restoreObjectsState();
        canvas.remove(group);

        const ids = [];
        items.forEach(item => {
            item.id = this.generateId();
            ids.push(item.id);
            canvas.add(item);
        });

        canvas.requestRenderAll();
        DesignCanvas.saveHistory();

        return ids;
    },

    /**
     * Add an ellipse to the canvas
     */
    addEllipse(x, y, rx, ry, fill, stroke, strokeWidth, opacity, angle) {
        const ellipse = new fabric.Ellipse({
            left: x,
            top: y,
            rx: rx || 60,
            ry: ry || 40,
            fill: fill || this.defaultFill,
            stroke: stroke || null,
            strokeWidth: strokeWidth || 0,
            opacity: opacity !== undefined ? opacity : 1,
            angle: angle || 0,
            id: this.generateId()
        });

        DesignCanvas.addObject(ellipse);
        return ellipse.id;
    },

    /**
     * Add a path to the canvas
     */
    addPath(pathData, x, y, fill, stroke, strokeWidth, opacity, angle) {
        const path = new fabric.Path(pathData, {
            left: x || 0,
            top: y || 0,
            fill: fill || this.defaultFill,
            stroke: stroke || null,
            strokeWidth: strokeWidth || 0,
            opacity: opacity !== undefined ? opacity : 1,
            angle: angle || 0,
            id: this.generateId()
        });

        DesignCanvas.addObject(path);
        return path.id;
    },

    /**
     * Copy selected objects to clipboard
     */
    copySelection() {
        const activeObject = DesignCanvas.canvas.getActiveObject();
        if (!activeObject) return false;

        activeObject.clone((cloned) => {
            this.clipboard = cloned;
        });
        return true;
    },

    /**
     * Paste from clipboard
     */
    pasteFromClipboard() {
        if (!this.clipboard) return false;

        this.clipboard.clone((cloned) => {
            cloned.set({
                left: cloned.left + 20,
                top: cloned.top + 20,
                id: this.generateId(),
                evented: true
            });

            if (cloned.type === 'activeSelection') {
                cloned.canvas = DesignCanvas.canvas;
                cloned.forEachObject((obj) => {
                    obj.id = this.generateId();
                    DesignCanvas.canvas.add(obj);
                });
                cloned.setCoords();
            } else {
                DesignCanvas.canvas.add(cloned);
            }

            this.clipboard.top += 20;
            this.clipboard.left += 20;
            DesignCanvas.canvas.setActiveObject(cloned);
            DesignCanvas.canvas.requestRenderAll();
            DesignCanvas.saveHistory();
        });

        return true;
    },

    /**
     * Align selected objects
     * @param {string} alignment - left, center, right, top, middle, bottom
     */
    alignObjects(alignment) {
        const canvas = DesignCanvas.canvas;
        const activeObject = canvas.getActiveObject();

        if (!activeObject) return false;

        // For single object, align to canvas
        if (activeObject.type !== 'activeSelection') {
            const bounds = activeObject.getBoundingRect();
            const canvasWidth = DesignCanvas.canvasWidth;
            const canvasHeight = DesignCanvas.canvasHeight;

            switch (alignment) {
                case 'left':
                    activeObject.set('left', 0);
                    break;
                case 'center':
                    activeObject.set('left', (canvasWidth - bounds.width) / 2);
                    break;
                case 'right':
                    activeObject.set('left', canvasWidth - bounds.width);
                    break;
                case 'top':
                    activeObject.set('top', 0);
                    break;
                case 'middle':
                    activeObject.set('top', (canvasHeight - bounds.height) / 2);
                    break;
                case 'bottom':
                    activeObject.set('top', canvasHeight - bounds.height);
                    break;
            }
            activeObject.setCoords();
        } else {
            // For multiple objects, align to selection bounds
            const objects = activeObject.getObjects();
            const selectionBounds = activeObject.getBoundingRect();

            objects.forEach(obj => {
                const objBounds = obj.getBoundingRect(true);
                const offset = {
                    x: objBounds.left - selectionBounds.left,
                    y: objBounds.top - selectionBounds.top
                };

                switch (alignment) {
                    case 'left':
                        obj.set('left', obj.left - offset.x);
                        break;
                    case 'center':
                        const centerX = selectionBounds.width / 2;
                        obj.set('left', obj.left - offset.x + centerX - objBounds.width / 2);
                        break;
                    case 'right':
                        obj.set('left', obj.left - offset.x + selectionBounds.width - objBounds.width);
                        break;
                    case 'top':
                        obj.set('top', obj.top - offset.y);
                        break;
                    case 'middle':
                        const centerY = selectionBounds.height / 2;
                        obj.set('top', obj.top - offset.y + centerY - objBounds.height / 2);
                        break;
                    case 'bottom':
                        obj.set('top', obj.top - offset.y + selectionBounds.height - objBounds.height);
                        break;
                }
                obj.setCoords();
            });
        }

        canvas.requestRenderAll();
        DesignCanvas.saveHistory();
        return true;
    },

    /**
     * Distribute selected objects evenly
     * @param {string} direction - horizontal or vertical
     */
    distributeObjects(direction) {
        const canvas = DesignCanvas.canvas;
        const activeObject = canvas.getActiveObject();

        if (!activeObject || activeObject.type !== 'activeSelection') return false;

        const objects = activeObject.getObjects();
        if (objects.length < 3) return false;

        // Sort objects by position
        const sorted = [...objects].sort((a, b) => {
            if (direction === 'horizontal') {
                return a.left - b.left;
            }
            return a.top - b.top;
        });

        // Calculate total space and gap
        const first = sorted[0];
        const last = sorted[sorted.length - 1];
        let totalSpace, totalSize = 0;

        if (direction === 'horizontal') {
            totalSpace = last.left + last.width * last.scaleX - first.left;
            sorted.forEach(obj => totalSize += obj.width * obj.scaleX);
        } else {
            totalSpace = last.top + last.height * last.scaleY - first.top;
            sorted.forEach(obj => totalSize += obj.height * obj.scaleY);
        }

        const gap = (totalSpace - totalSize) / (objects.length - 1);
        let currentPos = direction === 'horizontal' ? first.left : first.top;

        // Distribute objects
        sorted.forEach((obj, i) => {
            if (i === 0) {
                if (direction === 'horizontal') {
                    currentPos += obj.width * obj.scaleX + gap;
                } else {
                    currentPos += obj.height * obj.scaleY + gap;
                }
                return;
            }

            if (direction === 'horizontal') {
                obj.set('left', currentPos);
                currentPos += obj.width * obj.scaleX + gap;
            } else {
                obj.set('top', currentPos);
                currentPos += obj.height * obj.scaleY + gap;
            }
            obj.setCoords();
        });

        canvas.requestRenderAll();
        DesignCanvas.saveHistory();
        return true;
    },

    /**
     * Flip selected object
     * @param {string} direction - horizontal or vertical
     */
    flipObject(direction) {
        const activeObject = DesignCanvas.canvas.getActiveObject();
        if (!activeObject) return false;

        if (direction === 'horizontal') {
            activeObject.set('flipX', !activeObject.flipX);
        } else {
            activeObject.set('flipY', !activeObject.flipY);
        }

        DesignCanvas.canvas.requestRenderAll();
        DesignCanvas.saveHistory();
        return true;
    },

    /**
     * Rotate selected object by a specific amount
     */
    rotateObject(degrees) {
        const activeObject = DesignCanvas.canvas.getActiveObject();
        if (!activeObject) return false;

        const currentAngle = activeObject.angle || 0;
        activeObject.set('angle', currentAngle + degrees);
        activeObject.setCoords();

        DesignCanvas.canvas.requestRenderAll();
        DesignCanvas.saveHistory();
        return true;
    },

    /**
     * Scale object by a factor
     */
    scaleObject(factor) {
        const activeObject = DesignCanvas.canvas.getActiveObject();
        if (!activeObject) return false;

        activeObject.scale(activeObject.scaleX * factor);
        activeObject.setCoords();

        DesignCanvas.canvas.requestRenderAll();
        DesignCanvas.saveHistory();
        return true;
    },

    /**
     * Lock/unlock object from editing
     */
    lockObject(id, locked = true) {
        const obj = DesignCanvas.getObjectById(id);
        if (!obj) return false;

        obj.set({
            lockMovementX: locked,
            lockMovementY: locked,
            lockRotation: locked,
            lockScalingX: locked,
            lockScalingY: locked,
            hasControls: !locked,
            selectable: !locked
        });

        DesignCanvas.canvas.requestRenderAll();
        return true;
    },

    /**
     * Get all objects on canvas as structured data
     */
    getCanvasObjects() {
        const objects = DesignCanvas.canvas.getObjects();
        return objects.map(obj => ({
            id: obj.id,
            type: obj.type,
            left: Math.round(obj.left),
            top: Math.round(obj.top),
            width: Math.round((obj.width || 0) * (obj.scaleX || 1)),
            height: Math.round((obj.height || 0) * (obj.scaleY || 1)),
            fill: obj.fill,
            stroke: obj.stroke,
            opacity: obj.opacity,
            angle: obj.angle
        }));
    }
};
