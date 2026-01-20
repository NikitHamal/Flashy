// charts.js - SVG Chart Generation for Vedic Astrology
import I18n from '../core/i18n.js';
import {
    RASI_NAMES,
    PLANETARY_DIGNITIES,
    getDignity
} from './constants.js';

class Charts {
    constructor() {
        this.size = 380; // Larger size for better readability

        // Enhanced color scheme using CSS variables with fallbacks
        this.colors = {
            // Base colors - using theme tokens
            surface: 'var(--surface, #FDFBFA)',
            outline: 'var(--primary, #4A3728)',
            line: 'var(--outline-variant, #D8D0CB)',
            text: 'var(--on-surface-variant, #5D534E)',
            textBold: 'var(--on-surface, #1F1B19)',

            // Subtle house backgrounds
            houseFill: 'var(--surface-variant, #F5F5F0)',
            houseStroke: 'var(--outline-variant, #EBE5E0)',

            // Dignity Colors - Refined palette
            exalted: '#1B5E20',        // Darker Green
            debilitated: '#B71C1C',    // Darker Red
            ownSign: '#0D47A1',        // Darker Blue
            mooltrikona: '#4A148C',    // Darker Purple
            neutral: '#4A3728',        // Theme primary brown

            // Special States
            retrograde: '#E65100',     // Orange
            combusted: '#FF6F00',      // Amber
            ascendant: '#855E0B',      // Refined Gold

            // Background highlights
            exaltedBg: 'rgba(46, 125, 50, 0.08)',
            debilitatedBg: 'rgba(198, 40, 40, 0.08)',
        };

        // Planet-specific colors (Vedic tradition) - High Contrast
        this.planetColors = {
            Sun: '#B7791F',      // Deep Golden
            Moon: '#2B6CB0',     // Stronger Blue
            Mars: '#C53030',     // Strong Red
            Mercury: '#2F855A',  // Strong Green
            Jupiter: '#975A16',  // Dark Gold/Bronze
            Venus: '#B83280',    // Magenta/Pink
            Saturn: '#1A202C',   // Deep Gray/Black
            Rahu: '#4A5568',     // Slate Gray
            Ketu: '#718096',     // Light Slate
            Asc: '#855E0B'       // Dark Gold (Lagna)
        };

        // Reference centralized sign names (Sanskrit keys for I18n)
        this.signNames = RASI_NAMES;

        // Reference centralized dignity data
        this.dignities = PLANETARY_DIGNITIES;

        // Dignity symbols/markers to append to planet names
        this.dignityMarkers = {
            exalted: '↑',        // Up arrow for exalted
            debilitated: '↓',   // Down arrow for debilitated
            ownSign: '○',       // Circle for own sign
            mooltrikona: '△',   // Triangle for mooltrikona
            retrograde: '℞',    // Standard retrograde symbol (or use 'R')
            combusted: '☼',     // Sun symbol for combust
            vargottama: 'Ⓥ'      // V for Vargottama
        };

        this.northHouseCenters = this.calculateNorthHouseCenters();
        this.southSignPositions = this.calculateSouthSignPositions();
    }

    calculateNorthHouseCenters() {
        const s = this.size;
        const m = s / 2;
        // Optimized positions for planet text placement
        return {
            1: { x: m, y: s * 0.22, type: 'diamond', maxWidth: s * 0.35 },
            2: { x: s * 0.18, y: s * 0.1, type: 'triangle', maxWidth: s * 0.2 },
            3: { x: s * 0.1, y: s * 0.18, type: 'triangle', maxWidth: s * 0.2 },
            4: { x: s * 0.22, y: m, type: 'diamond', maxWidth: s * 0.35 },
            5: { x: s * 0.1, y: s * 0.82, type: 'triangle', maxWidth: s * 0.2 },
            6: { x: s * 0.18, y: s * 0.9, type: 'triangle', maxWidth: s * 0.2 },
            7: { x: m, y: s * 0.78, type: 'diamond', maxWidth: s * 0.35 },
            8: { x: s * 0.82, y: s * 0.9, type: 'triangle', maxWidth: s * 0.2 },
            9: { x: s * 0.9, y: s * 0.82, type: 'triangle', maxWidth: s * 0.2 },
            10: { x: s * 0.78, y: m, type: 'diamond', maxWidth: s * 0.35 },
            11: { x: s * 0.9, y: s * 0.18, type: 'triangle', maxWidth: s * 0.2 },
            12: { x: s * 0.82, y: s * 0.1, type: 'triangle', maxWidth: s * 0.2 }
        };
    }

