/**
 * Design Export Module
 * Handles exporting designs to various formats
 */
const DesignExport = {
    currentFormat: 'png',
    modal: null,

    init() {
        this.modal = document.getElementById('modal-export');
        this.setupEventListeners();
        return this;
    },

    setupEventListeners() {
        document.getElementById('btn-export')?.addEventListener('click', () => {
            this.showModal();
        });

        document.getElementById('btn-close-export')?.addEventListener('click', () => {
            this.hideModal();
        });

        this.modal?.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.hideModal();
            }
        });

        document.querySelectorAll('.export-option').forEach(option => {
            option.addEventListener('click', () => {
                this.selectFormat(option.dataset.format);
            });
        });

        document.getElementById('btn-do-export')?.addEventListener('click', () => {
            this.doExport();
        });

        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                this.quickExport('png');
            }
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 's') {
                e.preventDefault();
                this.showModal();
            }
        });
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
        const format = this.currentFormat;

        switch (format) {
            case 'png':
                await this.exportPNG();
                break;
            case 'jpg':
                await this.exportJPG();
                break;
            case 'webp':
                await this.exportWebP();
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

    async exportPNG() {
        const scale = parseFloat(document.getElementById('export-scale')?.value || 2);

        const dataURL = DesignCanvas.toDataURL({
            format: 'png',
            quality: 1,
            multiplier: scale
        });

        this.downloadFile(dataURL, `design_${Date.now()}.png`);
    },

    async exportJPG() {
        const scale = parseFloat(document.getElementById('export-scale')?.value || 2);
        const quality = parseFloat(document.getElementById('export-quality')?.value || 0.8);

        const dataURL = DesignCanvas.toDataURL({
            format: 'jpeg',
            quality: quality,
            multiplier: scale
        });

        this.downloadFile(dataURL, `design_${Date.now()}.jpg`);
    },

    async exportWebP() {
        const scale = parseFloat(document.getElementById('export-scale')?.value || 2);
        const quality = parseFloat(document.getElementById('export-quality')?.value || 0.8);

        const dataURL = DesignCanvas.toDataURL({
            format: 'webp',
            quality: quality,
            multiplier: scale
        });

        this.downloadFile(dataURL, `design_${Date.now()}.webp`);
    },

    async exportSVG() {
        const svgData = DesignCanvas.toSVG();
        const blob = new Blob([svgData], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);

        this.downloadFile(url, `design_${Date.now()}.svg`);
        URL.revokeObjectURL(url);
    },

    async exportJSON() {
        const json = DesignCanvas.toJSON();
        const jsonStr = JSON.stringify(json, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        this.downloadFile(url, `design_${Date.now()}.json`);
        URL.revokeObjectURL(url);
    },

    quickExport(format) {
        switch (format) {
            case 'png':
                this.exportPNG();
                break;
            case 'jpg':
                this.exportJPG();
                break;
            case 'webp':
                this.exportWebP();
                break;
            case 'svg':
                this.exportSVG();
                break;
            case 'json':
                this.exportJSON();
                break;
        }
    },

    downloadFile(url, filename) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },

    async importJSON() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';

        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = async (event) => {
                try {
                    const json = JSON.parse(event.target.result);
                    await DesignCanvas.loadFromJSON(json);
                } catch (error) {
                    console.error('Error importing JSON:', error);
                    alert('Failed to import design. Invalid file format.');
                }
            };
            reader.readAsText(file);
        };

        input.click();
    },

    async serverExportPNG() {
        const scale = parseFloat(document.getElementById('export-scale')?.value || 2);
        const dataURL = DesignCanvas.toDataURL({
            format: 'png',
            multiplier: scale
        });

        try {
            const response = await fetch('/design/export/png', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: DesignApp.sessionId,
                    canvas_data: dataURL,
                    width: DesignCanvas.canvasWidth,
                    height: DesignCanvas.canvasHeight,
                    scale: scale
                })
            });

            if (!response.ok) throw new Error('Export failed');

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            this.downloadFile(url, `design_${Date.now()}.png`);
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Server export failed:', error);
            this.exportPNG();
        }
    },

    async serverExportSVG() {
        const svgData = DesignCanvas.toSVG();

        try {
            const response = await fetch('/design/export/svg', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: DesignApp.sessionId,
                    svg_data: svgData
                })
            });

            if (!response.ok) throw new Error('Export failed');

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            this.downloadFile(url, `design_${Date.now()}.svg`);
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Server export failed:', error);
            this.exportSVG();
        }
    }
};
