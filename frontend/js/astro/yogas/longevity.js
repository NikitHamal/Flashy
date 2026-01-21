/**
 * Longevity (Ayur) Yogas Module
 * Implements life span indicators and health-related yogas
 */

import { YogaModuleBase, createYoga, kendras, trikonas, dusthanas, sevenPlanets } from './base.js';

export class LongevityYogas extends YogaModuleBase {
    check() {
        this._checkAlpayuYoga();
        this._checkMadhyayuYoga();
        this._checkDeerghayuYoga();
        this._checkBalarishtaVariations();
        this._checkMrityubhagYoga();
        this._checkApamrityuYoga();
        this._checkKakshyaYogas();
        this._checkAmaranathYoga();
    }

    /**
     * Alpayu Yoga (Short Life)
     * Severe afflictions to Lagna, Lagna lord, Moon, 8th house
     */
    _checkAlpayuYoga() {
        let shortLifeFactors = 0;
        const factors = [];

        const lord1 = this.getHouseLord(1);
        const lord8 = this.getHouseLord(8);

        // Lagna lord in 6/8/12
        const lord1House = this.getHouse(lord1);
        if (dusthanas.includes(lord1House)) {
            shortLifeFactors++;
            factors.push(`Lagna lord in ${lord1House}th`);
        }

        // Lagna lord debilitated
        if (this.getDignity(lord1) === 'Debilitated') {
            shortLifeFactors++;
            factors.push('Lagna lord debilitated');
        }

        // Moon in 6/8/12 and waning
        const moonHouse = this.getHouse('Moon');
        if (dusthanas.includes(moonHouse) && !this.isWaxingMoon()) {
            shortLifeFactors++;
            factors.push(`Waning Moon in ${moonHouse}th`);
        }

        // Moon debilitated
        if (this.getDignity('Moon') === 'Debilitated') {
            shortLifeFactors++;
            factors.push('Moon debilitated');
        }

        // 8th lord in Lagna afflicted
        const lord8House = this.getHouse(lord8);
        if (lord8House === 1) {
            const malefics = this.getNaturalMalefics();
            const afflicted = malefics.some(m => this.isConjunct(lord8, m) || this.aspects(m, lord8));
            if (afflicted) {
                shortLifeFactors++;
                factors.push('8th lord in Lagna afflicted');
            }
        }

        // Malefics in 1st and 8th
        const maleficsIn1 = this.getPlanetsInHouse(1).filter(p => this.getNaturalMalefics().includes(p));
        const maleficsIn8 = this.getPlanetsInHouse(8).filter(p => this.getNaturalMalefics().includes(p));
        if (maleficsIn1.length > 0 && maleficsIn8.length > 0) {
            shortLifeFactors++;
            factors.push('Malefics in 1st and 8th');
        }

        if (shortLifeFactors >= 3) {
            this.addYoga(createYoga({
                name: 'Alpayu Yoga',
                nameKey: 'Alpayu',
                category: 'Longevity',
                description: `Short life indicators (${shortLifeFactors} factors): ${factors.join('; ')}. May indicate health challenges. Remedies essential.`,
                descriptionKey: 'Alpayu',
                planets: [lord1, lord8, 'Moon'],
                nature: 'Malefic',
                strength: 3
            }));
        }
    }

    /**
     * Madhyayu Yoga (Medium Life)
     * Mix of positive and negative longevity factors
     */
    _checkMadhyayuYoga() {
        let positiveFactors = 0;
        let negativeFactors = 0;

        const lord1 = this.getHouseLord(1);
        const lord8 = this.getHouseLord(8);

        // Positive: Lagna lord in Kendra/Trikona
        const lord1House = this.getHouse(lord1);
        if ([...kendras, ...trikonas].includes(lord1House)) {
            positiveFactors++;
        }

        // Positive: Strong 8th lord
        if (this.isStrong(lord8)) {
            positiveFactors++;
        }

        // Positive: Jupiter in Kendra
        if (kendras.includes(this.getHouse('Jupiter'))) {
            positiveFactors++;
        }

        // Negative: Lagna lord combust
        if (this.isCombust(lord1)) {
            negativeFactors++;
        }

        // Negative: Moon afflicted
        const malefics = this.getNaturalMalefics();
        const moonAfflicted = malefics.some(m => this.isConjunct('Moon', m));
        if (moonAfflicted) {
            negativeFactors++;
        }

        // Negative: Saturn aspects Lagna
        const saturnAspectsLagna = this._aspectsHouse('Saturn', this.getHouse('Saturn'), 1);
        if (saturnAspectsLagna) {
            negativeFactors++;
        }

        // Only medium if balanced
        if (positiveFactors >= 2 && negativeFactors >= 1 && positiveFactors <= negativeFactors + 2) {
            this.addYoga(createYoga({
                name: 'Madhyayu Yoga',
                nameKey: 'Madhyayu',
                category: 'Longevity',
                description: `Medium life span indicators. Balance of positive (${positiveFactors}) and challenging (${negativeFactors}) factors.`,
                descriptionKey: 'Madhyayu',
                planets: [lord1, lord8],
                nature: 'Neutral',
                strength: 5
            }));
        }
    }