    calculateSouthSignPositions() {
        // South Indian chart: Fixed signs, houses rotate
        // Layout: Top row L-R: Pisces(11), Aries(0), Taurus(1), Gemini(2)
        const signGrid = [
            [11, 0, 1, 2],
            [10, -1, -1, 3],
            [9, -1, -1, 4],
            [8, 7, 6, 5]
        ];

        const positions = {};
        const box = this.size / 4;

        for (let r = 0; r < 4; r++) {
            for (let c = 0; c < 4; c++) {
                const signIdx = signGrid[r][c];
                if (signIdx !== -1) {
                    positions[signIdx] = {
                        x: c * box,
                        y: r * box,
                        cx: c * box + box / 2,
                        cy: r * box + box / 2,
                        width: box,
                        height: box
                    };
                }
            }
        }
        return positions;
    }

    /**
     * Main generation method
     */
    generate(data, style = 'north', vargaKey = 'D1', options = {}) {
        const chartData = data?.divisionals?.[vargaKey];
        if (!chartData) {
            return this.generateErrorSVG(`No data for ${vargaKey}`);
        }

        const mergedOptions = {
            showDegrees: false,
            showRetrograde: true,
            showDignities: true,
            showSignNumbers: true,
            showLegend: true,
            compactMode: false,
            ...options
        };

        const chartSvg = style === 'north'
            ? this.generateNorthIndian(chartData, mergedOptions)
            : this.generateSouthIndian(chartData, mergedOptions);

        // Add legend if requested
        if (mergedOptions.showLegend) {
            return this.wrapWithLegend(chartSvg, mergedOptions);
        }

        return chartSvg;
    }

    generateErrorSVG(message) {
        const s = this.size;
        return `<svg viewBox="0 0 ${s} ${s}" class="kundali-chart error" xmlns="http://www.w3.org/2000/svg">
            <rect x="0" y="0" width="${s}" height="${s}" fill="${this.colors.surface}" stroke="${this.colors.outline}" stroke-width="1"/>
            <text x="${s / 2}" y="${s / 2}" text-anchor="middle" dominant-baseline="middle" 
                  font-size="14" fill="${this.colors.debilitated}">${message}</text>
        </svg>`;
    }

    /**
     * North Indian Style Chart - Enhanced
     */
    generateNorthIndian(data, options) {
        const s = this.size;
        const m = s / 2;
        const pad = 2;

        let svg = `<svg viewBox="0 0 ${s} ${s}" class="kundali-chart north-style" xmlns="http://www.w3.org/2000/svg">`;

        // Background with subtle gradient
        svg += `<defs>
            <linearGradient id="chartBg" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="${this.colors.surface}" stop-opacity="1" />
                <stop offset="100%" stop-color="${this.colors.houseFill}" stop-opacity="1" />
            </linearGradient>
        </defs>`;
        svg += `<rect x="0" y="0" width="${s}" height="${s}" fill="url(#chartBg)"/>`;

        // Outer Frame - refined with double border effect
        svg += `<rect x="${pad}" y="${pad}" width="${s - pad * 2}" height="${s - pad * 2}" fill="none" stroke="${this.colors.outline}" stroke-width="2" rx="4"/>`;
        svg += `<rect x="${pad + 4}" y="${pad + 4}" width="${s - pad * 2 - 8}" height="${s - pad * 2 - 8}" fill="none" stroke="${this.colors.line}" stroke-width="0.5"/>`;

        // Diagonals - refined
        svg += `<line x1="${pad}" y1="${pad}" x2="${s - pad}" y2="${s - pad}" stroke="${this.colors.outline}" stroke-width="1.5" opacity="0.8"/>`;
        svg += `<line x1="${s - pad}" y1="${pad}" x2="${pad}" y2="${s - pad}" stroke="${this.colors.outline}" stroke-width="1.5" opacity="0.8"/>`;

        // Inner Diamond with slight fill
        svg += `<polygon points="${m},${pad + 4} ${pad + 4},${m} ${m},${s - pad - 4} ${s - pad - 4},${m}" 
                fill="${this.colors.houseFill}" fill-opacity="0.5" 
                stroke="${this.colors.outline}" stroke-width="1.5"/>`;

        const ascSignIndex = this.getAscendantSignIndex(data);
        options.ascSignIndex = ascSignIndex;

        for (let house = 1; house <= 12; house++) {
            const signIndex = (ascSignIndex + house - 1) % 12;
            const houseCenter = this.northHouseCenters[house];

            // Render Sign Number
            if (options.showSignNumbers) {
                const signNumPos = this.getSignNumberPosition(house, houseCenter);
                svg += `<text x="${signNumPos.x}" y="${signNumPos.y}" text-anchor="middle" 
                        dominant-baseline="middle" font-size="10" fill="${this.colors.text}" 
                        font-family="var(--font-family, Arial), sans-serif" opacity="0.5" font-weight="400">${I18n.n(signIndex + 1)}</text>`;
            }

            // Collect and render planets
            const planetsInSign = this.collectPlanetsInSign(signIndex, data, options);
            svg += this.renderPlanetsInHouse(planetsInSign, houseCenter, 'north', house);
        }

        svg += '</svg>';
        return svg;
    }

