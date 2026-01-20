/**
 * ============================================================================
 * JAIMINI SUTRAS - Advanced Jaimini Astrology Calculations
 * ============================================================================
 *
 * This module implements key concepts from Jaimini Sutras:
 * 1. Chara Karakas - Variable significators (7 and 8 karaka systems)
 * 2. Jaimini Aspects - Sign-to-sign aspects (Rashi Drishti)
 * 3. Argala - Planetary intervention system
 * 4. Pada/Arudha calculations
 *
 * References:
 * - Jaimini Sutras
 * - Brihat Parashara Hora Shastra (BPHS)
 * - Jaimini Upadesa Sutras (P.S. Sastri translation)
 *
 * @module jaimini
 * @version 1.0.0
 */

import I18n from '../core/i18n.js';
import {
    RASI_NAMES,
    SIGN_LORDS,
    SIGN_MODALITY,
    NAVAGRAHA,
    SAPTA_GRAHA
} from './constants.js';

// ============================================================================
// CHARA KARAKAS (Variable Significators)
// ============================================================================

/**
 * The eight Chara Karakas in order of significance
 * These are determined by planetary longitude within signs
 */
export const KARAKA_NAMES = Object.freeze([
    { key: 'AK', name: 'Atmakaraka', nameKey: 'jaimini.karakas.atmakaraka', signification: 'Soul, Self, King of the chart' },
    { key: 'AmK', name: 'Amatyakaraka', nameKey: 'jaimini.karakas.amatyakaraka', signification: 'Minister, Career, Mind' },
    { key: 'BK', name: 'Bhratrikaraka', nameKey: 'jaimini.karakas.bhratrikaraka', signification: 'Siblings, Courage, Initiative' },
    { key: 'MK', name: 'Matrikaraka', nameKey: 'jaimini.karakas.matrikaraka', signification: 'Mother, Happiness, Education' },
    { key: 'PiK', name: 'Pitrikaraka', nameKey: 'jaimini.karakas.pitrikaraka', signification: 'Father, Luck, Guru' },
    { key: 'PuK', name: 'Putrakaraka', nameKey: 'jaimini.karakas.putrakaraka', signification: 'Children, Intelligence, Mantra' },
    { key: 'GK', name: 'Gnatikaraka', nameKey: 'jaimini.karakas.gnatikaraka', signification: 'Relatives, Enemies, Disease' },
    { key: 'DK', name: 'Darakaraka', nameKey: 'jaimini.karakas.darakaraka', signification: 'Spouse, Partner, Relationships' }
]);

/**
 * Planets eligible for Chara Karaka assignment
 * 7-karaka system: Sun to Saturn (excludes Rahu)
 * 8-karaka system: Sun to Rahu (excludes Ketu)
 */
const KARAKA_PLANETS_7 = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
const KARAKA_PLANETS_8 = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu'];

/**
 * Calculate Chara Karakas based on planetary degrees
 * Planets are sorted by their degree within sign (highest = AK, lowest = DK)
 * 
 * Production-Grade Tie-breaking:
 * 1. Longitude within sign (including arc-seconds)
 * 2. If longitude is identical, use natural planetary strength (Sun > Moon > Mars...)
 *
 * @param {Object} positions - Planet positions { planet: { sign, degree, lon } }
 * @param {boolean} useEightKarakas - Use 8-karaka system (includes Rahu)
 * @returns {Object} Karaka assignments
 */
