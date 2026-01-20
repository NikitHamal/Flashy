/**
 * Astro Charts Module
 * 
 * Handles rendering of Vedic astrology charts using SVG.
 * Supports North Indian and South Indian chart styles.
 */

const AstroCharts = {
    // Sign names
    RASI_NAMES: [
        'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
        'Tula', 'Vrishchika', 'Dhanu', 'Makara', 'Kumbha', 'Meena'
    ],
    
    RASI_SYMBOLS: ['Ar', 'Ta', 'Ge', 'Cn', 'Le', 'Vi', 'Li', 'Sc', 'Sg', 'Cp', 'Aq', 'Pi'],
    
    // Planet abbreviations
    PLANET_ABBR: {
        'Sun': 'Su', 'Moon': 'Mo', 'Mars': 'Ma', 'Mercury': 'Me',
        'Jupiter': 'Ju', 'Venus': 'Ve', 'Saturn': 'Sa', 'Rahu': 'Ra', 'Ketu': 'Ke',
        'Lagna': 'Asc'
    },
    
    // Planet colors
    PLANET_COLORS: {
        'Sun': '#ff8c00',
        'Moon': '#708090',
        'Mars': '#dc143c',
        'Mercury': '#32cd32',
        'Jupiter': '#daa520',
        'Venus': '#ff69b4',
        'Saturn': '#4169e1',
        'Rahu': '#696969',
        'Ketu': '#8b4513',
        'Lagna': '#1a1a1a'
    },
    
    /**
     * Render a North Indian style chart
     */
    renderNorthIndian(container, chartData, options = {}) {
        const size = options.size || 400;
        const padding = 10;
        const innerSize = size - (padding * 2);
        
        // Clear container
        container.innerHTML = '';
        
        // Create SVG
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', size);
        svg.setAttribute('height', size);
        svg.setAttribute('viewBox', `0 0 ${size} ${size}`);
        svg.style.fontFamily = 'Inter, sans-serif';
        
        // Background
        const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        bg.setAttribute('width', size);
        bg.setAttribute('height', size);
        bg.setAttribute('fill', '#fffef5');
        svg.appendChild(bg);
        
        // Draw diamond structure
        const center = size / 2;
        const half = innerSize / 2;
        
        // Main outer square
        const outerSquare = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        outerSquare.setAttribute('x', padding);
        outerSquare.setAttribute('y', padding);
        outerSquare.setAttribute('width', innerSize);
        outerSquare.setAttribute('height', innerSize);
        outerSquare.setAttribute('fill', 'none');
        outerSquare.setAttribute('stroke', '#1a1a1a');
        outerSquare.setAttribute('stroke-width', '3');
        svg.appendChild(outerSquare);
        
        // Draw diagonals
        const diag1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        diag1.setAttribute('x1', padding);
        diag1.setAttribute('y1', padding);
        diag1.setAttribute('x2', size - padding);
        diag1.setAttribute('y2', size - padding);
        diag1.setAttribute('stroke', '#1a1a1a');
        diag1.setAttribute('stroke-width', '3');
        svg.appendChild(diag1);
        
        const diag2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        diag2.setAttribute('x1', size - padding);
        diag2.setAttribute('y1', padding);
        diag2.setAttribute('x2', padding);
        diag2.setAttribute('y2', size - padding);
        diag2.setAttribute('stroke', '#1a1a1a');
        diag2.setAttribute('stroke-width', '3');
        svg.appendChild(diag2);
        
        // Draw inner diamond
        const diamondPoints = [
            `${center},${padding}`,
            `${size - padding},${center}`,
            `${center},${size - padding}`,
            `${padding},${center}`
        ].join(' ');
        
        const diamond = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        diamond.setAttribute('points', diamondPoints);
        diamond.setAttribute('fill', 'none');
        diamond.setAttribute('stroke', '#1a1a1a');
        diamond.setAttribute('stroke-width', '3');
        svg.appendChild(diamond);
        
        // House positions in North Indian chart (Lagna is always house 1 in center top)
        // House mapping based on Lagna position
        const lagnaSign = chartData.lagna?.rasi?.index || 0;
        
        // North Indian house centers (relative positions)
        const houseCenters = this._getNorthIndianHouseCenters(center, half, padding);
        
        // Group planets by house
        const planetsByHouse = this._groupPlanetsByHouse(chartData, lagnaSign);
        
        // Render planets in each house
        for (let house = 1; house <= 12; house++) {
            const houseCenter = houseCenters[house];
            const planetsInHouse = planetsByHouse[house] || [];
            
            // Add house number (small)
            const houseLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            houseLabel.setAttribute('x', houseCenter.labelX);
            houseLabel.setAttribute('y', houseCenter.labelY);
            houseLabel.setAttribute('text-anchor', 'middle');
            houseLabel.setAttribute('font-size', '10');
            houseLabel.setAttribute('fill', '#999');
            houseLabel.textContent = house.toString();
            svg.appendChild(houseLabel);
            
            // Render planets
            this._renderPlanetsInHouse(svg, planetsInHouse, houseCenter.x, houseCenter.y, houseCenter.width);
        }
        
        container.appendChild(svg);
    },
    
    /**
     * Render a South Indian style chart
     */
    renderSouthIndian(container, chartData, options = {}) {
        const size = options.size || 400;
        const padding = 10;
        const cellSize = (size - (padding * 2)) / 4;
        
        container.innerHTML = '';
        
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', size);
        svg.setAttribute('height', size);
        svg.setAttribute('viewBox', `0 0 ${size} ${size}`);
        svg.style.fontFamily = 'Inter, sans-serif';
        
        // Background
        const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        bg.setAttribute('width', size);
        bg.setAttribute('height', size);
        bg.setAttribute('fill', '#fffef5');
        svg.appendChild(bg);
        
        // South Indian grid - signs are fixed, houses rotate
        // Grid layout (sign indices):
        // [11, 0,  1,  2 ]
        // [10, -,  -,  3 ]
        // [9,  -,  -,  4 ]
        // [8,  7,  6,  5 ]
        
        const signGrid = [
            [11, 0, 1, 2],
            [10, -1, -1, 3],
            [9, -1, -1, 4],
            [8, 7, 6, 5]
        ];
        
        const lagnaSign = chartData.lagna?.rasi?.index || 0;
        
        // Draw grid
        for (let row = 0; row < 4; row++) {
            for (let col = 0; col < 4; col++) {
                const signIdx = signGrid[row][col];
                if (signIdx === -1) continue; // Center cells
                
                const x = padding + (col * cellSize);
                const y = padding + (row * cellSize);
                
                // Cell border
                const cell = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                cell.setAttribute('x', x);
                cell.setAttribute('y', y);
                cell.setAttribute('width', cellSize);
                cell.setAttribute('height', cellSize);
                cell.setAttribute('fill', signIdx === lagnaSign ? '#ffe66d' : 'none');
                cell.setAttribute('stroke', '#1a1a1a');
                cell.setAttribute('stroke-width', '2');
                svg.appendChild(cell);
                
                // Sign symbol
                const signLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                signLabel.setAttribute('x', x + 8);
                signLabel.setAttribute('y', y + 14);
                signLabel.setAttribute('font-size', '10');
                signLabel.setAttribute('fill', '#666');
                signLabel.textContent = this.RASI_SYMBOLS[signIdx];
                svg.appendChild(signLabel);
                
                // House number
                const house = ((signIdx - lagnaSign + 12) % 12) + 1;
                const houseLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                houseLabel.setAttribute('x', x + cellSize - 8);
                houseLabel.setAttribute('y', y + 14);
                houseLabel.setAttribute('text-anchor', 'end');
                houseLabel.setAttribute('font-size', '10');
                houseLabel.setAttribute('fill', '#999');
                houseLabel.textContent = house.toString();
                svg.appendChild(houseLabel);
                
                // Get planets in this sign
                const planetsInSign = this._getPlanetsInSign(chartData, signIdx);
                this._renderPlanetsInCell(svg, planetsInSign, x, y + 20, cellSize);
            }
        }
        
        // Center cells - show chart info
        const centerX = padding + cellSize;
        const centerY = padding + cellSize;
        const centerSize = cellSize * 2;
        
        const centerRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        centerRect.setAttribute('x', centerX);
        centerRect.setAttribute('y', centerY);
        centerRect.setAttribute('width', centerSize);
        centerRect.setAttribute('height', centerSize);
        centerRect.setAttribute('fill', '#f5f5f5');
        centerRect.setAttribute('stroke', '#1a1a1a');
        centerRect.setAttribute('stroke-width', '2');
        svg.appendChild(centerRect);
        
        // Chart title in center
        const title = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        title.setAttribute('x', centerX + centerSize / 2);
        title.setAttribute('y', centerY + centerSize / 2 - 10);
        title.setAttribute('text-anchor', 'middle');
        title.setAttribute('font-size', '14');
        title.setAttribute('font-weight', 'bold');
        title.textContent = 'Rasi Chart';
        svg.appendChild(title);
        
        const lagnaText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        lagnaText.setAttribute('x', centerX + centerSize / 2);
        lagnaText.setAttribute('y', centerY + centerSize / 2 + 10);
        lagnaText.setAttribute('text-anchor', 'middle');
        lagnaText.setAttribute('font-size', '12');
        lagnaText.setAttribute('fill', '#666');
        lagnaText.textContent = `Lagna: ${this.RASI_NAMES[lagnaSign]}`;
        svg.appendChild(lagnaText);
        
        container.appendChild(svg);
    },
    
    /**
     * Get North Indian house center positions
     */
    _getNorthIndianHouseCenters(center, half, padding) {
        const q = half / 2;
        return {
            1:  { x: center, y: center - half + q, width: q * 1.5, labelX: center, labelY: padding + 15 },
            2:  { x: center - q, y: center - q, width: q, labelX: padding + 30, labelY: padding + 40 },
            3:  { x: padding + q, y: center - q, width: q, labelX: padding + 15, labelY: center - q },
            4:  { x: center - half + q, y: center, width: q * 1.5, labelX: padding + 15, labelY: center },
            5:  { x: padding + q, y: center + q, width: q, labelX: padding + 15, labelY: center + q + 30 },
            6:  { x: center - q, y: center + q, width: q, labelX: padding + 30, labelY: center + half - 10 },
            7:  { x: center, y: center + half - q, width: q * 1.5, labelX: center, labelY: center + half - 5 },
            8:  { x: center + q, y: center + q, width: q, labelX: center + half - 30, labelY: center + half - 10 },
            9:  { x: center + half - q, y: center + q, width: q, labelX: center + half - 15, labelY: center + q + 30 },
            10: { x: center + half - q, y: center, width: q * 1.5, labelX: center + half - 15, labelY: center },
            11: { x: center + half - q, y: center - q, width: q, labelX: center + half - 15, labelY: center - q },
            12: { x: center + q, y: center - q, width: q, labelX: center + half - 30, labelY: padding + 40 }
        };
    },
    
    /**
     * Group planets by house number
     */
    _groupPlanetsByHouse(chartData, lagnaSign) {
        const planetsByHouse = {};
        
        // Add Lagna
        const lagnaHouse = 1;
        if (!planetsByHouse[lagnaHouse]) planetsByHouse[lagnaHouse] = [];
        planetsByHouse[lagnaHouse].push({ name: 'Lagna', abbr: 'Asc' });
        
        // Add planets
        const planets = chartData.planets || {};
        for (const [name, data] of Object.entries(planets)) {
            const signIdx = data.rasi?.index ?? data.sign ?? 0;
            const house = ((signIdx - lagnaSign + 12) % 12) + 1;
            
            if (!planetsByHouse[house]) planetsByHouse[house] = [];
            
            planetsByHouse[house].push({
                name,
                abbr: this.PLANET_ABBR[name] || name.substr(0, 2),
                retrograde: data.is_retrograde || data.retrograde,
                dignity: data.dignity
            });
        }
        
        return planetsByHouse;
    },
    
    /**
     * Get planets in a specific sign
     */
    _getPlanetsInSign(chartData, signIdx) {
        const planets = [];
        
        // Check Lagna
        const lagnaSign = chartData.lagna?.rasi?.index ?? 0;
        if (lagnaSign === signIdx) {
            planets.push({ name: 'Lagna', abbr: 'Asc' });
        }
        
        // Check planets
        const chartPlanets = chartData.planets || {};
        for (const [name, data] of Object.entries(chartPlanets)) {
            const pSign = data.rasi?.index ?? data.sign ?? 0;
            if (pSign === signIdx) {
                planets.push({
                    name,
                    abbr: this.PLANET_ABBR[name] || name.substr(0, 2),
                    retrograde: data.is_retrograde || data.retrograde,
                    dignity: data.dignity
                });
            }
        }
        
        return planets;
    },
    
    /**
     * Render planets in a house (North Indian)
     */
    _renderPlanetsInHouse(svg, planets, cx, cy, maxWidth) {
        if (!planets.length) return;
        
        const spacing = 22;
        const startX = cx - ((planets.length - 1) * spacing) / 2;
        
        planets.forEach((planet, idx) => {
            const x = startX + (idx * spacing);
            const color = this.PLANET_COLORS[planet.name] || '#1a1a1a';
            
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', x);
            text.setAttribute('y', cy);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('font-size', '12');
            text.setAttribute('font-weight', '600');
            text.setAttribute('fill', color);
            
            let label = planet.abbr;
            if (planet.retrograde) label += 'ᴿ';
            if (planet.dignity === 'exalted') label += '↑';
            if (planet.dignity === 'debilitated') label += '↓';
            
            text.textContent = label;
            svg.appendChild(text);
        });
    },
    
    /**
     * Render planets in a cell (South Indian)
     */
    _renderPlanetsInCell(svg, planets, x, y, cellWidth) {
        if (!planets.length) return;
        
        const lineHeight = 12;
        const maxPerLine = 3;
        
        planets.forEach((planet, idx) => {
            const row = Math.floor(idx / maxPerLine);
            const col = idx % maxPerLine;
            const px = x + 8 + (col * 25);
            const py = y + 10 + (row * lineHeight);
            
            const color = this.PLANET_COLORS[planet.name] || '#1a1a1a';
            
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', px);
            text.setAttribute('y', py);
            text.setAttribute('font-size', '11');
            text.setAttribute('font-weight', '600');
            text.setAttribute('fill', color);
            
            let label = planet.abbr;
            if (planet.retrograde) label += 'ᴿ';
            
            text.textContent = label;
            svg.appendChild(text);
        });
    },
    
    /**
     * Render chart legend
     */
    renderLegend(container, chartData) {
        container.innerHTML = '';
        
        const planets = chartData.planets || {};
        
        Object.entries(planets).forEach(([name, data]) => {
            const item = document.createElement('div');
            item.className = 'legend-item';
            item.style.cssText = 'display:flex;align-items:center;gap:6px;font-size:12px;';
            
            const dot = document.createElement('span');
            dot.style.cssText = `width:12px;height:12px;border-radius:50%;background:${this.PLANET_COLORS[name]};border:2px solid #1a1a1a;`;
            
            const label = document.createElement('span');
            let text = `${name}: ${data.rasi?.name || this.RASI_NAMES[data.sign || 0]}`;
            if (data.is_retrograde || data.retrograde) text += ' (R)';
            label.textContent = text;
            
            item.appendChild(dot);
            item.appendChild(label);
            container.appendChild(item);
        });
    }
};
