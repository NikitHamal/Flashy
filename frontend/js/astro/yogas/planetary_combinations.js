/**
 * Planetary Combination Yogas Module
 * Implements specific two-planet conjunctions and their effects
 */

import { YogaModuleBase, createYoga } from './base.js';

export class PlanetaryCombinationYogas extends YogaModuleBase {
    check() {
        this._checkVenusShaniYoga();
        this._checkGuruShukraYoga();
        this._checkRaviMangalYoga();
        this._checkChandraShukraYoga();
        this._checkBudhaShukraYoga();
        this._checkShaniRahuYoga();
        this._checkMangalShaniYoga();
        this._checkGuruChandraVariations();
        this._checkShaniKetuYoga();
        this._checkMangalKetuYoga();
        this._checkShukraRahuYoga();
        this._checkBudhaRahuYoga();
        this._checkGrahaYuddha();
    }

    /**
     * Venus-Saturn Yoga
     */
    _checkVenusShaniYoga() {
        if (!this.isConjunct('Venus', 'Saturn')) return;

        const house = this.getHouse('Venus');
        const venusDig = this.getDignity('Venus');
        const satDig = this.getDignity('Saturn');

        let nature = 'Neutral';
        let description = 'Venus-Saturn conjunction. Delayed gratification in love, lasting but serious relationships, appreciation for classical arts.';

        if (['Exalted', 'Own'].includes(venusDig) || ['Exalted', 'Own'].includes(satDig)) {
            nature = 'Benefic';
            description += ' Strong dignity - mature love, long-lasting marriage.';
        } else if (venusDig === 'Debilitated' || satDig === 'Debilitated') {
            nature = 'Malefic';
            description += ' Weak dignity - relationship struggles, delayed happiness.';
        }

        this.addYoga(createYoga({
            name: 'Shukra-Shani Yoga',
            nameKey: 'Shukra_Shani',
            category: 'Planetary_Combinations',
            description,
            descriptionKey: 'Shukra_Shani',
            planets: ['Venus', 'Saturn'],
            nature,
            strength: this.getStrength(['Venus', 'Saturn'])
        }));
    }

    /**
     * Jupiter-Venus Yoga
     */
    _checkGuruShukraYoga() {
        if (!this.isConjunct('Jupiter', 'Venus')) return;

        const house = this.getHouse('Jupiter');

        // These are natural enemies but their conjunction has specific effects
        let description = 'Jupiter-Venus conjunction. Wealth, luxury, and wisdom combined. Good for arts, finance, counseling. ';

        if ([1, 4, 5, 9, 10].includes(house)) {
            description += 'Well-placed - excellent for material and spiritual prosperity.';
        } else {
            description += 'May cause conflicts between spiritual values and material desires.';
        }

        this.addYoga(createYoga({
            name: 'Guru-Shukra Yoga',
            nameKey: 'Guru_Shukra',
            category: 'Planetary_Combinations',
            description,
            descriptionKey: 'Guru_Shukra',
            planets: ['Jupiter', 'Venus'],
            nature: 'Benefic',
            strength: this.getStrength(['Jupiter', 'Venus'])
        }));
    }

    /**
     * Sun-Mars Yoga
     */
    _checkRaviMangalYoga() {
        if (!this.isConjunct('Sun', 'Mars')) return;

        const house = this.getHouse('Sun');
        const upachaya = [3, 6, 10, 11];

        let nature = 'Benefic';
        let description = 'Sun-Mars conjunction. Powerful combination - leadership, courage, authority, military/police aptitude.';

        if (upachaya.includes(house)) {
            description += ' In Upachaya - excellent for competitive success.';
        } else if ([7, 8, 12].includes(house)) {
            nature = 'Neutral';
            description += ' May cause aggression or conflict issues.';
        }

        this.addYoga(createYoga({
            name: 'Ravi-Mangal Yoga',
            nameKey: 'Ravi_Mangal',
            category: 'Planetary_Combinations',
            description,
            descriptionKey: 'Ravi_Mangal',
            planets: ['Sun', 'Mars'],
            nature,
            strength: this.getStrength(['Sun', 'Mars'])
        }));
    }

    /**
     * Moon-Venus Yoga
     */
    _checkChandraShukraYoga() {
        if (!this.isConjunct('Moon', 'Venus')) return;

        const house = this.getHouse('Moon');

        let description = 'Moon-Venus conjunction. Beauty, artistic sense, emotional sensitivity, luxury-loving nature.';

        if ([1, 2, 4, 5, 7].includes(house)) {
            description += ' Well-placed - attractive personality, comfortable life.';
        }

        this.addYoga(createYoga({
            name: 'Chandra-Shukra Yoga',
            nameKey: 'Chandra_Shukra',
            category: 'Planetary_Combinations',
            description,
            descriptionKey: 'Chandra_Shukra',
            planets: ['Moon', 'Venus'],
            nature: 'Benefic',
            strength: this.getStrength(['Moon', 'Venus'])
        }));
    }

