const DesignTools = {
    init() {
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.addEventListener('click', () => this.handleTool(btn.dataset.tool));
        });

        document.getElementById('btn-delete')?.addEventListener('click', () => this.deleteSelected());
        document.getElementById('btn-duplicate')?.addEventListener('click', () => this.duplicateSelected());
        document.getElementById('btn-bring-front')?.addEventListener('click', () => this.bringToFront());
        document.getElementById('btn-bring-forward')?.addEventListener('click', () => this.bringForward());
        document.getElementById('btn-send-backward')?.addEventListener('click', () => this.sendBackward());
        document.getElementById('btn-send-back')?.addEventListener('click', () => this.sendToBack());
    },

    handleTool(tool) {
        switch (tool) {
            case 'rectangle':
                this.addRectangle();
                break;
            case 'circle':
                this.addCircle();
                break;
            case 'line':
                this.addLine();
                break;
            case 'text':
                this.addText();
                break;
            case 'image':
                this.addImage();
                break;
        }
    },

    addRectangle(x = 200, y = 160, width = 240, height = 140, fill = '#FFB100', stroke = '#111111', strokeWidth = 2, id = null) {
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', x);
        rect.setAttribute('y', y);
        rect.setAttribute('width', width);
        rect.setAttribute('height', height);
        rect.setAttribute('fill', fill);
        rect.setAttribute('stroke', stroke);
        rect.setAttribute('stroke-width', strokeWidth);
        rect.setAttribute('id', id || this.generateId('rect'));
        DesignCanvas.addElement(rect);
    },

    addCircle(cx = 300, cy = 300, radius = 80, fill = '#fff8e8', stroke = '#111111', strokeWidth = 2, id = null) {
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', cx);
        circle.setAttribute('cy', cy);
        circle.setAttribute('r', radius);
        circle.setAttribute('fill', fill);
        circle.setAttribute('stroke', stroke);
        circle.setAttribute('stroke-width', strokeWidth);
        circle.setAttribute('id', id || this.generateId('circle'));
        DesignCanvas.addElement(circle);
    },

    addLine(x1 = 120, y1 = 120, x2 = 420, y2 = 120, stroke = '#111111', strokeWidth = 3, id = null) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', x1);
        line.setAttribute('y1', y1);
        line.setAttribute('x2', x2);
        line.setAttribute('y2', y2);
        line.setAttribute('stroke', stroke);
        line.setAttribute('stroke-width', strokeWidth);
        line.setAttribute('id', id || this.generateId('line'));
        DesignCanvas.addElement(line);
    },

    addText(x = 180, y = 200, text = 'Text', fontSize = 32, fill = '#111111', id = null) {
        const textEl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        textEl.setAttribute('x', x);
        textEl.setAttribute('y', y);
        textEl.setAttribute('fill', fill);
        textEl.setAttribute('font-size', fontSize);
        textEl.setAttribute('font-family', 'Poppins');
        textEl.setAttribute('font-weight', '700');
        textEl.setAttribute('id', id || this.generateId('text'));
        textEl.textContent = text;
        DesignCanvas.addElement(textEl);
    },

    addPath(path, fill = 'none', stroke = '#111111', strokeWidth = 2, id = null) {
        const pathEl = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        pathEl.setAttribute('d', path);
        pathEl.setAttribute('fill', fill);
        pathEl.setAttribute('stroke', stroke);
        pathEl.setAttribute('stroke-width', strokeWidth);
        pathEl.setAttribute('id', id || this.generateId('path'));
        DesignCanvas.addElement(pathEl);
    },

    addImage(href = '', x = 200, y = 200, width = 200, height = 200, id = null) {
        const img = document.createElementNS('http://www.w3.org/2000/svg', 'image');
        img.setAttribute('href', href);
        img.setAttribute('x', x);
        img.setAttribute('y', y);
        img.setAttribute('width', width);
        img.setAttribute('height', height);
        img.setAttribute('id', id || this.generateId('image'));
        DesignCanvas.addElement(img);
    },

    updateElement(id, attributes) {
        DesignCanvas.updateElement(id, attributes);
    },

    deleteSelected() {
        const id = DesignCanvas.getSelectedId();
        if (id) {
            DesignCanvas.removeElement(id);
            DesignCanvas.clearSelection();
        }
    },

    duplicateSelected() {
        const id = DesignCanvas.getSelectedId();
        if (!id) return;
        const element = document.getElementById(id);
        if (!element) return;
        const clone = element.cloneNode(true);
        clone.id = this.generateId('copy');
        DesignCanvas.addElement(clone);
        DesignCanvas.setSelection(clone);
    },

    bringToFront() {
        const element = DesignCanvas.selectedElement;
        if (element) {
            DesignCanvas.svg.appendChild(element);
        }
    },

    sendToBack() {
        const element = DesignCanvas.selectedElement;
        if (element) {
            const bg = document.getElementById('svg-background');
            if (bg && bg.nextSibling) {
                DesignCanvas.svg.insertBefore(element, bg.nextSibling);
            } else {
                DesignCanvas.svg.insertBefore(element, DesignCanvas.svg.firstChild);
            }
        }
    },

    bringForward() {
        const element = DesignCanvas.selectedElement;
        if (element && element.nextSibling) {
            DesignCanvas.svg.insertBefore(element.nextSibling, element);
        }
    },

    sendBackward() {
        const element = DesignCanvas.selectedElement;
        if (element && element.previousSibling && element.previousSibling.id !== 'svg-background') {
            DesignCanvas.svg.insertBefore(element, element.previousSibling);
        }
    },

    setBackground(color) {
        DesignCanvas.setBackground(color);
    },

    setCanvasSize(width, height) {
        DesignCanvas.applyCanvasSize(width, height);
        DesignCanvas.setBackground(DesignCanvas.background);
    },

    generateId(prefix) {
        return `${prefix}_${Math.random().toString(36).slice(2, 9)}`;
    }
};
