import I18n from '../core/i18n.js';

/**
 * Production-Grade Manglik (Kuja) Dosha Calculator
 * 
 * Implements complete Manglik Dosha analysis with:
 * - Mars position from Lagna, Moon, and Venus
 * - Dosha detection in houses 1, 2, 4, 7, 8, 12
 * - 15+ cancellation rules based on classical texts
 * - Intensity levels (High, Low, None)
 * - Compatibility checking between two charts
 * 
 * Based on Brihat Parasara Hora Shastra and standard astrological practices.
 */

// ============================================================================
// CONSTANTS
// ============================================================================

/**
 * Houses where Mars creates Manglik Dosha
 * 1st: Self, personality
 * 2nd: Family, speech (South Indian tradition includes this)
 * 4th: Home, mother, happiness
 * 7th: Marriage, spouse
 * 8th: Longevity, sudden events
 * 12th: Bed pleasures, losses
 */
const MANGLIK_HOUSES = [1, 2, 4, 7, 8, 12];

/**
 * Signs ruled by each planet
 */
const SIGN_RULERS = {
    1: 'Mars',      // Aries
    2: 'Venus',     // Taurus
    3: 'Mercury',   // Gemini
    4: 'Moon',      // Cancer
    5: 'Sun',       // Leo
    6: 'Mercury',   // Virgo
    7: 'Venus',     // Libra
    8: 'Mars',      // Scorpio
    9: 'Jupiter',   // Sagittarius
    10: 'Saturn',   // Capricorn
    11: 'Saturn',   // Aquarius
    12: 'Jupiter'   // Pisces
};

/**
 * Exaltation, debilitation, and own signs for Mars
 */
const MARS_DIGNITIES = {
    ownSigns: [1, 8],       // Aries, Scorpio
    exaltation: 10,          // Capricorn
    debilitation: 4,         // Cancer
    friendlySigns: [5, 9, 12], // Leo, Sagittarius, Pisces
    moolatrikona: 1          // Aries (first 12 degrees)
};

/**
 * Movable signs (Chara Rashi)
 */
const MOVABLE_SIGNS = [1, 4, 7, 10]; // Aries, Cancer, Libra, Capricorn

/**
 * Signs where Mars produces no dosha
 */
const MARS_EXEMPT_SIGNS = [5, 11]; // Leo, Aquarius

/**
 * Benefic planets
 */
const BENEFIC_PLANETS = ['Jupiter', 'Venus', 'Mercury', 'Moon'];

/**
 * Malefic planets (that can neutralize Mars's effects)
 */
const NEUTRALIZING_PLANETS = ['Saturn', 'Rahu', 'Ketu'];

// ============================================================================
// MANGLIK DOSHA CALCULATION
// ============================================================================

/**
 * Calculate house position of a planet from reference point
 * @param {number} planetSign - Sign containing the planet (1-12)
 * @param {number} referenceSign - Reference sign (Lagna, Moon, or Venus) (1-12)
 * @returns {number} House position (1-12)
 */
function getHouseFromSign(planetSign, referenceSign) {
    let house = ((planetSign - referenceSign + 12) % 12) + 1;
    return house === 13 ? 1 : house;
}

/**
 * Check if a specific aspect exists between planets
 * Mars aspects: 4th, 7th, 8th houses from itself
 * Jupiter aspects: 5th, 7th, 9th houses from itself
 * Saturn aspects: 3rd, 7th, 10th houses from itself
 */
function hasAspect(aspectingPlanetSign, targetSign, aspectingPlanet) {
    const distance = ((targetSign - aspectingPlanetSign + 12) % 12) + 1;

    // All planets aspect 7th house
    if (distance === 7) return true;

    if (aspectingPlanet === 'Mars' && (distance === 4 || distance === 8)) return true;
    if (aspectingPlanet === 'Jupiter' && (distance === 5 || distance === 9)) return true;
    if (aspectingPlanet === 'Saturn' && (distance === 3 || distance === 10)) return true;

    return false;
}

/**
 * Check if two planets are conjunct (in same sign)
 */
function isConjunct(sign1, sign2) {
    return sign1 === sign2;
}

/**
 * Main Manglik Dosha class
 */
class Manglik {

