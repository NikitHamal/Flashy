/**
 * Vargottama Yoga Module
 * Implements yogas for planets in same sign in D1 and D9
 */

import { YogaModuleBase, createYoga, sevenPlanets, allPlanets } from './base.js';

export class VargottamaYogas extends YogaModuleBase {
    check() {
        this._checkVargottamaPlanets();
        this._checkVargottamaLagna();
        this._checkPushkaraNavamsha();
        this._checkPushkaraAmsha();
    }

    /**
     * Check Vargottama planets
     * Planet in same sign in D1 (Rasi) and D9 (Navamsha)
     */
    _checkVargottamaPlanets() {
        // Need Navamsha data from context
        if (!this.ctx.navamshaPositions) return;

        for (const planet of allPlanets) {
            const rasiSign = this.getRasi(planet);
            const navamshaSign = this.ctx.navamshaPositions[planet];

            if (rasiSign === -1 || navamshaSign === undefined) continue;

            if (rasiSign === navamshaSign) {
                const planetDescriptions = {
                    'Sun': 'Soul strength, confidence, authority enhanced. Father blessed.',
                    'Moon': 'Mental peace, emotional stability. Mother blessed.',
                    'Mars': 'Courage, property, siblings blessed. Strong energy.',
                    'Mercury': 'Intelligence, communication, business blessed.',
                    'Jupiter': 'Wisdom, children, fortune blessed. Guru\'s grace.',
                    'Venus': 'Relationships, arts, luxury blessed. Marital happiness.',
                    'Saturn': 'Discipline, longevity, perseverance blessed.',
                    'Rahu': 'Worldly desires fulfilled, foreign connections blessed.',
                    'Ketu': 'Spiritual liberation, detachment, occult knowledge blessed.'
                };

                const house = this.getHouse(planet);
                const dignity = this.getDignity(planet);
                let strength = 7;

                // Enhanced if also in good dignity
                if (['Exalted', 'Own', 'Moolatrikona'].includes(dignity)) {
                    strength = 9;
                }

                this.addYoga(createYoga({
                    name: `Vargottama ${planet}`,
                    nameKey: 'Vargottama',
                    category: 'Vargottama',
                    description: `${planet} in same sign in Rasi and Navamsha. ${planetDescriptions[planet] || 'Enhanced strength and expression.'}`,
                    descriptionKey: 'Vargottama',
                    params: { planet },
                    planets: [planet],
                    nature: 'Benefic',
                    strength
                }));
            }
        }
    }

    /**
     * Check Vargottama Lagna
     * Lagna in same sign in D1 and D9
     */
    _checkVargottamaLagna() {
        if (!this.ctx.navamshaLagna) return;

        const rasiLagna = this.ctx.lagnaRasi;
        const navamshaLagna = this.ctx.navamshaLagna;

        if (rasiLagna === navamshaLagna) {
            this.addYoga(createYoga({
                name: 'Vargottama Lagna',
                nameKey: 'Vargottama_Lagna',
                category: 'Vargottama',
                description: 'Lagna in same sign in Rasi and Navamsha. Exceptional strength of personality, health, and overall chart. Very auspicious.',
                descriptionKey: 'Vargottama_Lagna',
                planets: [],
                nature: 'Benefic',
                strength: 9
            }));
        }
    }

    /**
     * Pushkara Navamsha
     * Planets in specific auspicious navamsha portions
     */
    _checkPushkaraNavamsha() {
        // Pushkara Navamshas are specific navamsha positions considered very auspicious
        // They occur at specific degree ranges in each sign

        const pushkaraRanges = {
            // Fire signs (Aries, Leo, Sagittarius): 7th (20°-23°20') and 9th (26°40'-30°)
            0: [[20, 23.33], [26.67, 30]], // Aries
            4: [[20, 23.33], [26.67, 30]], // Leo
            8: [[20, 23.33], [26.67, 30]], // Sagittarius
            // Earth signs (Taurus, Virgo, Capricorn): 6°40'-10° and 13°20'-16°40'
            1: [[6.67, 10], [13.33, 16.67]], // Taurus
            5: [[6.67, 10], [13.33, 16.67]], // Virgo
            9: [[6.67, 10], [13.33, 16.67]], // Capricorn
            // Air signs (Gemini, Libra, Aquarius): 16°40'-20° and 23°20'-26°40'
            2: [[16.67, 20], [23.33, 26.67]], // Gemini
            6: [[16.67, 20], [23.33, 26.67]], // Libra
            10: [[16.67, 20], [23.33, 26.67]], // Aquarius
            // Water signs (Cancer, Scorpio, Pisces): 0°-3°20' and 6°40'-10°
            3: [[0, 3.33], [6.67, 10]], // Cancer
            7: [[0, 3.33], [6.67, 10]], // Scorpio
            11: [[0, 3.33], [6.67, 10]]  // Pisces
        };

        for (const planet of sevenPlanets) {
            const sign = this.getRasi(planet);
            const degree = this.getDegree(planet);

            if (sign === -1 || isNaN(degree)) continue;

            const ranges = pushkaraRanges[sign];
            if (!ranges) continue;

            for (const [start, end] of ranges) {
                if (degree >= start && degree <= end) {
                    this.addYoga(createYoga({
                        name: `Pushkara Navamsha ${planet}`,
                        nameKey: 'Pushkara_Navamsha',
                        category: 'Vargottama',
                        description: `${planet} at ${degree.toFixed(1)}° in Pushkara Navamsha. Nourishing position - blessings flow to ${planet}'s significations.`,
                        descriptionKey: 'Pushkara_Navamsha',
                        params: { planet, degree },
                        planets: [planet],
                        nature: 'Benefic',
                        strength: 6
                    }));
                    break;
                }
            }
        }
    }

    /**
     * Pushkara Bhaga (Pushkara Degrees)
     * Specific degrees in each sign that are highly auspicious
     */
    _checkPushkaraAmsha() {
        // Pushkara degrees - extremely auspicious specific degrees
        const pushkaraDegrees = {
            0: [21, 24], // Aries
            1: [14, 19], // Taurus
            2: [18, 27], // Gemini
            3: [9, 26],  // Cancer
            4: [5, 14],  // Leo
            5: [6, 21],  // Virgo
            6: [11, 24], // Libra
            7: [14, 23], // Scorpio
            8: [18, 19], // Sagittarius
            9: [9, 20],  // Capricorn
            10: [8, 17], // Aquarius
            11: [11, 20] // Pisces
        };

        for (const planet of sevenPlanets) {
            const sign = this.getRasi(planet);
            const degree = Math.floor(this.getDegree(planet));

            if (sign === -1 || isNaN(degree)) continue;

            const degrees = pushkaraDegrees[sign];
            if (degrees && degrees.includes(degree)) {
                this.addYoga(createYoga({
                    name: `Pushkara Bhaga ${planet}`,
                    nameKey: 'Pushkara_Bhaga',
                    category: 'Vargottama',
                    description: `${planet} at ${degree}° - Pushkara Bhaga (auspicious degree). Highly beneficial for ${planet}'s significations. Exceptionally fortunate placement.`,
                    descriptionKey: 'Pushkara_Bhaga',
                    params: { planet, degree },
                    planets: [planet],
                    nature: 'Benefic',
                    strength: 8
                }));
            }
        }
    }
}

export default VargottamaYogas;
