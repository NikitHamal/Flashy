/**
 * ============================================================================
 * TRANSIT (GOCHARA) ENGINE - Advanced Vedic Transit Analysis
 * ============================================================================
 *
 * Provides comprehensive transit analysis according to Vedic Astrology principles:
 * - Real-time planetary positions overlaid on natal chart
 * - Transit-to-natal aspect calculations
 * - Vedha (obstruction) analysis
 * - Ashtakavarga-based transit strength
 * - Sade Sati (Saturn transit over Moon)
 * - Double Transit theory (Jupiter + Saturn)
 * - Planet Return charts (Solar, Lunar, Saturn)
 * - Transit event predictions
 *
 * References:
 * - Brihat Parashara Hora Shastra (BPHS)
 * - Phaladeepika
 * - Uttara Kalamrita
 *
 * @module transit
 * @version 1.0.0
 */

import Engine from './engine.js';
import Vedic from './vedic.js';
import {
    RASI_NAMES,
    NAVAGRAHA,
    SAPTA_GRAHA,
    SIGN_LORDS,
    PLANETARY_ASPECTS,
    getHouseNumber,
    getSignLord
} from './constants.js';

/**
 * Vedha (Obstruction) Points for each planet's transit
 * When a planet transits a house, if another planet is in the Vedha point,
 * the benefic results are obstructed
 * Format: { transitHouse: vedhaHouse }
 */
const VEDHA_POINTS = Object.freeze({
    Sun: { 3: 9, 6: 12, 10: 4, 11: 5 },
    Moon: { 1: 5, 3: 9, 6: 12, 7: 2, 10: 4, 11: 8 },
    Mars: { 3: 12, 6: 9, 11: 5 },
    Mercury: { 2: 5, 4: 3, 6: 9, 8: 1, 10: 8, 11: 12 },
    Jupiter: { 2: 12, 5: 4, 7: 3, 9: 10, 11: 8 },
    Venus: { 1: 8, 2: 7, 3: 1, 4: 10, 5: 9, 8: 5, 9: 11, 11: 6, 12: 3 },
    Saturn: { 3: 12, 6: 9, 11: 5 }
});

/**
 * Benefic houses for planetary transits (from Moon sign)
 * These houses give good results when transited
 */
const TRANSIT_BENEFIC_HOUSES = Object.freeze({
    Sun: [3, 6, 10, 11],
    Moon: [1, 3, 6, 7, 10, 11],
    Mars: [3, 6, 11],
    Mercury: [2, 4, 6, 8, 10, 11],
    Jupiter: [2, 5, 7, 9, 11],
    Venus: [1, 2, 3, 4, 5, 8, 9, 11, 12],
    Saturn: [3, 6, 11],
    Rahu: [3, 6, 10, 11],
    Ketu: [3, 6, 10, 11]
});

/**
 * Transit aspect strengths based on classical texts
 */
const TRANSIT_ASPECT_ORBS = Object.freeze({
    conjunction: { orb: 10, strength: 1.0 },
    opposition: { orb: 10, strength: 0.9 },
    trine: { orb: 8, strength: 0.7 },
    square: { orb: 8, strength: 0.6 },
    sextile: { orb: 6, strength: 0.5 }
});

/**
 * Sade Sati phases
 */
const SADE_SATI_PHASES = Object.freeze({
    RISING: 'rising',      // Saturn in 12th from Moon
    PEAK: 'peak',          // Saturn over Moon sign
    SETTING: 'setting',    // Saturn in 2nd from Moon
    NONE: 'none'
});

class TransitEngine {
    constructor() {
        this.vedic = Vedic;
    }

    /**
     * Calculate current transit chart
     * @param {Date} transitDate - Date for transit calculation
     * @param {Object} location - { lat, lng }
     * @returns {Object} Transit planetary positions
     */
    calculateTransitChart(transitDate, location) {
        return this.vedic.calculate(transitDate, location);
    }

