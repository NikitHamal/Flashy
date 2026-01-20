/**
 * ============================================================================
 * NABHASA SANKHYA YOGAS - Count-Based Planetary Patterns
 * ============================================================================
 *
 * These yogas are formed based on the number of houses occupied by all seven
 * classical planets (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn).
 * They describe the overall life pattern and destiny.
 *
 * References:
 * - Brihat Parashara Hora Shastra (BPHS) Chapter 35
 * - Phaladeepika Chapter 6
 * - Saravali
 *
 * @module yogas/nabhasa_sankhya
 * @version 1.0.0
 */

import { YogaModuleBase, createYoga, sevenPlanets } from './base.js';

import I18n from '../../core/i18n.js';

/**
 * Sankhya Yoga definitions based on house count
 * Each yoga has specific effects based on classical texts
 */
const sankhyaDefinitions = {
    1: {
        nameKey: 'Gola',
        nature: 'Malefic',
        strength: 2
    },
    2: {
        nameKey: 'Yuga',
        nature: 'Neutral',
        strength: 4
    },
    3: {
        nameKey: 'Shula',
        nature: 'Neutral',
        strength: 5
    },
    4: {
        nameKey: 'Kedara',
        nature: 'Benefic',
        strength: 6
    },
    5: {
        nameKey: 'Pasha',
        nature: 'Neutral',
        strength: 5
    },
    6: {
        nameKey: 'Dama',
        nature: 'Benefic',
        strength: 6
    },
    7: {
        nameKey: 'Veena',
        nature: 'Benefic',
        strength: 7
    }
};

/**
 * Ashraya (Sign-based) Yoga definitions
 * Based on whether all planets are in Movable, Fixed, or Dual signs
 */
const ashrayaDefinitions = {
    movable: {
        nameKey: 'Rajju',
        nature: 'Neutral',
        strength: 6
    },
    fixed: {
        nameKey: 'Musala',
        nature: 'Benefic',
        strength: 7
    },
    dual: {
        nameKey: 'Nala',
        nature: 'Neutral',
        strength: 5
    }
};

/**
 * Dala (Petal) Yoga definitions
 * Based on whether planets occupy predominantly benefic or malefic house combinations
 */
const dalaDefinitions = {
    mala: {
        nameKey: 'Mala_Dala',
        nature: 'Benefic',
        strength: 8
    },
    sarpa: {
        nameKey: 'Sarpa_Dala',
        nature: 'Malefic',
        strength: 3
    }
};

export class NabhasaSankhyaYogas extends YogaModuleBase {
    constructor(ctx) {
        super(ctx);
    }

    check() {
        this._checkSankhyaYogas();
        this._checkAshrayaYogas();
        this._checkDalaYogas();
    }

    /**
     * Check Sankhya Yogas based on house occupation count
     */
    _checkSankhyaYogas() {
        const occupiedHouses = new Set();

        for (const planet of sevenPlanets) {
            const house = this.getHouse(planet);
            if (house !== -1 && house !== 0) {
                occupiedHouses.add(house);
            }
        }

        const count = occupiedHouses.size;

        // Only form yoga if planets occupy 1-7 houses
        if (count >= 1 && count <= 7) {
            const def = sankhyaDefinitions[count];
            if (def) {
                // Calculate strength modification based on house quality
                let strengthMod = 0;
                const kendras = [1, 4, 7, 10];
                const trikonas = [1, 5, 9];

                for (const h of occupiedHouses) {
                    if (kendras.includes(h)) strengthMod += 0.3;
                    if (trikonas.includes(h) && h !== 1) strengthMod += 0.2;
                }

                this.addYoga(createYoga({
                    name: I18n.t(`lists.yoga_list.${def.nameKey}.name`),
                    nameKey: def.nameKey,
                    category: 'Nabhasa_Sankhya',
                    description: I18n.t(`lists.yoga_list.${def.nameKey}.effects`),
                    descriptionKey: def.nameKey,
                    planets: sevenPlanets,
                    nature: def.nature,
                    strength: Math.min(10, def.strength + strengthMod)
                }));
            }
        }
    }

