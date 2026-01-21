import Engine from './engine.js';
import DashaEngine from './dasha_engine.js';
import Ashtakavarga from './ashtakavarga.js';
import SpecialLagnas from './special_lagnas.js';
import JaiminiEngine from './jaimini.js';
import Upagrahas from './upagrahas.js';
import PanchangEngine from './panchang_engine.js';
import PlanetStateEngine from './planet_states.js';
import {
    RASI_NAMES,
    NAKSHATRA_NAMES,
    NAKSHATRA_SPAN,
    TITHI_NAMES,
    NITYA_YOGA_NAMES,
    KARANA_NAMES
} from './constants.js';

class Vedic {
    constructor() {
        this.dashaEngine = new DashaEngine();
        // Reference centralized constants
        this.rasis = RASI_NAMES;
        this.nakshatras = NAKSHATRA_NAMES;
        this.tithis = TITHI_NAMES;
        this.nityaYogas = NITYA_YOGA_NAMES;
        this.karanas = KARANA_NAMES;
    }

    /**
     * Set the Ayanamsa system
     * @param {string} system - System name (Lahiri, Raman, etc.)
     */
    setAyanamsaSystem(system) {
        Engine.setAyanamsaSystem(system);
    }

    calculatePanchang(date, location) {
        // Reuse calculate() to get basic positions
        const data = this.calculate(date, location);
        const sunLon = data.planets.Sun.lon;
        const moonLon = data.planets.Moon.lon;
        const moonNakshatra = data.planets.Moon.nakshatra;
        
        return PanchangEngine.calculate(date, location, sunLon, moonLon, moonNakshatra);
    }

    calculate(date, location) {
        // 1. Get Tropical Positions
        const tropical = Engine.calculatePlanets(date);

        // 2. Calculate Ayanamsa
        const ayanamsa = Engine.getAyanamsa(date);

        // 3. Convert to Sidereal
        const sidereal = {};
        for (const [planet, coords] of Object.entries(tropical)) {
            let lon = coords.elon - ayanamsa;
            if (lon < 0) lon += 360;

            sidereal[planet] = {
                lon: lon,
                lat: coords.elat,
                dist: coords.dist,
                dec: coords.dec, // Declination for Dig/Kala Bala
                speed: coords.speed, // Velocity for Chesta Bala
                rasi: this.getRasi(lon),
                nakshatra: this.getNakshatra(lon)
            };
        }

        // 4. Calculate Lagna (Ascendant) and MC
        const lagnaTropical = Engine.calculateLagna(date, location.lat, location.lng);
        let lagnaSidereal = lagnaTropical - ayanamsa;
        if (lagnaSidereal < 0) lagnaSidereal += 360;

        const mcTropical = Engine.calculateMC(date, location.lng);
        let mcSidereal = mcTropical - ayanamsa;
        if (mcSidereal < 0) mcSidereal += 360;

        const lagnaObj = {
            lon: lagnaSidereal,
            rasi: this.getRasi(lagnaSidereal),
            nakshatra: this.getNakshatra(lagnaSidereal)
        };

        const vargas = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 16, 20, 24, 27, 30, 40, 45, 60, 81, 108, 144];
        const divisionalCharts = {};

        vargas.forEach(v => {
            divisionalCharts['D' + v] = this.calculateDivisionalChart(sidereal, lagnaObj, v);
        });

        // 5. Post-process planets (Combustion, Vargottama, Dignity)
        const d9Planets = divisionalCharts.D9.planets;
        PlanetStateEngine.enrichPlanetStates(sidereal, d9Planets);