    /**
     * Calculate comprehensive transit analysis
     * @param {Object} natalChart - Birth chart data from Vedic.calculate()
     * @param {Date} transitDate - Date for transit analysis
     * @param {Object} location - { lat, lng }
     * @returns {Object} Complete transit analysis
     */
    calculateTransits(natalChart, transitDate, location) {
        // Calculate transit positions
        const transitChart = this.calculateTransitChart(transitDate, location);

        // Get natal Moon sign for Gochara analysis
        const natalMoonSign = natalChart.planets.Moon.rasi.index;
        const natalMoonNakshatra = natalChart.planets.Moon.nakshatra.index;
        const natalLagnaSign = natalChart.lagna.rasi.index;

        // Calculate transit positions relative to natal Moon
        const transitPositions = this.calculateTransitPositions(
            transitChart.planets,
            natalMoonSign,
            natalMoonNakshatra,
            natalLagnaSign
        );

        // Calculate transit aspects to natal planets
        const transitAspects = this.calculateTransitAspects(
            transitChart.planets,
            natalChart.planets
        );

        // Check Vedha (obstructions)
        const vedhaAnalysis = this.analyzeVedha(transitPositions, transitChart.planets);

        // Calculate Moorthi Nirnaya
        const moorthiAnalysis = this.analyzeMoorthiNirnaya(
            transitChart.planets,
            natalMoonSign,
            transitDate,
            location
        );

        // Ashtakavarga-based transit strength
        const ashtakavargaStrength = this.calculateAshtakavargaTransitStrength(
            transitChart.planets,
            natalChart.ashtakavarga
        );

        // Sade Sati analysis
        const sadeSati = this.analyzeSadeSati(
            transitChart.planets.Saturn,
            natalMoonSign
        );

        // Double Transit (Jupiter + Saturn)
        const doubleTransit = this.analyzeDoubleTransit(
            transitChart.planets.Jupiter,
            transitChart.planets.Saturn,
            natalLagnaSign
        );

        // Calculate significant transit events
        const transitEvents = this.identifyTransitEvents(
            transitPositions,
            transitAspects,
            vedhaAnalysis,
            sadeSati
        );

        // Transit strength summary
        const strengthSummary = this.calculateTransitStrengthSummary(
            transitPositions,
            vedhaAnalysis,
            ashtakavargaStrength,
            moorthiAnalysis
        );

        return {
            date: transitDate,
            natalMoonSign,
            natalLagnaSign,
            transitChart,
            transitPositions,
            transitAspects,
            vedhaAnalysis,
            moorthiAnalysis,
            ashtakavargaStrength,
            sadeSati,
            doubleTransit,
            transitEvents,
            strengthSummary
        };
    }

    /**
     * Calculate transit positions relative to natal Moon and Lagna
     * @param {Object} transitPlanets - Current planetary positions
     * @param {number} natalMoonSign - Natal Moon sign index (0-11)
     * @param {number} natalMoonNakshatra - Natal Moon Nakshatra index (0-26)
     * @param {number} natalLagnaSign - Natal Lagna sign index (0-11)
     * @returns {Object} Transit positions with house numbers
     */
    calculateTransitPositions(transitPlanets, natalMoonSign, natalMoonNakshatra, natalLagnaSign) {
        const positions = {};

        for (const planet of NAVAGRAHA) {
            const transitSign = transitPlanets[planet].rasi.index;
            const transitNakshatra = transitPlanets[planet].nakshatra.index;

            // House from Moon (Gochara standard)
            const houseFromMoon = ((transitSign - natalMoonSign + 12) % 12) + 1;

            // House from Lagna
            const houseFromLagna = ((transitSign - natalLagnaSign + 12) % 12) + 1;

            // Tara Bala (Nakshatra Transit)
            const taraBala = this.calculateTaraBala(transitNakshatra, natalMoonNakshatra);

            // Kakshya Analysis
            const kakshya = this.calculateKakshya(planet, transitPlanets[planet].lon);

            // Check if benefic house
            const isBenefic = TRANSIT_BENEFIC_HOUSES[planet]?.includes(houseFromMoon) || false;

            // Get degree
            const degree = transitPlanets[planet].lon % 30;

            // Check retrograde
            const isRetrograde = transitPlanets[planet].speed < 0;

            positions[planet] = {
                transitSign,
                transitSignName: RASI_NAMES[transitSign],
                houseFromMoon,
                houseFromLagna,
                degree,
                isRetrograde,
                isBenefic,
                taraBala,
                kakshya,
                lon: transitPlanets[planet].lon,
                nakshatra: transitPlanets[planet].nakshatra
            };
        }

        return positions;
    }

    /**
     * Calculate Tara Bala (Nakshatra strength)
     * @param {number} transitNak - Transit Nakshatra index
     * @param {number} natalNak - Natal Nakshatra index
     * @returns {Object} Tara Bala result
     */
    calculateTaraBala(transitNak, natalNak) {
        const diff = (transitNak - natalNak + 27) % 9 + 1;
        const taraNames = [
            'Janma', 'Sampat', 'Vipat', 'Kshema', 'Pratyari',
            'Sadhaka', 'Vadha', 'Mitra', 'Atimitra'
        ];
        const descriptions = [
            'Danger to body', 'Wealth and prosperity', 'Dangers and losses',
            'Prosperity and well-being', 'Obstacles and opposition',
            'Success and achievements', 'Danger and destruction',
            'Happiness and help', 'Great happiness and gains'
        ];
        const isAuspicious = [false, true, false, true, false, true, false, true, true];

        return {
            index: diff,
            name: taraNames[diff - 1],
            description: descriptions[diff - 1],
            isAuspicious: isAuspicious[diff - 1]
        };
    }

    /**
     * Calculate Kakshya (Ashtakavarga sub-division)
     * Each sign (30°) is divided into 8 parts of 3.75° each
     * @param {string} planet - Planet name
     * @param {number} lon - Planet longitude
     * @returns {Object} Kakshya info
     */
    calculateKakshya(planet, lon) {
        const signPos = lon % 30;
        const kakshyaIndex = Math.floor(signPos / 3.75);
        const kakshyaLords = ['Saturn', 'Jupiter', 'Mars', 'Sun', 'Venus', 'Mercury', 'Moon', 'Lagna'];

        return {
            index: kakshyaIndex,
            lord: kakshyaLords[kakshyaIndex],
            range: [kakshyaIndex * 3.75, (kakshyaIndex + 1) * 3.75]
        };
    }