    /**
     * South Indian Style Chart - Enhanced
     */
    generateSouthIndian(data, options) {
        const s = this.size;
        const box = s / 4;
        const pad = 2;

        let svg = `<svg viewBox="0 0 ${s} ${s}" class="kundali-chart south-style" xmlns="http://www.w3.org/2000/svg">`;

        // Background
        svg += `<rect x="0" y="0" width="${s}" height="${s}" fill="${this.colors.surface}"/>`;

        // Outer Frame - refined
        svg += `<rect x="${pad}" y="${pad}" width="${s - pad * 2}" height="${s - pad * 2}" fill="none" stroke="${this.colors.outline}" stroke-width="2" rx="4"/>`;

        // Grid Lines - refined
        for (let i = 1; i < 4; i++) {
            svg += `<line x1="${i * box}" y1="${pad}" x2="${i * box}" y2="${s - pad}" stroke="${this.colors.outline}" stroke-width="1" opacity="0.6"/>`;
            svg += `<line x1="${pad}" y1="${i * box}" x2="${s - pad}" y2="${i * box}" stroke="${this.colors.outline}" stroke-width="1" opacity="0.6"/>`;
        }

        // Center void with subtle fill
        svg += `<rect x="${box}" y="${box}" width="${box * 2}" height="${box * 2}" fill="${this.colors.houseFill}" stroke="none" rx="2"/>`;
        svg += `<rect x="${box}" y="${box}" width="${box * 2}" height="${box * 2}" fill="none" stroke="${this.colors.line}" stroke-width="1"/>`;

        const ascSignIndex = this.getAscendantSignIndex(data);
        options.ascSignIndex = ascSignIndex;

        for (let signIndex = 0; signIndex < 12; signIndex++) {
            const pos = this.southSignPositions[signIndex];
            if (!pos) continue;

            // Sign Number (top-left corner)
            if (options.showSignNumbers) {
                svg += `<text x="${pos.x + 5}" y="${pos.y + 12}" font-size="10" 
                        fill="${this.colors.text}" font-family="var(--font-family, Arial), sans-serif" opacity="0.5" font-weight="400">${I18n.n(signIndex + 1)}</text>`;
            }

            // Ascendant Indicator - refined diagonal
            if (signIndex === ascSignIndex) {
                svg += `<line x1="${pos.x + 2}" y1="${pos.y + pos.height - 2}" x2="${pos.x + pos.width - 2}" y2="${pos.y + 2}" 
                        stroke="${this.colors.ascendant}" stroke-width="1.5" opacity="0.6"/>`;
                svg += `<text x="${pos.x + pos.width - 6}" y="${pos.y + 14}" text-anchor="end" 
                        font-size="11" font-weight="700" fill="${this.colors.ascendant}" 
                        font-family="var(--font-family, Arial), sans-serif">${this.getPlanetSymbol('Asc')}</text>`;
            }

            // Collect and render planets
            const planetsInSign = this.collectPlanetsInSign(signIndex, data, options, false);
            svg += this.renderPlanetsInHouse(planetsInSign, pos, 'south');
        }

        svg += '</svg>';
        return svg;
    }

    // --- Helper Methods ---

    getAscendantSignIndex(data) {
        if (data.lagna?.rasi?.index !== undefined) return data.lagna.rasi.index;
        if (data.houses?.[1]?.signIndex !== undefined) return data.houses[1].signIndex;
        if (data.ascendant?.signIndex !== undefined) return data.ascendant.signIndex;
        if (data.ascendant?.rasi?.index !== undefined) return data.ascendant.rasi.index;
        return 0; // Default Aries
    }