export function calculateCharaKarakas(positions, useEightKarakas = true) {
    const planets = useEightKarakas ? KARAKA_PLANETS_8 : KARAKA_PLANETS_7;
    const karakaCount = useEightKarakas ? 8 : 7;

    // Natural strength order for tie-breaking (BPHS)
    const naturalStrength = ['Sun', 'Moon', 'Venus', 'Jupiter', 'Mercury', 'Mars', 'Saturn', 'Rahu'];

    // Get degrees for sorting
    const planetDegrees = planets.map(planet => {
        const pos = positions[planet];
        if (!pos) return { planet, degree: 0, priority: 0 };

        // Use full precision degree (0-30 range)
        let degree = (pos.lon % 30) || pos.degree || 0;

        // For Rahu, use 30 - degree (retrograde consideration)
        if (planet === 'Rahu') {
            degree = 30 - degree;
        }

        return { 
            planet, 
            degree, 
            priority: naturalStrength.indexOf(planet) 
        };
    });

    // Sort by degree descending (highest degree = AK)
    // Tie-breaker: If degrees are identical, the planet with higher natural priority wins
    planetDegrees.sort((a, b) => {
        if (Math.abs(a.degree - b.degree) < 0.000001) {
            return a.priority - b.priority;
        }
        return b.degree - a.degree;
    });

    // Assign karakas
    const result = {
        karakas: {},
        planetToKaraka: {},
        system: useEightKarakas ? '8-karaka' : '7-karaka'
    };

    const karakaKeys = KARAKA_NAMES.slice(0, karakaCount).map(k => k.key);

    for (let i = 0; i < karakaCount; i++) {
        const karakaKey = karakaKeys[i];
        const planet = planetDegrees[i].planet;
        const karakaInfo = KARAKA_NAMES[i];

        result.karakas[karakaKey] = {
            planet,
            degree: planetDegrees[i].degree,
            name: I18n.t(karakaInfo.nameKey),
            nameKey: karakaInfo.nameKey,
            signification: I18n.t(`jaimini.karakas.significations.${karakaKey}`)
        };

        result.planetToKaraka[planet] = karakaKey;
    }

    return result;
}

// ============================================================================
// JAIMINI ASPECTS (Rashi Drishti)
// ============================================================================

/**
 * Jaimini aspects are sign-to-sign, not planet-to-planet
 *
 * Rules:
 * - Movable (Chara) signs aspect Fixed (Sthira) signs except the adjacent one
 * - Fixed (Sthira) signs aspect Movable (Chara) signs except the adjacent one
 * - Dual (Dwiswabhava) signs aspect each other
 *
 * Sign Modalities (0-indexed):
 * Movable (0): Aries(0), Cancer(3), Libra(6), Capricorn(9)
 * Fixed (1): Taurus(1), Leo(4), Scorpio(7), Aquarius(10)
 * Dual (2): Gemini(2), Virgo(5), Sagittarius(8), Pisces(11)
 */

/**
 * Get the modality of a sign
 * @param {number} signIndex - Sign index (0-11)
 * @returns {number} 0=Movable, 1=Fixed, 2=Dual
 */
export function getSignModality(signIndex) {
    return SIGN_MODALITY[signIndex];
}

/**
 * Get signs of a specific modality
 * @param {number} modality - 0=Movable, 1=Fixed, 2=Dual
 * @returns {number[]} Array of sign indices
 */
export function getSignsByModality(modality) {
    return Object.entries(SIGN_MODALITY)
        .filter(([_, mod]) => mod === modality)
        .map(([sign]) => parseInt(sign));
}

/**
 * Calculate Jaimini aspects from a sign
 * @param {number} fromSign - Sign index (0-11)
 * @returns {number[]} Array of aspected sign indices
 */
export function calculateJaiminiAspects(fromSign) {
    const modality = SIGN_MODALITY[fromSign];
    const aspectedSigns = [];

    if (modality === 0) {
        // Movable signs aspect Fixed signs except adjacent
        const fixedSigns = getSignsByModality(1); // [1, 4, 7, 10]
        for (const sign of fixedSigns) {
            // Adjacent means 1 sign away
            const distance = Math.abs(sign - fromSign);
            if (distance !== 1 && distance !== 11) {
                aspectedSigns.push(sign);
            }
        }
    } else if (modality === 1) {
        // Fixed signs aspect Movable signs except adjacent
        const movableSigns = getSignsByModality(0); // [0, 3, 6, 9]
        for (const sign of movableSigns) {
            const distance = Math.abs(sign - fromSign);
            if (distance !== 1 && distance !== 11) {
                aspectedSigns.push(sign);
            }
        }
    } else {
        // Dual signs aspect other Dual signs
        const dualSigns = getSignsByModality(2); // [2, 5, 8, 11]
        for (const sign of dualSigns) {
            if (sign !== fromSign) {
                aspectedSigns.push(sign);
            }
        }
    }

    return aspectedSigns.sort((a, b) => a - b);
}

