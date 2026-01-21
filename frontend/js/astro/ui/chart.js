/**
 * ============================================================================
 * Astro Chart Module
 * ============================================================================
 *
 * Manages chart visualization using the existing SVG chart generator.
 * Handles chart rendering, style switching, and varga selection.
 *
 * @module astro/ui/chart
 */

import AstroStorage from './storage.js';

// Import calculation modules (relative paths from ui directory)
// These will be loaded dynamically to avoid circular dependencies

class AstroChart {
    constructor() {
        this.elements = {};
        this.currentKundali = null;
        this.currentVarga = 'D1';
        this.currentStyle = 'north';
        this.chartGenerator = null;
        this.calculationEngine = null;

        // Callbacks for external integration
        this.onPlanetClick = null;
    }

    /**
     * Initialize chart module
     */
    async init() {
        this._cacheElements();
        this._setupEventListeners();
        await this._loadModules();

        // Load saved preferences
        this.currentStyle = AstroStorage.getChartStyle();
        this._updateStyleToggle();

        console.log('[AstroChart] Initialized');
    }

    /**
     * Cache DOM elements
     */
    _cacheElements() {
        this.elements = {
            wrapper: document.querySelector('.chart-wrapper'),
            noChartState: document.getElementById('no-chart-state'),
            chartContainer: document.getElementById('chart-container'),
            svgContainer: document.getElementById('chart-svg-container'),
            chartSummary: document.getElementById('chart-summary'),
            planetInfoPanel: document.getElementById('planet-info-panel'),
            planetInfoName: document.getElementById('planet-info-name'),
            planetInfoContent: document.getElementById('planet-info-content'),
            activeChartName: document.getElementById('active-chart-name'),
            activeChartInfo: document.getElementById('active-chart-info'),
            summaryLagna: document.getElementById('summary-lagna'),
            summaryMoon: document.getElementById('summary-moon'),
            summaryNakshatra: document.getElementById('summary-nakshatra'),
            summaryDasha: document.getElementById('summary-dasha'),
            viewToggle: document.querySelector('.view-toggle'),
            chartTabs: document.querySelector('.chart-tabs'),
            closePanelBtn: document.querySelector('.btn-close-panel')
        };
    }

