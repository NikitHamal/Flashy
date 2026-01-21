/**
 * Kaal Sarpa Yoga Module
 * Implements all 12 named Kaal Sarpa Dosha variants plus partial Kaal Sarpa
 */

import I18n from '../../core/i18n.js';
import { YogaModuleBase, createYoga, allPlanets, sevenPlanets } from './base.js';

// Kaal Sarpa Yoga definitions
const kaalSarpaDefinitions = {
    1: { nameKey: 'Anant_Kaal_Sarpa', nature: 'Malefic' },
    2: { nameKey: 'Kulik_Kaal_Sarpa', nature: 'Malefic' },
    3: { nameKey: 'Vasuki_Kaal_Sarpa', nature: 'Neutral' },
    4: { nameKey: 'Shankhpal_Kaal_Sarpa', nature: 'Malefic' },
    5: { nameKey: 'Padma_Kaal_Sarpa', nature: 'Neutral' },
    6: { nameKey: 'Mahapadma_Kaal_Sarpa', nature: 'Neutral' },
    7: { nameKey: 'Takshak_Kaal_Sarpa', nature: 'Malefic' },
    8: { nameKey: 'Karkotak_Kaal_Sarpa', nature: 'Malefic' },
    9: { nameKey: 'Shankhachud_Kaal_Sarpa', nature: 'Neutral' },
    10: { nameKey: 'Ghatak_Kaal_Sarpa', nature: 'Neutral' },
    11: { nameKey: 'Vishdhar_Kaal_Sarpa', nature: 'Neutral' },
    12: { nameKey: 'Sheshnag_Kaal_Sarpa', nature: 'Benefic' }
};

export class KaalSarpaYogas extends YogaModuleBase {
    check() {
        this._checkKaalSarpaYoga();
        this._checkKalaAmritaYoga();
    }

