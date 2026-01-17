/**
 * Design App Module
 * Main application controller for Flashy Designs
 */
const DesignApp = {
    sessionId: null,
    projectName: 'Untitled Design',

    async init() {
        this.sessionId = this.generateSessionId();

        DesignCanvas.init();
        DesignTools.init();
        DesignProperties.init();
        DesignChat.init();
        DesignExport.init();

        this.setupProjectName();
        this.setupKeyboardShortcuts();

        DesignCanvas.zoomToFit();

        console.log('[DesignApp] Initialized with session:', this.sessionId);
    },

    generateSessionId() {
        return 'design_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    },

    setupProjectName() {
        const nameElement = document.getElementById('project-name');
        const renameBtn = document.getElementById('btn-rename');

        renameBtn?.addEventListener('click', () => {
            const newName = prompt('Enter project name:', this.projectName);
            if (newName && newName.trim()) {
                this.projectName = newName.trim();
                if (nameElement) {
                    nameElement.textContent = this.projectName;
                }
                document.title = `${this.projectName} | Flashy Designs`;
            }
        });
    },

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                if (e.key === 'Escape') {
                    e.target.blur();
                }
                return;
            }

            if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
                e.preventDefault();
                DesignExport.showModal();
            }

            if ((e.ctrlKey || e.metaKey) && e.key === 'i') {
                e.preventDefault();
                DesignExport.importJSON();
            }

            if ((e.ctrlKey || e.metaKey) && e.key === '0') {
                e.preventDefault();
                DesignCanvas.setZoom(1);
            }

            if ((e.ctrlKey || e.metaKey) && (e.key === '=' || e.key === '+')) {
                e.preventDefault();
                DesignCanvas.zoomIn();
            }

            if ((e.ctrlKey || e.metaKey) && e.key === '-') {
                e.preventDefault();
                DesignCanvas.zoomOut();
            }

            if (e.key === '1') {
                DesignCanvas.setZoom(1);
            }

            if (e.key === '2') {
                DesignCanvas.zoomToFit();
            }

            if (e.key === 'g' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                const activeObject = DesignCanvas.canvas.getActiveObject();
                if (activeObject && activeObject.type === 'activeSelection') {
                    const objects = activeObject.getObjects();
                    const ids = objects.map(obj => obj.id).filter(Boolean);
                    if (ids.length > 1) {
                        DesignTools.groupObjects(ids);
                    }
                }
            }

            if (e.key === 'g' && (e.ctrlKey || e.metaKey) && e.shiftKey) {
                e.preventDefault();
                const activeObject = DesignCanvas.canvas.getActiveObject();
                if (activeObject && activeObject.type === 'group' && activeObject.id) {
                    DesignTools.ungroupObjects(activeObject.id);
                }
            }
        });
    },

    async saveToServer() {
        const state = DesignCanvas.getState();

        try {
            await fetch('/design/canvas', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    state: state
                })
            });
        } catch (error) {
            console.error('Failed to save state:', error);
        }
    },

    async loadFromServer() {
        try {
            const response = await fetch(`/design/canvas/${this.sessionId}`);
            if (response.ok) {
                const state = await response.json();
                if (state && state.objects) {
                    await DesignCanvas.loadFromJSON(state);
                }
            }
        } catch (error) {
            console.error('Failed to load state:', error);
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    DesignApp.init();
});
