/**
 * ============================================================================
 * Special Lagnas Engine
 * ============================================================================
 *
 * Implements the special Lagna calculations per Brihat Parashara Hora Shastra
 * (BPHS) and Jaimini Sutras.
 *
 * Included Lagnas:
 * - Arudha Lagna (AL) & House Arudhas (A1-A12)
 * - Upapada Lagna (UL) - Arudha of 12th house
 * - Hora Lagna (HL) - Time-based, wealth indicator
 * - Ghati Lagna (GL) - 5 Ghatis/sign, career/status
 * - Varnada Lagna (VL) - Dharma and caste indicator
 * - Bhava Lagna (BL) - For Bhava Chalit
 * - Karakamsa - Atmakaraka's Navamsha position
 *
 * References:
 * - BPHS Chapters 29-30 (Arudha Lagnas)
 * - BPHS Chapter 6 (Special Lagnas)
 * - Jaimini Sutras (Varnada Lagna)
 *
 * @module astro/special_lagnas
 * @version 1.0.0
 */

import { SIGN_LORDS, RASI_NAMES, SIGN_MODALITY } from './constants.js';
import Engine from './engine.js';

class SpecialLagnas {
    constructor() {
        /**
         * Mapping of planet names to their owned signs
         * Needed for reverse lookup in Arudha calculations
         */
        this.planetOwnSigns = {
            Sun: [4],       // Leo
            Moon: [3],      // Cancer
            Mars: [0, 7],   // Aries, Scorpio
            Mercury: [2, 5], // Gemini, Virgo
            Jupiter: [8, 11], // Sagittarius, Pisces
            Venus: [1, 6],   // Taurus, Libra
            Saturn: [9, 10]  // Capricorn, Aquarius
        };
    }

    // =========================================================================
    // MAIN CALCULATION METHOD
    // =========================================================================

    /**
     * Calculate all special Lagnas for a chart
     * @param {Object} params - Calculation parameters
     * @param {Object} params.planets - Planetary positions with rasi.index
     * @param {Object} params.lagna - Lagna position with lon and rasi.index
     * @param {Date} params.date - Birth date/time
     * @param {Object} params.location - Location with lat/lng
     * @param {number} params.ayanamsa - Ayanamsa value
     * @param {Object} params.jaimini - Jaimini data with karakas
     * @returns {Object} All special Lagna data
     */
    calculate(params) {
        const { planets, lagna, date, location, ayanamsa, jaimini } = params;
        const lagnaIdx = lagna.rasi.index;

        // Calculate all Arudha Padas (A1 to A12)
        const arudhaPadas = this._calculateAllArudhas(planets, lagnaIdx);

        // Calculate time-based Lagnas
        const horaLagna = this._calculateHoraLagna(date, location, ayanamsa);
        const ghatiLagna = this._calculateGhatiLagna(date, location, ayanamsa);

        // Calculate Varnada Lagna
        const varnadaLagna = this._calculateVarnadaLagna(lagnaIdx, horaLagna.rasi.index);

        // Calculate Bhava Lagna
        const bhavaLagna = this._calculateBhavaLagna(date, location, ayanamsa);

        // Calculate Karakamsa
        const karakamsa = this._calculateKarakamsa(planets, jaimini);

        // Calculate Indu Lagna (Wealth)
        const induLagna = this._calculateInduLagna(planets, lagnaIdx);

        // Calculate Pranapada Lagna
        const pranapadaLagna = this._calculatePranapadaLagna(date, location, planets.Sun.lon, ayanamsa);

        // Special Arudhas
        const upapada = arudhaPadas.A12; // UL = A12

        return {
            // Primary Arudha Lagna
            arudhaLagna: arudhaPadas.A1,

            // All 12 House Arudhas
            arudhaPadas: arudhaPadas,

            // Upapada (A12) - Marriage indicator
            upapada: upapada,

            // Time-based Lagnas
            horaLagna: horaLagna,
            ghatiLagna: ghatiLagna,

            // Indu Lagna
            induLagna: induLagna,

            // Pranapada Lagna
            pranapadaLagna: pranapadaLagna,

            // Dharmic Lagna
            varnadaLagna: varnadaLagna,

            // Bhava Lagna
            bhavaLagna: bhavaLagna,

            // Jaimini Karakamsa
            karakamsa: karakamsa,

            // Summary for quick access
            summary: {
                AL: this._formatLagna(arudhaPadas.A1),
                UL: this._formatLagna(upapada),
                HL: this._formatLagna(horaLagna),
                GL: this._formatLagna(ghatiLagna),
                IL: this._formatLagna(induLagna),
                PL: this._formatLagna(pranapadaLagna),
                VL: this._formatLagna(varnadaLagna),
                BL: this._formatLagna(bhavaLagna),
                KA: karakamsa ? this._formatLagna(karakamsa) : null
            }
        };
    }

