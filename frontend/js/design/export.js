/**
 * Design Export Module
 * Handles exporting designs to various formats with quality options
 */
const DesignExport = {
    currentFormat: 'png',
    modal: null,
    isExporting: false,

    init() {
        this.modal = document.getElementById('modal-export');
        this.setupEventListeners();
        this.enhanceExportModal();
        return this;
    },

    /**
     * Add enhanced export options to modal
     */
    enhanceExportModal() {
        const settingsDiv = document.getElementById('export-settings');
        if (!settingsDiv) return;

        // Replace with enhanced settings
        settingsDiv.innerHTML = `
            <div class="property-row">
                <div class="property-field">
                    <label>Scale</label>
                    <select id="export-scale" class="prop-select">
                        <option value="0.5">0.5x</option>
                        <option value="1">1x</option>
                        <option value="2" selected>2x</option>
                        <option value="3">3x</option>
                        <option value="4">4x</option>
                    </select>
                </div>
                <div class="property-field" id="quality-field">
                    <label>Quality</label>
                    <select id="export-quality" class="prop-select">
                        <option value="0.6">Low (60%)</option>
                        <option value="0.8">Medium (80%)</option>
                        <option value="0.9">High (90%)</option>
                        <option value="1" selected>Max (100%)</option>
                    </select>
                </div>
            </div>
            <div class="property-row" id="transparent-field">
                <div class="property-field full">
                    <label class="checkbox-label">
                        <input type="checkbox" id="export-transparent">
                        <span>Transparent background</span>
                    </label>
                </div>
            </div>
            <div class="export-preview" id="export-preview">
                <div class="preview-info">
                    <span id="export-size-preview">Estimated size: calculating...</span>
                </div>
            </div>
        `;

        // Add JPEG option to export options if not exists
        const options = document.querySelector('.export-options');
        if (options && !options.querySelector('[data-format="jpeg"]')) {
            const jpegOption = document.createElement('button');
            jpegOption.className = 'export-option';
            jpegOption.dataset.format = 'jpeg';
            jpegOption.innerHTML = `
                <span class="material-symbols-outlined">photo</span>
                <div class="export-info">
                    <div class="export-title">JPEG Image</div>
                    <div class="export-desc">Compressed image, smaller file</div>
                </div>
            `;
            jpegOption.addEventListener('click', () => this.selectFormat('jpeg'));

            // Insert after PNG
            const pngOption = options.querySelector('[data-format="png"]');
            if (pngOption && pngOption.nextSibling) {
                options.insertBefore(jpegOption, pngOption.nextSibling);
            }
        }

        // Set up settings change listeners
        this.setupSettingsListeners();
    },

    /**
     * Set up listeners for export settings changes
     */
    setupSettingsListeners() {
        // Scale change updates size preview
        document.getElementById('export-scale')?.addEventListener('change', () => {
            this.updateSizePreview();
            this.updateFileSizeEstimate();
        });

        // Quality change updates file size estimate
        document.getElementById('export-quality')?.addEventListener('change', () => {
            this.updateFileSizeEstimate();
        });

        // Transparency changes file size estimate
        document.getElementById('export-transparent')?.addEventListener('change', () => {
            this.updateFileSizeEstimate();
        });
    },

    /**
     * Update estimated file size
     */
    updateFileSizeEstimate() {
        const preview = document.getElementById('export-size-preview');
        if (!preview) return;

        const scale = parseFloat(document.getElementById('export-scale')?.value || 2);
        const width = Math.round(DesignCanvas.canvasWidth * scale);
        const height = Math.round(DesignCanvas.canvasHeight * scale);

        // Rough estimate based on format and quality
        let estimatedKB;
        if (this.currentFormat === 'jpeg') {
            const quality = parseFloat(document.getElementById('export-quality')?.value || 0.9);
            estimatedKB = Math.round((width * height * 3 * quality) / 1024 / 5);
        } else if (this.currentFormat === 'png') {
            const transparent = document.getElementById('export-transparent')?.checked;
            estimatedKB = Math.round((width * height * (transparent ? 4 : 3)) / 1024 / 3);
        } else {
            estimatedKB = null;
        }

        let sizeText = `Output size: ${width} × ${height} pixels`;
        if (estimatedKB) {
            if (estimatedKB > 1024) {
                sizeText += ` (~${(estimatedKB / 1024).toFixed(1)} MB)`;
            } else {
                sizeText += ` (~${estimatedKB} KB)`;
            }
        }

        preview.textContent = sizeText;
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
        const qualityField = document.getElementById('quality-field');
        const transparentField = document.getElementById('transparent-field');

        if (settingsDiv) {
            // Show settings for image formats
            const isImageFormat = format === 'png' || format === 'jpeg';
            settingsDiv.style.display = isImageFormat ? 'block' : 'none';
        }

        // Quality is only relevant for JPEG
        if (qualityField) {
            qualityField.style.display = format === 'jpeg' ? 'block' : 'none';
        }

        // Transparency only for PNG
        if (transparentField) {
            transparentField.style.display = format === 'png' ? 'flex' : 'none';
        }

        this.updateFileSizeEstimate();
    },

    /**
     * Update the size preview (calls file size estimate for combined info)
     */
    updateSizePreview() {
        this.updateFileSizeEstimate();
    },

    async doExport() {
        if (this.isExporting) return;
        this.isExporting = true;

        const format = this.currentFormat;
        const exportBtn = document.getElementById('btn-do-export');
        const originalText = exportBtn?.innerHTML;

        if (exportBtn) {
            exportBtn.innerHTML = '<span class="material-symbols-outlined spinning">progress_activity</span> Exporting...';
            exportBtn.disabled = true;
        }

        try {
            switch (format) {
                case 'png':
                    await this.exportPNG();
                    break;
                case 'jpeg':
                    await this.exportJPEG();
                    break;
                case 'svg':
                    await this.exportSVG();
                    break;
                case 'json':
                    await this.exportJSON();
                    break;
            }
            this.hideModal();
        } catch (error) {
            console.error('Export failed:', error);
            alert('Export failed. Please try again.');
        } finally {
            this.isExporting = false;
            if (exportBtn) {
                exportBtn.innerHTML = originalText;
                exportBtn.disabled = false;
            }
        }
    },

    async exportPNG() {
        const scale = parseFloat(document.getElementById('export-scale')?.value || 2);
        const transparent = document.getElementById('export-transparent')?.checked || false;

        // Store original background
        const canvas = DesignCanvas.canvas;
        const originalBg = canvas.backgroundColor;

        // Set transparent background if needed
        if (transparent) {
            canvas.backgroundColor = null;
            canvas.requestRenderAll();
        }

        const dataURL = DesignCanvas.toDataURL({
            format: 'png',
            quality: 1,
            multiplier: scale
        });

        // Restore original background
        if (transparent) {
            canvas.backgroundColor = originalBg;
            canvas.requestRenderAll();
        }

        this.downloadFile(dataURL, `design_${Date.now()}.png`);
    },

    async exportJPEG() {
        const scale = parseFloat(document.getElementById('export-scale')?.value || 2);
        const quality = parseFloat(document.getElementById('export-quality')?.value || 0.9);

        // JPEG doesn't support transparency, ensure white background
        const canvas = DesignCanvas.canvas;
        const originalBg = canvas.backgroundColor;

        if (!originalBg || originalBg === 'transparent') {
            canvas.backgroundColor = '#ffffff';
            canvas.requestRenderAll();
        }

        const dataURL = DesignCanvas.toDataURL({
            format: 'jpeg',
            quality: quality,
            multiplier: scale
        });

        // Restore original background
        canvas.backgroundColor = originalBg;
        canvas.requestRenderAll();

        this.downloadFile(dataURL, `design_${Date.now()}.jpg`);
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
