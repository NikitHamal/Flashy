/**
 * ============================================================================
 * PLANETARY AVASTHAS - States of Planets
 * ============================================================================
 *
 * This module implements the three primary Avastha systems from Vedic astrology:
 * 1. Baladi Avasthas (Age-based states) - Physical/material manifestation
 * 2. Jagratadi Avasthas (Consciousness states) - Level of awareness/activity
 * 3. Lajjitadi Avasthas (Dignity-based states) - Psychological/behavioral states
 *
 * References:
 * - Brihat Parashara Hora Shastra (BPHS) Chapter 45
 * - Phaladeepika
 * - Saravali
 *
 * @module avasthas
 * @version 1.0.0
 */

import I18n from '../core/i18n.js';
import {
    SAPTA_GRAHA,
    NAVAGRAHA,
    EXALTATION,
    DEBILITATION,
    OWN_SIGNS,
    MOOLATRIKONA,
    NATURAL_FRIENDS,
    NATURAL_ENEMIES,
    SIGN_LORDS
} from './constants.js';

// ============================================================================
// BALADI AVASTHAS (Age-Based States)
// ============================================================================

/**
 * The five Baladi Avasthas represent the age/maturity of a planet
 * Each state gives different percentage of results
 */
export const BALADI_STATES = Object.freeze({
    BALA: { nameKey: 'avasthas.baladi.bala', strength: 0.25 },
    KUMARA: { nameKey: 'avasthas.baladi.kumara', strength: 0.50 },
    YUVA: { nameKey: 'avasthas.baladi.yuva', strength: 1.00 },
    VRIDDHA: { nameKey: 'avasthas.baladi.vriddha', strength: 0.50 },
    MRITA: { nameKey: 'avasthas.baladi.mrita', strength: 0.00 }
});

/**
 * Baladi state order for odd signs (Aries, Gemini, Leo, Libra, Sagittarius, Aquarius)
 * Dividing 30 degrees into 5 equal parts of 6 degrees each
 */
const BALADI_ODD_ORDER = ['BALA', 'KUMARA', 'YUVA', 'VRIDDHA', 'MRITA'];

/**
 * Baladi state order for even signs (Taurus, Cancer, Virgo, Scorpio, Capricorn, Pisces)
 * Reverse order for even signs
 */
const BALADI_EVEN_ORDER = ['MRITA', 'VRIDDHA', 'YUVA', 'KUMARA', 'BALA'];

/**
 * Calculate Baladi Avastha for a planet
 * @param {number} signIndex - Sign index (0-11)
 * @param {number} degree - Degree within sign (0-30)
 * @returns {Object} Baladi avastha details
 */
export function calculateBaladiAvastha(signIndex, degree) {
    const isOddSign = signIndex % 2 === 0; // 0=Aries (odd), 1=Taurus (even)
    const division = Math.floor(degree / 6);
    const stateOrder = isOddSign ? BALADI_ODD_ORDER : BALADI_EVEN_ORDER;
    const stateKey = stateOrder[Math.min(division, 4)];
    const state = BALADI_STATES[stateKey];

    const lowerKey = stateKey.toLowerCase();

    return {
        state: stateKey,
        name: I18n.t(state.nameKey),
        nameKey: state.nameKey,
        strength: state.strength,
        description: I18n.t(`avasthas.baladi.descriptions.${lowerKey}`),
        resultPercentage: state.strength * 100
    };
}

// ============================================================================
// JAGRATADI AVASTHAS (Consciousness States)
// ============================================================================

/**
 * The three Jagratadi Avasthas represent the consciousness level of a planet
 */
export const JAGRATADI_STATES = Object.freeze({
    JAGRATA: { nameKey: 'avasthas.jagratadi.jagrata', strength: 1.00 },
    SWAPNA: { nameKey: 'avasthas.jagratadi.swapna', strength: 0.50 },
    SUSHUPTI: { nameKey: 'avasthas.jagratadi.sushupti', strength: 0.00 }
});

/**
 * Calculate Jagratadi Avastha based on planet's sign placement
 * - Jagrata (Awake): Planet in own sign, exaltation, or friend's sign
 * - Swapna (Dreaming): Planet in neutral sign
 * - Sushupti (Sleep): Planet in enemy sign or debilitation
 *
 * @param {string} planet - Planet name
 * @param {number} signIndex - Sign index (0-11)
 * @returns {Object} Jagratadi avastha details
 */