    // ... (rest of the methods)

    // =========================================================================
    // INDU LAGNA - Per BPHS (Wealth Indicator)
    // =========================================================================

    /**
     * Calculate Indu Lagna
     * 
     * 1. Get lord of 9th from Lagna and 9th from Moon
     * 2. Sum their "Indu" points:
     *    Sun: 30, Moon: 16, Mars: 6, Mercury: 8, Jupiter: 10, Venus: 12, Saturn: 1
     * 3. Remainder of (Sum / 12) counted from Moon's sign = Indu Lagna
     * 
     * @param {Object} planets - Planetary positions
     * @param {number} lagnaIdx - Lagna sign index
     * @returns {Object} Indu Lagna data
     */
    _calculateInduLagna(planets, lagnaIdx) {
        const moonIdx = planets.Moon.rasi.index;
        
        // 9th house from Lagna and Moon
        const house9Lagna = (lagnaIdx + 8) % 12;
        const house9Moon = (moonIdx + 8) % 12;

        const lordLagna = SIGN_LORDS[house9Lagna];
        const lordMoon = SIGN_LORDS[house9Moon];

        const induPoints = {
            Sun: 30, Moon: 16, Mars: 6, Mercury: 8, Jupiter: 10, Venus: 12, Saturn: 1
        };

        const totalPoints = (induPoints[lordLagna] || 0) + (induPoints[lordMoon] || 0);
        let count = totalPoints % 12;
        if (count === 0) count = 12;

        const induLagnaIdx = (moonIdx + count - 1) % 12;

        return this._createLagnaObject(induLagnaIdx, 15);
    }

    // =========================================================================
    // PRANAPADA LAGNA - Per BPHS Ch. 4
    // =========================================================================

    /**
     * Calculate Pranapada Lagna
     * 
     * Formula:
     * 1. Convert time from sunrise to vighatikas (1 min = 2.5 vighatikas)
     * 2. If Sun is in Movable sign: Pranapada = Sun + (Vighatikas / 15) * 30? No.
     * 
     * Correct BPHS Formula:
     * Pranapada = (Vighatikas × 4 / 15) + correction based on Sun's sign position
     * Or more simply: Pranapada moves 1 sign per 15 vighatikas (6 minutes).
     * 
     * Starting point (at sunrise):
     * - Sun in Movable sign: Same as Sun
     * - Sun in Fixed sign: Sun + 240° (9th from Sun)
     * - Sun in Dual sign: Sun + 120° (5th from Sun)
     * 
     * Then add (Time from sunrise in minutes / 6) * 30°
     * 
     * @param {Date} date - Birth date/time
     * @param {Object} location - Location
     * @param {number} sunLon - Sidereal Sun longitude
     * @param {number} ayanamsa - Ayanamsa
     * @returns {Object} Pranapada Lagna data
     */
    _calculatePranapadaLagna(date, location, sunLon, ayanamsa) {
        const { sunrise } = Engine.getSunriseSunset(date, location.lat, location.lng);
        if (!sunrise) return this._createLagnaObject(0, 15);

        const msFromSunrise = date.getTime() - sunrise.getTime();
        let minutesFromSunrise = msFromSunrise / (1000 * 60);
        if (minutesFromSunrise < 0) minutesFromSunrise += 24 * 60;

        // Base starting point based on Sun's sign modality
        const sunSignIdx = Math.floor(sunLon / 30);
        const modality = SIGN_MODALITY[sunSignIdx]; // 0: Movable, 1: Fixed, 2: Dual

        let baseLon = sunLon;
        if (modality === 1) baseLon = (sunLon + 240) % 360; // 9th from Sun
        else if (modality === 2) baseLon = (sunLon + 120) % 360; // 5th from Sun

        // Progress 30° per 6 minutes (15 vighatikas)
        const progress = (minutesFromSunrise / 6) * 30;
        const pranapadaLon = (baseLon + progress) % 360;

        return this._createLagnaObject(Math.floor(pranapadaLon / 30), pranapadaLon % 30, pranapadaLon);
    }

