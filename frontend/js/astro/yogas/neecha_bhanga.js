/**
 * ============================================================================
 * NEECHA BHANGA RAJA YOGA - Cancellation of Debilitation
 * ============================================================================
 *
 * One of the most powerful Raja Yogas in Vedic astrology. When a debilitated
 * planet's weakness is cancelled by specific conditions, it becomes a source
 * of exceptional strength and success.
 *
 * References:
 * - Brihat Parashara Hora Shastra (BPHS) Chapter 36
 * - Phaladeepika Chapter 7
 * - Uttara Kalamrita
 *
 * @module yogas/neecha_bhanga
 * @version 1.0.0
 */

import I18n from '../../core/i18n.js';
import { YogaModuleBase, createYoga } from './base.js';
import { DEBILITATION, EXALTATION, OWN_SIGNS, SIGN_LORDS, KENDRAS, RASI_NAMES } from '../constants.js';

/**
 * All conditions for Neecha Bhanga Raja Yoga
 */
const NEECHA_BHANGA_CONDITIONS = {
    CONDITION_1: { id: 'dispositor_kendra', strengthBonus: 1.5 },
    CONDITION_2: { id: 'exaltation_lord_kendra', strengthBonus: 1.5 },
    CONDITION_3: { id: 'dispositor_exalted', strengthBonus: 2 },
    CONDITION_4: { id: 'planet_aspected_by_dispositor', strengthBonus: 1.5 },
    CONDITION_5: { id: 'planet_conjunct_exalted', strengthBonus: 2 },
    CONDITION_6: { id: 'same_planet_exalted_navamsha', strengthBonus: 2.5 },
    CONDITION_7: { id: 'dispositor_aspects_own_sign', strengthBonus: 1.5 },
    CONDITION_8: { id: 'exchange_with_dispositor', strengthBonus: 3 }
};

export class NeechaBhangaYogas extends YogaModuleBase {
    constructor(ctx) {
        super(ctx);
    }

    check() {
        this._checkNeechaBhangaRajaYoga();
    }

    /**
     * Get the sign where a planet gets exalted
     */
    _getExaltationSign(planet) {
        const data = EXALTATION[planet];
        return data ? data.sign : -1;
    }

    /**
     * Get the sign where a planet gets debilitated
     */
    _getDebilitationSign(planet) {
        return DEBILITATION[planet] !== undefined ? DEBILITATION[planet] : -1;
    }

    /**
     * Get the lord of a sign
     */
    _getSignLord(sign) {
        return SIGN_LORDS[sign];
    }

    /**
     * Check if planet is in Kendra from reference
     */
    _isInKendra(planet, fromHouse = 1) {
        const house = this.getHouse(planet);
        if (house === -1) return false;
        // Calculate relative house position
        let relativeHouse = house - fromHouse + 1;
        if (relativeHouse <= 0) relativeHouse += 12;
        return KENDRAS.includes(relativeHouse);
    }

    /**
     * Check if planet is exalted
     */
    _isExalted(planet) {
        const sign = this.getRasi(planet);
        const exaltSign = this._getExaltationSign(planet);
        return sign === exaltSign;
    }

    /**
     * Main check for Neecha Bhanga Raja Yoga
     */
    _checkNeechaBhangaRajaYoga() {
        const planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];