    getSignNumberPosition(house, center) {
        const off = 28;
        const smallOff = 15;
        switch (house) {
            case 1: return { x: center.x, y: center.y - off };
            case 2: return { x: center.x + smallOff, y: center.y + smallOff };
            case 3: return { x: center.x - smallOff, y: center.y + smallOff };
            case 4: return { x: center.x + off, y: center.y };
            case 5: return { x: center.x - smallOff, y: center.y - smallOff };
            case 6: return { x: center.x + smallOff, y: center.y - smallOff };
            case 7: return { x: center.x, y: center.y + off };
            case 8: return { x: center.x - smallOff, y: center.y - smallOff };
            case 9: return { x: center.x + smallOff, y: center.y - smallOff };
            case 10: return { x: center.x - off, y: center.y };
            case 11: return { x: center.x + smallOff, y: center.y + smallOff };
            case 12: return { x: center.x - smallOff, y: center.y + smallOff };
            default: return { x: center.x, y: center.y };
        }
    }

    collectPlanetsInSign(signIndex, data, options, includeAsc = true) {
        const planets = [];

        // Add Ascendant marker if in this sign (for North charts)
        if (includeAsc && data.lagna?.rasi?.index === signIndex) {
            const lagnaDeg = data.lagna.degree || 0;
            const degStr = `${Math.floor(lagnaDeg)}° ${Math.floor((lagnaDeg % 1) * 60)}'`;
            const signName = I18n.t('rasis.' + this.signNames[signIndex]);
            const lagnaName = I18n.t('planets.Asc');

            planets.push({
                symbol: this.getPlanetSymbol('Asc'),
                fullSymbol: this.getPlanetSymbol('Asc'),
                name: lagnaName,
                dignityState: 'ascendant',
                color: this.colors.ascendant,
                fontWeight: 'bold',
                isRetrograde: false,
                degree: lagnaDeg,
                tooltip: `${lagnaName}: ${degStr} ${signName}`
            });
        }

        // Process each planet
        if (data.planets) {
            for (const [name, planet] of Object.entries(data.planets)) {
                const pSignIndex = planet.rasi?.index !== undefined ? planet.rasi.index : (planet.signIndex ?? 0);

                if (pSignIndex === signIndex) {
                    const planetData = this.processPlanet(name, planet, signIndex, options);
                    planets.push(planetData);
                }
            }
        }

        // Sort by degree for consistent ordering
        planets.sort((a, b) => (a.degree || 0) - (b.degree || 0));
        return planets;
    }

    processPlanet(name, planet, signIndex, options) {
        const baseSymbol = this.getPlanetSymbol(name);
        const isRetrograde = planet.isRetrograde === true || planet.retrograde === true || (planet.speed !== undefined && planet.speed < 0);
        const degree = planet.longitude !== undefined ? planet.longitude % 30 : (planet.degree ?? (planet.lon ? planet.lon % 30 : 0));

        let dignityState = 'neutral';
        let dignityMarker = '';
        // ALWAYS use planet's natural color as requested
        let color = this.planetColors[name] || this.colors.neutral;
        let tooltip = name;
        let fontWeight = '700'; // Bold for better visibility

        // Calculate dignity
        if (options.showDignities && this.dignities[name]) {
            dignityState = this.calculateDignity(name, signIndex, degree);

            // Add dignity marker symbol
            if (dignityState !== 'neutral') {
                dignityMarker = this.dignityMarkers[dignityState] || '';
            }
        }

        // Build expanded tooltip
        const planetName = I18n.t('planets.' + name);
        const signName = I18n.t('rasis.' + this.signNames[signIndex]);
        const degStr = `${I18n.n(Math.floor(degree))}° ${I18n.n(Math.floor((degree % 1) * 60))}'`;
        const nakName = planet.nakshatra ? I18n.t('lists.nakshatras.' + planet.nakshatra.index) : '';
        const pada = planet.nakshatra ? I18n.n(planet.nakshatra.pada) : '';

        tooltip = `${planetName}: ${degStr} ${signName}`;
        if (nakName) tooltip += `\n${I18n.t('kundali.nakshatra')}: ${nakName} (${pada} ${I18n.t('common.pada')})`;
        if (dignityState !== 'neutral') tooltip += `\n${I18n.t('kundali.dignity')}: ${this.formatDignityName(dignityState)}`;

        // Add Lordship (relative to chart lagna)
        const ascSignIndex = options.ascSignIndex;
        if (ascSignIndex !== undefined) {
            const ruledHouses = this.getRuledHouses(name, ascSignIndex);
            if (ruledHouses.length > 0) {
                const housesStr = ruledHouses.map(h => I18n.n(h)).join(', ');
                tooltip += `\n${I18n.t('analysis.lords')}: ${housesStr} ${I18n.getLocale() === 'ne' ? 'भाव' : 'L'}`;
            }
        }

        // Build the display symbol
        let displaySymbol = baseSymbol;

        // Add short retrograde marker (R) or (व)
        if (isRetrograde && options.showRetrograde) {
            displaySymbol += `${I18n.t('kundali.retrograde_short')}`;
            tooltip += ` [${I18n.t('kundali.retrograde_full')}]`;
        }

        // Add dignity marker after retrograde
        if (dignityMarker && options.showDignities) {
            displaySymbol += dignityMarker;
        }

        // Add degree if requested
        if (options.showDegrees) {
            displaySymbol += ` ${I18n.n(Math.floor(degree))}°`;
        }

        return {
            symbol: displaySymbol,
            baseSymbol: baseSymbol,
            name,
            degree,
            isRetrograde,
            dignityState,
            dignityMarker,
            color,
            fontWeight,
            tooltip
        };
    }