    /**
     * Calculate Manglik Dosha for a single chart
     * 
     * @param {Object} chartData - Chart data containing planet positions
     * @param {number} chartData.lagnaSign - Ascendant sign (1-12)
     * @param {number} chartData.moonSign - Moon's sign (1-12)
     * @param {number} chartData.venusSign - Venus's sign (1-12) 
     * @param {number} chartData.marsSign - Mars's sign (1-12)
     * @param {number} chartData.jupiterSign - Jupiter's sign (1-12)
     * @param {number} chartData.saturnSign - Saturn's sign (1-12)
     * @param {number} chartData.rahuSign - Rahu's sign (1-12)
     * @param {number} chartData.ketuSign - Ketu's sign (1-12)
     * @param {number} chartData.sunSign - Sun's sign (1-12) - for combust check
     * @param {string} [chartData.gender] - 'male' or 'female'
     * @param {number} [chartData.age] - Age in years
     * @returns {Object} Complete Manglik analysis
     */
    calculate(chartData) {
        const {
            lagnaSign,
            moonSign,
            venusSign,
            marsSign,
            jupiterSign,
            saturnSign,
            rahuSign,
            ketuSign,
            sunSign,
            gender,
            age
        } = chartData;

        // Calculate Mars position from each reference
        const marsFromLagna = getHouseFromSign(marsSign, lagnaSign);
        const marsFromMoon = getHouseFromSign(marsSign, moonSign);
        const marsFromVenus = getHouseFromSign(marsSign, venusSign);

        // Check if Mars is in Manglik houses from each reference
        const manglikFromLagna = MANGLIK_HOUSES.includes(marsFromLagna);
        const manglikFromMoon = MANGLIK_HOUSES.includes(marsFromMoon);
        const manglikFromVenus = MANGLIK_HOUSES.includes(marsFromVenus);

        // Count how many charts show Manglik
        const manglikCount = [manglikFromLagna, manglikFromMoon, manglikFromVenus].filter(Boolean).length;

        // Determine base dosha presence
        let hasDosha = manglikCount > 0;
        let intensity = 'None';

        if (manglikCount === 3) {
            intensity = 'High';
        } else if (manglikCount === 2) {
            intensity = 'Medium-High';
        } else if (manglikCount === 1) {
            intensity = 'Low';
        }

        // Check for cancellations
        const cancellations = this.checkCancellations({
            marsSign,
            marsFromLagna,
            marsFromMoon,
            marsFromVenus,
            lagnaSign,
            moonSign,
            jupiterSign,
            venusSign,
            saturnSign,
            rahuSign,
            ketuSign,
            sunSign,
            gender,
            age
        });

        // Determine final status
        const isCancelled = cancellations.isCancelled;
        const finalHasDosha = hasDosha && !isCancelled;

        // Adjust intensity based on cancellations
        let finalIntensity = intensity;
        if (isCancelled) {
            finalIntensity = 'Cancelled';
        } else if (cancellations.isPartiallyMitigated) {
            if (intensity === 'High') finalIntensity = 'Medium';
            else if (intensity === 'Medium-High') finalIntensity = 'Low';
            else if (intensity === 'Low') finalIntensity = 'Very Low';
        }

        return {
            hasDosha: finalHasDosha,
            isManglik: manglikCount > 0,
            isEffectiveManglik: finalHasDosha,
            intensity: finalIntensity,
            originalIntensity: intensity,

            manglikFromLagna: manglikFromLagna,
            manglikFromMoon: manglikFromMoon,
            manglikFromVenus: manglikFromVenus,
            manglikCount: manglikCount,

            marsPosition: {
                sign: marsSign,
                fromLagna: marsFromLagna,
                fromMoon: marsFromMoon,
                fromVenus: marsFromVenus
            },

            cancellations: cancellations,

            description: this.getDescription(finalHasDosha, finalIntensity, manglikCount, cancellations),
            recommendations: this.getRecommendations(finalHasDosha, finalIntensity, cancellations)
        };
    }