    /**
     * Check for Kaal Sarpa Yoga
     * All 7 planets hemmed between Rahu and Ketu
     */
    _checkKaalSarpaYoga() {
        const rahuHouse = this.getHouse('Rahu');
        const ketuHouse = this.getHouse('Ketu');

        if (rahuHouse === -1 || ketuHouse === -1) return;

        // Get houses where all 7 planets are located
        const planetHouses = sevenPlanets.map(p => this.getHouse(p)).filter(h => h !== -1);
        if (planetHouses.length !== 7) return;

        // Check if all planets are between Rahu and Ketu (moving counterclockwise)
        const { allHemmed, partialHemmed, outsideCount } = this._checkHemming(rahuHouse, ketuHouse, planetHouses);

        if (allHemmed) {
            // Full Kaal Sarpa Yoga - determine which type based on Rahu's house
            const def = kaalSarpaDefinitions[rahuHouse];
            if (def) {
                // Check for ascending (Rahu before Ketu) vs descending (Ketu before Rahu)
                const isAscending = this._isAscendingKaalSarpa(rahuHouse, ketuHouse, planetHouses);
                const suffix = isAscending ? '' : ` (${I18n.t('common.descending')})`;

                this.addYoga(createYoga({
                    name: I18n.t(`lists.yoga_list.${def.nameKey}.name`) + suffix,
                    nameKey: def.nameKey,
                    category: 'Kaal_Sarpa',
                    description: I18n.t(`lists.yoga_list.${def.nameKey}.effects`) + (isAscending ? '' : ` ${I18n.t('yogas.descending_note')}`),
                    descriptionKey: def.nameKey,
                    planets: ['Rahu', 'Ketu', ...sevenPlanets],
                    nature: def.nature,
                    strength: isAscending ? 4 : 3.5
                }));
            }
        } else if (outsideCount === 1) {
             // Single planet breaking the chain (Kaal Sarpa Bhanga)
             this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Kaal_Sarpa_Bhanga.name'),
                nameKey: 'Kaal_Sarpa_Bhanga',
                category: 'Kaal_Sarpa',
                description: I18n.t('lists.yoga_list.Kaal_Sarpa_Bhanga.effects'),
                descriptionKey: 'Kaal_Sarpa_Bhanga',
                planets: ['Rahu', 'Ketu'],
                nature: 'Benefic',
                strength: 5
            }));
        } else if (partialHemmed && outsideCount <= 2) {
            // Partial Kaal Sarpa Yoga
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Partial_Kaal_Sarpa.name'),
                nameKey: 'Partial_Kaal_Sarpa',
                category: 'Kaal_Sarpa',
                description: I18n.t('lists.yoga_list.Partial_Kaal_Sarpa.effects'),
                descriptionKey: 'Partial_Kaal_Sarpa',
                planets: ['Rahu', 'Ketu'],
                nature: 'Neutral',
                strength: 3 - (outsideCount * 0.5)
            }));
        }
    }

    /**
     * Check if planets are hemmed between Rahu and Ketu
     */
    _checkHemming(rahuHouse, ketuHouse, planetHouses) {
        // Kaal Sarpa: All planets on one side of Rahu-Ketu axis
        // Calculate houses on Rahu's side (counterclockwise to Ketu)
        const hemmedHouses = new Set();

        // From Rahu going counterclockwise to Ketu (not including Rahu/Ketu houses)
        let current = rahuHouse;
        while (current !== ketuHouse) {
            current = current === 12 ? 1 : current + 1;
            if (current !== ketuHouse) {
                hemmedHouses.add(current);
            }
        }

        let outsideCount = 0;
        let insideCount = 0;

        for (const h of planetHouses) {
            if (h === rahuHouse || h === ketuHouse) {
                // Planet conjunct node - breaks Kaal Sarpa for most authorities
                outsideCount++;
            } else if (hemmedHouses.has(h)) {
                insideCount++;
            } else {
                outsideCount++;
            }
        }

        return {
            allHemmed: outsideCount === 0 && insideCount === 7,
            partialHemmed: insideCount >= 5,
            outsideCount
        };
    }

    /**
     * Determine if Kaal Sarpa is ascending (most planets moving toward Rahu)
     */
    _isAscendingKaalSarpa(rahuHouse, ketuHouse, planetHouses) {
        // Ascending: More planets closer to Ketu side (moving toward Rahu in transit)
        let countNearRahu = 0;
        let countNearKetu = 0;

        for (const h of planetHouses) {
            const distToRahu = (rahuHouse - h + 12) % 12;
            const distToKetu = (ketuHouse - h + 12) % 12;
            if (distToRahu < distToKetu) {
                countNearRahu++;
            } else {
                countNearKetu++;
            }
        }

        return countNearKetu >= countNearRahu;
    }

    /**
     * Check for Kala Amrita Yoga (reverse of Kaal Sarpa)
     * All planets between Ketu and Rahu (opposite direction)
     */
    _checkKalaAmritaYoga() {
        const rahuHouse = this.getHouse('Rahu');
        const ketuHouse = this.getHouse('Ketu');

        if (rahuHouse === -1 || ketuHouse === -1) return;

        const planetHouses = sevenPlanets.map(p => this.getHouse(p)).filter(h => h !== -1);
        if (planetHouses.length !== 7) return;

        // Check if all planets are between Ketu and Rahu (opposite of Kaal Sarpa)
        const hemmedHouses = new Set();

        // From Ketu going counterclockwise to Rahu
        let current = ketuHouse;
        while (current !== rahuHouse) {
            current = current === 12 ? 1 : current + 1;
            if (current !== rahuHouse) {
                hemmedHouses.add(current);
            }
        }

        let outsideCount = 0;
        for (const h of planetHouses) {
            if (h === rahuHouse || h === ketuHouse) {
                outsideCount++;
            } else if (!hemmedHouses.has(h)) {
                outsideCount++;
            }
        }

        if (outsideCount === 0) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Kala_Amrita.name'),
                nameKey: 'Kala_Amrita',
                category: 'Kaal_Sarpa',
                description: I18n.t('lists.yoga_list.Kala_Amrita.effects'),
                descriptionKey: 'Kala_Amrita',
                planets: ['Ketu', 'Rahu', ...sevenPlanets],
                nature: 'Neutral',
                strength: 5
            }));
        }
    }
}

export default KaalSarpaYogas;
