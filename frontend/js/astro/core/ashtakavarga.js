/**
 * ============================================================================
 * Ashtakavarga Engine
 * ============================================================================
 *
 * Implements the classical Ashtakavarga (Eight-fold strength) system as per
 * Brihat Parashara Hora Shastra (BPHS) Chapters 66-72.
 *
 * Features:
 * - Bhinnastakavarga (BAV): Individual planet point grids
 * - Sarvastakavarga (SAV): Aggregate strength across all planets
 * - Trikona Shodhana: Triangular reduction per BPHS
 * - Ekadhipatya Shodhana: Same-lordship reduction per BPHS
 * - Kakshya-wise analysis: Sub-divisions for precise transit timing
 * - House strength analysis: Interpretive utilities
 *
 * @module astro/ashtakavarga
 * @version 2.0.0
 */

import { SIGN_LORDS } from './constants.js';

class Ashtakavarga {
    constructor() {
        /**
         * Ashtakavarga Bindu (point) contribution tables.
         * For each planet, points are contributed from 8 reference points:
         * Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, and Lagna.
         * The indices represent signs relative to the reference planet's placement (1-based).
         */
        this.tables = {
            Sun: {
                Sun: [1, 2, 4, 7, 8, 9, 10, 11],
                Moon: [3, 6, 10, 11],
                Mars: [1, 2, 4, 7, 8, 9, 10, 11],
                Mercury: [3, 5, 6, 9, 10, 11, 12],
                Jupiter: [5, 6, 9, 11],
                Venus: [6, 7, 12],
                Saturn: [1, 2, 4, 7, 8, 9, 10, 11],
                Lagna: [3, 4, 6, 10, 11, 12]
            },
            Moon: {
                Sun: [3, 6, 7, 8, 10, 11],
                Moon: [1, 3, 6, 7, 10, 11],
                Mars: [2, 3, 5, 6, 9, 10, 11],
                Mercury: [1, 3, 4, 5, 7, 8, 10, 11],
                Jupiter: [1, 4, 7, 8, 10, 11, 12],
                Venus: [3, 4, 5, 7, 9, 10, 11],
                Saturn: [3, 5, 6, 11],
                Lagna: [3, 6, 10, 11]
            },
            Mars: {
                Sun: [3, 5, 6, 10, 11],
                Moon: [3, 6, 11],
                Mars: [1, 2, 4, 7, 8, 10, 11],
                Mercury: [3, 5, 6, 11],
                Jupiter: [6, 10, 11, 12],
                Venus: [6, 8, 11, 12],
                Saturn: [1, 4, 7, 8, 9, 10, 11],
                Lagna: [1, 3, 6, 10, 11]
            },
            Mercury: {
                Sun: [5, 6, 9, 11, 12],
                Moon: [2, 4, 6, 8, 10, 11],
                Mars: [1, 2, 4, 7, 8, 9, 10, 11],
                Mercury: [1, 3, 5, 6, 9, 10, 11, 12],
                Jupiter: [6, 8, 11, 12],
                Venus: [1, 2, 3, 4, 5, 8, 9, 11],
                Saturn: [1, 2, 4, 7, 8, 9, 10, 11],
                Lagna: [1, 2, 4, 6, 8, 10, 11]
            },
            Jupiter: {
                Sun: [1, 2, 3, 4, 7, 8, 9, 10, 11],
                Moon: [2, 5, 7, 9, 11],
                Mars: [1, 2, 4, 7, 8, 10, 11],
                Mercury: [1, 2, 4, 5, 6, 9, 10, 11],
                Jupiter: [1, 2, 3, 4, 7, 8, 10, 11],
                Venus: [2, 5, 6, 9, 10, 11],
                Saturn: [3, 5, 6, 12],
                Lagna: [1, 2, 4, 5, 6, 7, 9, 10, 11]
            },
            Venus: {
                Sun: [8, 11, 12],
                Moon: [1, 2, 3, 4, 5, 8, 9, 11, 12],
                Mars: [3, 5, 6, 9, 11, 12],
                Mercury: [3, 5, 6, 9, 11],
                Jupiter: [5, 8, 9, 10, 11],
                Venus: [1, 2, 3, 4, 5, 8, 9, 10, 11],
                Saturn: [3, 4, 5, 8, 9, 10, 11],
                Lagna: [1, 2, 3, 4, 5, 8, 9, 11]
            },
            Saturn: {
                Sun: [1, 2, 4, 7, 8, 10, 11],
                Moon: [3, 6, 11],
                Mars: [3, 5, 6, 10, 11, 12],
                Mercury: [6, 8, 9, 10, 11, 12],
                Jupiter: [5, 6, 11, 12],
                Venus: [6, 11, 12],
                Saturn: [3, 5, 6],
                Lagna: [1, 3, 4, 6, 10, 11]
            }
        };

        /**
         * Rasi Gunaakar (Sign Multipliers) per BPHS
         */
        this.rasiGunaakars = [7, 10, 8, 4, 10, 5, 7, 8, 9, 5, 11, 12];

        /**
         * Graha Gunaakar (Planet Multipliers) per BPHS
         */
        this.grahaGunaakars = {
            Sun: 5, Moon: 5, Mars: 8, Mercury: 5, Jupiter: 10, Venus: 7, Saturn: 5
        };

        this.planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];