export function calculateJagratAvastha(planet, signIndex) {
    const getResult = (stateKey, reason) => {
        const state = JAGRATADI_STATES[stateKey];
        const lowerKey = stateKey.toLowerCase();
        return {
            state: stateKey,
            name: I18n.t(state.nameKey),
            nameKey: state.nameKey,
            strength: state.strength,
            description: I18n.t(`avasthas.jagratadi.descriptions.${lowerKey}`),
            reason: I18n.t(`avasthas.jagratadi.reasons.${reason}`)
        };
    };

    // Check exaltation
    const exaltData = EXALTATION[planet];
    if (exaltData && exaltData.sign === signIndex) {
        return getResult('JAGRATA', 'exalted');
    }

    // Check debilitation
    if (DEBILITATION[planet] === signIndex) {
        return getResult('SUSHUPTI', 'debilitated');
    }

    // Check own sign
    if (OWN_SIGNS[planet]?.includes(signIndex)) {
        return getResult('JAGRATA', 'own_sign');
    }

    // Check moolatrikona
    const moola = MOOLATRIKONA[planet];
    if (moola && moola.sign === signIndex) {
        return getResult('JAGRATA', 'moolatrikona');
    }

    // Check friendship with sign lord
    const signLord = SIGN_LORDS[signIndex];
    if (signLord) {
        const friends = NATURAL_FRIENDS[planet] || [];
        const enemies = NATURAL_ENEMIES[planet] || [];

        if (friends.includes(signLord)) {
            return getResult('JAGRATA', 'friend_sign');
        }

        if (enemies.includes(signLord)) {
            return getResult('SUSHUPTI', 'enemy_sign');
        }
    }

    // Neutral sign
    return getResult('SWAPNA', 'neutral_sign');
}

// ============================================================================
// SAYANAADI AVASTHAS (12 Microscopic States)
// ============================================================================

/**
 * The twelve Sayanaadi Avasthas represent specific activities of a planet
 */
export const SAYANAADI_STATES = Object.freeze({
    SAYANA: { nameKey: 'avasthas.sayanaadi.sayana' },      // Resting
    UPAVESANA: { nameKey: 'avasthas.sayanaadi.upavesana' },// Sitting
    NETRAPANI: { nameKey: 'avasthas.sayanaadi.netrapani' },// Eyes on hand (Ready)
    PRAKASANA: { nameKey: 'avasthas.sayanaadi.prakasana' },// Shining
    GAMANA: { nameKey: 'avasthas.sayanaadi.gamana' },      // Going
    AGAMANA: { nameKey: 'avasthas.sayanaadi.agamana' },    // Coming
    SABHA: { nameKey: 'avasthas.sayanaadi.sabha' },        // In assembly
    AGAMA: { nameKey: 'avasthas.sayanaadi.agama' },        // Acquisition
    BHOJANA: { nameKey: 'avasthas.sayanaadi.bhojana' },    // Eating
    NRITYALIPSA: { nameKey: 'avasthas.sayanaadi.nrityalipsa' },// Desire to dance
    KAUTUKA: { nameKey: 'avasthas.sayanaadi.kautuka' },    // Curiosity/Eagerness
    NIDRA: { nameKey: 'avasthas.sayanaadi.nidra' }         // Sleep
});

/**
 * Calculate Sayanaadi Avastha for a planet
 * Formula: (PlanetIndex * NakshatraIndex * NavamshaIndex + BirthGhati) % 12
 * We use high-precision longitudes to derive these indices.
 */
