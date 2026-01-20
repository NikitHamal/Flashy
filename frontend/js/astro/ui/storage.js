/**
 * ============================================================================
 * Astro Storage Module
 * ============================================================================
 *
 * Manages localStorage persistence for kundalis and app settings.
 * Provides CRUD operations with automatic save/load.
 *
 * @module astro/ui/storage
 */

const STORAGE_KEYS = {
    KUNDALIS: 'flashy_jyotish_kundalis',
    ACTIVE_KUNDALI: 'flashy_jyotish_active',
    AYANAMSA: 'flashy_jyotish_ayanamsa',
    CHART_STYLE: 'flashy_jyotish_chart_style',
    SETTINGS: 'flashy_jyotish_settings'
};

class AstroStorage {
    constructor() {
        this._cache = {
            kundalis: null,
            settings: null
        };
    }

    /**
     * Get all stored kundalis
     * @returns {Array} Array of kundali objects
     */
    getKundalis() {
        if (this._cache.kundalis !== null) {
            return this._cache.kundalis;
        }

        try {
            const data = localStorage.getItem(STORAGE_KEYS.KUNDALIS);
            this._cache.kundalis = data ? JSON.parse(data) : [];
            return this._cache.kundalis;
        } catch (error) {
            console.error('[AstroStorage] Failed to load kundalis:', error);
            return [];
        }
    }

    /**
     * Save all kundalis to localStorage
     * @param {Array} kundalis - Array of kundali objects
     */
    saveKundalis(kundalis) {
        try {
            localStorage.setItem(STORAGE_KEYS.KUNDALIS, JSON.stringify(kundalis));
            this._cache.kundalis = kundalis;
        } catch (error) {
            console.error('[AstroStorage] Failed to save kundalis:', error);
            // Try to clear some space if quota exceeded
            if (error.name === 'QuotaExceededError') {
                this._handleQuotaExceeded();
            }
        }
    }

    /**
     * Get a single kundali by ID
     * @param {string} id - Kundali ID
     * @returns {Object|null} Kundali object or null
     */
    getKundali(id) {
        const kundalis = this.getKundalis();
        return kundalis.find(k => k.id === id) || null;
    }

    /**
     * Add a new kundali
     * @param {Object} kundali - Kundali object with birth_details and optional chart_data
     * @returns {Object} The added kundali with generated ID
     */
    addKundali(kundali) {
        const kundalis = this.getKundalis();

        // Generate ID if not provided
        if (!kundali.id) {
            kundali.id = this._generateKundaliId();
        }

        // Add timestamps
        kundali.created_at = kundali.created_at || new Date().toISOString();
        kundali.updated_at = new Date().toISOString();

        kundalis.unshift(kundali); // Add to beginning (most recent first)
        this.saveKundalis(kundalis);

        return kundali;
    }

    /**
     * Update an existing kundali
     * @param {string} id - Kundali ID
     * @param {Object} updates - Fields to update
     * @returns {Object|null} Updated kundali or null if not found
     */
    updateKundali(id, updates) {
        const kundalis = this.getKundalis();
        const index = kundalis.findIndex(k => k.id === id);

        if (index === -1) {
            console.warn('[AstroStorage] Kundali not found:', id);
            return null;
        }

        // Merge updates
        kundalis[index] = {
            ...kundalis[index],
            ...updates,
            updated_at: new Date().toISOString()
        };

        this.saveKundalis(kundalis);
        return kundalis[index];
    }

    /**
     * Update chart data for a kundali
     * @param {string} id - Kundali ID
     * @param {Object} chartData - Calculated chart data
     * @returns {Object|null} Updated kundali or null
     */
    updateChartData(id, chartData) {
        return this.updateKundali(id, { chart_data: chartData });
    }

    /**
     * Delete a kundali
     * @param {string} id - Kundali ID
     * @returns {boolean} True if deleted, false if not found
     */
    deleteKundali(id) {
        const kundalis = this.getKundalis();
        const filteredKundalis = kundalis.filter(k => k.id !== id);

        if (filteredKundalis.length === kundalis.length) {
            return false; // Not found
        }

        this.saveKundalis(filteredKundalis);

        // Clear active if deleted
        if (this.getActiveKundaliId() === id) {
            this.clearActiveKundali();
        }

        return true;
    }

    /**
     * Search kundalis by name or tags
     * @param {string} query - Search query
     * @returns {Array} Matching kundalis
     */
    searchKundalis(query) {
        if (!query || !query.trim()) {
            return this.getKundalis();
        }

        const lowerQuery = query.toLowerCase().trim();
        const kundalis = this.getKundalis();

        return kundalis.filter(k => {
            const name = (k.birth_details?.name || '').toLowerCase();
            const place = (k.birth_details?.place || '').toLowerCase();
            const tags = (k.tags || []).map(t => t.toLowerCase());

            return name.includes(lowerQuery) ||
                   place.includes(lowerQuery) ||
                   tags.some(t => t.includes(lowerQuery));
        });
    }

    /**
     * Get count of stored kundalis
     * @returns {number}
     */
    getKundaliCount() {
        return this.getKundalis().length;
    }

    // =========================================================================
    // Active Kundali Management
    // =========================================================================

