/**
 * ============================================================================
 * VARSHAPHALA (SOLAR RETURN) ENGINE
 * ============================================================================
 *
 * Calculates the Varshaphala (Annual Horoscope) based on the Tajika system.
 * The Varshaphala chart is cast for the exact moment when the transiting Sun
 * returns to its natal position each year.
 *
 * Features:
 * - Precise Solar Return moment calculation using binary search
 * - Muntha (Annual Lagna) calculation
 * - Sahams (Arabic Parts/Sensitive Points)
 * - Tajika Yogas detection
 * - Panchadhikari (Five Lordships) analysis
 * - Hadda (Ptolemaic Terms) and Drekkana considerations
 * - Year lord (Varshesh) calculation
 *
 * References:
 * - Tajika Neelakanthi
 * - Varshaphala by Dr. K.S. Charak
 * - Uttara Kalamrita
 *
 * @module varshaphala
 * @version 1.0.0
 */

import Engine from './engine.js';
import I18n from '../core/i18n.js';
import {
    RASI_NAMES,
    SIGN_LORDS,
    SAPTA_GRAHA,
    NAVAGRAHA,
    NAKSHATRA_NAMES,
    NAKSHATRA_SPAN
} from './constants.js';

/**
 * Tajika Yoga definitions
 * Based on the angular distance between planets
 */
const TAJIKA_ASPECTS = {
    conjunction: { min: 0, max: 12, name: 'Yuti', strength: 'full' },
    opposition: { min: 168, max: 192, name: 'Pratiyuti', strength: 'full' },
    trine: { min: 108, max: 132, name: 'Trikona', strength: 'high' },
    square: { min: 78, max: 102, name: 'Chaturasra', strength: 'medium' },
    sextile: { min: 48, max: 72, name: 'Shashtashtaka', strength: 'low' }
};

/**
 * Muntha cycle - Annual Lagna progresses 1 sign per year
 */
const MUNTHA_SIGNIFICATIONS = {
    1: 'Self, health, new beginnings',
    2: 'Wealth, family, speech',
    3: 'Courage, siblings, short journeys',
    4: 'Home, mother, comfort, property',
    5: 'Intelligence, children, romance',
    6: 'Enemies, health issues, service',
    7: 'Partnership, marriage, business',
    8: 'Obstacles, transformation, longevity',
    9: 'Fortune, father, long journeys, dharma',
    10: 'Career, status, profession',
    11: 'Gains, friends, aspirations',
    12: 'Losses, expenses, spirituality'
};

/**
 * Saham (Arabic Parts) definitions
 * Formula: Saham = Lagna + A - B (adjusted for day/night)
 */
const SAHAMS = {
    punya: { name: 'Punya Saham', formula: { day: ['Moon', 'Sun'], night: ['Sun', 'Moon'] },
             meaning: 'Fortune, merit, general auspiciousness' },
    vidya: { name: 'Vidya Saham', formula: { day: ['Jupiter', 'Mercury'], night: ['Mercury', 'Jupiter'] },
             meaning: 'Education, knowledge, learning' },
    yashas: { name: 'Yashas Saham', formula: { day: ['Sun', 'Saturn'], night: ['Saturn', 'Sun'] },
             meaning: 'Fame, reputation, honor' },
    mitra: { name: 'Mitra Saham', formula: { day: ['Jupiter', 'Saturn'], night: ['Saturn', 'Jupiter'] },
             meaning: 'Friends, allies, social relationships' },
    gaurava: { name: 'Gaurava Saham', formula: { day: ['Sun', 'Jupiter'], night: ['Jupiter', 'Sun'] },
             meaning: 'Respect, dignity, authority' },
    pitru: { name: 'Pitru Saham', formula: { day: ['Saturn', 'Sun'], night: ['Sun', 'Saturn'] },
             meaning: 'Father, ancestral matters' },
    matru: { name: 'Matru Saham', formula: { day: ['Moon', 'Venus'], night: ['Venus', 'Moon'] },
             meaning: 'Mother, maternal happiness' },
    bhratru: { name: 'Bhratru Saham', formula: { day: ['Jupiter', 'Mars'], night: ['Mars', 'Jupiter'] },
             meaning: 'Siblings, brothers' },
    putra: { name: 'Putra Saham', formula: { day: ['Jupiter', 'Moon'], night: ['Moon', 'Jupiter'] },
             meaning: 'Children, progeny' },
    karma: { name: 'Karma Saham', formula: { day: ['Mars', 'Mercury'], night: ['Mercury', 'Mars'] },
             meaning: 'Actions, profession, work' },
    vivaha: { name: 'Vivaha Saham', formula: { day: ['Venus', 'Saturn'], night: ['Saturn', 'Venus'] },
             meaning: 'Marriage, partnership' },
    roga: { name: 'Roga Saham', formula: { day: ['Saturn', 'Mars'], night: ['Mars', 'Saturn'] },
             meaning: 'Disease, health challenges' },
    mrityu: { name: 'Mrityu Saham', formula: { day: ['Moon', 'Saturn'], night: ['Saturn', 'Moon'] },
             meaning: 'Longevity concerns (use carefully)' },
    paradesh: { name: 'Paradesh Saham', formula: { day: ['Mars', 'Moon'], night: ['Moon', 'Mars'] },
             meaning: 'Foreign travel, distant lands' }
};