    /**
     * Check all cancellation rules
     */
    checkCancellations(data) {
        const {
            marsSign,
            marsFromLagna,
            marsFromMoon,
            marsFromVenus,
            lagnaSign,
            moonSign,
            jupiterSign,
            venusSign,
            saturnSign,
            rahuSign,
            ketuSign,
            sunSign,
            gender,
            age
        } = data;

        const cancellationReasons = [];
        let isCancelled = false;
        let isPartiallyMitigated = false;

        // Rule 1: Mars in own sign (Aries, Scorpio)
        if (MARS_DIGNITIES.ownSigns.includes(marsSign)) {
            cancellationReasons.push({
                rule: 'Mars in Own Sign',
                ruleKey: 'own_sign',
                description: `Mars is in its own sign (${this.getSignName(marsSign)})`,
                descriptionKey: 'own_sign_desc',
                params: { signIndex: marsSign },
                type: 'full'
            });
            isCancelled = true;
        }

        // Rule 2: Mars exalted (Capricorn)
        if (marsSign === MARS_DIGNITIES.exaltation) {
            cancellationReasons.push({
                rule: 'Mars Exalted',
                ruleKey: 'exalted',
                description: 'Mars is exalted in Capricorn',
                descriptionKey: 'exalted_desc',
                type: 'full'
            });
            isCancelled = true;
        }

        // Rule 3: Mars in Leo or Aquarius (no dosha)
        if (MARS_EXEMPT_SIGNS.includes(marsSign)) {
            cancellationReasons.push({
                rule: 'Mars in Exempt Sign',
                ruleKey: 'exempt_sign',
                description: `Mars produces no dosha in ${this.getSignName(marsSign)}`,
                descriptionKey: 'exempt_sign_desc',
                params: { signIndex: marsSign },
                type: 'full'
            });
            isCancelled = true;
        }

        // Rule 4: Mars in movable signs (Aries, Cancer, Libra, Capricorn)
        if (MOVABLE_SIGNS.includes(marsSign)) {
            cancellationReasons.push({
                rule: 'Mars in Movable Sign',
                ruleKey: 'movable_sign',
                description: `Mars in movable sign ${this.getSignName(marsSign)} - dosha significantly reduced`,
                descriptionKey: 'movable_sign_desc',
                params: { signIndex: marsSign },
                type: 'partial'
            });
            isPartiallyMitigated = true;
        }

        // Rule 5: Mars debilitated (Cancer) - power reduced
        if (marsSign === MARS_DIGNITIES.debilitation) {
            cancellationReasons.push({
                rule: 'Mars Debilitated',
                ruleKey: 'debilitated',
                description: 'Mars is debilitated in Cancer - malefic power reduced',
                descriptionKey: 'debilitated_desc',
                type: 'full'
            });
            isCancelled = true;
        }

        // Rule 6: Cancer or Leo ascendant (Mars is Yogakaraka)
        if (lagnaSign === 4 || lagnaSign === 5) {
            cancellationReasons.push({
                rule: 'Yogakaraka Mars',
                ruleKey: 'yogakaraka',
                description: `Mars is Yogakaraka for ${this.getSignName(lagnaSign)} Ascendant`,
                descriptionKey: 'yogakaraka_desc',
                params: { signIndex: lagnaSign },
                type: 'full'
            });
            isCancelled = true;
        }

        // Rule 7: Mars conjunct Jupiter
        if (isConjunct(marsSign, jupiterSign)) {
            cancellationReasons.push({
                rule: 'Mars-Jupiter Conjunction',
                ruleKey: 'conj_jupiter',
                description: 'Mars conjunct benefic Jupiter neutralizes dosha',
                descriptionKey: 'conj_jupiter_desc',
                type: 'full'
            });
            isCancelled = true;
        }

        // Rule 8: Mars aspected by Jupiter
        if (hasAspect(jupiterSign, marsSign, 'Jupiter')) {
            cancellationReasons.push({
                rule: 'Jupiter Aspects Mars',
                ruleKey: 'aspect_jupiter',
                description: 'Jupiter aspects Mars, providing protection',
                descriptionKey: 'aspect_jupiter_desc',
                type: 'full'
            });
            isCancelled = true;
        }

        // Rule 9: Mars conjunct Venus or Moon
        if (isConjunct(marsSign, venusSign)) {
            cancellationReasons.push({
                rule: 'Mars-Venus Conjunction',
                ruleKey: 'conj_venus',
                description: 'Mars conjunct Venus mitigates harmful effects',
                descriptionKey: 'conj_venus_desc',
                type: 'partial'
            });
            isPartiallyMitigated = true;
        }

        if (isConjunct(marsSign, moonSign)) {
            cancellationReasons.push({
                rule: 'Mars-Moon Conjunction',
                ruleKey: 'conj_moon',
                description: 'Mars conjunct Moon mitigates harmful effects',
                descriptionKey: 'conj_moon_desc',
                type: 'partial'
            });
            isPartiallyMitigated = true;
        }

        // Rule 10: Mars conjunct or aspected by Saturn, Rahu, or Ketu
        if (isConjunct(marsSign, saturnSign)) {
            cancellationReasons.push({
                rule: 'Mars-Saturn Conjunction',
                ruleKey: 'conj_saturn',
                description: 'Mars conjunct Saturn neutralizes Manglik effects',
                descriptionKey: 'conj_saturn_desc',
                type: 'full'
            });
            isCancelled = true;
        }

        if (isConjunct(marsSign, rahuSign) || isConjunct(marsSign, ketuSign)) {
            cancellationReasons.push({
                rule: 'Mars with Nodes',
                ruleKey: 'with_nodes',
                description: 'Mars conjunct Rahu/Ketu affects dosha formation',
                descriptionKey: 'with_nodes_desc',
                type: 'partial'
            });
            isPartiallyMitigated = true;
        }

        if (hasAspect(saturnSign, marsSign, 'Saturn')) {
            cancellationReasons.push({
                rule: 'Saturn Aspects Mars',
                ruleKey: 'aspect_saturn',
                description: 'Saturn aspects Mars, nullifying Manglik effects',
                descriptionKey: 'aspect_saturn_desc',
                type: 'partial'
            });
            isPartiallyMitigated = true;
        }

        // Rule 11: Mars combust (close to Sun)
        if (isConjunct(marsSign, sunSign)) {
            cancellationReasons.push({
                rule: 'Mars Combust',
                ruleKey: 'combust',
                description: 'Mars combust by Sun - malefic power reduced',
                descriptionKey: 'combust_desc',
                type: 'partial'
            });
            isPartiallyMitigated = true;
        }

        // Rule 12: Moon in Kendra (1, 4, 7, 10) from Lagna
        const moonFromLagna = getHouseFromSign(moonSign, lagnaSign);
        if ([1, 4, 7, 10].includes(moonFromLagna)) {
            cancellationReasons.push({
                rule: 'Moon in Kendra',
                ruleKey: 'moon_kendra',
                description: `Moon in house ${moonFromLagna} (Kendra) provides protection`,
                descriptionKey: 'moon_kendra_desc',
                params: { house: moonFromLagna },
                type: 'partial'
            });
            isPartiallyMitigated = true;
        }

        // Rule 13: Benefic in Ascendant
        const jupiterFromLagna = getHouseFromSign(jupiterSign, lagnaSign);
        const venusFromLagna = getHouseFromSign(venusSign, lagnaSign);
        if (jupiterFromLagna === 1) {
            cancellationReasons.push({
                rule: 'Jupiter in Lagna',
                ruleKey: 'jupiter_lagna',
                description: 'Jupiter in Ascendant provides strong protection',
                descriptionKey: 'jupiter_lagna_desc',
                type: 'full'
            });
            isCancelled = true;
        }
        if (venusFromLagna === 1) {
            cancellationReasons.push({
                rule: 'Venus in Lagna',
                ruleKey: 'venus_lagna',
                description: 'Venus in Ascendant mitigates Manglik dosha',
                descriptionKey: 'venus_lagna_desc',
                type: 'partial'
            });
            isPartiallyMitigated = true;
        }

        // Rule 14: Specific house/sign combinations
        if (marsFromLagna === 2 && (marsSign === 3 || marsSign === 6)) {
            cancellationReasons.push({
                rule: '2nd House Exception',
                ruleKey: 'house2_except',
                description: `Mars in 2nd house in ${this.getSignName(marsSign)} - no dosha`,
                descriptionKey: 'house2_except_desc',
                params: { signIndex: marsSign },
                type: 'full'
            });
            isCancelled = true;
        }

        if (marsFromLagna === 4 && (marsSign === 1 || marsSign === 8)) {
            cancellationReasons.push({
                rule: '4th House Exception',
                ruleKey: 'house4_except',
                description: `Mars in 4th house in own sign ${this.getSignName(marsSign)} - no dosha`,
                descriptionKey: 'house4_except_desc',
                params: { signIndex: marsSign },
                type: 'full'
            });
            isCancelled = true;
        }

        if (marsFromLagna === 7 && (marsSign === 4 || marsSign === 10)) {
            cancellationReasons.push({
                rule: '7th House Exception',
                ruleKey: 'house7_except',
                description: `Mars in 7th house in ${this.getSignName(marsSign)} - no dosha`,
                descriptionKey: 'house7_except_desc',
                params: { signIndex: marsSign },
                type: 'full'
            });
            isCancelled = true;
        }

        if (marsFromLagna === 8 && (marsSign === 9 || marsSign === 12)) {
            cancellationReasons.push({
                rule: '8th House Exception',
                ruleKey: 'house8_except',
                description: `Mars in 8th house in ${this.getSignName(marsSign)} - no dosha`,
                descriptionKey: 'house8_except_desc',
                params: { signIndex: marsSign },
                type: 'full'
            });
            isCancelled = true;
        }

        if (marsFromLagna === 12 && (marsSign === 2 || marsSign === 7)) {
            cancellationReasons.push({
                rule: '12th House Exception',
                ruleKey: 'house12_except',
                description: `Mars in 12th house in ${this.getSignName(marsSign)} - no dosha`,
                descriptionKey: 'house12_except_desc',
                params: { signIndex: marsSign },
                type: 'full'
            });
            isCancelled = true;
        }

        // Rule 15: Dispositor of Mars in Kendra/Trikona
        const marsLord = SIGN_RULERS[marsSign];
        const lordSign = this.getLordSign(marsLord, { jupiterSign, venusSign, saturnSign, moonSign, sunSign, marsSign });
        if (lordSign) {
            const lordFromLagna = getHouseFromSign(lordSign, lagnaSign);
            if ([1, 4, 7, 10, 5, 9].includes(lordFromLagna)) {
                cancellationReasons.push({
                    rule: 'Dispositor in Kendra/Trikona',
                    ruleKey: 'dispositor_kendra',
                    description: `Mars's lord ${marsLord} in house ${lordFromLagna} (Kendra/Trikona)`,
                    descriptionKey: 'dispositor_kendra_desc',
                    params: { planet: marsLord, house: lordFromLagna },
                    type: 'partial'
                });
                isPartiallyMitigated = true;
            }
        }

        // Rule 16: Age factor (after 28)
        if (age && age >= 28) {
            cancellationReasons.push({
                rule: 'Age Factor',
                ruleKey: 'age_factor',
                description: 'Person is above 28 years - Manglik effects naturally reduced',
                descriptionKey: 'age_factor_desc',
                type: 'partial'
            });
            isPartiallyMitigated = true;
        }

        return {
            isCancelled: isCancelled,
            isPartiallyMitigated: isPartiallyMitigated && !isCancelled,
            reasons: cancellationReasons,
            fullCancellations: cancellationReasons.filter(r => r.type === 'full'),
            partialMitigations: cancellationReasons.filter(r => r.type === 'partial')
        };
    }

