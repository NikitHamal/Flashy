const DesignTools = {
    currentTool: "select",

    init() {
        this.setupToolButtons();
        this.setupQuickActions();
        return this;
    },

    setupToolButtons() {
        document.querySelectorAll(".tool-btn").forEach((btn) => {
            btn.addEventListener("click", () => {
                const tool = btn.dataset.tool;
                if (tool) this.setTool(tool);
            });
        });
    },

    setTool(toolName) {
        this.currentTool = toolName;
        if (toolName === "image") {
            this.triggerImageUpload();
            return;
        }
        this.insertElementForTool(toolName);
    },

    insertElementForTool(tool) {
        const defaults = {
            fill: "#ffb000",
            stroke: "#14120e",
            "stroke-width": "3"
        };

        switch (tool) {
            case "rectangle":
                DesignCanvas.addElement("rect", {
                    x: 200,
                    y: 140,
                    width: 240,
                    height: 140,
                    rx: 12,
                    fill: defaults.fill,
                    stroke: defaults.stroke,
                    "stroke-width": defaults["stroke-width"]
                });
                break;
            case "circle":
                DesignCanvas.addElement("circle", {
                    cx: 360,
                    cy: 280,
                    r: 80,
                    fill: "#b8f2c2",
                    stroke: defaults.stroke,
                    "stroke-width": defaults["stroke-width"]
                });
                break;
            case "triangle":
                DesignCanvas.addElement("polygon", {
                    points: "360,160 260,340 460,340",
                    fill: "#fff1d6",
                    stroke: defaults.stroke,
                    "stroke-width": defaults["stroke-width"]
                });
                break;
            case "line":
                DesignCanvas.addElement("line", {
                    x1: 200,
                    y1: 120,
                    x2: 480,
                    y2: 120,
                    stroke: defaults.stroke,
                    "stroke-width": "4"
                });
                break;
            case "text":
                DesignCanvas.addElement("text", {
                    x: 240,
                    y: 220,
                    fill: "#14120e",
                    "font-family": "Space Grotesk, sans-serif",
                    "font-size": "28",
                    "font-weight": "700"
                }, "Edit me");
                break;
            case "polygon":
                DesignCanvas.addElement("polygon", {
                    points: "260,200 320,140 400,160 420,240 340,320 260,280",
                    fill: "#ffe066",
                    stroke: defaults.stroke,
                    "stroke-width": defaults["stroke-width"]
                });
                break;
            case "star":
                DesignCanvas.addElement("polygon", {
                    points: "360,120 380,180 440,180 392,216 410,276 360,238 310,276 328,216 280,180 340,180",
                    fill: "#ffd1dc",
                    stroke: defaults.stroke,
                    "stroke-width": defaults["stroke-width"]
                });
                break;
            default:
                break;
        }
    },

    setupQuickActions() {
        document.getElementById("btn-undo")?.addEventListener("click", () => DesignCanvas.undo());
        document.getElementById("btn-redo")?.addEventListener("click", () => DesignCanvas.redo());
        document.getElementById("btn-delete")?.addEventListener("click", () => DesignCanvas.deleteSelection());
        document.getElementById("btn-duplicate")?.addEventListener("click", () => DesignCanvas.duplicateSelection());
    },

    triggerImageUpload() {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = "image/*";
        input.addEventListener("change", (event) => {
            const file = event.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (e) => {
                DesignCanvas.addElement("image", {
                    href: e.target.result,
                    x: 200,
                    y: 160,
                    width: 240,
                    height: 180,
                    preserveAspectRatio: "xMidYMid slice"
                });
            };
            reader.readAsDataURL(file);
        });
        input.click();
    }
};
