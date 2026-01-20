/**
 * ============================================================================
 * DARIDRA YOGAS - Poverty and Financial Hardship Indicators
 * ============================================================================
 *
 * These yogas indicate financial challenges, blocked gains, and poverty.
 * Important to detect both for awareness and for suggesting remedies.
 * Many have cancellation conditions that should be checked.
 *
 * References:
 * - Brihat Parashara Hora Shastra (BPHS) Chapter 41
 * - Phaladeepika
 * - Jataka Parijata
 *
 * @module yogas/daridra
 * @version 1.0.0
 */

import I18n from '../../core/i18n.js';
import { YogaModuleBase, createYoga, dusthanas, kendras, trikonas } from './base.js';

export class DaridraYogas extends YogaModuleBase {
    constructor(ctx) {
        super(ctx);
    }

    check() {
        this._checkDaridraYogas();
        this._checkDaridraBhangaYogas();
        this._checkSpecificPovertyYogas();
    }

    /**
     * Main Daridra Yoga checks
     */
    _checkDaridraYogas() {
        const ctx = this.ctx;
        const lord11 = ctx.getHouseLord(11);
        const lord2 = ctx.getHouseLord(2);
        const lord1 = ctx.getHouseLord(1);

        // 1. Classic Daridra Yoga: 11th lord in Dusthana
        const lord11House = this.getHouse(lord11);
        if (dusthanas.includes(lord11House)) {
            const dignity = this.getDignity(lord11);
            const isWeak = dignity === 'Debilitated' || this.isCombust(lord11);

            if (isWeak) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Daridra_11.name'),
                    nameKey: 'Daridra_11',
                    category: 'Daridra',
                    description: I18n.t('lists.yoga_list.Daridra_11.effects'),
                    descriptionKey: 'Daridra_11',
                    planets: [lord11],
                    nature: 'Malefic',
                    strength: 3
                }));
            } else {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Daridra_Mild.name'),
                    nameKey: 'Daridra_Mild',
                    category: 'Daridra',
                    description: I18n.t('lists.yoga_list.Daridra_Mild.effects'),
                    descriptionKey: 'Daridra_Mild',
                    planets: [lord11],
                    nature: 'Malefic',
                    strength: 4
                }));
            }
        }

        // 2. Daridra Yoga: 2nd lord in Dusthana and afflicted
        const lord2House = this.getHouse(lord2);
        if (dusthanas.includes(lord2House)) {
            const isAfflicted = this._isPlanetAfflicted(lord2);
            if (isAfflicted) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Daridra_2.name'),
                    nameKey: 'Daridra_2',
                    category: 'Daridra',
                    description: I18n.t('lists.yoga_list.Daridra_2.effects'),
                    descriptionKey: 'Daridra_2',
                    planets: [lord2],
                    nature: 'Malefic',
                    strength: 3
                }));
            }
        }

        // 3. Daridra Yoga: Lagna lord in 6th/8th/12th and afflicted
        const lord1House = this.getHouse(lord1);
        if (dusthanas.includes(lord1House)) {
            const isDebilitated = this.getDignity(lord1) === 'Debilitated';
            if (isDebilitated) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Daridra_Lagna.name'),
                    nameKey: 'Daridra_Lagna',
                    category: 'Daridra',
                    description: I18n.t('lists.yoga_list.Daridra_Lagna.effects'),
                    descriptionKey: 'Daridra_Lagna',
                    planets: [lord1],
                    nature: 'Malefic',
                    strength: 3
                }));
            }
        }

        // 4. Chandra-Daridra: Weak Moon in Dusthana
        const moonHouse = this.getHouse('Moon');
        const moonDignity = this.getDignity('Moon');
        const isWaningMoon = !this.isWaxingMoon();

        if (dusthanas.includes(moonHouse) && isWaningMoon && moonDignity !== 'Exalted') {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Chandra_Daridra.name'),
                nameKey: 'Chandra_Daridra',
                category: 'Daridra',
                description: I18n.t('lists.yoga_list.Chandra_Daridra.effects'),
                descriptionKey: 'Chandra_Daridra',
                planets: ['Moon'],
                nature: 'Malefic',
                strength: 4
            }));
        }

        // 5. Guru-Daridra: Jupiter afflicted in Dusthana
        const jupiterHouse = this.getHouse('Jupiter');
        const jupiterDignity = this.getDignity('Jupiter');
        if (dusthanas.includes(jupiterHouse) && jupiterDignity === 'Debilitated') {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Guru_Daridra.name'),
                nameKey: 'Guru_Daridra',
                category: 'Daridra',
                description: I18n.t('lists.yoga_list.Guru_Daridra.effects'),
                descriptionKey: 'Guru_Daridra',
                planets: ['Jupiter'],
                nature: 'Malefic',
                strength: 3
            }));
        }

        // 6. 5th and 9th lords in Dusthana
        const lord5 = ctx.getHouseLord(5);
        const lord9 = ctx.getHouseLord(9);
        const lord5House = this.getHouse(lord5);
        const lord9House = this.getHouse(lord9);

        if (dusthanas.includes(lord5House) && dusthanas.includes(lord9House)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Bhagya_Daridra.name'),
                nameKey: 'Bhagya_Daridra',
                category: 'Daridra',
                description: I18n.t('lists.yoga_list.Bhagya_Daridra.effects'),
                descriptionKey: 'Bhagya_Daridra',
                planets: [lord5, lord9],
                nature: 'Malefic',
                strength: 3
            }));
        }
    }

    /**
     * Check for cancellation of Daridra Yogas
     */
    _checkDaridraBhangaYogas() {
        const ctx = this.ctx;
        const lord11 = ctx.getHouseLord(11);
        const lord11House = this.getHouse(lord11);

        // Daridra Bhanga conditions
        const bhangaConditions = [];

        // 1. 11th lord in Dusthana but exalted
        if (dusthanas.includes(lord11House) && this.getDignity(lord11) === 'Exalted') {
            bhangaConditions.push('Exalted');
        }

        // 2. Jupiter aspects 2nd or 11th house
        const jupiterHouse = this.getHouse('Jupiter');
        if (jupiterHouse !== -1) {
            const jupiterAspects = this._getJupiterAspectedHouses(jupiterHouse);
            if (jupiterAspects.includes(2) || jupiterAspects.includes(11)) {
                bhangaConditions.push('Jupiter aspect');
            }
        }

        // 3. Benefics in 2nd and 11th houses
        const benefics = this.getNaturalBenefics();
        const planetsIn2 = ctx.getPlanetsInHouse(2);
        const planetsIn11 = ctx.getPlanetsInHouse(11);
        const beneficsIn2 = planetsIn2.filter(p => benefics.includes(p));
        const beneficsIn11 = planetsIn11.filter(p => benefics.includes(p));

        if (beneficsIn2.length > 0 && beneficsIn11.length > 0) {
            bhangaConditions.push('Benefics');
        }

        // 4. Strong Lagna lord in Kendra
        const lord1 = ctx.getHouseLord(1);
        const lord1House = this.getHouse(lord1);
        const lord1Strong = this.isStrong(lord1);

        if (kendras.includes(lord1House) && lord1Strong) {
            bhangaConditions.push('Lagna Lord');
        }

        // If multiple bhanga conditions exist, report Daridra Bhanga
        if (bhangaConditions.length >= 2) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Daridra_Bhanga.name'),
                nameKey: 'Daridra_Bhanga',
                category: 'Daridra_Bhanga',
                description: I18n.t('lists.yoga_list.Daridra_Bhanga.effects'),
                descriptionKey: 'Daridra_Bhanga',
                planets: [lord11, 'Jupiter'],
                nature: 'Benefic',
                strength: 6
            }));
        }
    }

    /**
     * Check specific poverty-related yogas from classical texts
     */
    _checkSpecificPovertyYogas() {
        const ctx = this.ctx;

        // 1. Kemadruma-like poverty yoga
        const moonHouse = this.getHouse('Moon');
        if (moonHouse !== -1) {
            const planetsIn2FromMoon = this._getPlanetsInHouseFromMoon(2);
            const planetsIn12FromMoon = this._getPlanetsInHouseFromMoon(12);

            // Moon isolated without support
            if (planetsIn2FromMoon.length === 0 && planetsIn12FromMoon.length === 0) {
                // Check if Moon is also weak
                if (!this.isStrong('Moon') && !this.isWaxingMoon()) {
                    // Check for cancellation
                    const moonInKendra = kendras.includes(moonHouse);
                    if (!moonInKendra) {
                        this.addYoga(createYoga({
                            name: I18n.t('lists.yoga_list.Kemadruma_Poverty.name'),
                            nameKey: 'Kemadruma_Poverty',
                            category: 'Daridra',
                            description: I18n.t('lists.yoga_list.Kemadruma_Poverty.effects'),
                            descriptionKey: 'Kemadruma_Poverty',
                            planets: ['Moon'],
                            nature: 'Malefic',
                            strength: 4
                        }));
                    }
                }
            }
        }

        // 2. Saturn-Mars combination in wealth houses
        if (this.isConjunct('Saturn', 'Mars')) {
            const conjHouse = this.getHouse('Saturn');
            if ([2, 5, 9, 11].includes(conjHouse)) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Shani_Mangal_Daridra.name'),
                    nameKey: 'Shani_Mangal_Daridra',
                    category: 'Daridra',
                    description: I18n.t('lists.yoga_list.Shani_Mangal_Daridra.effects'),
                    descriptionKey: 'Shani_Mangal_Daridra',
                    planets: ['Saturn', 'Mars'],
                    nature: 'Malefic',
                    strength: 4
                }));
            }
        }

        // 3. Rahu in 2nd afflicting wealth
        const rahuHouse = this.getHouse('Rahu');
        if (rahuHouse === 2) {
            const lord2 = ctx.getHouseLord(2);
            if (this._isPlanetAfflicted(lord2)) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Rahu_Daridra.name'),
                    nameKey: 'Rahu_Daridra',
                    category: 'Daridra',
                    description: I18n.t('lists.yoga_list.Rahu_Daridra.effects'),
                    descriptionKey: 'Rahu_Daridra',
                    planets: ['Rahu', lord2],
                    nature: 'Malefic',
                    strength: 4
                }));
            }
        }

        // 4. All malefics in 2nd, 4th, 5th houses
        const malefics = ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu'];
        const maleficsIn2 = malefics.filter(p => this.getHouse(p) === 2);
        const maleficsIn4 = malefics.filter(p => this.getHouse(p) === 4);
        const maleficsIn5 = malefics.filter(p => this.getHouse(p) === 5);

        if (maleficsIn2.length >= 2 || maleficsIn4.length >= 2 || maleficsIn5.length >= 2) {
            const affectedHouse = maleficsIn2.length >= 2 ? 2 : (maleficsIn4.length >= 2 ? 4 : 5);
            const affectedPlanets = affectedHouse === 2 ? maleficsIn2 : (affectedHouse === 4 ? maleficsIn4 : maleficsIn5);

            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Multi_Malefic_Daridra.name'),
                nameKey: 'Multi_Malefic_Daridra',
                category: 'Daridra',
                description: I18n.t('lists.yoga_list.Multi_Malefic_Daridra.effects'),
                descriptionKey: 'Multi_Malefic_Daridra',
                planets: affectedPlanets,
                nature: 'Malefic',
                strength: 3
            }));
        }

        // 5. 10th lord in 8th - Career obstacles
        const lord10 = ctx.getHouseLord(10);
        const lord10House = this.getHouse(lord10);
        if (lord10House === 8) {
            const isDebilitated = this.getDignity(lord10) === 'Debilitated';
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Karma_Daridra.name'),
                nameKey: 'Karma_Daridra',
                category: 'Daridra',
                description: I18n.t('lists.yoga_list.Karma_Daridra.effects', { 
                    planet: I18n.t('planets.' + lord10),
                    isDebilitated: isDebilitated ? I18n.t('analysis.debilitation_intensifies') : ''
                }),
                descriptionKey: 'Karma_Daridra',
                planets: [lord10],
                nature: isDebilitated ? 'Malefic' : 'Neutral',
                strength: isDebilitated ? 3 : 5
            }));
        }
    }

    /**
     * Helper: Check if planet is afflicted
     */
    _isPlanetAfflicted(planet) {
        const malefics = ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu'];

        // Check conjunction with malefics
        for (const malefic of malefics) {
            if (malefic !== planet && this.isConjunct(planet, malefic)) {
                return true;
            }
        }

        // Check aspect from malefics
        for (const malefic of malefics) {
            if (this.aspects(malefic, planet)) {
                return true;
            }
        }

        // Check combustion
        if (this.isCombust(planet)) {
            return true;
        }

        return false;
    }



    /**
     * Helper: Check if planet is afflicted
     */
    _isPlanetAfflicted(planet) {
        const malefics = ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu'];

        // Check conjunction with malefics
        for (const malefic of malefics) {
            if (malefic !== planet && this.isConjunct(planet, malefic)) {
                return true;
            }
        }

        // Check aspect from malefics
        for (const malefic of malefics) {
            if (this.aspects(malefic, planet)) {
                return true;
            }
        }

        // Check combustion
        if (this.isCombust(planet)) {
            return true;
        }

        return false;
    }

    /**
     * Helper: Get planets in house from Moon
     */
    _getPlanetsInHouseFromMoon(houseFromMoon) {
        const moonRasi = this.getRasi('Moon');
        if (moonRasi === -1) return [];

        const sevenPlanets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
        const result = [];

        for (const planet of sevenPlanets) {
            if (planet === 'Moon') continue;
            const planetRasi = this.getRasi(planet);
            if (planetRasi === -1) continue;

            let diff = planetRasi - moonRasi;
            if (diff < 0) diff += 12;
            const house = diff + 1;

            if (house === houseFromMoon) {
                result.push(planet);
            }
        }

        return result;
    }

    /**
     * Helper: Get houses aspected by Jupiter
     */
    _getJupiterAspectedHouses(fromHouse) {
        const aspects = [5, 7, 9];
        return aspects.map(a => {
            let house = fromHouse + a - 1;
            if (house > 12) house -= 12;
            return house;
        });
    }
}

export default DaridraYogas;