    // =========================================================================
    // ARUDHA LAGNA CALCULATIONS - Per BPHS Ch. 29
    // =========================================================================

    /**
     * Calculate all 12 house Arudhas
     * @param {Object} planets - Planetary positions
     * @param {number} lagnaIdx - Lagna sign index
     * @returns {Object} All Arudha padas A1-A12
     */
    _calculateAllArudhas(planets, lagnaIdx) {
        const arudhas = {};

        for (let house = 1; house <= 12; house++) {
            const signIdx = (lagnaIdx + house - 1) % 12;
            arudhas[`A${house}`] = this._calculateArudha(planets, lagnaIdx, signIdx, house);
        }

        return arudhas;
    }

    /**
     * Calculate Arudha for a specific house
     *
     * Algorithm per BPHS:
     * 1. Find the lord of the house
     * 2. Count from the house to the lord's position (A)
     * 3. Count same distance from the lord = Arudha
     *
     * Exception rules:
     * - If Arudha falls in the same sign or 7th from house,
     *   take the 10th sign from the original house instead
     *
     * @param {Object} planets - Planetary positions
     * @param {number} lagnaIdx - Lagna sign index
     * @param {number} signIdx - Sign index of the house
     * @param {number} houseNum - House number (1-12)
     * @returns {Object} Arudha data
     */
    _calculateArudha(planets, lagnaIdx, signIdx, houseNum) {
        // Get the lord of this house/sign
        const lord = SIGN_LORDS[signIdx];

        // Get the lord's position
        const lordPos = planets[lord]?.rasi?.index;
        if (lordPos === undefined) {
            return this._createLagnaObject(signIdx, 15); // Fallback
        }

        // Calculate distance from house sign to lord
        // Count is 1-based: if lord is in same sign, count = 1
        let distance = (lordPos - signIdx + 12) % 12;
        if (distance === 0) distance = 12;

        // Arudha = Same distance from lord
        let arudhaIdx = (lordPos + distance) % 12;

        // Exception: If Arudha falls in same sign as house (1st) or 7th from house
        const house7th = (signIdx + 6) % 12;

        if (arudhaIdx === signIdx || arudhaIdx === house7th) {
            // Take 10th from the original house sign
            arudhaIdx = (signIdx + 9) % 12;
        }

        return this._createLagnaObject(arudhaIdx, 15);
    }

    // =========================================================================
    // HORA LAGNA - Per BPHS Ch. 6
    // =========================================================================

    /**
     * Calculate Hora Lagna
     *
     * Hora Lagna moves through one sign per hora (2.5 ghatis = 1 hour).
     * Starting point is the sign rising at sunrise.
     *
     * Formula: HL = Sunrise Lagna + (time from sunrise in hours) × 30°
     *
     * @param {Date} date - Birth date/time
     * @param {Object} location - Location with lat/lng
     * @param {number} ayanamsa - Ayanamsa value
     * @returns {Object} Hora Lagna data
     */
    _calculateHoraLagna(date, location, ayanamsa) {
        const { sunrise } = Engine.getSunriseSunset(date, location.lat, location.lng);
        
        // Calculate Precise Sunrise Lagna
        const sunriseLagnaTropical = Engine.calculateLagna(sunrise, location.lat, location.lng);
        let sunriseLagna = (sunriseLagnaTropical - ayanamsa + 360) % 360;

        // Time elapsed since sunrise
        const msFromSunrise = date.getTime() - sunrise.getTime();
        let hoursFromSunrise = msFromSunrise / (1000 * 60 * 60);
        if (hoursFromSunrise < 0) hoursFromSunrise += 24;

        // Hora Lagna progresses 30° per hour from sunrise
        let horaLon = (sunriseLagna + (hoursFromSunrise * 30)) % 360;

        return this._createLagnaObject(Math.floor(horaLon / 30), horaLon % 30, horaLon);
    }

