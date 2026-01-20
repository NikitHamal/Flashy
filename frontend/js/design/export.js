const DesignExport = {
    currentFormat: "svg",
    modal: null,

    init() {
        this.modal = document.getElementById("modal-export");
        this.setupEventListeners();
        return this;
    },

    setupEventListeners() {
        document.getElementById("btn-export")?.addEventListener("click", () => this.showModal());
        document.getElementById("btn-close-export")?.addEventListener("click", () => this.hideModal());
        this.modal?.addEventListener("click", (e) => {
            if (e.target === this.modal) this.hideModal();
        });

        document.querySelectorAll(".export-option").forEach((option) => {
            option.addEventListener("click", () => this.selectFormat(option.dataset.format));
        });

        document.getElementById("btn-do-export")?.addEventListener("click", () => this.doExport());
    },

    showModal() {
        this.modal?.classList.remove("hidden");
        this.selectFormat("svg");
    },

    hideModal() {
        this.modal?.classList.add("hidden");
    },

    selectFormat(format) {
        this.currentFormat = format;
        document.querySelectorAll(".export-option").forEach((option) => {
            option.classList.toggle("active", option.dataset.format === format);
        });
    },

    async doExport() {
        switch (this.currentFormat) {
            case "svg":
                return this.exportSVG();
            case "png":
                return this.exportRaster("png");
            case "jpg":
                return this.exportRaster("jpeg");
            case "json":
                return this.exportJSON();
            default:
                return this.exportSVG();
        }
    },

    exportSVG() {
        const svgData = DesignCanvas.getSvgString();
        this.downloadBlob(svgData, "image/svg+xml", `design_${Date.now()}.svg`);
        this.hideModal();
    },

    exportJSON() {
        const jsonStr = JSON.stringify(DesignCanvas.getState(), null, 2);
        this.downloadBlob(jsonStr, "application/json", `design_${Date.now()}.json`);
        this.hideModal();
    },

    async exportRaster(format) {
        const svgData = DesignCanvas.getSvgString();
        const canvas = document.createElement("canvas");
        canvas.width = DesignCanvas.width;
        canvas.height = DesignCanvas.height;
        const ctx = canvas.getContext("2d");

        const img = new Image();
        const svgBlob = new Blob([svgData], { type: "image/svg+xml;charset=utf-8" });
        const url = URL.createObjectURL(svgBlob);
        await new Promise((resolve) => {
            img.onload = () => resolve();
            img.src = url;
        });
        ctx.drawImage(img, 0, 0);
        URL.revokeObjectURL(url);
        const dataUrl = canvas.toDataURL(`image/${format}`, 0.92);
        this.downloadFile(dataUrl, `design_${Date.now()}.${format === "jpeg" ? "jpg" : format}`);
        this.hideModal();
    },

    downloadBlob(content, type, filename) {
        const blob = new Blob([content], { type });
        const url = URL.createObjectURL(blob);
        this.downloadFile(url, filename);
        URL.revokeObjectURL(url);
    },

    downloadFile(url, filename) {
        const link = document.createElement("a");
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
    }
};
