const DesignExport = {
    currentFormat: 'png',
    modal: null,

    init() {
        this.modal = document.getElementById('modal-export');
        this.setupEventListeners();
        return this;
    },

    setupEventListeners() {
        document.getElementById('btn-export')?.addEventListener('click', () => this.showModal());
        document.getElementById('btn-close-export')?.addEventListener('click', () => this.hideModal());
        document.querySelectorAll('.export-option').forEach(option => {
            option.addEventListener('click', () => this.selectFormat(option.dataset.format));
        });
        document.getElementById('btn-do-export')?.addEventListener('click', () => this.doExport());
    },

    showModal() {
        this.modal?.classList.remove('hidden');
        this.selectFormat('png');
    },

    hideModal() {
        this.modal?.classList.add('hidden');
    },

    selectFormat(format) {
        this.currentFormat = format;
        document.querySelectorAll('.export-option').forEach(option => {
            option.classList.toggle('active', option.dataset.format === format);
        });
        const settingsDiv = document.getElementById('export-settings');
        if (settingsDiv) {
            settingsDiv.style.display = ['png', 'jpg', 'webp'].includes(format) ? 'block' : 'none';
            const qualityField = document.getElementById('export-quality')?.closest('.property-field');
            if (qualityField) {
                qualityField.style.display = format === 'png' ? 'none' : 'block';
            }
        }
    },

    async doExport() {
        switch (this.currentFormat) {
            case 'png':
                await this.exportRaster('image/png');
                break;
            case 'jpg':
                await this.exportRaster('image/jpeg');
                break;
            case 'webp':
                await this.exportRaster('image/webp');
                break;
            case 'svg':
                await this.exportSVG();
                break;
            case 'json':
                await this.exportJSON();
                break;
        }
        this.hideModal();
    },

    async exportRaster(type) {
        const scale = parseFloat(document.getElementById('export-scale')?.value || 2);
        const quality = parseFloat(document.getElementById('export-quality')?.value || 0.9);
        const { svg, width, height } = DesignCanvas.getState();

        const svgBlob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' });
        const url = URL.createObjectURL(svgBlob);
        const img = new Image();

        img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = width * scale;
            canvas.height = height * scale;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = DesignCanvas.background;
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            const dataUrl = canvas.toDataURL(type, quality);
            this.downloadFile(dataUrl, `design_${Date.now()}.${type.split('/')[1]}`);
            URL.revokeObjectURL(url);
        };
        img.src = url;
    },

    async exportSVG() {
        const svg = DesignCanvas.getState().svg;
        this.downloadBlob(svg, 'image/svg+xml', `design_${Date.now()}.svg`);
    },

    async exportJSON() {
        const state = DesignCanvas.getState();
        this.downloadBlob(JSON.stringify(state, null, 2), 'application/json', `design_${Date.now()}.json`);
    },

    downloadFile(dataUrl, filename) {
        const link = document.createElement('a');
        link.href = dataUrl;
        link.download = filename;
        link.click();
    },

    downloadBlob(content, type, filename) {
        const blob = new Blob([content], { type });
        const url = URL.createObjectURL(blob);
        this.downloadFile(url, filename);
        URL.revokeObjectURL(url);
    }
};