export function calculateSayanaadiAvastha(planet, chartData) {
    const planetMap = { Sun: 1, Moon: 2, Mars: 3, Mercury: 4, Jupiter: 5, Venus: 6, Saturn: 7, Rahu: 8, Ketu: 9 };
    const pIdx = planetMap[planet];
    const pos = chartData.planets[planet];
    if (!pos || !chartData.panchang) return null;

    // Components for formula
    let nakIdx = 0;
    if (chartData.planets.Moon.nakshatra) {
        nakIdx = chartData.planets.Moon.nakshatra.index + 1;
    } else {
        // Fallback: Calculate from longitude if missing
        const moonLon = chartData.planets.Moon.lon;
        nakIdx = Math.floor(moonLon / (360 / 27)) + 1;
    }
    const deg = (pos.sign * 30) + (pos.degree || 0);
    const navIdx = Math.floor(deg / 3.333333) + 1;
    
    // Time component: Ghati of birth (starts from Sunrise)
    const birthDate = new Date(chartData.date);
    const sunrise = chartData.panchang?.sunrise || new Date(birthDate.getFullYear(), birthDate.getMonth(), birthDate.getDate(), 6, 0, 0);
    
    let msFromSunrise = birthDate.getTime() - sunrise.getTime();
    if (msFromSunrise < 0) {
        // Birth before sunrise, use previous sunrise
        msFromSunrise += 24 * 60 * 60 * 1000;
    }
    
    const hoursFromSunrise = msFromSunrise / (1000 * 60 * 60);
    const ghatiProxy = Math.floor(hoursFromSunrise * 2.5); // 1 hour = 2.5 ghatis

    // Canonical BPHS Formula: ((P * N * Nav) + G) % 12
    let result = ((pIdx * nakIdx * navIdx) + ghatiProxy) % 12;
    if (result === 0) result = 12;

    const stateKeys = Object.keys(SAYANAADI_STATES);
    const stateKey = stateKeys[result - 1];
    const state = SAYANAADI_STATES[stateKey];

    return {
        state: stateKey,
        name: I18n.t(state.nameKey),
        nameKey: state.nameKey,
        description: I18n.t(`avasthas.sayanaadi.descriptions.${stateKey.toLowerCase()}`)
    };
}

// ============================================================================
// DEEPTADI AVASTHAS (Dignity-Based States)
// ============================================================================

/**
 * The nine Deeptadi Avasthas represent the attitude of a planet based on dignity
 */
export const DEEPTADI_STATES = Object.freeze({
    DEEPTA: { nameKey: 'avasthas.deeptadi.deepta', nature: 'Highly Benefic' }, // Exalted
    SWASTHA: { nameKey: 'avasthas.deeptadi.swastha', nature: 'Benefic' }, // Own sign
    MUDITA: { nameKey: 'avasthas.deeptadi.mudita', nature: 'Benefic' }, // Friend sign
    SHANTA: { nameKey: 'avasthas.deeptadi.shanta', nature: 'Benefic' }, // Benefic varga
    DEENA: { nameKey: 'avasthas.deeptadi.deena', nature: 'Neutral' }, // Neutral sign
    DUKHITA: { nameKey: 'avasthas.deeptadi.dukhita', nature: 'Malefic' }, // Enemy sign
    VIKALA: { nameKey: 'avasthas.deeptadi.vikala', nature: 'Malefic' }, // Conjunct malefic
    KHALA: { nameKey: 'avasthas.deeptadi.khala', nature: 'Malefic' }, // Debilitated
    KHOBHITA: { nameKey: 'avasthas.deeptadi.khobhita', nature: 'Malefic' } // Combust
});

/**
 * Calculate Deeptadi Avastha based on BPHS rules
 * @param {string} planet - Planet name
 * @param {Object} chartData - Chart data with dignity and aspects
 */
export function calculateDeeptadiAvastha(planet, chartData) {
    const pos = chartData.planets[planet];
    if (!pos) return null;

    const sign = pos.sign;
    const dignity = getDignityStatus(planet, sign);
    
    let stateKey = 'DEENA'; // Default

    if (dignity === 'Exalted') stateKey = 'DEEPTA';
    else if (dignity === 'Own') stateKey = 'SWASTHA';
    else if (dignity === 'Friend') stateKey = 'MUDITA';
    else if (dignity === 'Debilitated') stateKey = 'KHALA';
    else if (dignity === 'Enemy') stateKey = 'DUKHITA';

    // Overrides for special conditions
    if (chartData.sunDistance?.[planet] <= 10) stateKey = 'KHOBHITA';
    else if (chartData.conjunctions?.[planet]?.some(p => ['Mars', 'Saturn', 'Rahu', 'Ketu'].includes(p))) {
        // If already bad, keep it, else it becomes Vikala
        if (!['KHALA', 'DUKHITA', 'KHOBHITA'].includes(stateKey)) stateKey = 'VIKALA';
    }

    const state = DEEPTADI_STATES[stateKey];
    return {
        state: stateKey,
        name: I18n.t(state.nameKey),
        nameKey: state.nameKey,
        nature: state.nature,
        description: I18n.t(`avasthas.deeptadi.descriptions.${stateKey.toLowerCase()}`)
    };
}

