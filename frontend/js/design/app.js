/**
 * Design App Module (SVG-based)
 * Main application controller for Flashy Designs
 */
const DesignApp = {
    projectName: 'Untitled Design',

    async init() {
        // Initialize all modules
        DesignCanvas.init();
        DesignTools.init();
        DesignProperties.init();
        DesignChat.init();
        DesignExport.init();

        this.setupProjectName();
        this.setupKeyboardShortcuts();

        // Center the canvas
        DesignCanvas.zoomToFit();

        console.log('[DesignApp] Initialized with session:', DesignCanvas.sessionId);
    },

    get sessionId() {
        return DesignCanvas.sessionId;
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
            // Skip if in input/textarea
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                if (e.key === 'Escape') {
                    e.target.blur();
                }
                return;
            }

            // Export modal
            if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
                e.preventDefault();
                DesignExport.showModal();
            }

            // Import
            if ((e.ctrlKey || e.metaKey) && e.key === 'i') {
                e.preventDefault();
                DesignExport.importJSON();
            }

            // Reset zoom
            if ((e.ctrlKey || e.metaKey) && e.key === '0') {
                e.preventDefault();
                DesignCanvas.setZoom(1);
            }

            // Zoom in
            if ((e.ctrlKey || e.metaKey) && (e.key === '=' || e.key === '+')) {
                e.preventDefault();
                DesignCanvas.zoomIn();
            }

            // Zoom out
            if ((e.ctrlKey || e.metaKey) && e.key === '-') {
                e.preventDefault();
                DesignCanvas.zoomOut();
            }

            // Quick zoom shortcuts
            if (!e.ctrlKey && !e.metaKey && !e.altKey) {
                if (e.key === '1') {
                    DesignCanvas.setZoom(1);
                }
                if (e.key === '2') {
                    DesignCanvas.zoomToFit();
                }
            }

            // Layer shortcuts
            if (e.key === '[' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                DesignCanvas.sendBackward();
            }

            if (e.key === ']' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                DesignCanvas.bringForward();
            }

            if (e.key === '[' && (e.ctrlKey || e.metaKey) && e.shiftKey) {
                e.preventDefault();
                DesignCanvas.sendToBack();
            }

            if (e.key === ']' && (e.ctrlKey || e.metaKey) && e.shiftKey) {
                e.preventDefault();
                DesignCanvas.bringToFront();
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
                    session_id: DesignCanvas.sessionId,
                    state: state
                })
            });
        } catch (error) {
            console.error('Failed to save state:', error);
        }
    },

    async loadFromServer() {
        try {
            const response = await fetch(`/design/canvas/${DesignCanvas.sessionId}`);
            if (response.ok) {
                const state = await response.json();
                if (state) {
                    DesignCanvas.setState(state);
                }
            }
        } catch (error) {
            console.error('Failed to load state:', error);
        }
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    DesignApp.init();
});
