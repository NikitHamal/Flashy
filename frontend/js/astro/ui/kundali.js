/**
 * ============================================================================
 * Astro Kundali List Module
 * ============================================================================
 *
 * Manages the kundali sidebar list with search, selection, and CRUD operations.
 *
 * @module astro/ui/kundali
 */

import AstroStorage from './storage.js';
import AstroAPI from './api.js';

class AstroKundaliList {
    constructor() {
        this.elements = {};
        this.kundalis = [];
        this.filteredKundalis = [];
        this.searchQuery = '';

        // Callbacks for external integration
        this.onSelect = null;
        this.onDelete = null;
        this.onCreate = null;
    }

    /**
     * Initialize kundali list module
     */
    init() {
        this._cacheElements();
        this._setupEventListeners();
        this._loadKundalis();
        console.log('[AstroKundaliList] Initialized');
    }

    /**
     * Cache DOM elements
     */
    _cacheElements() {
        this.elements = {
            list: document.getElementById('kundali-list'),
            emptyState: document.getElementById('kundali-empty-state'),
            searchInput: document.getElementById('kundali-search'),
            chartCount: document.getElementById('chart-count'),
            btnNewKundali: document.getElementById('btn-new-kundali'),
            btnCreateFirst: document.getElementById('btn-create-first'),
            btnStartCreate: document.getElementById('btn-start-create')
        };
    }

    /**
     * Setup event listeners
     */
    _setupEventListeners() {
        // New kundali buttons
        this.elements.btnNewKundali?.addEventListener('click', () => {
            if (this.onCreate) this.onCreate();
        });

        this.elements.btnCreateFirst?.addEventListener('click', () => {
            if (this.onCreate) this.onCreate();
        });

        this.elements.btnStartCreate?.addEventListener('click', () => {
            if (this.onCreate) this.onCreate();
        });

        // Search
        this.elements.searchInput?.addEventListener('input', (e) => {
            this.searchQuery = e.target.value.trim().toLowerCase();
            this._filterAndRender();
        });
    }

    /**
     * Load kundalis from storage
     */
    _loadKundalis() {
        this.kundalis = AstroStorage.getKundalis();
        this._filterAndRender();
    }

    /**
     * Refresh the kundali list
     */
    refresh() {
        this._loadKundalis();
    }

    /**
     * Set kundalis from external source (AI updates)
     */
    setKundalis(kundalis) {
        if (!Array.isArray(kundalis)) return;

        this.kundalis = kundalis;
        AstroStorage.saveKundalis(kundalis);
        this._filterAndRender();
    }

    /**
     * Add a new kundali
     */
    addKundali(kundali) {
        const added = AstroStorage.addKundali(kundali);
        if (added) {
            this.kundalis = AstroStorage.getKundalis();
            this._filterAndRender();
        }
        return added;
    }

    /**
     * Update a kundali
     */
    updateKundali(id, updates) {
        const updated = AstroStorage.updateKundali(id, updates);
        if (updated) {
            this.kundalis = AstroStorage.getKundalis();
            this._filterAndRender();
        }
        return updated;
    }

    /**
     * Delete a kundali
     */
    deleteKundali(id) {
        const deleted = AstroStorage.deleteKundali(id);
        if (deleted) {
            this.kundalis = AstroStorage.getKundalis();
            this._filterAndRender();
        }
        return deleted;
    }

    /**
     * Filter kundalis by search query and render
     */
    _filterAndRender() {
        if (!this.searchQuery) {
            this.filteredKundalis = [...this.kundalis];
        } else {
            this.filteredKundalis = this.kundalis.filter(k => {
                const bd = k.birth_details || {};
                const name = (bd.name || '').toLowerCase();
                const place = (bd.place || '').toLowerCase();
                const tags = (k.tags || []).join(' ').toLowerCase();

                return name.includes(this.searchQuery) ||
                       place.includes(this.searchQuery) ||
                       tags.includes(this.searchQuery);
            });
        }

        this._render();
    }

    /**
     * Render the kundali list
     */
    _render() {
        if (!this.elements.list) return;

        // Update chart count
        if (this.elements.chartCount) {
            const count = this.kundalis.length;
            this.elements.chartCount.textContent = `${count} chart${count !== 1 ? 's' : ''}`;
        }

        // Show empty state or list
        if (this.kundalis.length === 0) {
            this._showEmptyState();
            return;
        }

        this._hideEmptyState();

        // Get active kundali ID
        const activeId = AstroStorage.getActiveKundaliId();

        // Build list HTML
        const html = this.filteredKundalis.map(k => this._renderCard(k, activeId)).join('');

        // Clear existing cards (keep empty state element)
        const cards = this.elements.list.querySelectorAll('.kundali-card');
        cards.forEach(card => card.remove());

        // Insert new cards
        this.elements.list.insertAdjacentHTML('beforeend', html);

        // Setup card event listeners
        this._setupCardListeners();
    }