    /**
     * Helper to check if planet aspects a specific house
     */
    _aspectsHouse(planet, planetHouse, targetHouse) {
        const aspects = {
            'Sun': [7], 'Moon': [7], 'Mercury': [7], 'Venus': [7],
            'Mars': [4, 7, 8], 'Jupiter': [5, 7, 9], 'Saturn': [3, 7, 10],
            'Rahu': [5, 7, 9], 'Ketu': [5, 7, 9]
        };

        const planetAspects = aspects[planet] || [7];
        for (const asp of planetAspects) {
            const aspectedHouse = ((planetHouse - 1 + asp) % 12) + 1;
            if (aspectedHouse === targetHouse) return true;
        }
        return false;
    }

    /**
     * Deerghayu Yoga (Long Life)
     * Strong longevity indicators
     */
    _checkDeerghayuYoga() {
        let longLifeFactors = 0;
        const factors = [];

        const lord1 = this.getHouseLord(1);
        const lord8 = this.getHouseLord(8);

        // Strong Lagna lord in Kendra/Trikona
        const lord1House = this.getHouse(lord1);
        if ([...kendras, ...trikonas].includes(lord1House) && this.isStrong(lord1)) {
            longLifeFactors++;
            factors.push('Strong Lagna lord in Kendra/Trikona');
        }

        // Strong 8th lord in good dignity
        const lord8Dignity = this.getDignity(lord8);
        if (['Exalted', 'Own', 'Moolatrikona'].includes(lord8Dignity)) {
            longLifeFactors++;
            factors.push(`8th lord ${lord8Dignity}`);
        }

        // Jupiter aspects Lagna
        const jupAspectsLagna = this._aspectsHouse('Jupiter', this.getHouse('Jupiter'), 1);
        if (jupAspectsLagna) {
            longLifeFactors++;
            factors.push('Jupiter aspects Lagna');
        }

        // Saturn in 3rd, 6th, or 11th (Upachaya from Lagna)
        const saturnHouse = this.getHouse('Saturn');
        if ([3, 6, 11].includes(saturnHouse)) {
            longLifeFactors++;
            factors.push(`Saturn in ${saturnHouse}th (Upachaya)`);
        }

        // Strong Moon
        if (this.isWaxingMoon() && ['Exalted', 'Own'].includes(this.getDignity('Moon'))) {
            longLifeFactors++;
            factors.push('Strong waxing Moon');
        }

        // Benefics in Kendras
        const benefics = this.getNaturalBenefics();
        const beneficsInKendras = benefics.filter(p => kendras.includes(this.getHouse(p)));
        if (beneficsInKendras.length >= 2) {
            longLifeFactors++;
            factors.push('Benefics in Kendras');
        }

        if (longLifeFactors >= 3) {
            this.addYoga(createYoga({
                name: 'Deerghayu Yoga',
                nameKey: 'Deerghayu',
                category: 'Longevity',
                description: `Long life indicators (${longLifeFactors} factors): ${factors.join('; ')}. Blessed with vitality and longevity.`,
                descriptionKey: 'Deerghayu',
                planets: [lord1, lord8, 'Jupiter'],
                nature: 'Benefic',
                strength: 8
            }));
        }
    }

