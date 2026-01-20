import engine from "./engine.js";
import {
    RASI_NAMES,
    NAKSHATRA_NAMES,
    NAKSHATRA_SPAN,
    PLANET_ORDER,
    PLANET_DIGNITIES,
    PLANET_SYMBOLS
} from "./constants.js";

const DASHA_SEQUENCE = [
    { lord: "Ketu", years: 7 },
    { lord: "Venus", years: 20 },
    { lord: "Sun", years: 6 },
    { lord: "Moon", years: 10 },
    { lord: "Mars", years: 7 },
    { lord: "Rahu", years: 18 },
    { lord: "Jupiter", years: 16 },
    { lord: "Saturn", years: 19 },
    { lord: "Mercury", years: 17 }
];

function getRasi(lon) {
    const index = Math.floor(lon / 30) % 12;
    return { index, name: RASI_NAMES[index] };
}

function getNakshatra(lon) {
    const index = Math.floor(lon / NAKSHATRA_SPAN) % 27;
    const pada = Math.floor((lon % NAKSHATRA_SPAN) / (NAKSHATRA_SPAN / 4)) + 1;
    return { index, name: NAKSHATRA_NAMES[index], pada };
}

function getHouseIndex(lagnaRasiIndex, planetRasiIndex) {
    const diff = planetRasiIndex - lagnaRasiIndex;
    return (diff + 12) % 12;
}

function getNavamsaSign(lon) {
    const signIndex = Math.floor(lon / 30) % 12;
    const degreesInSign = lon % 30;
    const navamsaIndex = Math.floor(degreesInSign / (30 / 9));

    const movable = [0, 3, 6, 9];
    const fixed = [1, 4, 7, 10];
    const dual = [2, 5, 8, 11];

    let startSign = signIndex;
    if (fixed.includes(signIndex)) {
        startSign = (signIndex + 8) % 12;
    } else if (dual.includes(signIndex)) {
        startSign = (signIndex + 4) % 12;
    }

    return (startSign + navamsaIndex) % 12;
}

function toSidereal(tropicalLon, ayanamsa) {
    let lon = tropicalLon - ayanamsa;
    if (lon < 0) lon += 360;
    return lon;
}

function enrichPlanet(planet, lon, lagnaRasiIndex) {
    const rasi = getRasi(lon);
    const nak = getNakshatra(lon);
    const degrees = lon % 30;
    const houseIndex = getHouseIndex(lagnaRasiIndex, rasi.index);
    const dignity = PLANET_DIGNITIES[planet] || {};
    const status = {
        exalted: dignity.exalted === rasi.index,
        debilitated: dignity.debilitated === rasi.index,
        own: Array.isArray(dignity.own) && dignity.own.includes(rasi.index)
    };

    return {
        name: planet,
        symbol: PLANET_SYMBOLS[planet],
        lon,
        degrees,
        rasi,
        nakshatra: nak,
        house: houseIndex + 1,
        retrograde: false,
        status
    };
}

function computeVimshottari(moonLon, birthDate) {
    const nakIndex = Math.floor(moonLon / NAKSHATRA_SPAN) % 27;
    const nakSpan = NAKSHATRA_SPAN;
    const fraction = (moonLon % nakSpan) / nakSpan;
    const dashaIndex = nakIndex % DASHA_SEQUENCE.length;
    const currentDasha = DASHA_SEQUENCE[dashaIndex];
    const remainingYears = currentDasha.years * (1 - fraction);

    const results = [];
    let cursorDate = new Date(birthDate);
    let idx = dashaIndex;
    let years = remainingYears;

    for (let i = 0; i < 6; i += 1) {
        const lord = DASHA_SEQUENCE[idx].lord;
        const duration = i === 0 ? years : DASHA_SEQUENCE[idx].years;
        const end = new Date(cursorDate);
        end.setFullYear(end.getFullYear() + Math.floor(duration));
        end.setMonth(end.getMonth() + Math.round((duration % 1) * 12));
        results.push({
            lord,
            start: cursorDate.toISOString().slice(0, 10),
            end: end.toISOString().slice(0, 10),
            years: duration.toFixed(2)
        });
        cursorDate = end;
        idx = (idx + 1) % DASHA_SEQUENCE.length;
    }
    return results;
}

export function calculateKundali(profile) {
    const dateStr = profile.birthDate;
    const timeStr = profile.birthTime;
    const tzOffset = Number(profile.timezone);
    const [year, month, day] = dateStr.split("-").map(Number);
    const [hour, minute] = timeStr.split(":").map(Number);

    const totalMinutes = (hour * 60 + minute) - (tzOffset * 60);
    const utcDate = new Date(Date.UTC(year, month - 1, day, 0, totalMinutes));
    const lat = Number(profile.latitude);
    const lng = Number(profile.longitude);

    const tropical = engine.calculatePlanets(utcDate);
    const ayanamsa = engine.getAyanamsa(utcDate);
    const lagnaTropical = engine.calculateLagna(utcDate, lat, lng);
    const lagnaSidereal = toSidereal(lagnaTropical, ayanamsa);
    const lagna = enrichPlanet("Lagna", lagnaSidereal, getRasi(lagnaSidereal).index);

    const lagnaRasiIndex = lagna.rasi.index;
    const planets = {};

    Object.entries(tropical).forEach(([planet, data]) => {
        const lon = toSidereal(data.elon, ayanamsa);
        planets[planet] = enrichPlanet(planet, lon, lagnaRasiIndex);
        planets[planet].retrograde = data.speed < 0;
    });

    const navamsa = {};
    const navLagnaSign = getNavamsaSign(lagnaSidereal);
    Object.keys(planets).forEach((planet) => {
        const navSign = getNavamsaSign(planets[planet].lon);
        navamsa[planet] = {
            ...planets[planet],
            rasi: { index: navSign, name: RASI_NAMES[navSign] },
            house: getHouseIndex(navLagnaSign, navSign) + 1
        };
    });

    const houses = [];
    for (let i = 0; i < 12; i += 1) {
        houses.push({
            house: i + 1,
            sign: RASI_NAMES[(lagnaRasiIndex + i) % 12]
        });
    }

    const dashas = planets.Moon ? computeVimshottari(planets.Moon.lon, utcDate) : [];

    const summaryParts = [];
    if (lagna && lagna.rasi) summaryParts.push(`Lagna ${lagna.rasi.name}`);
    if (planets.Moon && planets.Moon.rasi) summaryParts.push(`Moon ${planets.Moon.rasi.name}`);
    if (planets.Sun && planets.Sun.rasi) summaryParts.push(`Sun ${planets.Sun.rasi.name}`);
    const summary = summaryParts.join(", ");

    return {
        profile,
        ayanamsa,
        lagna,
        planets,
        houses,
        navamsa,
        dashas,
        summary
    };
}

export function formatPlanetTable(planets) {
    if (!planets) return [];
    return PLANET_ORDER.map((planet) => {
        const data = planets[planet];
        if (!data || !data.rasi || !data.nakshatra) return null;
        return {
            planet: planet,
            sign: data.rasi.name || "Unknown",
            house: data.house || "?",
            nakshatra: `${data.nakshatra.name || "Unknown"} ${data.nakshatra.pada || ""}`,
            degrees: typeof data.degrees === "number" ? data.degrees.toFixed(2) : "0.00",
            retrograde: data.retrograde ? "Yes" : "No"
        };
    }).filter(Boolean);
}
