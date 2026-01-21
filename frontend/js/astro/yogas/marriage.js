/**
 * Marriage/Relationship Yogas Module
 * Implements marriage timing, quality, and compatibility yogas
 */

import I18n from '../../core/i18n.js';
import { YogaModuleBase, createYoga, kendras, trikonas, dusthanas } from './base.js';

export class MarriageYogas extends YogaModuleBase {
    check() {
        this._checkKalatraYoga();
        this._checkVivahaYoga();
        this._checkVishakanyaYoga();
        this._checkGanaYogas();
        this._checkWidowYoga();
        this._checkBahuVivahaYoga();
        this._checkVivahaNashakYoga();
        this._checkJaraYoga();
        this._checkKalatradoshaYoga();
        this._checkSundariYoga();
    }

    /**
     * Kalatra Yoga
     * 7th lord strong in Kendra/Trikona
     */
    _checkKalatraYoga() {
        const lord7 = this.getHouseLord(7);
        const lord7House = this.getHouse(lord7);
        const lord7Strong = this.isStrong(lord7);
        const lord7Dignity = this.getDignity(lord7);

        const goodHouses = [...kendras, ...trikonas];
        const inGoodDignity = ['Exalted', 'Own', 'Moolatrikona'].includes(lord7Dignity);

        if (goodHouses.includes(lord7House) && (lord7Strong || inGoodDignity)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Kalatra.name'),
                nameKey: 'Kalatra',
                category: 'Marriage',
                description: I18n.t('lists.yoga_list.Kalatra.effects'),
                descriptionKey: 'Kalatra',
                planets: [lord7],
                nature: 'Benefic',
                strength: this.getStrength([lord7]) + 2
            }));
        }
    }

    /**
     * Vivaha Yoga
     * Venus-Jupiter connection with 7th house
     */
    _checkVivahaYoga() {
        const venusHouse = this.getHouse('Venus');
        const jupiterHouse = this.getHouse('Jupiter');

        // Venus in 7th
        if (venusHouse === 7 && !this.isCombust('Venus')) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vivaha.name'),
                nameKey: 'Vivaha',
                category: 'Marriage',
                description: I18n.t('lists.yoga_list.Vivaha.effects'),
                descriptionKey: 'Vivaha',
                planets: ['Venus'],
                nature: 'Benefic',
                strength: 7
            }));
        }

        // Jupiter aspects 7th or Venus
        const jupiterAspects7 = this._aspectsHouse('Jupiter', jupiterHouse, 7);
        const jupiterAspectsVenus = this.aspects('Jupiter', 'Venus');

        if (jupiterAspects7 || (jupiterAspectsVenus && venusHouse === 7)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vivaha_Jupiter.name'),
                nameKey: 'Vivaha_Jupiter',
                category: 'Marriage',
                description: I18n.t('lists.yoga_list.Vivaha_Jupiter.effects'),
                descriptionKey: 'Vivaha_Jupiter',
                planets: ['Jupiter', 'Venus'],
                nature: 'Benefic',
                strength: 7
            }));
        }

        // Venus-Jupiter conjunction
        if (this.isConjunct('Venus', 'Jupiter')) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vivaha_VJ.name'),
                nameKey: 'Vivaha_VJ',
                category: 'Marriage',
                description: I18n.t('lists.yoga_list.Vivaha_VJ.effects'),
                descriptionKey: 'Vivaha_VJ',
                planets: ['Venus', 'Jupiter'],
                nature: 'Benefic',
                strength: 8
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

    /**
     * Vishakanya Yoga (Poison Maiden)
     * Venus-Moon-Saturn specific positions
     */
    _checkVishakanyaYoga() {
        const venusSign = this.getRasi('Venus');
        const moonSign = this.getRasi('Moon');
        const saturnSign = this.getRasi('Saturn');

        const isMovable = (sign) => [0, 3, 6, 9].includes(sign);
        const isFixed = (sign) => [1, 4, 7, 10].includes(sign);
        const isDual = (sign) => [2, 5, 8, 11].includes(sign);

        const condition1 = isMovable(venusSign) && isFixed(moonSign) && isDual(saturnSign);
        const condition2 = this.isConjunct('Venus', 'Saturn') && this.getHouse('Venus') === 7;

        if (condition1) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vishakanya.name'),
                nameKey: 'Vishakanya',
                category: 'Marriage',
                description: I18n.t('lists.yoga_list.Vishakanya.effects'),
                descriptionKey: 'Vishakanya',
                planets: ['Venus', 'Moon', 'Saturn'],
                nature: 'Malefic',
                strength: 3
            }));
        } else if (condition2) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vishakanya_Variant.name'),
                nameKey: 'Vishakanya_Variant',
                category: 'Marriage',
                description: I18n.t('lists.yoga_list.Vishakanya_Variant.effects'),
                descriptionKey: 'Vishakanya_Variant',
                planets: ['Venus', 'Saturn'],
                nature: 'Neutral',
                strength: 4
            }));
        }
    }

    /**
     * Gana Yogas (Temperament matching)
     * Deva, Manushya, Rakshasa classifications
     */
    _checkGanaYogas() {
        const moonNak = this._getMoonNakshatra();
        if (moonNak === -1) return;

        // Nakshatra to Gana mapping
        const ganaMap = {
            deva: [0, 4, 6, 8, 12, 14, 16, 20, 26],
            manushya: [1, 3, 5, 10, 11, 13, 17, 21, 25],
            rakshasa: [2, 7, 9, 15, 18, 19, 22, 23, 24]
        };

        let gana = 'Unknown';
        if (ganaMap.deva.includes(moonNak)) gana = 'Deva';
        else if (ganaMap.manushya.includes(moonNak)) gana = 'Manushya';
        else if (ganaMap.rakshasa.includes(moonNak)) gana = 'Rakshasa';

        if (gana !== 'Unknown') {
            const key = `${gana}_Gana`;
            this.addYoga(createYoga({
                name: I18n.t(`lists.yoga_list.${key}.name`),
                nameKey: key,
                category: 'Marriage',
                description: I18n.t(`lists.yoga_list.${key}.effects`),
                descriptionKey: key,
                planets: ['Moon'],
                nature: 'Neutral',
                strength: 5
            }));
        }
    }

    /**
     * Get Moon's nakshatra index (0-26)
     */
    _getMoonNakshatra() {
        const moonLon = this.getLongitude('Moon');
        if (isNaN(moonLon)) return -1;
        return Math.floor(moonLon / (360 / 27));
    }

    /**
     * Widow/Widower Yoga
     * 7th lord afflicted, Mars in 7th or 8th
     */
    _checkWidowYoga() {
        const lord7 = this.getHouseLord(7);
        const lord7House = this.getHouse(lord7);
        const marsHouse = this.getHouse('Mars');

        const malefics = this.getNaturalMalefics();
        const lord7Afflicted = dusthanas.includes(lord7House) ||
            this.getDignity(lord7) === 'Debilitated' ||
            malefics.some(m => this.isConjunct(lord7, m));

        const marsIn7or8 = [7, 8].includes(marsHouse);

        if (lord7Afflicted && marsIn7or8) {
            // Check for saving graces
            const jupiterAspects7 = this._aspectsHouse('Jupiter', this.getHouse('Jupiter'), 7);
            const venusStrong = this.isStrong('Venus');

            if (jupiterAspects7 || venusStrong) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Vaidhavya_Bhanga.name'),
                    nameKey: 'Vaidhavya_Bhanga',
                    category: 'Marriage',
                    description: I18n.t('lists.yoga_list.Vaidhavya_Bhanga.effects'),
                    descriptionKey: 'Vaidhavya_Bhanga',
                    planets: [lord7, 'Mars', 'Jupiter'],
                    nature: 'Neutral',
                    strength: 5
                }));
            } else {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Vaidhavya.name'),
                    nameKey: 'Vaidhavya',
                    category: 'Marriage',
                    description: I18n.t('lists.yoga_list.Vaidhavya.effects'),
                    descriptionKey: 'Vaidhavya',
                    planets: [lord7, 'Mars'],
                    nature: 'Malefic',
                    strength: 3
                }));
            }
        }
    }

    /**
     * Bahu Vivaha Yoga
     * Multiple marriages indicators
     */
    _checkBahuVivahaYoga() {
        const planetsIn7 = this.getPlanetsInHouse(7);
        const lord7 = this.getHouseLord(7);
        const venusSign = this.getRasi('Venus');

        let multipleIndicators = 0;

        // Multiple planets in 7th
        if (planetsIn7.length >= 2) multipleIndicators++;
        // 7th lord in dual sign
        const isDual = (sign) => [2, 5, 8, 11].includes(sign);
        if (isDual(this.getRasi(lord7))) multipleIndicators++;
        // Venus in dual sign
        if (isDual(venusSign)) multipleIndicators++;
        // Mars and Venus together
        if (this.isConjunct('Mars', 'Venus')) multipleIndicators++;
        // Rahu in 7th
        if (this.getHouse('Rahu') === 7) multipleIndicators++;

        if (multipleIndicators >= 2) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Bahu_Vivaha.name'),
                nameKey: 'Bahu_Vivaha',
                category: 'Marriage',
                description: I18n.t('lists.yoga_list.Bahu_Vivaha.effects'),
                descriptionKey: 'Bahu_Vivaha',
                planets: planetsIn7.length > 0 ? planetsIn7 : ['Venus', lord7],
                nature: 'Neutral',
                strength: 4
            }));
        }
    }

    /**
     * Vivaha Nashak Yoga
     * Denial of marriage
     */
    _checkVivahaNashakYoga() {
        const lord7 = this.getHouseLord(7);
        const planetsIn7 = this.getPlanetsInHouse(7);

        let denialFactors = 0;

        // Saturn in 7th without benefic aspect
        if (planetsIn7.includes('Saturn')) {
            const beneficAspects = this.getNaturalBenefics().some(b => this._aspectsHouse(b, this.getHouse(b), 7));
            if (!beneficAspects) denialFactors++;
        }

        // Ketu in 7th
        if (this.getHouse('Ketu') === 7) denialFactors++;
        // 7th lord in 12th
        if (this.getHouse(lord7) === 12) denialFactors++;
        // Venus combust and debilitated
        if (this.isCombust('Venus') && this.getDignity('Venus') === 'Debilitated') denialFactors++;

        if (denialFactors >= 2) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vivaha_Nashak.name'),
                nameKey: 'Vivaha_Nashak',
                category: 'Marriage',
                description: I18n.t('lists.yoga_list.Vivaha_Nashak.effects'),
                descriptionKey: 'Vivaha_Nashak',
                planets: [lord7, 'Venus'],
                nature: 'Malefic',
                strength: 3
            }));
        }
    }

    /**
     * Jara Yoga
     * Late marriage
     */
    _checkJaraYoga() {
        const saturnHouse = this.getHouse('Saturn');
        const lord7 = this.getHouseLord(7);
        const venusHouse = this.getHouse('Venus');

        let delayFactors = 0;

        if (saturnHouse === 7) delayFactors++;
        if (this._aspectsHouse('Saturn', saturnHouse, 7)) delayFactors++;
        if (this.aspects('Saturn', 'Venus')) delayFactors++;
        if (this.isConjunct(lord7, 'Saturn')) delayFactors++;
        if (venusHouse === 12) delayFactors++;

        if (delayFactors >= 2) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Jara.name'),
                nameKey: 'Jara',
                category: 'Marriage',
                description: I18n.t('lists.yoga_list.Jara.effects'),
                descriptionKey: 'Jara',
                planets: ['Saturn', lord7],
                nature: 'Neutral',
                strength: 4
            }));
        }
    }

    /**
     * Kalatra Dosha
     * General spouse affliction
     */
    _checkKalatradoshaYoga() {
        const planetsIn7 = this.getPlanetsInHouse(7);
        const malefics = this.getNaturalMalefics();

        const onlyMaleficsIn7 = planetsIn7.length > 0 &&
            planetsIn7.every(p => malefics.includes(p));

        const beneficAspects7 = this.getNaturalBenefics().some(b =>
            this._aspectsHouse(b, this.getHouse(b), 7)
        );

        if (onlyMaleficsIn7 && !beneficAspects7) {
            const planetNames = planetsIn7.map(p => I18n.t('planets.' + p)).join(', ');
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Kalatra_Dosha.name'),
                nameKey: 'Kalatra_Dosha',
                category: 'Marriage',
                description: I18n.t('lists.yoga_list.Kalatra_Dosha.effects', { planets: planetNames }),
                descriptionKey: 'Kalatra_Dosha',
                planets: planetsIn7,
                nature: 'Malefic',
                strength: 3,
                params: { planets: planetsIn7.join(', ') }
            }));
        }
    }

    /**
     * Sundari Yoga (Beautiful spouse)
     * Venus strong in 7th or aspecting 7th
     */
    _checkSundariYoga() {
        const venusHouse = this.getHouse('Venus');
        const venusDig = this.getDignity('Venus');
        const venusStrong = this.isStrong('Venus') || ['Exalted', 'Own'].includes(venusDig);

        if (venusHouse === 7 && venusStrong && !this.isCombust('Venus')) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Sundari.name'),
                nameKey: 'Sundari',
                category: 'Marriage',
                description: I18n.t('lists.yoga_list.Sundari.effects'),
                descriptionKey: 'Sundari',
                planets: ['Venus'],
                nature: 'Benefic',
                strength: this.getStrength(['Venus']) + 1
            }));
        }
    }
}

export default MarriageYogas;
