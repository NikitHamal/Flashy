import { PLANET_ORDER, PLANET_SYMBOLS } from "./constants.js";

const SIZE = 420;

const HOUSE_POSITIONS = {
    1: { x: 210, y: 70 },
    2: { x: 110, y: 40 },
    3: { x: 40, y: 110 },
    4: { x: 70, y: 210 },
    5: { x: 40, y: 310 },
    6: { x: 110, y: 380 },
    7: { x: 210, y: 350 },
    8: { x: 310, y: 380 },
    9: { x: 380, y: 310 },
    10: { x: 350, y: 210 },
    11: { x: 380, y: 110 },
    12: { x: 310, y: 40 }
};

function housePlanetLabels(planets) {
    const houses = {};
    PLANET_ORDER.forEach((planet) => {
        const data = planets[planet];
        if (!data) return;
        const key = data.house;
        if (!houses[key]) houses[key] = [];
        const suffix = data.retrograde ? "℞" : "";
        houses[key].push(`${PLANET_SYMBOLS[planet]}${suffix}`);
    });
    return houses;
}

export function renderNorthChart(planets, title = "D1") {
    const houseLabels = housePlanetLabels(planets);
    let svg = `<svg viewBox="0 0 ${SIZE} ${SIZE}" xmlns="http://www.w3.org/2000/svg" class="astro-chart">`;
    svg += `<rect x="4" y="4" width="${SIZE - 8}" height="${SIZE - 8}" fill="var(--surface)" stroke="var(--ink)" stroke-width="3"/>`;
    svg += `<line x1="4" y1="4" x2="${SIZE - 4}" y2="${SIZE - 4}" stroke="var(--ink)" stroke-width="2"/>`;
    svg += `<line x1="${SIZE - 4}" y1="4" x2="4" y2="${SIZE - 4}" stroke="var(--ink)" stroke-width="2"/>`;
    svg += `<polygon points="${SIZE / 2},8 8,${SIZE / 2} ${SIZE / 2},${SIZE - 8} ${SIZE - 8},${SIZE / 2}" fill="none" stroke="var(--ink)" stroke-width="2"/>`;

    Object.entries(HOUSE_POSITIONS).forEach(([house, pos]) => {
        const labels = houseLabels[house] || [];
        if (labels.length === 0) return;
        svg += `<text x="${pos.x}" y="${pos.y}" text-anchor="middle" class="chart-text">${labels.join(" ")}</text>`;
    });

    svg += `<text x="${SIZE - 16}" y="24" text-anchor="end" class="chart-title">${title}</text>`;
    svg += "</svg>";
    return svg;
}
