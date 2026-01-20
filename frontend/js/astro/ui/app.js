/**
 * ============================================================================
 * Flashy Jyotish - Main Application Controller
 * ============================================================================
 *
 * Orchestrates all UI modules for the Vedic Astrology Agent interface.
 * Manages initialization, inter-module communication, and global state.
 *
 * @module astro/ui/app
 */

import AstroAPI from './api.js';
import AstroStorage from './storage.js';
import AstroChat from './chat.js';
import AstroKundaliList from './kundali.js';
import AstroChart from './chart.js';
import AstroModals from './modals.js';

class AstroApp {
    constructor() {
        this.initialized = false;
    }

    /**
     * Initialize the application
     */
    async init() {
        if (this.initialized) return;

        console.log('[AstroApp] Initializing Flashy Jyotish...');

        try {
            // Initialize all modules
            await this._initModules();

            // Setup inter-module communication
            this._setupCallbacks();

            // Sync initial state with backend
            await this._syncInitialState();

            // Load initial state
            this._loadInitialState();

            // Setup global event handlers
            this._setupGlobalHandlers();

            this.initialized = true;
            console.log('[AstroApp] Initialization complete');

        } catch (error) {
            console.error('[AstroApp] Initialization failed:', error);
            this._showError('Failed to initialize application. Please refresh the page.');
        }
    }

    /**
     * Initialize all UI modules
     */
    async _initModules() {
        // Initialize modules in order
        AstroChat.init();
        AstroKundaliList.init();
        await AstroChart.init();
        AstroModals.init();

        console.log('[AstroApp] All modules initialized');
    }

    /**
     * Setup callbacks for inter-module communication
     */
    _setupCallbacks() {
        // Chat -> Kundali updates from AI
        AstroChat.onKundaliUpdate = (kundalis) => {
            AstroKundaliList.setKundalis(kundalis);
        };

        // Chat -> Active kundali updates from AI
        AstroChat.onActiveKundaliUpdate = (active) => {
            if (active?.id) {
                const kundali = AstroKundaliList.getKundali(active.id);
                if (kundali) {
                    AstroKundaliList.selectKundali(active.id);
                    AstroChart.displayKundali(kundali);
                }
            }
        };

        // Kundali List -> Chart selection
        AstroKundaliList.onSelect = (kundali) => {
            AstroChart.displayKundali(kundali);
            this._updateTopBar(kundali);
        };

        // Kundali List -> Delete request
        AstroKundaliList.onDelete = (kundali) => {
            AstroModals.openDelete(kundali);
        };

        // Kundali List -> Create request
        AstroKundaliList.onCreate = () => {
            AstroModals.openCreate();
        };

        // Modal -> Kundali created
        AstroModals.onKundaliCreated = (result) => {
            AstroKundaliList.refresh();

            // Select the newly created kundali
            if (result.active_kundali?.id) {
                const kundali = AstroKundaliList.getKundali(result.active_kundali.id);
                if (kundali) {
                    AstroKundaliList.selectKundali(result.active_kundali.id);
                    AstroChart.displayKundali(kundali);
                }
            }
        };

        // Modal -> Kundali deleted
        AstroModals.onKundaliDeleted = (id, result) => {
            AstroKundaliList.refresh();

            // Clear chart if deleted was active
            const activeId = AstroStorage.getActiveKundaliId();
            if (activeId === id || !activeId) {
                AstroChart.clear();
            }
        };

        // Modal -> Export request
        AstroModals.onExport = (format) => {
            this._handleExport(format);
        };

        // Chart -> Planet click
        AstroChart.onPlanetClick = (planet, data) => {
            // Could trigger AI analysis of specific planet
            console.log('[AstroApp] Planet clicked:', planet, data);
        };

        console.log('[AstroApp] Callbacks configured');
    }

    /**
     * Sync initial state with backend
     */
    async _syncInitialState() {
        try {
            const kundalis = AstroStorage.getKundalis();
            if (kundalis.length > 0) {
                await AstroAPI.syncKundalis(kundalis);
                console.log('[AstroApp] Synced', kundalis.length, 'kundalis with backend');
            }
        } catch (error) {
            console.warn('[AstroApp] Failed to sync with backend:', error);
            // Non-fatal - continue with local data
        }
    }

    /**
     * Load initial state from storage
     */
    _loadInitialState() {
        // Load active kundali if set
        const activeId = AstroStorage.getActiveKundaliId();
        if (activeId) {
            const kundali = AstroKundaliList.getKundali(activeId);
            if (kundali) {
                AstroKundaliList.selectKundali(activeId);
                AstroChart.displayKundali(kundali);
            }
        }

        // Set ayanamsa
        const ayanamsa = AstroStorage.getAyanamsa();
        const ayanamsaSelect = document.getElementById('ayanamsa-select');
        if (ayanamsaSelect) {
            ayanamsaSelect.value = ayanamsa;
        }

        console.log('[AstroApp] Initial state loaded');
    }