    /**
     * Analyze Moorthi Nirnaya (Murthi Decision)
     * Based on Moon's position at the time of planet's ingress into sign
     */
    analyzeMoorthiNirnaya(transitPlanets, natalMoonSign, transitDate, location) {
        const results = {};

        for (const planet of SAPTA_GRAHA) {
            // Find ingress date for the current sign
            const currentSign = transitPlanets[planet].rasi.index;
            const ingressDate = this.findIngressDate(planet, currentSign, transitDate, location);

            // Calculate Moon sign at ingress
            const ingressChart = this.calculateTransitChart(ingressDate, location);
            const ingressMoonSign = ingressChart.planets.Moon.rasi.index;

            // Calculate house from natal Moon
            const houseFromMoon = ((ingressMoonSign - natalMoonSign + 12) % 12) + 1;

            let type, quality, color;
            if ([1, 6, 11].includes(houseFromMoon)) {
                type = 'Swarna'; // Gold
                quality = 'excellent';
                color = '#FFD700';
            } else if ([2, 5, 9].includes(houseFromMoon)) {
                type = 'Rajata'; // Silver
                quality = 'good';
                color = '#C0C0C0';
            } else if ([3, 7, 10].includes(houseFromMoon)) {
                type = 'Tamra'; // Copper
                quality = 'average';
                color = '#B87333';
            } else {
                type = 'Loha'; // Iron
                quality = 'poor';
                color = '#808080';
            }

            results[planet] = {
                ingressDate,
                ingressMoonSign,
                houseFromMoon,
                type,
                quality,
                color,
                description: `${planet} entered sign as ${type} Moorthi`
            };
        }

        return results;
    }

    /**
     * Find the date/time when a planet entered its current sign
     */
    findIngressDate(planet, targetSign, currentDate, location) {
        let low = new Date(currentDate.getTime() - 40 * 24 * 60 * 60 * 1000); // 40 days back for fast planets
        if (['Jupiter', 'Saturn'].includes(planet)) {
            low = new Date(currentDate.getTime() - 400 * 24 * 60 * 60 * 1000); // 400 days back for slow planets
        }

        let high = new Date(currentDate.getTime());

        for (let i = 0; i < 24; i++) {
            const mid = new Date((low.getTime() + high.getTime()) / 2);
            const chart = this.calculateTransitChart(mid, location);
            const midSign = chart.planets[planet].rasi.index;

            if (midSign === targetSign) {
                high = mid;
            } else {
                low = mid;
            }
        }
        return high;
    }

    /**
     * Calculate transit aspects to natal planets
     * @param {Object} transitPlanets - Transit positions
     * @param {Object} natalPlanets - Natal positions
     * @returns {Array} Transit aspects
     */
    calculateTransitAspects(transitPlanets, natalPlanets) {
        const aspects = [];

        for (const transitPlanet of NAVAGRAHA) {
            const transitLon = transitPlanets[transitPlanet].lon;

            for (const natalPlanet of NAVAGRAHA) {
                const natalLon = natalPlanets[natalPlanet].lon;

                // Special Vedic aspects (Graha Drishti)
                const specialAspects = PLANETARY_ASPECTS[transitPlanet] || [];
                for (const aspectHouse of specialAspects) {
                    const aspectedSign = (transitPlanets[transitPlanet].rasi.index + aspectHouse - 1) % 12;
                    const natalSign = natalPlanets[natalPlanet].rasi.index;

                    if (aspectedSign === natalSign) {
                        aspects.push({
                            transitPlanet,
                            natalPlanet,
                            aspectType: aspectHouse === 1 ? 'conjunction' : `vedic_${aspectHouse}th`,
                            orb: 0,
                            exactness: 1,
                            strength: 1.0,
                            isVedic: true,
                            isApplying: true,
                            description: aspectHouse === 1 ?
                                `Transit ${transitPlanet} conjunct natal ${natalPlanet}` :
                                `Transit ${transitPlanet} aspects natal ${natalPlanet} (${aspectHouse}th house aspect)`
                        });
                    }
                }

                // Rashi Drishti (Sign Aspects)
                if (this.hasRashiDrishti(transitPlanets[transitPlanet].rasi.index, natalPlanets[natalPlanet].rasi.index)) {
                    aspects.push({
                        transitPlanet,
                        natalPlanet,
                        aspectType: 'rashi_drishti',
                        orb: 0,
                        exactness: 1,
                        strength: 0.7,
                        isVedic: true,
                        isApplying: true,
                        description: `Transit ${transitPlanet} has Rashi Drishti on natal ${natalPlanet}`
                    });
                }

                // Western aspects (Secondary in Vedic app)
                const diff = this.getAngularDiff(transitLon, natalLon);
                const westernAspect = this.getAspectType(diff);

                if (westernAspect) {
                    // Check if already covered by Vedic aspect (conjunction)
                    const isConjunction = westernAspect === 'conjunction';
                    if (!isConjunction) {
                        const aspectConfig = TRANSIT_ASPECT_ORBS[westernAspect];
                        const exactness = 1 - (Math.abs(diff - this.getAspectDegree(westernAspect)) / aspectConfig.orb);

                        if (exactness > 0) {
                            aspects.push({
                                transitPlanet,
                                natalPlanet,
                                aspectType: westernAspect,
                                orb: Math.abs(diff - this.getAspectDegree(westernAspect)),
                                exactness: Math.max(0, exactness),
                                strength: aspectConfig.strength * exactness * 0.5, // De-prioritized
                                isVedic: false,
                                isApplying: this.isAspectApplying(transitPlanets[transitPlanet], natalLon),
                                description: `Transit ${transitPlanet} ${westernAspect} natal ${natalPlanet} (Western)`
                            });
                        }
                    }
                }
            }
        }

        // Sort by strength and Vedic priority
        aspects.sort((a, b) => {
            if (a.isVedic && !b.isVedic) return -1;
            if (!a.isVedic && b.isVedic) return 1;
            return b.strength - a.strength;
        });

        return aspects;
    }