    /**
     * Mercury-Venus Yoga
     */
    _checkBudhaShukraYoga() {
        if (!this.isConjunct('Mercury', 'Venus')) return;

        const house = this.getHouse('Mercury');

        let description = 'Mercury-Venus conjunction. Excellent for arts, writing, music, diplomacy. Charming communication.';

        if ([2, 3, 5, 10].includes(house)) {
            description += ' In expression houses - creative success, entertainment industry aptitude.';
        }

        this.addYoga(createYoga({
            name: 'Budha-Shukra Yoga',
            nameKey: 'Budha_Shukra',
            category: 'Planetary_Combinations',
            description,
            descriptionKey: 'Budha_Shukra',
            planets: ['Mercury', 'Venus'],
            nature: 'Benefic',
            strength: this.getStrength(['Mercury', 'Venus'])
        }));
    }

    /**
     * Saturn-Rahu Yoga (Shrapit - covered in doshas, this is the combination aspect)
     */
    _checkShaniRahuYoga() {
        if (!this.isConjunct('Saturn', 'Rahu')) return;

        const house = this.getHouse('Saturn');

        let nature = 'Malefic';
        let description = 'Saturn-Rahu conjunction. Karmic obstacles, hidden enemies, chronic issues. ';

        // Check for mitigation
        const jupAspects = this.aspects('Jupiter', 'Saturn');
        if (jupAspects) {
            nature = 'Neutral';
            description += 'Jupiter aspect provides relief. ';
        }

        if ([3, 6, 10, 11].includes(house)) {
            description += 'In Upachaya - can overcome obstacles through perseverance.';
        } else {
            description += 'Requires strong remedies for Saturn and Rahu.';
        }

        this.addYoga(createYoga({
            name: 'Shani-Rahu Yoga',
            nameKey: 'Shani_Rahu',
            category: 'Planetary_Combinations',
            description,
            descriptionKey: 'Shani_Rahu',
            planets: ['Saturn', 'Rahu'],
            nature,
            strength: 4
        }));
    }

    /**
     * Mars-Saturn Yoga
     */
    _checkMangalShaniYoga() {
        if (!this.isConjunct('Mars', 'Saturn')) return;

        const house = this.getHouse('Mars');

        let nature = 'Neutral';
        let description = 'Mars-Saturn conjunction. Fire meets ice - frustration, delayed action, but eventual determination. Engineering, construction.';

        if ([3, 6, 10, 11].includes(house)) {
            nature = 'Benefic';
            description += ' In Upachaya - success through persistent effort.';
        } else if ([1, 4, 7, 8].includes(house)) {
            nature = 'Malefic';
            description += ' May cause health issues, accidents, or relationship friction.';
        }

        this.addYoga(createYoga({
            name: 'Mangal-Shani Yoga',
            nameKey: 'Mangal_Shani',
            category: 'Planetary_Combinations',
            description,
            descriptionKey: 'Mangal_Shani',
            planets: ['Mars', 'Saturn'],
            nature,
            strength: this.getStrength(['Mars', 'Saturn'])
        }));
    }

    /**
     * Jupiter-Moon variations beyond Gajakesari
     */
    _checkGuruChandraVariations() {
        if (!this.isConjunct('Jupiter', 'Moon')) return;

        // Gajakesari is Kendra-based, this is conjunction
        const house = this.getHouse('Jupiter');
        const moonWaxing = this.isWaxingMoon();

        let description = 'Jupiter-Moon conjunction. Wisdom meets emotion - generous, nurturing, popular, good fortune.';

        if (moonWaxing) {
            description += ' Waxing Moon enhances benefits.';
        }

        if ([1, 5, 9].includes(house)) {
            description += ' In Trikona - exceptional blessing.';
        }

        this.addYoga(createYoga({
            name: 'Guru-Chandra Yoga',
            nameKey: 'Guru_Chandra',
            category: 'Planetary_Combinations',
            description,
            descriptionKey: 'Guru_Chandra',
            planets: ['Jupiter', 'Moon'],
            nature: 'Benefic',
            strength: this.getStrength(['Jupiter', 'Moon']) + (moonWaxing ? 1 : 0)
        }));
    }

