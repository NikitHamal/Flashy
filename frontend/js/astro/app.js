/**
 * Astro App Main Module
 * 
 * Main application controller for the Flashy Astro agent.
 */

const AstroApp = {
    selectedProfileId: null,
    currentChartData: null,
    chartStyle: 'north',
    
    /**
     * Initialize the application
     */
    init() {
        // Initialize modules
        AstroStorage.init();
        AstroChat.init();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Load saved state
        this.selectedProfileId = AstroStorage.getSelectedProfileId();
        
        // Render UI
        this.renderKundaliList();
        
        // Load selected kundali if any
        if (this.selectedProfileId) {
            this.selectKundali(this.selectedProfileId);
        }
        
        // Expose to global for chat module
        window.AstroApp = this;
    },
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Create kundali buttons
        document.getElementById('btn-new-kundali')?.addEventListener('click', () => this.showCreateModal());
        document.getElementById('btn-create-first')?.addEventListener('click', () => this.showCreateModal());
        
        // Modal controls
        document.getElementById('btn-close-modal')?.addEventListener('click', () => this.hideCreateModal());
        document.getElementById('btn-cancel-create')?.addEventListener('click', () => this.hideCreateModal());
        document.querySelector('#modal-create-kundali .modal-backdrop')?.addEventListener('click', () => this.hideCreateModal());
        
        // Form submission
        document.getElementById('kundali-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.createKundali();
        });
        
        // Place autocomplete
        const placeInput = document.getElementById('input-place');
        let debounceTimer;
        placeInput?.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => this.searchPlace(placeInput.value), 300);
        });
        
        // Delete kundali
        document.getElementById('btn-delete-kundali')?.addEventListener('click', () => this.showDeleteConfirm());
        document.getElementById('btn-cancel-delete')?.addEventListener('click', () => this.hideDeleteConfirm());
        document.getElementById('btn-confirm-delete')?.addEventListener('click', () => this.deleteKundali());
        document.querySelector('#modal-confirm-delete .modal-backdrop')?.addEventListener('click', () => this.hideDeleteConfirm());
        
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
        });
        
        // Chart style toggle
        document.querySelectorAll('.style-btn').forEach(btn => {
            btn.addEventListener('click', () => this.setChartStyle(btn.dataset.style));
        });
        
        // Varga selector
        document.getElementById('varga-select')?.addEventListener('change', (e) => {
            this.renderVargaChart(e.target.value);
        });
        
        // View buttons
        document.getElementById('btn-view-chart')?.addEventListener('click', () => this.switchTab('chart'));
        document.getElementById('btn-view-dashas')?.addEventListener('click', () => this.switchTab('dashas'));
        document.getElementById('btn-view-yogas')?.addEventListener('click', () => this.switchTab('yogas'));
    },
    
    /**
     * Render the kundali list in sidebar
     */
    renderKundaliList() {
        const container = document.getElementById('kundali-list');
        if (!container) return;
        
        const profiles = AstroStorage.getProfiles();
        
        if (!profiles.length) {
            container.innerHTML = `
                <div class="empty-list" style="text-align:center;padding:20px;color:var(--color-text-muted);">
                    <p>No kundalis yet</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = profiles.map(profile => {
            const isActive = profile.id === this.selectedProfileId;
            const date = new Date(profile.datetime);
            const dateStr = date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
            
            return `
                <div class="kundali-item ${isActive ? 'active' : ''}" data-id="${profile.id}">
                    <div class="kundali-item-name">${this.escapeHtml(profile.name)}</div>
                    <div class="kundali-item-meta">${dateStr}</div>
                </div>
            `;
        }).join('');
        
        // Add click handlers
        container.querySelectorAll('.kundali-item').forEach(item => {
            item.addEventListener('click', () => {
                this.selectKundali(item.dataset.id);
            });
        });
    },
    
    /**
     * Select a kundali for viewing
     */
    async selectKundali(profileId) {
        this.selectedProfileId = profileId;
        AstroStorage.setSelectedProfileId(profileId);
        
        // Update list selection
        document.querySelectorAll('.kundali-item').forEach(item => {
            item.classList.toggle('active', item.dataset.id === profileId);
        });
        
        // Hide empty state, show kundali view
        document.getElementById('empty-state')?.classList.add('hidden');
        document.getElementById('kundali-view')?.classList.remove('hidden');
        
        // Fetch chart data
        try {
            const analysis = await AstroAPI.getAnalysis(profileId);
            this.currentChartData = analysis;
            this.renderKundaliView(analysis);
            
            // Notify chat about selection
            AstroChat.addSystemMessage(`Selected kundali: ${analysis.profile?.name || 'Unknown'}`);
        } catch (error) {
            console.error('Failed to load kundali:', error);
            
            // Try from local storage
            const profile = AstroStorage.getProfile(profileId);
            if (profile) {
                this.renderBasicInfo(profile);
            }
        }
    },
    
    /**
     * Render the kundali view with chart data
     */
    renderKundaliView(data) {
        const profile = data.profile || {};
        const lagna = data.lagna || {};
        const planets = data.planets || {};
        const currentDasha = data.current_dasha || {};
        const yogas = data.yogas || [];
        
        // Header info
        document.getElementById('kundali-name').textContent = profile.name || 'Unknown';
        
        const date = new Date(profile.datetime);
        document.getElementById('kundali-datetime').textContent = 
            date.toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' }) +
            ' at ' + date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
        
        document.getElementById('kundali-place').textContent = profile.place_name || `${profile.latitude?.toFixed(2)}, ${profile.longitude?.toFixed(2)}`;
        
        // Overview cards
        document.getElementById('lagna-info').innerHTML = `
            <strong>${lagna.sign || '--'}</strong>
            <div style="font-size:12px;color:var(--color-text-muted);">
                ${lagna.nakshatra || ''} Pada ${lagna.pada || ''}
            </div>
        `;
        
        const moon = planets.Moon || {};
        document.getElementById('moon-info').innerHTML = `
            <strong>${moon.sign || '--'}</strong>
            <div style="font-size:12px;color:var(--color-text-muted);">
                ${moon.nakshatra || ''} Pada ${moon.pada || ''}
            </div>
        `;
        
        const sun = planets.Sun || {};
        document.getElementById('sun-info').innerHTML = `
            <strong>${sun.sign || '--'}</strong>
            <div style="font-size:12px;color:var(--color-text-muted);">
                ${sun.nakshatra || ''}
            </div>
        `;
        
        // Current dasha
        const md = currentDasha.mahadasha || {};
        const ad = currentDasha.antardasha || {};
        document.getElementById('current-dasha-info').innerHTML = `
            <strong>${md.planet || '--'}</strong>
            ${ad.planet ? `<span style="color:var(--color-text-muted);">/ ${ad.planet}</span>` : ''}
        `;
        
        // Quick planets grid
        this.renderPlanetsGrid(planets);
        
        // Render chart
        this.renderBirthChart(data);
        
        // Render dashas
        this.renderDashas(data);
        
        // Render yogas
        this.renderYogas(yogas);
    },
    
    /**
     * Render planets grid in overview
     */
    renderPlanetsGrid(planets) {
        const container = document.getElementById('planets-quick-list');
        if (!container) return;
        
        const planetNames = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];
        
        container.innerHTML = planetNames.map(name => {
            const planet = planets[name] || {};
            const retrograde = planet.retrograde ? ' (R)' : '';
            
            return `
                <div class="planet-card">
                    <div class="planet-icon ${name.toLowerCase()}">${name.substr(0, 2)}</div>
                    <div class="planet-info">
                        <div class="planet-name">${name}${retrograde}</div>
                        <div class="planet-sign">${planet.sign || '--'} ${planet.degree?.toFixed(1) || ''}°</div>
                    </div>
                </div>
            `;
        }).join('');
    },
    
    /**
     * Render birth chart
     */
    renderBirthChart(data) {
        const container = document.getElementById('birth-chart-svg');
        if (!container || !data) return;
        
        // Convert data format if needed
        const chartData = {
            lagna: {
                rasi: { index: this.getSignIndex(data.lagna?.sign) },
                ...data.lagna
            },
            planets: {}
        };
        
        for (const [name, planet] of Object.entries(data.planets || {})) {
            chartData.planets[name] = {
                rasi: { index: this.getSignIndex(planet.sign) },
                is_retrograde: planet.retrograde,
                dignity: planet.dignity,
                ...planet
            };
        }
        
        if (this.chartStyle === 'north') {
            AstroCharts.renderNorthIndian(container, chartData, { size: 400 });
        } else {
            AstroCharts.renderSouthIndian(container, chartData, { size: 400 });
        }
        
        // Render legend
        const legendContainer = document.getElementById('chart-legend');
        if (legendContainer) {
            AstroCharts.renderLegend(legendContainer, chartData);
        }
    },
    
    /**
     * Set chart style
     */
    setChartStyle(style) {
        this.chartStyle = style;
        
        document.querySelectorAll('.style-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.style === style);
        });
        
        if (this.currentChartData) {
            this.renderBirthChart(this.currentChartData);
        }
    },
    
    /**
     * Get sign index from name
     */
    getSignIndex(signName) {
        const signs = ['Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
                       'Tula', 'Vrishchika', 'Dhanu', 'Makara', 'Kumbha', 'Meena'];
        const idx = signs.findIndex(s => s.toLowerCase() === (signName || '').toLowerCase());
        return idx >= 0 ? idx : 0;
    },
    
    /**
     * Render dashas
     */
    renderDashas(data) {
        const container = document.getElementById('dasha-timeline');
        const badgeContainer = document.getElementById('current-period-badge');
        if (!container) return;
        
        const currentDasha = data.current_dasha || {};
        const chart = data.chart || {};
        const dashas = chart.vimshottari_dasha || [];
        
        // Current period badge
        if (badgeContainer && currentDasha.mahadasha) {
            badgeContainer.textContent = `${currentDasha.mahadasha.planet}${currentDasha.antardasha ? ' / ' + currentDasha.antardasha.planet : ''}`;
        }
        
        // Dasha timeline
        container.innerHTML = dashas.map(dasha => {
            const isCurrent = currentDasha.mahadasha?.planet === dasha.planet;
            const startDate = new Date(dasha.start_date);
            const endDate = new Date(dasha.end_date);
            
            return `
                <div class="dasha-period ${isCurrent ? 'current' : ''}">
                    <div class="dasha-planet">${dasha.planet}</div>
                    <div class="dasha-dates">
                        ${startDate.toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })} - 
                        ${endDate.toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })}
                    </div>
                    <div class="dasha-duration">${dasha.duration_years?.toFixed(1) || '--'} years</div>
                </div>
            `;
        }).join('');
    },
    
    /**
     * Render yogas
     */
    renderYogas(yogas) {
        const container = document.getElementById('yogas-list');
        if (!container) return;
        
        if (!yogas.length) {
            container.innerHTML = `
                <div style="text-align:center;padding:40px;color:var(--color-text-muted);">
                    No significant yogas detected
                </div>
            `;
            return;
        }
        
        container.innerHTML = yogas.map(yoga => `
            <div class="yoga-card">
                <div class="yoga-header">
                    <span class="yoga-name">${yoga.name}</span>
                    <span class="yoga-badge ${yoga.nature}">${yoga.nature}</span>
                </div>
                <div class="yoga-description">
                    Category: ${yoga.category} | Planets: ${yoga.planets?.join(', ') || '--'}
                </div>
                <div class="yoga-strength">
                    <span>Strength:</span>
                    <div class="strength-bar">
                        <div class="strength-fill" style="width:${yoga.strength || 0}%"></div>
                    </div>
                    <span>${yoga.strength || 0}%</span>
                </div>
            </div>
        `).join('');
    },
    
    /**
     * Render varga chart
     */
    renderVargaChart(varga) {
        const container = document.getElementById('varga-chart');
        if (!container || !this.currentChartData) return;
        
        const divisional = this.currentChartData.divisional_charts || {};
        const positions = divisional[varga] || {};
        
        container.innerHTML = `
            <div style="padding:20px;">
                <h4>${varga} Chart Positions</h4>
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:16px;">
                    ${Object.entries(positions).map(([planet, signIdx]) => `
                        <div style="padding:10px;border:2px solid var(--border-color);background:var(--color-bg);">
                            <div style="font-weight:600;">${planet}</div>
                            <div style="font-size:12px;color:var(--color-text-muted);">
                                ${AstroCharts.RASI_NAMES[signIdx] || 'Unknown'}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    },
    
    /**
     * Switch tab
     */
    switchTab(tabId) {
        // Update buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabId);
        });
        
        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('hidden', content.id !== `tab-${tabId}`);
        });
    },
    
    /**
     * Show create kundali modal
     */
    showCreateModal() {
        document.getElementById('modal-create-kundali')?.classList.remove('hidden');
        document.getElementById('input-name')?.focus();
    },
    
    /**
     * Hide create kundali modal
     */
    hideCreateModal() {
        document.getElementById('modal-create-kundali')?.classList.add('hidden');
        document.getElementById('kundali-form')?.reset();
    },
    
    /**
     * Create a new kundali
     */
    async createKundali() {
        const name = document.getElementById('input-name')?.value;
        const birthDate = document.getElementById('input-date')?.value;
        const birthTime = document.getElementById('input-time')?.value;
        const placeName = document.getElementById('input-place')?.value;
        const latitude = parseFloat(document.getElementById('input-lat')?.value);
        const longitude = parseFloat(document.getElementById('input-lng')?.value);
        const gender = document.getElementById('input-gender')?.value;
        const timezone = document.getElementById('input-timezone')?.value;
        
        if (!name || !birthDate || !birthTime) {
            alert('Please fill in all required fields');
            return;
        }
        
        if (isNaN(latitude) || isNaN(longitude)) {
            alert('Please enter valid coordinates or select a place');
            return;
        }
        
        const submitBtn = document.getElementById('btn-submit-kundali');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating...';
        
        try {
            const result = await AstroAPI.createKundali({
                name,
                birthDate,
                birthTime,
                latitude,
                longitude,
                placeName,
                gender,
                timezone
            });
            
            if (result.success && result.profile) {
                AstroStorage.addProfile(result.profile);
                this.renderKundaliList();
                this.selectKundali(result.profile.id);
                this.hideCreateModal();
                
                // Notify in chat
                AstroChat.addSystemMessage(`Created kundali for ${name}`);
            }
        } catch (error) {
            alert('Failed to create kundali: ' + error.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span class="material-symbols-outlined">add</span> Create Kundali';
        }
    },
    
    /**
     * Search for a place and show suggestions
     */
    async searchPlace(query) {
        const container = document.getElementById('place-suggestions');
        if (!container || query.length < 3) {
            container?.classList.add('hidden');
            return;
        }
        
        const results = await AstroAPI.geocode(query);
        
        if (!results.length) {
            container.classList.add('hidden');
            return;
        }
        
        container.innerHTML = results.map(r => `
            <div class="suggestion-item" data-lat="${r.lat}" data-lng="${r.lng}" data-name="${this.escapeHtml(r.name)}">
                ${this.escapeHtml(r.name.substring(0, 60))}${r.name.length > 60 ? '...' : ''}
            </div>
        `).join('');
        
        container.classList.remove('hidden');
        
        container.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', () => {
                document.getElementById('input-place').value = item.dataset.name;
                document.getElementById('input-lat').value = item.dataset.lat;
                document.getElementById('input-lng').value = item.dataset.lng;
                container.classList.add('hidden');
            });
        });
    },
    
    /**
     * Show delete confirmation
     */
    showDeleteConfirm() {
        document.getElementById('modal-confirm-delete')?.classList.remove('hidden');
    },
    
    /**
     * Hide delete confirmation
     */
    hideDeleteConfirm() {
        document.getElementById('modal-confirm-delete')?.classList.add('hidden');
    },
    
    /**
     * Delete the selected kundali
     */
    async deleteKundali() {
        if (!this.selectedProfileId) return;
        
        try {
            await AstroAPI.deleteKundali(this.selectedProfileId);
            AstroStorage.deleteProfile(this.selectedProfileId);
            
            this.selectedProfileId = null;
            AstroStorage.setSelectedProfileId(null);
            
            this.renderKundaliList();
            this.hideDeleteConfirm();
            
            // Show empty state
            document.getElementById('kundali-view')?.classList.add('hidden');
            document.getElementById('empty-state')?.classList.remove('hidden');
        } catch (error) {
            alert('Failed to delete: ' + error.message);
        }
    },
    
    /**
     * Render basic info from local profile (fallback)
     */
    renderBasicInfo(profile) {
        document.getElementById('kundali-name').textContent = profile.name || 'Unknown';
        
        const date = new Date(profile.datetime);
        document.getElementById('kundali-datetime').textContent = 
            date.toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' }) +
            ' at ' + date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
        
        document.getElementById('kundali-place').textContent = profile.place_name || `${profile.latitude?.toFixed(2)}, ${profile.longitude?.toFixed(2)}`;
        
        // Clear other sections
        ['lagna-info', 'moon-info', 'sun-info', 'current-dasha-info'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = '<em style="color:var(--color-text-muted)">Loading...</em>';
        });
    },
    
    /**
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    AstroApp.init();
});
