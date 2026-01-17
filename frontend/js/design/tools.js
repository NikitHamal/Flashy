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

        DesignCanvas.addObject(textObj);
        return textObj.id;
    },

    addPolygon(x, y, radius, sides, fill, stroke, strokeWidth, opacity, angle, id) {
        const points = this.createPolygonPoints({ x: 0, y: 0 }, radius, sides);
        const polygon = new fabric.Polygon(points, {
            left: x,
            top: y,
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
        return new Promise((resolve) => {
            fabric.Image.fromURL(url, (img) => {
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
    }
};