    /**
     * Setup global event handlers
     */
    _setupGlobalHandlers() {
        // Ayanamsa change
        const ayanamsaSelect = document.getElementById('ayanamsa-select');
        ayanamsaSelect?.addEventListener('change', async (e) => {
            const system = e.target.value;
            AstroStorage.setAyanamsa(system);

            try {
                await AstroAPI.setAyanamsa(system);
            } catch (error) {
                console.warn('[AstroApp] Failed to sync ayanamsa:', error);
            }

            // Recalculate current chart if any
            const activeKundali = AstroChart.getCurrentKundali();
            if (activeKundali) {
                // Clear cached chart data to force recalculation
                activeKundali.chart_data = null;
                AstroChart.displayKundali(activeKundali);
            }
        });

        // Ask Jyotishi button
        const btnAskJyotishi = document.getElementById('btn-ask-jyotishi');
        btnAskJyotishi?.addEventListener('click', () => {
            const chatInput = document.getElementById('jyotishi-input');
            chatInput?.focus();
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K: Focus chat input
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                document.getElementById('jyotishi-input')?.focus();
            }

            // Ctrl/Cmd + N: New kundali
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                e.preventDefault();
                AstroModals.openCreate();
            }
        });

        // Visibility change - refresh on return
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                AstroKundaliList.refresh();
            }
        });

        console.log('[AstroApp] Global handlers configured');
    }

    /**
     * Handle export request
     */
    async _handleExport(format) {
        const kundali = AstroChart.getCurrentKundali();
        if (!kundali) {
            this._showToast('No chart to export', 'warning');
            return;
        }

        const name = kundali.birth_details?.name || 'chart';
        const safeName = name.replace(/[^a-z0-9]/gi, '_').toLowerCase();

        try {
            switch (format) {
                case 'svg':
                    this._exportSvg(safeName);
                    break;

                case 'png':
                    await this._exportPng(safeName);
                    break;

                case 'pdf':
                    this._showToast('PDF export coming soon', 'warning');
                    break;

                case 'json':
                    this._exportJson(safeName, kundali);
                    break;

                default:
                    console.warn('[AstroApp] Unknown export format:', format);
            }
        } catch (error) {
            console.error('[AstroApp] Export failed:', error);
            this._showToast('Export failed: ' + error.message, 'error');
        }
    }

    /**
     * Export chart as SVG
     */
    _exportSvg(name) {
        const svg = AstroChart.exportSvg();
        if (!svg) {
            this._showToast('No chart to export', 'warning');
            return;
        }

        const blob = new Blob([svg], { type: 'image/svg+xml' });
        this._downloadBlob(blob, `${name}_chart.svg`);
        this._showToast('SVG exported', 'success');
    }

    /**
     * Export chart as PNG
     */
    async _exportPng(name) {
        const dataUrl = await AstroChart.exportPng(2);
        if (!dataUrl) {
            this._showToast('No chart to export', 'warning');
            return;
        }

        const link = document.createElement('a');
        link.download = `${name}_chart.png`;
        link.href = dataUrl;
        link.click();
        this._showToast('PNG exported', 'success');
    }

    /**
     * Export kundali as JSON
     */
    _exportJson(name, kundali) {
        const data = JSON.stringify(kundali, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        this._downloadBlob(blob, `${name}_kundali.json`);
        this._showToast('JSON exported', 'success');
    }

    /**
     * Download a blob as file
     */
    _downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        URL.revokeObjectURL(url);
    }

    /**
     * Update top bar with kundali info
     */
    _updateTopBar(kundali) {
        const nameEl = document.getElementById('active-chart-name');
        const infoEl = document.getElementById('active-chart-info');

        if (kundali) {
            const bd = kundali.birth_details || {};
            if (nameEl) nameEl.textContent = bd.name || 'Unknown Chart';
            if (infoEl) infoEl.textContent = `${bd.date || ''} • ${bd.place || ''}`;
        } else {
            if (nameEl) nameEl.textContent = 'Select or Create a Chart';
            if (infoEl) infoEl.textContent = '';
        }
    }

    /**
     * Show toast notification
     */
    _showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const icons = {
            success: 'check_circle',
            error: 'error',
            warning: 'warning'
        };

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <span class="material-symbols-outlined">${icons[type] || 'info'}</span>
            <span class="toast-message">${message}</span>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'toast-in 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    /**
     * Show error message
     */
    _showError(message) {
        const wrapper = document.querySelector('.chart-wrapper');
        if (wrapper) {
            wrapper.innerHTML = `
                <div style="text-align: center; padding: 60px; color: var(--astro-rose);">
                    <span class="material-symbols-outlined" style="font-size: 64px;">error</span>
                    <h2 style="margin-top: 20px; color: var(--astro-text-primary);">Oops!</h2>
                    <p style="margin-top: 12px; color: var(--astro-text-secondary);">${message}</p>
                    <button onclick="location.reload()" style="
                        margin-top: 24px;
                        padding: 12px 24px;
                        background: var(--astro-gold);
                        color: #0a0a0f;
                        border: 2px solid #0a0a0f;
                        font-weight: 600;
                        cursor: pointer;
                    ">
                        Refresh Page
                    </button>
                </div>
            `;
        }
    }

    /**
     * Send a message to the AI programmatically
     */
    sendMessage(message) {
        AstroChat.sendPrompt(message);
    }

    /**
     * Get current session ID
     */
    getSessionId() {
        return AstroAPI.getSessionId();
    }

    /**
     * Reset the application state
     */
    async reset() {
        try {
            AstroStorage.clear();
            AstroAPI.resetSession();
            AstroChart.clear();
            AstroKundaliList.refresh();
            this._showToast('Application reset', 'success');
        } catch (error) {
            console.error('[AstroApp] Reset failed:', error);
        }
    }
}

// Create and export singleton instance
const app = new AstroApp();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => app.init());
} else {
    app.init();
}

// Expose to window for debugging
window.AstroApp = app;

export default app;
