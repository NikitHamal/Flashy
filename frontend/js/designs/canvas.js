(function () {
    const state = window.DesignState;
    const utils = window.DesignUtils;

    function initCanvas(canvasId, width, height) {
        const canvas = new fabric.Canvas(canvasId, {
            backgroundColor: '#ffffff',
            preserveObjectStacking: true,
            selection: true
        });
        canvas.setWidth(width);
        canvas.setHeight(height);
        canvas.renderAll();

        canvas.on('mouse:down', (opt) => handleMouseDown(opt));
        canvas.on('mouse:move', (opt) => handleMouseMove(opt));
        canvas.on('mouse:up', () => handleMouseUp());

        canvas.on('selection:created', () => window.DesignUI.syncSelection());
        canvas.on('selection:updated', () => window.DesignUI.syncSelection());
        canvas.on('selection:cleared', () => window.DesignUI.syncSelection());

        state.canvas = canvas;
        return canvas;
    }

    let activeShape = null;
    let startPoint = null;

    function handleMouseDown(opt) {
        if (!state.canvas) return;
        const pointer = state.canvas.getPointer(opt.e);

        if (state.currentTool === 'hand') {
            state.isPanning = true;
            state.panStart = { x: opt.e.clientX, y: opt.e.clientY };
            return;
        }

        if (state.currentTool === 'select') {
            return;
        }

        if (state.currentTool === 'text') {
            const text = new fabric.IText('Type here', {
                left: pointer.x,
                top: pointer.y,
                fontFamily: 'Space Grotesk',
                fill: '#111111',
                fontSize: 42
            });
            state.canvas.add(text);
            state.canvas.setActiveObject(text);
            state.canvas.renderAll();
            window.DesignHistory.capture();
            return;
        }

        if (state.currentTool === 'image') {
            document.getElementById('asset-upload').click();
            return;
        }

        startPoint = pointer;

        if (state.currentTool === 'rect' || state.currentTool === 'frame') {
            activeShape = new fabric.Rect({
                left: pointer.x,
                top: pointer.y,
                width: 1,
                height: 1,
                fill: state.currentTool === 'frame' ? 'rgba(255,255,255,0.03)' : '#ffffff',
                stroke: state.currentTool === 'frame' ? '#111111' : '#111111',
                strokeWidth: state.currentTool === 'frame' ? 2 : 0,
                rx: 0,
                ry: 0
            });
        }

        if (state.currentTool === 'circle') {
            activeShape = new fabric.Ellipse({
                left: pointer.x,
                top: pointer.y,
                rx: 1,
                ry: 1,
                fill: '#ffffff',
                stroke: '#111111',
                strokeWidth: 0
            });
        }

        if (state.currentTool === 'line') {
            activeShape = new fabric.Line([pointer.x, pointer.y, pointer.x + 1, pointer.y + 1], {
                stroke: '#111111',
                strokeWidth: 2
            });
        }

        if (activeShape) {
            state.canvas.add(activeShape);
        }
    }

    function handleMouseMove(opt) {
        if (!state.canvas) return;

        if (state.isPanning && state.currentTool === 'hand') {
            const dx = opt.e.clientX - state.panStart.x;
            const dy = opt.e.clientY - state.panStart.y;
            const vpt = state.canvas.viewportTransform;
            vpt[4] += dx;
            vpt[5] += dy;
            state.canvas.requestRenderAll();
            state.panStart = { x: opt.e.clientX, y: opt.e.clientY };
            return;
        }

        if (!activeShape || !startPoint) return;
        const pointer = state.canvas.getPointer(opt.e);
        const w = pointer.x - startPoint.x;
        const h = pointer.y - startPoint.y;

        if (activeShape.type === 'rect') {
            activeShape.set({
                width: Math.abs(w),
                height: Math.abs(h),
                left: w < 0 ? pointer.x : startPoint.x,
                top: h < 0 ? pointer.y : startPoint.y
            });
        }

        if (activeShape.type === 'ellipse') {
            activeShape.set({
                rx: Math.abs(w) / 2,
                ry: Math.abs(h) / 2,
                left: w < 0 ? pointer.x : startPoint.x,
                top: h < 0 ? pointer.y : startPoint.y
            });
        }

        if (activeShape.type === 'line') {
            activeShape.set({ x2: pointer.x, y2: pointer.y });
        }

        state.canvas.renderAll();
    }

    function handleMouseUp() {
        if (state.isPanning) {
            state.isPanning = false;
            return;
        }
        if (activeShape) {
            state.canvas.setActiveObject(activeShape);
            activeShape = null;
            startPoint = null;
            state.canvas.renderAll();
            window.DesignHistory.capture();
        }
    }

    function addImageFromFile(file) {
        const reader = new FileReader();
        reader.onload = () => {
            fabric.Image.fromURL(reader.result, (img) => {
                const maxSize = Math.min(state.canvas.width, state.canvas.height) * 0.6;
                const scale = Math.min(maxSize / img.width, maxSize / img.height, 1);
                img.set({
                    left: state.canvas.width / 2 - (img.width * scale) / 2,
                    top: state.canvas.height / 2 - (img.height * scale) / 2,
                    scaleX: scale,
                    scaleY: scale
                });
                state.canvas.add(img);
                state.canvas.setActiveObject(img);
                state.canvas.renderAll();
                window.DesignHistory.capture();
            }, { crossOrigin: 'anonymous' });
        };
        reader.readAsDataURL(file);
    }

    function setCanvasSize(width, height) {
        if (!state.canvas) return;
        state.canvas.setWidth(width);
        state.canvas.setHeight(height);
        state.canvas.renderAll();
        window.DesignUI.updateStatus();
        window.DesignHistory.capture();
    }

    function setZoom(value) {
        if (!state.canvas) return;
        state.zoom = utils.clamp(value, 0.2, 3);
        state.canvas.setZoom(state.zoom);
        state.canvas.requestRenderAll();
        window.DesignUI.updateZoom();
    }

    function fitToScreen() {
        if (!state.canvas) return;
        const stage = document.getElementById('canvas-stage');
        const padding = 80;
        const scale = Math.min(
            (stage.clientWidth - padding) / state.canvas.width,
            (stage.clientHeight - padding) / state.canvas.height
        );
        setZoom(scale);
        state.canvas.viewportTransform[4] = (stage.clientWidth - state.canvas.width * scale) / 2;
        state.canvas.viewportTransform[5] = (stage.clientHeight - state.canvas.height * scale) / 2;
        state.canvas.requestRenderAll();
    }

    function applyObjectProperties(obj, props) {
        if (!obj) return;
        obj.set(props);
        if (props.radius !== undefined) {
            obj.set({ rx: props.radius, ry: props.radius });
        }
        if (obj.type === 'i-text' && props.text !== undefined) {
            obj.text = props.text;
        }
        obj.setCoords();
        state.canvas.renderAll();
        window.DesignHistory.capture();
    }

    function applyDesignSpec(spec) {
        if (!spec || !state.canvas) return;
        if (spec.canvas) {
            if (spec.canvas.background) {
                state.canvas.setBackgroundColor(spec.canvas.background, state.canvas.renderAll.bind(state.canvas));
            }
            if (spec.canvas.width && spec.canvas.height) {
                setCanvasSize(spec.canvas.width, spec.canvas.height);
            }
        }
        if (Array.isArray(spec.elements)) {
            spec.elements.forEach(el => {
                if (el.type === 'rect') {
                    const rect = new fabric.Rect({
                        left: el.x || 100,
                        top: el.y || 100,
                        width: el.width || 200,
                        height: el.height || 120,
                        fill: el.fill || '#ffffff',
                        stroke: el.stroke || '#111111',
                        strokeWidth: el.strokeWidth || 0,
                        rx: el.radius || 0,
                        ry: el.radius || 0,
                        opacity: el.opacity ?? 1
                    });
                    state.canvas.add(rect);
                }
                if (el.type === 'circle') {
                    const circle = new fabric.Ellipse({
                        left: el.x || 100,
                        top: el.y || 100,
                        rx: (el.width || 160) / 2,
                        ry: (el.height || 160) / 2,
                        fill: el.fill || '#ffffff',
                        stroke: el.stroke || '#111111',
                        strokeWidth: el.strokeWidth || 0,
                        opacity: el.opacity ?? 1
                    });
                    state.canvas.add(circle);
                }
                if (el.type === 'text') {
                    const text = new fabric.IText(el.text || 'Headline', {
                        left: el.x || 120,
                        top: el.y || 120,
                        fontFamily: el.fontFamily || 'Space Grotesk',
                        fontSize: el.fontSize || 48,
                        fill: el.fill || '#111111',
                        fontWeight: el.fontWeight || '600',
                        textAlign: el.textAlign || 'left'
                    });
                    state.canvas.add(text);
                }
                if (el.type === 'line') {
                    const line = new fabric.Line([
                        el.x || 80,
                        el.y || 80,
                        (el.x || 80) + (el.width || 160),
                        (el.y || 80) + (el.height || 0)
                    ], {
                        stroke: el.stroke || '#111111',
                        strokeWidth: el.strokeWidth || 2,
                        opacity: el.opacity ?? 1
                    });
                    state.canvas.add(line);
                }
            });
            state.canvas.renderAll();
            window.DesignHistory.capture();
        }
    }

    window.DesignCanvas = {
        initCanvas,
        addImageFromFile,
        setCanvasSize,
        setZoom,
        fitToScreen,
        applyObjectProperties,
        applyDesignSpec
    };
})();