    calculateDignity(planetName, signIndex, degree) {
        // Use centralized getDignity function
        const dignity = getDignity(planetName, signIndex, degree);
        // Map centralized dignity names to chart-specific names
        if (dignity === 'own') return 'ownSign';
        if (dignity === 'moolatrikona') return 'mooltrikona';
        return dignity;
    }

    formatDignityName(state) {
        const names = {
            exalted: I18n.t('kundali.exalted'),
            debilitated: I18n.t('kundali.debilitated'),
            ownSign: I18n.t('kundali.own_sign'),
            mooltrikona: I18n.t('kundali.mooltrikona'),
            neutral: I18n.t('kundali.neutral'),
            ascendant: I18n.t('planets.Asc')
        };
        return names[state] || state;
    }

    getPlanetSymbol(name) {
        // Handle name consistency
        let key = name;
        if (name === 'Ascendant' || name === 'Lagna' || name === 'Asc') {
            key = 'Asc';
        }

        return I18n.t('planet_symbols.' + key);
    }

    getDignityColor(state) {
        return this.colors[state] || this.colors.neutral;
    }

    getRuledHouses(planet, lagnaSignIndex) {
        const owners = {
            Sun: [4], Moon: [3],
            Mars: [0, 7], Mercury: [2, 5],
            Jupiter: [8, 11], Venus: [1, 6],
            Saturn: [9, 10]
        };

        const ruledSigns = owners[planet] || [];
        const houses = [];

        ruledSigns.forEach(signIdx => {
            const house = (signIdx - lagnaSignIndex + 12) % 12 + 1;
            houses.push(house);
        });

        return houses.sort((a, b) => a - b);
    }

    /**
     * Render planets within a house area
     * Handles overlapping by creating rows/columns
     */
    renderPlanetsInHouse(planets, center, style, houseNumber = 0) {
        if (!planets || planets.length === 0) return '';

        const cx = center.cx || center.x;
        const cy = center.cy || center.y;

        let svg = '';
        const count = planets.length;

        // LARGER font sizing for better readability
        let fontSize = 14;
        let lineHeight = 16;

        if (style === 'south') {
            // South style has more space per box
            fontSize = count > 5 ? 11 : (count > 3 ? 12 : 14);
            lineHeight = count > 5 ? 13 : 16;
        } else {
            // North style - ensure MINIMUM 11px even in triangles
            const isTriangle = center.type === 'triangle';
            if (isTriangle) {
                fontSize = count > 4 ? 11 : (count > 2 ? 11 : 12);
                lineHeight = count > 4 ? 13 : 14;
            } else {
                // Diamond houses have more space
                fontSize = count > 5 ? 11 : (count > 3 ? 12 : 14);
                lineHeight = count > 5 ? 13 : 16;
            }
        }

        // Calculate layout
        if (style === 'south') {
            svg += this.renderSouthLayout(planets, cx, cy, fontSize, lineHeight, center);
        } else {
            svg += this.renderNorthLayout(planets, cx, cy, fontSize, lineHeight, center);
        }

        return svg;
    }

