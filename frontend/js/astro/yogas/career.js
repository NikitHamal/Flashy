/**
 * Career/Profession Yogas Module
 * Implements yogas related to career success and professional life
 */

import I18n from '../../core/i18n.js';
import { YogaModuleBase, createYoga, kendras, trikonas, dusthanas } from './base.js';

export class CareerYogas extends YogaModuleBase {
    check() {
        this._checkRajyaYoga();
        this._checkAmatyaYoga();
        this._checkMantriYoga();
        this._checkSenapatiYoga();
        this._checkVanijaYoga();
        this._checkChikitsakaYoga();
        this._checkNyayaYoga();
        this._checkKarmaAdhipatiYoga();
    }

    /**
     * Rajya Yoga (Government position)
     * Sun strong with connections to 10th house
     */
    _checkRajyaYoga() {
        const sunHouse = this.getHouse('Sun');
        const sunStrong = this.isStrong('Sun') ||
            ['Exalted', 'Moolatrikona'].includes(this.getDignity('Sun'));
        const lord10 = this.getHouseLord(10);

        // Sun in 10th or 1st with dignity
        if ([1, 10].includes(sunHouse) && sunStrong) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Rajya.name'),
                nameKey: 'Rajya',
                category: 'Career',
                description: I18n.t('lists.yoga_list.Rajya.effects'),
                descriptionKey: 'Rajya',
                planets: ['Sun'],
                nature: 'Benefic',
                strength: this.getStrength(['Sun']) + 2
            }));
        }

        // Sun connected with 10th lord
        if (this.isConjunct('Sun', lord10) && sunStrong) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Rajya_10L.name'),
                nameKey: 'Rajya_10L',
                category: 'Career',
                description: I18n.t('lists.yoga_list.Rajya_10L.effects'),
                descriptionKey: 'Rajya_10L',
                planets: ['Sun', lord10],
                nature: 'Benefic',
                strength: this.getStrength(['Sun', lord10])
            }));
        }
    }

    /**
     * Amatya Yoga (Minister/Advisor)
     * Mercury strong in Kendra with 10th connection
     */
    _checkAmatyaYoga() {
        const mercHouse = this.getHouse('Mercury');
        const mercStrong = this.isStrong('Mercury') ||
            ['Exalted', 'Own', 'Moolatrikona'].includes(this.getDignity('Mercury'));
        const lord10 = this.getHouseLord(10);

        // Mercury in Kendra
        if (kendras.includes(mercHouse) && mercStrong) {
            // Connection with 10th house/lord
            const aspectsLord10 = this.aspects('Mercury', lord10);
            const conjunctLord10 = this.isConjunct('Mercury', lord10);
            const in10th = mercHouse === 10;

            if (in10th || aspectsLord10 || conjunctLord10) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Amatya.name'),
                    nameKey: 'Amatya',
                    category: 'Career',
                    description: I18n.t('lists.yoga_list.Amatya.effects'),
                    descriptionKey: 'Amatya',
                    planets: ['Mercury', lord10],
                    nature: 'Benefic',
                    strength: this.getStrength(['Mercury']) + 1
                }));
            }
        }
    }

    /**
     * Mantri Yoga (Counselor)
     * Jupiter in 1st, 4th, or 10th with Moon aspect
     */
    _checkMantriYoga() {
        const jupHouse = this.getHouse('Jupiter');
        const moonAspectsJup = this.aspects('Moon', 'Jupiter');
        const moonConjJup = this.isConjunct('Moon', 'Jupiter');

        if ([1, 4, 10].includes(jupHouse) && (moonAspectsJup || moonConjJup)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Mantri.name'),
                nameKey: 'Mantri',
                category: 'Career',
                description: I18n.t('lists.yoga_list.Mantri.effects'),
                descriptionKey: 'Mantri',
                planets: ['Jupiter', 'Moon'],
                nature: 'Benefic',
                strength: this.getStrength(['Jupiter', 'Moon'])
            }));
        }
    }

    /**
     * Senapati Yoga (Military commander)
     * Mars strong in 1st, 10th, or 3rd with Sun
     */
    _checkSenapatiYoga() {
        const marsHouse = this.getHouse('Mars');
        const marsStrong = this.isStrong('Mars') ||
            ['Exalted', 'Own', 'Moolatrikona'].includes(this.getDignity('Mars'));

        // Mars in commanding houses
        const commandHouses = [1, 3, 10];

        if (commandHouses.includes(marsHouse) && marsStrong) {
            // Sun connection enhances
            const sunConjMars = this.isConjunct('Sun', 'Mars');
            const sunAspectsMars = this.aspects('Sun', 'Mars');

            if (sunConjMars || sunAspectsMars) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Senapati.name'),
                    nameKey: 'Senapati',
                    category: 'Career',
                    description: I18n.t('lists.yoga_list.Senapati.effects'),
                    descriptionKey: 'Senapati',
                    planets: ['Mars', 'Sun'],
                    nature: 'Benefic',
                    strength: this.getStrength(['Mars', 'Sun']) + 1
                }));
            } else {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Parakrama_Career.name'),
                    nameKey: 'Parakrama_Career',
                    category: 'Career',
                    description: I18n.t('lists.yoga_list.Parakrama_Career.effects'),
                    descriptionKey: 'Parakrama_Career',
                    planets: ['Mars'],
                    nature: 'Benefic',
                    strength: this.getStrength(['Mars'])
                }));
            }
        }
    }

    /**
     * Vanija Yoga (Business success)
     * Mercury-Jupiter connection with 2nd, 7th, 10th, 11th
     */
    _checkVanijaYoga() {
        const mercHouse = this.getHouse('Mercury');
        const jupHouse = this.getHouse('Jupiter');
        const venusHouse = this.getHouse('Venus');

        const businessHouses = [2, 7, 10, 11];

        // Mercury-Jupiter connection in business houses
        const mercJupConnected = this.isConjunct('Mercury', 'Jupiter') ||
            this.aspects('Mercury', 'Jupiter');

        const inBusinessHouse = businessHouses.includes(mercHouse) ||
            businessHouses.includes(jupHouse);

        if (mercJupConnected && inBusinessHouse) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vanija.name'),
                nameKey: 'Vanija',
                category: 'Career',
                description: I18n.t('lists.yoga_list.Vanija.effects'),
                descriptionKey: 'Vanija',
                planets: ['Mercury', 'Jupiter'],
                nature: 'Benefic',
                strength: this.getStrength(['Mercury', 'Jupiter'])
            }));
        }

        // Alternative: Venus in 7th or 10th strong (luxury business)
        if ([7, 10].includes(venusHouse) && this.isStrong('Venus')) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vanija_Luxury.name'),
                nameKey: 'Vanija_Luxury',
                category: 'Career',
                description: I18n.t('lists.yoga_list.Vanija_Luxury.effects'),
                descriptionKey: 'Vanija_Luxury',
                planets: ['Venus'],
                nature: 'Benefic',
                strength: this.getStrength(['Venus'])
            }));
        }
    }

    /**
     * Chikitsaka Yoga (Medical profession)
     * Sun-Mars or Ketu involvement with 6th, 8th, 12th lords
     */
    _checkChikitsakaYoga() {
        // Sun-Mars conjunction (surgery)
        const sunMarsConj = this.isConjunct('Sun', 'Mars');

        // Ketu (healing, alternative medicine) in 6th or 12th
        const ketuHouse = this.getHouse('Ketu');
        const ketuIn6or12 = [6, 12].includes(ketuHouse);

        // Connection to health houses
        const sunHouse = this.getHouse('Sun');
        const marsHouse = this.getHouse('Mars');
        const healthHouses = [6, 8, 12];

        if (sunMarsConj && (healthHouses.includes(sunHouse) || healthHouses.includes(marsHouse))) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Chikitsaka_Surgery.name'),
                nameKey: 'Chikitsaka_Surgery',
                category: 'Career',
                description: I18n.t('lists.yoga_list.Chikitsaka_Surgery.effects'),
                descriptionKey: 'Chikitsaka_Surgery',
                planets: ['Sun', 'Mars'],
                nature: 'Benefic',
                strength: this.getStrength(['Sun', 'Mars'])
            }));
        }

        if (ketuIn6or12 && this.isStrong('Jupiter')) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Chikitsaka_Healing.name'),
                nameKey: 'Chikitsaka_Healing',
                category: 'Career',
                description: I18n.t('lists.yoga_list.Chikitsaka_Healing.effects'),
                descriptionKey: 'Chikitsaka_Healing',
                planets: ['Ketu', 'Jupiter'],
                nature: 'Benefic',
                strength: 6
            }));
        }

        // Moon-Venus for nursing/care
        if (this.isConjunct('Moon', 'Venus') && [6, 12].includes(this.getHouse('Moon'))) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Chikitsaka_Care.name'),
                nameKey: 'Chikitsaka_Care',
                category: 'Career',
                description: I18n.t('lists.yoga_list.Chikitsaka_Care.effects'),
                descriptionKey: 'Chikitsaka_Care',
                planets: ['Moon', 'Venus'],
                nature: 'Benefic',
                strength: this.getStrength(['Moon', 'Venus'])
            }));
        }
    }

    /**
     * Nyaya Yoga (Legal profession)
     * Jupiter strong in 1st, 9th, or 10th with Sun aspect
     */
    _checkNyayaYoga() {
        const jupHouse = this.getHouse('Jupiter');
        const jupStrong = this.isStrong('Jupiter') ||
            ['Exalted', 'Own', 'Moolatrikona'].includes(this.getDignity('Jupiter'));

        const legalHouses = [1, 9, 10];
        const sunAspectsJup = this.aspects('Sun', 'Jupiter');
        const sunConjJup = this.isConjunct('Sun', 'Jupiter');

        if (legalHouses.includes(jupHouse) && jupStrong && (sunAspectsJup || sunConjJup)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Nyaya.name'),
                nameKey: 'Nyaya',
                category: 'Career',
                description: I18n.t('lists.yoga_list.Nyaya.effects'),
                descriptionKey: 'Nyaya',
                planets: ['Jupiter', 'Sun'],
                nature: 'Benefic',
                strength: this.getStrength(['Jupiter', 'Sun']) + 1
            }));
        }

        // Alternative: Saturn-Jupiter for law (structure + justice)
        const satConjJup = this.isConjunct('Saturn', 'Jupiter');
        if (satConjJup && [9, 10].includes(jupHouse)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Nyaya_SJ.name'),
                nameKey: 'Nyaya_SJ',
                category: 'Career',
                description: I18n.t('lists.yoga_list.Nyaya_SJ.effects'),
                descriptionKey: 'Nyaya_SJ',
                planets: ['Saturn', 'Jupiter'],
                nature: 'Benefic',
                strength: this.getStrength(['Saturn', 'Jupiter'])
            }));
        }
    }

    /**
     * Karma Adhipati Yoga (Career mastery)
     * 10th house and lord combinations
     */
    _checkKarmaAdhipatiYoga() {
        const lord10 = this.getHouseLord(10);
        const lord10House = this.getHouse(lord10);
        const lord10Dignity = this.getDignity(lord10);
        const planetsIn10 = this.getPlanetsInHouse(10);

        let careerFactors = 0;

        // 10th lord in Kendra/Trikona
        if ([...kendras, ...trikonas].includes(lord10House)) careerFactors++;
        // 10th lord in dignity
        if (['Exalted', 'Own', 'Moolatrikona'].includes(lord10Dignity)) careerFactors++;
        // Benefics in 10th
        const beneficsIn10 = planetsIn10.filter(p => this.getNaturalBenefics().includes(p));
        if (beneficsIn10.length > 0) careerFactors++;
        // Saturn in 10th or aspecting 10th (discipline)
        const satHouse = this.getHouse('Saturn');
        if (satHouse === 10 || this._aspectsHouse('Saturn', satHouse, 10)) careerFactors++;
        // Sun in 10th (authority)
        if (planetsIn10.includes('Sun') && this.getDignity('Sun') !== 'Debilitated') careerFactors++;

        if (careerFactors >= 3) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Karma_Adhipati.name'),
                nameKey: 'Karma_Adhipati',
                category: 'Career',
                description: I18n.t('lists.yoga_list.Karma_Adhipati.effects'),
                descriptionKey: 'Karma_Adhipati',
                planets: planetsIn10.length > 0 ? planetsIn10 : [lord10],
                nature: 'Benefic',
                strength: 5 + careerFactors
            }));
        }
    }

    /**
     * Helper to check house aspect
     */
    _aspectsHouse(planet, planetHouse, targetHouse) {
        const aspects = {
            'Sun': [7], 'Moon': [7], 'Mercury': [7], 'Venus': [7],
            'Mars': [4, 7, 8], 'Jupiter': [5, 7, 9], 'Saturn': [3, 7, 10],
            'Rahu': [5, 7, 9], 'Ketu': [5, 7, 9]
        };

        const planetAspects = aspects[planet] || [7];
        for (const asp of planetAspects) {
            if (((planetHouse - 1 + asp) % 12) + 1 === targetHouse) return true;
        }
        return false;
    }
}

export default CareerYogas;