    /**
     * Setup event listeners
     */
    _setupEventListeners() {
        // View style toggle (North/South)
        this.elements.viewToggle?.querySelectorAll('.view-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const style = btn.dataset.view;
                if (style) {
                    this.setStyle(style);
                }
            });
        });

        // Chart tabs (D1, D9, D10, etc.)
        this.elements.chartTabs?.querySelectorAll('.chart-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const chart = tab.dataset.chart;
                if (chart === 'more') {
                    // Open varga selection modal
                    document.getElementById('modal-varga-select')?.classList.remove('hidden');
                } else if (chart) {
                    this.setVarga(chart);
                }
            });
        });

        // Close planet info panel
        this.elements.closePanelBtn?.addEventListener('click', () => {
            this._hidePlanetInfo();
        });

        // Varga modal buttons
        document.querySelectorAll('.varga-btn')?.forEach(btn => {
            btn.addEventListener('click', () => {
                const varga = btn.dataset.varga;
                if (varga) {
                    this.setVarga(varga);
                    document.getElementById('modal-varga-select')?.classList.add('hidden');
                }
            });
        });
    }

    /**
     * Load calculation modules dynamically
     */
    async _loadModules() {
        try {
            // Import the chart generator
            const chartsModule = await import('../core/charts.js');
            this.chartGenerator = chartsModule.default;

            // Import the calculation engine
            const engineModule = await import('../core/engine.js');
            this.calculationEngine = engineModule.default;

            console.log('[AstroChart] Modules loaded');
        } catch (error) {
            console.error('[AstroChart] Failed to load modules:', error);
        }
    }

    /**
     * Display a kundali chart
     */
    async displayKundali(kundali) {
        if (!kundali) {
            this.clear();
            return;
        }

        this.currentKundali = kundali;

        // Show chart container, hide empty state
        this._showChart();

        // Update header info
        this._updateHeader(kundali);

        // Render the chart
        await this._renderChart();

        // Update summary cards
        this._updateSummary(kundali);
    }

    /**
     * Render the current chart
     */
    async _renderChart() {
        if (!this.currentKundali || !this.elements.svgContainer) return;

        // Get or calculate chart data
        let chartData = this.currentKundali.chart_data;

        if (!chartData && this.calculationEngine) {
            // Calculate chart data from birth details
            try {
                chartData = await this._calculateChart(this.currentKundali);
                this.currentKundali.chart_data = chartData;
            } catch (error) {
                console.error('[AstroChart] Failed to calculate chart:', error);
                this._showCalculationError(error);
                return;
            }
        }

        if (!chartData) {
            console.warn('[AstroChart] No chart data available');
            return;
        }

        // Generate SVG using chart generator
        if (this.chartGenerator) {
            try {
                const svg = this.chartGenerator.generate(
                    chartData,
                    this.currentStyle,
                    this.currentVarga,
                    {
                        interactive: true,
                        showDegrees: true,
                        showNakshatras: true,
                        onPlanetClick: (planet) => this._handlePlanetClick(planet)
                    }
                );

                this.elements.svgContainer.innerHTML = svg;

                // Setup planet click handlers on SVG elements
                this._setupSvgInteraction();
            } catch (error) {
                console.error('[AstroChart] Failed to generate chart:', error);
                this._showChartError(error);
            }
        }
    }

    /**
     * Calculate chart data from birth details
     */
    async _calculateChart(kundali) {
        // Normalize birth details - handle both nested and flat structures
        const bd = kundali.birth_details || {};
        const birthDetails = {
            date: bd.date || kundali.date,
            time: bd.time || kundali.time,
            place: bd.place || kundali.place,
            latitude: bd.latitude ?? kundali.latitude,
            longitude: bd.longitude ?? kundali.longitude,
            timezone: bd.timezone || kundali.timezone
        };

        // Validate required fields
        if (!birthDetails.date || !birthDetails.time) {
            console.warn('[AstroChart] Missing date or time in birth details, using placeholder');
            return this._createPlaceholderChartData(birthDetails);
        }

        if (birthDetails.latitude === undefined || birthDetails.longitude === undefined ||
            isNaN(birthDetails.latitude) || isNaN(birthDetails.longitude)) {
            console.warn('[AstroChart] Missing or invalid coordinates in birth details, using placeholder');
            return this._createPlaceholderChartData(birthDetails);
        }

        // Check for calculation engine
        if (!this.calculationEngine) {
            // Try to load it again
            try {
                const engineModule = await import('../core/engine.js');
                this.calculationEngine = engineModule.default;
            } catch (loadError) {
                console.warn('[AstroChart] Chart calculation skipped - engine not available:', loadError.message);
                // Return a minimal placeholder structure so the UI can still show something
                return this._createPlaceholderChartData(birthDetails);
            }
        }

        // Parse date and time
        const [year, month, day] = birthDetails.date.split('-').map(Number);
        const [hour, minute] = birthDetails.time.split(':').map(Number);

        // Create Date object for calculations
        // Note: JavaScript months are 0-indexed
        const birthDate = new Date(year, month - 1, day, hour, minute, 0);

        // Get ayanamsa
        const ayanamsa = AstroStorage.getAyanamsa();
        this.calculationEngine.setAyanamsaSystem(ayanamsa);

        // Get ayanamsa value for this date
        const ayanamsaValue = this.calculationEngine.getAyanamsa(birthDate);

        // Calculate planets using Date object
        const rawPlanets = this.calculationEngine.calculatePlanets(birthDate);

        // Calculate lagna (tropical) and convert to sidereal
        const tropicalLagna = this.calculationEngine.calculateLagna(birthDate, birthDetails.latitude, birthDetails.longitude);
        const siderealLagna = (tropicalLagna - ayanamsaValue + 360) % 360;

        // Convert tropical positions to sidereal and add nakshatra/rasi info
        const planets = {};
        const RASI_NAMES = ['Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
            'Tula', 'Vrishchika', 'Dhanu', 'Makara', 'Kumbha', 'Meena'];
        const NAKSHATRA_NAMES = [
            'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
            'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
            'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
            'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishtha', 'Shatabhisha',
            'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
        ];

        Object.entries(rawPlanets).forEach(([name, data]) => {
            const siderealLon = (data.elon - ayanamsaValue + 360) % 360;
            const signIndex = Math.floor(siderealLon / 30);
            const nakshatraIndex = Math.floor(siderealLon / (360 / 27));
            const nakshatraPada = Math.floor((siderealLon % (360 / 27)) / (360 / 27 / 4)) + 1;

            planets[name] = {
                longitude: siderealLon,
                tropicalLongitude: data.elon,
                latitude: data.elat || 0,
                distance: data.dist,
                speed: data.speed,
                retrograde: data.speed < 0,
                rasi: {
                    index: signIndex,
                    name: RASI_NAMES[signIndex],
                    degree: siderealLon % 30
                },
                nakshatra: {
                    index: nakshatraIndex,
                    name: NAKSHATRA_NAMES[nakshatraIndex],
                    pada: nakshatraPada,
                    lord: this._getNakshatraLord(nakshatraIndex)
                }
            };
        });

        // Build lagna object
        const lagnaSignIndex = Math.floor(siderealLagna / 30);
        const lagnaNakshatraIndex = Math.floor(siderealLagna / (360 / 27));
        const lagna = {
            longitude: siderealLagna,
            tropicalLongitude: tropicalLagna,
            rasi: {
                index: lagnaSignIndex,
                name: RASI_NAMES[lagnaSignIndex],
                degree: siderealLagna % 30
            },
            nakshatra: {
                index: lagnaNakshatraIndex,
                name: NAKSHATRA_NAMES[lagnaNakshatraIndex],
                pada: Math.floor((siderealLagna % (360 / 27)) / (360 / 27 / 4)) + 1
            }
        };

        // Calculate Julian Day for reference
        const jd = this.calculationEngine.dateToJulian(birthDate);

        // Build chart data structure
        const chartData = {
            jd,
            birthDate: birthDate.toISOString(),
            ayanamsa,
            ayanamsaValue,
            lagna,
            planets,
            houses: this._calculateHouses(lagna, planets),
            nakshatras: this._extractNakshatras(planets),
            divisionals: this._buildDivisionals(lagna, planets),
            vargas: {}
        };

        return chartData;
    }

    /**
     * Get Nakshatra lord for Vimshottari dasha
     */
    _getNakshatraLord(nakshatraIndex) {
        const lords = [
            'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
            'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
            'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury'
        ];
        return lords[nakshatraIndex] || 'Unknown';
    }

    /**
     * Create placeholder chart data when calculation engine is unavailable
     */
    _createPlaceholderChartData(birthDetails) {
        return {
            jd: null,
            ayanamsa: AstroStorage.getAyanamsa(),
            lagna: { longitude: 0, rasi: { index: 0, name: 'Mesha' } },
            planets: {},
            houses: {},
            nakshatras: {},
            divisionals: { D1: { houses: {} } },
            vargas: {},
            _placeholder: true,
            _message: 'Chart calculation not available. Please ensure the astronomical engine is loaded.'
        };
    }

    /**
     * Build divisional chart data structures
     */
    _buildDivisionals(lagna, planets) {
        const vargas = {
            D1: 1, D2: 2, D3: 3, D4: 4, D7: 7, D9: 9, D10: 10, D12: 12,
            D16: 16, D20: 20, D24: 24, D27: 27, D30: 30, D40: 40, D45: 45, D60: 60
        };

        const divisionals = {};

        Object.entries(vargas).forEach(([varga, div]) => {
            const lagnaVargaSign = Math.floor(lagna.longitude * div / 30) % 12;
            const houses = {};

            // Initialize houses (indexed by sign index 0-11)
            for (let s = 0; s < 12; s++) {
                houses[s] = {
                    number: ((s - lagnaVargaSign + 12) % 12) + 1,
                    planets: []
                };
            }

            // Place planets in varga positions
            Object.entries(planets).forEach(([name, data]) => {
                const planetVargaSign = Math.floor(data.longitude * div / 30) % 12;
                if (houses[planetVargaSign]) {
                    houses[planetVargaSign].planets.push({
                        name,
                        longitude: (data.longitude * div) % 360,
                        retrograde: data.retrograde || false
                    });
                }
            });

            divisionals[varga] = { houses, lagna: lagnaVargaSign };
        });

        return divisionals;
    }

    /**
     * Calculate house placements from lagna
     */
    _calculateHouses(lagna, planets) {
        const houses = {};
        const lagnaSign = Math.floor(lagna.longitude / 30);

        // Initialize houses
        for (let i = 1; i <= 12; i++) {
            houses[i] = {
                sign: (lagnaSign + i - 1) % 12,
                planets: []
            };
        }

        // Place planets in houses
        Object.entries(planets).forEach(([name, data]) => {
            const planetSign = Math.floor(data.longitude / 30);
            const house = ((planetSign - lagnaSign + 12) % 12) + 1;
            houses[house].planets.push(name);
        });

        return houses;
    }

    /**
     * Extract nakshatra data from planets
     */
    _extractNakshatras(planets) {
        const nakshatras = {};

        Object.entries(planets).forEach(([name, data]) => {
            if (data.nakshatra) {
                nakshatras[name] = {
                    name: data.nakshatra.name,
                    pada: data.nakshatra.pada,
                    lord: data.nakshatra.lord
                };
            }
        });

        return nakshatras;
    }

    /**
     * Setup SVG interaction handlers
     */
    _setupSvgInteraction() {
        const svg = this.elements.svgContainer?.querySelector('svg');
        if (!svg) return;

        // Find planet elements and add click handlers
        svg.querySelectorAll('[data-planet]').forEach(el => {
            el.style.cursor = 'pointer';
            el.addEventListener('click', (e) => {
                const planet = el.dataset.planet;
                this._handlePlanetClick(planet);
            });
        });
    }

    /**
     * Handle planet click
     */
    _handlePlanetClick(planet) {
        if (!planet || !this.currentKundali?.chart_data) return;

        const chartData = this.currentKundali.chart_data;
        const planetData = chartData.planets?.[planet];

        if (!planetData) return;

        // Show planet info panel
        this._showPlanetInfo(planet, planetData);

        // External callback
        if (this.onPlanetClick) {
            this.onPlanetClick(planet, planetData);
        }
    }

    /**
     * Show planet info panel
     */
    _showPlanetInfo(planet, data) {
        if (!this.elements.planetInfoPanel) return;

        if (this.elements.planetInfoName) {
            this.elements.planetInfoName.textContent = planet;
        }

        if (this.elements.planetInfoContent) {
            const rasi = data.rasi?.name || 'Unknown';
            const nakshatra = data.nakshatra?.name || 'Unknown';
            const pada = data.nakshatra?.pada || '?';
            const degree = data.longitude ? (data.longitude % 30).toFixed(2) : '?';
            const retrograde = data.retrograde ? ' (R)' : '';

            this.elements.planetInfoContent.innerHTML = `
                <p><strong>Sign:</strong> ${rasi}${retrograde}</p>
                <p><strong>Degree:</strong> ${degree}°</p>
                <p><strong>Nakshatra:</strong> ${nakshatra} Pada ${pada}</p>
                ${data.dignity ? `<p><strong>Dignity:</strong> ${data.dignity}</p>` : ''}
                ${data.house ? `<p><strong>House:</strong> ${data.house}</p>` : ''}
            `;
        }

        this.elements.planetInfoPanel.classList.remove('hidden');
    }

    /**
     * Hide planet info panel
     */
    _hidePlanetInfo() {
        this.elements.planetInfoPanel?.classList.add('hidden');
    }

    /**
     * Update header with kundali info
     */
    _updateHeader(kundali) {
        const bd = kundali.birth_details || {};

        if (this.elements.activeChartName) {
            this.elements.activeChartName.textContent = bd.name || 'Unknown Chart';
        }

        if (this.elements.activeChartInfo) {
            const date = bd.date || '';
            const place = bd.place || '';
            this.elements.activeChartInfo.textContent = `${date} • ${place}`;
        }
    }

    /**
     * Update summary cards
     */
    _updateSummary(kundali) {
        const chartData = kundali.chart_data;
        if (!chartData) return;

        // Lagna
        if (this.elements.summaryLagna) {
            const lagnaName = chartData.lagna?.rasi?.name || '—';
            this.elements.summaryLagna.textContent = lagnaName;
        }

        // Moon sign
        if (this.elements.summaryMoon) {
            const moonSign = chartData.planets?.Moon?.rasi?.name || '—';
            this.elements.summaryMoon.textContent = moonSign;
        }

        // Nakshatra
        if (this.elements.summaryNakshatra) {
            const nakshatra = chartData.planets?.Moon?.nakshatra?.name || '—';
            this.elements.summaryNakshatra.textContent = nakshatra;
        }

        // Current dasha (placeholder - requires dasha calculation)
        if (this.elements.summaryDasha) {
            this.elements.summaryDasha.textContent = '—';
        }

        // Show summary
        this.elements.chartSummary?.classList.remove('hidden');
    }

    /**
     * Set chart style (north/south)
     */
    setStyle(style) {
        if (style !== 'north' && style !== 'south') return;

        this.currentStyle = style;
        AstroStorage.setChartStyle(style);
        this._updateStyleToggle();

        // Re-render chart
        this._renderChart();
    }

    /**
     * Update style toggle buttons
     */
    _updateStyleToggle() {
        this.elements.viewToggle?.querySelectorAll('.view-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === this.currentStyle);
        });
    }

    /**
     * Set current varga
     */
    setVarga(varga) {
        this.currentVarga = varga;

        // Update tab active state
        this.elements.chartTabs?.querySelectorAll('.chart-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.chart === varga);
        });

        // Update varga modal active state
        document.querySelectorAll('.varga-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.varga === varga);
        });

        // Re-render chart
        this._renderChart();
    }

    /**
     * Show chart container
     */
    _showChart() {
        this.elements.noChartState?.classList.add('hidden');
        this.elements.chartContainer?.classList.remove('hidden');
    }

    /**
     * Show empty state
     */
    _showEmpty() {
        this.elements.chartContainer?.classList.add('hidden');
        this.elements.chartSummary?.classList.add('hidden');
        this.elements.noChartState?.classList.remove('hidden');

        if (this.elements.activeChartName) {
            this.elements.activeChartName.textContent = 'Select or Create a Chart';
        }
        if (this.elements.activeChartInfo) {
            this.elements.activeChartInfo.textContent = '';
        }
    }

    /**
     * Show calculation error
     */
    _showCalculationError(error) {
        if (this.elements.svgContainer) {
            this.elements.svgContainer.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--astro-rose);">
                    <span class="material-symbols-outlined" style="font-size: 48px;">error</span>
                    <p style="margin-top: 16px;">Failed to calculate chart</p>
                    <p style="font-size: 12px; color: var(--astro-text-muted);">${error.message}</p>
                </div>
            `;
        }
    }

    /**
     * Show chart rendering error
     */
    _showChartError(error) {
        if (this.elements.svgContainer) {
            this.elements.svgContainer.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--astro-rose);">
                    <span class="material-symbols-outlined" style="font-size: 48px;">warning</span>
                    <p style="margin-top: 16px;">Failed to render chart</p>
                    <p style="font-size: 12px; color: var(--astro-text-muted);">${error.message}</p>
                </div>
            `;
        }
    }

    /**
     * Clear the chart display
     */
    clear() {
        this.currentKundali = null;
        this._hidePlanetInfo();
        this._showEmpty();

        if (this.elements.svgContainer) {
            this.elements.svgContainer.innerHTML = '';
        }
    }

    /**
     * Get current kundali
     */
    getCurrentKundali() {
        return this.currentKundali;
    }

    /**
     * Export current chart as SVG
     */
    exportSvg() {
        const svg = this.elements.svgContainer?.querySelector('svg');
        if (!svg) return null;

        return svg.outerHTML;
    }

    /**
     * Export current chart as PNG data URL
     */
    async exportPng(scale = 2) {
        const svg = this.elements.svgContainer?.querySelector('svg');
        if (!svg) return null;

        return new Promise((resolve) => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const img = new Image();

            const svgData = new XMLSerializer().serializeToString(svg);
            const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
            const url = URL.createObjectURL(svgBlob);

            img.onload = () => {
                canvas.width = img.width * scale;
                canvas.height = img.height * scale;
                ctx.scale(scale, scale);
                ctx.drawImage(img, 0, 0);
                URL.revokeObjectURL(url);
                resolve(canvas.toDataURL('image/png'));
            };

            img.src = url;
        });
    }
}

// Export singleton instance
export default new AstroChart();
