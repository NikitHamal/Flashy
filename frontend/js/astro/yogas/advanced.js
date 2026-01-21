/**
 * ============================================================================
 * ADVANCED YOGAS - Rare and Classical Planetary Combinations
 * ============================================================================
 *
 * This module implements advanced yogas from classical texts including:
 * - Rare Raja Yogas
 * - Nabhas Asamanya Yogas
 * - Special Moon-based Yogas
 * - Combustion and Retrogression Yogas
 * - Gandanta and Sandhi Yogas
 *
 * References:
 * - Brihat Parashara Hora Shastra (BPHS) Chapters 35-41
 * - Phaladeepika
 * - Saravali
 * - Jataka Parijata
 *
 * @module yogas/advanced
 * @version 1.0.0
 */

import I18n from '../../core/i18n.js';
import { YogaModuleBase, createYoga, kendras, trikonas, dusthanas, upachayas } from './base.js';

/**
 * Advanced Yogas Module
 */
export class AdvancedYogas extends YogaModuleBase {
    constructor(ctx) {
        super(ctx);
    }

    check() {
        this._checkRareRajaYogas();
        this._checkChandraYogas();
        this._checkSuryaYogas();
        this._checkSpecialCombustionYogas();
        this._checkRetrogressionYogas();
        this._checkGandantaYogas();
        this._checkNavamshaYogas();
        this._checkAshtakavargaYogas();
    }

    // ========================================================================
    // RARE RAJA YOGAS
    // ========================================================================