    /**
     * Get active kundali ID
     * @returns {string|null}
     */
    getActiveKundaliId() {
        return localStorage.getItem(STORAGE_KEYS.ACTIVE_KUNDALI) || null;
    }

    /**
     * Set active kundali ID
     * @param {string} id - Kundali ID
     */
    setActiveKundaliId(id) {
        if (id) {
            localStorage.setItem(STORAGE_KEYS.ACTIVE_KUNDALI, id);
        } else {
            this.clearActiveKundali();
        }
    }

    /**
     * Clear active kundali
     */
    clearActiveKundali() {
        localStorage.removeItem(STORAGE_KEYS.ACTIVE_KUNDALI);
    }

    /**
     * Get active kundali object
     * @returns {Object|null}
     */
    getActiveKundali() {
        const id = this.getActiveKundaliId();
        return id ? this.getKundali(id) : null;
    }

    // =========================================================================
    // Settings Management
    // =========================================================================

    /**
     * Get ayanamsa system
     * @returns {string}
     */
    getAyanamsa() {
        return localStorage.getItem(STORAGE_KEYS.AYANAMSA) || 'Lahiri';
    }

    /**
     * Set ayanamsa system
     * @param {string} system - Ayanamsa system name
     */
    setAyanamsa(system) {
        localStorage.setItem(STORAGE_KEYS.AYANAMSA, system);
    }

    /**
     * Get chart style preference
     * @returns {string} 'north' or 'south'
     */
    getChartStyle() {
        return localStorage.getItem(STORAGE_KEYS.CHART_STYLE) || 'north';
    }

    /**
     * Set chart style preference
     * @param {string} style - 'north' or 'south'
     */
    setChartStyle(style) {
        localStorage.setItem(STORAGE_KEYS.CHART_STYLE, style);
    }

    /**
     * Get all settings
     * @returns {Object}
     */
    getSettings() {
        if (this._cache.settings !== null) {
            return this._cache.settings;
        }

        try {
            const data = localStorage.getItem(STORAGE_KEYS.SETTINGS);
            this._cache.settings = data ? JSON.parse(data) : this._getDefaultSettings();
            return this._cache.settings;
        } catch (error) {
            return this._getDefaultSettings();
        }
    }

    /**
     * Update settings
     * @param {Object} updates - Settings to update
     */
    updateSettings(updates) {
        const settings = { ...this.getSettings(), ...updates };
        try {
            localStorage.setItem(STORAGE_KEYS.SETTINGS, JSON.stringify(settings));
            this._cache.settings = settings;
        } catch (error) {
            console.error('[AstroStorage] Failed to save settings:', error);
        }
    }

    _getDefaultSettings() {
        return {
            ayanamsa: 'Lahiri',
            chartStyle: 'north',
            showDegrees: false,
            showRetrograde: true,
            showDignities: true,
            chatFontSize: 'medium',
            thinkingVisible: false
        };
    }

    // =========================================================================
    // Utility Methods
    // =========================================================================

    /**
     * Generate unique kundali ID
     * @returns {string}
     */
    _generateKundaliId() {
        return 'kund_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Handle storage quota exceeded
     * Tries to remove oldest kundalis without chart data
     */
    _handleQuotaExceeded() {
        console.warn('[AstroStorage] Storage quota exceeded, attempting cleanup...');

        const kundalis = this.getKundalis();

        // Sort by created_at ascending (oldest first)
        const sorted = [...kundalis].sort((a, b) =>
            new Date(a.created_at || 0) - new Date(b.created_at || 0)
        );

        // Try to remove oldest kundalis until we have space
        // Keep at least 10 kundalis
        while (sorted.length > 10) {
            sorted.shift();
            try {
                localStorage.setItem(STORAGE_KEYS.KUNDALIS, JSON.stringify(sorted));
                this._cache.kundalis = sorted;
                console.log('[AstroStorage] Removed old kundali to free space');
                return;
            } catch (e) {
                // Keep trying
            }
        }

        // If still failing, clear all chart_data
        sorted.forEach(k => delete k.chart_data);
        try {
            localStorage.setItem(STORAGE_KEYS.KUNDALIS, JSON.stringify(sorted));
            this._cache.kundalis = sorted;
        } catch (e) {
            console.error('[AstroStorage] Failed to free storage space');
        }
    }

    /**
     * Export all data for backup
     * @returns {Object}
     */
    exportAll() {
        return {
            kundalis: this.getKundalis(),
            activeKundaliId: this.getActiveKundaliId(),
            settings: this.getSettings(),
            exportedAt: new Date().toISOString()
        };
    }

    /**
     * Import data from backup
     * @param {Object} data - Exported data object
     */
    importAll(data) {
        if (data.kundalis && Array.isArray(data.kundalis)) {
            this.saveKundalis(data.kundalis);
        }

        if (data.activeKundaliId) {
            this.setActiveKundaliId(data.activeKundaliId);
        }

        if (data.settings) {
            this.updateSettings(data.settings);
        }
    }

    /**
     * Clear all stored data
     */
    clearAll() {
        Object.values(STORAGE_KEYS).forEach(key => {
            localStorage.removeItem(key);
        });
        this._cache = { kundalis: null, settings: null };
    }

    /**
     * Clear cache to force reload from localStorage
     */
    clearCache() {
        this._cache = { kundalis: null, settings: null };
    }
}

// Export singleton instance
export default new AstroStorage();