    /**
     * Render a single kundali card
     */
    _renderCard(kundali, activeId) {
        const bd = kundali.birth_details || {};
        const isActive = kundali.id === activeId;

        const formattedDate = this._formatDate(bd.date);
        const formattedTime = this._formatTime(bd.time);

        const tagsHtml = (kundali.tags || []).map(tag =>
            `<span class="tag">${this._escapeHtml(tag)}</span>`
        ).join('');

        return `
            <div class="kundali-card${isActive ? ' active' : ''}" data-id="${kundali.id}">
                <div class="kundali-card-header">
                    <h4 class="kundali-card-name">${this._escapeHtml(bd.name || 'Unknown')}</h4>
                    <div class="kundali-card-actions">
                        <button class="kundali-card-btn edit" title="Edit" data-action="edit">
                            <span class="material-symbols-outlined">edit</span>
                        </button>
                        <button class="kundali-card-btn delete" title="Delete" data-action="delete">
                            <span class="material-symbols-outlined">delete</span>
                        </button>
                    </div>
                </div>
                <div class="kundali-card-info">
                    <div class="date-place">
                        <span class="material-symbols-outlined">calendar_today</span>
                        ${formattedDate} at ${formattedTime}
                    </div>
                    <div class="date-place">
                        <span class="material-symbols-outlined">location_on</span>
                        ${this._escapeHtml(bd.place || 'Unknown')}
                    </div>
                </div>
                ${tagsHtml ? `<div class="kundali-card-tags">${tagsHtml}</div>` : ''}
            </div>
        `;
    }

    /**
     * Setup event listeners for kundali cards
     */
    _setupCardListeners() {
        const cards = this.elements.list?.querySelectorAll('.kundali-card');

        cards?.forEach(card => {
            // Card click for selection
            card.addEventListener('click', (e) => {
                // Ignore clicks on action buttons
                if (e.target.closest('.kundali-card-btn')) return;

                const id = card.dataset.id;
                this.selectKundali(id);
            });

            // Delete button
            const deleteBtn = card.querySelector('[data-action="delete"]');
            deleteBtn?.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = card.dataset.id;
                const kundali = this.kundalis.find(k => k.id === id);
                if (kundali && this.onDelete) {
                    this.onDelete(kundali);
                }
            });

            // Edit button
            const editBtn = card.querySelector('[data-action="edit"]');
            editBtn?.addEventListener('click', (e) => {
                e.stopPropagation();
                // Edit functionality can be added later
                console.log('[AstroKundaliList] Edit not implemented yet');
            });
        });
    }

    /**
     * Select a kundali by ID
     */
    selectKundali(id) {
        AstroStorage.setActiveKundaliId(id);

        // Update UI
        const cards = this.elements.list?.querySelectorAll('.kundali-card');
        cards?.forEach(card => {
            card.classList.toggle('active', card.dataset.id === id);
        });

        // Notify server
        AstroAPI.setActiveKundali(id).catch(err => {
            console.warn('[AstroKundaliList] Failed to sync active kundali:', err);
        });

        // Callback
        const kundali = this.kundalis.find(k => k.id === id);
        if (kundali && this.onSelect) {
            this.onSelect(kundali);
        }
    }

    /**
     * Get active kundali
     */
    getActiveKundali() {
        const activeId = AstroStorage.getActiveKundaliId();
        return this.kundalis.find(k => k.id === activeId) || null;
    }

    /**
     * Clear active selection
     */
    clearSelection() {
        AstroStorage.setActiveKundaliId(null);

        const cards = this.elements.list?.querySelectorAll('.kundali-card');
        cards?.forEach(card => card.classList.remove('active'));
    }

    /**
     * Show empty state
     */
    _showEmptyState() {
        if (this.elements.emptyState) {
            this.elements.emptyState.style.display = '';
        }
    }

    /**
     * Hide empty state
     */
    _hideEmptyState() {
        if (this.elements.emptyState) {
            this.elements.emptyState.style.display = 'none';
        }
    }

    /**
     * Format date for display
     */
    _formatDate(dateStr) {
        if (!dateStr) return 'Unknown';

        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric'
            });
        } catch {
            return dateStr;
        }
    }

    /**
     * Format time for display
     */
    _formatTime(timeStr) {
        if (!timeStr) return 'Unknown';

        try {
            const [hours, minutes] = timeStr.split(':');
            const h = parseInt(hours);
            const ampm = h >= 12 ? 'PM' : 'AM';
            const h12 = h % 12 || 12;
            return `${h12}:${minutes} ${ampm}`;
        } catch {
            return timeStr;
        }
    }

    /**
     * Escape HTML special characters
     */
    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Get all kundalis
     */
    getKundalis() {
        return this.kundalis;
    }

    /**
     * Get kundali by ID
     */
    getKundali(id) {
        return this.kundalis.find(k => k.id === id) || null;
    }
}

// Export singleton instance
export default new AstroKundaliList();
