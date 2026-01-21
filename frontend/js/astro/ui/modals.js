/**
 * ============================================================================
 * Astro Modals Module
 * ============================================================================
 *
 * Manages all modal dialogs for the astro interface:
 * - Create Kundali
 * - Delete Confirmation
 * - Export Options
 * - Varga Selection
 * - Dasha Timeline
 * - Yogas View
 * - Shadbala View
 *
 * @module astro/ui/modals
 */

import AstroAPI from './api.js';
import AstroStorage from './storage.js';

class AstroModals {
    constructor() {
        this.elements = {};
        this.selectedGender = '';
        this.selectedPlace = null;
        this.deleteTargetId = null;
        this.editTargetKundali = null; // For edit mode
        this.isEditMode = false;

        // Geocoding optimization
        this.debounceTimer = null;
        this.abortController = null;
        this.geocodingCache = new Map();

        // Callbacks
        this.onKundaliCreated = null;
        this.onKundaliUpdated = null; // For edit mode
        this.onKundaliDeleted = null;
        this.onExport = null;
    }

    /**
     * Initialize modals module
     */
    init() {
        this._cacheElements();
        this._setupEventListeners();
        console.log('[AstroModals] Initialized');
    }

    /**
     * Cache DOM elements
     */
    _cacheElements() {
        this.elements = {
            // Create Kundali Modal
            createModal: document.getElementById('modal-create-kundali'),
            createForm: document.getElementById('form-create-kundali'),
            btnCloseCreate: document.getElementById('btn-close-create'),
            btnCancelCreate: document.getElementById('btn-cancel-create'),
            btnSubmitCreate: document.getElementById('btn-submit-create'),
            genderBtns: document.querySelectorAll('.gender-btn'),
            genderInput: document.getElementById('kundali-gender'),
            placeInput: document.getElementById('kundali-place'),
            placeSuggestions: document.getElementById('place-suggestions'),
            latInput: document.getElementById('kundali-lat'),
            lngInput: document.getElementById('kundali-lng'),
            tzInput: document.getElementById('kundali-tz'),
            toggleOptional: document.getElementById('toggle-optional'),
            optionalFields: document.getElementById('optional-fields'),

            // Delete Modal
            deleteModal: document.getElementById('modal-delete'),
            deleteName: document.getElementById('delete-name'),
            btnCloseDelete: document.getElementById('btn-close-delete'),
            btnCancelDelete: document.getElementById('btn-cancel-delete'),
            btnConfirmDelete: document.getElementById('btn-confirm-delete'),

            // Export Modal
            exportModal: document.getElementById('modal-export'),
            btnCloseExport: document.getElementById('btn-close-export'),
            exportOptions: document.querySelectorAll('.export-option'),

            // Varga Modal
            vargaModal: document.getElementById('modal-varga-select'),
            btnCloseVarga: document.getElementById('btn-close-varga'),

            // Dasha Modal
            dashaModal: document.getElementById('modal-dasha'),
            dashaContent: document.getElementById('dasha-content'),
            btnCloseDasha: document.getElementById('btn-close-dasha'),
            btnDasha: document.getElementById('btn-dasha'),

            // Yogas Modal
            yogasModal: document.getElementById('modal-yogas'),
            yogasContent: document.getElementById('yogas-content'),
            btnCloseYogas: document.getElementById('btn-close-yogas'),
            btnYogas: document.getElementById('btn-yogas'),

            // Shadbala Modal
            shadbalaModal: document.getElementById('modal-shadbala'),
            shadbalaContent: document.getElementById('shadbala-content'),
            btnCloseShadbala: document.getElementById('btn-close-shadbala'),
            btnShadbala: document.getElementById('btn-shadbala'),

            // Export button
            btnExportChart: document.getElementById('btn-export-chart')
        };
    }