    /**
     * Balarishta Variations
     * Early life health challenges
     */
    _checkBalarishtaVariations() {
        const moonHouse = this.getHouse('Moon');
        const moonDig = this.getDignity('Moon');
        const lord1 = this.getHouseLord(1);
        const malefics = this.getNaturalMalefics();

        const afflictions = [];

        // Moon in 6/8/12 and weak
        if (dusthanas.includes(moonHouse) && !this.isWaxingMoon()) {
            afflictions.push(`Waning Moon in ${moonHouse}th`);
        }

        // Moon debilitated
        if (moonDig === 'Debilitated') {
            afflictions.push('Moon debilitated');
        }

        // Malefics aspect Moon without benefic relief
        const maleficsAspectMoon = malefics.filter(m => this.aspects(m, 'Moon'));
        const beneficsAspectMoon = this.getNaturalBenefics().some(b => this.aspects(b, 'Moon'));

        if (maleficsAspectMoon.length > 0 && !beneficsAspectMoon) {
            afflictions.push(`${maleficsAspectMoon.join(', ')} aspect Moon without benefic relief`);
        }

        // Lagna lord in 6/8/12 combust
        const lord1House = this.getHouse(lord1);
        if (dusthanas.includes(lord1House) && this.isCombust(lord1)) {
            afflictions.push('Lagna lord in Dusthana and combust');
        }

        if (afflictions.length >= 2) {
            // Check for cancellation
            const jupiterInKendra = kendras.includes(this.getHouse('Jupiter'));
            const moonInKendra = kendras.includes(moonHouse);

            if (jupiterInKendra || moonInKendra) {
                this.addYoga(createYoga({
                    name: 'Balarishta Bhanga',
                    nameKey: 'Balarishta_Bhanga',
                    category: 'Longevity',
                    description: `Early life challenges cancelled by Jupiter/Moon in Kendra. Recovery after initial difficulties.`,
                    descriptionKey: 'Balarishta_Bhanga',
                    planets: ['Moon', 'Jupiter'],
                    nature: 'Neutral',
                    strength: 5
                }));
            } else {
                this.addYoga(createYoga({
                    name: 'Balarishta Yoga',
                    nameKey: 'Balarishta',
                    category: 'Longevity',
                    description: `Early childhood health challenges: ${afflictions.join('; ')}. Extra care needed in first years.`,
                    descriptionKey: 'Balarishta',
                    planets: ['Moon', lord1],
                    nature: 'Malefic',
                    strength: 3
                }));
            }
        }
    }

    /**
     * Mrityubhag Yoga
     * Moon/Lagna in death degrees (specific degrees per sign)
     */
    _checkMrityubhagYoga() {
        // Traditional Mrityubhaga degrees (varies by sign)
        const mrityuDegrees = {
            0: 26,  // Aries
            1: 12,  // Taurus
            2: 13,  // Gemini
            3: 25,  // Cancer
            4: 24,  // Leo
            5: 11,  // Virgo
            6: 26,  // Libra
            7: 14,  // Scorpio
            8: 13,  // Sagittarius
            9: 25,  // Capricorn
            10: 5,  // Aquarius
            11: 12  // Pisces
        };

        const moonSign = this.getRasi('Moon');
        const moonDegree = this.getDegree('Moon');
        const lagnaSign = this.ctx.lagnaRasi;

        // Check Moon in Mrityubhaga (within 1 degree orb)
        if (moonSign !== -1) {
            const mrityuDeg = mrityuDegrees[moonSign];
            if (Math.abs(moonDegree - mrityuDeg) <= 1) {
                this.addYoga(createYoga({
                    name: 'Mrityubhag Yoga (Moon)',
                    nameKey: 'Mrityubhag_Moon',
                    category: 'Longevity',
                    description: `Moon at ${moonDegree.toFixed(1)}° in death degree zone of ${this._getSignName(moonSign)}. Sensitive point - requires protective remedies.`,
                    descriptionKey: 'Mrityubhag_Moon',
                    planets: ['Moon'],
                    nature: 'Malefic',
                    strength: 3
                }));
            }
        }
    }

    /**
     * Get sign name from index
     */
    _getSignName(index) {
        const signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
            'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
        return signs[(index + 12) % 12];
    }

    /**
     * Apamrityu Yoga
     * Unnatural death indicators
     */
    _checkApamrityuYoga() {
        const malefics = this.getNaturalMalefics();
        let indicators = 0;
        const factors = [];

        // Mars-Saturn conjunction
        if (this.isConjunct('Mars', 'Saturn')) {
            indicators++;
            factors.push('Mars-Saturn conjunction');
        }

        // 8th lord with Mars and Saturn
        const lord8 = this.getHouseLord(8);
        const lord8WithMars = this.isConjunct(lord8, 'Mars');
        const lord8WithSaturn = this.isConjunct(lord8, 'Saturn');
        if (lord8WithMars && lord8WithSaturn) {
            indicators++;
            factors.push('8th lord with Mars and Saturn');
        }

        // Rahu in 8th aspected by Mars
        const rahuIn8 = this.getHouse('Rahu') === 8;
        const marsAspectsRahu = this.aspects('Mars', 'Rahu');
        if (rahuIn8 && marsAspectsRahu) {
            indicators++;
            factors.push('Rahu in 8th aspected by Mars');
        }

        // Multiple malefics in 8th
        const maleficsIn8 = this.getPlanetsInHouse(8).filter(p => malefics.includes(p));
        if (maleficsIn8.length >= 2) {
            indicators++;
            factors.push(`Multiple malefics in 8th (${maleficsIn8.join(', ')})`);
        }

        if (indicators >= 2) {
            // Check for protection
            const jupiterAspects8 = this._aspectsHouse('Jupiter', this.getHouse('Jupiter'), 8);

            if (jupiterAspects8) {
                this.addYoga(createYoga({
                    name: 'Apamrityu Bhanga',
                    nameKey: 'Apamrityu_Bhanga',
                    category: 'Longevity',
                    description: `Accident indicators neutralized by Jupiter's protection. Caution advised but protection available.`,
                    descriptionKey: 'Apamrityu_Bhanga',
                    planets: ['Jupiter', ...factors.includes('Mars-Saturn conjunction') ? ['Mars', 'Saturn'] : []],
                    nature: 'Neutral',
                    strength: 5
                }));
            } else {
                this.addYoga(createYoga({
                    name: 'Apamrityu Yoga',
                    nameKey: 'Apamrityu',
                    category: 'Longevity',
                    description: `Accident/sudden event indicators: ${factors.join('; ')}. Extra caution with vehicles, heights, and risky activities.`,
                    descriptionKey: 'Apamrityu',
                    planets: maleficsIn8.length > 0 ? maleficsIn8 : ['Mars', 'Saturn'],
                    nature: 'Malefic',
                    strength: 3
                }));
            }
        }
    }

