const DesignApp = {
    sessionId: null,
    projectName: 'Untitled Design',

    init() {
        this.sessionId = this.generateSessionId();
        DesignCanvas.init();
        DesignTools.init();
        DesignProperties.init();
        DesignChat.init();
        DesignExport.init();
        this.setupProjectName();
        DesignCanvas.zoomToFit();
    },

    generateSessionId() {
        return `design_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    },

    setupProjectName() {
        const nameElement = document.getElementById('project-name');
        const renameBtn = document.getElementById('btn-rename');

        renameBtn?.addEventListener('click', () => {
            const newName = prompt('Enter project name:', this.projectName);
            if (newName && newName.trim()) {
                this.projectName = newName.trim();
                nameElement.textContent = this.projectName;
                document.title = `${this.projectName} | Flashy Designs`;
            }
        });
    }
};

document.addEventListener('DOMContentLoaded', () => {
    DesignApp.init();
});