        for (const planet of planets) {
            const sign = this.getRasi(planet);
            const debSign = this._getDebilitationSign(planet);

            // Check if planet is debilitated
            if (sign !== debSign || sign === -1) continue;

            const dispositor = this._getSignLord(sign);
            const exaltationSign = this._getExaltationSign(planet);
            const exaltationLord = exaltationSign !== -1 ? this._getSignLord(exaltationSign) : null;

            const conditions = [];
            let totalStrength = 3; // Base strength for having a debilitated planet

            // CONDITION 1: Dispositor in Kendra from Lagna
            if (this._isInKendra(dispositor, 1)) {
                conditions.push({
                    ...NEECHA_BHANGA_CONDITIONS.CONDITION_1,
                    details: I18n.t('yogas.neecha_bhanga_details.dispositor_kendra_lagna', { planet: I18n.t('planets.' + dispositor) })
                });
                totalStrength += NEECHA_BHANGA_CONDITIONS.CONDITION_1.strengthBonus;
            }

            // Also check from Moon
            const moonHouse = this.getHouse('Moon');
            if (moonHouse !== -1) {
                const dispositorHouse = this.getHouse(dispositor);
                if (dispositorHouse !== -1) {
                    let relFromMoon = dispositorHouse - moonHouse + 1;
                    if (relFromMoon <= 0) relFromMoon += 12;
                    if (KENDRAS.includes(relFromMoon)) {
                        conditions.push({
                            ...NEECHA_BHANGA_CONDITIONS.CONDITION_1,
                            details: I18n.t('yogas.neecha_bhanga_details.dispositor_kendra_moon', { planet: I18n.t('planets.' + dispositor) })
                        });
                        totalStrength += 1;
                    }
                }
            }

            // CONDITION 2: Exaltation lord in Kendra
            if (exaltationLord && this._isInKendra(exaltationLord, 1)) {
                conditions.push({
                    ...NEECHA_BHANGA_CONDITIONS.CONDITION_2,
                    details: I18n.t('yogas.neecha_bhanga_details.exaltation_lord_kendra', { planet: I18n.t('planets.' + exaltationLord) })
                });
                totalStrength += NEECHA_BHANGA_CONDITIONS.CONDITION_2.strengthBonus;
            }

            // CONDITION 3: Dispositor is exalted
            if (this._isExalted(dispositor)) {
                conditions.push({
                    ...NEECHA_BHANGA_CONDITIONS.CONDITION_3,
                    details: I18n.t('yogas.neecha_bhanga_details.dispositor_exalted', { planet: I18n.t('planets.' + dispositor) })
                });
                totalStrength += NEECHA_BHANGA_CONDITIONS.CONDITION_3.strengthBonus;
            }

            // CONDITION 4: Debilitated planet aspected by dispositor
            if (this.aspects(dispositor, planet)) {
                conditions.push({
                    ...NEECHA_BHANGA_CONDITIONS.CONDITION_4,
                    details: I18n.t('yogas.neecha_bhanga_details.planet_aspected_by_dispositor', { planet: I18n.t('planets.' + planet), dispositor: I18n.t('planets.' + dispositor) })
                });
                totalStrength += NEECHA_BHANGA_CONDITIONS.CONDITION_4.strengthBonus;
            }

            // CONDITION 5: Conjunct an exalted planet
            for (const other of planets) {
                if (other !== planet && this.isConjunct(planet, other)) {
                    if (this._isExalted(other)) {
                        conditions.push({
                            ...NEECHA_BHANGA_CONDITIONS.CONDITION_5,
                            details: I18n.t('yogas.neecha_bhanga_details.planet_conjunct_exalted', { planet: I18n.t('planets.' + planet), other: I18n.t('planets.' + other) })
                        });
                        totalStrength += NEECHA_BHANGA_CONDITIONS.CONDITION_5.strengthBonus;
                        break;
                    }
                }
            }

            // CONDITION 6: Exalted in Navamsha
            if (this.ctx.navamshaPositions) {
                const navSign = this.ctx.navamshaPositions[planet]?.sign;
                if (navSign !== undefined && navSign === exaltationSign) {
                    conditions.push({
                        ...NEECHA_BHANGA_CONDITIONS.CONDITION_6,
                        details: I18n.t('yogas.neecha_bhanga_details.same_planet_exalted_navamsha', { planet: I18n.t('planets.' + planet) })
                    });
                    totalStrength += NEECHA_BHANGA_CONDITIONS.CONDITION_6.strengthBonus;
                }
            }

            // CONDITION 7: Dispositor aspects own sign (where debilitated planet sits)
            const dispositorHouse = this.getHouse(dispositor);
            const debPlanetHouse = this.getHouse(planet);
            if (dispositorHouse !== -1 && debPlanetHouse !== -1) {
                // Check if dispositor aspects the house where debilitated planet sits
                const aspectHouses = this._getAspectedHouses(dispositor, dispositorHouse);
                if (aspectHouses.includes(debPlanetHouse)) {
                    const alreadyHasCondition4 = conditions.some(c => c.id === 'planet_aspected_by_dispositor');
                    if (!alreadyHasCondition4) {
                        conditions.push({
                            ...NEECHA_BHANGA_CONDITIONS.CONDITION_7,
                            details: I18n.t('yogas.neecha_bhanga_details.dispositor_aspects_own_sign', { planet: I18n.t('planets.' + dispositor) })
                        });
                        totalStrength += NEECHA_BHANGA_CONDITIONS.CONDITION_7.strengthBonus;
                    }
                }
            }

            // CONDITION 8: Exchange with dispositor (Parivartana)
            const dispositorSign = this.getRasi(dispositor);
            const planetOwnSigns = OWN_SIGNS[planet] || [];
            if (planetOwnSigns.includes(dispositorSign)) {
                conditions.push({
                    ...NEECHA_BHANGA_CONDITIONS.CONDITION_8,
                    details: I18n.t('yogas.neecha_bhanga_details.exchange_with_dispositor', { planet: I18n.t('planets.' + planet), dispositor: I18n.t('planets.' + dispositor) })
                });
                totalStrength += NEECHA_BHANGA_CONDITIONS.CONDITION_8.strengthBonus;
            }

            // If any condition is met, Neecha Bhanga is formed
            if (conditions.length > 0) {
                // Advanced: Integrate Ishta Phala and Deeptadi status
                const phala = this.ctx.shadbala?.phala?.[planet];
                const netPhala = phala ? phala.net : 0;
                
                // Get Deeptadi status if available in ctx (passed from AnalysisEngine)
                const deeptadi = this.ctx.avasthas?.[planet]?.deeptadi?.state;
                
                let strength = Math.min(10, totalStrength + (netPhala / 10));
                if (deeptadi === 'DEEPTA') strength = Math.min(10, strength + 1);
                
                const conditionCount = conditions.length;

                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Neecha_Bhanga.name'),
                    nameKey: 'Neecha_Bhanga',
                    category: 'Neecha_Bhanga',
                    description: I18n.t('lists.yoga_list.Neecha_Bhanga.effects'),
                    descriptionKey: 'Neecha_Bhanga',
                    planets: [planet, dispositor],
                    nature: 'Benefic',
                    strength: strength,
                    params: {
                        planet: planet,
                        dispositor: dispositor,
                        conditionCount: conditionCount,
                        sign: I18n.t('rasis.' + RASI_NAMES[sign]),
                        isRadiant: netPhala > 15 || deeptadi === 'DEEPTA'
                    }
                }));
            }
        }
    }

    /**
     * Get houses aspected by a planet from a given house
     */
    _getAspectedHouses(planet, fromHouse) {
        const aspects = {
            Sun: [7],
            Moon: [7],
            Mars: [4, 7, 8],
            Mercury: [7],
            Jupiter: [5, 7, 9],
            Venus: [7],
            Saturn: [3, 7, 10]
        };

        const planetAspects = aspects[planet] || [7];
        return planetAspects.map(a => {
            let house = fromHouse + a - 1;
            if (house > 12) house -= 12;
            return house;
        });
    }

    /**
     * Get sign name from index
     */
    _getSignName(signIndex) {
        const names = [
            'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
            'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
        ];
        return names[signIndex] || 'Unknown';
    }
}

export default NeechaBhangaYogas;