    renderSouthLayout(planets, cx, cy, fontSize, lineHeight, box) {
        let svg = '';
        const count = planets.length;

        // For south charts, we have a box with some padding
        const maxWidth = (box.width || 75) - 10;
        const usableHeight = (box.height || 75) - 16;

        if (count <= 3) {
            // Simple vertical stack
            const totalHeight = (count - 1) * lineHeight;
            const startY = cy - totalHeight / 2;

            planets.forEach((planet, i) => {
                svg += this.renderPlanetText(planet, cx, startY + i * lineHeight, fontSize);
            });
        } else {
            // Two-column layout
            const cols = 2;
            const rows = Math.ceil(count / cols);
            const colWidth = maxWidth / cols;
            const totalHeight = (rows - 1) * lineHeight;
            const startY = cy - totalHeight / 2;
            const startX = cx - colWidth / 2;

            planets.forEach((planet, i) => {
                const col = i % cols;
                const row = Math.floor(i / cols);
                const x = startX + col * colWidth;
                const y = startY + row * lineHeight;
                svg += this.renderPlanetText(planet, x, y, fontSize - 1);
            });
        }

        return svg;
    }

    renderNorthLayout(planets, cx, cy, fontSize, lineHeight, houseCenter) {
        let svg = '';
        const count = planets.length;
        const isTriangle = houseCenter.type === 'triangle';

        if (count === 1) {
            svg += this.renderPlanetText(planets[0], cx, cy, fontSize);
        } else if (count === 2) {
            // Side by side or vertical based on space
            if (isTriangle) {
                // Vertical stack for triangles
                svg += this.renderPlanetText(planets[0], cx, cy - lineHeight / 2, fontSize);
                svg += this.renderPlanetText(planets[1], cx, cy + lineHeight / 2, fontSize);
            } else {
                // Side by side for diamonds
                const spacing = 22;
                svg += this.renderPlanetText(planets[0], cx - spacing, cy, fontSize);
                svg += this.renderPlanetText(planets[1], cx + spacing, cy, fontSize);
            }
        } else if (count === 3) {
            if (isTriangle) {
                // Vertical stack - NO font reduction
                const totalHeight = 2 * lineHeight;
                const startY = cy - totalHeight / 2;
                planets.forEach((p, i) => {
                    svg += this.renderPlanetText(p, cx, startY + i * lineHeight, fontSize);
                });
            } else {
                // 2 top, 1 bottom
                const spacing = 22;
                svg += this.renderPlanetText(planets[0], cx - spacing, cy - lineHeight / 2, fontSize);
                svg += this.renderPlanetText(planets[1], cx + spacing, cy - lineHeight / 2, fontSize);
                svg += this.renderPlanetText(planets[2], cx, cy + lineHeight / 2, fontSize);
            }
        } else {
            // 4+ planets: grid layout
            const cols = isTriangle ? 1 : 2;
            const rows = Math.ceil(count / cols);
            const colSpacing = cols > 1 ? 25 : 0;
            const totalHeight = (rows - 1) * lineHeight;
            const startY = cy - totalHeight / 2;

            planets.forEach((planet, i) => {
                const col = i % cols;
                const row = Math.floor(i / cols);
                const x = cols > 1 ? (cx + (col - 0.5) * colSpacing) : cx;
                const y = startY + row * lineHeight;
                svg += this.renderPlanetText(planet, x, y, fontSize); // NO font reduction
            });
        }

        return svg;
    }

    renderPlanetText(planet, x, y, fontSize) {
        const fontWeight = planet.fontWeight || 'normal';
        const fill = planet.color || this.colors.neutral;

        // Create tooltip
        const tooltip = `<title>${planet.tooltip || planet.name}</title>`;

        // Refined text with better styling
        let extraElements = '';

        // Add small indicator for retrograde
        if (planet.isRetrograde) {
            // Position dot relative to planet center - offset to the top-right
            const dotX = x + (fontSize * 0.6);
            const dotY = y - (fontSize * 0.6);
            extraElements += `<circle cx="${dotX}" cy="${dotY}" r="2" fill="${this.colors.retrograde}" opacity="0.9"/>`;
        }

        return `<text x="${x}" y="${y}" 
                text-anchor="middle" dominant-baseline="middle" 
                font-size="${fontSize}" font-weight="${fontWeight}" 
                fill="${fill}" font-family="var(--font-family, Arial), sans-serif">
                ${tooltip}${planet.symbol}
                </text>${extraElements}`;
    }