/**
 * Hadda (Ptolemaic Terms) boundaries
 * Each sign is divided among 5 planets in specific degrees
 */
const HADDA_BOUNDARIES = {
    0:  [{ end: 6, lord: 'Jupiter' }, { end: 14, lord: 'Venus' }, { end: 21, lord: 'Mercury' }, { end: 26, lord: 'Mars' }, { end: 30, lord: 'Saturn' }],
    1:  [{ end: 8, lord: 'Venus' }, { end: 15, lord: 'Mercury' }, { end: 22, lord: 'Jupiter' }, { end: 26, lord: 'Saturn' }, { end: 30, lord: 'Mars' }],
    2:  [{ end: 7, lord: 'Mercury' }, { end: 14, lord: 'Jupiter' }, { end: 21, lord: 'Venus' }, { end: 25, lord: 'Saturn' }, { end: 30, lord: 'Mars' }],
    3:  [{ end: 6, lord: 'Mars' }, { end: 13, lord: 'Jupiter' }, { end: 20, lord: 'Mercury' }, { end: 27, lord: 'Venus' }, { end: 30, lord: 'Saturn' }],
    4:  [{ end: 6, lord: 'Saturn' }, { end: 13, lord: 'Mercury' }, { end: 19, lord: 'Venus' }, { end: 25, lord: 'Jupiter' }, { end: 30, lord: 'Mars' }],
    5:  [{ end: 7, lord: 'Mercury' }, { end: 13, lord: 'Venus' }, { end: 18, lord: 'Jupiter' }, { end: 24, lord: 'Saturn' }, { end: 30, lord: 'Mars' }],
    6:  [{ end: 6, lord: 'Saturn' }, { end: 11, lord: 'Venus' }, { end: 19, lord: 'Jupiter' }, { end: 24, lord: 'Mercury' }, { end: 30, lord: 'Mars' }],
    7:  [{ end: 6, lord: 'Mars' }, { end: 14, lord: 'Jupiter' }, { end: 21, lord: 'Venus' }, { end: 27, lord: 'Mercury' }, { end: 30, lord: 'Saturn' }],
    8:  [{ end: 8, lord: 'Jupiter' }, { end: 14, lord: 'Venus' }, { end: 19, lord: 'Mercury' }, { end: 25, lord: 'Saturn' }, { end: 30, lord: 'Mars' }],
    9:  [{ end: 6, lord: 'Venus' }, { end: 12, lord: 'Mercury' }, { end: 19, lord: 'Jupiter' }, { end: 25, lord: 'Mars' }, { end: 30, lord: 'Saturn' }],
    10: [{ end: 6, lord: 'Saturn' }, { end: 12, lord: 'Mercury' }, { end: 20, lord: 'Venus' }, { end: 25, lord: 'Jupiter' }, { end: 30, lord: 'Mars' }],
    11: [{ end: 8, lord: 'Venus' }, { end: 14, lord: 'Jupiter' }, { end: 20, lord: 'Mercury' }, { end: 26, lord: 'Mars' }, { end: 30, lord: 'Saturn' }]
};

