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
        const bd = kundali.birth_details;
        if (!bd || !this.calculationEngine) {
            throw new Error('Missing birth details or calculation engine');
        }

        // Parse date and time
        const [year, month, day] = bd.date.split('-').map(Number);
        const [hour, minute] = bd.time.split(':').map(Number);

        // Get ayanamsa
        const ayanamsa = AstroStorage.getAyanamsa();
        this.calculationEngine.setAyanamsaSystem(ayanamsa);

        // Calculate Julian Day
        const jd = this.calculationEngine.dateToJulian(year, month, day, hour, minute, 0);

        // Calculate planets
        const planets = this.calculationEngine.calculatePlanets(jd, bd.latitude, bd.longitude);

        // Calculate lagna (ascendant)
        const lagna = this.calculationEngine.calculateLagna(jd, bd.latitude, bd.longitude);

        // Build chart data structure
        const chartData = {
            jd,
            ayanamsa,
            lagna,
            planets,
            houses: this._calculateHouses(lagna, planets),
            nakshatras: this._extractNakshatras(planets),
            vargas: {}
        };

        return chartData;
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