    getAngularDiff(lon1, lon2) {
        let diff = Math.abs(lon1 - lon2);
        if (diff > 180) diff = 360 - diff;
        return diff;
    }

    /**
     * Check for Rashi Drishti (Sign Aspect)
     * Movable signs aspect Fixed signs (except adjacent)
     * Fixed signs aspect Movable signs (except adjacent)
     * Dual signs aspect other Dual signs
     */
    hasRashiDrishti(sign1, sign2) {
        if (sign1 === sign2) return false;

        const type1 = sign1 % 3; // 0: Movable, 1: Fixed, 2: Dual
        const type2 = sign2 % 3;

        if (type1 === 0) { // Movable
            // Aspects Fixed (1) except adjacent (sign1 + 1)
            return type2 === 1 && sign2 !== (sign1 + 1) % 12;
        } else if (type1 === 1) { // Fixed
            // Aspects Movable (0) except adjacent (sign1 - 1)
            return type2 === 0 && sign2 !== (sign1 + 11) % 12;
        } else if (type1 === 2) { // Dual
            // Aspects other Dual signs
            return type2 === 2;
        }
        return false;
    }

    /**
     * Get aspect type from angular separation
     */
    getAspectType(diff) {
        if (diff <= 10) return 'conjunction';
        if (Math.abs(diff - 180) <= 10) return 'opposition';
        if (Math.abs(diff - 120) <= 8) return 'trine';
        if (Math.abs(diff - 90) <= 8) return 'square';
        if (Math.abs(diff - 60) <= 6) return 'sextile';
        return null;
    }

    /**
     * Get exact degree for aspect type
     */
    getAspectDegree(aspectType) {
        const degrees = {
            conjunction: 0,
            sextile: 60,
            square: 90,
            trine: 120,
            opposition: 180
        };
        return degrees[aspectType] || 0;
    }

    /**
     * Check if aspect is applying (getting closer)
     */
    isAspectApplying(transitPlanet, natalLon) {
        // If transit planet is moving toward natal position
        const speed = transitPlanet.speed || 0;
        const transitLon = transitPlanet.lon;

        let diff = natalLon - transitLon;
        if (diff < 0) diff += 360;

        // Applying if moving toward and within 180 degrees
        return (speed > 0 && diff < 180) || (speed < 0 && diff > 180);
    }

    /**
     * Analyze Vedha (obstruction) in transits
     * @param {Object} transitPositions - Transit positions from calculateTransitPositions
     * @param {Object} transitPlanets - Raw transit planet data
     * @returns {Object} Vedha analysis
     */
    analyzeVedha(transitPositions, transitPlanets) {
        const vedhaResults = {};

        for (const planet of SAPTA_GRAHA) {
            const position = transitPositions[planet];
            const houseFromMoon = position.houseFromMoon;
            const vedhaPoints = VEDHA_POINTS[planet] || {};

            vedhaResults[planet] = {
                houseFromMoon,
                isBenefic: position.isBenefic,
                hasVedha: false,
                vedhaDetails: null
            };

            // Check if this is a benefic transit and if Vedha applies
            if (position.isBenefic) {
                const vedhaHouse = vedhaPoints[houseFromMoon];

                if (vedhaHouse) {
                    // Check if any planet is in the Vedha house
                    for (const checkPlanet of SAPTA_GRAHA) {
                        if (checkPlanet !== planet) {
                            // EXCEPTIONS: 
                            // 1. Sun & Saturn do not obstruct each other
                            // 2. Moon & Mercury do not obstruct each other
                            if ((planet === 'Sun' && checkPlanet === 'Saturn') ||
                                (planet === 'Saturn' && checkPlanet === 'Sun') ||
                                (planet === 'Moon' && checkPlanet === 'Mercury') ||
                                (planet === 'Mercury' && checkPlanet === 'Moon')) {
                                continue;
                            }

                            const checkPosition = transitPositions[checkPlanet];
                            if (checkPosition && checkPosition.houseFromMoon === vedhaHouse) {
                                vedhaResults[planet].hasVedha = true;
                                vedhaResults[planet].vedhaDetails = {
                                    vedhaHouse,
                                    obstructingPlanet: checkPlanet,
                                    description: `${planet}'s benefic transit in ${houseFromMoon}th house is obstructed by ${checkPlanet} in ${vedhaHouse}th house`
                                };
                                break;
                            }
                        }
                    }
                }
            }

            // Final effective status
            vedhaResults[planet].effectiveResult =
                position.isBenefic && !vedhaResults[planet].hasVedha ? 'benefic' :
                    !position.isBenefic ? 'malefic' : 'obstructed';
        }

        return vedhaResults;
    }

