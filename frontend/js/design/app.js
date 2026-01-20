/**
 * Design App Module (SVG)
 */
const DesignApp = {
    sessionId: null,
    projectName: "Untitled Design",

    async init() {
        this.sessionId = this.generateSessionId();
        DesignCanvas.init();
        DesignTools.init();
        DesignProperties.init();
        DesignChat.init();
        DesignExport.init();
        this.setupProjectName();
        this.setupKeyboardShortcuts();
        this.setupPanels();
        console.log("[DesignApp] Initialized", this.sessionId);
    },

    generateSessionId() {
        return `design_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
    },

    setupProjectName() {
        const nameElement = document.getElementById("project-name");
        const renameBtn = document.getElementById("btn-rename");
        renameBtn?.addEventListener("click", () => {
            const newName = prompt("Enter project name:", this.projectName);
            if (newName && newName.trim()) {
                this.projectName = newName.trim();
                nameElement.textContent = this.projectName;
                document.title = `${this.projectName} | Flashy Designs`;
            }
        });
    },

    setupKeyboardShortcuts() {
        document.addEventListener("keydown", (e) => {
            if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
                e.preventDefault();
                DesignCanvas.undo();
            }
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "y") {
                e.preventDefault();
                DesignCanvas.redo();
            }
            if (e.key === "Delete") {
                DesignCanvas.deleteSelection();
            }
        });
    },
    setupPanels() {
        const chatPanel = document.getElementById("chat-panel");
        const propertiesPanel = document.getElementById("properties-panel");
        document.getElementById("btn-toggle-chat")?.addEventListener("click", () => {
            chatPanel?.classList.toggle("active");
            propertiesPanel?.classList.remove("active");
        });
        document.getElementById("btn-toggle-properties")?.addEventListener("click", () => {
            propertiesPanel?.classList.toggle("active");
            chatPanel?.classList.remove("active");
        });

        document.querySelectorAll(".sidebar-tab").forEach((tab) => {
            tab.addEventListener("click", () => {
                const target = tab.dataset.tab;
                document.querySelectorAll(".sidebar-tab").forEach((t) => t.classList.remove("active"));
                tab.classList.add("active");
                if (target === "chat") {
                    chatPanel?.classList.add("active");
                    propertiesPanel?.classList.remove("active");
                } else {
                    propertiesPanel?.classList.add("active");
                    chatPanel?.classList.remove("active");
                }
            });
        });
    }
};

document.addEventListener("DOMContentLoaded", () => {
    DesignApp.init();
});
