/**
 * ============================================================================
 * COMPREHENSIVE DHANA YOGAS - Classical Wealth Combinations
 * ============================================================================
 *
 * Dhana Yogas confer wealth, prosperity, and financial success. They are
 * formed by combinations involving 2nd (wealth), 5th (past merit), 9th (fortune),
 * 11th (gains) houses and their lords, along with natural significators.
 *
 * References:
 * - Brihat Parashara Hora Shastra (BPHS) Chapter 41
 * - Phaladeepika Chapter 7
 * - Jataka Parijata
 * - Saravali
 *
 * @module yogas/dhana_comprehensive
 * @version 1.0.0
 */

import I18n from '../../core/i18n.js';
import { YogaModuleBase, createYoga, kendras, trikonas, dusthanas, sevenPlanets } from './base.js';

/**
 * Wealth houses and their significations
 */
const WEALTH_HOUSES = [2, 5, 9, 11];
const ARTHA_TRIKONAS = [2, 6, 10]; // Material wealth axis

export class DhanaComprehensiveYogas extends YogaModuleBase {
    constructor(ctx) {
        super(ctx);
    }

    check() {
        this._checkClassicDhanaYogas();
        this._checkLordConnectionDhana();
        this._checkSpecialDhanaYogas();
        this._checkPlanetaryDhanaYogas();
        this._checkHousePlacementDhana();
        this._checkYogakaraka();
        this._checkAscendantSpecificDhana();
    }