    /**
     * Saturn-Ketu Yoga
     */
    _checkShaniKetuYoga() {
        if (!this.isConjunct('Saturn', 'Ketu')) return;

        const house = this.getHouse('Saturn');

        let description = 'Saturn-Ketu conjunction. Deep spirituality, detachment, past-life karma surfacing. Good for meditation, research.';

        if ([8, 12].includes(house)) {
            description += ' In moksha houses - spiritual liberation potential.';
        }

        this.addYoga(createYoga({
            name: 'Shani-Ketu Yoga',
            nameKey: 'Shani_Ketu',
            category: 'Planetary_Combinations',
            description,
            descriptionKey: 'Shani_Ketu',
            planets: ['Saturn', 'Ketu'],
            nature: 'Neutral',
            strength: 5
        }));
    }

    /**
     * Mars-Ketu Yoga (Pishach Yoga)
     */
    _checkMangalKetuYoga() {
        if (!this.isConjunct('Mars', 'Ketu')) return;

        const house = this.getHouse('Mars');

        let nature = 'Neutral';
        let description = 'Mars-Ketu conjunction (Pishach Yoga). Sudden events, surgical skills, occult interests, past-life warrior karma.';

        if ([3, 6, 10, 11].includes(house)) {
            nature = 'Benefic';
            description += ' In Upachaya - courage in adversity.';
        } else if ([1, 4, 7].includes(house)) {
            nature = 'Malefic';
            description += ' Care needed for accidents, conflicts.';
        }

        this.addYoga(createYoga({
            name: 'Mangal-Ketu Yoga (Pishach)',
            nameKey: 'Mangal_Ketu',
            category: 'Planetary_Combinations',
            description,
            descriptionKey: 'Mangal_Ketu',
            planets: ['Mars', 'Ketu'],
            nature,
            strength: 5
        }));
    }

    /**
     * Venus-Rahu Yoga
     */
    _checkShukraRahuYoga() {
        if (!this.isConjunct('Venus', 'Rahu')) return;

        const house = this.getHouse('Venus');

        let description = 'Venus-Rahu conjunction. Unconventional relationships, foreign connections, intense desires. Film industry, glamour.';

        if ([1, 5, 7, 10].includes(house)) {
            description += ' Can bring fame through beauty/arts, but with intensity.';
        }

        this.addYoga(createYoga({
            name: 'Shukra-Rahu Yoga',
            nameKey: 'Shukra_Rahu',
            category: 'Planetary_Combinations',
            description,
            descriptionKey: 'Shukra_Rahu',
            planets: ['Venus', 'Rahu'],
            nature: 'Neutral',
            strength: 5
        }));
    }

    /**
     * Mercury-Rahu Yoga
     */
    _checkBudhaRahuYoga() {
        if (!this.isConjunct('Mercury', 'Rahu')) return;

        const house = this.getHouse('Mercury');

        let description = 'Mercury-Rahu conjunction. Clever, unconventional thinking, tech-savvy, foreign languages. Risk of deception.';

        if ([3, 10, 11].includes(house)) {
            description += ' Good for technology, innovation, unconventional careers.';
        }

        this.addYoga(createYoga({
            name: 'Budha-Rahu Yoga',
            nameKey: 'Budha_Rahu',
            category: 'Planetary_Combinations',
            description,
            descriptionKey: 'Budha_Rahu',
            planets: ['Mercury', 'Rahu'],
            nature: 'Neutral',
            strength: 5
        }));
    }

    /**
     * Graha Yuddha (Planetary War)
     * When two planets are within 1 degree
     */
    _checkGrahaYuddha() {
        const fivePlanets = ['Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];

        for (let i = 0; i < fivePlanets.length; i++) {
            for (let j = i + 1; j < fivePlanets.length; j++) {
                const p1 = fivePlanets[i];
                const p2 = fivePlanets[j];

                if (!this.isConjunct(p1, p2)) continue;

                const lon1 = this.getLongitude(p1);
                const lon2 = this.getLongitude(p2);

                let diff = Math.abs(lon1 - lon2);
                if (diff > 180) diff = 360 - diff;

                if (diff <= 1) {
                    // Planetary war - determine winner by brightness/dignity
                    const strength1 = this.getStrength([p1]);
                    const strength2 = this.getStrength([p2]);
                    const winner = strength1 > strength2 ? p1 : p2;
                    const loser = winner === p1 ? p2 : p1;

                    this.addYoga(createYoga({
                        name: `Graha Yuddha (${p1}-${p2})`,
                        nameKey: 'Graha_Yuddha',
                        category: 'Planetary_Combinations',
                        description: `Planetary war between ${p1} and ${p2} (within 1°). ${winner} wins - its significations prosper. ${loser}'s significations may suffer.`,
                        descriptionKey: 'Graha_Yuddha',
                        params: { winner, loser },
                        planets: [p1, p2],
                        nature: 'Neutral',
                        strength: 4
                    }));
                }
            }
        }
    }
}

export default PlanetaryCombinationYogas;
