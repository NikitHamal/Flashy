/**
 * Education/Knowledge Yogas Module
 * Implements learning, intellect, and artistic talent yogas
 */

import I18n from '../../core/i18n.js';
import { YogaModuleBase, createYoga, kendras, trikonas } from './base.js';

export class EducationYogas extends YogaModuleBase {
    check() {
        this._checkSaraswatiFullYoga();
        this._checkVidyaYoga();
        this._checkKalaYoga();
        this._checkSangeethaYoga();
        this._checkKavyaYoga();
        this._checkBhashyaYoga();
        this._checkNipunaYoga();
        this._checkShilpiYoga();
        this._checkMantraSiddhiYoga();
    }

    /**
     * Saraswati Yoga (Full version)
     * Jupiter, Venus, Mercury in Kendras/Trikonas/2nd + Jupiter in dignity
     */
    _checkSaraswatiFullYoga() {
        const goodHouses = [...kendras, ...trikonas, 2];

        const jupHouse = this.getHouse('Jupiter');
        const venHouse = this.getHouse('Venus');
        const merHouse = this.getHouse('Mercury');

        const jupDig = this.getDignity('Jupiter');
        const jupInDignity = ['Exalted', 'Own', 'Moolatrikona'].includes(jupDig);

        const allInGoodHouses = goodHouses.includes(jupHouse) &&
            goodHouses.includes(venHouse) &&
            goodHouses.includes(merHouse);

        if (allInGoodHouses && jupInDignity) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Saraswati_Full.name'),
                nameKey: 'Saraswati_Full',
                category: 'Education',
                description: I18n.t('lists.yoga_list.Saraswati_Full.effects'),
                descriptionKey: 'Saraswati_Full',
                planets: ['Jupiter', 'Venus', 'Mercury'],
                nature: 'Benefic',
                strength: 9
            }));
        } else if (allInGoodHouses) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Saraswati_Partial.name'),
                nameKey: 'Saraswati_Partial',
                category: 'Education',
                description: I18n.t('lists.yoga_list.Saraswati_Partial.effects'),
                descriptionKey: 'Saraswati_Partial',
                planets: ['Jupiter', 'Venus', 'Mercury'],
                nature: 'Benefic',
                strength: 6
            }));
        }
    }

    /**
     * Vidya Yoga (Learning)
     * 5th lord strong with Mercury
     */
    _checkVidyaYoga() {
        const lord5 = this.getHouseLord(5);
        const lord5Strong = this.isStrong(lord5) ||
            ['Exalted', 'Own', 'Moolatrikona'].includes(this.getDignity(lord5));

        const mercuryConnected = this.isConjunct(lord5, 'Mercury') ||
            this.aspects('Mercury', lord5) ||
            this.aspects(lord5, 'Mercury');

        if (lord5Strong && mercuryConnected) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vidya.name'),
                nameKey: 'Vidya',
                category: 'Education',
                description: I18n.t('lists.yoga_list.Vidya.effects'),
                descriptionKey: 'Vidya',
                planets: [lord5, 'Mercury'],
                nature: 'Benefic',
                strength: this.getStrength([lord5, 'Mercury'])
            }));
        }
    }

    /**
     * Kala Yoga (Artistic ability)
     * Venus strong in 2nd, 3rd, or 5th
     */
    _checkKalaYoga() {
        const venusHouse = this.getHouse('Venus');
        const venusStrong = this.isStrong('Venus') ||
            ['Exalted', 'Own', 'Moolatrikona'].includes(this.getDignity('Venus'));

        const artHouses = [2, 3, 5];

        if (artHouses.includes(venusHouse) && venusStrong && !this.isCombust('Venus')) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Kala.name'),
                nameKey: 'Kala',
                category: 'Education',
                description: I18n.t('lists.yoga_list.Kala.effects'),
                descriptionKey: 'Kala',
                planets: ['Venus'],
                nature: 'Benefic',
                strength: this.getStrength(['Venus']) + 1,
                params: { house: venusHouse }
            }));
        }
    }

    /**
     * Sangeetha Yoga (Musical talent)
     * Venus-Moon connection with 2nd/3rd house
     */
    _checkSangeethaYoga() {
        const venusHouse = this.getHouse('Venus');
        const moonHouse = this.getHouse('Moon');

        const connected = this.isConjunct('Venus', 'Moon') ||
            this.aspects('Venus', 'Moon') ||
            this.aspects('Moon', 'Venus');

        const musicHouses = [2, 3, 5];
        const inMusicHouse = musicHouses.includes(venusHouse) || musicHouses.includes(moonHouse);

        if (connected && inMusicHouse) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Sangeetha.name'),
                nameKey: 'Sangeetha',
                category: 'Education',
                description: I18n.t('lists.yoga_list.Sangeetha.effects'),
                descriptionKey: 'Sangeetha',
                planets: ['Venus', 'Moon'],
                nature: 'Benefic',
                strength: this.getStrength(['Venus', 'Moon'])
            }));
        }

        const mercVenConjunct = this.isConjunct('Mercury', 'Venus');
        const mercHouse = this.getHouse('Mercury');
        if (mercVenConjunct && [2, 3].includes(mercHouse)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Sangeetha_MV.name'),
                nameKey: 'Sangeetha_MV',
                category: 'Education',
                description: I18n.t('lists.yoga_list.Sangeetha_MV.effects'),
                descriptionKey: 'Sangeetha_MV',
                planets: ['Mercury', 'Venus'],
                nature: 'Benefic',
                strength: this.getStrength(['Mercury', 'Venus'])
            }));
        }
    }

    /**
     * Kavya Yoga (Poetic ability)
     * Mercury-Jupiter-Venus connection with 2nd/5th
     */
    _checkKavyaYoga() {
        const mercHouse = this.getHouse('Mercury');
        const jupHouse = this.getHouse('Jupiter');

        const mercJupConnected = this.isConjunct('Mercury', 'Jupiter') ||
            this.aspects('Mercury', 'Jupiter') ||
            this.aspects('Jupiter', 'Mercury');

        const expressionHouses = [2, 3, 5];
        const inExpressionHouse = expressionHouses.includes(mercHouse) ||
            expressionHouses.includes(jupHouse);

        if (mercJupConnected && inExpressionHouse) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Kavya.name'),
                nameKey: 'Kavya',
                category: 'Education',
                description: I18n.t('lists.yoga_list.Kavya.effects'),
                descriptionKey: 'Kavya',
                planets: ['Mercury', 'Jupiter'],
                nature: 'Benefic',
                strength: this.getStrength(['Mercury', 'Jupiter'])
            }));
        }
    }

    /**
     * Bhashya Yoga (Linguistic talent)
     * Strong Mercury in 2nd or 3rd with Jupiter aspect
     */
    _checkBhashyaYoga() {
        const mercHouse = this.getHouse('Mercury');
        const mercStrong = this.isStrong('Mercury') ||
            ['Exalted', 'Own', 'Moolatrikona'].includes(this.getDignity('Mercury'));

        const jupAspectsMerc = this.aspects('Jupiter', 'Mercury');

        if ([2, 3].includes(mercHouse) && mercStrong) {
            if (jupAspectsMerc) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Bhashya.name'),
                    nameKey: 'Bhashya',
                    category: 'Education',
                    description: I18n.t('lists.yoga_list.Bhashya.effects'),
                    descriptionKey: 'Bhashya',
                    planets: ['Mercury', 'Jupiter'],
                    nature: 'Benefic',
                    strength: 8
                }));
            } else {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Vakya.name'),
                    nameKey: 'Vakya',
                    category: 'Education',
                    description: I18n.t('lists.yoga_list.Vakya.effects'),
                    descriptionKey: 'Vakya',
                    planets: ['Mercury'],
                    nature: 'Benefic',
                    strength: 6
                }));
            }
        }
    }

    /**
     * Nipuna Yoga (Technical expertise)
     * Mercury-Mars connection with 3rd or 10th
     */
    _checkNipunaYoga() {
        const mercHouse = this.getHouse('Mercury');
        const marsHouse = this.getHouse('Mars');

        const connected = this.isConjunct('Mercury', 'Mars') ||
            this.aspects('Mercury', 'Mars') ||
            this.aspects('Mars', 'Mercury');

        const technicalHouses = [3, 6, 10];
        const inTechHouse = technicalHouses.includes(mercHouse) ||
            technicalHouses.includes(marsHouse);

        if (connected && inTechHouse) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Nipuna.name'),
                nameKey: 'Nipuna',
                category: 'Education',
                description: I18n.t('lists.yoga_list.Nipuna.effects'),
                descriptionKey: 'Nipuna',
                planets: ['Mercury', 'Mars'],
                nature: 'Benefic',
                strength: this.getStrength(['Mercury', 'Mars'])
            }));
        }

        if (this.isConjunct('Mercury', 'Rahu') && technicalHouses.includes(mercHouse)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Nipuna_Modern.name'),
                nameKey: 'Nipuna_Modern',
                category: 'Education',
                description: I18n.t('lists.yoga_list.Nipuna_Modern.effects'),
                descriptionKey: 'Nipuna_Modern',
                planets: ['Mercury', 'Rahu'],
                nature: 'Benefic',
                strength: 6
            }));
        }
    }

    /**
     * Shilpi Yoga (Craftsmanship)
     * Venus-Mars connection with 3rd house
     */
    _checkShilpiYoga() {
        const venusHouse = this.getHouse('Venus');
        const marsHouse = this.getHouse('Mars');

        const connected = this.isConjunct('Venus', 'Mars') ||
            this.aspects('Venus', 'Mars') ||
            this.aspects('Mars', 'Venus');

        const in3rd = venusHouse === 3 || marsHouse === 3;
        const aspects3rd = this._aspectsHouse('Venus', venusHouse, 3) ||
            this._aspectsHouse('Mars', marsHouse, 3);

        if (connected && (in3rd || aspects3rd)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Shilpi.name'),
                nameKey: 'Shilpi',
                category: 'Education',
                description: I18n.t('lists.yoga_list.Shilpi.effects'),
                descriptionKey: 'Shilpi',
                planets: ['Venus', 'Mars'],
                nature: 'Benefic',
                strength: this.getStrength(['Venus', 'Mars'])
            }));
        }
    }

    /**
     * Helper to check planet aspect on house
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

    /**
     * Mantra Siddhi Yoga (Spiritual practice mastery)
     * Jupiter-Ketu connection with 5th, 9th, or 12th
     */
    _checkMantraSiddhiYoga() {
        const jupHouse = this.getHouse('Jupiter');
        const ketuHouse = this.getHouse('Ketu');

        const connected = this.isConjunct('Jupiter', 'Ketu') ||
            this.aspects('Jupiter', 'Ketu') ||
            this.aspects('Ketu', 'Jupiter');

        const spiritualHouses = [5, 9, 12];
        const inSpiritualHouse = spiritualHouses.includes(jupHouse) ||
            spiritualHouses.includes(ketuHouse);

        if (connected && inSpiritualHouse) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Mantra_Siddhi.name'),
                nameKey: 'Mantra_Siddhi',
                category: 'Education',
                description: I18n.t('lists.yoga_list.Mantra_Siddhi.effects'),
                descriptionKey: 'Mantra_Siddhi',
                planets: ['Jupiter', 'Ketu'],
                nature: 'Benefic',
                strength: 7
            }));
        }

        if (this.isConjunct('Moon', 'Jupiter') && spiritualHouses.includes(jupHouse)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Guru_Siddhi.name'),
                nameKey: 'Guru_Siddhi',
                category: 'Education',
                description: I18n.t('lists.yoga_list.Guru_Siddhi.effects'),
                descriptionKey: 'Guru_Siddhi',
                planets: ['Moon', 'Jupiter'],
                nature: 'Benefic',
                strength: 7
            }));
        }
    }
}

export default EducationYogas;
