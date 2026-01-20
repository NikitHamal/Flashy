import { renderNorthChart } from "./chart_renderer.js";
import { formatPlanetTable } from "./vedic_calculator.js";

function renderListItem(kundali, activeId) {
    const item = document.createElement("button");
    item.className = "kundali-item";
    if (kundali.id === activeId) item.classList.add("active");
    item.innerHTML = `
        <div class="kundali-name">${kundali.name || "Unnamed"}</div>
        <div class="kundali-meta">${kundali.birthDate || ""} ${kundali.birthTime || ""}</div>
        <div class="kundali-meta">${kundali.birthPlace || ""}</div>
    `;
    item.dataset.id = kundali.id;
    return item;
}

export function renderKundaliList(kundalis, activeId) {
    const list = document.getElementById("kundali-list");
    const empty = document.getElementById("kundali-empty");
    if (!list || !empty) return;

    if (!kundalis.length) {
        list.classList.add("hidden");
        empty.classList.remove("hidden");
        list.innerHTML = "";
        return;
    }

    empty.classList.add("hidden");
    list.classList.remove("hidden");
    list.innerHTML = "";
    kundalis.forEach((kundali) => {
        list.appendChild(renderListItem(kundali, activeId));
    });
}

export function renderDetail(kundali) {
    const detail = document.getElementById("kundali-detail");
    const empty = document.getElementById("astro-main-empty");
    if (!detail || !empty) return;

    if (!kundali) {
        detail.classList.add("hidden");
        empty.classList.remove("hidden");
        return;
    }

    empty.classList.add("hidden");
    detail.classList.remove("hidden");

    document.getElementById("detail-name").textContent = kundali.name || "Kundali";
    document.getElementById("detail-meta").textContent = `${kundali.birthDate} ${kundali.birthTime} • ${kundali.birthPlace} • ${kundali.gender}`;

    const chartD1 = document.getElementById("chart-d1");
    const chartD9 = document.getElementById("chart-d9");
    const planetTable = document.getElementById("planet-table");
    const dashaTable = document.getElementById("dasha-table");

    if (kundali.chart) {
        chartD1.innerHTML = renderNorthChart(kundali.chart.planets, "D1");
        chartD9.innerHTML = renderNorthChart(kundali.chart.navamsa, "D9");
        planetTable.innerHTML = renderTable(formatPlanetTable(kundali.chart.planets));
        dashaTable.innerHTML = renderDashaTable(kundali.chart.dashas);
    } else {
        chartD1.innerHTML = "<div class='muted'>Chart pending</div>";
        chartD9.innerHTML = "<div class='muted'>Chart pending</div>";
        planetTable.innerHTML = "";
        dashaTable.innerHTML = "";
    }
}

function renderTable(rows) {
    if (!rows || !rows.length) return "<div class='muted'>No data</div>";
    const headers = Object.keys(rows[0]);
    const head = headers.map((h) => `<th>${h}</th>`).join("");
    const body = rows
        .map((row) => {
            const cells = headers.map((h) => `<td>${row[h]}</td>`).join("");
            return `<tr>${cells}</tr>`;
        })
        .join("");
    return `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

function renderDashaTable(rows) {
    if (!rows || !rows.length) return "<div class='muted'>No dashas available</div>";
    const head = "<tr><th>Lord</th><th>Start</th><th>End</th><th>Years</th></tr>";
    const body = rows
        .map((row) => `<tr><td>${row.lord}</td><td>${row.start}</td><td>${row.end}</td><td>${row.years}</td></tr>`)
        .join("");
    return `<table><thead>${head}</thead><tbody>${body}</tbody></table>`;
}
