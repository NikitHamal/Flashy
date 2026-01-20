/**
 * Design Export Module (SVG-based)
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
        
        try {
            const dataURL = await this.renderToCanvas('png', scale);
            this.downloadFile(dataURL, `design_${Date.now()}.png`);
        } catch (error) {
            console.error('PNG export failed:', error);
            alert('Failed to export PNG. Please try again.');
        }
    },

    async exportJPG() {
        const scale = parseFloat(document.getElementById('export-scale')?.value || 2);
        const quality = parseFloat(document.getElementById('export-quality')?.value || 0.9);
        
        try {
            const dataURL = await this.renderToCanvas('jpeg', scale, quality);
            this.downloadFile(dataURL, `design_${Date.now()}.jpg`);
        } catch (error) {
            console.error('JPG export failed:', error);
            alert('Failed to export JPG. Please try again.');
        }
    },

    async exportWebP() {
        const scale = parseFloat(document.getElementById('export-scale')?.value || 2);
        const quality = parseFloat(document.getElementById('export-quality')?.value || 0.9);
        
        try {
            const dataURL = await this.renderToCanvas('webp', scale, quality);
            this.downloadFile(dataURL, `design_${Date.now()}.webp`);
        } catch (error) {
            console.error('WebP export failed:', error);
            alert('Failed to export WebP. Please try again.');
        }
    },

    async exportSVG() {
        const svgData = DesignCanvas.getSVG();
        const blob = new Blob([svgData], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);

        this.downloadFile(url, `design_${Date.now()}.svg`);
        URL.revokeObjectURL(url);
    },

    async exportJSON() {
        const state = DesignCanvas.getState();
        const jsonStr = JSON.stringify(state, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        this.downloadFile(url, `design_${Date.now()}.json`);
        URL.revokeObjectURL(url);
    },

    /**
     * Render SVG to canvas and return data URL
     */
    async renderToCanvas(format, scale = 2, quality = 0.9) {
        return new Promise((resolve, reject) => {
            const svgElement = document.getElementById('design-svg');
            if (!svgElement) {
                reject(new Error('SVG element not found'));
                return;
            }

            const width = DesignCanvas.width;
            const height = DesignCanvas.height;
            const background = DesignCanvas.background;

            // Create canvas
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = width * scale;
            canvas.height = height * scale;

            // Draw background
            ctx.fillStyle = background;
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Clone and prepare SVG
            const svgClone = svgElement.cloneNode(true);
            svgClone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
            svgClone.setAttribute('width', width);
            svgClone.setAttribute('height', height);
            
            // Remove selection classes
            svgClone.querySelectorAll('.selected').forEach(el => {
                el.classList.remove('selected');
            });

            // Serialize SVG
            const svgData = new XMLSerializer().serializeToString(svgClone);
            const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
            const url = URL.createObjectURL(svgBlob);

            // Draw to canvas
            const img = new Image();
            img.onload = () => {
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                URL.revokeObjectURL(url);

                const mimeType = format === 'jpeg' ? 'image/jpeg' : 
                                format === 'webp' ? 'image/webp' : 'image/png';
                resolve(canvas.toDataURL(mimeType, quality));
            };
            img.onerror = () => {
                URL.revokeObjectURL(url);
                reject(new Error('Failed to load SVG image'));
            };
            img.src = url;
        });
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
                    const state = JSON.parse(event.target.result);
                    DesignCanvas.setState(state);
                } catch (error) {
                    console.error('Error importing JSON:', error);
                    alert('Failed to import design. Invalid file format.');
                }
            };
            reader.readAsText(file);
        };

        input.click();
    },

    async importSVG() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.svg';

        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = async (event) => {
                try {
                    const svgContent = event.target.result;
                    DesignCanvas.updateSVG(svgContent);
                } catch (error) {
                    console.error('Error importing SVG:', error);
                    alert('Failed to import SVG. Invalid file format.');
                }
            };
            reader.readAsText(file);
        };

        input.click();
    },

    async serverExportPNG() {
        const scale = parseFloat(document.getElementById('export-scale')?.value || 2);
        
        try {
            const dataURL = await this.renderToCanvas('png', scale);

            const response = await fetch('/design/export/png', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: DesignCanvas.sessionId,
                    canvas_data: dataURL,
                    width: DesignCanvas.width,
                    height: DesignCanvas.height,
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
        const svgData = DesignCanvas.getSVG();

        try {
            const response = await fetch('/design/export/svg', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: DesignCanvas.sessionId,
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