    /**
     * Wrap chart SVG with legend
     */
    wrapWithLegend(chartSvg, options) {
        const rSym = `(${I18n.t('kundali.retrograde_short')})`;
        const cSym = this.dignityMarkers.combusted;
        const vSym = this.dignityMarkers.vargottama;

        const legendHtml = `
            <div class="chart-container">
                <div class="chart-svg-wrapper">
                    ${chartSvg}
                </div>
                <div class="chart-legend">
                    <div class="legend-title">${I18n.t('kundali.legend')}</div>
                    <div class="legend-grid">
                        <div class="legend-item">
                            <span class="legend-symbol" style="color: ${this.colors.exalted};">↑</span>
                            <span class="legend-label">${I18n.t('kundali.exalted')}</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-symbol" style="color: ${this.colors.debilitated};">↓</span>
                            <span class="legend-label">${I18n.t('kundali.debilitated')}</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-symbol" style="color: ${this.colors.ownSign};">○</span>
                            <span class="legend-label">${I18n.t('kundali.own_sign')}</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-symbol" style="color: ${this.colors.mooltrikona};">△</span>
                            <span class="legend-label">${I18n.t('kundali.mooltrikona')}</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-symbol" style="color: ${this.colors.retrograde};">${rSym}</span>
                            <span class="legend-label">${I18n.t('kundali.retrograde')}</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-symbol" style="color: ${this.colors.combusted};">${cSym}</span>
                            <span class="legend-label">${I18n.t('kundali.combust')}</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-symbol" style="color: #4DB6AC;">${vSym}</span>
                            <span class="legend-label">${I18n.t('kundali.vargottama')}</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-symbol" style="color: #AB47BC; font-size: 13px;">AK</span>
                            <span class="legend-label">${I18n.t('kundali.ak')}</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-symbol" style="color: #7E57C2; font-size: 13px;">AmK</span>
                            <span class="legend-label">${I18n.t('kundali.amk')}</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-symbol" style="color: ${this.colors.ascendant}; font-weight: bold;">${this.getPlanetSymbol('Asc')}</span>
                            <span class="legend-label">${I18n.t('planets.Asc')}</span>
                        </div>
                    </div>
                    <div class="legend-note">
                        <small>${I18n.t('kundali.hover_details')}</small>
                    </div>
                </div>
            </div>
        `;
        return legendHtml;
    }

    /**
     * Generate standalone legend HTML
     */
    generateLegend() {
        return `
            <div class="chart-legend standalone">
                <div class="legend-title">Chart Symbols</div>
                <div class="legend-grid">
                    <div class="legend-section">
                        <div class="legend-section-title">Planetary Dignities</div>
                        <div class="legend-item">
                            <span class="legend-color-box" style="background: ${this.colors.exalted};"></span>
                            <span class="legend-marker">↑</span>
                            <span class="legend-label">Exalted - Planet at peak strength</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color-box" style="background: ${this.colors.debilitated};"></span>
                            <span class="legend-marker">↓</span>
                            <span class="legend-label">Debilitated - Planet at weakest</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color-box" style="background: ${this.colors.ownSign};"></span>
                            <span class="legend-marker">○</span>
                            <span class="legend-label">Own Sign - Planet in its home sign</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color-box" style="background: ${this.colors.mooltrikona};"></span>
                            <span class="legend-marker">△</span>
                            <span class="legend-label">Mooltrikona - Strong office position</span>
                        </div>
                    </div>
                    <div class="legend-section">
                        <div class="legend-section-title">Special States</div>
                        <div class="legend-item">
                            <span class="legend-color-box" style="background: ${this.colors.retrograde};"></span>
                            <span class="legend-marker">(R)</span>
                            <span class="legend-label">Retrograde - Apparent backward motion</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color-box" style="background: ${this.colors.ascendant};"></span>
                            <span class="legend-marker">Asc</span>
                            <span class="legend-label">Ascendant / Lagna - Rising sign</span>
                        </div>
                    </div>
                    <div class="legend-section">
                        <div class="legend-section-title">Planet Abbreviations</div>
                        <div class="legend-planets">
                            <span>Su = Sun</span>
                            <span>Mo = Moon</span>
                            <span>Ma = Mars</span>
                            <span>Me = Mercury</span>
                            <span>Ju = Jupiter</span>
                            <span>Ve = Venus</span>
                            <span>Sa = Saturn</span>
                            <span>Ra = Rahu</span>
                            <span>Ke = Ketu</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Generate Varga Grid (multiple divisional charts)
     */
    generateVargaGrid(data, vargas = ['D1', 'D9', 'D2', 'D3', 'D7', 'D10', 'D12', 'D30'], style = 'south') {
        const gridSize = Math.ceil(Math.sqrt(vargas.length));
        const cellSize = 150;
        const totalSize = gridSize * cellSize;
        const originalSize = this.size;

        let svg = `<svg viewBox="0 0 ${totalSize} ${totalSize}" class="varga-grid" xmlns="http://www.w3.org/2000/svg">`;

        vargas.forEach((varga, index) => {
            const row = Math.floor(index / gridSize);
            const col = index % gridSize;
            const x = col * cellSize;
            const y = row * cellSize;

            // Temporarily resize for mini charts
            this.size = cellSize - 20;
            this.northHouseCenters = this.calculateNorthHouseCenters();
            this.southSignPositions = this.calculateSouthSignPositions();

            const chartData = data?.divisionals?.[varga];
            if (chartData) {
                const options = {
                    showDegrees: false,
                    showRetrograde: true,
                    showDignities: true,
                    showSignNumbers: false,
                    showLegend: false
                };

                const chartSvg = style === 'north'
                    ? this.generateNorthIndian(chartData, options)
                    : this.generateSouthIndian(chartData, options);

                // Extract inner SVG content
                const innerSvg = chartSvg.replace(/<svg[^>]*>/, '').replace(/<\/svg>/, '');

                svg += `<g transform="translate(${x + 10}, ${y + 10})">
                            ${innerSvg}
                            <text x="${this.size / 2}" y="${this.size + 8}" text-anchor="middle" 
                                font-size="12" font-weight="bold" fill="${this.colors.textBold}">${varga}</text>
                        </g>`;
            } else {
                svg += `<g transform="translate(${x + 10}, ${y + 10})">
                    <rect width="${this.size}" height="${this.size}" fill="${this.colors.surface}" stroke="${this.colors.line}"/>
                    <text x="${this.size / 2}" y="${this.size / 2}" text-anchor="middle" 
                        dominant-baseline="middle" font-size="12" fill="${this.colors.text}">No ${varga}</text>
                </g>`;
            }
        });

        // Restore original size
        this.size = originalSize;
        this.northHouseCenters = this.calculateNorthHouseCenters();
        this.southSignPositions = this.calculateSouthSignPositions();

        svg += '</svg>';
        return svg;
    }

    /**
     * Set chart size and recalculate positions
     */
    setSize(size) {
        this.size = size;
        this.northHouseCenters = this.calculateNorthHouseCenters();
        this.southSignPositions = this.calculateSouthSignPositions();
    }

    /**
     * Get CSS styles for the chart legend
     */
    static getStyles() {
        return `
            .chart-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 16px;
            }
            
