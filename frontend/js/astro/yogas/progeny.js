/**
 * Progeny (Putra) Yogas Module
 * Implements children-related yogas
 */

import I18n from '../../core/i18n.js';
import { YogaModuleBase, createYoga, kendras, trikonas, dusthanas } from './base.js';

export class ProgenyYogas extends YogaModuleBase {
    check() {
        this._checkPutraYoga();
        this._checkSantanaYoga();
        this._checkAputraYoga();
        this._checkBahusantanaYoga();
        this._checkEkaputraYoga();
        this._checkDattakaYoga();
        this._checkPutraShokaYoga();
    }

    /**
     * Putra Yoga (Children blessing)
     * 5th lord strong, Jupiter aspects
     */
    _checkPutraYoga() {
        const lord5 = this.getHouseLord(5);
        const lord5Strong = this.isStrong(lord5) ||
            ['Exalted', 'Own', 'Moolatrikona'].includes(this.getDignity(lord5));

        const jupiterAspects5 = this._aspectsHouse('Jupiter', this.getHouse('Jupiter'), 5);
        const jupiterAspectsLord5 = this.aspects('Jupiter', lord5);

        if (lord5Strong && (jupiterAspects5 || jupiterAspectsLord5)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Putra.name'),
                nameKey: 'Putra',
                category: 'Progeny',
                description: I18n.t('lists.yoga_list.Putra.effects'),
                descriptionKey: 'Putra',
                planets: [lord5, 'Jupiter'],
                nature: 'Benefic',
                strength: this.getStrength([lord5, 'Jupiter'])
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
     * Santana Yoga
     * Multiple children blessing yogas
     */
    _checkSantanaYoga() {
        const lord5 = this.getHouseLord(5);
        const planetsIn5 = this.getPlanetsInHouse(5);
        const benefics = this.getNaturalBenefics();

        const beneficsIn5 = planetsIn5.filter(p => benefics.includes(p));
        const jupiterIn5 = this.getHouse('Jupiter') === 5;
        const lord5House = this.getHouse(lord5);
        const lord5InGoodHouse = [...kendras, ...trikonas].includes(lord5House);
        const venusStrong = this.isStrong('Venus');
        const moonWaxing = this.isWaxingMoon();

        let santanaFactors = 0;
        if (beneficsIn5.length > 0) santanaFactors++;
        if (jupiterIn5) santanaFactors++;
        if (lord5InGoodHouse) santanaFactors++;
        if (venusStrong && moonWaxing) santanaFactors++;

        if (santanaFactors >= 2) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Santana.name'),
                nameKey: 'Santana',
                category: 'Progeny',
                description: I18n.t('lists.yoga_list.Santana.effects'),
                descriptionKey: 'Santana',
                planets: beneficsIn5.length > 0 ? beneficsIn5 : [lord5],
                nature: 'Benefic',
                strength: 6 + santanaFactors
            }));
        }
    }

    /**
     * Aputra Yoga
     * Denial of children
     */
    _checkAputraYoga() {
        const lord5 = this.getHouseLord(5);
        const lord5House = this.getHouse(lord5);
        const planetsIn5 = this.getPlanetsInHouse(5);
        const malefics = this.getNaturalMalefics();

        let denialFactors = 0;

        const onlyMaleficsIn5 = planetsIn5.length > 0 &&
            planetsIn5.every(p => malefics.includes(p));
        if (onlyMaleficsIn5) denialFactors++;
        if (dusthanas.includes(lord5House)) denialFactors++;
        if (this.getDignity(lord5) === 'Debilitated' && this.isCombust(lord5)) denialFactors++;
        
        const jupiterAfflicted = (this.getDignity('Jupiter') === 'Debilitated' || this.isCombust('Jupiter')) && 
                                 [8, 12].includes(this.getHouse('Jupiter'));
        if (jupiterAfflicted) denialFactors++;

        if (this.getHouse('Saturn') === 5 && !this._aspectsHouse('Jupiter', this.getHouse('Jupiter'), 5)) denialFactors++;

        if (denialFactors >= 2) {
            const jupiterAspects5 = this._aspectsHouse('Jupiter', this.getHouse('Jupiter'), 5);
            if (jupiterAspects5 && this.isStrong('Jupiter')) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Aputra_Bhanga.name'),
                    nameKey: 'Aputra_Bhanga',
                    category: 'Progeny',
                    description: I18n.t('lists.yoga_list.Aputra_Bhanga.effects'),
                    descriptionKey: 'Aputra_Bhanga',
                    planets: ['Jupiter', lord5],
                    nature: 'Neutral',
                    strength: 5
                }));
            } else {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Aputra.name'),
                    nameKey: 'Aputra',
                    category: 'Progeny',
                    description: I18n.t('lists.yoga_list.Aputra.effects'),
                    descriptionKey: 'Aputra',
                    planets: [lord5, 'Jupiter'],
                    nature: 'Malefic',
                    strength: 3
                }));
            }
        }
    }

    /**
     * Bahusantana Yoga
     * Many children
     */
    _checkBahusantanaYoga() {
        const lord5 = this.getHouseLord(5);
        const planetsIn5 = this.getPlanetsInHouse(5);
        const benefics = this.getNaturalBenefics();
        const beneficsIn5 = planetsIn5.filter(p => benefics.includes(p));

        let manyChildFactors = 0;
        if (beneficsIn5.length >= 2) manyChildFactors++;
        if ([2, 5, 8, 11].includes(this.getRasi(lord5))) manyChildFactors++;
        if ([5, 11].includes(this.getHouse('Jupiter'))) manyChildFactors++;
        if (this.isStrong('Venus') && [2, 5, 7, 9, 11].includes(this.getHouse('Venus'))) manyChildFactors++;
        if (this.getHouse('Moon') === 5 && this.isWaxingMoon()) manyChildFactors++;

        if (manyChildFactors >= 2) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Bahusantana.name'),
                nameKey: 'Bahusantana',
                category: 'Progeny',
                description: I18n.t('lists.yoga_list.Bahusantana.effects'),
                descriptionKey: 'Bahusantana',
                planets: beneficsIn5.length > 0 ? beneficsIn5 : [lord5, 'Jupiter'],
                nature: 'Benefic',
                strength: 7
            }));
        }
    }

    /**
     * Ekaputra Yoga
     * Only one child
     */
    _checkEkaputraYoga() {
        const lord5 = this.getHouseLord(5);
        const planetsIn5 = this.getPlanetsInHouse(5);

        let singleChildFactors = 0;
        if ([1, 4, 7, 10].includes(this.getRasi(lord5)) && this.isStrong(lord5)) singleChildFactors++;
        if (planetsIn5.length === 1 && this.getNaturalBenefics().includes(planetsIn5[0])) singleChildFactors++;
        if (this.getHouse('Sun') === 5 && this.getDignity('Sun') !== 'Debilitated') singleChildFactors++;
        if (this._aspectsHouse('Saturn', this.getHouse('Saturn'), 5) && !this._aspectsHouse('Jupiter', this.getHouse('Jupiter'), 5)) singleChildFactors++;

        if (singleChildFactors >= 2 && !this._hasAputraYoga()) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Ekaputra.name'),
                nameKey: 'Ekaputra',
                category: 'Progeny',
                description: I18n.t('lists.yoga_list.Ekaputra.effects'),
                descriptionKey: 'Ekaputra',
                planets: [lord5],
                nature: 'Neutral',
                strength: 5
            }));
        }
    }

    /**
     * Check if Aputra factors exist
     */
    _hasAputraYoga() {
        const lord5 = this.getHouseLord(5);
        const lord5House = this.getHouse(lord5);
        return dusthanas.includes(lord5House) && this.getDignity(lord5) === 'Debilitated';
    }

    /**
     * Dattaka Yoga
     * Adopted children
     */
    _checkDattakaYoga() {
        const lord5 = this.getHouseLord(5);
        const lord5House = this.getHouse(lord5);
        const planetsIn5 = this.getPlanetsInHouse(5);

        let adoptionFactors = 0;
        if (lord5House === 8) adoptionFactors++;
        if (planetsIn5.includes('Saturn')) adoptionFactors++;
        if (this.isConjunct(lord5, 'Rahu') || this.isConjunct(lord5, 'Ketu')) adoptionFactors++;
        if (this.getHouse('Moon') === 5 && (this.getDignity('Moon') === 'Debilitated' || !this.isWaxingMoon())) adoptionFactors++;

        if (adoptionFactors >= 2 && this._aspectsHouse('Jupiter', this.getHouse('Jupiter'), 5)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Dattaka.name'),
                nameKey: 'Dattaka',
                category: 'Progeny',
                description: I18n.t('lists.yoga_list.Dattaka.effects'),
                descriptionKey: 'Dattaka',
                planets: [lord5, 'Jupiter'],
                nature: 'Neutral',
                strength: 5
            }));
        }
    }

    /**
     * Putra Shoka Yoga
     * Loss/grief from children
     */
    _checkPutraShokaYoga() {
        const lord5 = this.getHouseLord(5);
        const malefics = this.getNaturalMalefics();

        let griefFactors = 0;
        const marsIn5 = this.getHouse('Mars') === 5;
        const saturnIn5 = this.getHouse('Saturn') === 5;
        const marsAspects5 = this._aspectsHouse('Mars', this.getHouse('Mars'), 5);
        const saturnAspects5 = this._aspectsHouse('Saturn', this.getHouse('Saturn'), 5);

        if ((marsIn5 || marsAspects5) && (saturnIn5 || saturnAspects5)) griefFactors++;
        
        const lord5House = this.getHouse(lord5);
        const prevHouse = lord5House === 1 ? 12 : lord5House - 1;
        const nextHouse = lord5House === 12 ? 1 : lord5House + 1;
        if (malefics.some(m => this.getHouse(m) === prevHouse) && malefics.some(m => this.getHouse(m) === nextHouse)) griefFactors++;

        const rahuHouse = this.getHouse('Rahu');
        const ketuHouse = this.getHouse('Ketu');
        if ((rahuHouse === 5 && ketuHouse === 11) || (rahuHouse === 11 && ketuHouse === 5)) griefFactors++;

        if (griefFactors >= 2) {
            if (this.isStrong('Jupiter') && this._aspectsHouse('Jupiter', this.getHouse('Jupiter'), 5)) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Putra_Shoka_Bhanga.name'),
                    nameKey: 'Putra_Shoka_Bhanga',
                    category: 'Progeny',
                    description: I18n.t('lists.yoga_list.Putra_Shoka_Bhanga.effects'),
                    descriptionKey: 'Putra_Shoka_Bhanga',
                    planets: ['Jupiter', lord5],
                    nature: 'Neutral',
                    strength: 5
                }));
            } else {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Putra_Shoka.name'),
                    nameKey: 'Putra_Shoka',
                    category: 'Progeny',
                    description: I18n.t('lists.yoga_list.Putra_Shoka.effects'),
                    descriptionKey: 'Putra_Shoka',
                    planets: [lord5, ...malefics.filter(m => [5, lord5House].includes(this.getHouse(m)))],
                    nature: 'Malefic',
                    strength: 3
                }));
            }
        }
    }
}

export default ProgenyYogas;