    /**
     * Calculate transit strength using Ashtakavarga
     * @param {Object} transitPlanets - Transit positions
     * @param {Object} ashtakavarga - Natal Ashtakavarga data
     * @returns {Object} Transit strength per planet
     */
    calculateAshtakavargaTransitStrength(transitPlanets, ashtakavarga) {
        const strength = {};

        if (!ashtakavarga || !ashtakavarga.bav) {
            return strength;
        }

        for (const planet of SAPTA_GRAHA) {
            const transitSign = transitPlanets[planet].rasi.index;
            const bavPoints = ashtakavarga.bav[planet]?.[transitSign] || 0;
            const savPoints = ashtakavarga.sav?.[transitSign] || 0;

            // Categorize strength
            let bavCategory, savCategory;

            if (bavPoints >= 5) bavCategory = 'excellent';
            else if (bavPoints >= 4) bavCategory = 'good';
            else if (bavPoints >= 3) bavCategory = 'average';
            else bavCategory = 'weak';

            if (savPoints >= 30) savCategory = 'excellent';
            else if (savPoints >= 25) savCategory = 'good';
            else if (savPoints >= 20) savCategory = 'average';
            else savCategory = 'weak';

            strength[planet] = {
                transitSign,
                bavPoints,
                savPoints,
                bavCategory,
                savCategory,
                isStrong: bavPoints >= 4 && savPoints >= 25,
                description: `${planet} transiting ${RASI_NAMES[transitSign]} has BAV ${bavPoints}/8 and SAV ${savPoints}/56`
            };
        }

        return strength;
    }

    /**
     * Analyze Sade Sati (7.5 year Saturn transit)
     * @param {Object} transitSaturn - Transit Saturn position
     * @param {number} natalMoonSign - Natal Moon sign index
     * @returns {Object} Sade Sati analysis
     */
    analyzeSadeSati(transitSaturn, natalMoonSign) {
        const saturnSign = transitSaturn.rasi.index;
        const houseFromMoon = ((saturnSign - natalMoonSign + 12) % 12) + 1;

        let phase = SADE_SATI_PHASES.NONE;
        let intensity = 0;
        let descriptionKey = '';

        if (houseFromMoon === 12) {
            phase = SADE_SATI_PHASES.RISING;
            intensity = 0.6;
            descriptionKey = 'sade_sati_rising_desc';
        } else if (houseFromMoon === 1) {
            phase = SADE_SATI_PHASES.PEAK;
            intensity = 1.0;
            descriptionKey = 'sade_sati_peak_desc';
        } else if (houseFromMoon === 2) {
            phase = SADE_SATI_PHASES.SETTING;
            intensity = 0.7;
            descriptionKey = 'sade_sati_setting_desc';
        } else {
            descriptionKey = 'sade_sati_inactive_desc';
        }

        // Additional analysis
        const isRetrograde = transitSaturn.speed < 0;
        const saturnDegree = transitSaturn.lon % 30;

        // Estimate phase progression
        let phaseProgress = 0;
        if (phase !== SADE_SATI_PHASES.NONE) {
            phaseProgress = (saturnDegree / 30) * 100;
        }

        return {
            isActive: phase !== SADE_SATI_PHASES.NONE,
            phase,
            intensity,
            saturnSign,
            saturnSignName: RASI_NAMES[saturnSign],
            houseFromMoon,
            isRetrograde,
            phaseProgress,
            descriptionKey,
            recommendationsKeys: this.getSadeSatiRecommendations(phase, intensity)
        };
    }

    /**
     * Get Sade Sati recommendations
     */
    getSadeSatiRecommendations(phase, intensity) {
        if (phase === SADE_SATI_PHASES.NONE) {
            return [];
        }

        const recommendations = [
            'ss_rec_patience',
            'ss_rec_spiritual',
            'ss_rec_no_risk',
            'ss_rec_service'
        ];

        if (intensity >= 0.8) {
            recommendations.push('ss_rec_shanti');
            recommendations.push('ss_rec_charity');
        }

        return recommendations;
    }

