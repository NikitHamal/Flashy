/**
 * Nabhasa Yogas - Akriti (Shape) Category
 * Implements pattern-based yogas based on planet distribution
 */

import I18n from '../../core/i18n.js';
import { YogaModuleBase, createYoga, sevenPlanets, kendras, trikonas, apoklimas } from './base.js';

export class NabhasaAkritiYogas extends YogaModuleBase {
    check() {
        this._checkYupaGroup();
        this._checkNaukaGroup();
        this._checkChakraSamudra();
        this._checkGadaGroup();
        this._checkVihagaShakta();
        this._checkShringataka();
        this._checkHalaYoga();
        this._checkVajraYava();
    }

    /**
     * Get occupied house count for 7 planets
     */
    _getOccupiedHouses() {
        const houses = new Set();
        for (const p of sevenPlanets) {
            const h = this.getHouse(p);
            if (h !== -1) houses.add(h);
        }
        return houses;
    }

    /**
     * Check if all 7 planets are in N consecutive houses starting from a given house
     */
    _planetsInConsecutiveHouses(startHouse, count) {
        const validHouses = new Set();
        for (let i = 0; i < count; i++) {
            validHouses.add(((startHouse - 1 + i) % 12) + 1);
        }

        for (const p of sevenPlanets) {
            const h = this.getHouse(p);
            if (h === -1 || !validHouses.has(h)) return false;
        }
        return true;
    }

    /**
     * Check if all planets are in specific houses only
     */
    _planetsOnlyInHouses(allowedHouses) {
        for (const p of sevenPlanets) {
            const h = this.getHouse(p);
            if (h === -1 || !allowedHouses.includes(h)) return false;
        }
        return true;
    }