        // Propagate common properties (Combustion, Vargottama, Dignity) to all divisional charts
        // Dignity is Varga-dependent, so we recalculate it for each varga planet if needed,
        // but Combustion and Vargottama are D1/D9 properties usually carried over.
        for (const [p, data] of Object.entries(sidereal)) {
             vargas.forEach(v => {
                const targetP = divisionalCharts['D' + v].planets[p];
                if (targetP) {
                    targetP.isCombust = data.isCombust;
                    targetP.isVargottama = data.isVargottama;
                    // Note: Dignity in D-charts is relative to that chart's signs
                    // We can enrich it here if we want full analysis in every varga
                    // Using centralized utility:
                    // import { getDignity } from './constants.js' (Need to make sure it's available or use PlanetStateEngine helper)
                }
            });
        }

        // 6. Jaimini Calculations
        const jaimini = JaiminiEngine.calculateJaiminiChart({
            planets: sidereal,
            lagnaRasi: lagnaObj.rasi.index,
            navamshaPositions: divisionalCharts.D9.planets
        });
        
        // Enrich planets with Jaimini Karakas (AK, AmK, etc.)
        const planetToKaraka = jaimini.charaKarakas.planetToKaraka;
        for (const [p, karaka] of Object.entries(planetToKaraka)) {
            if (sidereal[p]) {
                sidereal[p].jaiminiKaraka = karaka;
                // Propagate to Vargas
                vargas.forEach(v => {
                    if (divisionalCharts['D' + v].planets[p]) {
                        divisionalCharts['D' + v].planets[p].jaiminiKaraka = karaka;
                    }
                });
            }
        }

        // 7. Calculate all Dashas
        /* 
           We keep result.dashas as Vimshottari for backward compatibility with existing views.
           We add result.dashaDetails for the new multi-system view.
        */
        const vimshottari = this.dashaEngine.calculateVimshottari(sidereal.Moon.lon, date);
        const yogini = this.dashaEngine.calculateYogini(sidereal.Moon.lon, date);
        const ashtottari = this.dashaEngine.calculateAshtottari(sidereal.Moon.lon, date, sidereal.Moon.nakshatra.index, lagnaObj.nakshatra.index);
        const shodashottari = this.dashaEngine.calculateShodashottari(sidereal.Moon.lon, date, sidereal.Moon.nakshatra.index);
        const dwadashottari = this.dashaEngine.calculateDwadashottari(sidereal.Moon.lon, date);
        const chara = this.dashaEngine.calculateChara(sidereal, lagnaObj, date);
        const kalachakra = this.dashaEngine.calculateKalachakra(sidereal.Moon.lon, date);
        const narayana = this.dashaEngine.calculateNarayana(sidereal, lagnaObj, date);

        // 8. Calculate Special Lagnas (Arudha, Hora, Ghati, Varnada, etc.)
        const specialLagnas = SpecialLagnas.calculate({
            planets: sidereal,
            lagna: lagnaObj,
            date: date,
            location: location,
            ayanamsa: ayanamsa,
            jaimini: jaimini
        });

        const upagrahaData = Upagrahas.calculateUpagrahas(sidereal.Sun.lon);
        const mandiGulika = Upagrahas.calculateMandiGulika(date, location, ayanamsa);
        const allUpagrahas = { ...upagrahaData, ...mandiGulika };

        const bhavaChalit = this.calculateBhavaChalit(lagnaSidereal, mcSidereal);
        const { sunrise, sunset } = Engine.getSunriseSunset(date, location.lat, location.lng);

        const result = {
            date: date,
            location: location,
            sunrise,
            sunset,
            ayanamsa: ayanamsa,
            ayanamsaName: Engine.getAyanamsaSystem(),
            lagna: lagnaObj,
            mc: mcSidereal,
            planets: sidereal,
            houses: this.calculateHouses(lagnaSidereal),
            bhavaChalit: bhavaChalit,
            divisionals: divisionalCharts,
            dashas: vimshottari, // Backward compatibility
            dashaDetails: {
                vimshottari: vimshottari,
                yogini: yogini,
                ashtottari: ashtottari,
                shodashottari: shodashottari,
                dwadashottari: dwadashottari,
                chara: chara,
                kalachakra: kalachakra,
                narayana: narayana
            },
            jaimini: jaimini,
            specialLagnas: specialLagnas,
            upagrahas: allUpagrahas,
            ashtakavarga: Ashtakavarga.calculate(sidereal, lagnaObj)
        };