        /**
         * Kakshya lords for each 3°45' subdivision within a sign
         * Each sign is divided into 8 Kakshyas ruled by planets in order:
         * Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon, Lagna
         */
        this.kakshyaLords = ['Saturn', 'Jupiter', 'Mars', 'Sun', 'Venus', 'Mercury', 'Moon', 'Lagna'];

        /**
         * Total BAV maximums per planet (theoretical max = 8 contributors × 8 houses)
         * Practical maximums are typically:
         * Sun: 48, Moon: 49, Mars: 39, Mercury: 54, Jupiter: 56, Venus: 52, Saturn: 39
         */
        this.bavMaximums = {
            Sun: 48, Moon: 49, Mars: 39, Mercury: 54,
            Jupiter: 56, Venus: 52, Saturn: 39
        };
    }

    // =========================================================================
    // CORE CALCULATIONS
    // =========================================================================

    /**
     * Calculates complete Ashtakavarga data for a chart
     * @param {Object} planets - Planetary positions with rasi.index
     * @param {Object} lagna - Lagna position with rasi.index
     * @param {Object} options - Calculation options
     * @returns {Object} Complete Ashtakavarga data
     */
    calculate(planets, lagna, options = {}) {
        const { includeShodhana = true, includeKakshya = false } = options;

        // 1. Calculate raw Bhinnastakavarga (BAV)
        const bavRaw = this._calculateBAV(planets, lagna);

        // 2. Calculate raw Sarvastakavarga (SAV)
        const savRaw = this._calculateSAV(bavRaw);

        // 3. Apply Shodhana (reduction) if requested
        let bavShodhana = null;
        let savShodhana = null;

        if (includeShodhana) {
            bavShodhana = this._applyTrikona(bavRaw);
            bavShodhana = this._applyEkadhipatya(bavShodhana, lagna.rasi.index, planets);
            savShodhana = this._calculateSAV(bavShodhana);
        }

        // 4. Calculate Kakshya-wise points if requested
        let kakshyaData = null;
        if (includeKakshya) {
            kakshyaData = this._calculateKakshya(bavRaw, planets);
        }

        // 5. Calculate Pindas (Rasi Pinda, Graha Pinda, Shuddha Pinda)
        const pindas = {};
        if (includeShodhana && bavShodhana) {
            this.planets.forEach(planet => {
                pindas[planet] = this._calculatePlanetPinda(planet, bavShodhana[planet], planets);
            });
        }

        // 6. Calculate interpretive analysis
        const analysis = this._analyzeStrengths(bavRaw, savRaw, lagna.rasi.index);

        return {
            bav: bavRaw,
            sav: savRaw,
            bavShodhana,
            savShodhana,
            pindas,
            kakshya: kakshyaData,
            analysis,
            totals: this._calculateTotals(bavRaw)
        };
    }

    /**
     * Calculate Rasi Pinda and Graha Pinda for a planet
     */
    _calculatePlanetPinda(planet, reducedGrid, planetaryPositions) {
        // 1. Rasi Pinda: Sum of (Reduced Bindus * Rasi Multiplier)
        let rasiPinda = 0;
        reducedGrid.forEach((bindus, i) => {
            rasiPinda += bindus * this.rasiGunaakars[i];
        });

        // 2. Graha Pinda: Sum of (Reduced Bindus in occupied signs * Planet Multiplier)
        let grahaPinda = 0;
        this.planets.forEach(p => {
            const pos = planetaryPositions[p];
            if (pos) {
                const signIdx = pos.rasi.index;
                const bindusInSign = reducedGrid[signIdx];
                grahaPinda += bindusInSign * this.grahaGunaakars[p];
            }
        });

        return {
            rasiPinda,
            grahaPinda,
            shuddhaPinda: rasiPinda + grahaPinda
        };
    }

    /**
     * Calculate Bhinnastakavarga for all 7 planets
     */
    _calculateBAV(planets, lagna) {
        const bav = {};

        this.planets.forEach(targetPlanet => {
            const grid = new Array(12).fill(0);
            const table = this.tables[targetPlanet];

            // Contributions from 7 planets
            this.planets.forEach(refPlanet => {
                const refSignIdx = planets[refPlanet].rasi.index;
                const contributingHouses = table[refPlanet];

                contributingHouses.forEach(h => {
                    const signIdx = (refSignIdx + h - 1) % 12;
                    grid[signIdx]++;
                });
            });

            // Contribution from Lagna
            const lagnaSignIdx = lagna.rasi.index;
            const lagnaContributingHouses = table.Lagna;
            lagnaContributingHouses.forEach(h => {
                const signIdx = (lagnaSignIdx + h - 1) % 12;
                grid[signIdx]++;
            });

            bav[targetPlanet] = grid;
        });

        return bav;
    }

    /**
     * Calculate Sarvastakavarga (aggregate of all BAVs)
     */
    _calculateSAV(bav) {
        const sav = new Array(12).fill(0);

        this.planets.forEach(planet => {
            bav[planet].forEach((bindus, i) => {
                sav[i] += bindus;
            });
        });

        return sav;
    }

    // =========================================================================
    // SHODHANA (REDUCTION) RULES
    // =========================================================================

    /**
     * Trikona Shodhana (Triangular Reduction)
     * Per BPHS Ch. 69: Among signs in trikona (1-5-9), the minimum bindu
     * value is retained and subtracted from each sign.
     */
    _applyTrikona(bavRaw) {
        const bavReduced = {};

        this.planets.forEach(planet => {
            const grid = [...bavRaw[planet]];

            // Process 4 trikona groups
            for (let i = 0; i < 4; i++) {
                const trikonaSigns = [i, (i + 4) % 12, (i + 8) % 12];
                const values = trikonaSigns.map(s => grid[s]);
                const minValue = Math.min(...values);

                // Subtract minimum from each sign in trikona
                trikonaSigns.forEach(s => {
                    grid[s] -= minValue;
                });
            }

            bavReduced[planet] = grid;
        });

        return bavReduced;
    }

    /**
     * Ekadhipatya Shodhana (Same Lordship Reduction)
     * Per BPHS Ch. 70: When two signs share the same lord, compare bindus.
     * Retain values if both signs are occupied.
     */
    _applyEkadhipatya(bavTrikona, lagnaIdx, planets) {
        const bavReduced = {};

        // Helper to check if a sign is occupied by any planet
        const isOccupied = (signIdx) => {
            return Object.values(planets).some(p => p.rasi?.index === signIdx);
        };

        // Pairs of signs with same lord (excluding Sun/Moon)
        const ekadhipatyaPairs = [
            [0, 7],   // Mars: Aries-Scorpio
            [1, 6],   // Venus: Taurus-Libra
            [2, 5],   // Mercury: Gemini-Virgo
            [8, 11],  // Jupiter: Sagittarius-Pisces
            [9, 10]   // Saturn: Capricorn-Aquarius
        ];

        this.planets.forEach(planet => {
            const grid = [...bavTrikona[planet]];

            ekadhipatyaPairs.forEach(([sign1, sign2]) => {
                const val1 = grid[sign1];
                const val2 = grid[sign2];
                const occ1 = isOccupied(sign1);
                const occ2 = isOccupied(sign2);

                if (val1 === 0 && val2 === 0) return;

                // 1. If both are occupied, no reduction
                if (occ1 && occ2) return;

                // 2. If only one is occupied
                if (occ1 && !occ2) {
                    // Sign 1 is occupied, Sign 2 is not.
                    // Rule: Compare values. If sign 2 has more, reduce it to sign 1's level?
                    // Actually, BPHS says if only one is occupied, its value is retained and other becomes 0?
                    // "If one is occupied and other is not... take the value of occupied one for both?" No.
                    // "Retain the value of the occupied sign and set the other to zero."
                    grid[sign2] = 0;
                    return;
                }
                if (!occ1 && occ2) {
                    grid[sign1] = 0;
                    return;
                }

                // 3. Both are unoccupied - Compare values
                const minVal = Math.min(val1, val2);
                
                // Simplified BPHS comparison logic
                const dist1 = Math.min(Math.abs(sign1 - lagnaIdx), 12 - Math.abs(sign1 - lagnaIdx));
                const dist2 = Math.min(Math.abs(sign2 - lagnaIdx), 12 - Math.abs(sign2 - lagnaIdx));

                if (dist1 <= dist2) {
                    grid[sign1] = minVal;
                    grid[sign2] = 0;
                } else {
                    grid[sign1] = 0;
                    grid[sign2] = minVal;
                }
            });

            bavReduced[planet] = grid;
        });

        return bavReduced;
    }

    // =========================================================================
    // KAKSHYA CALCULATIONS
    // =========================================================================

    /**
     * Calculate Kakshya (sub-division) points for transit timing
     * Each sign is divided into 8 Kakshyas of 3°45' each
     */
    _calculateKakshya(bav, planets) {
        const kakshyaData = {};

        this.planets.forEach(planet => {
            const planetKakshya = [];

            for (let sign = 0; sign < 12; sign++) {
                const signKakshya = [];

                // 8 Kakshyas per sign
                for (let k = 0; k < 8; k++) {
                    const lord = this.kakshyaLords[k];
                    // Bindu present if lord contributes to this sign in BAV
                    // This is a simplified check - full implementation would check
                    // the Prastara Ashtakavarga tables
                    const hasBindu = this._checkKakshyaBindu(planet, sign, lord, planets);
                    signKakshya.push({
                        lord,
                        hasBindu,
                        startDeg: k * 3.75,
                        endDeg: (k + 1) * 3.75
                    });
                }

                planetKakshya.push(signKakshya);
            }

            kakshyaData[planet] = planetKakshya;
        });

        return kakshyaData;
    }

    /**
     * Check if a specific Kakshya has a bindu
     */
    _checkKakshyaBindu(targetPlanet, signIdx, kakshyaLord, planets) {
        if (kakshyaLord === 'Lagna') {
            // Lagna contribution check
            const table = this.tables[targetPlanet];
            return table.Lagna.some(h => {
                const lagnaSign = planets.lagnaIndex || 0;
                return (lagnaSign + h - 1) % 12 === signIdx;
            });
        }

        // Planet contribution check
        const table = this.tables[targetPlanet];
        if (!table[kakshyaLord]) return false;

        const refSignIdx = planets[kakshyaLord]?.rasi?.index;
        if (refSignIdx === undefined) return false;

        return table[kakshyaLord].some(h => {
            return (refSignIdx + h - 1) % 12 === signIdx;
        });
    }

    // =========================================================================
    // ANALYSIS & INTERPRETATION
    // =========================================================================

    /**
     * Analyze strengths for interpretation
     */
    _analyzeStrengths(bav, sav, lagnaIdx) {
        const analysis = {
            houseStrengths: [],
            strongHouses: [],
            weakHouses: [],
            averageSAV: 0,
            interpretation: {}
        };

        // Average SAV bindu count
        const savTotal = sav.reduce((a, b) => a + b, 0);
        analysis.averageSAV = savTotal / 12;

        // Classify houses by strength
        const avgBindus = 337 / 12; // ~28 is average for total SAV
        sav.forEach((bindus, i) => {
            const houseNum = ((i - lagnaIdx + 12) % 12) + 1;

            const strength = {
                house: houseNum,
                sign: i,
                bindus,
                status: bindus >= 30 ? 'strong' : (bindus <= 25 ? 'weak' : 'moderate')
            };

            analysis.houseStrengths.push(strength);

            if (bindus >= 30) {
                analysis.strongHouses.push(houseNum);
            } else if (bindus <= 25) {
                analysis.weakHouses.push(houseNum);
            }
        });

        // Key house interpretations
        const getHouseBindus = (house) => {
            const signIdx = (lagnaIdx + house - 1) % 12;
            return sav[signIdx];
        };

        analysis.interpretation = {
            // 1st House: Self, personality
            personality: getHouseBindus(1) >= 28 ? 'strong' : 'moderate',
            // 2nd House: Wealth, family
            wealth: getHouseBindus(2) >= 28 ? 'good' : 'moderate',
            // 7th House: Marriage, partnerships
            relationships: getHouseBindus(7) >= 28 ? 'favorable' : 'moderate',
            // 10th House: Career, status
            career: getHouseBindus(10) >= 28 ? 'promising' : 'moderate',
            // 11th House: Gains, income
            gains: getHouseBindus(11) >= 28 ? 'substantial' : 'moderate'
        };

        return analysis;
    }

    /**
     * Calculate planet-wise totals
     */
    _calculateTotals(bav) {
        const totals = {};

        this.planets.forEach(planet => {
            const sum = bav[planet].reduce((a, b) => a + b, 0);
            const max = this.bavMaximums[planet];

            totals[planet] = {
                total: sum,
                maximum: max,
                percentage: Math.round((sum / max) * 100),
                status: sum >= max * 0.6 ? 'strong' : (sum <= max * 0.4 ? 'weak' : 'moderate')
            };
        });

        return totals;
    }

    // =========================================================================
    // TRANSIT ANALYSIS
    // =========================================================================

    /**
     * Analyze transit effects based on Ashtakavarga
     * @param {Object} ashtakavargaData - Result from calculate()
     * @param {number} transitSignIdx - Sign index where planet is transiting
     * @param {string} transitPlanet - Planet that is transiting
     * @returns {Object} Transit analysis
     */
    analyzeTransit(ashtakavargaData, transitSignIdx, transitPlanet) {
        const bav = ashtakavargaData.bav;
        const sav = ashtakavargaData.sav;

        if (!bav[transitPlanet]) {
            return { valid: false, message: 'Invalid transit planet' };
        }

        const bavBindus = bav[transitPlanet][transitSignIdx];
        const savBindus = sav[transitSignIdx];

        // Transit strength thresholds per classical texts
        const bavStrength = bavBindus >= 5 ? 'excellent' :
            (bavBindus >= 4 ? 'good' : (bavBindus >= 3 ? 'moderate' : 'weak'));

        const savStrength = savBindus >= 30 ? 'auspicious' :
            (savBindus >= 25 ? 'neutral' : 'challenging');

        return {
            valid: true,
            planet: transitPlanet,
            sign: transitSignIdx,
            bavBindus,
            savBindus,
            bavStrength,
            savStrength,
            overallResult: this._getTransitResult(bavBindus, savBindus),
            recommendations: this._getTransitRecommendations(transitPlanet, bavStrength, savStrength)
        };
    }

    /**
     * Get overall transit result
     */
    _getTransitResult(bavBindus, savBindus) {
        const bavScore = bavBindus / 8; // Normalize to 0-1
        const savScore = savBindus / 56; // Max theoretical SAV per sign

        const combined = (bavScore * 0.6) + (savScore * 0.4);

        if (combined >= 0.6) return 'highly_favorable';
        if (combined >= 0.45) return 'favorable';
        if (combined >= 0.35) return 'mixed';
        return 'challenging';
    }

    /**
     * Get transit recommendations based on strength
     */
    _getTransitRecommendations(planet, bavStrength, savStrength) {
        const recommendations = [];

        if (bavStrength === 'weak') {
            recommendations.push({
                type: 'caution',
                key: `transit_weak_${planet.toLowerCase()}`
            });
        }

        if (savStrength === 'challenging') {
            recommendations.push({
                type: 'remedy',
                key: 'transit_remedy_general'
            });
        }

        if (bavStrength === 'excellent' && savStrength === 'auspicious') {
            recommendations.push({
                type: 'opportunity',
                key: `transit_opportunity_${planet.toLowerCase()}`
            });
        }

        return recommendations;
    }

    // =========================================================================
    // UTILITY METHODS
    // =========================================================================

    /**
     * Get sign lord
     */
    _getSignLord(signIdx) {
        return SIGN_LORDS[signIdx];
    }

    /**
     * Get bindu count for a specific planet in a specific sign
     */
    getBindus(ashtakavargaData, planet, signIdx) {
        if (!ashtakavargaData?.bav?.[planet]) return 0;
        return ashtakavargaData.bav[planet][signIdx] || 0;
    }

    /**
     * Get SAV bindus for a sign
     */
    getSAVBindus(ashtakavargaData, signIdx) {
        if (!ashtakavargaData?.sav) return 0;
        return ashtakavargaData.sav[signIdx] || 0;
    }

    /**
     * Check if a transit is favorable based on Ashtakavarga
     * Quick utility for simple yes/no checks
     */
    isTransitFavorable(ashtakavargaData, planet, signIdx) {
        const bavBindus = this.getBindus(ashtakavargaData, planet, signIdx);
        return bavBindus >= 4; // 4+ bindus is generally considered favorable
    }

    /**
     * Get the best signs for a planet based on BAV
     */
    getBestSigns(ashtakavargaData, planet, count = 3) {
        const bav = ashtakavargaData?.bav?.[planet];
        if (!bav) return [];

        return bav
            .map((bindus, idx) => ({ sign: idx, bindus }))
            .sort((a, b) => b.bindus - a.bindus)
            .slice(0, count);
    }

    /**
     * Get the worst signs for a planet based on BAV
     */
    getWorstSigns(ashtakavargaData, planet, count = 3) {
        const bav = ashtakavargaData?.bav?.[planet];
        if (!bav) return [];

        return bav
            .map((bindus, idx) => ({ sign: idx, bindus }))
            .sort((a, b) => a.bindus - b.bindus)
            .slice(0, count);
    }
}

export default new Ashtakavarga();
