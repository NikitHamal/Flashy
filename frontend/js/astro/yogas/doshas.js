/**
 * Dosha Yogas Module
 * Implements malefic combinations, afflictions, and doshas
 */

import I18n from '../../core/i18n.js';
import { YogaModuleBase, createYoga, kendras, dusthanas, sevenPlanets } from './base.js';

export class DoshaYogas extends YogaModuleBase {
    check() {
        this._checkManglikDosha();
        this._checkPitruDosha();
        this._checkMatruDosha();
        this._checkShrapitDosha();
        this._checkAngarakYoga();
        this._checkVishYoga();
        this._checkDaridrYoga();
        this._checkDurYoga();
        this._checkKemadrumaVariations();
        this._checkPitraSharepaYoga();
        this._checkBandhanYoga();
        this._checkPapaKartariYoga();
        this._checkGrahanDosha();
        this._checkPutraDosha();
        this._checkSakataYoga();
    }

    /**
     * Sakata Yoga
     * Moon in 6th, 8th, or 12th from Jupiter
     * Effect: Cycles of fortune and misfortune
     */
    _checkSakataYoga() {
        const moonHouse = this.getHouse('Moon');
        const jupHouse = this.getHouse('Jupiter');
        
        if (moonHouse === -1 || jupHouse === -1) return;

        // Calculate Moon's position relative to Jupiter
        // 6th, 8th, 12th from Jupiter
        let relPos = moonHouse - jupHouse + 1;
        if (relPos <= 0) relPos += 12;

        if ([6, 8, 12].includes(relPos)) {
            // Check for Cancellation (Bhanga)
            // 1. Moon in Kendra from Lagna
            if (kendras.includes(moonHouse)) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Sakata_Bhanga.name'),
                    nameKey: 'Sakata_Bhanga',
                    category: 'Dosha',
                    description: I18n.t('lists.yoga_list.Sakata_Bhanga.effects'),
                    descriptionKey: 'Sakata_Bhanga',
                    planets: ['Moon', 'Jupiter'],
                    nature: 'Neutral',
                    strength: 5,
                    params: { reason: 'Moon in Kendra' }
                }));
            } else {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Sakata.name'),
                    nameKey: 'Sakata',
                    category: 'Dosha',
                    description: I18n.t('lists.yoga_list.Sakata.effects'),
                    descriptionKey: 'Sakata',
                    planets: ['Moon', 'Jupiter'],
                    nature: 'Malefic',
                    strength: 4
                }));
            }
        }
    }

    /**
     * Manglik/Kuja Dosha
     * Mars in 1st, 2nd, 4th, 7th, 8th, 12th from Lagna/Moon/Venus
     */
    _checkManglikDosha() {
        const manglikHouses = [1, 2, 4, 7, 8, 12];
        const references = [
            { ref: this.ctx.lagnaRasi, name: 'Lagna', nameKey: 'Lagna' },
            { ref: this.ctx.moonRasi, name: 'Moon', nameKey: 'Moon' },
            { ref: this.getRasi('Venus'), name: 'Venus', nameKey: 'Venus' }
        ];

        for (const { ref, name, nameKey } of references) {
            if (ref === -1) continue;

            const marsHouse = this.getHouse('Mars', ref);
            if (manglikHouses.includes(marsHouse)) {
                // Check for cancellation conditions
                const cancellations = this._getManglikCancellations(marsHouse, ref);

                const localizedRef = I18n.t(`matching.${nameKey.toLowerCase()}`) || name;

                if (cancellations.length > 0) {
                    this.addYoga(createYoga({
                        name: I18n.t('lists.yoga_list.Manglik_Cancelled.name', { ref: localizedRef }),
                        nameKey: 'Manglik_Cancelled',
                        category: 'Dosha',
                        description: I18n.t('lists.yoga_list.Manglik_Cancelled.effects', { house: I18n.n(marsHouse), ref: localizedRef }),
                        descriptionKey: 'Manglik_Cancelled',
                        params: { ref: name, house: marsHouse },
                        planets: ['Mars'],
                        nature: 'Neutral',
                        strength: 5
                    }));
                } else {
                    const intensity = this._getManglikIntensity(marsHouse);
                    this.addYoga(createYoga({
                        name: I18n.t('lists.yoga_list.Manglik.name', { ref: localizedRef }),
                        nameKey: 'Manglik',
                        category: 'Dosha',
                        description: I18n.t('lists.yoga_list.Manglik.effects', { house: I18n.n(marsHouse), ref: localizedRef }),
                        descriptionKey: 'Manglik',
                        params: { ref: name, house: marsHouse },
                        planets: ['Mars'],
                        nature: 'Malefic',
                        strength: intensity.strength
                    }));
                }
            }
        }
    }

    /**
     * Get Manglik cancellation conditions
     */
    _getManglikCancellations(house, ref) {
        const cancellations = [];
        const marsDignity = this.getDignity('Mars');

        // Mars in own sign
        if (['Own', 'Moolatrikona'].includes(marsDignity)) {
            cancellations.push('Mars in own sign');
        }

        // Mars exalted
        if (marsDignity === 'Exalted') {
            cancellations.push('Mars exalted');
        }

        // Jupiter aspects Mars
        if (this.aspects('Jupiter', 'Mars')) {
            cancellations.push('Jupiter aspects Mars');
        }

        // Mars conjunct Jupiter
        if (this.isConjunct('Mars', 'Jupiter')) {
            cancellations.push('Mars conjunct Jupiter');
        }

        // Mars conjunct benefic Venus or Moon
        if (this.isConjunct('Mars', 'Venus')) {
            cancellations.push('Mars conjunct Venus');
        }

        // Specific house exceptions
        if (house === 2 && ['Gemini', 'Virgo'].includes(this._getSignName(ref + house - 1))) {
            cancellations.push('Mars in 2nd in Mercury sign');
        }

        return cancellations;
    }

    /**
     * Get intensity of Manglik based on house
     */
    _getManglikIntensity(house) {
        const intensities = {
            1: { desc: 'Mild - affects health and temperament.', strength: 3 },
            2: { desc: 'Moderate - affects family and speech.', strength: 4 },
            4: { desc: 'High - affects domestic peace and property.', strength: 5 },
            7: { desc: 'Very High - directly affects marriage and spouse.', strength: 6 },
            8: { desc: 'High - affects longevity and in-laws.', strength: 5 },
            12: { desc: 'Moderate - affects bedroom affairs and expenses.', strength: 4 }
        };
        return intensities[house] || { desc: 'Unknown placement.', strength: 3 };
    }

    /**
     * Get sign name from index
     */
    _getSignName(index) {
        const signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
            'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
        return signs[(index + 12) % 12];
    }

    /**
     * Pitru Dosha
     * Sun afflicted by Saturn/Rahu/Ketu in specific houses
     */
    _checkPitruDosha() {
        const sunHouse = this.getHouse('Sun');
        const afflictedHouses = [1, 5, 9, 10]; // Key houses for father/authority

        if (!afflictedHouses.includes(sunHouse)) return;

        const afflictions = [];

        if (this.isConjunct('Sun', 'Saturn')) afflictions.push('Saturn');
        if (this.isConjunct('Sun', 'Rahu')) afflictions.push('Rahu');
        if (this.isConjunct('Sun', 'Ketu')) afflictions.push('Ketu');
        if (this.aspects('Saturn', 'Sun')) afflictions.push('Saturn');
        if (this.aspects('Rahu', 'Sun')) afflictions.push('Rahu');

        if (afflictions.length > 0) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Pitru_Dosha.name'),
                nameKey: 'Pitru_Dosha',
                category: 'Dosha',
                description: I18n.t('lists.yoga_list.Pitru_Dosha.effects', { house: I18n.n(sunHouse) }),
                descriptionKey: 'Pitru_Dosha',
                planets: ['Sun', ...new Set(afflictions)],
                nature: 'Malefic',
                strength: 4,
                params: { house: sunHouse }
            }));
        }
    }

    /**
     * Matru Dosha
     * Moon afflicted in 4th house
     */
    _checkMatruDosha() {
        const moonHouse = this.getHouse('Moon');
        if (moonHouse !== 4) return;

        const afflictions = [];
        const malefics = this.getNaturalMalefics();

        for (const mal of malefics) {
            if (mal === 'Moon') continue;
            if (this.isConnected('Moon', mal)) {
                afflictions.push(mal);
            }
        }

        if (afflictions.length > 0) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Matru_Dosha.name'),
                nameKey: 'Matru_Dosha',
                category: 'Dosha',
                description: I18n.t('lists.yoga_list.Matru_Dosha.effects'),
                descriptionKey: 'Matru_Dosha',
                planets: ['Moon', ...afflictions],
                nature: 'Malefic',
                strength: 4
            }));
        }
    }

    /**
     * Shrapit/Shapit Dosha
     * Saturn-Rahu conjunction
     */
    _checkShrapitDosha() {
        if (this.isConjunct('Saturn', 'Rahu')) {
            const house = this.getHouse('Saturn');
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Shrapit.name'),
                nameKey: 'Shrapit',
                category: 'Dosha',
                description: I18n.t('lists.yoga_list.Shrapit.effects', { house: I18n.n(house) }),
                descriptionKey: 'Shrapit',
                planets: ['Saturn', 'Rahu'],
                nature: 'Malefic',
                strength: 5,
                params: { house }
            }));
        }
    }

    /**
     * Angarak Yoga/Dosha
     * Mars-Rahu conjunction
     */
    _checkAngarakYoga() {
        if (this.isConjunct('Mars', 'Rahu')) {
            const house = this.getHouse('Mars');
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Angarak.name'),
                nameKey: 'Angarak',
                category: 'Dosha',
                description: I18n.t('lists.yoga_list.Angarak.effects', { house: I18n.n(house) }),
                descriptionKey: 'Angarak',
                planets: ['Mars', 'Rahu'],
                nature: 'Malefic',
                strength: 5,
                params: { house }
            }));
        }
    }

    /**
     * Vish Yoga (Poison)
     * Saturn-Moon conjunction
     */
    _checkVishYoga() {
        if (this.isConjunct('Saturn', 'Moon')) {
            const moonDignity = this.getDignity('Moon');
            const isWaxing = this.isWaxingMoon();

            let nature = 'Malefic';
            let strength = 5;

            // Modifications based on Moon strength
            if (['Exalted', 'Own'].includes(moonDignity)) {
                nature = 'Neutral';
                strength = 3;
            } else if (isWaxing) {
                strength = 4;
            }

            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vish.name'),
                nameKey: 'Vish',
                category: 'Dosha',
                description: I18n.t('lists.yoga_list.Vish.effects'),
                descriptionKey: 'Vish',
                planets: ['Saturn', 'Moon'],
                nature,
                strength
            }));
        }
    }

    /**
     * Daridra Yoga (Poverty)
     * Lords of 11th in 6th/8th/12th, weak
     */
    _checkDaridrYoga() {
        const lord11 = this.getHouseLord(11);
        const lord11House = this.getHouse(lord11);

        if (dusthanas.includes(lord11House) && !this.isStrong(lord11)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Daridra.name'),
                nameKey: 'Daridra',
                category: 'Dosha',
                description: I18n.t('lists.yoga_list.Daridra.effects', { house: I18n.n(lord11House) }),
                descriptionKey: 'Daridra',
                planets: [lord11],
                nature: 'Malefic',
                strength: 3,
                params: { house: lord11House }
            }));
        }
    }

    /**
     * Dur Yoga
     * Moon in 6th, 8th, or 12th, afflicted
     */
    _checkDurYoga() {
        const moonHouse = this.getHouse('Moon');
        if (!dusthanas.includes(moonHouse)) return;

        const malefics = this.getNaturalMalefics().filter(p => p !== 'Moon');
        const afflicted = malefics.some(m => this.isConnected('Moon', m));

        if (afflicted) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Dur.name'),
                nameKey: 'Dur',
                category: 'Dosha',
                description: I18n.t('lists.yoga_list.Dur.effects', { house: I18n.n(moonHouse) }),
                descriptionKey: 'Dur',
                planets: ['Moon'],
                nature: 'Malefic',
                strength: 3,
                params: { house: moonHouse }
            }));
        }
    }

    /**
     * Kemadruma variations and cancellations
     */
    _checkKemadrumaVariations() {
        const moonSign = this.ctx.moonRasi;
        const planetsIn2nd = this.getPlanetsInHouse(2, moonSign).filter(p => p !== 'Moon' && p !== 'Sun');
        const planetsIn12th = this.getPlanetsInHouse(12, moonSign).filter(p => p !== 'Moon' && p !== 'Sun');

        // Only check if basic Kemadruma exists (no planets in 2nd/12th from Moon)
        if (planetsIn2nd.length > 0 || planetsIn12th.length > 0) return;

        // List all possible cancellations beyond basic ones
        const cancellations = [];

        // Moon in Kendra from Lagna
        if (kendras.includes(this.getHouse('Moon'))) cancellations.push('Moon in Kendra');
        // Venus in Kendra from Moon
        if (kendras.includes(this.getHouse('Venus', moonSign))) cancellations.push('Venus in Kendra');
        // Jupiter in Kendra from Lagna
        if (kendras.includes(this.getHouse('Jupiter'))) cancellations.push('Jupiter in Kendra');

        // Strong Moon (Full Moon)
        const moonLon = this.getLongitude('Moon');
        const sunLon = this.getLongitude('Sun');
        const phase = (moonLon - sunLon + 360) % 360;
        if (phase > 170 && phase < 190) {
            cancellations.push('Full Moon');
        }

        // Moon in own or exalted sign
        const moonDig = this.getDignity('Moon');
        if (['Exalted', 'Own'].includes(moonDig)) {
            cancellations.push(moonDig);
        }

        if (cancellations.length >= 2) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Kemadruma_Bhanga_Multiple.name'),
                nameKey: 'Kemadruma_Bhanga_Multiple',
                category: 'Dosha',
                description: I18n.t('lists.yoga_list.Kemadruma_Bhanga_Multiple.effects'),
                descriptionKey: 'Kemadruma_Bhanga_Multiple',
                planets: ['Moon'],
                nature: 'Neutral',
                strength: 6
            }));
        }
    }

    /**
     * Pitra Shapa Yoga (Ancestral Curse)
     * 9th house/lord severely afflicted
     */
    _checkPitraSharepaYoga() {
        const lord9 = this.getHouseLord(9);
        const lord9House = this.getHouse(lord9);
        const planetsIn9 = this.getPlanetsInHouse(9);

        const malefics = this.getNaturalMalefics();
        let afflictionCount = 0;

        // Check afflictions to 9th house
        const maleficsIn9 = planetsIn9.filter(p => malefics.includes(p));
        afflictionCount += maleficsIn9.length;

        // Check afflictions to 9th lord
        if (dusthanas.includes(lord9House)) afflictionCount++;
        if (this.getDignity(lord9) === 'Debilitated') afflictionCount++;
        for (const mal of malefics) {
            if (this.isConnected(lord9, mal)) afflictionCount++;
        }

        if (afflictionCount >= 3) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Pitra_Shapa.name'),
                nameKey: 'Pitra_Shapa',
                category: 'Dosha',
                description: I18n.t('lists.yoga_list.Pitra_Shapa.effects'),
                descriptionKey: 'Pitra_Shapa',
                planets: [lord9, ...maleficsIn9],
                nature: 'Malefic',
                strength: 4
            }));
        }
    }

    /**
     * Bandhan Yoga (Imprisonment)
     * All malefics in Kendras, Lagna aspected by malefic
     */
    _checkBandhanYoga() {
        const malefics = this.getNaturalMalefics();
        const maleficsInKendras = malefics.filter(p => kendras.includes(this.getHouse(p)));

        const lagnaAspectedByMalefic = malefics.some(m => this.aspects(m, this.getHouseLord(1)));

        if (maleficsInKendras.length >= 3 && lagnaAspectedByMalefic) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Bandhan.name'),
                nameKey: 'Bandhan',
                category: 'Dosha',
                description: I18n.t('lists.yoga_list.Bandhan.effects'),
                descriptionKey: 'Bandhan',
                planets: maleficsInKendras,
                nature: 'Malefic',
                strength: 4
            }));
        }
    }

    /**
     * Papa Kartari Yoga
     * House hemmed by malefics (for key houses)
     */
    _checkPapaKartariYoga() {
        const malefics = this.getNaturalMalefics();
        const maleficHouses = new Set(malefics.map(p => this.getHouse(p)).filter(h => h !== -1));

        const keyHouses = [1, 2, 4, 5, 7, 9, 10];

        for (const house of keyHouses) {
            const prev = house === 1 ? 12 : house - 1;
            const next = house === 12 ? 1 : house + 1;

            if (maleficHouses.has(prev) && maleficHouses.has(next)) {
                const planetsInHouse = this.getPlanetsInHouse(house);
                const hasBenefics = planetsInHouse.some(p => this.getNaturalBenefics().includes(p));

                if (!hasBenefics) {
                    this.addYoga(createYoga({
                        name: I18n.t('lists.yoga_list.Papa_Kartari.name', { house: I18n.n(house) }),
                        nameKey: 'Papa_Kartari',
                        category: 'Dosha',
                        description: I18n.t('lists.yoga_list.Papa_Kartari.effects', { house: I18n.n(house) }),
                        descriptionKey: 'Papa_Kartari',
                        planets: [...malefics.filter(p => [prev, next].includes(this.getHouse(p)))],
                        nature: 'Malefic',
                        strength: 4,
                        params: { house }
                    }));
                }
            }
        }
    }

    /**
     * Grahan Dosha (Eclipse)
     * Sun/Moon closely conjunct Rahu/Ketu
     */
    _checkGrahanDosha() {
        const checkEclipse = (luminary, node) => {
            if (!this.isConjunct(luminary, node)) return false;
            const diff = Math.abs(this.getLongitude(luminary) - this.getLongitude(node));
            return (diff > 180 ? 360 - diff : diff) < 10;
        };

        if (checkEclipse('Sun', 'Rahu')) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Grahan_Solar.name'),
                nameKey: 'Grahan_Solar',
                category: 'Dosha',
                description: I18n.t('lists.yoga_list.Grahan_Solar.effects'),
                descriptionKey: 'Grahan_Solar',
                planets: ['Sun', 'Rahu'],
                nature: 'Malefic',
                strength: 5
            }));
        }

        if (checkEclipse('Moon', 'Rahu')) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Grahan_Lunar_Rahu.name'),
                nameKey: 'Grahan_Lunar_Rahu',
                category: 'Dosha',
                description: I18n.t('lists.yoga_list.Grahan_Lunar_Rahu.effects'),
                descriptionKey: 'Grahan_Lunar_Rahu',
                planets: ['Moon', 'Rahu'],
                nature: 'Malefic',
                strength: 5
            }));
        }

        if (checkEclipse('Moon', 'Ketu')) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Grahan_Lunar_Ketu.name'),
                nameKey: 'Grahan_Lunar_Ketu',
                category: 'Dosha',
                description: I18n.t('lists.yoga_list.Grahan_Lunar_Ketu.effects'),
                descriptionKey: 'Grahan_Lunar_Ketu',
                planets: ['Moon', 'Ketu'],
                nature: 'Neutral',
                strength: 4
            }));
        }
    }

    /**
     * Putra Dosha (Children affliction)
     * 5th house/lord affliction
     */
    _checkPutraDosha() {
        const lord5 = this.getHouseLord(5);
        const lord5House = this.getHouse(lord5);
        const planetsIn5 = this.getPlanetsInHouse(5);

        const malefics = this.getNaturalMalefics();
        let afflictionCount = 0;

        const maleficsIn5 = planetsIn5.filter(p => malefics.includes(p));
        afflictionCount += maleficsIn5.length;

        if (dusthanas.includes(lord5House)) afflictionCount++;
        if (this.getDignity(lord5) === 'Debilitated') afflictionCount++;
        
        const jupAfflicted = malefics.some(m => m !== 'Jupiter' && this.isConnected('Jupiter', m));
        if (jupAfflicted) afflictionCount++;

        if (afflictionCount >= 2) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Putra_Dosha.name'),
                nameKey: 'Putra_Dosha',
                category: 'Dosha',
                description: I18n.t('lists.yoga_list.Putra_Dosha.effects'),
                descriptionKey: 'Putra_Dosha',
                planets: [lord5, ...maleficsIn5],
                nature: 'Malefic',
                strength: 4
            }));
        }
    }
}

export default DoshaYogas;