function getDignityStatus(planet, signIndex) {
    if (EXALTATION[planet]?.sign === signIndex) return 'Exalted';
    if (DEBILITATION[planet] === signIndex) return 'Debilitated';
    if (OWN_SIGNS[planet]?.includes(signIndex)) return 'Own';
    
    const signLord = SIGN_LORDS[signIndex];
    if (NATURAL_FRIENDS[planet]?.includes(signLord)) return 'Friend';
    if (NATURAL_ENEMIES[planet]?.includes(signLord)) return 'Enemy';
    return 'Neutral';
}

// ============================================================================
// LAJJITADI AVASTHAS (Psychological States)
// ============================================================================

/**
 * The nine Lajjitadi Avasthas represent psychological/behavioral states
 * Per BPHS Chapter 45, these depend on conjunctions and aspects
 */
export const LAJJITADI_STATES = Object.freeze({
    LAJJITA: {
        nameKey: 'avasthas.lajjitadi.lajjita',
        nature: 'Malefic'
    },
    GARVITA: {
        nameKey: 'avasthas.lajjitadi.garvita',
        nature: 'Benefic'
    },
    KSHUDITA: {
        nameKey: 'avasthas.lajjitadi.kshudita',
        nature: 'Malefic'
    },
    TRUSHITA: {
        nameKey: 'avasthas.lajjitadi.trushita',
        nature: 'Malefic'
    },
    MUDITA: {
        nameKey: 'avasthas.lajjitadi.mudita',
        nature: 'Benefic'
    },
    KSHOBHITA: {
        nameKey: 'avasthas.lajjitadi.kshobhita',
        nature: 'Malefic'
    },
    DIPTA: {
        nameKey: 'avasthas.lajjitadi.dipta',
        nature: 'Highly Benefic'
    },
    NIRVEDA: {
        nameKey: 'avasthas.lajjitadi.nirveda',
        nature: 'Malefic'
    },
    SUVIRYATA: {
        nameKey: 'avasthas.lajjitadi.suviryata',
        nature: 'Benefic'
    }
});

/**
 * Watery signs for Trushita calculation
 */
const WATERY_SIGNS = [3, 7, 11]; // Cancer, Scorpio, Pisces

/**
 * Calculate all applicable Lajjitadi Avasthas for a planet
 * A planet can have multiple Lajjitadi states simultaneously
 *
 * @param {string} planet - Planet name
 * @param {number} signIndex - Sign index (0-11)
 * @param {number} house - House number (1-12)
 * @param {Object} chartData - Full chart data with conjunctions and aspects
 * @returns {Object[]} Array of applicable Lajjitadi avasthas
 */
