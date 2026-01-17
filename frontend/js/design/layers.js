/**
 * Design Layers Module
 * Manages the layers panel for viewing and organizing canvas objects
 */
const DesignLayers = {
    container: null,
    layersList: null,
    isVisible: false,

    init() {
        this.createLayersPanel();
        this.setupEventListeners();
        this.setupCanvasListeners();
        return this;
    },

    /**
     * Create the layers panel HTML structure
     */
    createLayersPanel() {
        // Create layers panel container
        const panel = document.createElement('div');
        panel.id = 'layers-panel';
        panel.className = 'layers-panel hidden';
        panel.innerHTML = `
            <div class="layers-header">
                <span>Layers</span>
                <div class="layers-header-actions">
                    <button id="btn-add-layer" class="btn-icon-xs" title="Add Layer">
                        <span class="material-symbols-outlined">add</span>
                    </button>
                    <button id="btn-close-layers" class="btn-icon-xs" title="Close">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
            </div>
            <div id="layers-list" class="layers-list"></div>
            <div class="layers-footer">
                <button id="btn-delete-layer" class="layer-action-btn" title="Delete Selected" disabled>
                    <span class="material-symbols-outlined">delete</span>
                </button>
                <button id="btn-duplicate-layer" class="layer-action-btn" title="Duplicate Selected" disabled>
                    <span class="material-symbols-outlined">content_copy</span>
                </button>
                <button id="btn-lock-layer" class="layer-action-btn" title="Lock/Unlock" disabled>
                    <span class="material-symbols-outlined">lock_open</span>
                </button>
                <button id="btn-visibility-layer" class="layer-action-btn" title="Show/Hide" disabled>
                    <span class="material-symbols-outlined">visibility</span>
                </button>
            </div>
        `;

        // Insert after the right sidebar
        const rightSidebar = document.querySelector('.right-sidebar');
        if (rightSidebar) {
            rightSidebar.parentNode.insertBefore(panel, rightSidebar.nextSibling);
        } else {
            document.querySelector('.design-app-container')?.appendChild(panel);
        }

        this.container = panel;
        this.layersList = panel.querySelector('#layers-list');

        // Add toggle button to canvas top bar
        const canvasActions = document.querySelector('.canvas-actions');
        if (canvasActions) {
            const toggleBtn = document.createElement('button');
            toggleBtn.id = 'btn-toggle-layers';
            toggleBtn.className = 'btn-ghost';
            toggleBtn.title = 'Toggle Layers Panel';
            toggleBtn.innerHTML = '<span class="material-symbols-outlined">layers</span>';

            // Insert before the divider
            const divider = canvasActions.querySelector('.action-divider');
            if (divider) {
                canvasActions.insertBefore(toggleBtn, divider);
            } else {
                canvasActions.insertBefore(toggleBtn, canvasActions.firstChild);
            }
        }
    },

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Toggle layers panel
        document.getElementById('btn-toggle-layers')?.addEventListener('click', () => {
            this.toggle();
        });

        // Close button
        document.getElementById('btn-close-layers')?.addEventListener('click', () => {
            this.hide();
        });

        // Footer actions
        document.getElementById('btn-delete-layer')?.addEventListener('click', () => {
            DesignCanvas.deleteSelected();
            this.refresh();
        });

        document.getElementById('btn-duplicate-layer')?.addEventListener('click', () => {
            DesignCanvas.duplicateSelected();
            this.refresh();
        });

        document.getElementById('btn-lock-layer')?.addEventListener('click', () => {
            this.toggleLockSelected();
        });

        document.getElementById('btn-visibility-layer')?.addEventListener('click', () => {
            this.toggleVisibilitySelected();
        });

        // Keyboard shortcut
        document.addEventListener('keydown', (e) => {
            if (e.key === 'F7' || (e.altKey && e.key === 'l')) {
                e.preventDefault();
                this.toggle();
            }
        });
    },

    /**
     * Set up canvas event listeners for auto-refresh
     */
    setupCanvasListeners() {
        if (!DesignCanvas.canvas) {
            // Wait for canvas to initialize
            setTimeout(() => this.setupCanvasListeners(), 100);
            return;
        }

        DesignCanvas.canvas.on('object:added', () => this.refresh());
        DesignCanvas.canvas.on('object:removed', () => this.refresh());
        DesignCanvas.canvas.on('object:modified', () => this.refresh());
        DesignCanvas.canvas.on('selection:created', () => this.updateSelection());
        DesignCanvas.canvas.on('selection:updated', () => this.updateSelection());
        DesignCanvas.canvas.on('selection:cleared', () => this.updateSelection());
    },

    /**
     * Show the layers panel
     */
    show() {
        this.container?.classList.remove('hidden');
        document.getElementById('btn-toggle-layers')?.classList.add('active');
        this.isVisible = true;
        this.refresh();
    },

    /**
     * Hide the layers panel
     */
    hide() {
        this.container?.classList.add('hidden');
        document.getElementById('btn-toggle-layers')?.classList.remove('active');
        this.isVisible = false;
    },

    /**
     * Toggle the layers panel
     */
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    },

    /**
     * Refresh the layers list
     */
    refresh() {
        if (!this.layersList || !DesignCanvas.canvas) return;

        const objects = DesignCanvas.canvas.getObjects();
        const activeObject = DesignCanvas.canvas.getActiveObject();
        const activeIds = this.getActiveObjectIds(activeObject);

        this.layersList.innerHTML = '';

        // Render layers in reverse order (top layer first)
        for (let i = objects.length - 1; i >= 0; i--) {
            const obj = objects[i];
            const layerItem = this.createLayerItem(obj, i, activeIds.includes(obj.id));
            this.layersList.appendChild(layerItem);
        }

        // Show empty state if no objects
        if (objects.length === 0) {
            this.layersList.innerHTML = `
                <div class="layers-empty">
                    <span class="material-symbols-outlined">layers_clear</span>
                    <p>No layers yet</p>
                </div>
            `;
        }

        this.updateActionButtons();
    },

    /**
     * Create a layer item element
     */
    createLayerItem(obj, index, isSelected) {
        const item = document.createElement('div');
        item.className = `layer-item${isSelected ? ' selected' : ''}${obj.visible === false ? ' hidden-layer' : ''}`;
        item.dataset.id = obj.id || index;
        item.dataset.index = index;

        const icon = this.getObjectIcon(obj);
        const name = this.getObjectName(obj);
        const isLocked = obj.lockMovementX && obj.lockMovementY;
        const isHidden = obj.visible === false;

        item.innerHTML = `
            <div class="layer-drag-handle">
                <span class="material-symbols-outlined">drag_indicator</span>
            </div>
            <div class="layer-icon">
                <span class="material-symbols-outlined">${icon}</span>
            </div>
            <div class="layer-name" title="${this.escapeHtml(name)}">${this.escapeHtml(name)}</div>
            <div class="layer-actions">
                <button class="layer-action-mini visibility-toggle${isHidden ? ' off' : ''}" title="Toggle Visibility">
                    <span class="material-symbols-outlined">${isHidden ? 'visibility_off' : 'visibility'}</span>
                </button>
                <button class="layer-action-mini lock-toggle${isLocked ? ' on' : ''}" title="Toggle Lock">
                    <span class="material-symbols-outlined">${isLocked ? 'lock' : 'lock_open'}</span>
                </button>
            </div>
        `;

        // Click to select
        item.addEventListener('click', (e) => {
            if (e.target.closest('.layer-action-mini')) return;
            this.selectObject(obj);
        });

        // Double-click to edit name (for text objects)
        item.addEventListener('dblclick', () => {
            if (obj.type === 'i-text' || obj.type === 'text' || obj.type === 'textbox') {
                this.selectObject(obj);
                obj.enterEditing();
                DesignCanvas.canvas.requestRenderAll();
            }
        });

        // Visibility toggle
        item.querySelector('.visibility-toggle')?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleVisibility(obj);
        });

        // Lock toggle
        item.querySelector('.lock-toggle')?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleLock(obj);
        });

        // Drag and drop for reordering
        item.draggable = true;
        item.addEventListener('dragstart', (e) => this.handleDragStart(e, index));
        item.addEventListener('dragover', (e) => this.handleDragOver(e));
        item.addEventListener('drop', (e) => this.handleDrop(e, index));
        item.addEventListener('dragend', () => this.handleDragEnd());

        return item;
    },

    /**
     * Get icon for object type
     */
    getObjectIcon(obj) {
        const icons = {
            'rect': 'rectangle',
            'circle': 'circle',
            'ellipse': 'circle',
            'triangle': 'change_history',
            'polygon': 'hexagon',
            'line': 'horizontal_rule',
            'path': 'gesture',
            'i-text': 'title',
            'text': 'title',
            'textbox': 'title',
            'image': 'image',
            'group': 'folder',
            'activeSelection': 'select_all'
        };
        return icons[obj.type] || 'shape_line';
    },

    /**
     * Get display name for object
     */
    getObjectName(obj) {
        if (obj.name) return obj.name;

        // For text objects, use the text content
        if (obj.text) {
            const text = obj.text.substring(0, 20);
            return text + (obj.text.length > 20 ? '...' : '');
        }

        // Generate name from type
        const typeNames = {
            'rect': 'Rectangle',
            'circle': 'Circle',
            'ellipse': 'Ellipse',
            'triangle': 'Triangle',
            'polygon': 'Polygon',
            'line': 'Line',
            'path': 'Path',
            'i-text': 'Text',
            'text': 'Text',
            'textbox': 'Textbox',
            'image': 'Image',
            'group': 'Group'
        };

        return typeNames[obj.type] || 'Object';
    },

    /**
     * Get active object IDs
     */
    getActiveObjectIds(activeObject) {
        if (!activeObject) return [];

        if (activeObject.type === 'activeSelection') {
            return activeObject.getObjects().map(obj => obj.id).filter(Boolean);
        }

        return activeObject.id ? [activeObject.id] : [];
    },

    /**
     * Select an object on the canvas
     */
    selectObject(obj) {
        DesignCanvas.canvas.setActiveObject(obj);
        DesignCanvas.canvas.requestRenderAll();
        this.updateSelection();
    },

    /**
     * Update selection state
     */
    updateSelection() {
        const activeObject = DesignCanvas.canvas?.getActiveObject();
        const activeIds = this.getActiveObjectIds(activeObject);

        this.layersList?.querySelectorAll('.layer-item').forEach(item => {
            const id = item.dataset.id;
            item.classList.toggle('selected', activeIds.includes(id));
        });

        this.updateActionButtons();
    },

    /**
     * Update action buttons enabled state
     */
    updateActionButtons() {
        const hasSelection = !!DesignCanvas.canvas?.getActiveObject();

        document.getElementById('btn-delete-layer').disabled = !hasSelection;
        document.getElementById('btn-duplicate-layer').disabled = !hasSelection;
        document.getElementById('btn-lock-layer').disabled = !hasSelection;
        document.getElementById('btn-visibility-layer').disabled = !hasSelection;
    },

    /**
     * Toggle visibility of an object
     */
    toggleVisibility(obj) {
        const newVisibility = obj.visible === false ? true : false;
        obj.set('visible', !newVisibility);
        DesignCanvas.canvas.requestRenderAll();
        this.refresh();
    },

    /**
     * Toggle visibility of selected object
     */
    toggleVisibilitySelected() {
        const activeObject = DesignCanvas.canvas?.getActiveObject();
        if (activeObject) {
            this.toggleVisibility(activeObject);
        }
    },

    /**
     * Toggle lock state of an object
     */
    toggleLock(obj) {
        const isLocked = obj.lockMovementX && obj.lockMovementY;
        const newLocked = !isLocked;

        obj.set({
            lockMovementX: newLocked,
            lockMovementY: newLocked,
            lockRotation: newLocked,
            lockScalingX: newLocked,
            lockScalingY: newLocked,
            hasControls: !newLocked
        });

        DesignCanvas.canvas.requestRenderAll();
        this.refresh();
    },

    /**
     * Toggle lock state of selected object
     */
    toggleLockSelected() {
        const activeObject = DesignCanvas.canvas?.getActiveObject();
        if (activeObject) {
            this.toggleLock(activeObject);
        }
    },

    /**
     * Drag and drop handlers for reordering
     */
    handleDragStart(e, index) {
        e.dataTransfer.setData('text/plain', index.toString());
        e.target.classList.add('dragging');
    },

    handleDragOver(e) {
        e.preventDefault();
        const item = e.target.closest('.layer-item');
        if (item) {
            const items = this.layersList.querySelectorAll('.layer-item');
            items.forEach(i => i.classList.remove('drag-over'));
            item.classList.add('drag-over');
        }
    },

    handleDrop(e, targetIndex) {
        e.preventDefault();
        const sourceIndex = parseInt(e.dataTransfer.getData('text/plain'));

        if (sourceIndex !== targetIndex) {
            this.reorderLayers(sourceIndex, targetIndex);
        }

        this.layersList.querySelectorAll('.layer-item').forEach(i => {
            i.classList.remove('drag-over');
        });
    },

    handleDragEnd() {
        this.layersList?.querySelectorAll('.layer-item').forEach(i => {
            i.classList.remove('dragging', 'drag-over');
        });
    },

    /**
     * Reorder layers
     */
    reorderLayers(sourceIndex, targetIndex) {
        const canvas = DesignCanvas.canvas;
        const objects = canvas.getObjects();
        const obj = objects[sourceIndex];

        if (!obj) return;

        // Calculate new z-index
        // Since our list is reversed, we need to convert indices
        const totalObjects = objects.length;
        const fromZIndex = sourceIndex;
        const toZIndex = targetIndex;

        // Move object to new position
        canvas.moveTo(obj, toZIndex);
        canvas.requestRenderAll();
        DesignCanvas.saveHistory();
        this.refresh();
    },

    /**
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};