    /**
     * Kakshya Hrasa/Vriddhi Yogas
     * Longevity modifications
     */
    _checkKakshyaYogas() {
        const lord8 = this.getHouseLord(8);
        const lord8House = this.getHouse(lord8);
        const lord8Dignity = this.getDignity(lord8);

        // Kakshya Vriddhi (Increase)
        if (['Exalted', 'Own'].includes(lord8Dignity) && kendras.includes(lord8House)) {
            this.addYoga(createYoga({
                name: 'Kakshya Vriddhi Yoga',
                nameKey: 'Kakshya_Vriddhi',
                category: 'Longevity',
                description: '8th lord strong in Kendra. Longevity increased - exceeds normal lifespan indicators.',
                descriptionKey: 'Kakshya_Vriddhi',
                planets: [lord8],
                nature: 'Benefic',
                strength: 7
            }));
        }

        // Kakshya Hrasa (Decrease)
        if (lord8Dignity === 'Debilitated' && dusthanas.includes(lord8House)) {
            this.addYoga(createYoga({
                name: 'Kakshya Hrasa Yoga',
                nameKey: 'Kakshya_Hrasa',
                category: 'Longevity',
                description: '8th lord weak in Dusthana. Longevity reduced - health consciousness essential.',
                descriptionKey: 'Kakshya_Hrasa',
                planets: [lord8],
                nature: 'Malefic',
                strength: 3
            }));
        }
    }

    /**
     * Amaranath Yoga
     * Exceptional longevity indicators
     */
    _checkAmaranathYoga() {
        let exceptionalFactors = 0;
        const factors = [];

        const lord1 = this.getHouseLord(1);
        const lord8 = this.getHouseLord(8);

        // Both Lagna and 8th lords exalted
        if (this.getDignity(lord1) === 'Exalted' && this.getDignity(lord8) === 'Exalted') {
            exceptionalFactors++;
            factors.push('Both Lagna and 8th lords exalted');
        }

        // Jupiter in Lagna exalted/own
        const jupHouse = this.getHouse('Jupiter');
        const jupDig = this.getDignity('Jupiter');
        if (jupHouse === 1 && ['Exalted', 'Own'].includes(jupDig)) {
            exceptionalFactors++;
            factors.push('Jupiter in Lagna in dignity');
        }

        // Saturn in 3rd/6th/11th and strong
        const satHouse = this.getHouse('Saturn');
        if ([3, 6, 11].includes(satHouse) && this.isStrong('Saturn')) {
            exceptionalFactors++;
            factors.push('Strong Saturn in Upachaya');
        }

        // All benefics in Kendras
        const benefics = this.getNaturalBenefics();
        const allBeneficsInKendras = benefics.every(b => kendras.includes(this.getHouse(b)));
        if (allBeneficsInKendras) {
            exceptionalFactors++;
            factors.push('All benefics in Kendras');
        }

        if (exceptionalFactors >= 2) {
            this.addYoga(createYoga({
                name: 'Amaranath Yoga',
                nameKey: 'Amaranath',
                category: 'Longevity',
                description: `Exceptional longevity: ${factors.join('; ')}. Blessed with very long, healthy life.`,
                descriptionKey: 'Amaranath',
                planets: [lord1, lord8, 'Jupiter'],
                nature: 'Benefic',
                strength: 9
            }));
        }
    }
}

export default LongevityYogas;