    /**
     * Classic Dhana Yogas from BPHS and Phaladeepika
     */
    _checkClassicDhanaYogas() {
        const ctx = this.ctx;
        const lord1 = ctx.getHouseLord(1);
        const lord2 = ctx.getHouseLord(2);
        const lord5 = ctx.getHouseLord(5);
        const lord9 = ctx.getHouseLord(9);
        const lord11 = ctx.getHouseLord(11);

        // 1. Basic Dhana Yoga: 2nd and 11th lords connected
        if (this.isConnected(lord2, lord11)) {
            const house = this.getHouse(lord2);
            let strength = this._calculateDhanaStrength(lord2, lord11, house);

            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Dhana_2_11.name', { h1: I18n.n(2), h2: I18n.n(11) }),
                nameKey: 'Dhana_2_11',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Dhana_2_11.effects', {
                    planet: I18n.t('planets.' + lord2),
                    p2: I18n.t('planets.' + lord11)
                }),
                descriptionKey: 'Dhana_2_11',
                planets: [lord2, lord11],
                nature: 'Benefic',
                strength,
                params: { h1: 2, h2: 11, planet: lord2, p2: lord11, house }
            }));
        }

        // 2. Dhana Yoga: 1st and 2nd lords connected
        if (this.isConnected(lord1, lord2) && lord1 !== lord2) {
            let strength = this._calculateDhanaStrength(lord1, lord2);

            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Dhana_1_2.name', { h1: I18n.n(1), h2: I18n.n(2) }),
                nameKey: 'Dhana_1_2',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Dhana_1_2.effects', {
                    planet: I18n.t('planets.' + lord1),
                    p2: I18n.t('planets.' + lord2)
                }),
                descriptionKey: 'Dhana_1_2',
                planets: [lord1, lord2],
                nature: 'Benefic',
                strength,
                params: { h1: 1, h2: 2, planet: lord1, p2: lord2 }
            }));
        }

        // 3. Dhana Yoga: 5th and 9th lords connected (Trikona Dhana)
        if (this.isConnected(lord5, lord9)) {
            let strength = this._calculateDhanaStrength(lord5, lord9) + 1;

            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Trikona_Dhana.name', { h1: I18n.n(5), h2: I18n.n(9) }),
                nameKey: 'Trikona_Dhana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Trikona_Dhana.effects', {
                    planet: I18n.t('planets.' + lord5),
                    p2: I18n.t('planets.' + lord9)
                }),
                descriptionKey: 'Trikona_Dhana',
                planets: [lord5, lord9],
                nature: 'Benefic',
                strength: Math.min(10, strength),
                params: { h1: 5, h2: 9, planet: lord5, p2: lord9 }
            }));
        }

        // 4. Maha Dhana Yoga: 1st, 2nd, and 11th lords connected
        if (this.isConnected(lord1, lord2) && this.isConnected(lord2, lord11)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Maha_Dhana.name'),
                nameKey: 'Maha_Dhana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Maha_Dhana.effects', {
                    p1: I18n.t('planets.' + lord1),
                    p2: I18n.t('planets.' + lord2),
                    p3: I18n.t('planets.' + lord11)
                }),
                descriptionKey: 'Maha_Dhana',
                planets: [lord1, lord2, lord11],
                nature: 'Benefic',
                strength: 9,
                params: { planet: lord1, p2: lord2, p3: lord11 }
            }));
        }

        // 5. Lakshmi Yoga: 9th lord in Kendra/Trikona in dignity with strong Lagna lord
        const lord9House = this.getHouse(lord9);
        const lord9Dignity = this.getDignity(lord9);
        const goodHouses = [...kendras, ...trikonas];

        if (goodHouses.includes(lord9House) && ['Exalted', 'Own', 'Moolatrikona'].includes(lord9Dignity)) {
            if (this.isStrong(lord1)) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Lakshmi_Complete.name'),
                    nameKey: 'Lakshmi_Complete',
                    category: 'Dhana',
                    description: I18n.t('lists.yoga_list.Lakshmi_Complete.effects', {
                        planet: I18n.t('planets.' + lord9),
                        dignity: I18n.t('kundali.' + lord9Dignity.toLowerCase()),
                        house: I18n.n(lord9House)
                    }),
                    descriptionKey: 'Lakshmi_Complete',
                    planets: [lord9, lord1],
                    nature: 'Benefic',
                    strength: 9,
                    params: { planet: lord9, house: lord9House, dignity: lord9Dignity }
                }));
            }
        }
    }

    /**
     * Lord Connection Dhana Yogas - Various combinations of wealth house lords
     */
    _checkLordConnectionDhana() {
        const ctx = this.ctx;
        const lords = {};
        for (let i = 1; i <= 12; i++) {
            lords[i] = ctx.getHouseLord(i);
        }

        // 1. 2nd-5th lords connected
        if (this.isConnected(lords[2], lords[5]) && lords[2] !== lords[5]) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Dhana_2_5.name', { h1: I18n.n(2), h2: I18n.n(5) }),
                nameKey: 'Dhana_2_5',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Dhana_2_5.effects', {
                    planet: I18n.t('planets.' + lords[2]),
                    p2: I18n.t('planets.' + lords[5])
                }),
                descriptionKey: 'Dhana_2_5',
                planets: [lords[2], lords[5]],
                nature: 'Benefic',
                strength: 7,
                params: { h1: 2, h2: 5, planet: lords[2], p2: lords[5] }
            }));
        }

        // 2. 2nd-9th lords connected (Pitri Dhana)
        if (this.isConnected(lords[2], lords[9]) && lords[2] !== lords[9]) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Pitri_Dhana_Enhanced.name', { h1: I18n.n(2), h2: I18n.n(9) }),
                nameKey: 'Pitri_Dhana_Enhanced',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Pitri_Dhana_Enhanced.effects', {
                    planet: I18n.t('planets.' + lords[2]),
                    p2: I18n.t('planets.' + lords[9])
                }),
                descriptionKey: 'Pitri_Dhana_Enhanced',
                planets: [lords[2], lords[9]],
                nature: 'Benefic',
                strength: 8,
                params: { h1: 2, h2: 9, planet: lords[2], p2: lords[9] }
            }));
        }

        // 3. 5th-11th lords connected (Speculation Gains)
        if (this.isConnected(lords[5], lords[11]) && lords[5] !== lords[11]) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Labha_Dhana.name', { h1: I18n.n(5), h2: I18n.n(11) }),
                nameKey: 'Labha_Dhana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Labha_Dhana.effects', {
                    planet: I18n.t('planets.' + lords[5]),
                    p2: I18n.t('planets.' + lords[11])
                }),
                descriptionKey: 'Labha_Dhana',
                planets: [lords[5], lords[11]],
                nature: 'Benefic',
                strength: 7,
                params: { h1: 5, h2: 11, planet: lords[5], p2: lords[11] }
            }));
        }

        // 4. 9th-11th lords connected (Fortune Gains)
        if (this.isConnected(lords[9], lords[11]) && lords[9] !== lords[11]) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Bhagya_Labha.name', { h1: I18n.n(9), h2: I18n.n(11) }),
                nameKey: 'Bhagya_Labha',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Bhagya_Labha.effects', {
                    planet: I18n.t('planets.' + lords[9]),
                    p2: I18n.t('planets.' + lords[11])
                }),
                descriptionKey: 'Bhagya_Labha',
                planets: [lords[9], lords[11]],
                nature: 'Benefic',
                strength: 8,
                params: { h1: 9, h2: 11, planet: lords[9], p2: lords[11] }
            }));
        }

        // 5. 1st-5th-9th lords connected (Triple Trikona Dhana)
        if (this.isConnected(lords[1], lords[5]) && this.isConnected(lords[5], lords[9])) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Trikona_Raja_Dhana.name'),
                nameKey: 'Trikona_Raja_Dhana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Trikona_Raja_Dhana.effects', {
                    p1: I18n.t('planets.' + lords[1]),
                    p2: I18n.t('planets.' + lords[5]),
                    p3: I18n.t('planets.' + lords[9])
                }),
                descriptionKey: 'Trikona_Raja_Dhana',
                planets: [lords[1], lords[5], lords[9]],
                nature: 'Benefic',
                strength: 9,
                params: { p1: lords[1], p2: lords[5], p3: lords[9] }
            }));
        }

        // 6. 4th-9th lords connected (Property Fortune)
        if (this.isConnected(lords[4], lords[9]) && lords[4] !== lords[9]) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Bhumi_Bhagya.name', { h1: I18n.n(4), h2: I18n.n(9) }),
                nameKey: 'Bhumi_Bhagya',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Bhumi_Bhagya.effects', {
                    planet: I18n.t('planets.' + lords[4]),
                    p2: I18n.t('planets.' + lords[9])
                }),
                descriptionKey: 'Bhumi_Bhagya',
                planets: [lords[4], lords[9]],
                nature: 'Benefic',
                strength: 7,
                params: { h1: 4, h2: 9, planet: lords[4], p2: lords[9] }
            }));
        }

        // 7. 7th-11th lords connected (Partnership Gains)
        if (this.isConnected(lords[7], lords[11]) && lords[7] !== lords[11]) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vyapara_Labha.name', { h1: I18n.n(7), h2: I18n.n(11) }),
                nameKey: 'Vyapara_Labha',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Vyapara_Labha.effects', {
                    planet: I18n.t('planets.' + lords[7]),
                    p2: I18n.t('planets.' + lords[11])
                }),
                descriptionKey: 'Vyapara_Labha',
                planets: [lords[7], lords[11]],
                nature: 'Benefic',
                strength: 7,
                params: { h1: 7, h2: 11, planet: lords[7], p2: lords[11] }
            }));
        }

        // 8. 10th-11th lords connected (Career Gains)
        if (this.isConnected(lords[10], lords[11]) && lords[10] !== lords[11]) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Karma_Labha.name', { h1: I18n.n(10), h2: I18n.n(11) }),
                nameKey: 'Karma_Labha',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Karma_Labha.effects', {
                    planet: I18n.t('planets.' + lords[10]),
                    p2: I18n.t('planets.' + lords[11])
                }),
                descriptionKey: 'Karma_Labha',
                planets: [lords[10], lords[11]],
                nature: 'Benefic',
                strength: 8,
                params: { h1: 10, h2: 11, planet: lords[10], p2: lords[11] }
            }));
        }
    }

    /**
     * Special Named Dhana Yogas from classical texts
     */
    _checkSpecialDhanaYogas() {
        const ctx = this.ctx;

        // 1. Adhi Yoga: Benefics in 6th, 7th, 8th from Moon
        const benefics = this.getNaturalBenefics();
        const moonRasi = ctx.moonRasi;
        const in6 = benefics.filter(p => this.getHouse(p, moonRasi) === 6);
        const in7 = benefics.filter(p => this.getHouse(p, moonRasi) === 7);
        const in8 = benefics.filter(p => this.getHouse(p, moonRasi) === 8);

        if (in6.length > 0 && in7.length > 0 && in8.length > 0) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Adhi_Complete.name'),
                nameKey: 'Adhi_Complete',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Adhi_Complete.effects', {
                    planets: [...in6, ...in7, ...in8].map(p => I18n.t('planets.' + p)).join(', ')
                }),
                descriptionKey: 'Adhi_Complete',
                planets: [...in6, ...in7, ...in8],
                nature: 'Benefic',
                strength: 9,
                params: { planets: [...in6, ...in7, ...in8].join(', ') }
            }));
        } else if ((in6.length + in7.length + in8.length) >= 2) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Adhi_Partial.name'),
                nameKey: 'Adhi_Partial',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Adhi_Partial.effects', {
                    planets: [...in6, ...in7, ...in8].map(p => I18n.t('planets.' + p)).join(', ')
                }),
                descriptionKey: 'Adhi_Partial',
                planets: [...in6, ...in7, ...in8],
                nature: 'Benefic',
                strength: 6,
                params: { planets: [...in6, ...in7, ...in8].join(', ') }
            }));
        }

        // 2. Amala Yoga: Benefic in 10th from Lagna or Moon
        const planetsIn10 = ctx.getPlanetsInHouse(10);
        const beneficsIn10 = planetsIn10.filter(p => benefics.includes(p));

        if (beneficsIn10.length > 0) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Amala.name'),
                nameKey: 'Amala',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Amala.effects', {
                    planets: beneficsIn10.map(p => I18n.t('planets.' + p)).join(', ')
                }),
                descriptionKey: 'Amala',
                planets: beneficsIn10,
                nature: 'Benefic',
                strength: 8,
                params: { planets: beneficsIn10.join(', ') }
            }));
        }

        // 3. Vasumati Yoga: Benefics in Upachayas from Moon
        const upachayaFromMoon = [3, 6, 10, 11];
        const beneficsInUpachaya = benefics.filter(p => upachayaFromMoon.includes(this.getHouse(p, moonRasi)));

        if (beneficsInUpachaya.length >= 3) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vasumati_Strong.name'),
                nameKey: 'Vasumati_Strong',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Vasumati_Strong.effects', {
                    planets: beneficsInUpachaya.map(p => I18n.t('planets.' + p)).join(', ')
                }),
                descriptionKey: 'Vasumati_Strong',
                planets: beneficsInUpachaya,
                nature: 'Benefic',
                strength: 8,
                params: { planets: beneficsInUpachaya.join(', ') }
            }));
        }

        // 4. Dhana Karak Yoga: Jupiter in 2nd, 5th, 9th, or 11th
        const jupHouse = this.getHouse('Jupiter');
        if (WEALTH_HOUSES.includes(jupHouse) && !this.isCombust('Jupiter')) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Jupiter_Dhana.name', { house: I18n.n(jupHouse) }),
                nameKey: 'Jupiter_Dhana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Jupiter_Dhana.effects', {
                    planet: I18n.t('planets.Jupiter'),
                    house: I18n.n(jupHouse)
                }),
                descriptionKey: 'Jupiter_Dhana',
                planets: ['Jupiter'],
                nature: 'Benefic',
                strength: this.isStrong('Jupiter') ? 8 : 6,
                params: { planet: 'Jupiter', house: jupHouse }
            }));
        }

        // 5. Venus in 2nd or 11th (Luxury Wealth)
        const venHouse = this.getHouse('Venus');
        if ([2, 11].includes(venHouse) && !this.isCombust('Venus')) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Venus_Dhana.name', { house: I18n.n(venHouse) }),
                nameKey: 'Venus_Dhana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Venus_Dhana.effects', {
                    planet: I18n.t('planets.Venus'),
                    house: I18n.n(venHouse)
                }),
                descriptionKey: 'Venus_Dhana',
                planets: ['Venus'],
                nature: 'Benefic',
                strength: this.isStrong('Venus') ? 7 : 5,
                params: { planet: 'Venus', house: venHouse }
            }));
        }

        // 6. Kalanidhi Yoga: Jupiter in 2nd/5th with Mercury or Venus
        if ([2, 5].includes(jupHouse)) {
            const mercHouse = this.getHouse('Mercury');
            const venusHouse = this.getHouse('Venus');
            if (mercHouse === jupHouse || venusHouse === jupHouse) {
                const partner = mercHouse === jupHouse ? 'Mercury' : 'Venus';
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Kalanidhi.name'),
                    nameKey: 'Kalanidhi',
                    category: 'Dhana',
                    description: I18n.t('lists.yoga_list.Kalanidhi.effects', {
                        planet: I18n.t('planets.Jupiter'),
                        p2: I18n.t('planets.' + partner),
                        house: I18n.n(jupHouse)
                    }),
                    descriptionKey: 'Kalanidhi',
                    planets: ['Jupiter', partner],
                    nature: 'Benefic',
                    strength: 8,
                    params: { planet: 'Jupiter', p2: partner, house: jupHouse }
                }));
            }
        }
    }

    /**
     * Planetary Combination Dhana Yogas
     */
    _checkPlanetaryDhanaYogas() {
        const ctx = this.ctx;

        // 1. Jupiter-Venus conjunction
        if (this.isConjunct('Jupiter', 'Venus')) {
            const house = this.getHouse('Jupiter');
            let strength = 7;
            if (WEALTH_HOUSES.includes(house) || kendras.includes(house)) strength = 9;

            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Guru_Shukra_Dhana.name'),
                nameKey: 'Guru_Shukra_Dhana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Guru_Shukra_Dhana.effects', {
                    planet: I18n.t('planets.Jupiter'),
                    p2: I18n.t('planets.Venus'),
                    house: I18n.n(house)
                }),
                descriptionKey: 'Guru_Shukra_Dhana',
                planets: ['Jupiter', 'Venus'],
                nature: 'Benefic',
                strength,
                params: { planet: 'Jupiter', p2: 'Venus', house }
            }));
        }

        // 2. Mercury-Jupiter conjunction (Business Wisdom)
        if (this.isConjunct('Mercury', 'Jupiter')) {
            const house = this.getHouse('Mercury');
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Budha_Guru_Dhana.name'),
                nameKey: 'Budha_Guru_Dhana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Budha_Guru_Dhana.effects', {
                    planet: I18n.t('planets.Mercury'),
                    p2: I18n.t('planets.Jupiter'),
                    house: I18n.n(house)
                }),
                descriptionKey: 'Budha_Guru_Dhana',
                planets: ['Mercury', 'Jupiter'],
                nature: 'Benefic',
                strength: 7,
                params: { planet: 'Mercury', p2: 'Jupiter', house }
            }));
        }

        // 3. Moon-Venus conjunction in wealth houses
        if (this.isConjunct('Moon', 'Venus')) {
            const house = this.getHouse('Moon');
            if (WEALTH_HOUSES.includes(house) || house === 4) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Chandra_Shukra_Dhana.name'),
                    nameKey: 'Chandra_Shukra_Dhana',
                    category: 'Dhana',
                    description: I18n.t('lists.yoga_list.Chandra_Shukra_Dhana.effects', {
                        planet: I18n.t('planets.Moon'),
                        p2: I18n.t('planets.Venus'),
                        house: I18n.n(house)
                    }),
                    descriptionKey: 'Chandra_Shukra_Dhana',
                    planets: ['Moon', 'Venus'],
                    nature: 'Benefic',
                    strength: 7,
                    params: { planet: 'Moon', p2: 'Venus', house }
                }));
            }
        }

        // 4. Sun-Mercury in 2nd, 10th, or 11th
        if (this.isConjunct('Sun', 'Mercury')) {
            const house = this.getHouse('Sun');
            if ([2, 10, 11].includes(house) && !this.isCombust('Mercury')) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Budhaditya_Dhana.name'),
                    nameKey: 'Budhaditya_Dhana',
                    category: 'Dhana',
                    description: I18n.t('lists.yoga_list.Budhaditya_Dhana.effects', {
                        planet: I18n.t('planets.Sun'),
                        p2: I18n.t('planets.Mercury'),
                        house: I18n.n(house)
                    }),
                    descriptionKey: 'Budhaditya_Dhana',
                    planets: ['Sun', 'Mercury'],
                    nature: 'Benefic',
                    strength: 6,
                    params: { planet: 'Sun', p2: 'Mercury', house }
                }));
            }
        }

        // 5. Saturn-Mercury conjunction (Business Discipline)
        if (this.isConjunct('Saturn', 'Mercury')) {
            const house = this.getHouse('Saturn');
            if ([2, 6, 10, 11].includes(house)) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Shani_Budha_Dhana.name'),
                    nameKey: 'Shani_Budha_Dhana',
                    category: 'Dhana',
                    description: I18n.t('lists.yoga_list.Shani_Budha_Dhana.effects', {
                        planet: I18n.t('planets.Saturn'),
                        p2: I18n.t('planets.Mercury'),
                        house: I18n.n(house)
                    }),
                    descriptionKey: 'Shani_Budha_Dhana',
                    planets: ['Saturn', 'Mercury'],
                    nature: 'Benefic',
                    strength: 6,
                    params: { planet: 'Saturn', p2: 'Mercury', house }
                }));
            }
        }
    }

    /**
     * House Placement Dhana Yogas
     */
    _checkHousePlacementDhana() {
        const ctx = this.ctx;

        // 1. All wealth house lords in Kendras
        const lord2 = ctx.getHouseLord(2);
        const lord5 = ctx.getHouseLord(5);
        const lord9 = ctx.getHouseLord(9);
        const lord11 = ctx.getHouseLord(11);
        const lord2House = this.getHouse(lord2);
        const lord11House = this.getHouse(lord11);

        const wealthLordsInKendra = [lord2, lord5, lord9, lord11].filter(l =>
            kendras.includes(this.getHouse(l))
        );

        if (wealthLordsInKendra.length >= 3) {
            const planetNames = [...new Set(wealthLordsInKendra)].map(p => I18n.t('planets.' + p)).join(', ');
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Kendra_Sthiti_Dhana.name'),
                nameKey: 'Kendra_Sthiti_Dhana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Kendra_Sthiti_Dhana.effects', {
                    planets: planetNames
                }),
                descriptionKey: 'Kendra_Sthiti_Dhana',
                planets: [...new Set(wealthLordsInKendra)],
                nature: 'Benefic',
                strength: 8,
                params: { planets: [...new Set(wealthLordsInKendra)].join(', ') }
            }));
        }

        // 2. 2nd lord in 11th and vice versa
        if (lord2House === 11 && lord11House === 2 && lord2 !== lord11) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Dhana_Parivartana.name', { h1: I18n.n(2), h2: I18n.n(11) }),
                nameKey: 'Dhana_Parivartana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Dhana_Parivartana.effects', {
                    planet: I18n.t('planets.' + lord2),
                    p2: I18n.t('planets.' + lord11)
                }),
                descriptionKey: 'Dhana_Parivartana',
                planets: [lord2, lord11],
                nature: 'Benefic',
                strength: 9,
                params: { h1: 2, h2: 11, planet: lord2, p2: lord11 }
            }));
        }

        // 3. Benefics in 2nd and 11th together
        const benefics = this.getNaturalBenefics();
        const beneficsIn2 = benefics.filter(p => this.getHouse(p) === 2);
        const beneficsIn11 = benefics.filter(p => this.getHouse(p) === 11);

        if (beneficsIn2.length > 0 && beneficsIn11.length > 0) {
            const planetNames = [...beneficsIn2, ...beneficsIn11].map(p => I18n.t('planets.' + p)).join(', ');
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Shubha_Dhana.name'),
                nameKey: 'Shubha_Dhana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Shubha_Dhana.effects', {
                    planets: planetNames
                }),
                descriptionKey: 'Shubha_Dhana',
                planets: [...beneficsIn2, ...beneficsIn11],
                nature: 'Benefic',
                strength: 8,
                params: { planets: [...beneficsIn2, ...beneficsIn11].join(', ') }
            }));
        }

        // 4. 9th lord in 9th (Bhagyasthan)
        const lord9House = this.getHouse(lord9);
        if (lord9House === 9) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Bhagya_Sthana.name'),
                nameKey: 'Bhagya_Sthana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Bhagya_Sthana.effects', {
                    planet: I18n.t('planets.' + lord9)
                }),
                descriptionKey: 'Bhagya_Sthana',
                planets: [lord9],
                nature: 'Benefic',
                strength: 8,
                params: { planet: lord9, house: 9 }
            }));
        }

        // 5. 11th lord in 11th (Labha Sthana)
        if (lord11House === 11) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Labha_Sthana.name'),
                nameKey: 'Labha_Sthana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Labha_Sthana.effects', {
                    planet: I18n.t('planets.' + lord11)
                }),
                descriptionKey: 'Labha_Sthana',
                planets: [lord11],
                nature: 'Benefic',
                strength: 8,
                params: { planet: lord11, house: 11 }
            }));
        }
    }

    /**
     * Yogakaraka Dhana effects
     */
    _checkYogakaraka() {
        const ctx = this.ctx;
        const lagnaSign = ctx.lagnaRasi !== undefined ? ctx.lagnaRasi : -1;
        if (lagnaSign === -1) return;

        let yogakaraka = null;
        // Taurus/Libra: Saturn (9th and 10th for Taurus, 4th and 5th for Libra)
        // Cancer/Leo: Mars (5th and 10th for Cancer, 4th and 9th for Leo)
        if (lagnaSign === 1) yogakaraka = 'Saturn'; // Taurus
        else if (lagnaSign === 6) yogakaraka = 'Saturn'; // Libra
        else if (lagnaSign === 3) yogakaraka = 'Mars'; // Cancer
        else if (lagnaSign === 4) yogakaraka = 'Mars'; // Leo

        if (yogakaraka) {
            const ykHouse = this.getHouse(yogakaraka);
            if (WEALTH_HOUSES.includes(ykHouse) || kendras.includes(ykHouse)) {
                const ykDignity = this.getDignity(yogakaraka);
                let strength = 7;
                if (['Exalted', 'Own', 'Moolatrikona'].includes(ykDignity)) strength = 9;

                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Yogakaraka_Dhana.name'),
                    nameKey: 'Yogakaraka_Dhana',
                    category: 'Dhana',
                    description: I18n.t('lists.yoga_list.Yogakaraka_Dhana.effects', {
                        planet: I18n.t('planets.' + yogakaraka),
                        house: I18n.n(ykHouse),
                        dignity: I18n.t('kundali.' + ykDignity.toLowerCase())
                    }),
                    descriptionKey: 'Yogakaraka_Dhana',
                    planets: [yogakaraka],
                    nature: 'Benefic',
                    strength,
                    params: { planet: yogakaraka, house: ykHouse, dignity: ykDignity }
                }));
            }
        }
    }

    /**
     * Ascendant-specific Dhana Yogas
     */
    _checkAscendantSpecificDhana() {
        const ctx = this.ctx;
        const lagnaSign = ctx.lagnaRasi !== undefined ? ctx.lagnaRasi : -1;
        if (lagnaSign === -1) return;

        const rasiNames = ['Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
            'Tula', 'Vrishchika', 'Dhanu', 'Makara', 'Kumbha', 'Meena'];

        // Check for specific favorable planet placements based on ascendant
        const dhanaKarakas = {
            0: ['Jupiter', 'Sun'], // Aries
            1: ['Saturn', 'Mercury'], // Taurus
            2: ['Venus', 'Mercury'], // Gemini
            3: ['Mars', 'Jupiter'], // Cancer
            4: ['Mars', 'Sun'], // Leo
            5: ['Mercury', 'Venus'], // Virgo
            6: ['Saturn', 'Venus'], // Libra
            7: ['Jupiter', 'Moon'], // Scorpio
            8: ['Jupiter', 'Sun'], // Sagittarius
            9: ['Saturn', 'Venus'], // Capricorn
            10: ['Saturn', 'Venus'], // Aquarius
            11: ['Jupiter', 'Moon'] // Pisces
        };

        const karakas = dhanaKarakas[lagnaSign] || [];

        for (const karak of karakas) {
            const karakHouse = this.getHouse(karak);
            if (WEALTH_HOUSES.includes(karakHouse) && this.isStrong(karak)) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Ascendant_Dhana.name'),
                    nameKey: 'Ascendant_Dhana',
                    category: 'Dhana',
                    description: I18n.t('lists.yoga_list.Ascendant_Dhana.effects', {
                        planet: I18n.t('planets.' + karak),
                        house: I18n.n(karakHouse),
                        ref: I18n.t('rasis.' + rasiNames[lagnaSign])
                    }),
                    descriptionKey: 'Ascendant_Dhana',
                    planets: [karak],
                    nature: 'Benefic',
                    strength: 7,
                    params: { planet: karak, house: karakHouse, ref: rasiNames[lagnaSign] }
                }));
                break; // Only report one per ascendant
            }
        }
    }

    /**
     * Calculate Dhana Yoga strength
     */
    _calculateDhanaStrength(planet1, planet2, house = null) {
        let strength = 5;

        // House placement bonus
        if (house) {
            if (WEALTH_HOUSES.includes(house)) strength += 1.5;
            else if (kendras.includes(house)) strength += 1;
            else if (dusthanas.includes(house)) strength -= 1;
        }

        // Dignity bonuses
        const dig1 = this.getDignity(planet1);
        const dig2 = planet2 ? this.getDignity(planet2) : null;

        if (dig1 === 'Exalted') strength += 1.5;
        else if (dig1 === 'Own' || dig1 === 'Moolatrikona') strength += 1;
        else if (dig1 === 'Debilitated') strength -= 1;

        if (dig2) {
            if (dig2 === 'Exalted') strength += 1.5;
            else if (dig2 === 'Own' || dig2 === 'Moolatrikona') strength += 1;
            else if (dig2 === 'Debilitated') strength -= 1;
        }

        // Combustion penalty
        if (this.isCombust(planet1)) strength -= 0.5;
        if (planet2 && this.isCombust(planet2)) strength -= 0.5;

        // Jupiter aspect bonus
        if (this.aspects('Jupiter', planet1)) strength += 0.5;
        if (planet2 && this.aspects('Jupiter', planet2)) strength += 0.5;

        return Math.max(3, Math.min(10, strength));
    }
}

export default DhanaComprehensiveYogas;