    // =========================================================================
    // GHATI LAGNA - Per BPHS Ch. 6
    // =========================================================================

    /**
     * Calculate Ghati Lagna
     *
     * Ghati Lagna moves through one sign per 5 ghatis (2 hours).
     * One ghati = 24 minutes. 5 ghatis = 120 minutes = 2 hours.
     *
     * Formula: GL = Sunrise Lagna + (ghatis from sunrise / 5) × 30°
     *
     * @param {Date} date - Birth date/time
     * @param {Object} location - Location with lat/lng
     * @param {number} ayanamsa - Ayanamsa value
     * @returns {Object} Ghati Lagna data
     */
    _calculateGhatiLagna(date, location, ayanamsa) {
        const { sunrise } = Engine.getSunriseSunset(date, location.lat, location.lng);
        
        const sunriseLagnaTropical = Engine.calculateLagna(sunrise, location.lat, location.lng);
        let sunriseLagna = (sunriseLagnaTropical - ayanamsa + 360) % 360;

        const msFromSunrise = date.getTime() - sunrise.getTime();
        let minutesFromSunrise = msFromSunrise / (1000 * 60);
        if (minutesFromSunrise < 0) minutesFromSunrise += 24 * 60;

        const ghatisFromSunrise = minutesFromSunrise / 24;

        // Ghati Lagna progresses 30° per 5 ghatis
        const ghatiProgress = (ghatisFromSunrise / 5) * 30;
        let ghatiLon = (sunriseLagna + ghatiProgress) % 360;

        return this._createLagnaObject(Math.floor(ghatiLon / 30), ghatiLon % 30, ghatiLon);
    }

    // =========================================================================
    // VARNADA LAGNA - Per Jaimini Sutras
    // =========================================================================

    /**
     * Calculate Varnada Lagna
     *
     * Varnada Lagna combines Lagna and Hora Lagna using Jaimini methodology.
     * It indicates Dharma, caste, and life purpose.
     *
     * Algorithm (Jaimini):
     * 1. If Lagna is in odd sign: Count from Aries to Lagna
     * 2. If Lagna is in even sign: Count from Pisces to Lagna (reverse)
     * 3. Same for Hora Lagna
     * 4. If both counts are odd-odd or even-even: Add them
     * 5. If one is odd and one is even: Subtract smaller from larger
     * 6. Result counted from Aries if final is odd, from Pisces if even
     *
     * @param {number} lagnaIdx - Lagna sign index
     * @param {number} horaLagnaIdx - Hora Lagna sign index
     * @returns {Object} Varnada Lagna data
     */
    _calculateVarnadaLagna(lagnaIdx, horaLagnaIdx) {
        // Determine if signs are odd or even (0-indexed: 0=Aries=Odd)
        const lagnaOdd = lagnaIdx % 2 === 0;
        const horaOdd = horaLagnaIdx % 2 === 0;

        // Calculate counts
        // Odd signs: Count from Aries (0)
        // Even signs: Count from Pisces (11) backwards
        let lagnaCount, horaCount;

        if (lagnaOdd) {
            lagnaCount = lagnaIdx + 1; // 1-based from Aries
        } else {
            lagnaCount = 12 - lagnaIdx; // Count back from Pisces
        }

        if (horaOdd) {
            horaCount = horaLagnaIdx + 1;
        } else {
            horaCount = 12 - horaLagnaIdx;
        }

        // Combine based on odd/even parity
        let result;
        const lagnaCountOdd = lagnaCount % 2 === 1;
        const horaCountOdd = horaCount % 2 === 1;

        if (lagnaCountOdd === horaCountOdd) {
            // Same parity: Add
            result = lagnaCount + horaCount;
        } else {
            // Different parity: Subtract
            result = Math.abs(lagnaCount - horaCount);
        }

        // Reduce to 12-sign range
        result = ((result - 1) % 12) + 1;

        // Determine final sign
        // If result is odd, count from Aries; if even, count from Pisces backwards
        let varnadaIdx;
        if (result % 2 === 1) {
            varnadaIdx = result - 1; // From Aries
        } else {
            varnadaIdx = (12 - result + 12) % 12; // From Pisces backwards
        }

        return this._createLagnaObject(varnadaIdx, 15);
    }

