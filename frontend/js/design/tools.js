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
        // Ensure external URLs are proxied
        let finalUrl = url;
        if (url && (url.startsWith('http://') || url.startsWith('https://')) && !url.includes('/proxy_image')) {
            finalUrl = `/proxy_image?url=${encodeURIComponent(url)}`;
        }

        fabric.Image.fromURL(finalUrl, (img) => {
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

    addRectangle(x, y, width, height, fill, stroke, strokeWidth, opacity, rx, ry, angle, id) {
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
            id: id || this.generateId()
        });

        DesignCanvas.addObject(rect);
        return rect.id;
    },

    addCircle(x, y, radius, fill, stroke, strokeWidth, opacity, id) {
        const circle = new fabric.Circle({
            left: x,
            top: y,
            originX: 'center',
            originY: 'center',
            radius: radius,
            fill: fill || this.defaultFill,
            stroke: stroke || null,
            strokeWidth: strokeWidth || 0,
            opacity: opacity !== undefined ? opacity : 1,
            id: id || this.generateId()
        });

        DesignCanvas.addObject(circle);
        return circle.id;
    },

    addEllipse(x, y, rx, ry, fill, stroke, strokeWidth, opacity, angle, id) {
        const ellipse = new fabric.Ellipse({
            left: x,
            top: y,
            originX: 'center',
            originY: 'center',
            rx: rx,
            ry: ry,
            fill: fill || this.defaultFill,
            stroke: stroke || null,
            strokeWidth: strokeWidth || 0,
            opacity: opacity !== undefined ? opacity : 1,
            angle: angle || 0,
            id: id || this.generateId()
        });

        DesignCanvas.addObject(ellipse);
        return ellipse.id;
    },

    addTriangle(x, y, width, height, fill, stroke, strokeWidth, opacity, angle, id) {
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
            id: id || this.generateId()
        });

        DesignCanvas.addObject(triangle);
        return triangle.id;
    },

    addLine(x1, y1, x2, y2, stroke, strokeWidth, opacity, id) {
        const line = new fabric.Line([x1, y1, x2, y2], {
            stroke: stroke || '#000000',
            strokeWidth: strokeWidth || 2,
            opacity: opacity !== undefined ? opacity : 1,
            id: id || this.generateId()
        });

        DesignCanvas.addObject(line);
        return line.id;
    },

    addText(x, y, text, fontSize, fontFamily, fontWeight, fill, textAlign, opacity, angle, id) {
        // Fix common typo for textBaseline if it ever reaches here
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
            id: id || this.generateId()
        });

        // Ensure textBaseline is correct
        if (textObj.textBaseline === 'alphabetical') {
            textObj.set('textBaseline', 'alphabetic');
        }

        DesignCanvas.addObject(textObj);
        return textObj.id;
    },

    addPolygon(x, y, radius, sides, fill, stroke, strokeWidth, opacity, angle, id) {
        const points = this.createPolygonPoints({ x: 0, y: 0 }, radius, sides);
        const polygon = new fabric.Polygon(points, {
            left: x,
            top: y,
            originX: 'center',
            originY: 'center',
            fill: fill || this.defaultFill,
            stroke: stroke || null,
            strokeWidth: strokeWidth || 0,
            opacity: opacity !== undefined ? opacity : 1,
            angle: angle || 0,
            id: id || this.generateId()
        });

        DesignCanvas.addObject(polygon);
        return polygon.id;
    },

    addPolygonFromPoints(points, fill, stroke, strokeWidth, opacity, angle, id) {
        if (!points || points.length === 0) return null;
        const normalized = points.map(point => Array.isArray(point) ? point : [point.x, point.y]);
        const xs = normalized.map(point => point[0]);
        const ys = normalized.map(point => point[1]);
        const minX = Math.min(...xs);
        const minY = Math.min(...ys);
        const adjusted = normalized.map(point => ({ x: point[0] - minX, y: point[1] - minY }));

        const polygon = new fabric.Polygon(adjusted, {
            left: minX,
            top: minY,
            fill: fill || this.defaultFill,
            stroke: stroke || null,
            strokeWidth: strokeWidth || 0,
            opacity: opacity !== undefined ? opacity : 1,
            angle: angle || 0,
            id: id || this.generateId()
        });

        DesignCanvas.addObject(polygon);
        return polygon.id;
    },

    addStar(x, y, outerRadius, innerRadius, points, fill, stroke, strokeWidth, opacity, angle, id) {
        const starPoints = this.createStarPoints({ x: 0, y: 0 }, outerRadius, innerRadius || outerRadius * 0.4, points || 5);
        const star = new fabric.Polygon(starPoints, {
            left: x,
            top: y,
            originX: 'center',
            originY: 'center',
            fill: fill || this.defaultFill,
            stroke: stroke || null,
            strokeWidth: strokeWidth || 0,
            opacity: opacity !== undefined ? opacity : 1,
            angle: angle || 0,
            id: id || this.generateId()
        });

        DesignCanvas.addObject(star);
        return star.id;
    },

    addPath(path, fill, stroke, strokeWidth, opacity, angle, id) {
        if (!path) return null;
        const svgPath = new fabric.Path(path, {
            left: 0,
            top: 0,
            fill: fill || this.defaultFill,
            stroke: stroke || null,
            strokeWidth: strokeWidth || 0,
            opacity: opacity !== undefined ? opacity : 1,
            angle: angle || 0,
            id: id || this.generateId()
        });

        DesignCanvas.addObject(svgPath);
        return svgPath.id;
    },

    addImage(url, x, y, width, height, opacity, angle, id) {
        if (!url) return Promise.resolve(null);

        // Ensure URL is proxied if it's external
        let finalUrl = url;
        if (url && (url.startsWith('http://') || url.startsWith('https://')) && !url.includes('/proxy_image')) {
            finalUrl = `/proxy_image?url=${encodeURIComponent(url)}`;
        }

        return new Promise((resolve) => {
            fabric.Image.fromURL(finalUrl, (img) => {
                const props = {
                    left: x,
                    top: y,
                    opacity: opacity !== undefined ? opacity : 1,
                    angle: angle || 0,
                    id: id || this.generateId()
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
        if (properties.scaleX !== undefined) mappedProps.scaleX = properties.scaleX;
        if (properties.scaleY !== undefined) mappedProps.scaleY = properties.scaleY;
        if (properties.text !== undefined) mappedProps.text = properties.text;
        if (properties.fontSize !== undefined) mappedProps.fontSize = properties.fontSize;
        if (properties.fontFamily !== undefined) mappedProps.fontFamily = properties.fontFamily;
        if (properties.fontWeight !== undefined) mappedProps.fontWeight = properties.fontWeight;
        if (properties.fontStyle !== undefined) mappedProps.fontStyle = properties.fontStyle;
        if (properties.textAlign !== undefined) mappedProps.textAlign = properties.textAlign;
        if (properties.rx !== undefined) mappedProps.rx = properties.rx;
        if (properties.ry !== undefined) mappedProps.ry = properties.ry;

        // Fix textBaseline typo and apply if present
        if (properties.textBaseline === 'alphabetical') properties.textBaseline = 'alphabetic';
        if (properties.textBaseline !== undefined) mappedProps.textBaseline = properties.textBaseline;

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

    groupObjects(ids, groupId) {
        const canvas = DesignCanvas.canvas;
        const objects = ids.map(id => DesignCanvas.getObjectById(id)).filter(Boolean);

        if (objects.length < 2) return null;

        const group = new fabric.Group(objects, {
            id: groupId || this.generateId()
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
            if (!item.id) {
                item.id = this.generateId();
            }
            ids.push(item.id);
            canvas.add(item);
        });

        canvas.requestRenderAll();
        DesignCanvas.saveHistory();

        return ids;
    },
    duplicateObject(id, newId) {
        const obj = DesignCanvas.getObjectById(id);
        if (!obj) return null;

        obj.clone((cloned) => {
            cloned.set({
                left: (cloned.left || 0) + 20,
                top: (cloned.top || 0) + 20,
                id: newId || this.generateId()
            });

            if (cloned.type === 'activeSelection') {
                cloned.canvas = DesignCanvas.canvas;
                cloned.forEachObject((child) => {
                    child.id = this.generateId();
                    DesignCanvas.canvas.add(child);
                });
                cloned.setCoords();
            } else {
                DesignCanvas.canvas.add(cloned);
            }

            DesignCanvas.canvas.setActiveObject(cloned);
            DesignCanvas.canvas.requestRenderAll();
            DesignCanvas.saveHistory();
        });

        return true;
    },

    bringToFront(id) {
        const obj = DesignCanvas.getObjectById(id);
        if (!obj) return false;
        DesignCanvas.canvas.bringToFront(obj);
        DesignCanvas.canvas.requestRenderAll();
        DesignCanvas.saveHistory();
        return true;
    },

    sendToBack(id) {
        const obj = DesignCanvas.getObjectById(id);
        if (!obj) return false;
        DesignCanvas.canvas.sendToBack(obj);
        DesignCanvas.canvas.requestRenderAll();
        DesignCanvas.saveHistory();
        return true;
    },

    bringForward(id) {
        const obj = DesignCanvas.getObjectById(id);
        if (!obj) return false;
        DesignCanvas.canvas.bringForward(obj);
        DesignCanvas.canvas.requestRenderAll();
        DesignCanvas.saveHistory();
        return true;
    },

    sendBackward(id) {
        const obj = DesignCanvas.getObjectById(id);
        if (!obj) return false;
        DesignCanvas.canvas.sendBackwards(obj);
        DesignCanvas.canvas.requestRenderAll();
        DesignCanvas.saveHistory();
        return true;
    },

    alignObjects(ids, alignment) {
        const canvas = DesignCanvas.canvas;
        const objects = ids.map(id => DesignCanvas.getObjectById(id)).filter(Boolean);
        if (objects.length < 2) return false;

        const bounds = objects.map(obj => obj.getBoundingRect(true));
        const minX = Math.min(...bounds.map(b => b.left));
        const maxX = Math.max(...bounds.map(b => b.left + b.width));
        const minY = Math.min(...bounds.map(b => b.top));
        const maxY = Math.max(...bounds.map(b => b.top + b.height));
        const centerX = (minX + maxX) / 2;
        const centerY = (minY + maxY) / 2;

        objects.forEach((obj, index) => {
            const rect = bounds[index];
            switch (alignment) {
                case 'left':
                    obj.set('left', minX);
                    break;
                case 'center':
                    obj.set('left', centerX - rect.width / 2);
                    break;
                case 'right':
                    obj.set('left', maxX - rect.width);
                    break;
                case 'top':
                    obj.set('top', minY);
                    break;
                case 'middle':
                    obj.set('top', centerY - rect.height / 2);
                    break;
                case 'bottom':
                    obj.set('top', maxY - rect.height);
                    break;
            }
            obj.setCoords();
        });

        canvas.requestRenderAll();
        DesignCanvas.saveHistory();
        return true;
    },

    distributeObjects(ids, direction) {
        const canvas = DesignCanvas.canvas;
        const objects = ids.map(id => DesignCanvas.getObjectById(id)).filter(Boolean);
        if (objects.length < 3) return false;

        const sorted = objects.slice().sort((a, b) => {
            const rectA = a.getBoundingRect(true);
            const rectB = b.getBoundingRect(true);
            return direction === 'horizontal' ? rectA.left - rectB.left : rectA.top - rectB.top;
        });

        if (direction === 'horizontal') {
            const leftMost = sorted[0].getBoundingRect(true).left;
            const rightMost = sorted[sorted.length - 1].getBoundingRect(true);
            const totalWidth = sorted.reduce((sum, obj) => sum + obj.getBoundingRect(true).width, 0);
            const spacing = (rightMost.left + rightMost.width - leftMost - totalWidth) / (sorted.length - 1);

            let current = leftMost;
            sorted.forEach((obj) => {
                const rect = obj.getBoundingRect(true);
                obj.set('left', current);
                obj.setCoords();
                current += rect.width + spacing;
            });
        } else {
            const topMost = sorted[0].getBoundingRect(true).top;
            const bottomMost = sorted[sorted.length - 1].getBoundingRect(true);
            const totalHeight = sorted.reduce((sum, obj) => sum + obj.getBoundingRect(true).height, 0);
            const spacing = (bottomMost.top + bottomMost.height - topMost - totalHeight) / (sorted.length - 1);

            let current = topMost;
            sorted.forEach((obj) => {
                const rect = obj.getBoundingRect(true);
                obj.set('top', current);
                obj.setCoords();
                current += rect.height + spacing;
            });
        }

        canvas.requestRenderAll();
        DesignCanvas.saveHistory();
        return true;
    },

    // =========================================================================
    // ADVANCED EFFECTS
    // =========================================================================

    /**
     * Add a drop shadow to an object
     */
    addShadow(id, offsetX = 4, offsetY = 4, blur = 8, color = 'rgba(0, 0, 0, 0.3)', spread = 0, inset = false) {
        const obj = DesignCanvas.getObjectById(id);
        if (!obj) return false;

        const shadow = new fabric.Shadow({
            color: color,
            blur: blur,
            offsetX: offsetX,
            offsetY: offsetY,
            affectStroke: false,
            nonScaling: false
        });

        obj.set('shadow', shadow);
        DesignCanvas.canvas.requestRenderAll();
        DesignCanvas.saveHistory();
        return true;
    },

    /**
     * Remove shadow from an object
     */
    removeShadow(id) {
        const obj = DesignCanvas.getObjectById(id);
        if (!obj) return false;

        obj.set('shadow', null);
        DesignCanvas.canvas.requestRenderAll();
        DesignCanvas.saveHistory();
        return true;
    },

    /**
     * Apply a gradient fill to an object
     */
    setGradient(id, gradientType = 'linear', colors = null, angle = 0, stops = null, cx = 0.5, cy = 0.5, preset = null) {
        const obj = DesignCanvas.getObjectById(id);
        if (!obj) return false;

        // Handle preset gradients
        const presetGradients = {
            'blue_purple': { colors: ['#667eea', '#764ba2'], angle: 135 },
            'sunset': { colors: ['#f093fb', '#f5576c', '#f7971e'], angle: 135 },
            'ocean': { colors: ['#2193b0', '#6dd5ed'], angle: 135 },
            'midnight': { colors: ['#232526', '#414345'], angle: 135 },
            'emerald': { colors: ['#11998e', '#38ef7d'], angle: 135 },
            'fire': { colors: ['#f12711', '#f5af19'], angle: 135 },
            'rainbow': { colors: ['#ff0000', '#ff8000', '#ffff00', '#00ff00', '#0080ff', '#8000ff', '#ff00ff'], angle: 90 }
        };

        if (preset && presetGradients[preset.toLowerCase()]) {
            const p = presetGradients[preset.toLowerCase()];
            colors = p.colors;
            angle = p.angle;
        }

        if (!colors || colors.length < 2) {
            colors = ['#667eea', '#764ba2'];
        }

        // Build color stops
        const colorStops = {};
        if (stops && stops.length === colors.length) {
            colors.forEach((color, i) => {
                colorStops[stops[i]] = color;
            });
        } else {
            colors.forEach((color, i) => {
                const offset = i / (colors.length - 1);
                colorStops[offset] = color;
            });
        }

        let gradient;
        if (gradientType === 'radial') {
            gradient = new fabric.Gradient({
                type: 'radial',
                coords: {
                    x1: obj.width * cx,
                    y1: obj.height * cy,
                    x2: obj.width * cx,
                    y2: obj.height * cy,
                    r1: 0,
                    r2: Math.max(obj.width, obj.height) * 0.7
                },
                colorStops: Object.entries(colorStops).map(([offset, color]) => ({
                    offset: parseFloat(offset),
                    color: color
                }))
            });
        } else {
            // Linear gradient
            const rad = angle * Math.PI / 180;
            const x1 = 0.5 - 0.5 * Math.cos(rad);
            const y1 = 0.5 - 0.5 * Math.sin(rad);
            const x2 = 0.5 + 0.5 * Math.cos(rad);
            const y2 = 0.5 + 0.5 * Math.sin(rad);

            gradient = new fabric.Gradient({
                type: 'linear',
                coords: {
                    x1: obj.width * x1,
                    y1: obj.height * y1,
                    x2: obj.width * x2,
                    y2: obj.height * y2
                },
                colorStops: Object.entries(colorStops).map(([offset, color]) => ({
                    offset: parseFloat(offset),
                    color: color
                }))
            });
        }

        obj.set('fill', gradient);
        DesignCanvas.canvas.requestRenderAll();
        DesignCanvas.saveHistory();
        return true;
    },

    /**
     * Remove gradient from an object, optionally restore solid color
     */
    removeGradient(id, restoreColor = null) {
        const obj = DesignCanvas.getObjectById(id);
        if (!obj) return false;

        obj.set('fill', restoreColor || '#4ade80');
        DesignCanvas.canvas.requestRenderAll();
        DesignCanvas.saveHistory();
        return true;
    },

    /**
     * Set border radius for rounded corners
     */
    setBorderRadius(id, radius) {
        const obj = DesignCanvas.getObjectById(id);
        if (!obj) return false;

        if (obj.type === 'rect') {
            obj.set({
                rx: radius,
                ry: radius
            });
        }

        DesignCanvas.canvas.requestRenderAll();
        DesignCanvas.saveHistory();
        return true;
    },

    /**
     * Apply advanced text styling
     */
    styleText(id, options = {}) {
        const obj = DesignCanvas.getObjectById(id);
        if (!obj || (obj.type !== 'i-text' && obj.type !== 'text' && obj.type !== 'textbox')) {
            return false;
        }

        const props = {};

        if (options.letterSpacing !== undefined) {
            props.charSpacing = options.letterSpacing * 10; // Fabric uses charSpacing in 1/1000 em
        }
        if (options.lineHeight !== undefined) {
            props.lineHeight = options.lineHeight;
        }
        if (options.textDecoration !== undefined) {
            props.underline = options.textDecoration === 'underline';
            props.linethrough = options.textDecoration === 'line-through';
        }
        if (options.textTransform !== undefined) {
            // Apply transform to text content
            let text = obj.text;
            switch (options.textTransform) {
                case 'uppercase':
                    text = text.toUpperCase();
                    break;
                case 'lowercase':
                    text = text.toLowerCase();
                    break;
                case 'capitalize':
                    text = text.replace(/\b\w/g, l => l.toUpperCase());
                    break;
            }
            props.text = text;
        }

        // Text shadow
        if (options.textShadowX !== undefined || options.textShadowY !== undefined ||
            options.textShadowBlur !== undefined || options.textShadowColor !== undefined) {
            const shadow = new fabric.Shadow({
                color: options.textShadowColor || 'rgba(0, 0, 0, 0.3)',
                blur: options.textShadowBlur || 2,
                offsetX: options.textShadowX || 1,
                offsetY: options.textShadowY || 1
            });
            props.shadow = shadow;
        }

        obj.set(props);
        DesignCanvas.canvas.requestRenderAll();
        DesignCanvas.saveHistory();
        return true;
    },

    /**
     * Set blend mode for an object (visual effect)
     * Note: Fabric.js supports globalCompositeOperation for blend modes
     */
    setBlendMode(id, mode) {
        const obj = DesignCanvas.getObjectById(id);
        if (!obj) return false;

        const validModes = [
            'normal', 'multiply', 'screen', 'overlay', 'darken', 'lighten',
            'color-dodge', 'color-burn', 'hard-light', 'soft-light',
            'difference', 'exclusion', 'hue', 'saturation', 'color', 'luminosity'
        ];

        if (validModes.includes(mode)) {
            obj.set('globalCompositeOperation', mode);
            DesignCanvas.canvas.requestRenderAll();
            DesignCanvas.saveHistory();
            return true;
        }
        return false;
    },

    /**
     * Apply effect preset (combines multiple effects)
     */
    applyEffectPreset(id, preset) {
        const obj = DesignCanvas.getObjectById(id);
        if (!obj) return false;

        const presetLower = preset.toLowerCase().replace(/[-\s]/g, '_');

        // Shadow presets
        switch (presetLower) {
            case 'soft_shadow':
                return this.addShadow(id, 0, 4, 12, 'rgba(0, 0, 0, 0.15)');
            case 'hard_shadow':
                return this.addShadow(id, 4, 4, 0, 'rgba(0, 0, 0, 0.25)');
            case 'glow':
                return this.addShadow(id, 0, 0, 20, 'rgba(255, 255, 255, 0.8)');
            case 'glow_blue':
                return this.addShadow(id, 0, 0, 20, 'rgba(59, 130, 246, 0.8)');
            case 'glow_purple':
                return this.addShadow(id, 0, 0, 20, 'rgba(139, 92, 246, 0.8)');
            case 'glow_pink':
                return this.addShadow(id, 0, 0, 20, 'rgba(236, 72, 153, 0.8)');
            case 'glow_green':
                return this.addShadow(id, 0, 0, 20, 'rgba(16, 185, 129, 0.8)');
            case 'inner_shadow':
                // Note: True inner shadow not supported in Fabric.js, using small offset
                return this.addShadow(id, 2, 2, 4, 'rgba(0, 0, 0, 0.2)');
            case 'long_shadow':
                return this.addShadow(id, 20, 20, 0, 'rgba(0, 0, 0, 0.15)');

            // Gradient presets
            case 'blue_purple':
            case 'sunset':
            case 'ocean':
            case 'midnight':
            case 'emerald':
            case 'fire':
            case 'rainbow':
                return this.setGradient(id, 'linear', null, 0, null, 0.5, 0.5, presetLower);

            // Filter-like presets (applied via opacity/color manipulation)
            case 'glassmorphism':
                // Semi-transparent with blur-like effect via opacity
                obj.set({ opacity: 0.7 });
                this.addShadow(id, 0, 8, 32, 'rgba(0, 0, 0, 0.1)');
                if (obj.type === 'rect') {
                    this.setBorderRadius(id, 16);
                }
                DesignCanvas.canvas.requestRenderAll();
                DesignCanvas.saveHistory();
                return true;

            default:
                console.warn('Unknown effect preset:', preset);
                return false;
        }
    },

    /**
     * Set backdrop blur (glassmorphism effect)
     * Note: True backdrop blur requires CSS filters, we simulate with opacity
     */
    setBackdropBlur(id, blur) {
        const obj = DesignCanvas.getObjectById(id);
        if (!obj) return false;

        // Fabric.js doesn't support backdrop-filter directly
        // We simulate the effect with reduced opacity
        const simulatedOpacity = Math.max(0.5, 1 - (blur / 40));
        obj.set('opacity', simulatedOpacity);
        DesignCanvas.canvas.requestRenderAll();
        DesignCanvas.saveHistory();
        return true;
    },

    /**
     * Add a filter effect to an object
     * Note: Fabric.js has limited filter support for shapes (mainly for images)
     */
    addFilter(id, filterType, value) {
        const obj = DesignCanvas.getObjectById(id);
        if (!obj) return false;

        // For images, we can apply Fabric.js filters
        if (obj.type === 'image') {
            if (!obj.filters) obj.filters = [];

            switch (filterType.toLowerCase()) {
                case 'brightness':
                    obj.filters.push(new fabric.Image.filters.Brightness({ brightness: value - 1 }));
                    break;
                case 'contrast':
                    obj.filters.push(new fabric.Image.filters.Contrast({ contrast: value - 1 }));
                    break;
                case 'saturation':
                    obj.filters.push(new fabric.Image.filters.Saturation({ saturation: value - 1 }));
                    break;
                case 'grayscale':
                    obj.filters.push(new fabric.Image.filters.Grayscale());
                    break;
                case 'sepia':
                    obj.filters.push(new fabric.Image.filters.Sepia());
                    break;
                case 'invert':
                    obj.filters.push(new fabric.Image.filters.Invert());
                    break;
                case 'blur':
                    obj.filters.push(new fabric.Image.filters.Blur({ blur: value / 10 }));
                    break;
                default:
                    console.warn('Unknown filter type:', filterType);
                    return false;
            }

            obj.applyFilters();
            DesignCanvas.canvas.requestRenderAll();
            DesignCanvas.saveHistory();
            return true;
        }

        // For non-images, filter effects are limited
        console.warn('Filters are primarily supported for images in Fabric.js');
        return false;
    },

    /**
     * Remove all filters from an object
     */
    removeFilters(id, filterType = null) {
        const obj = DesignCanvas.getObjectById(id);
        if (!obj) return false;

        if (obj.type === 'image') {
            obj.filters = [];
            obj.applyFilters();
            DesignCanvas.canvas.requestRenderAll();
            DesignCanvas.saveHistory();
        }
        return true;
    },

    /**
     * Set gradient background for the canvas
     */
    setGradientBackground(gradientType = 'linear', colors = null, angle = 0) {
        if (!colors || colors.length < 2) {
            colors = ['#667eea', '#764ba2'];
        }

        const canvas = DesignCanvas.canvas;
        const width = canvas.width;
        const height = canvas.height;

        // Build color stops
        const colorStops = {};
        colors.forEach((color, i) => {
            const offset = i / (colors.length - 1);
            colorStops[offset] = color;
        });

        let gradient;
        if (gradientType === 'radial') {
            gradient = new fabric.Gradient({
                type: 'radial',
                coords: {
                    x1: width / 2,
                    y1: height / 2,
                    x2: width / 2,
                    y2: height / 2,
                    r1: 0,
                    r2: Math.max(width, height) * 0.7
                },
                colorStops: Object.entries(colorStops).map(([offset, color]) => ({
                    offset: parseFloat(offset),
                    color: color
                }))
            });
        } else {
            const rad = angle * Math.PI / 180;
            const x1 = 0.5 - 0.5 * Math.cos(rad);
            const y1 = 0.5 - 0.5 * Math.sin(rad);
            const x2 = 0.5 + 0.5 * Math.cos(rad);
            const y2 = 0.5 + 0.5 * Math.sin(rad);

            gradient = new fabric.Gradient({
                type: 'linear',
                coords: {
                    x1: width * x1,
                    y1: height * y1,
                    x2: width * x2,
                    y2: height * y2
                },
                colorStops: Object.entries(colorStops).map(([offset, color]) => ({
                    offset: parseFloat(offset),
                    color: color
                }))
            });
        }

        // Create a background rect with gradient
        // Remove existing background rect if any
        const existingBg = canvas.getObjects().find(obj => obj.id === 'canvas-background-gradient');
        if (existingBg) {
            canvas.remove(existingBg);
        }

        const bgRect = new fabric.Rect({
            id: 'canvas-background-gradient',
            left: 0,
            top: 0,
            width: width,
            height: height,
            fill: gradient,
            selectable: false,
            evented: false,
            excludeFromExport: false
        });

        canvas.insertAt(bgRect, 0);
        canvas.requestRenderAll();
        DesignCanvas.saveHistory();
        return true;
    }
};
