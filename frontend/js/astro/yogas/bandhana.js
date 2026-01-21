/**
 * Bandhana (Imprisonment/Bondage) Yogas Module
 * Implements combinations indicating restriction, imprisonment, or feeling trapped.
 *
 * References:
 * - Saravali
 * - Jataka Parijata
 */

import { YogaModuleBase, createYoga, kendras, trikonas, dusthanas, sevenPlanets } from './base.js';

export class BandhanaYogas extends YogaModuleBase {
    check() {
        this._checkSankhyaBandhana();
        this._checkMaleficBandhana();
        this._checkLagnaLordBandhana();
        this._checkSaturnMoonMarsBandhana();
    }

    /**
     * Sankhya Bandhana
     * Equal number of planets in pairs of houses:
     * 2-12, 3-11, 4-10, 5-9, 6-8
     */
    _checkSankhyaBandhana() {
        const pairs = [
            { h1: 2, h2: 12, name: 'Dhana-Vyaya' },
            { h1: 3, h2: 11, name: 'Sahaja-Labha' },
            { h1: 4, h2: 10, name: 'Bandhu-Karma' },
            { h1: 5, h2: 9, name: 'Putra-Dharma' },
            { h1: 6, h2: 8, name: 'Ari-Mrityu' }
        ];

        for (const { h1, h2, name } of pairs) {
            const p1 = this.getPlanetsInHouse(h1);
            const p2 = this.getPlanetsInHouse(h2);

            // Must have at least one planet in each to be considered "bondage" via equality
            // Some texts say equal number implies bondage.
            if (p1.length > 0 && p2.length > 0 && p1.length === p2.length) {
                // Check if malefics are involved (usually required for actual imprisonment)
                const hasMalefic = [...p1, ...p2].some(p => this.getNaturalMalefics().includes(p));
                
                if (hasMalefic) {
                    this.addYoga(createYoga({
                        name: `Bandhana Yoga (${name})`,
                        nameKey: 'Bandhana_Sankhya',
                        category: 'Bandhana',
                        description: `Equal number of planets in ${h1}th and ${h2}th houses. Restriction or feeling trapped related to these houses.`,
                        descriptionKey: 'Bandhana_Sankhya',
                        planets: [...p1, ...p2],
                        nature: 'Malefic',
                        strength: 4,
                        params: { h1, h2 }
                    }));
                }
            }
        }
    }

    /**
     * Malefic Bandhana
     * Malefics in 2nd and 12th; 5th and 9th; 6th and 12th
     */
    _checkMaleficBandhana() {
        const pairs = [
            { h1: 2, h2: 12, type: 'Financial/Physical restriction' },
            { h1: 5, h2: 9, type: 'Mental/Spiritual restriction' },
            { h1: 6, h2: 12, type: 'Service/Confinement' }
        ];

        const malefics = this.getNaturalMalefics(); // Sun, Mars, Sat, Rahu, Ketu

        for (const { h1, h2, type } of pairs) {
            const p1 = this.getPlanetsInHouse(h1).filter(p => malefics.includes(p));
            const p2 = this.getPlanetsInHouse(h2).filter(p => malefics.includes(p));

            if (p1.length > 0 && p2.length > 0) {
                this.addYoga(createYoga({
                    name: 'Bandhana Yoga (Malefics)',
                    nameKey: 'Bandhana_Malefics',
                    category: 'Bandhana',
                    description: `Malefics in ${h1}th and ${h2}th houses. Indicates ${type}.`,
                    descriptionKey: 'Bandhana_Malefics',
                    planets: [...p1, ...p2],
                    nature: 'Malefic',
                    strength: 5,
                    params: { h1, h2, type }
                }));
            }
        }
    }

    /**
     * Lagna Lord Bandhana
     * Lagna Lord and 6th Lord in Kendra/Trikona with Saturn/Rahu/Ketu
     */
    _checkLagnaLordBandhana() {
        const lord1 = this.getHouseLord(1);
        const lord6 = this.getHouseLord(6);
        
        const h1 = this.getHouse(lord1);
        const h6 = this.getHouse(lord6);

        // Check if both are in Kendra or Trikona
        const goodHouses = [...kendras, ...trikonas];
        if (goodHouses.includes(h1) && goodHouses.includes(h6)) {
            // Check conjunction with Saturn, Rahu, or Ketu
            const restrictors = ['Saturn', 'Rahu', 'Ketu'];
            const lord1Restricted = restrictors.some(r => this.isConjunct(lord1, r));
            const lord6Restricted = restrictors.some(r => this.isConjunct(lord6, r));

            if (lord1Restricted && lord6Restricted) {
                this.addYoga(createYoga({
                    name: 'Bandhana Yoga (Lords)',
                    nameKey: 'Bandhana_Lords',
                    category: 'Bandhana',
                    description: 'Lagna Lord and 6th Lord in Kendra/Trikona with Saturn/Rahu/Ketu. Potential for legal issues or confinement.',
                    descriptionKey: 'Bandhana_Lords',
                    planets: [lord1, lord6],
                    nature: 'Malefic',
                    strength: 6
                }));
            }
        }
    }

    /**
     * Saturn-Moon-Mars Bandhana
     * Saturn, Moon, Mars in 2nd, 4th, 9th (any combination)
     */
    _checkSaturnMoonMarsBandhana() {
        const houses = [2, 4, 9];
        const p1 = this.getHouse('Saturn');
        const p2 = this.getHouse('Moon');
        const p3 = this.getHouse('Mars');

        if (houses.includes(p1) && houses.includes(p2) && houses.includes(p3)) {
            this.addYoga(createYoga({
                name: 'Bandhana Yoga (Graha)',
                nameKey: 'Bandhana_Graha',
                category: 'Bandhana',
                description: 'Saturn, Moon, and Mars in 2nd, 4th, or 9th houses. Indicators of restriction.',
                descriptionKey: 'Bandhana_Graha',
                planets: ['Saturn', 'Moon', 'Mars'],
                nature: 'Malefic',
                strength: 5
            }));
        }
    }
}

export default BandhanaYogas;