    // =========================================================================
    // BHAVA LAGNA - For Bhava Chalit
    // =========================================================================

    /**
     * Calculate Bhava Lagna
     * BL = LST × 15 (degrees per hour)
     */
    _calculateBhavaLagna(date, location, ayanamsa) {
        // Precise Local Sidereal Time from Astronomy library
        /* global Astronomy */
        const gmst = Astronomy.SiderealTime(date);
        const lst = (gmst + location.lng / 15 + 24) % 24;

        // Bhava Lagna = LST × 15° (tropical) - ayanamsa
        let bhavaLon = (lst * 15 - ayanamsa + 360) % 360;

        return this._createLagnaObject(Math.floor(bhavaLon / 30), bhavaLon % 30, bhavaLon);
    }

    // =========================================================================
    // KARAKAMSA - Jaimini System
    // =========================================================================

    /**
     * Calculate Karakamsa
     *
     * Karakamsa is the Navamsha position of the Atmakaraka (AK).
     * It's crucial in Jaimini astrology for career, spirituality, and life path.
     *
     * @param {Object} planets - Planetary positions
     * @param {Object} jaimini - Jaimini data containing karakas
     * @returns {Object|null} Karakamsa data or null if AK not found
     */
    _calculateKarakamsa(planets, jaimini) {
        if (!jaimini?.charaKarakas?.karakas?.AK) {
            return null;
        }

        const akPlanet = jaimini.charaKarakas.karakas.AK.planet;
        const akLon = planets[akPlanet]?.lon;

        if (akLon === undefined) {
            return null;
        }

        // Calculate Navamsha (D9) position
        // Each Navamsha = 3°20' (3.333...°)
        const navamshaSpan = 3.333333333333;
        const navamshaIndex = Math.floor(akLon / navamshaSpan);
        const navamshaSignIdx = navamshaIndex % 12;

        return {
            ...this._createLagnaObject(navamshaSignIdx, 15),
            atmakaraka: akPlanet,
            akLongitude: akLon
        };
    }

    // =========================================================================
    // INDU LAGNA - Per BPHS (Wealth Indicator)
    // =========================================================================

    /**
     * Calculate Indu Lagna
     * 
     * 1. Get lord of 9th from Lagna and 9th from Moon
     * 2. Sum their "Indu" points:
     *    Sun: 30, Moon: 16, Mars: 6, Mercury: 8, Jupiter: 10, Venus: 12, Saturn: 1
     * 3. Remainder of (Sum / 12) counted from Moon's sign = Indu Lagna
     * 
     * @param {Object} planets - Planetary positions
     * @param {number} lagnaIdx - Lagna sign index
     * @returns {Object} Indu Lagna data
     */
    _calculateInduLagna(planets, lagnaIdx) {
        const moonIdx = planets.Moon.rasi.index;
        
        // 9th house from Lagna and Moon
        const house9Lagna = (lagnaIdx + 8) % 12;
        const house9Moon = (moonIdx + 8) % 12;

        const lordLagna = SIGN_LORDS[house9Lagna];
        const lordMoon = SIGN_LORDS[house9Moon];

        const induPoints = {
            Sun: 30, Moon: 16, Mars: 6, Mercury: 8, Jupiter: 10, Venus: 12, Saturn: 1
        };

        const totalPoints = (induPoints[lordLagna] || 0) + (induPoints[lordMoon] || 0);
        let count = totalPoints % 12;
        if (count === 0) count = 12;

        const induLagnaIdx = (moonIdx + count - 1) % 12;

        return this._createLagnaObject(induLagnaIdx, 15);
    }