class Varshaphala {
    /**
     * Calculate the complete Varshaphala for a given year
     * @param {Object} natalData - Natal chart data from Vedic.calculate()
     * @param {number} yearNumber - Year number (1 = first year, 2 = second, etc.)
     * @param {Object} location - Location for Varshaphala calculation {lat, lng, tz}
     * @returns {Object} Complete Varshaphala analysis
     */
    calculate(natalData, yearNumber, location = null) {
        // Use natal location if not specified
        const calcLocation = location || natalData.location;

        // 1. Find the exact Solar Return moment
        const solarReturnMoment = this.findSolarReturn(
            natalData.planets.Sun.lon,
            natalData.date,
            yearNumber
        );

        // 2. Calculate planetary positions at Solar Return
        const tropicalPlanets = Engine.calculatePlanets(solarReturnMoment);
        const ayanamsa = Engine.getAyanamsa(solarReturnMoment);

        // Convert to sidereal
        const planets = {};
        for (const [planet, coords] of Object.entries(tropicalPlanets)) {
            let lon = coords.elon - ayanamsa;
            if (lon < 0) lon += 360;
            planets[planet] = {
                lon: lon,
                lat: coords.elat,
                speed: coords.speed,
                rasi: this.getRasi(lon),
                nakshatra: this.getNakshatra(lon)
            };
        }

        // 3. Calculate Varshaphala Lagna
        const tropicalLagna = Engine.calculateLagna(
            solarReturnMoment,
            calcLocation.lat,
            calcLocation.lng
        );
        let lagnaLon = tropicalLagna - ayanamsa;
        if (lagnaLon < 0) lagnaLon += 360;

        const lagna = {
            lon: lagnaLon,
            rasi: this.getRasi(lagnaLon),
            nakshatra: this.getNakshatra(lagnaLon)
        };

        // 4. Calculate houses
        const houses = this.calculateHouses(lagnaLon);

        // 5. Calculate Muntha
        const muntha = this.calculateMuntha(natalData.lagna.rasi.index, yearNumber);

        // 6. Determine Year Lord (Varshesh)
        const varshesh = this.determineVarshesh(lagna, muntha, planets, yearNumber, solarReturnMoment, natalData);

        // 7. Calculate Sahams
        const isDaytime = this.isDaytime(solarReturnMoment, calcLocation);
        const sahams = this.calculateSahams(lagnaLon, planets, isDaytime);

        // 8. Detect Tajika Yogas
        const tajikaYogas = this.detectTajikaYogas(planets, lagna);

        // 9. Calculate Hadda lords for key points
        const haddaAnalysis = this.analyzeHadda(planets, lagnaLon);

        // 10. Panchadhikari (Five Lordships) analysis
        const panchadhikari = this.analyzePanchadhikari(
            lagna, muntha, planets, yearNumber, solarReturnMoment, calcLocation
        );

        // 11. Generate yearly predictions
        const predictions = this.generatePredictions(
            lagna, muntha, varshesh, planets, tajikaYogas, sahams, houses
        );

        return {
            yearNumber: yearNumber,
            solarReturn: {
                date: solarReturnMoment,
                sunLongitude: planets.Sun.lon
            },
            natalSunLongitude: natalData.planets.Sun.lon,
            ayanamsa: ayanamsa,
            location: calcLocation,
            lagna: lagna,
            planets: planets,
            houses: houses,
            muntha: muntha,
            varshesh: varshesh,
            panchadhikari: panchadhikari,
            sahams: sahams,
            tajikaYogas: tajikaYogas,
            haddaAnalysis: haddaAnalysis,
            predictions: predictions
        };
    }

    /**
     * Find the exact moment of Solar Return using binary search
     * @param {number} natalSunLon - Natal Sun longitude (sidereal)
     * @param {Date} birthDate - Birth date
     * @param {number} yearNumber - Year number (1, 2, 3...)
     * @returns {Date} Exact Solar Return moment
     */
    findSolarReturn(natalSunLon, birthDate, yearNumber) {
        // Approximate date: birthdate + yearNumber years
        const approxDate = new Date(birthDate);
        approxDate.setFullYear(birthDate.getFullYear() + yearNumber);

        // Search window: ±2 days around approximate date
        let startDate = new Date(approxDate);
        startDate.setDate(startDate.getDate() - 2);
        let endDate = new Date(approxDate);
        endDate.setDate(endDate.getDate() + 2);

        // Binary search for exact moment
        const tolerance = 0.0001; // About 0.36 arc-seconds
        const maxIterations = 50;

        for (let i = 0; i < maxIterations; i++) {
            const midDate = new Date((startDate.getTime() + endDate.getTime()) / 2);
            const currentSunLon = this.getSiderealSunLongitude(midDate);

            // Calculate difference accounting for zodiac wrap-around
            let diff = currentSunLon - natalSunLon;
            if (diff > 180) diff -= 360;
            if (diff < -180) diff += 360;

            if (Math.abs(diff) < tolerance) {
                return midDate;
            }

            // Adjust search window
            if (diff > 0) {
                endDate = midDate;
            } else {
                startDate = midDate;
            }
        }

        // Return best approximation
        return new Date((startDate.getTime() + endDate.getTime()) / 2);
    }

    /**
     * Get sidereal Sun longitude for a given date
     * @param {Date} date - Date
     * @returns {number} Sidereal Sun longitude
     */
    getSiderealSunLongitude(date) {
        const sunVector = Astronomy.GeoVector('Sun', date, true);
        const ecliptic = Astronomy.Ecliptic(sunVector);
        const ayanamsa = Engine.getAyanamsa(date);
        let lon = ecliptic.elon - ayanamsa;
        if (lon < 0) lon += 360;
        return lon;
    }

    /**
     * Calculate Muntha (Annual Lagna)
     * Progresses one sign per year from Ascendant
     * @param {number} natalLagnaIndex - Natal Lagna sign index
     * @param {number} yearNumber - Year number
     * @returns {Object} Muntha data
     */
    calculateMuntha(natalLagnaIndex, yearNumber) {
        // Muntha moves 1 sign per year
        // Year 1: Same as natal Lagna
        // Year 2: Next sign, etc.
        const munthaIndex = (natalLagnaIndex + yearNumber - 1) % 12;
        const houseFromLagna = ((munthaIndex - natalLagnaIndex + 12) % 12) + 1;

        return {
            signIndex: munthaIndex,
            signName: RASI_NAMES[munthaIndex],
            lord: SIGN_LORDS[munthaIndex],
            houseFromLagna: houseFromLagna,
            signification: I18n.t('varshaphala.muntha_effects.' + houseFromLagna)
        };
    }