    /**
     * Yupa/Ishu/Shakti/Danda group - 4 consecutive houses
     */
    _checkYupaGroup() {
        // Yupa: All planets in 4 consecutive houses from Lagna (1-4)
        if (this._planetsInConsecutiveHouses(1, 4)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Yupa.name'),
                nameKey: 'Yupa',
                category: 'Nabhasa_Akriti',
                description: I18n.t('lists.yoga_list.Yupa.effects'),
                descriptionKey: 'Yupa',
                planets: sevenPlanets,
                nature: 'Benefic',
                strength: 6
            }));
        }

        // Ishu/Sara: All planets in 4 consecutive houses from 4th (4-7)
        if (this._planetsInConsecutiveHouses(4, 4)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Ishu.name'),
                nameKey: 'Ishu',
                category: 'Nabhasa_Akriti',
                description: I18n.t('lists.yoga_list.Ishu.effects'),
                descriptionKey: 'Ishu',
                planets: sevenPlanets,
                nature: 'Neutral',
                strength: 5
            }));
        }

        // Shakti: All planets in 4 consecutive houses from 7th (7-10)
        if (this._planetsInConsecutiveHouses(7, 4)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Shakti.name'),
                nameKey: 'Shakti',
                category: 'Nabhasa_Akriti',
                description: I18n.t('lists.yoga_list.Shakti.effects'),
                descriptionKey: 'Shakti',
                planets: sevenPlanets,
                nature: 'Malefic',
                strength: 3
            }));
        }

        // Danda: All planets in 4 consecutive houses from 10th (10-1)
        if (this._planetsInConsecutiveHouses(10, 4)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Danda.name'),
                nameKey: 'Danda',
                category: 'Nabhasa_Akriti',
                description: I18n.t('lists.yoga_list.Danda.effects'),
                descriptionKey: 'Danda',
                planets: sevenPlanets,
                nature: 'Malefic',
                strength: 3
            }));
        }
    }

    /**
     * Nauka/Kuta/Chhatra/Chapa group - 7 consecutive houses
     */
    _checkNaukaGroup() {
        // Nauka (Nav): All planets in 7 consecutive houses from Lagna
        if (this._planetsInConsecutiveHouses(1, 7)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Nauka.name'),
                nameKey: 'Nauka',
                category: 'Nabhasa_Akriti',
                description: I18n.t('lists.yoga_list.Nauka.effects'),
                descriptionKey: 'Nauka',
                planets: sevenPlanets,
                nature: 'Benefic',
                strength: 7
            }));
        }

        // Kuta: All planets in 7 consecutive houses from 4th
        if (this._planetsInConsecutiveHouses(4, 7)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Kuta.name'),
                nameKey: 'Kuta',
                category: 'Nabhasa_Akriti',
                description: I18n.t('lists.yoga_list.Kuta.effects'),
                descriptionKey: 'Kuta',
                planets: sevenPlanets,
                nature: 'Malefic',
                strength: 3
            }));
        }

        // Chhatra: All planets in 7 consecutive houses from 7th
        if (this._planetsInConsecutiveHouses(7, 7)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Chhatra.name'),
                nameKey: 'Chhatra',
                category: 'Nabhasa_Akriti',
                description: I18n.t('lists.yoga_list.Chhatra.effects'),
                descriptionKey: 'Chhatra',
                planets: sevenPlanets,
                nature: 'Benefic',
                strength: 6
            }));
        }

        // Chapa/Dhanush: All planets in 7 consecutive houses from 10th
        if (this._planetsInConsecutiveHouses(10, 7)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Chapa.name'),
                nameKey: 'Chapa',
                category: 'Nabhasa_Akriti',
                description: I18n.t('lists.yoga_list.Chapa.effects'),
                descriptionKey: 'Chapa',
                planets: sevenPlanets,
                nature: 'Neutral',
                strength: 5
            }));
        }

        // Ardha Chandra: All planets in 7 consecutive houses (any start)
        for (let start = 1; start <= 12; start++) {
            // Skip if already covered by specific yogas above
            if ([1, 4, 7, 10].includes(start)) continue;

            if (this._planetsInConsecutiveHouses(start, 7)) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Ardha_Chandra.name'),
                    nameKey: 'Ardha_Chandra',
                    category: 'Nabhasa_Akriti',
                    description: I18n.t('lists.yoga_list.Ardha_Chandra.effects'),
                    descriptionKey: 'Ardha_Chandra',
                    planets: sevenPlanets,
                    nature: 'Benefic',
                    strength: 6
                }));
                break; // Only add once
            }
        }
    }

    /**
     * Chakra and Samudra yogas
     */
    _checkChakraSamudra() {
        const oddHouses = [1, 3, 5, 7, 9, 11];
        const evenHouses = [2, 4, 6, 8, 10, 12];

        // Chakra: All planets in odd houses
        if (this._planetsOnlyInHouses(oddHouses)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Chakra.name'),
                nameKey: 'Chakra',
                category: 'Nabhasa_Akriti',
                description: I18n.t('lists.yoga_list.Chakra.effects'),
                descriptionKey: 'Chakra',
                planets: sevenPlanets,
                nature: 'Benefic',
                strength: 8
            }));
        }

        // Samudra: All planets in even houses
        if (this._planetsOnlyInHouses(evenHouses)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Samudra.name'),
                nameKey: 'Samudra',
                category: 'Nabhasa_Akriti',
                description: I18n.t('lists.yoga_list.Samudra.effects'),
                descriptionKey: 'Samudra',
                planets: sevenPlanets,
                nature: 'Benefic',
                strength: 8
            }));
        }
    }

    /**
     * Gada group - planets in two kendras
     */
    _checkGadaGroup() {
        const kendraPairs = [
            { houses: [1, 4], key: 'Gada' },
            { houses: [4, 7], key: 'Gada' },
            { houses: [7, 10], key: 'Gada' },
            { houses: [10, 1], key: 'Gada' }
        ];

        for (const pair of kendraPairs) {
            if (this._planetsOnlyInHouses(pair.houses)) {
                this.addYoga(createYoga({
                    name: I18n.t(`lists.yoga_list.${pair.key}.name`),
                    nameKey: pair.key,
                    category: 'Nabhasa_Akriti',
                    description: I18n.t(`lists.yoga_list.${pair.key}.effects`),
                    descriptionKey: pair.key,
                    planets: sevenPlanets,
                    nature: 'Neutral',
                    strength: 5
                }));
                break;
            }
        }
    }

    /**
     * Shakata and Vihaga yogas
     */
    _checkVihagaShakta() {
        // Shakata (Akriti): All planets in 1st and 7th houses only
        if (this._planetsOnlyInHouses([1, 7])) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Shakata_Akriti.name'),
                nameKey: 'Shakata_Akriti',
                category: 'Nabhasa_Akriti',
                description: I18n.t('lists.yoga_list.Shakata_Akriti.effects'),
                descriptionKey: 'Shakata_Akriti',
                planets: sevenPlanets,
                nature: 'Malefic',
                strength: 3
            }));
        }

        // Vihaga/Pakshi: All planets in 4th and 10th houses only
        if (this._planetsOnlyInHouses([4, 10])) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vihaga.name'),
                nameKey: 'Vihaga',
                category: 'Nabhasa_Akriti',
                description: I18n.t('lists.yoga_list.Vihaga.effects'),
                descriptionKey: 'Vihaga',
                planets: sevenPlanets,
                nature: 'Neutral',
                strength: 5
            }));
        }
    }

    /**
     * Shringataka Yoga - planets in trikonas only
     */
    _checkShringataka() {
        if (this._planetsOnlyInHouses([1, 5, 9])) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Shringataka.name'),
                nameKey: 'Shringataka',
                category: 'Nabhasa_Akriti',
                description: I18n.t('lists.yoga_list.Shringataka.effects'),
                descriptionKey: 'Shringataka',
                planets: sevenPlanets,
                nature: 'Neutral',
                strength: 5
            }));
        }
    }

    /**
     * Hala Yoga - planets in apoklimas
     */
    _checkHalaYoga() {
        if (this._planetsOnlyInHouses([3, 6, 9, 12])) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Hala.name'),
                nameKey: 'Hala',
                category: 'Nabhasa_Akriti',
                description: I18n.t('lists.yoga_list.Hala.effects'),
                descriptionKey: 'Hala',
                planets: sevenPlanets,
                nature: 'Malefic',
                strength: 3
            }));
        }
    }

    /**
     * Vajra and Yava yogas
     */
    _checkVajraYava() {
        const benefics = this.getNaturalBenefics();
        const malefics = this.getNaturalMalefics();

        // Helper to check planet distribution
        const getBeneficHouses = () => {
            return benefics.map(p => this.getHouse(p)).filter(h => h !== -1);
        };

        const getMaleficHouses = () => {
            return malefics.filter(p => sevenPlanets.includes(p)).map(p => this.getHouse(p)).filter(h => h !== -1);
        };

        const beneficHouses = getBeneficHouses();
        const maleficHouses = getMaleficHouses();

        // Vajra: Benefics in 1st & 7th, Malefics in 4th & 10th
        const beneficsIn1_7 = beneficHouses.every(h => [1, 7].includes(h));
        const maleficsIn4_10 = maleficHouses.every(h => [4, 10].includes(h));

        if (beneficHouses.length >= 2 && maleficHouses.length >= 2 && beneficsIn1_7 && maleficsIn4_10) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vajra.name'),
                nameKey: 'Vajra',
                category: 'Nabhasa_Akriti',
                description: I18n.t('lists.yoga_list.Vajra.effects'),
                descriptionKey: 'Vajra',
                planets: [...benefics.filter(p => [1, 7].includes(this.getHouse(p))),
                ...malefics.filter(p => [4, 10].includes(this.getHouse(p)))],
                nature: 'Benefic',
                strength: 6
            }));
        }

        // Yava: Malefics in 1st & 7th, Benefics in 4th & 10th
        const maleficsIn1_7 = maleficHouses.every(h => [1, 7].includes(h));
        const beneficsIn4_10 = beneficHouses.every(h => [4, 10].includes(h));

        if (beneficHouses.length >= 2 && maleficHouses.length >= 2 && maleficsIn1_7 && beneficsIn4_10) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Yava.name'),
                nameKey: 'Yava',
                category: 'Nabhasa_Akriti',
                description: I18n.t('lists.yoga_list.Yava.effects'),
                descriptionKey: 'Yava',
                planets: [...malefics.filter(p => [1, 7].includes(this.getHouse(p))),
                ...benefics.filter(p => [4, 10].includes(this.getHouse(p)))],
                nature: 'Neutral',
                strength: 5
            }));
        }
    }
}

export default NabhasaAkritiYogas;