    _checkRareRajaYogas() {
        const ctx = this.ctx;

        // 1. Yukta Yoga - Lord of 10th conjunct lord of Lagna
        const lord1 = ctx.getHouseLord(1);
        const lord10 = ctx.getHouseLord(10);
        if (ctx.isConjunct(lord1, lord10)) {
            const house = ctx.getHouse(lord1);
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Yukta.name'),
                nameKey: 'Yukta',
                category: 'Raja',
                description: I18n.t('lists.yoga_list.Yukta.effects'),
                descriptionKey: 'Yukta',
                planets: [lord1, lord10],
                nature: 'Benefic',
                strength: ctx.getStrength([lord1, lord10]) + 1
            }));
        }

        // 2. Malika Yoga - All planets in consecutive houses
        this._checkMalikaYoga();

        // 3. Sankhya Shakata Yoga - Moon in 6th, 8th, or 12th from Jupiter
        const moonHouseFromJup = ctx.getHouse('Moon', ctx.getRasi('Jupiter'));
        if ([6, 8, 12].includes(moonHouseFromJup)) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Shakata.name'),
                nameKey: 'Shakata',
                category: 'Lunar',
                description: I18n.t('lists.yoga_list.Shakata.effects', { house: I18n.n(moonHouseFromJup), planet: I18n.t('planets.Moon') }),
                descriptionKey: 'Shakata',
                planets: ['Moon', 'Jupiter'],
                nature: 'Malefic',
                strength: 4,
                params: { planet: 'Moon' }
            }));
        }

        // 4. Amala Yoga
        this._checkAmalaYoga();

        // 5. Pushkala Yoga
        this._checkPushkalaYoga();

        // 6. Kalpadruma Yoga
        this._checkKalpadrumaYoga();

        // 7. Amsavatara Yoga
        this._checkAmsavataraYoga();

        // 8. Devendra Yoga
        this._checkDevendraYoga();

        // 9. Indra Yoga
        this._checkIndraYoga();

        // 10. Subha Yoga
        this._checkSubhaYoga();
    }

    _checkMalikaYoga() {
        const ctx = this.ctx;
        const sevenPlanetsList = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];

        const occupiedHouses = new Set();
        for (const planet of sevenPlanetsList) {
            const house = ctx.getHouse(planet);
            if (house > 0) occupiedHouses.add(house);
        }

        const houses = Array.from(occupiedHouses).sort((a, b) => a - b);
        if (houses.length >= 7) {
            for (let start = 1; start <= 6; start++) {
                const consecutive = [];
                for (let h = start; h < start + 7; h++) {
                    const checkHouse = ((h - 1) % 12) + 1;
                    if (occupiedHouses.has(checkHouse)) {
                        consecutive.push(checkHouse);
                    }
                }
                if (consecutive.length === 7) {
                    const name = this._getMalikaName(consecutive[0]);
                    const key = `Malika_${name}`;
                    ctx.addYoga(createYoga({
                        name: I18n.t(`lists.yoga_list.${key}.name`),
                        nameKey: key,
                        category: 'Nabhasa',
                        description: I18n.t(`lists.yoga_list.${key}.effects`),
                        descriptionKey: key,
                        planets: sevenPlanetsList,
                        nature: 'Benefic',
                        strength: 7
                    }));
                    break;
                }
            }
        }
    }

    _getMalikaName(startHouse) {
        const names = {
            1: 'Lagna', 2: 'Dhana', 3: 'Vikrama', 4: 'Sukha',
            5: 'Putra', 6: 'Shatru', 7: 'Kalatra', 8: 'Mrityu',
            9: 'Bhagya', 10: 'Karma', 11: 'Labha', 12: 'Vyaya'
        };
        return names[startHouse] || '';
    }

    _checkAmalaYoga() {
        const ctx = this.ctx;
        const benefics = ['Jupiter', 'Venus'];
        const planetsIn10 = ctx.getPlanetsInHouse(10);
        const beneficsIn10 = planetsIn10.filter(p => benefics.includes(p));

        if (beneficsIn10.length > 0) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Amala.name'),
                nameKey: 'Amala',
                category: 'Raja',
                description: I18n.t('lists.yoga_list.Amala.effects', { planets: beneficsIn10.map(p => I18n.t('planets.' + p)).join(', ') }),
                descriptionKey: 'Amala',
                planets: beneficsIn10,
                nature: 'Benefic',
                strength: ctx.getStrength(beneficsIn10) + 1
            }));
        }
    }

    _checkPushkalaYoga() {
        const ctx = this.ctx;
        const lagnaLord = ctx.getHouseLord(1);
        const moonLord = ctx.getSignLord(ctx.moonRasi);

        if (ctx.isStrong(lagnaLord)) {
            const moonLordHouse = ctx.getHouse(moonLord);
            if (kendras.includes(moonLordHouse)) {
                if (ctx.isConnected(lagnaLord, moonLord)) {
                    ctx.addYoga(createYoga({
                        name: I18n.t('lists.yoga_list.Pushkala.name'),
                        nameKey: 'Pushkala',
                        category: 'Raja',
                        description: I18n.t('lists.yoga_list.Pushkala.effects'),
                        descriptionKey: 'Pushkala',
                        planets: [lagnaLord, moonLord, 'Moon'],
                        nature: 'Benefic',
                        strength: 8
                    }));
                }
            }
        }
    }

    _checkKalpadrumaYoga() {
        const ctx = this.ctx;
        const lagnaLord = ctx.getHouseLord(1);
        const l1Sign = ctx.getRasi(lagnaLord);
        const l2 = ctx.getSignLord(l1Sign); // Dispositor of L1
        const l2Sign = ctx.getRasi(l2);
        const l3 = ctx.getSignLord(l2Sign); // Dispositor of L2
        
        // Navamsha lord of L2
        const l2NavSign = ctx.navamshaPositions?.[l2];
        const l4 = l2NavSign !== undefined ? ctx.getSignLord(l2NavSign) : null;

        const kendraTrikonas = [...new Set([...kendras, ...trikonas])];
        
        const chain = [lagnaLord, l2, l3, l4].filter(p => p !== null);
        const allInGoodHouses = chain.every(p => {
            const house = ctx.getHouse(p);
            return kendraTrikonas.includes(house);
        });

        if (allInGoodHouses && chain.length >= 3) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Kalpadruma.name'),
                nameKey: 'Kalpadruma',
                category: 'Raja',
                description: I18n.t('lists.yoga_list.Kalpadruma.effects'),
                descriptionKey: 'Kalpadruma',
                planets: [...new Set(chain)],
                nature: 'Benefic',
                strength: 9
            }));
        }
    }

    _checkAmsavataraYoga() {
        const ctx = this.ctx;
        const jupHouse = ctx.getHouse('Jupiter');
        const venHouse = ctx.getHouse('Venus');
        const satHouse = ctx.getHouse('Saturn');
        const marHouse = ctx.getHouse('Mars');

        if (kendras.includes(jupHouse) && venHouse === 7 && satHouse === 10 && marHouse === 11) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Amsavatara.name'),
                nameKey: 'Amsavatara',
                category: 'Raja',
                description: I18n.t('lists.yoga_list.Amsavatara.effects'),
                descriptionKey: 'Amsavatara',
                planets: ['Jupiter', 'Venus', 'Saturn', 'Mars'],
                nature: 'Benefic',
                strength: 10
            }));
        }
    }

    _checkDevendraYoga() {
        const ctx = this.ctx;
        const lord1 = ctx.getHouseLord(1);
        const lord11 = ctx.getHouseLord(11);

        if (ctx.getHouse(lord1) === 11 && ctx.getHouse(lord11) === 1) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Devendra.name'),
                nameKey: 'Devendra',
                category: 'Raja',
                description: I18n.t('lists.yoga_list.Devendra.effects'),
                descriptionKey: 'Devendra',
                planets: [lord1, lord11],
                nature: 'Benefic',
                strength: 8
            }));
        }
    }

    _checkIndraYoga() {
        const ctx = this.ctx;
        const lord5 = ctx.getHouseLord(5);
        const lord11 = ctx.getHouseLord(11);

        if (ctx.getHouse(lord5) === 11 && ctx.getHouse(lord11) === 5) {
            if (ctx.isConjunct('Moon', 'Jupiter')) {
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Indra.name'),
                    nameKey: 'Indra',
                    category: 'Raja',
                    description: I18n.t('lists.yoga_list.Indra.effects'),
                    descriptionKey: 'Indra',
                    planets: [lord5, lord11, 'Moon', 'Jupiter'],
                    nature: 'Benefic',
                    strength: 9
                }));
            }
        }
    }

    _checkSubhaYoga() {
        const ctx = this.ctx;
        const benefics = ctx.getNaturalBenefics();
        const malefics = ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu'];

        const beneficsInKendra = benefics.every(p => kendras.includes(ctx.getHouse(p)));
        const maleficsInUpachaya = malefics.every(p => [3, 6, 11].includes(ctx.getHouse(p)));

        if (beneficsInKendra && maleficsInUpachaya) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Subha.name'),
                nameKey: 'Subha',
                category: 'Raja',
                description: I18n.t('lists.yoga_list.Subha.effects'),
                descriptionKey: 'Subha',
                planets: [...benefics, ...malefics],
                nature: 'Benefic',
                strength: 9
            }));
        }
    }

    // ========================================================================
    // CHANDRA (MOON) BASED YOGAS
    // ========================================================================

    _checkChandraYogas() {
        this._checkVasumanYoga();
        this._checkAdhamaYoga();
        this._checkSamaYoga();
        this._checkUttamaYoga();
        this._checkPakshaBalaYogas();
    }

    _checkVasumanYoga() {
        const ctx = this.ctx;
        const benefics = ctx.getNaturalBenefics();
        const upachayasFromMoon = [3, 6, 10, 11];
        const beneficsInUpachaya = benefics.filter(p => upachayasFromMoon.includes(ctx.getHouse(p, ctx.moonRasi)));

        if (beneficsInUpachaya.length === benefics.length && benefics.length >= 2) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vasuman.name'),
                nameKey: 'Vasuman',
                category: 'Lunar',
                description: I18n.t('lists.yoga_list.Vasuman.effects', { planets: beneficsInUpachaya.map(p => I18n.t('planets.' + p)).join(', ') }),
                descriptionKey: 'Vasuman',
                planets: ['Moon', ...beneficsInUpachaya],
                nature: 'Benefic',
                strength: ctx.getStrength(beneficsInUpachaya)
            }));
        }
    }

    _checkAdhamaYoga() {
        const ctx = this.ctx;
        const lagnaLord = ctx.getHouseLord(1);
        const moonHouseFromLL = ctx.getHouse('Moon', ctx.getRasi(lagnaLord));

        if ([6, 8, 12].includes(moonHouseFromLL)) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Adhama.name'),
                nameKey: 'Adhama',
                category: 'Lunar',
                description: I18n.t('lists.yoga_list.Adhama.effects'),
                descriptionKey: 'Adhama',
                planets: ['Moon', lagnaLord],
                nature: 'Malefic',
                strength: 4
            }));
        }
    }

    _checkSamaYoga() {
        const ctx = this.ctx;
        const lagnaLord = ctx.getHouseLord(1);
        const moonHouseFromLL = ctx.getHouse('Moon', ctx.getRasi(lagnaLord));

        if (kendras.includes(moonHouseFromLL)) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Sama.name'),
                nameKey: 'Sama',
                category: 'Lunar',
                description: I18n.t('lists.yoga_list.Sama.effects'),
                descriptionKey: 'Sama',
                planets: ['Moon', lagnaLord],
                nature: 'Benefic',
                strength: 6
            }));
        }
    }

    _checkUttamaYoga() {
        const ctx = this.ctx;
        const lagnaLord = ctx.getHouseLord(1);
        const moonHouseFromLL = ctx.getHouse('Moon', ctx.getRasi(lagnaLord));

        if (trikonas.includes(moonHouseFromLL)) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Uttama.name'),
                nameKey: 'Uttama',
                category: 'Lunar',
                description: I18n.t('lists.yoga_list.Uttama.effects'),
                descriptionKey: 'Uttama',
                planets: ['Moon', lagnaLord],
                nature: 'Benefic',
                strength: 7
            }));
        }
    }

    _checkPakshaBalaYogas() {
        const ctx = this.ctx;
        const isWaxing = ctx.isWaxingMoon();
        const moonHouse = ctx.getHouse('Moon');

        if (isWaxing) {
            if ([1, 4, 5, 7, 9, 10].includes(moonHouse)) {
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Paksha_Shubha.name'),
                    nameKey: 'Paksha_Shubha',
                    category: 'Lunar',
                    description: I18n.t('lists.yoga_list.Paksha_Shubha.effects'),
                    descriptionKey: 'Paksha_Shubha',
                    planets: ['Moon'],
                    nature: 'Benefic',
                    strength: 6
                }));
            }
        } else if (dusthanas.includes(moonHouse)) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Paksha_Durbala.name'),
                nameKey: 'Paksha_Durbala',
                category: 'Lunar',
                description: I18n.t('lists.yoga_list.Paksha_Durbala.effects'),
                descriptionKey: 'Paksha_Durbala',
                planets: ['Moon'],
                nature: 'Malefic',
                strength: 3
            }));
        }
    }

    // ========================================================================
    // SURYA (SUN) BASED YOGAS
    // ========================================================================

    _checkSuryaYogas() {
        const ctx = this.ctx;
        const sunHouse = ctx.getHouse('Sun');
        const mercHouse = ctx.getHouse('Mercury');
        const moonHouse = ctx.getHouse('Moon');

        if (sunHouse === 2 && mercHouse === 2 && moonHouse === 11) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Bhaskara.name'),
                nameKey: 'Bhaskara',
                category: 'Solar',
                description: I18n.t('lists.yoga_list.Bhaskara.effects'),
                descriptionKey: 'Bhaskara',
                planets: ['Sun', 'Mercury', 'Moon'],
                nature: 'Benefic',
                strength: 7
            }));
        }

        if (ctx.isConjunct('Sun', 'Mercury')) {
            const house = ctx.getHouse('Sun');
            if (!ctx.isCombust('Mercury') && [1, 4, 5, 9, 10, 11].includes(house)) {
                const strength = house === 1 ? 9 : (house === 10 ? 8 : 7);
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Budhaditya_House.name'),
                    nameKey: 'Budhaditya_House',
                    category: 'Solar',
                    description: I18n.t('lists.yoga_list.Budhaditya_House.effects'),
                    descriptionKey: 'Budhaditya_House',
                    planets: ['Sun', 'Mercury'],
                    nature: 'Benefic',
                    strength,
                    params: { house }
                }));
            }
        }

        if (ctx.isConjunct('Sun', 'Jupiter')) {
            const house = ctx.getHouse('Sun');
            if ([1, 4, 5, 9, 10, 11].includes(house)) {
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Ravi_Guru.name'),
                    nameKey: 'Ravi_Guru',
                    category: 'Solar',
                    description: I18n.t('lists.yoga_list.Ravi_Guru.effects'),
                    descriptionKey: 'Ravi_Guru',
                    planets: ['Sun', 'Jupiter'],
                    nature: 'Benefic',
                    strength: ctx.getStrength(['Sun', 'Jupiter'])
                }));
            }
        }
    }

    // ========================================================================
    // COMBUSTION YOGAS
    // ========================================================================

    _checkSpecialCombustionYogas() {
        const ctx = this.ctx;
        const planets = ['Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];

        for (const planet of planets) {
            if (ctx.isCombust(planet)) {
                const dignity = ctx.getDignity(planet);
                if (dignity === 'Exalted') {
                    ctx.addYoga(createYoga({
                        name: I18n.t('lists.yoga_list.Asta_Exalted.name', { planet: I18n.t('planets.' + planet) }),
                        nameKey: 'Asta_Exalted',
                        category: 'Combustion',
                        description: I18n.t('lists.yoga_list.Asta_Exalted.effects', { planet: I18n.t('planets.' + planet) }),
                        descriptionKey: 'Asta_Exalted',
                        planets: ['Sun', planet],
                        nature: 'Neutral',
                        strength: 5,
                        params: { planet }
                    }));
                } else if (dignity === 'Debilitated') {
                    ctx.addYoga(createYoga({
                        name: I18n.t('lists.yoga_list.Maha_Asta.name', { planet: I18n.t('planets.' + planet) }),
                        nameKey: 'Maha_Asta',
                        category: 'Combustion',
                        description: I18n.t('lists.yoga_list.Maha_Asta.effects', { planet: I18n.t('planets.' + planet) }),
                        descriptionKey: 'Maha_Asta',
                        planets: ['Sun', planet],
                        nature: 'Malefic',
                        strength: 2,
                        params: { planet }
                    }));
                }
            }
        }
    }

    // ========================================================================
    // RETROGRESSION YOGAS
    // ========================================================================

    _checkRetrogressionYogas() {
        const ctx = this.ctx;
        const planets = ['Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];

        for (const planet of planets) {
            if (ctx.isRetrograde(planet)) {
                const dignity = ctx.getDignity(planet);
                const house = ctx.getHouse(planet);

                if (['Exalted', 'Own', 'Moolatrikona'].includes(dignity)) {
                    ctx.addYoga(createYoga({
                        name: I18n.t('lists.yoga_list.Vakri_Shubha.name', { planet: I18n.t('planets.' + planet) }),
                        nameKey: 'Vakri_Shubha',
                        category: 'Retrogression',
                        description: I18n.t('lists.yoga_list.Vakri_Shubha.effects', { planet: I18n.t('planets.' + planet), dignity: I18n.t('kundali.' + dignity.toLowerCase()) }),
                        descriptionKey: 'Vakri_Shubha',
                        planets: [planet],
                        nature: 'Benefic',
                        strength: 7,
                        params: { planet, dignity }
                    }));
                } else if (kendras.includes(house)) {
                    ctx.addYoga(createYoga({
                        name: I18n.t('lists.yoga_list.Vakri_Kendra.name', { planet: I18n.t('planets.' + planet) }),
                        nameKey: 'Vakri_Kendra',
                        category: 'Retrogression',
                        description: I18n.t('lists.yoga_list.Vakri_Kendra.effects', { planet: I18n.t('planets.' + planet), house: I18n.n(house) }),
                        descriptionKey: 'Vakri_Kendra',
                        planets: [planet],
                        nature: 'Neutral',
                        strength: 6,
                        params: { planet, house }
                    }));
                } else if (dignity === 'Debilitated') {
                    ctx.addYoga(createYoga({
                        name: I18n.t('lists.yoga_list.Vakri_Neecha.name', { planet: I18n.t('planets.' + planet) }),
                        nameKey: 'Vakri_Neecha',
                        category: 'Retrogression',
                        description: I18n.t('lists.yoga_list.Vakri_Neecha.effects', { planet: I18n.t('planets.' + planet) }),
                        descriptionKey: 'Vakri_Neecha',
                        planets: [planet],
                        nature: 'Neutral',
                        strength: 5,
                        params: { planet }
                    }));
                }
            }
        }

        const retroPlanets = planets.filter(p => ctx.isRetrograde(p));
        if (retroPlanets.length >= 3) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Bahu_Vakri.name'),
                nameKey: 'Bahu_Vakri',
                category: 'Retrogression',
                description: I18n.t('lists.yoga_list.Bahu_Vakri.effects'),
                descriptionKey: 'Bahu_Vakri',
                planets: retroPlanets,
                nature: 'Neutral',
                strength: 5
            }));
        }
    }

    // ========================================================================
    // GANDANTA YOGAS (Junction Points)
    // ========================================================================

    _checkGandantaYogas() {
        const ctx = this.ctx;
        const gandantaRanges = [
            { signs: [3, 4], range: [26, 4] },
            { signs: [7, 8], range: [26, 4] },
            { signs: [11, 0], range: [26, 4] }
        ];

        for (const planet of ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']) {
            const sign = ctx.getRasi(planet);
            const degree = ctx.getDegree(planet);

            for (const { signs, range } of gandantaRanges) {
                if (signs.includes(sign)) {
                    const inGandanta = (sign === signs[0] && degree >= range[0]) ||
                        (sign === signs[1] && degree <= range[1]);

                    if (inGandanta) {
                        const severity = planet === 'Moon' ? 'Malefic' : 'Neutral';
                        ctx.addYoga(createYoga({
                            name: I18n.t('lists.yoga_list.Gandanta.name', { planet: I18n.t('planets.' + planet) }),
                            nameKey: 'Gandanta',
                            category: 'Gandanta',
                            description: I18n.t('lists.yoga_list.Gandanta.effects', { planet: I18n.t('planets.' + planet), degree: I18n.n(degree.toFixed(1)) }),
                            descriptionKey: 'Gandanta',
                            planets: [planet],
                            nature: severity,
                            strength: planet === 'Moon' ? 3 : 4,
                            params: { planet, degree: degree.toFixed(1) }
                        }));
                        break;
                    }
                }
            }
        }
    }

    // ========================================================================
    // NAVAMSHA BASED YOGAS
    // ========================================================================

    _checkNavamshaYogas() {
        const ctx = this.ctx;
        const navamshaPos = ctx.navamshaPositions;
        if (!navamshaPos) return;

        this._checkPushkaramsha(navamshaPos);

        for (const planet of ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']) {
            const rasiSign = ctx.getRasi(planet);
            const navSign = navamshaPos[planet];

            if (rasiSign !== -1 && rasiSign === navSign) {
                const dignity = ctx.getDignity(planet);
                let strength = 7;
                if (['Exalted', 'Own'].includes(dignity)) strength = 9;

                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Vargottama.name', { planet: I18n.t('planets.' + planet) }),
                    nameKey: 'Vargottama',
                    category: 'Vargottama',
                    description: I18n.t('lists.yoga_list.Vargottama.effects', { planet: I18n.t('planets.' + planet), dignity: I18n.t('kundali.' + dignity.toLowerCase()) }),
                    descriptionKey: 'Vargottama_Planet',
                    planets: [planet],
                    nature: 'Benefic',
                    strength,
                    params: { planet, dignity }
                }));
            }
        }
    }

    _checkPushkaramsha(navamshaPos) {
        const ctx = this.ctx;
        const pushkaraSigns = {
            // Fire signs (0, 4, 8) -> Libra(6) and Sag(8)
            0: [6, 8], 4: [6, 8], 8: [6, 8],
            // Earth signs (1, 5, 9) -> Pisces(11) and Taurus(1)
            1: [11, 1], 5: [11, 1], 9: [11, 1],
            // Air signs (2, 6, 10) -> Pisces(11) and Taurus(1)
            2: [11, 1], 6: [11, 1], 10: [11, 1],
            // Water signs (3, 7, 11) -> Cancer(3) and Virgo(5)
            3: [3, 5], 7: [3, 5], 11: [3, 5]
        };

        for (const planet of ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']) {
            const rasiSign = ctx.getRasi(planet);
            const navSign = navamshaPos[planet];

            if (rasiSign !== -1 && navSign !== undefined) {
                const pushkaras = pushkaraSigns[rasiSign];
                if (pushkaras && pushkaras.includes(navSign)) {
                    ctx.addYoga(createYoga({
                        name: I18n.t('lists.yoga_list.Pushkaramsha.name', { planet: I18n.t('planets.' + planet) }),
                        nameKey: 'Pushkaramsha',
                        category: 'Navamsha',
                        description: I18n.t('lists.yoga_list.Pushkaramsha.effects', { planet: I18n.t('planets.' + planet) }),
                        descriptionKey: 'Pushkaramsha',
                        planets: [planet],
                        nature: 'Benefic',
                        strength: 7,
                        params: { planet }
                    }));
                }
            }
        }
    }

    _checkAshtakavargaYogas() {
        // Ashtakavarga yogas would require SAV data
    }
}

export default AdvancedYogas;