/**
 * Check if two signs have Jaimini aspect relationship
 * @param {number} sign1 - First sign index
 * @param {number} sign2 - Second sign index
 * @returns {boolean} True if sign1 aspects sign2
 */
export function hasJaiminiAspect(sign1, sign2) {
    const aspects = calculateJaiminiAspects(sign1);
    return aspects.includes(sign2);
}

/**
 * Get all Jaimini aspects in a chart (sign-to-sign)
 * @param {Object} positions - Planet positions
 * @returns {Object} Aspect relationships
 */
export function getChartJaiminiAspects(positions) {
    const result = {};

    // Group planets by sign
    const planetsBySign = {};
    for (let i = 0; i < 12; i++) {
        planetsBySign[i] = [];
    }

    for (const [planet, pos] of Object.entries(positions)) {
        if (pos && typeof pos.sign === 'number') {
            planetsBySign[pos.sign].push(planet);
        }
    }

    // Calculate aspects for each occupied sign
    for (let sign = 0; sign < 12; sign++) {
        if (planetsBySign[sign].length === 0) continue;

        const aspects = calculateJaiminiAspects(sign);
        result[sign] = {
            planets: planetsBySign[sign],
            aspects: aspects.map(aspSign => ({
                sign: aspSign,
                signName: RASI_NAMES[aspSign],
                planets: planetsBySign[aspSign]
            }))
        };
    }

    return result;
}

// ============================================================================
// ARGALA (Planetary Intervention)
// ============================================================================

/**
 * Argala is the intervention/influence of planets from specific houses
 *
 * Primary Argala houses: 2nd, 4th, 11th, 5th
 * Obstruction (Virodha Argala) houses: 12th (obstructs 2nd), 10th (obstructs 4th),
 *                                       3rd (obstructs 11th), 9th (obstructs 5th)
 */

export const ARGALA_HOUSES = Object.freeze({
    primary: {
        2: { name: 'Dhana Argala', obstruction: 12, type: 'Wealth' },
        4: { name: 'Sukha Argala', obstruction: 10, type: 'Happiness' },
        11: { name: 'Labha Argala', obstruction: 3, type: 'Gains' },
        5: { name: 'Putra Argala', obstruction: 9, type: 'Children/Intelligence' }
    },
    secondary: {
        3: { name: 'Vikrama Argala', type: 'Courage (weak)' }
    }
});

/**
 * Calculate Argala for a specific house/planet
 * @param {number} targetHouse - House to check argala on (1-12)
 * @param {Object} planetsByHouse - Planets in each house { 1: [...], 2: [...] }
 * @param {number} lagnaRasi - Lagna sign index
 * @returns {Object} Argala analysis
 */
export function calculateArgala(targetHouse, planetsByHouse, lagnaRasi) {
    const result = {
        targetHouse,
        argalas: [],
        obstructed: [],
        netEffect: 'Neutral'
    };

    let beneficCount = 0;
    let maleficCount = 0;

    for (const [houseOffset, info] of Object.entries(ARGALA_HOUSES.primary)) {
        const argalaHouse = ((targetHouse - 1 + parseInt(houseOffset)) % 12) + 1;
        const obstructHouse = ((targetHouse - 1 + info.obstruction) % 12) + 1;

        const argalaPlanets = planetsByHouse[argalaHouse] || [];
        const obstructPlanets = planetsByHouse[obstructHouse] || [];

        if (argalaPlanets.length > 0) {
            // Check if obstructed
            const isObstructed = obstructPlanets.length >= argalaPlanets.length;

            const argalaEntry = {
                house: argalaHouse,
                type: I18n.t(`jaimini.argala.types.${info.type}`),
                name: I18n.t(`jaimini.argala.${info.name.toLowerCase().replace(' ', '_')}`),
                planets: argalaPlanets,
                obstructedBy: isObstructed ? obstructPlanets : [],
                active: !isObstructed
            };

            if (isObstructed) {
                result.obstructed.push(argalaEntry);
            } else {
                result.argalas.push(argalaEntry);

                // Count benefic/malefic
                for (const p of argalaPlanets) {
                    if (['Jupiter', 'Venus', 'Moon', 'Mercury'].includes(p)) {
                        beneficCount++;
                    } else {
                        maleficCount++;
                    }
                }
            }
        }
    }

    // Determine net effect
    if (beneficCount > maleficCount) {
        result.netEffect = 'Benefic';
    } else if (maleficCount > beneficCount) {
        result.netEffect = 'Malefic';
    }

    return result;
}