    // =========================================================================
    // PRANAPADA LAGNA - Per BPHS Ch. 4
    // =========================================================================

    /**
     * Calculate Pranapada Lagna
     * 
     * Formula:
     * 1. Convert time from sunrise to vighatikas (1 min = 2.5 vighatikas)
     * 2. If Sun is in Movable sign: Pranapada = Sun + (Vighatikas / 15) * 30? No.
     * 
     * Correct BPHS Formula:
     * Pranapada = (Vighatikas × 4 / 15) + correction based on Sun's sign position
     * Or more simply: Pranapada moves 1 sign per 15 vighatikas (6 minutes).
     * 
     * Starting point (at sunrise):
     * - Sun in Movable sign: Same as Sun
     * - Sun in Fixed sign: Sun + 240° (9th from Sun)
     * - Sun in Dual sign: Sun + 120° (5th from Sun)
     * 
     * Then add (Time from sunrise in minutes / 6) * 30°
     * 
     * @param {Date} date - Birth date/time
     * @param {Object} location - Location
     * @param {number} sunLon - Sidereal Sun longitude
     * @param {number} ayanamsa - Ayanamsa
     * @returns {Object} Pranapada Lagna data
     */
    _calculatePranapadaLagna(date, location, sunLon, ayanamsa) {
        const { sunrise } = Engine.getSunriseSunset(date, location.lat, location.lng);
        if (!sunrise) return this._createLagnaObject(0, 15);

        const msFromSunrise = date.getTime() - sunrise.getTime();
        let minutesFromSunrise = msFromSunrise / (1000 * 60);
        if (minutesFromSunrise < 0) minutesFromSunrise += 24 * 60;

        // Base starting point based on Sun's sign modality
        const sunSignIdx = Math.floor(sunLon / 30);
        const modality = SIGN_MODALITY[sunSignIdx]; // 0: Movable, 1: Fixed, 2: Dual

        let baseLon = sunLon;
        if (modality === 1) baseLon = (sunLon + 240) % 360; // 9th from Sun
        else if (modality === 2) baseLon = (sunLon + 120) % 360; // 5th from Sun

        // Progress 30° per 6 minutes (15 vighatikas)
        const progress = (minutesFromSunrise / 6) * 30;
        const pranapadaLon = (baseLon + progress) % 360;

        return this._createLagnaObject(Math.floor(pranapadaLon / 30), pranapadaLon % 30, pranapadaLon);
    }

    // =========================================================================
    // HELPER METHODS
    // =========================================================================

    /**
     * Create a standardized Lagna object
     * @param {number} signIdx - Sign index (0-11)
     * @param {number} degrees - Degrees within sign (0-30)
     * @param {number} lon - Full longitude (optional)
     * @returns {Object} Lagna object
     */
    _createLagnaObject(signIdx, degrees = 15, lon = null) {
        const actualLon = lon !== null ? lon : (signIdx * 30 + degrees);

        return {
            lon: actualLon,
            rasi: {
                index: signIdx,
                name: RASI_NAMES[signIdx],
                degrees: degrees
            }
        };
    }

    /**
     * Format Lagna for display
     * @param {Object} lagna - Lagna object
     * @returns {string} Formatted string like "Leo 15°23'"
     */
    _formatLagna(lagna) {
        if (!lagna) return null;

        const deg = Math.floor(lagna.rasi.degrees);
        const min = Math.floor((lagna.rasi.degrees - deg) * 60);

        return `${lagna.rasi.name} ${deg}°${min}'`;
    }

    // =========================================================================
    // SPECIAL ANALYSIS METHODS
    // =========================================================================