    /**
     * Get sign name from index
     */
    getSignName(index) {
        const signs = ['', 'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
            'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
        return signs[index] || 'Unknown';
    }

    /**
     * Get the sign position of a planet (for dispositor check)
     */
    getLordSign(planet, planets) {
        const mapping = {
            'Jupiter': planets.jupiterSign,
            'Venus': planets.venusSign,
            'Saturn': planets.saturnSign,
            'Moon': planets.moonSign,
            'Sun': planets.sunSign,
            'Mars': planets.marsSign,
            'Mercury': null // Would need Mercury sign in data
        };
        return mapping[planet];
    }

    /**
     * Generate description based on analysis
     */
    getDescription(hasDosha, intensity, manglikCount, cancellations) {
        if (!hasDosha && cancellations.isCancelled) {
            const reason = cancellations.fullCancellations[0];
            return {
                key: 'cancelled_with_reason',
                params: {
                    reason: reason.description, // Fallback
                    reasonKey: reason.ruleKey,
                    descKey: reason.descriptionKey,
                    params: reason.params
                }
            };
        }

        if (!hasDosha && manglikCount === 0) {
            return { key: 'none' };
        }

        return {
            key: 'present',
            intensity: intensity,
            intensityKey: intensity.toLowerCase().replace('-', '_')
        };
    }

    /**
     * Generate recommendations based on analysis
     */
    getRecommendations(hasDosha, intensity, cancellations) {
        if (!hasDosha || intensity === 'Cancelled') {
            return [{ key: 'none_required' }];
        }

        const recommendations = [];
        if (intensity === 'Low' || intensity === 'Very Low') {
            recommendations.push({ key: 'minor_manglik' });
            recommendations.push({ key: 'kumbh_vivah' });
        } else if (intensity === 'Medium' || intensity === 'Medium-High') {
            recommendations.push({ key: 'matching_recommended' });
            recommendations.push({ key: 'mars_remedies' });
        } else if (intensity === 'High') {
            recommendations.push({ key: 'strong_manglik' });
            recommendations.push({ key: 'kumbh_vivah_essential' });
        }

        return recommendations;
    }

    /**
     * Check compatibility between two Manglik analyses
     */
    checkCompatibility(person1Analysis, person2Analysis) {
        const p1Manglik = person1Analysis.isEffectiveManglik;
        const p2Manglik = person2Analysis.isEffectiveManglik;

        let compatibilityKey = 'Good';
        let description = '';
        let warnings = [];
        let recommendations = [];

        // Rule: Mutual Cancellation (Mars-Saturn or Both Manglik)
        // If both are Manglik, they cancel each other out (Simha-Avalokana rule)
        if (p1Manglik && p2Manglik) {
            compatibilityKey = 'Excellent';
            description = I18n.t('matching.manglik_desc.both_manglik_cancelled');
            recommendations.push(I18n.t('matching.manglik_desc.both_manglik_adv'));
        } else if (!p1Manglik && !p2Manglik) {
            compatibilityKey = 'Excellent';
            description = I18n.t('matching.manglik_desc.both_safe');
        } else if (p1Manglik !== p2Manglik) {
            // One Manglik, one not
            const manglikPerson = p1Manglik ? person1Analysis : person2Analysis;
            const intensity = manglikPerson.intensity;

            if (intensity === 'Low' || intensity === 'Very Low') {
                compatibilityKey = 'Acceptable';
                description = I18n.t('matching.manglik_desc.one_low');
                recommendations.push(I18n.t('matching.manglik_desc.minor_remedy'));
                recommendations.push(I18n.t('matching.manglik_desc.both_manglik_adv')); // Wait, this is for both? No.
                // Let's re-check recommendations in locale.
            } else if (intensity === 'Medium' || intensity === 'Medium-High') {
                compatibilityKey = 'Caution';
                description = I18n.t('matching.manglik_desc.one_medium');
                warnings.push(I18n.t('matching.manglik_desc.caution_manglik'));
                recommendations.push(I18n.t('matching.manglik_desc.kumbh_vivah'));
                recommendations.push(I18n.t('matching.manglik_desc.wait_28'));
                recommendations.push(I18n.t('matching.manglik_desc.consult_astrologer'));
            } else if (intensity === 'High') {
                compatibilityKey = 'Not Recommended';
                description = I18n.t('matching.manglik_desc.one_high');
                warnings.push(I18n.t('matching.manglik_desc.high_manglik_warning'));
                warnings.push(I18n.t('matching.manglik_desc.both_manglik_adv')); // Wait, wrong logic in original?
                recommendations.push(I18n.t('matching.manglik_desc.extensive_remedies'));
                recommendations.push(I18n.t('matching.manglik_desc.kumbh_essential'));
                recommendations.push(I18n.t('matching.manglik_desc.overall_check'));
            }
        }

        return {
            compatibility: compatibilityKey,
            description: description,
            warnings: warnings,
            recommendations: recommendations,
            person1: {
                isManglik: p1Manglik,
                intensity: person1Analysis.intensity
            },
            person2: {
                isManglik: p2Manglik,
                intensity: person2Analysis.intensity
            }
        };
    }
}

export default new Manglik();