    /**
     * Analyze Double Transit (Jupiter + Saturn)
     * This is crucial for predicting major life events
     * @param {Object} transitJupiter - Jupiter position
     * @param {Object} transitSaturn - Saturn position
     * @param {number} natalLagnaSign - Natal Lagna sign
     * @returns {Object} Double transit analysis
     */
    analyzeDoubleTransit(transitJupiter, transitSaturn, natalLagnaSign) {
        const jupiterSign = transitJupiter.rasi.index;
        const saturnSign = transitSaturn.rasi.index;

        // Calculate houses aspected by Jupiter (5th, 7th, 9th aspects)
        const jupiterAspectedHouses = new Set();
        jupiterAspectedHouses.add(((jupiterSign - natalLagnaSign + 12) % 12) + 1); // Conjunction
        jupiterAspectedHouses.add(((jupiterSign + 4 - natalLagnaSign + 12) % 12) + 1); // 5th aspect
        jupiterAspectedHouses.add(((jupiterSign + 6 - natalLagnaSign + 12) % 12) + 1); // 7th aspect
        jupiterAspectedHouses.add(((jupiterSign + 8 - natalLagnaSign + 12) % 12) + 1); // 9th aspect

        // Calculate houses aspected by Saturn (3rd, 7th, 10th aspects)
        const saturnAspectedHouses = new Set();
        saturnAspectedHouses.add(((saturnSign - natalLagnaSign + 12) % 12) + 1); // Conjunction
        saturnAspectedHouses.add(((saturnSign + 2 - natalLagnaSign + 12) % 12) + 1); // 3rd aspect
        saturnAspectedHouses.add(((saturnSign + 6 - natalLagnaSign + 12) % 12) + 1); // 7th aspect
        saturnAspectedHouses.add(((saturnSign + 9 - natalLagnaSign + 12) % 12) + 1); // 10th aspect

        // Find houses with double transit (both Jupiter and Saturn influence)
        const doubleTransitHouses = [];
        for (let house = 1; house <= 12; house++) {
            if (jupiterAspectedHouses.has(house) && saturnAspectedHouses.has(house)) {
                doubleTransitHouses.push({
                    house,
                    signification: this.getHouseSignification(house),
                    strength: 'high'
                });
            }
        }

        return {
            jupiterSign,
            jupiterSignName: RASI_NAMES[jupiterSign],
            saturnSign,
            saturnSignName: RASI_NAMES[saturnSign],
            jupiterAspectedHouses: Array.from(jupiterAspectedHouses),
            saturnAspectedHouses: Array.from(saturnAspectedHouses),
            doubleTransitHouses,
            hasDoubleTransit: doubleTransitHouses.length > 0,
            descriptionKey: doubleTransitHouses.length > 0 ? 'double_transit_active_desc' : 'no_double_transit_desc'
        };
    }

    /**
     * Get house signification
     */
    getHouseSignification(house) {
        return `house_${house}_signification`;
    }

    /**
     * Identify significant transit events
     */
    identifyTransitEvents(transitPositions, transitAspects, vedhaAnalysis, sadeSati) {
        const events = [];

        // Check for planets changing signs (ingress)
        for (const planet of NAVAGRAHA) {
            const position = transitPositions[planet];

            // Near sign change (within 1 degree of sign boundary)
            if (position.degree < 1 || position.degree > 29) {
                events.push({
                    type: 'ingress',
                    planet,
                    sign: position.transitSignName,
                    degree: position.degree,
                    priority: 'high',
                    descriptionKey: position.degree < 1 ? 'event_ingress_just_entered' : 'event_ingress_about_to_leave',
                    params: { planet, sign: position.transitSignName }
                });
            }

            // Retrograde stations
            if (position.isRetrograde && planet !== 'Sun' && planet !== 'Moon') {
                events.push({
                    type: 'retrograde',
                    planet,
                    sign: position.transitSignName,
                    priority: 'medium',
                    descriptionKey: 'event_retrograde_desc',
                    params: { planet, sign: position.transitSignName }
                });
            }
        }

        // Tight aspects (orb < 2 degrees)
        const tightAspects = transitAspects.filter(a => a.orb < 2 && a.isVedic);
        for (const aspect of tightAspects) {
            events.push({
                type: 'aspect',
                transitPlanet: aspect.transitPlanet,
                natalPlanet: aspect.natalPlanet,
                aspectType: aspect.aspectType,
                orb: aspect.orb,
                isApplying: aspect.isApplying,
                priority: aspect.isApplying ? 'high' : 'medium',
                descriptionKey: 'event_aspect_desc',
                params: { transitPlanet: aspect.transitPlanet, natalPlanet: aspect.natalPlanet, aspectType: aspect.aspectType }
            });
        }

        // Sade Sati
        if (sadeSati.isActive) {
            events.push({
                type: 'sadeSati',
                phase: sadeSati.phase,
                intensity: sadeSati.intensity,
                priority: sadeSati.phase === SADE_SATI_PHASES.PEAK ? 'high' : 'medium',
                descriptionKey: sadeSati.descriptionKey
            });
        }

        // Benefic transits without Vedha
        for (const planet of SAPTA_GRAHA) {
            const vedha = vedhaAnalysis[planet];
            if (vedha.effectiveResult === 'benefic') {
                events.push({
                    type: 'beneficTransit',
                    planet,
                    house: vedha.houseFromMoon,
                    priority: 'low',
                    descriptionKey: 'event_benefic_transit_desc',
                    params: { planet, house: vedha.houseFromMoon }
                });
            }
        }

        // Sort by priority
        const priorityOrder = { high: 0, medium: 1, low: 2 };
        events.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);