// ============================================================================
// ARUDHA/PADA CALCULATIONS
// ============================================================================

/**
 * Calculate Arudha Pada for any house
 *
 * Formula:
 * 1. Find the lord of the house
 * 2. Count signs from the house to where the lord is placed
 * 3. Count the same number from the lord's position
 * 4. The resulting sign is the Arudha
 *
 * Exception: If Arudha falls in the same house or 7th from it, move it to the 10th
 *
 * @param {number} houseNumber - House number (1-12)
 * @param {number} lagnaRasi - Lagna sign index (0-11)
 * @param {Object} positions - Planet positions
 * @returns {Object} Arudha pada calculation
 */
export function calculateArudhaPada(houseNumber, lagnaRasi, positions) {
    // Get sign of the house
    const houseSign = (lagnaRasi + houseNumber - 1) % 12;

    // Get lord of the house sign
    const lord = SIGN_LORDS[houseSign];

    // Get lord's position
    const lordPos = positions[lord];
    if (!lordPos || lordPos.sign === undefined) {
        return {
            house: houseNumber,
            sign: null,
            lord,
            error: 'Lord position not found'
        };
    }

    const lordSign = lordPos.sign;

    // Count from house to lord
    let distance = (lordSign - houseSign + 12) % 12;

    // Count same distance from lord
    let arudhaSign = (lordSign + distance) % 12;

    // Jaimini Arudha Exceptions (Classical Rules):
    // 1. If Arudha is in the same sign as the house: Move 10 houses forward
    // 2. If Arudha is in the 7th sign from the house: Move 10 houses forward (resulting in 4th from house)
    
    const arudhaHouseFromOriginal = (arudhaSign - houseSign + 12) % 12;
    if (arudhaHouseFromOriginal === 0) {
        arudhaSign = (houseSign + 9) % 12; // 10th from house
    } else if (arudhaHouseFromOriginal === 6) {
        arudhaSign = (houseSign + 3) % 12; // 4th from house (10th from 7th)
    }

    // Calculate house from Lagna
    const arudhaHouse = (arudhaSign - lagnaRasi + 12) % 12 + 1;

    return {
        house: houseNumber,
        name: `A${houseNumber}`,
        sign: arudhaSign,
        signName: RASI_NAMES[arudhaSign],
        arudhaHouse,
        lord,
        lordSign,
        distance
    };
}

/**
 * Calculate all 12 Arudha Padas
 * @param {number} lagnaRasi - Lagna sign index
 * @param {Object} positions - Planet positions
 * @returns {Object} All arudha padas
 */
export function calculateAllArudhaPadas(lagnaRasi, positions) {
    const result = {};

    for (let house = 1; house <= 12; house++) {
        result[house] = calculateArudhaPada(house, lagnaRasi, positions);
    }

    // Add special names
    result[1].specialName = I18n.t('jaimini.padas.names.AL');
    result[7].specialName = I18n.t('jaimini.padas.names.A7');
    result[12].specialName = I18n.t('jaimini.padas.names.UL');
    result[2].specialName = I18n.t('jaimini.padas.names.A2');
    result[4].specialName = I18n.t('jaimini.padas.names.A4');
    result[5].specialName = I18n.t('jaimini.padas.names.A5');
    result[9].specialName = I18n.t('jaimini.padas.names.A9');
    result[10].specialName = I18n.t('jaimini.padas.names.A10');

    return result;
}

// ============================================================================
// KARAKAMSA ANALYSIS
// ============================================================================

/**
 * Calculate Karakamsa (Atmakaraka in Navamsha)
 * This is crucial for determining life purpose and spiritual path
 *
 * @param {Object} rasiPositions - Rasi chart positions
 * @param {Object} navamshaPositions - Navamsha positions
 * @param {boolean} useEightKarakas - Use 8-karaka system
 * @returns {Object} Karakamsa analysis
 */