export function calculateLajjitadiAvasthas(planet, signIndex, house, chartData) {
    const avasthas = [];
    const signLord = SIGN_LORDS[signIndex];
    const conjunctions = chartData.conjunctions?.[planet] || [];
    const aspects = chartData.aspects?.[planet] || [];

    const getResult = (stateKey, reasonKey, params = {}) => {
        const state = LAJJITADI_STATES[stateKey];
        const lowerKey = stateKey.toLowerCase();
        let reason = I18n.t(`avasthas.lajjitadi.reasons.${reasonKey}`);
        Object.keys(params).forEach(p => {
            reason = reason.replace(`{${p}}`, params[p]);
        });

        return {
            state: stateKey,
            name: I18n.t(state.nameKey),
            nameKey: state.nameKey,
            nature: state.nature,
            description: I18n.t(`avasthas.lajjitadi.descriptions.${lowerKey}`),
            effects: I18n.t(`avasthas.lajjitadi.effects.${lowerKey}`),
            reason: reason
        };
    };

    // 1. GARVITA (Proud) - In exaltation or moolatrikona
    const exaltData = EXALTATION[planet];
    const moola = MOOLATRIKONA[planet];

    if (exaltData && exaltData.sign === signIndex) {
        avasthas.push(getResult('GARVITA', 'exalted'));
        // Also DIPTA for exaltation
        avasthas.push(getResult('DIPTA', 'dipta_exalted'));
    } else if (moola && moola.sign === signIndex) {
        avasthas.push(getResult('GARVITA', 'moolatrikona'));
    }

    // 2. NIRVEDA (Dejected) - In debilitation
    if (DEBILITATION[planet] === signIndex) {
        avasthas.push(getResult('NIRVEDA', 'debilitated'));
    }

    // 3. SUVIRYATA (Heroic) - In own sign
    if (OWN_SIGNS[planet]?.includes(signIndex)) {
        avasthas.push(getResult('SUVIRYATA', 'own_sign'));
    }

    // 4. LAJJITA (Ashamed) - Planet in 5th house with Rahu/Ketu/Saturn
    if (house === 5) {
        const maleficsIn5th = conjunctions.filter(p => ['Rahu', 'Ketu', 'Saturn'].includes(p));
        if (maleficsIn5th.length > 0) {
            const planetNames = maleficsIn5th.map(p => I18n.t(`planets.${p}`)).join(', ');
            avasthas.push(getResult('LAJJITA', 'lajjita_5th', { planets: planetNames }));
        }
    }

    // 5. KSHUDITA (Hungry) - In enemy sign or aspected by enemy
    if (signLord) {
        const enemies = NATURAL_ENEMIES[planet] || [];
        if (enemies.includes(signLord)) {
            avasthas.push(getResult('KSHUDITA', 'kshudita_enemy_sign', { signLord: I18n.t(`planets.${signLord}`) }));
        }

        // Check if aspected by enemy
        const enemyAspects = aspects.filter(p => enemies.includes(p));
        if (enemyAspects.length > 0) {
            const planetNames = enemyAspects.map(p => I18n.t(`planets.${p}`)).join(', ');
            avasthas.push(getResult('KSHUDITA', 'kshudita_enemy_aspect', { planets: planetNames }));
        }
    }

    // 6. TRUSHITA (Thirsty) - In watery sign, aspected by enemy, no benefic aspect
    if (WATERY_SIGNS.includes(signIndex)) {
        const enemies = NATURAL_ENEMIES[planet] || [];
        const enemyAspects = aspects.filter(p => enemies.includes(p));
        const beneficAspects = aspects.filter(p => ['Jupiter', 'Venus'].includes(p) ||
            (p === 'Moon' && chartData.isWaxingMoon) ||
            (p === 'Mercury' && !chartData.mercuryWithMalefics));

        if (enemyAspects.length > 0 && beneficAspects.length === 0) {
            avasthas.push(getResult('TRUSHITA', 'trushita_watery'));
        }
    }

    // 7. MUDITA (Delighted) - In friend's sign or conjunct friend
    if (signLord) {
        const friends = NATURAL_FRIENDS[planet] || [];
        if (friends.includes(signLord)) {
            avasthas.push(getResult('MUDITA', 'mudita_friend_sign', { signLord: I18n.t(`planets.${signLord}`) }));
        }

        // Conjunct with friend
        const friendConjunctions = conjunctions.filter(p => friends.includes(p));
        if (friendConjunctions.length > 0) {
            const planetNames = friendConjunctions.map(p => I18n.t(`planets.${p}`)).join(', ');
            avasthas.push(getResult('MUDITA', 'mudita_friend_conjunct', { planets: planetNames }));
        }
    }

    // 8. KSHOBHITA (Agitated) - Conjunct Sun (combust)
    if (planet !== 'Sun' && conjunctions.includes('Sun')) {
        // Check combustion orb
        const sunDist = chartData.sunDistance?.[planet];
        const combustOrbs = { Moon: 12, Mars: 17, Mercury: 14, Jupiter: 11, Venus: 10, Saturn: 15 };
        const orb = combustOrbs[planet] || 10;

        if (sunDist !== undefined && sunDist <= orb) {
            avasthas.push(getResult('KSHOBHITA', 'kshobhita_combust'));
        }
    }

    return avasthas;
}

// ============================================================================
// MAIN AVASTHA CALCULATOR
// ============================================================================

/**
 * Calculate all three Avastha systems for a planet
 * @param {string} planet - Planet name
 * @param {Object} position - Planet position { sign, degree }
 * @param {number} house - House number (1-12)
 * @param {Object} chartData - Full chart data
 * @returns {Object} All avastha calculations
 */
export function calculateAllAvasthas(planet, position, house, chartData) {
    const { sign, degree } = position;

    return {
        planet,
        baladi: calculateBaladiAvastha(sign, degree),
        jagratadi: calculateJagratAvastha(planet, sign),
        deeptadi: calculateDeeptadiAvastha(planet, chartData),
        sayanaadi: calculateSayanaadiAvastha(planet, chartData),
        lajjitadi: calculateLajjitadiAvasthas(planet, sign, house, chartData)
    };
}

/**
 * Calculate Avasthas for all planets in a chart
 * @param {Object} chartData - Chart data with planets, positions, and aspects
 * @returns {Object} Avasthas for all planets
 */