        return events;
    }

    /**
     * Calculate overall transit strength summary
     */
    calculateTransitStrengthSummary(transitPositions, vedhaAnalysis, ashtakavargaStrength, moorthiAnalysis) {
        let beneficCount = 0;
        let maleficCount = 0;
        let obstructedCount = 0;
        let strongTransits = [];
        let weakTransits = [];

        for (const planet of SAPTA_GRAHA) {
            const vedha = vedhaAnalysis[planet];
            const avStrength = ashtakavargaStrength[planet];
            const moorthi = moorthiAnalysis[planet];

            // Weight calculation based on Ashtakavarga
            // BAV < 3 is a heavy penalty, BAV > 5 is a major boost
            let avWeight = 1.0;
            if (avStrength?.bavPoints !== undefined) {
                if (avStrength.bavPoints >= 6) avWeight = 1.5;
                else if (avStrength.bavPoints >= 4) avWeight = 1.2;
                else if (avStrength.bavPoints <= 2) avWeight = 0.5;
            }

            if (vedha.effectiveResult === 'benefic') {
                beneficCount += avWeight;
                if (avStrength?.isStrong || moorthi.quality === 'excellent') {
                    strongTransits.push(planet);
                }
            } else if (vedha.effectiveResult === 'malefic') {
                // Moorthi can improve a malefic transit
                if (moorthi.quality === 'excellent' || moorthi.quality === 'good') {
                    obstructedCount += 0.5; // Treat as half-malefic
                } else {
                    maleficCount += (2.0 - avWeight); // Malefic is worse if BAV is low
                    if (avStrength && !avStrength.isStrong) {
                        weakTransits.push(planet);
                    }
                }
            } else if (vedha.effectiveResult === 'obstructed') {
                obstructedCount++;
            }
        }

        // Overall score (0-100)
        const totalPlanets = SAPTA_GRAHA.length;
        const normalizedBenefic = (beneficCount / totalPlanets) * 100;
        const normalizedMalefic = (maleficCount / totalPlanets) * 50; // Malefic impact is 50%
        const overallScore = Math.round(Math.max(0, Math.min(100, normalizedBenefic - normalizedMalefic)));

        let overallAssessment;
        if (overallScore >= 60) overallAssessment = 'favorable';
        else if (overallScore >= 40) overallAssessment = 'mixed';
        else if (overallScore >= 20) overallAssessment = 'challenging';
        else overallAssessment = 'difficult';

        return {
            beneficCount,
            maleficCount,
            obstructedCount,
            strongTransits,
            weakTransits,
            overallScore,
            overallAssessment,
            description: `${beneficCount} benefic, ${maleficCount} malefic, ${obstructedCount} obstructed transits. Overall: ${overallAssessment}`
        };
    }

    /**
     * Calculate transit timeline for a date range
     * @param {Object} natalChart - Natal chart data
     * @param {Date} startDate - Start date
     * @param {Date} endDate - End date
     * @param {Object} location - Location
     * @param {string} interval - 'daily', 'weekly', 'monthly'
     * @returns {Array} Timeline of transit snapshots
     */
    calculateTransitTimeline(natalChart, startDate, endDate, location, interval = 'daily') {
        const timeline = [];
        const current = new Date(startDate);

        const intervalDays = {
            daily: 1,
            weekly: 7,
            monthly: 30
        };

        const step = intervalDays[interval] || 1;

        while (current <= endDate) {
            const transit = this.calculateTransits(natalChart, current, location);
            timeline.push({
                date: new Date(current),
                summary: transit.strengthSummary,
                sadeSati: transit.sadeSati.isActive ? transit.sadeSati.phase : null,
                doubleTransitHouses: transit.doubleTransit.doubleTransitHouses.map(h => h.house),
                significantEvents: transit.transitEvents.filter(e => e.priority === 'high')
            });

            current.setDate(current.getDate() + step);
        }

        return timeline;
    }

    /**
     * Find next planetary return (Solar, Lunar, Saturn)
     * @param {Object} natalChart - Natal chart
     * @param {string} planet - 'Sun', 'Moon', or 'Saturn'
     * @param {Date} fromDate - Search from this date
     * @param {Object} location - Location
     * @returns {Object} Return chart data
     */
    findPlanetaryReturn(natalChart, planet, fromDate, location) {
        const natalLon = natalChart.planets[planet].lon;
        let searchDate = new Date(fromDate);

        // Approximate periods for each planet
        const searchStep = {
            Sun: 1,      // Daily search
            Moon: 0.5,   // Every 12 hours
            Saturn: 7    // Weekly (29.5 years cycle)
        };

        const step = searchStep[planet] || 1;
        const maxIterations = planet === 'Saturn' ? 2000 : 400;
        let iterations = 0;

        while (iterations < maxIterations) {
            const transitChart = this.calculateTransitChart(searchDate, location);
            const transitLon = transitChart.planets[planet].lon;

            // Check if within 1 degree
            let diff = Math.abs(transitLon - natalLon);
            if (diff > 180) diff = 360 - diff;

            if (diff < 1) {
                // Found approximate return, now refine
                return this.refineReturn(natalChart, planet, searchDate, location, natalLon);
            }

            searchDate.setDate(searchDate.getDate() + step);
            iterations++;
        }

        return null;
    }

    /**
     * Refine planetary return to exact moment
     */
    refineReturn(natalChart, planet, approxDate, location, natalLon) {
        // Binary search for exact return
        let low = new Date(approxDate.getTime() - 24 * 60 * 60 * 1000);
        let high = new Date(approxDate.getTime() + 24 * 60 * 60 * 1000);

        for (let i = 0; i < 20; i++) {
            const mid = new Date((low.getTime() + high.getTime()) / 2);
            const transitChart = this.calculateTransitChart(mid, location);
            const transitLon = transitChart.planets[planet].lon;

            let diff = transitLon - natalLon;
            if (diff > 180) diff -= 360;
            if (diff < -180) diff += 360;

            if (Math.abs(diff) < 0.01) {
                // Found exact return
                const returnChart = this.calculateTransitChart(mid, location);
                return {
                    planet,
                    returnDate: mid,
                    returnChart,
                    natalLon,
                    exactLon: transitLon,
                    description: `${planet} Return on ${mid.toLocaleDateString()}`
                };
            }

            if (diff > 0) {
                high = mid;
            } else {
                low = mid;
            }
        }

        // Return approximate if exact not found
        const returnChart = this.calculateTransitChart(approxDate, location);
        return {
            planet,
            returnDate: approxDate,
            returnChart,
            natalLon,
            exactLon: returnChart.planets[planet].lon,
            description: `${planet} Return (approximate) on ${approxDate.toLocaleDateString()}`
        };
    }

    /**
     * Get current Dasha period transit effects
     * @param {Object} natalChart - Natal chart with dashas
     * @param {Object} transitData - Transit analysis
     * @returns {Object} Dasha-transit interaction
     */
    analyzeDashaTransitInteraction(natalChart, transitData) {
        // Get Mahadasha and Antardasha active at the transit date
        const targetDate = new Date(transitData.date);
        const dashas = natalChart.dashas;

        let currentMD = null;
        let currentAD = null;

        for (const md of dashas) {
            if (md.start <= targetDate && md.end >= targetDate) {
                currentMD = md;
                for (const ad of md.antardashas || []) {
                    if (ad.start <= targetDate && ad.end >= targetDate) {
                        currentAD = ad;
                        break;
                    }
                }
                break;
            }
        }

        if (!currentMD) {
            return { available: false };
        }

        // Find transit aspects to dasha lords
        const mdPlanet = currentMD.planet;
        const adPlanet = currentAD?.planet;

        const mdTransitAspects = transitData.transitAspects.filter(a =>
            a.natalPlanet === mdPlanet
        );

        const adTransitAspects = currentAD ? transitData.transitAspects.filter(a =>
            a.natalPlanet === adPlanet
        ) : [];

        // Check if dasha lords are transiting favorable houses
        const mdTransitPosition = transitData.transitPositions[mdPlanet];
        const adTransitPosition = currentAD ? transitData.transitPositions[adPlanet] : null;

        return {
            available: true,
            mahadasha: {
                planet: mdPlanet,
                transitPosition: mdTransitPosition,
                aspectsReceived: mdTransitAspects,
                isFavorable: mdTransitPosition?.isBenefic || false
            },
            antardasha: currentAD ? {
                planet: adPlanet,
                transitPosition: adTransitPosition,
                aspectsReceived: adTransitAspects,
                isFavorable: adTransitPosition?.isBenefic || false
            } : null,
            interaction: this.describeDashaTransitInteraction(
                mdPlanet, mdTransitPosition, mdTransitAspects,
                adPlanet, adTransitPosition, adTransitAspects
            )
        };
    }

    /**
     * Describe Dasha-Transit interaction
     */
    describeDashaTransitInteraction(mdPlanet, mdPos, mdAspects, adPlanet, adPos, adAspects) {
        const parts = [];

        if (mdPos?.isBenefic) {
            parts.push({ key: 'dasha_md_favorable', params: { planet: mdPlanet, house: mdPos.houseFromMoon } });
        } else if (mdPos) {
            parts.push({ key: 'dasha_md_challenging', params: { planet: mdPlanet, house: mdPos.houseFromMoon } });
        }

        if (mdAspects.length > 0) {
            const strongAspect = mdAspects[0];
            parts.push({
                key: 'dasha_md_aspect',
                params: { transitPlanet: strongAspect.transitPlanet, aspectType: strongAspect.aspectType, natalPlanet: mdPlanet }
            });
        }

        if (adPlanet && adPos) {
            if (adPos.isBenefic) {
                parts.push({ key: 'dasha_ad_favorable', params: { planet: adPlanet, house: adPos.houseFromMoon } });
            } else {
                parts.push({ key: 'dasha_ad_challenging', params: { planet: adPlanet, house: adPos.houseFromMoon } });
            }
        }

        return parts.length > 0 ? parts : [{ key: 'dasha_no_interaction' }];
    }
}

export default new TransitEngine();