        return result;
    }

    calculateDivisionalChart(planets, lagna, vargaNum) {
        const divPlanets = {};

        for (const [p, data] of Object.entries(planets)) {
            divPlanets[p] = this.getVargaPosition(data.lon, vargaNum);
        }

        const divLagna = this.getVargaPosition(lagna.lon, vargaNum);

        return {
            planets: divPlanets,
            lagna: divLagna,
            houses: this.calculateHouses(divLagna.lon)
        };
    }

    /**
     * Sripati Bhava Chalit (House Cusps)
     * Trisects the arcs between Lagna, IC, Descendant, MC
     */
    calculateBhavaChalit(lagna, mc) {
        const ic = (mc + 180) % 360;
        const desc = (lagna + 180) % 360;

        const cusps = new Array(13);
        cusps[1] = lagna;
        cusps[4] = ic;
        cusps[7] = desc;
        cusps[10] = mc;

        const getArc = (start, end) => {
            let diff = end - start;
            if (diff < 0) diff += 360;
            return diff;
        };

        const trisection = (startHouse, endHouse, startLon, endLon) => {
            const arc = getArc(startLon, endLon);
            const step = arc / 3;
            cusps[startHouse + 1] = (startLon + step) % 360;
            cusps[startHouse + 2] = (startLon + 2 * step) % 360;
        };

        // 1-4, 4-7, 7-10, 10-1
        trisection(1, 4, cusps[1], cusps[4]);
        trisection(4, 7, cusps[4], cusps[7]);
        trisection(7, 10, cusps[7], cusps[10]);
        trisection(10, 1, cusps[10], cusps[1]);

        const houses = {};
        for (let i = 1; i <= 12; i++) {
            const mid = cusps[i];
            const start = (mid - (getArc(cusps[i === 1 ? 12 : i - 1], mid) / 2) + 360) % 360;
            const end = (mid + (getArc(mid, cusps[i === 12 ? 1 : i + 1]) / 2)) % 360;

            houses[i] = {
                cusp: mid,
                start: start,
                end: end,
                sign: this.rasis[Math.floor(mid / 30)],
                rasiIndex: Math.floor(mid / 30)
            };
        }

        return houses;
    }

    getVargaPosition(lon, varga) {
        const signIdx = Math.floor(lon / 30);
        const signPos = lon % 30;
        const isOdd = (signIdx % 2 === 0);

        const toLon = (idx) => {
            let normalizedIdx = idx % 12;
            if (normalizedIdx < 0) normalizedIdx += 12;
            return normalizedIdx * 30 + 15;
        };

        // Standard Navamsha helper
        const getNavRasi = (l) => {
            const sIdx = Math.floor(l / 30);
            const p = Math.floor((l % 30) / 3.3333333333);
            const st = [0, 9, 6, 3][sIdx % 4];
            return (st + p) % 12;
        };

        // Config-driven strategy for standard Parashara vargas
        const vargaConfigs = {
            1: () => lon,
            2: () => {
                const firstHalf = signPos < 15;
                const sign = isOdd ? (firstHalf ? 4 : 3) : (firstHalf ? 3 : 4);
                return toLon(sign);
            },
            3: () => toLon(signIdx + (Math.floor(signPos / 10) * 4)),
            4: () => toLon(signIdx + (Math.floor(signPos / 7.5) * 3)),
            5: () => toLon((isOdd ? 0 : 7) + Math.floor(signPos / 6)),
            6: () => toLon((isOdd ? 0 : 6) + Math.floor(signPos / 5)),
            7: () => toLon((isOdd ? signIdx : signIdx + 6) + Math.floor(signPos / (30 / 7))),
            8: () => {
                const start = [0, 8, 4][signIdx % 3];
                return toLon(start + Math.floor(signPos / 3.75));
            },
            9: () => toLon(getNavRasi(lon)),
            10: () => toLon((isOdd ? signIdx : signIdx + 8) + Math.floor(signPos / 3)),
            11: () => toLon((signIdx - Math.floor(signPos / (30 / 11)) + 12) % 12),
            12: () => toLon(signIdx + Math.floor(signPos / 2.5)),
            16: () => {
                const start = [0, 4, 8][signIdx % 3];
                return toLon(start + Math.floor(signPos / (30 / 16)));
            },
            20: () => {
                const start = [0, 8, 4][signIdx % 3];
                return toLon(start + Math.floor(signPos / (30 / 20)));
            },
            24: () => toLon((isOdd ? 4 : 3) + Math.floor(signPos / (30 / 24))),
            27: () => toLon((signIdx % 4) * 3 + Math.floor(signPos / (30 / 27))),
            30: () => {
                const oddTable = [[5, 0], [10, 10], [18, 8], [25, 2], [30, 6]];
                const evenTable = [[5, 1], [12, 5], [20, 11], [25, 9], [30, 7]];
                const table = isOdd ? oddTable : evenTable;
                const sign = table.find(entry => signPos < entry[0])[1];
                return toLon(sign);
            },
            40: () => toLon((isOdd ? 0 : 6) + Math.floor(signPos / (30 / 40))),
            45: () => {
                const start = [0, 4, 8][signIdx % 3];
                return toLon(start + Math.floor(signPos / (30 / 45)));
            },
            60: () => toLon(signIdx + Math.floor(signPos / 0.5)),
            81: () => {
                const r1 = getNavRasi(lon);
                const r2 = getNavRasi(r1 * 30 + (lon % 3.3333333333) * 9);
                return toLon(r2);
            },
            108: () => toLon(Math.floor(lon / 3.3333333333) + Math.floor(((lon % 3.3333333333) * 9) / 2.5)),
            144: () => {
                const r1 = (signIdx + Math.floor(signPos / 2.5)) % 12;
                const r2 = (r1 + Math.floor(((signPos % 2.5) * 12) / 2.5)) % 12;
                return toLon(r2);
            }
        };

        const vLon = vargaConfigs[varga] ? vargaConfigs[varga]() : (lon * varga) % 360;

        return {
            lon: vLon,
            rasi: this.getRasi(vLon)
        };
    }
    // Old calculateVimshottari removed. Delegated to DashaEngine.
    calculateHouses(ascendantLon) {
        const ascRasiIndex = Math.floor(ascendantLon / 30);
        const houses = {};

        for (let i = 1; i <= 12; i++) {
            let signIndex = (ascRasiIndex + i - 1) % 12;
            houses[i] = {
                sign: this.rasis[signIndex],
                signIndex: signIndex
            };
        }

        return houses;
    }

    getRasi(lon) {
        if (isNaN(lon)) return { index: 0, name: 'Error', degrees: 0 };
        // Handle wrap-around
        let normalizedLon = lon % 360;
        if (normalizedLon < 0) normalizedLon += 360;

        const index = Math.floor(normalizedLon / 30) % 12;
        return {
            index: index,
            name: this.rasis[index],
            degrees: normalizedLon % 30
        };
    }

    getNakshatra(lon) {
        const index = Math.floor(lon / NAKSHATRA_SPAN);
        const posInNak = lon % NAKSHATRA_SPAN;
        // Pada calculation: 4 padas per nakshatra (each pada = 3°20')
        const pada = Math.floor(posInNak / (NAKSHATRA_SPAN / 4)) + 1;

        return {
            index: index,
            name: this.nakshatras[index],
            pada: pada
        };
    }
}

export default new Vedic();