    /**
     * Setup event listeners
     */
    _setupEventListeners() {
        // Create Modal
        this._setupCreateModal();

        // Delete Modal
        this._setupDeleteModal();

        // Export Modal
        this._setupExportModal();

        // Varga Modal
        this.elements.btnCloseVarga?.addEventListener('click', () => this.closeVarga());
        this.elements.vargaModal?.addEventListener('click', (e) => {
            if (e.target === this.elements.vargaModal) this.closeVarga();
        });

        // Dasha Modal
        this.elements.btnDasha?.addEventListener('click', () => this.openDasha());
        this.elements.btnCloseDasha?.addEventListener('click', () => this.closeDasha());
        this.elements.dashaModal?.addEventListener('click', (e) => {
            if (e.target === this.elements.dashaModal) this.closeDasha();
        });

        // Yogas Modal
        this.elements.btnYogas?.addEventListener('click', () => this.openYogas());
        this.elements.btnCloseYogas?.addEventListener('click', () => this.closeYogas());
        this.elements.yogasModal?.addEventListener('click', (e) => {
            if (e.target === this.elements.yogasModal) this.closeYogas();
        });

        // Shadbala Modal
        this.elements.btnShadbala?.addEventListener('click', () => this.openShadbala());
        this.elements.btnCloseShadbala?.addEventListener('click', () => this.closeShadbala());
        this.elements.shadbalaModal?.addEventListener('click', (e) => {
            if (e.target === this.elements.shadbalaModal) this.closeShadbala();
        });

        // Export button
        this.elements.btnExportChart?.addEventListener('click', () => this.openExport());

        // Close modals on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this._closeAllModals();
            }
        });
    }

    /**
     * Setup create kundali modal
     */
    _setupCreateModal() {
        // Close buttons
        this.elements.btnCloseCreate?.addEventListener('click', () => this.closeCreate());
        this.elements.btnCancelCreate?.addEventListener('click', () => this.closeCreate());

        // Background click to close
        this.elements.createModal?.addEventListener('click', (e) => {
            if (e.target === this.elements.createModal) this.closeCreate();
        });

        // Gender buttons
        this.elements.genderBtns?.forEach(btn => {
            btn.addEventListener('click', () => {
                this.elements.genderBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.selectedGender = btn.dataset.gender;
                if (this.elements.genderInput) {
                    this.elements.genderInput.value = this.selectedGender;
                }
            });
        });

        // Place autocomplete
        this.elements.placeInput?.addEventListener('input', (e) => {
            this._handlePlaceInput(e.target.value);
        });

        // Optional fields toggle
        this.elements.toggleOptional?.addEventListener('click', () => {
            this.elements.optionalFields?.classList.toggle('collapsed');
            const icon = this.elements.toggleOptional.querySelector('.expand-icon');
            if (icon) {
                icon.style.transform = this.elements.optionalFields?.classList.contains('collapsed')
                    ? '' : 'rotate(180deg)';
            }
        });

        // Form submission
        this.elements.createForm?.addEventListener('submit', (e) => {
            e.preventDefault();
            this._handleCreateSubmit();
        });
    }

    /**
     * Setup delete modal
     */
    _setupDeleteModal() {
        this.elements.btnCloseDelete?.addEventListener('click', () => this.closeDelete());
        this.elements.btnCancelDelete?.addEventListener('click', () => this.closeDelete());
        this.elements.btnConfirmDelete?.addEventListener('click', () => this._handleDeleteConfirm());

        this.elements.deleteModal?.addEventListener('click', (e) => {
            if (e.target === this.elements.deleteModal) this.closeDelete();
        });
    }

    /**
     * Setup export modal
     */
    _setupExportModal() {
        this.elements.btnCloseExport?.addEventListener('click', () => this.closeExport());

        this.elements.exportModal?.addEventListener('click', (e) => {
            if (e.target === this.elements.exportModal) this.closeExport();
        });

        this.elements.exportOptions?.forEach(option => {
            option.addEventListener('click', () => {
                const format = option.dataset.format;
                if (format && this.onExport) {
                    this.onExport(format);
                }
                this.closeExport();
            });
        });
    }

    /**
     * Handle place input for autocomplete
     */
    _handlePlaceInput(query) {
        // Clear previous timer
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }

        if (!query || query.length < 3) {
            this._hidePlaceSuggestions();
            return;
        }

        // Check cache
        if (this.geocodingCache.has(query)) {
            this._showPlaceSuggestions(this.geocodingCache.get(query));
            return;
        }

        // Set debounce timer
        this.debounceTimer = setTimeout(async () => {
            // Abort previous request if any
            if (this.abortController) {
                this.abortController.abort();
            }

            this.abortController = new AbortController();

            try {
                const response = await fetch(
                    `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5`,
                    {
                        headers: { 'Accept-Language': 'en' },
                        signal: this.abortController.signal
                    }
                );

                if (!response.ok) return;

                const results = await response.json();

                // Cache the results
                this.geocodingCache.set(query, results);

                this._showPlaceSuggestions(results);
            } catch (error) {
                if (error.name === 'AbortError') {
                    // Ignore abort errors
                    return;
                }
                console.warn('[AstroModals] Geocoding failed:', error);
            } finally {
                this.abortController = null;
            }
        }, 500);
    }

    /**
     * Show place suggestions
     */
    _showPlaceSuggestions(results) {
        if (!this.elements.placeSuggestions || results.length === 0) {
            this._hidePlaceSuggestions();
            return;
        }

        const html = results.map(r => `
            <div class="place-suggestion" data-lat="${r.lat}" data-lon="${r.lon}" data-name="${r.display_name}">
                ${r.display_name}
            </div>
        `).join('');

        this.elements.placeSuggestions.innerHTML = html;
        this.elements.placeSuggestions.classList.remove('hidden');

        // Add click handlers
        this.elements.placeSuggestions.querySelectorAll('.place-suggestion').forEach(el => {
            el.addEventListener('click', () => {
                this._selectPlace(el);
            });
        });
    }

    /**
     * Hide place suggestions
     */
    _hidePlaceSuggestions() {
        this.elements.placeSuggestions?.classList.add('hidden');
    }

    /**
     * Select a place from suggestions
     */
    _selectPlace(el) {
        const lat = parseFloat(el.dataset.lat);
        const lon = parseFloat(el.dataset.lon);
        const name = el.dataset.name;

        if (this.elements.placeInput) {
            this.elements.placeInput.value = name;
        }

        if (this.elements.latInput) {
            this.elements.latInput.value = lat.toFixed(4);
        }

        if (this.elements.lngInput) {
            this.elements.lngInput.value = lon.toFixed(4);
        }

        // Try to get timezone
        this._getTimezone(lat, lon);

        // Enable coords row
        document.querySelector('.coords-row')?.classList.add('active');

        this.selectedPlace = { name, lat, lon };
        this._hidePlaceSuggestions();
    }

    /**
     * Get timezone for coordinates
     */
    async _getTimezone(lat, lon) {
        // Simple timezone approximation based on longitude
        // For production, use a proper timezone API
        const offsetHours = Math.round(lon / 15);
        const sign = offsetHours >= 0 ? '+' : '';
        const tz = `UTC${sign}${offsetHours}`;

        if (this.elements.tzInput) {
            this.elements.tzInput.value = tz;
        }
    }

    /**
     * Handle create/edit form submission
     */
    async _handleCreateSubmit() {
        const form = this.elements.createForm;
        if (!form) return;

        // Get form values
        const name = form.querySelector('#kundali-name')?.value?.trim();
        const date = form.querySelector('#kundali-date')?.value;
        const time = form.querySelector('#kundali-time')?.value;
        const place = form.querySelector('#kundali-place')?.value?.trim();
        const lat = parseFloat(form.querySelector('#kundali-lat')?.value);
        const lng = parseFloat(form.querySelector('#kundali-lng')?.value);
        const tz = form.querySelector('#kundali-tz')?.value?.trim() || 'UTC+0';
        const notes = form.querySelector('#kundali-notes')?.value?.trim() || '';
        const tagsStr = form.querySelector('#kundali-tags')?.value?.trim() || '';
        const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()).filter(Boolean) : [];

        // Validation
        if (!name || !date || !time || !place || isNaN(lat) || isNaN(lng)) {
            this._showToast('Please fill in all required fields', 'error');
            return;
        }

        // Disable submit button
        const loadingText = this.isEditMode ? 'Saving...' : 'Creating...';
        if (this.elements.btnSubmitCreate) {
            this.elements.btnSubmitCreate.disabled = true;
            this.elements.btnSubmitCreate.innerHTML = `
                <span class="material-symbols-outlined">hourglass_empty</span>
                ${loadingText}
            `;
        }

        try {
            if (this.isEditMode && this.editTargetKundali) {
                // EDIT MODE - Update existing kundali locally
                const updatedKundali = {
                    ...this.editTargetKundali,
                    birth_details: {
                        name,
                        date,
                        time,
                        place,
                        latitude: lat,
                        longitude: lng,
                        timezone: tz,
                        gender: this.selectedGender || 'other'
                    },
                    notes,
                    tags,
                    chart_data: null, // Clear chart data to force recalculation
                    updated_at: new Date().toISOString()
                };

                // Update in localStorage
                AstroStorage.updateKundali(this.editTargetKundali.id, updatedKundali);

                // Sync all kundalis to server to ensure persistence
                try {
                    await AstroAPI.syncKundalis(AstroStorage.getKundalis());
                } catch (syncError) {
                    console.warn('[AstroModals] Failed to sync update to server:', syncError);
                }

                // Callback
                if (this.onKundaliUpdated) {
                    this.onKundaliUpdated(updatedKundali);
                }

                this._showToast('Kundali updated successfully', 'success');
            } else {
                // CREATE MODE - Create via API
                const result = await AstroAPI.createKundali({
                    name,
                    date,
                    time,
                    place,
                    latitude: lat,
                    longitude: lng,
                    timezone: tz,
                    gender: this.selectedGender || 'other',
                    notes,
                    tags
                });

                // Save to localStorage
                if (result.kundalis) {
                    AstroStorage.saveKundalis(result.kundalis);
                }

                // Set as active
                if (result.active_kundali?.id) {
                    AstroStorage.setActiveKundaliId(result.active_kundali.id);
                }

                // Callback
                if (this.onKundaliCreated) {
                    this.onKundaliCreated(result);
                }

                this._showToast('Kundali created successfully', 'success');
            }

            this.closeCreate();
            this._resetCreateForm();

        } catch (error) {
            const action = this.isEditMode ? 'update' : 'create';
            console.error(`[AstroModals] Failed to ${action} kundali:`, error);
            this._showToast(`Failed to ${action} kundali: ${error.message}`, 'error');
        } finally {
            // Re-enable submit button
            this._updateSubmitButton(this.isEditMode ? 'Save Changes' : 'Cast Kundali');
            if (this.elements.btnSubmitCreate) {
                this.elements.btnSubmitCreate.disabled = false;
            }
        }
    }

    /**
     * Reset create form
     */
    _resetCreateForm() {
        this.elements.createForm?.reset();
        this.selectedGender = '';
        this.selectedPlace = null;
        this.elements.genderBtns?.forEach(b => b.classList.remove('active'));
        document.querySelector('.coords-row')?.classList.remove('active');
    }

    /**
     * Handle delete confirmation
     */
    async _handleDeleteConfirm() {
        if (!this.deleteTargetId) return;

        try {
            const result = await AstroAPI.deleteKundali(this.deleteTargetId);

            // Update localStorage
            if (result.kundalis) {
                AstroStorage.saveKundalis(result.kundalis);
            }

            // Callback
            if (this.onKundaliDeleted) {
                this.onKundaliDeleted(this.deleteTargetId, result);
            }

            this._showToast('Kundali deleted', 'success');
            this.closeDelete();

        } catch (error) {
            console.error('[AstroModals] Failed to delete kundali:', error);
            this._showToast(`Failed to delete: ${error.message}`, 'error');
        }
    }

    /**
     * Open create modal (new kundali)
     */
    openCreate() {
        this.isEditMode = false;
        this.editTargetKundali = null;
        this._resetCreateForm();
        this._updateModalTitle('Cast New Kundali', 'auto_awesome');
        this._updateSubmitButton('Cast Kundali');
        this.elements.createModal?.classList.remove('hidden');
        this.elements.createForm?.querySelector('#kundali-name')?.focus();
    }

    /**
     * Open edit modal for existing kundali
     */
    openEdit(kundali) {
        if (!kundali) return;

        this.isEditMode = true;
        this.editTargetKundali = kundali;

        // Populate form with existing data
        const bd = kundali.birth_details || {};
        const form = this.elements.createForm;
        if (!form) return;

        // Fill in form fields
        const nameInput = form.querySelector('#kundali-name');
        const dateInput = form.querySelector('#kundali-date');
        const timeInput = form.querySelector('#kundali-time');
        const placeInput = form.querySelector('#kundali-place');
        const latInput = form.querySelector('#kundali-lat');
        const lngInput = form.querySelector('#kundali-lng');
        const tzInput = form.querySelector('#kundali-tz');
        const notesInput = form.querySelector('#kundali-notes');
        const tagsInput = form.querySelector('#kundali-tags');

        if (nameInput) nameInput.value = bd.name || '';
        if (dateInput) dateInput.value = bd.date || '';
        if (timeInput) timeInput.value = bd.time || '';
        if (placeInput) placeInput.value = bd.place || '';
        if (latInput) latInput.value = bd.latitude || '';
        if (lngInput) lngInput.value = bd.longitude || '';
        if (tzInput) tzInput.value = bd.timezone || '';
        if (notesInput) notesInput.value = kundali.notes || bd.notes || '';
        if (tagsInput) tagsInput.value = (kundali.tags || []).join(', ');

        // Set gender
        const gender = bd.gender || kundali.gender || '';
        this.selectedGender = gender;
        this.elements.genderBtns?.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.gender === gender);
        });
        if (this.elements.genderInput) {
            this.elements.genderInput.value = gender;
        }

        // Set selected place
        if (bd.latitude && bd.longitude) {
            this.selectedPlace = {
                name: bd.place || '',
                lat: bd.latitude,
                lon: bd.longitude
            };
            document.querySelector('.coords-row')?.classList.add('active');
        }

        // Update modal UI for edit mode
        this._updateModalTitle('Edit Kundali', 'edit');
        this._updateSubmitButton('Save Changes');

        this.elements.createModal?.classList.remove('hidden');
        this.elements.createForm?.querySelector('#kundali-name')?.focus();
    }

    /**
     * Update modal title
     */
    _updateModalTitle(text, icon) {
        const titleEl = this.elements.createModal?.querySelector('.modal-title-area h2');
        const iconEl = this.elements.createModal?.querySelector('.modal-icon');
        if (titleEl) titleEl.textContent = text;
        if (iconEl) iconEl.textContent = icon === 'edit' ? '✎' : '✦';
    }

    /**
     * Update submit button text
     */
    _updateSubmitButton(text) {
        if (this.elements.btnSubmitCreate) {
            const icon = this.isEditMode ? 'save' : 'auto_awesome';
            this.elements.btnSubmitCreate.innerHTML = `
                <span class="material-symbols-outlined">${icon}</span>
                ${text}
            `;
        }
    }

    /**
     * Close create/edit modal
     */
    closeCreate() {
        this.elements.createModal?.classList.add('hidden');
        this.isEditMode = false;
        this.editTargetKundali = null;
    }

    /**
     * Open delete modal
     */
    openDelete(kundali) {
        if (!kundali) return;

        this.deleteTargetId = kundali.id;
        const name = kundali.birth_details?.name || 'this chart';

        if (this.elements.deleteName) {
            this.elements.deleteName.textContent = name;
        }

        this.elements.deleteModal?.classList.remove('hidden');
    }

    /**
     * Close delete modal
     */
    closeDelete() {
        this.elements.deleteModal?.classList.add('hidden');
        this.deleteTargetId = null;
    }

    /**
     * Open export modal
     */
    openExport() {
        this.elements.exportModal?.classList.remove('hidden');
    }

    /**
     * Close export modal
     */
    closeExport() {
        this.elements.exportModal?.classList.add('hidden');
    }

    /**
     * Open varga modal
     */
    openVarga() {
        this.elements.vargaModal?.classList.remove('hidden');
    }

    /**
     * Close varga modal
     */
    closeVarga() {
        this.elements.vargaModal?.classList.add('hidden');
    }

    /**
     * Open dasha modal
     */
    openDasha() {
        // TODO: Load and render dasha timeline
        if (this.elements.dashaContent) {
            this.elements.dashaContent.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--astro-text-muted);">
                    <span class="material-symbols-outlined" style="font-size: 48px;">timeline</span>
                    <p style="margin-top: 16px;">Dasha timeline will be displayed here</p>
                </div>
            `;
        }
        this.elements.dashaModal?.classList.remove('hidden');
    }

    /**
     * Close dasha modal
     */
    closeDasha() {
        this.elements.dashaModal?.classList.add('hidden');
    }

    /**
     * Open yogas modal
     */
    openYogas() {
        // TODO: Load and render yogas
        if (this.elements.yogasContent) {
            this.elements.yogasContent.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--astro-text-muted);">
                    <span class="material-symbols-outlined" style="font-size: 48px;">auto_awesome</span>
                    <p style="margin-top: 16px;">Yogas analysis will be displayed here</p>
                </div>
            `;
        }
        this.elements.yogasModal?.classList.remove('hidden');
    }

    /**
     * Close yogas modal
     */
    closeYogas() {
        this.elements.yogasModal?.classList.add('hidden');
    }

    /**
     * Open shadbala modal
     */
    openShadbala() {
        // TODO: Load and render shadbala
        if (this.elements.shadbalaContent) {
            this.elements.shadbalaContent.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--astro-text-muted);">
                    <span class="material-symbols-outlined" style="font-size: 48px;">bar_chart</span>
                    <p style="margin-top: 16px;">Planetary strength analysis will be displayed here</p>
                </div>
            `;
        }
        this.elements.shadbalaModal?.classList.remove('hidden');
    }

    /**
     * Close shadbala modal
     */
    closeShadbala() {
        this.elements.shadbalaModal?.classList.add('hidden');
    }

    /**
     * Close all modals
     */
    _closeAllModals() {
        this.closeCreate();
        this.closeDelete();
        this.closeExport();
        this.closeVarga();
        this.closeDasha();
        this.closeYogas();
        this.closeShadbala();
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

        // Auto-remove after 4 seconds
        setTimeout(() => {
            toast.style.animation = 'toast-in 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
}

// Export singleton instance
export default new AstroModals();