    /**
     * Check Ashraya (Sign-based) Yogas
     * All planets in signs of same modality
     */
    _checkAshrayaYogas() {
        const modalityCounts = { 0: 0, 1: 0, 2: 0 }; // 0=Movable, 1=Fixed, 2=Dual
        const modalityMap = {
            0: 0, 1: 1, 2: 2, 3: 0,    // Aries-Cancer
            4: 1, 5: 2, 6: 0, 7: 1,    // Leo-Scorpio
            8: 2, 9: 0, 10: 1, 11: 2   // Sagittarius-Pisces
        };

        for (const planet of sevenPlanets) {
            const sign = this.getRasi(planet);
            if (sign !== -1) {
                const modality = modalityMap[sign];
                modalityCounts[modality]++;
            }
        }

        const addYogaInternal = (def) => {
            this.addYoga(createYoga({
                name: I18n.t(`lists.yoga_list.${def.nameKey}.name`),
                nameKey: def.nameKey,
                category: 'Nabhasa_Ashraya',
                description: I18n.t(`lists.yoga_list.${def.nameKey}.effects`),
                descriptionKey: def.nameKey,
                planets: sevenPlanets,
                nature: def.nature,
                strength: def.strength
            }));
        };

        // Check if all 7 planets are in same modality signs
        if (modalityCounts[0] === 7) {
            addYogaInternal(ashrayaDefinitions.movable);
        } else if (modalityCounts[1] === 7) {
            addYogaInternal(ashrayaDefinitions.fixed);
        } else if (modalityCounts[2] === 7) {
            addYogaInternal(ashrayaDefinitions.dual);
        }
    }

    /**
     * Check Dala (Petal) Yogas
     * Based on benefics/malefics in Kendras
     */
    _checkDalaYogas() {
        const kendras = [1, 4, 7, 10];
        const benefics = this.getNaturalBenefics();
        const malefics = this.getNaturalMalefics().filter(p => sevenPlanets.includes(p));

        // Count benefics and malefics in Kendras
        const beneficsInKendras = benefics.filter(p => kendras.includes(this.getHouse(p)));
        const maleficsInKendras = malefics.filter(p => kendras.includes(this.getHouse(p)));

        // Mala Yoga: All benefics in Kendras
        if (beneficsInKendras.length >= 2 && beneficsInKendras.length === benefics.length) {
            const def = dalaDefinitions.mala;
            this.addYoga(createYoga({
                name: I18n.t(`lists.yoga_list.${def.nameKey}.name`),
                nameKey: def.nameKey,
                category: 'Nabhasa_Dala',
                description: I18n.t(`lists.yoga_list.${def.nameKey}.effects`),
                descriptionKey: def.nameKey,
                planets: beneficsInKendras,
                nature: def.nature,
                strength: def.strength
            }));
        }

        // Sarpa Yoga: All malefics in Kendras
        if (maleficsInKendras.length >= 3) {
            // Check if all natural malefics among seven planets are in Kendras
            const allMaleficsInKendras = malefics.every(p => kendras.includes(this.getHouse(p)));
            if (allMaleficsInKendras) {
                const def = dalaDefinitions.sarpa;
                this.addYoga(createYoga({
                    name: I18n.t(`lists.yoga_list.${def.nameKey}.name`),
                    nameKey: def.nameKey,
                    category: 'Nabhasa_Dala',
                    description: I18n.t(`lists.yoga_list.${def.nameKey}.effects`),
                    descriptionKey: def.nameKey,
                    planets: maleficsInKendras,
                    nature: def.nature,
                    strength: def.strength
                }));
            }
        }
    }
}

export default NabhasaSankhyaYogas;