    /**
     * Determine the Varshesh (Year Lord)
     * Based on Tajika system's Panchadhikari
     * Rule: Strongest among 5 office-bearers who ASPECTS the Varsha Lagna.
     */
    determineVarshesh(lagna, muntha, planets, yearNumber, solarReturnMoment, natalData) {
        // 1. Identify 5 office-bearers (Panchadhikari) with their roles
        const candidates = this.getPanchadhikari(lagna, muntha, solarReturnMoment, natalData);
        
        // 2. Calculate Harsha Bala (4-fold strength) for each
        const scoredCandidates = candidates.map(c => ({
            planet: c.planet,
            reason: c.role,
            strength: this.calculateHarshaBala(c.planet, planets, lagna, solarReturnMoment, natalData.location),
            aspectsLagna: this.planetAspectsLagna(c.planet, planets, lagna)
        }));

        // 3. Filter those who aspect Lagna
        let eligible = scoredCandidates.filter(c => c.aspectsLagna);
        
        // If none aspect Lagna (rare), the strongest overall is taken
        if (eligible.length === 0) eligible = scoredCandidates;

        // 4. Sort by strength
        eligible.sort((a, b) => b.strength - a.strength);
        const varshesh = eligible[0];

        const varsheshData = planets[varshesh.planet];
        const varsheshHouse = this.getHousePosition(varsheshData.lon, lagna.lon);

        return {
            planet: varshesh.planet,
            reason: varshesh.reason,
            strength: varshesh.strength,
            aspectsLagna: varshesh.aspectsLagna,
            position: {
                sign: varsheshData.rasi.name,
                house: varsheshHouse,
                degree: varsheshData.rasi.degrees
            }
        };
    }

    /**
     * Check if a planet aspects the Varsha Lagna
     * In Tajika, aspects are: 3, 5, 9, 11 (Friendly) and 1, 4, 7, 10 (Inimical)
     * All these count as "aspecting" for Varshesh eligibility
     */
    planetAspectsLagna(planet, planets, lagna) {
        const pLon = planets[planet].lon;
        const lLon = lagna.lon;
        let house = Math.floor(((pLon - lLon + 360) % 360) / 30) + 1;
        
        // Tajika aspects: conjunction(1), square(4), opposition(7), square(10)
        // And friendly: 3, 5, 9, 11.
        // Basically any major house except 2, 6, 8, 12.
        return ![2, 6, 8, 12].includes(house);
    }

    /**
     * Get the 5 office-bearers for the year
     */
    getPanchadhikari(lagna, muntha, date, natalData) {
        const bearers = [];
        
        // 1. Natal Lagna Lord
        bearers.push({ planet: SIGN_LORDS[natalData.lagna.rasi.index], role: 'lagna_lord' });
        
        // 2. Varsha Lagna Lord
        const varshaLagnaLord = SIGN_LORDS[lagna.rasi.index];
        bearers.push({ planet: varshaLagnaLord, role: 'lagna_lord' });
        
        // 3. Muntha Lord
        bearers.push({ planet: muntha.lord, role: 'muntha_lord' });
        
        // 4. Dina-Ratri Pati (Day/Night Lord of Natal Birth)
        const isNatalDay = this.isDaytime(natalData.date, natalData.location);
        bearers.push({ planet: isNatalDay ? 'Sun' : 'Moon', role: 'vara_lord' });
        
        // 5. Trirashipati (Lord of the Trigona of Varsha Lagna)
        const isVarshaDay = this.isDaytime(date, natalData.location);
        bearers.push({ 
            planet: this.getTriRashiLord(lagna.rasi.index, isVarshaDay), 
            role: 'tri_rasi_lord' 
        });
        
        // Use a unique list to avoid duplicate planets, but keep the first role found
        const unique = [];
        const seen = new Set();
        for (const b of bearers) {
            if (!seen.has(b.planet)) {
                seen.add(b.planet);
                unique.push(b);
            }
        }
        
        return unique;
    }

    /**
     * Calculate simple strength for Varshesh determination
     * @param {string} planet - Planet name
     * @param {Object} planets - All planetary positions
     * @param {Object} lagna - Lagna data
     * @returns {number} Strength score
     */
    calculatePlanetStrength(planet, planets, lagna) {
        const data = planets[planet];
        if (!data) return 0;

        let strength = 50; // Base strength

        const signIndex = data.rasi.index;
        const house = this.getHousePosition(data.lon, lagna.lon);

        // In own sign: +20
        if (this.isOwnSign(planet, signIndex)) strength += 20;

        // Exalted: +30
        if (this.isExalted(planet, signIndex)) strength += 30;

        // Debilitated: -20
        if (this.isDebilitated(planet, signIndex)) strength -= 20;

        // Angular houses (1, 4, 7, 10): +15
        if ([1, 4, 7, 10].includes(house)) strength += 15;

        // Trinal houses (1, 5, 9): +10
        if ([1, 5, 9].includes(house)) strength += 10;

        // Dusthana (6, 8, 12): -10
        if ([6, 8, 12].includes(house)) strength -= 10;

        // Direct motion: +5
        if (data.speed > 0) strength += 5;

        return Math.max(0, strength);
    }