            .chart-svg-wrapper {
                width: 100%;
                max-width: 400px;
            }
            
            .chart-svg-wrapper svg {
                width: 100%;
                height: auto;
            }
            
            .kundali-chart text {
                user-select: none;
            }
            
            .chart-legend {
                background: var(--surface-variant, #f5f5f5);
                border-radius: 8px;
                padding: 12px 16px;
                width: 100%;
                max-width: 400px;
            }
            
            .chart-legend.standalone {
                max-width: 600px;
            }
            
            .legend-title {
                font-size: 12px;
                font-weight: 600;
                color: var(--on-surface, #333);
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .legend-items {
                display: flex;
                flex-wrap: wrap;
                gap: 8px 16px;
            }
            
            .legend-item {
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 11px;
            }
            
            .legend-symbol {
                font-family: Arial, sans-serif;
                font-size: 14px;
                min-width: 36px;
            }
            
            .legend-label {
                color: var(--on-surface-variant, #666);
            }
            
            .legend-color-box {
                width: 12px;
                height: 12px;
                border-radius: 2px;
                flex-shrink: 0;
            }
            
            .legend-marker {
                font-weight: bold;
                min-width: 28px;
                font-family: Arial, sans-serif;
            }
            
            .legend-note {
                margin-top: 8px;
                padding-top: 8px;
                border-top: 1px solid var(--outline-variant, #ddd);
                color: var(--on-surface-variant, #888);
                font-size: 10px;
            }
            
            .legend-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 16px;
            }
            
            .legend-section {
                display: flex;
                flex-direction: column;
                gap: 6px;
            }
            
            .legend-section-title {
                font-size: 11px;
                font-weight: 600;
                color: var(--on-surface, #333);
                margin-bottom: 4px;
            }
            
            .legend-planets {
                display: flex;
                flex-wrap: wrap;
                gap: 4px 12px;
                font-size: 10px;
                color: var(--on-surface-variant, #666);
            }
            
            /* Responsive */
            @media (max-width: 480px) {
                .legend-items {
                    gap: 6px 12px;
                }
                
                .legend-item {
                    font-size: 10px;
                }
                
                .legend-grid {
                    grid-template-columns: 1fr;
                }
            }
        `;
    }
}

export default new Charts();