export function calculateChartAvasthas(chartData) {
    const { planets, lagnaRasi } = chartData;
    const results = {};

    // Build conjunctions and aspects data
    const conjunctions = {};
    const aspects = {};
    const sunDistances = {};

    // Calculate conjunctions (same sign)
    for (const planet of NAVAGRAHA) {
        conjunctions[planet] = [];
        aspects[planet] = [];

        const planetSign = planets[planet]?.sign;
        if (planetSign === undefined) continue;

        for (const other of NAVAGRAHA) {
            if (other === planet) continue;
            const otherSign = planets[other]?.sign;
            if (otherSign === planetSign) {
                conjunctions[planet].push(other);
            }
        }

        // Calculate distance from Sun for combustion
        if (planet !== 'Sun' && planets['Sun'] && planets[planet]) {
            const sunLon = (planets['Sun'].sign * 30) + (planets['Sun'].degree || 0);
            const planetLon = (planets[planet].sign * 30) + (planets[planet].degree || 0);
            let dist = Math.abs(sunLon - planetLon);
            if (dist > 180) dist = 360 - dist;
            sunDistances[planet] = dist;
        }
    }

    // Calculate aspects (simplified - 7th house aspect for all)
    // More complex aspects would need the full aspect system
    for (const planet of NAVAGRAHA) {
        const planetSign = planets[planet]?.sign;
        if (planetSign === undefined) continue;

        const aspectedSign = (planetSign + 6) % 12; // 7th house aspect
        for (const other of NAVAGRAHA) {
            if (other === planet) continue;
            if (planets[other]?.sign === aspectedSign) {
                aspects[planet].push(other);
            }
        }
    }

    // Prepare chart context
    const chartContext = {
        ...chartData,
        conjunctions,
        aspects,
        sunDistance: sunDistances,
        isWaxingMoon: isWaxingMoon(planets),
        mercuryWithMalefics: isMercuryWithMalefics(planets)
    };

    // Calculate avasthas for each planet
    for (const planet of SAPTA_GRAHA) {
        const position = planets[planet];
        if (!position) continue;

        const house = getHouseFromLagna(position.sign, lagnaRasi);
        results[planet] = calculateAllAvasthas(planet, position, house, chartContext);
    }

    return results;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Check if Moon is waxing (Shukla Paksha)
 */
function isWaxingMoon(planets) {
    if (!planets.Moon || !planets.Sun) return true;
    const moonLon = (planets.Moon.sign * 30) + (planets.Moon.degree || 0);
    const sunLon = (planets.Sun.sign * 30) + (planets.Sun.degree || 0);
    const phase = (moonLon - sunLon + 360) % 360;
    return phase < 180;
}

/**
 * Check if Mercury is with malefics
 */
function isMercuryWithMalefics(planets) {
    if (!planets.Mercury) return false;
    const mercSign = planets.Mercury.sign;
    const malefics = ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu'];

    for (const malefic of malefics) {
        if (planets[malefic]?.sign === mercSign) return true;
    }
    return false;
}

/**
 * Get house number from sign relative to Lagna
 */
function getHouseFromLagna(sign, lagnaRasi) {
    return ((sign - lagnaRasi + 12) % 12) + 1;
}

/**
 * Get overall strength multiplier from all avasthas
 * @param {Object} avasthas - Avastha results for a planet
 * @returns {number} Combined strength multiplier (0-1)
 */
export function getAvasthaCombinedStrength(avasthas) {
    let strength = 1.0;

    // Apply Baladi strength
    strength *= avasthas.baladi.strength;

    // Apply Jagratadi strength
    strength *= avasthas.jagratadi.strength;

    // Apply Lajjitadi modifiers
    for (const laj of avasthas.lajjitadi) {
        if (laj.nature === 'Highly Benefic') {
            strength *= 1.25;
        } else if (laj.nature === 'Benefic') {
            strength *= 1.1;
        } else if (laj.nature === 'Malefic') {
            strength *= 0.8;
        }
    }

    return Math.min(1.5, Math.max(0, strength));
}

// ============================================================================
// EXPORT SINGLETON CALCULATOR
// ============================================================================

export const AvasthaEngine = {
    calculateBaladiAvastha,
    calculateJagratAvastha,
    calculateLajjitadiAvasthas,
    calculateAllAvasthas,
    calculateChartAvasthas,
    getAvasthaCombinedStrength,
    BALADI_STATES,
    JAGRATADI_STATES,
    LAJJITADI_STATES
};

export default AvasthaEngine;