    /**
     * Calculate Sahams (Arabic Parts)
     * @param {number} lagnaLon - Lagna longitude
     * @param {Object} planets - Planetary positions
     * @param {boolean} isDaytime - True if solar return is during daytime
     * @returns {Object} Saham positions
     */
    calculateSahams(lagnaLon, planets, isDaytime) {
        const results = {};

        for (const [key, saham] of Object.entries(SAHAMS)) {
            const formula = isDaytime ? saham.formula.day : saham.formula.night;
            const planetA = formula[0];
            const planetB = formula[1];

            // Saham = Lagna + A - B
            let sahamLon = lagnaLon + planets[planetA].lon - planets[planetB].lon;

            // Normalize to 0-360
            while (sahamLon < 0) sahamLon += 360;
            while (sahamLon >= 360) sahamLon -= 360;

            results[key] = {
                name: I18n.t('varshaphala.saham_names.' + key),
                longitude: sahamLon,
                sign: this.getRasi(sahamLon),
                meaning: I18n.t('varshaphala.saham_meanings.' + key),
                houseFromLagna: this.getHousePosition(sahamLon, lagnaLon)
            };
        }

        return results;
    }

    /**
     * Detect Tajika Yogas between planets
     * @param {Object} planets - Planetary positions
     * @param {Object} lagna - Lagna data
     * @returns {Array} List of detected Tajika Yogas
     */
    detectTajikaYogas(planets, lagna) {
        const yogas = [];
        const planetNames = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];

        // Check each pair of planets
        for (let i = 0; i < planetNames.length; i++) {
            for (let j = i + 1; j < planetNames.length; j++) {
                const p1 = planetNames[i];
                const p2 = planetNames[j];
                const lon1 = planets[p1].lon;
                const lon2 = planets[p2].lon;

                // Calculate angular distance
                let diff = Math.abs(lon1 - lon2);
                if (diff > 180) diff = 360 - diff;

                // Check each aspect type
                for (const [aspectType, config] of Object.entries(TAJIKA_ASPECTS)) {
                    if (diff >= config.min && diff <= config.max) {
                        // Determine if applying or separating
                        const applying = this.isAspectApplying(planets[p1], planets[p2]);

                        // Calculate orb
                        const idealAngle = (config.min + config.max) / 2;
                        const orb = Math.abs(diff - idealAngle);

                        yogas.push({
                            type: aspectType,
                            sanskritName: config.name,
                            planet1: p1,
                            planet2: p2,
                            orb: orb.toFixed(2),
                            strength: config.strength,
                            applying: applying,
                            description: this.getTajikaYogaDescription(p1, p2, aspectType, applying),
                            data: { type: 'yoga', yogaType: aspectType, planet1: p1, planet2: p2, applying }
                        });
                    }
                }
            }
        }

        // Check for specific Tajika Yogas

        // Ithasala (Applying conjunction/aspect)
        const ithasalaYogas = yogas.filter(y => y.applying);
        ithasalaYogas.forEach(y => {
            y.specialYoga = 'Ithasala';
            y.effect = I18n.t('varshaphala.tajika_yoga_list.Ithasala.effect');
        });

        // Ishrafa (Separating aspect)
        const ishrafaYogas = yogas.filter(y => !y.applying);
        ishrafaYogas.forEach(y => {
            y.specialYoga = 'Ishrafa';
            y.effect = I18n.t('varshaphala.tajika_yoga_list.Ishrafa.effect');
        });

        // Add special yogas to results
        this.detectSpecialTajikaYogas(yogas, planets, lagna);