export function calculateKarakamsa(rasiPositions, navamshaPositions, useEightKarakas = true) {
    // Get Chara Karakas
    const karakas = calculateCharaKarakas(rasiPositions, useEightKarakas);
    const atmakaraka = karakas.karakas.AK.planet;

    // Get AK position in Navamsha
    const akNavamshaPos = navamshaPositions?.[atmakaraka];
    if (!akNavamshaPos) {
        return {
            atmakaraka,
            karakamsa: null,
            error: 'Navamsha position not found'
        };
    }

    const karakamsaSign = akNavamshaPos.sign;

    // Analyze planets in/aspecting Karakamsa
    const planetsInKarakamsa = [];
    const planetsAspectingKarakamsa = [];

    for (const [planet, pos] of Object.entries(navamshaPositions)) {
        if (!pos || pos.sign === undefined) continue;

        if (pos.sign === karakamsaSign) {
            planetsInKarakamsa.push(planet);
        }

        // Check Jaimini aspects
        if (hasJaiminiAspect(pos.sign, karakamsaSign)) {
            planetsAspectingKarakamsa.push(planet);
        }
    }

    // Generate interpretation based on Karakamsa sign
    const interpretation = getKarakamsaInterpretation(karakamsaSign, planetsInKarakamsa);

    return {
        atmakaraka,
        karakamsa: karakamsaSign,
        karakamsaName: RASI_NAMES[karakamsaSign],
        planetsInKarakamsa,
        planetsAspectingKarakamsa,
        interpretation
    };
}

/**
 * Get interpretation for Karakamsa placement
 */
function getKarakamsaInterpretation(sign, planets) {
    let interpretation = I18n.t(`jaimini.karakamsa.interpretations.${sign}`);

    // Add planet-specific interpretations
    if (planets.includes('Sun')) {
        interpretation += ' ' + I18n.t('jaimini.karakamsa.planets.Sun');
    }
    if (planets.includes('Moon')) {
        interpretation += ' ' + I18n.t('jaimini.karakamsa.planets.Moon');
    }
    if (planets.includes('Jupiter')) {
        interpretation += ' ' + I18n.t('jaimini.karakamsa.planets.Jupiter');
    }
    if (planets.includes('Venus')) {
        interpretation += ' ' + I18n.t('jaimini.karakamsa.planets.Venus');
    }
    if (planets.includes('Ketu')) {
        interpretation += ' ' + I18n.t('jaimini.karakamsa.planets.Ketu');
    }

    return interpretation;
}

// ============================================================================
// MAIN JAIMINI CALCULATOR
// ============================================================================

/**
 * Calculate all Jaimini parameters for a chart
 * @param {Object} chartData - Full chart data
 * @returns {Object} Complete Jaimini analysis
 */
export function calculateJaiminiChart(chartData) {
    const { planets, lagnaRasi, navamshaPositions } = chartData;

    // Build planets by house
    const planetsByHouse = {};
    for (let h = 1; h <= 12; h++) {
        planetsByHouse[h] = [];
    }

    for (const [planet, pos] of Object.entries(planets)) {
        if (pos && typeof pos.sign === 'number') {
            const house = ((pos.sign - lagnaRasi + 12) % 12) + 1;
            planetsByHouse[house].push(planet);
        }
    }

    return {
        charaKarakas: calculateCharaKarakas(planets, true),
        charaKarakas7: calculateCharaKarakas(planets, false),
        jaiminiAspects: getChartJaiminiAspects(planets),
        arudhaPadas: calculateAllArudhaPadas(lagnaRasi, planets),
        karakamsa: navamshaPositions ? calculateKarakamsa(planets, navamshaPositions, true) : null,
        argala: {
            lagna: calculateArgala(1, planetsByHouse, lagnaRasi),
            moon: calculateArgala(((planets.Moon?.sign - lagnaRasi + 12) % 12) + 1, planetsByHouse, lagnaRasi)
        }
    };
}

// ============================================================================
// EXPORTS
// ============================================================================

export const JaiminiEngine = {
    calculateCharaKarakas,
    calculateJaiminiAspects,
    hasJaiminiAspect,
    getChartJaiminiAspects,
    calculateArgala,
    calculateArudhaPada,
    calculateAllArudhaPadas,
    calculateKarakamsa,
    calculateJaiminiChart,
    KARAKA_NAMES,
    ARGALA_HOUSES
};

export default JaiminiEngine;