    /**
     * Get planets in a specific Arudha
     * @param {Object} planets - Planetary positions
     * @param {Object} arudha - Arudha data
     * @returns {Array} List of planets in this Arudha
     */
    getPlanetsInArudha(planets, arudha) {
        const arudhaSign = arudha.rasi.index;
        const planetsInArudha = [];

        Object.entries(planets).forEach(([name, data]) => {
            if (data.rasi?.index === arudhaSign) {
                planetsInArudha.push(name);
            }
        });

        return planetsInArudha;
    }

    /**
     * Calculate aspect/relationship between Lagna and Arudha Lagna
     * @param {number} lagnaIdx - Lagna sign index
     * @param {Object} arudhaLagna - Arudha Lagna data
     * @returns {Object} Relationship analysis
     */
    analyzeArudhaFromLagna(lagnaIdx, arudhaLagna) {
        const alIdx = arudhaLagna.rasi.index;
        const distance = (alIdx - lagnaIdx + 12) % 12;

        // House number (1-12)
        const house = distance + 1;

        // Determine nature based on house
        let nature = 'neutral';
        if ([1, 4, 5, 7, 9, 10].includes(house)) {
            nature = 'favorable';
        } else if ([6, 8, 12].includes(house)) {
            nature = 'challenging';
        }

        return {
            house: house,
            distance: distance,
            nature: nature,
            interpretation: this._getArudhaPlacementInterpretation(house)
        };
    }

    /**
     * Get interpretation for Arudha Lagna placement
     * @param {number} house - House number from Lagna
     * @returns {string} Interpretation key
     */
    _getArudhaPlacementInterpretation(house) {
        const interpretations = {
            1: 'al_in_1st',    // Self-made success
            2: 'al_in_2nd',    // Family wealth
            3: 'al_in_3rd',    // Self effort success
            4: 'al_in_4th',    // Comforts and property
            5: 'al_in_5th',    // Intelligence recognition
            6: 'al_in_6th',    // Hidden enemies affect status
            7: 'al_in_7th',    // Partnership success
            8: 'al_in_8th',    // Sudden changes in status
            9: 'al_in_9th',    // Fortune and dharma
            10: 'al_in_10th',  // Career prominence
            11: 'al_in_11th',  // Gains and fulfillment
            12: 'al_in_12th'   // Foreign success, expenses
        };

        return interpretations[house] || 'al_general';
    }

    /**
     * Analyze Upapada for marriage indications
     * @param {Object} upapada - Upapada data
     * @param {Object} planets - Planetary positions
     * @param {number} lagnaIdx - Lagna sign index
     * @returns {Object} Marriage analysis
     */
    analyzeUpapada(upapada, planets, lagnaIdx) {
        const ulIdx = upapada.rasi.index;
        const ulLord = SIGN_LORDS[ulIdx];
        const planetsInUL = this.getPlanetsInArudha(planets, upapada);

        // Distance from Lagna
        const distanceFromLagna = (ulIdx - lagnaIdx + 12) % 12;

        // Check if UL lord is well-placed
        const ulLordPosition = planets[ulLord]?.rasi?.index;
        let ulLordStrength = 'moderate';

        if (ulLordPosition !== undefined) {
            // Good houses from UL: 1, 2, 4, 5, 7, 9, 10, 11
            const goodHousesFromUL = [0, 1, 3, 4, 6, 8, 9, 10];
            const distFromUL = (ulLordPosition - ulIdx + 12) % 12;

            if (goodHousesFromUL.includes(distFromUL)) {
                ulLordStrength = 'strong';
            } else if ([5, 7, 11].includes(distFromUL)) {
                ulLordStrength = 'weak';
            }
        }

        return {
            sign: upapada.rasi.name,
            signIndex: ulIdx,
            lord: ulLord,
            lordStrength: ulLordStrength,
            planetsInUL: planetsInUL,
            houseFromLagna: distanceFromLagna + 1,
            beneficsInUL: planetsInUL.filter(p => ['Jupiter', 'Venus', 'Moon', 'Mercury'].includes(p)),
            maleficsInUL: planetsInUL.filter(p => ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu'].includes(p))
        };
    }
}

export default new SpecialLagnas();