        return yogas;
    }

    /**
     * Detect special Tajika Yogas
     * @param {Array} yogas - Existing yoga array (modified in place)
     * @param {Object} planets - Planetary positions
     * @param {Object} lagna - Lagna
     */
    detectSpecialTajikaYogas(yogas, planets, lagna) {
        // Nakta Yoga: Moon in Lagna at night-time chart
        const moonHouse = this.getHousePosition(planets.Moon.lon, lagna.lon);
        if (moonHouse === 1) {
            yogas.push({
                type: 'special',
                sanskritName: 'Nakta',
                planets: ['Moon'],
                description: I18n.t('varshaphala.tajika_yoga_list.Nakta.description'),
                effect: I18n.t('varshaphala.tajika_yoga_list.Nakta.effect'),
                data: { type: 'special_yoga', name: 'Nakta' }
            });
        }

        // Yamaya Yoga: Benefics in Kendras
        const benefics = ['Jupiter', 'Venus', 'Mercury'];
        const kendras = [1, 4, 7, 10];
        let beneficsInKendra = 0;
        benefics.forEach(b => {
            const house = this.getHousePosition(planets[b].lon, lagna.lon);
            if (kendras.includes(house)) beneficsInKendra++;
        });

        if (beneficsInKendra >= 2) {
            yogas.push({
                type: 'special',
                sanskritName: 'Yamaya',
                description: I18n.t('varshaphala.tajika_yoga_list.Yamaya.description', { n: I18n.n(beneficsInKendra) }),
                effect: I18n.t('varshaphala.tajika_yoga_list.Yamaya.effect'),
                data: { type: 'special_yoga', name: 'Yamaya' }
            });
        }

        // Kamboola Yoga: Moon applies to Lagna Lord
        const lagnaLord = SIGN_LORDS[lagna.rasi.index];
        const moonLagnaLordDiff = this.getAngularDifference(planets.Moon.lon, planets[lagnaLord].lon);
        if (moonLagnaLordDiff < 12 && planets.Moon.speed > planets[lagnaLord].speed) {
            yogas.push({
                type: 'special',
                sanskritName: 'Kamboola',
                planets: ['Moon', lagnaLord],
                description: I18n.t('varshaphala.tajika_yoga_list.Kamboola.description'),
                effect: I18n.t('varshaphala.tajika_yoga_list.Kamboola.effect'),
                data: { type: 'special_yoga', name: 'Kamboola' }
            });
        }

        // Rudda Yoga: Malefic in 12th without benefic aspect
        const maleficsList = ['Saturn', 'Mars', 'Rahu', 'Ketu'];
        maleficsList.forEach(m => {
            if (planets[m]) {
                const house = this.getHousePosition(planets[m].lon, lagna.lon);
                if (house === 12) {
                    yogas.push({
                        type: 'special',
                        sanskritName: 'Rudda',
                        planets: [m],
                        description: I18n.t('varshaphala.tajika_yoga_list.Rudda.description', { planet: I18n.t('planets.' + m) }),
                        effect: I18n.t('varshaphala.tajika_yoga_list.Rudda.effect'),
                        data: { type: 'special_yoga', name: 'Rudda', planet: m }
                    });
                }
            }
        });
    }

    /**
     * Check if an aspect is applying or separating
     * @param {Object} planet1 - First planet data
     * @param {Object} planet2 - Second planet data
     * @returns {boolean} True if applying
     */
    isAspectApplying(planet1, planet2) {
        // Faster planet applies to slower
        const speed1 = planet1.speed || 0;
        const speed2 = planet2.speed || 0;

        if (speed1 === speed2) return false;

        const fasterPlanet = speed1 > speed2 ? planet1 : planet2;
        const slowerPlanet = speed1 > speed2 ? planet2 : planet1;

        // Check if faster is behind slower and catching up
        let diff = slowerPlanet.lon - fasterPlanet.lon;
        if (diff < 0) diff += 360;

        // If diff is less than 180, faster is approaching
        return diff < 180 && diff > 0;
    }

    /**
     * Get description for a Tajika Yoga
     */
    getTajikaYogaDescription(planet1, planet2, aspectType, applying) {
        const action = applying ? I18n.t('common.applying') : I18n.t('common.separating');
        const aspect = I18n.t(`varshaphala.tajika_aspects.${aspectType}`);
        
        return I18n.t('varshaphala.prediction_indications.yoga', {
            p1: I18n.t('planets.' + planet1),
            action: action,
            aspect: aspect,
            p2: I18n.t('planets.' + planet2)
        });
    }

    /**
     * Analyze Hadda (Ptolemaic Terms) for key points
     * @param {Object} planets - Planetary positions
     * @param {number} lagnaLon - Lagna longitude
     * @returns {Object} Hadda analysis
     */
    analyzeHadda(planets, lagnaLon) {
        const results = {
            lagna: this.getHaddaLord(lagnaLon),
            sun: this.getHaddaLord(planets.Sun.lon),
            moon: this.getHaddaLord(planets.Moon.lon),
            mc: null // Would need MC calculation
        };

        return results;
    }

    /**
     * Get Hadda (Term) Lord for a longitude
     * @param {number} longitude - Position in degrees
     * @returns {Object} Hadda lord data
     */
    getHaddaLord(longitude) {
        const signIndex = Math.floor(longitude / 30);
        const degreeInSign = longitude % 30;
        const boundaries = HADDA_BOUNDARIES[signIndex];

        for (const boundary of boundaries) {
            if (degreeInSign < boundary.end) {
                return {
                    lord: boundary.lord,
                    signIndex: signIndex,
                    degree: degreeInSign.toFixed(2)
                };
            }
        }

        return { lord: boundaries[boundaries.length - 1].lord, signIndex, degree: degreeInSign };
    }

    /**
     * Analyze Panchadhikari (Five Lordships)
     */
    analyzePanchadhikari(lagna, muntha, planets, yearNumber, date, location) {
        const dayOfWeek = date.getDay();
        const varaLords = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
        const varaLord = varaLords[dayOfWeek];
        const isDay = this.isDaytime(date, location);

        return {
            lagna_lord: {
                planet: SIGN_LORDS[lagna.rasi.index],
                role: I18n.t('varshaphala.panchadhikari_roles.lagna_lord'),
                signification: I18n.t('varshaphala.panchadhikari_significations.lagna_lord')
            },
            muntha_lord: {
                planet: muntha.lord,
                role: I18n.t('varshaphala.panchadhikari_roles.muntha_lord'),
                signification: I18n.t('varshaphala.panchadhikari_significations.muntha_lord')
            },
            vara_lord: {
                planet: varaLord,
                role: I18n.t('varshaphala.panchadhikari_roles.vara_lord'),
                signification: I18n.t('varshaphala.panchadhikari_significations.vara_lord')
            },
            tri_rasi_lord: {
                planet: this.getTriRashiLord(lagna.rasi.index, isDay),
                role: I18n.t('varshaphala.panchadhikari_roles.tri_rasi_lord'),
                signification: I18n.t('varshaphala.panchadhikari_significations.tri_rasi_lord')
            }
        };
    }

    /**
     * Calculate Harsha Bala (4-fold strength)
     * Per Tajika Neelakanthi
     */
    calculateHarshaBala(planet, planets, lagna, date, location) {
        let score = 0;
        const pData = planets[planet];
        const house = this.getHousePosition(pData.lon, lagna.lon);
        const isDay = this.isDaytime(date, location);

        // 1. First Strength (Stree-Purusha Bala)
        // Male planets (Sun, Mars, Jup) in Male signs (Odd)
        // Female planets (Moon, Ven, Sat) in Female signs (Even)
        const isOdd = pData.rasi.index % 2 === 0;
        const isMalePlanet = ['Sun', 'Mars', 'Jupiter'].includes(planet);
        if ((isMalePlanet && isOdd) || (!isMalePlanet && !isOdd)) score += 5;

        // 2. Second Strength (Day/Night)
        if ((isDay && isMalePlanet) || (!isDay && !isMalePlanet)) score += 5;

        // 3. Third Strength (Swa-kshetra / Uccha)
        if (this.isOwnSign(planet, pData.rasi.index) || this.isExalted(planet, pData.rasi.index)) score += 5;

        // 4. Fourth Strength (House Placement)
        // Specific houses where planets gain joy
        const joyHouses = {
            Sun: 9, Moon: 3, Mars: 6, Mercury: 1, Jupiter: 11, Venus: 5, Saturn: 12
        };
        if (joyHouses[planet] === house) score += 5;

        return score; // Max 20
    }

    /**
     * Get Tri-Rashi Lord based on sign and day/night
     */
    getTriRashiLord(signIdx, isDay) {
        const triTable = [
            { day: 'Sun', night: 'Jupiter' },   // Fire (Ar, Le, Sg)
            { day: 'Venus', night: 'Moon' },    // Earth (Ta, Vi, Cp)
            { day: 'Saturn', night: 'Mercury' },// Air (Ge, Li, Aq)
            { day: 'Venus', night: 'Mars' }     // Water (Cn, Sc, Pi)
        ];
        const elementIdx = signIdx % 4;
        return isDay ? triTable[elementIdx].day : triTable[elementIdx].night;
    }

    /**
     * Generate yearly predictions based on analysis
     */
    generatePredictions(lagna, muntha, varshesh, planets, tajikaYogas, sahams, houses) {
        const predictions = {
            overall: [],
            career: [],
            wealth: [],
            health: [],
            relationships: [],
            spirituality: []
        };

        // Overall analysis based on Varshesh
        predictions.overall.push({
            factor: I18n.t('varshaphala.prediction_factors.year_lord'),
            indication: I18n.t('varshaphala.prediction_indications.varshesh', { planet: I18n.t('planets.' + varshesh.planet), house: I18n.n(varshesh.position.house) }),
            effect: this.getVarsheshEffect(varshesh),
            data: { type: 'varshesh', planet: varshesh.planet, house: varshesh.position.house }
        });

        // Muntha analysis
        predictions.overall.push({
            factor: I18n.t('varshaphala.prediction_factors.muntha'),
            indication: I18n.t('varshaphala.prediction_indications.muntha', { sign: I18n.t('rasis.' + muntha.signName), house: I18n.n(muntha.houseFromLagna) }),
            effect: I18n.t('varshaphala.muntha_effects.' + muntha.houseFromLagna),
            data: { type: 'muntha', sign: muntha.signName, house: muntha.houseFromLagna }
        });

        // Analyze key Sahams
        if (sahams.karma) {
            const karmaHouse = sahams.karma.houseFromLagna;
            predictions.career.push({
                factor: I18n.t('varshaphala.saham_names.karma'),
                indication: I18n.t('varshaphala.prediction_indications.saham', { house: I18n.n(karmaHouse) }),
                effect: this.getSahamEffect('karma', karmaHouse),
                data: { type: 'saham', name: 'Karma Saham', house: karmaHouse }
            });
        }

        if (sahams.punya) {
            const punyaHouse = sahams.punya.houseFromLagna;
            predictions.overall.push({
                factor: I18n.t('varshaphala.saham_names.punya'),
                indication: I18n.t('varshaphala.prediction_indications.saham', { house: I18n.n(punyaHouse) }),
                effect: I18n.t('varshaphala.saham_effects.punya_general'),
                data: { type: 'saham', name: 'Punya Saham', house: punyaHouse }
            });
        }

        // Strong Tajika Yogas
        const strongYogas = tajikaYogas.filter(y =>
            y.strength === 'full' || y.strength === 'high'
        );
        strongYogas.forEach(yoga => {
            predictions.overall.push({
                factor: yoga.sanskritName,
                indication: yoga.description,
                effect: yoga.effect || this.getYogaEffect(yoga),
                data: { 
                    type: 'yoga', 
                    yogaType: yoga.type, 
                    planet1: yoga.planet1, 
                    planet2: yoga.planet2, 
                    applying: yoga.applying 
                }
            });
        });

        return predictions;
    }

    /**
     * Get effect description for Varshesh position
     */
    getVarsheshEffect(varshesh) {
        const house = varshesh.position.house;
        return I18n.t('varshaphala.varshesh_effects.' + house);
    }

    /**
     * Get Saham effect based on house position
     */
    getSahamEffect(sahamType, house) {
        const translatedEffect = I18n.t(`varshaphala.saham_effects.${sahamType}.${house}`);
        if (!translatedEffect.includes('varshaphala.saham_effects.')) {
            return translatedEffect;
        }

        // Fallback to generic
        return I18n.t('varshaphala.saham_effects.general', { 
            name: I18n.t('varshaphala.saham_names.' + sahamType), 
            house: I18n.n(house) 
        });
    }

    /**
     * Get general yoga effect
     */
    getYogaEffect(yoga) {
        if (yoga.applying) {
            return I18n.t('varshaphala.prediction_indications.yoga_effect_applying', { 
                p1: I18n.t('planets.' + yoga.planet1), 
                p2: I18n.t('planets.' + yoga.planet2) 
            });
        }
        return I18n.t('varshaphala.prediction_indications.yoga_effect_general', { 
            p1: I18n.t('planets.' + yoga.planet1), 
            p2: I18n.t('planets.' + yoga.planet2) 
        });
    }

    // ============== UTILITY METHODS ==============

    getRasi(lon) {
        const index = Math.floor(lon / 30);
        return {
            index: index,
            name: RASI_NAMES[index],
            degrees: lon % 30
        };
    }

    getNakshatra(lon) {
        const index = Math.floor(lon / NAKSHATRA_SPAN);
        const posInNak = lon % NAKSHATRA_SPAN;
        const pada = Math.floor(posInNak / (NAKSHATRA_SPAN / 4)) + 1;

        return {
            index: index,
            name: NAKSHATRA_NAMES[index],
            pada: pada
        };
    }

    calculateHouses(lagnaLon) {
        const ascRasiIndex = Math.floor(lagnaLon / 30);
        const houses = {};

        for (let i = 1; i <= 12; i++) {
            const signIndex = (ascRasiIndex + i - 1) % 12;
            houses[i] = {
                sign: RASI_NAMES[signIndex],
                signIndex: signIndex,
                lord: SIGN_LORDS[signIndex]
            };
        }

        return houses;
    }

    getHousePosition(planetLon, lagnaLon) {
        let diff = planetLon - lagnaLon;
        if (diff < 0) diff += 360;
        return Math.floor(diff / 30) + 1;
    }

    getAngularDifference(lon1, lon2) {
        let diff = Math.abs(lon1 - lon2);
        if (diff > 180) diff = 360 - diff;
        return diff;
    }

    isDaytime(date, location) {
        if (!location || typeof location.lat !== 'number') return true;
        try {
            const sunTimes = Engine.getSunriseSunset(date, location.lat, location.lng);
            if (sunTimes.sunrise && sunTimes.sunset) {
                return date >= sunTimes.sunrise && date < sunTimes.sunset;
            }
        } catch (e) {
            console.warn('Could not determine day/night, defaulting to day');
        }
        // Default to daytime
        return true;
    }

    isOwnSign(planet, signIndex) {
        const ownSigns = {
            Sun: [4], Moon: [3], Mars: [0, 7], Mercury: [2, 5],
            Jupiter: [8, 11], Venus: [1, 6], Saturn: [9, 10]
        };
        return ownSigns[planet]?.includes(signIndex) || false;
    }

    isExalted(planet, signIndex) {
        const exaltedSigns = {
            Sun: 0, Moon: 1, Mars: 9, Mercury: 5,
            Jupiter: 3, Venus: 11, Saturn: 6
        };
        return exaltedSigns[planet] === signIndex;
    }

    isDebilitated(planet, signIndex) {
        const debilitatedSigns = {
            Sun: 6, Moon: 7, Mars: 3, Mercury: 11,
            Jupiter: 9, Venus: 5, Saturn: 0
        };
        return debilitatedSigns[planet] === signIndex;
    }

    /**
     * Get multiple years of Varshaphala
     * @param {Object} natalData - Natal chart data
     * @param {number} startYear - Starting year number
     * @param {number} count - Number of years to calculate
     * @param {Object} location - Optional location
     * @returns {Array} Array of Varshaphala results
     */
    calculateMultipleYears(natalData, startYear = 1, count = 5, location = null) {
        const results = [];
        for (let i = 0; i < count; i++) {
            results.push(this.calculate(natalData, startYear + i, location));
        }
        return results;
    }
}

export default new Varshaphala();
