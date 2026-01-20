/**
 * ============================================================================
 * SPECIAL CLASSICAL YOGAS - Rare Combinations from Authoritative Texts
 * ============================================================================
 *
 * This module implements special yogas from classical texts including:
 * - Named Yogas from BPHS, Phaladeepika, Saravali
 * - Deity Yogas (Named after Gods)
 * - Special Fortune Yogas
 * - Rare Mahayogas
 *
 * References:
 * - Brihat Parashara Hora Shastra (BPHS)
 * - Phaladeepika by Mantreshwar
 * - Saravali by Kalyana Varma
 * - Jataka Parijata
 *
 * @module yogas/special_classical
 * @version 1.0.0
 */

import I18n from '../../core/i18n.js';
import { YogaModuleBase, createYoga, kendras, trikonas, dusthanas, upachayas, panaparas, apoklimas } from './base.js';

/**
 * Special Classical Yogas Module
 */
export class SpecialClassicalYogas extends YogaModuleBase {
    constructor(ctx) {
        super(ctx);
    }

    check() {
        this._checkDeityYogas();
        this._checkFortuneYogas();
        this._checkSpecialRajaYogas();
        this._checkPanchagrahaYogas();
        this._checkAshtakaYogas();
        this._checkKalaSarpaVariants();
        this._checkSpecialMoonYogas();
        this._checkBhagaYogas();
        this._checkEssentialClassicalYogas();
    }

    /**
     * Essential Classical Yogas found in almost all professional charts
     */
    _checkEssentialClassicalYogas() {
        const ctx = this.ctx;

        // 1. Gaja-Kesari Yoga: Jupiter in Kendra from Moon
        const moonRasi = ctx.moonRasi;
        const jupRasi = ctx.getRasi('Jupiter');
        if (moonRasi !== -1 && jupRasi !== -1) {
            let relHouse = ((jupRasi - moonRasi + 12) % 12) + 1;
            if (kendras.includes(relHouse)) {
                // Additional strength factors
                const jupStrong = this.isStrong('Jupiter');
                const moonStrong = this.isStrong('Moon');
                
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Gajakesari.name'),
                    nameKey: 'Gajakesari',
                    category: 'Raja',
                    description: I18n.t('lists.yoga_list.Gajakesari.effects'),
                    descriptionKey: 'Gajakesari',
                    planets: ['Moon', 'Jupiter'],
                    nature: 'Benefic',
                    strength: (jupStrong && moonStrong) ? 9 : 7,
                    params: { relHouse }
                }));
            }
        }

        // 2. Guru-Mangala Yoga: Jupiter and Mars conjunct or in mutual aspect
        if (ctx.isConnected('Jupiter', 'Mars')) {
            this.addYoga(createYoga({
                name: 'Guru-Mangala Yoga',
                nameKey: 'Guru_Mangala',
                category: 'Raja',
                description: 'Jupiter and Mars connection. Dynamic energy guided by wisdom - success in administration, courageous, righteous leader.',
                descriptionKey: 'Guru_Mangala',
                planets: ['Jupiter', 'Mars'],
                nature: 'Benefic',
                strength: this.getStrength(['Jupiter', 'Mars']),
                params: { planet: 'Jupiter', p2: 'Mars' }
            }));
        }
    }

    // ========================================================================
    // DEITY YOGAS (Named after Gods)
    // ========================================================================

    _checkDeityYogas() {
        const ctx = this.ctx;

        // 1. Brahma Yoga - Jupiter in Kendra, Venus in 9th, ruler of Lagna strong
        const jupHouse = ctx.getHouse('Jupiter');
        const venHouse = ctx.getHouse('Venus');
        const lord1 = ctx.getHouseLord(1);

        if (kendras.includes(jupHouse) && venHouse === 9 && ctx.isStrong(lord1)) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Brahma.name'),
                nameKey: 'Brahma',
                category: 'Deity',
                description: I18n.t('lists.yoga_list.Brahma.effects'),
                descriptionKey: 'Brahma',
                planets: ['Jupiter', 'Venus', lord1],
                nature: 'Benefic',
                strength: 8
            }));
        }

        // 2. Vishnu Yoga - 9th lord in 10th, 10th lord in 9th
        const lord9 = ctx.getHouseLord(9);
        const lord10 = ctx.getHouseLord(10);
        if (ctx.getHouse(lord9) === 10 && ctx.getHouse(lord10) === 9) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vishnu.name'),
                nameKey: 'Vishnu',
                category: 'Deity',
                description: I18n.t('lists.yoga_list.Vishnu.effects'),
                descriptionKey: 'Vishnu',
                planets: [lord9, lord10],
                nature: 'Benefic',
                strength: 8
            }));
        }

        // 3. Shiva Yoga - 5th lord in 9th, 9th lord in 10th, 10th lord in 5th
        const lord5 = ctx.getHouseLord(5);
        if (ctx.getHouse(lord5) === 9 && ctx.getHouse(lord9) === 10 && ctx.getHouse(lord10) === 5) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Shiva.name'),
                nameKey: 'Shiva',
                category: 'Deity',
                description: I18n.t('lists.yoga_list.Shiva.effects'),
                descriptionKey: 'Shiva',
                planets: [lord5, lord9, lord10],
                nature: 'Benefic',
                strength: 9
            }));
        }

        // 4. Lakshmi Narayan Yoga - Venus-Mercury in Kendra together
        if (ctx.isConjunct('Venus', 'Mercury') && kendras.includes(ctx.getHouse('Venus'))) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Lakshmi_Narayan.name'),
                nameKey: 'Lakshmi_Narayan',
                category: 'Deity',
                description: I18n.t('lists.yoga_list.Lakshmi_Narayan.effects'),
                descriptionKey: 'Lakshmi_Narayan',
                planets: ['Venus', 'Mercury'],
                nature: 'Benefic',
                strength: 7
            }));
        }

        // 5. Ganesha Yoga - Mercury exalted or own sign in Kendra
        const mercHouse = ctx.getHouse('Mercury');
        const mercDignity = ctx.getDignity('Mercury');
        if (kendras.includes(mercHouse) && ['Exalted', 'Own'].includes(mercDignity)) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Ganesha.name'),
                nameKey: 'Ganesha',
                category: 'Deity',
                description: I18n.t('lists.yoga_list.Ganesha.effects'),
                descriptionKey: 'Ganesha',
                planets: ['Mercury'],
                nature: 'Benefic',
                strength: 7
            }));
        }

        // 6. Durga Yoga - Moon exalted or own sign in Kendra with benefic aspect
        const moonHouse = ctx.getHouse('Moon');
        const moonDignity = ctx.getDignity('Moon');
        if (kendras.includes(moonHouse) && ['Exalted', 'Own'].includes(moonDignity)) {
            if (ctx.aspects('Jupiter', 'Moon') || ctx.aspects('Venus', 'Moon')) {
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Durga.name'),
                    nameKey: 'Durga',
                    category: 'Deity',
                    description: I18n.t('lists.yoga_list.Durga.effects'),
                    descriptionKey: 'Durga',
                    planets: ['Moon', 'Jupiter'],
                    nature: 'Benefic',
                    strength: 7
                }));
            }
        }

        // 7. Saraswati Yoga (Full) - Jupiter, Venus, Mercury in Kendras/Trikonas/2nd, Jupiter in own/exalted
        const jupDig = ctx.getDignity('Jupiter');
        const goodHouses = [...kendras, ...trikonas, 2];
        const jupInGood = goodHouses.includes(jupHouse);
        const venInGood = goodHouses.includes(venHouse);
        const mercInGood = goodHouses.includes(mercHouse);

        if (jupInGood && venInGood && mercInGood && ['Exalted', 'Own', 'Moolatrikona'].includes(jupDig)) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Saraswati_Full.name'),
                nameKey: 'Saraswati_Full',
                category: 'Deity',
                description: I18n.t('lists.yoga_list.Saraswati_Full.effects'),
                descriptionKey: 'Saraswati_Full',
                planets: ['Jupiter', 'Venus', 'Mercury'],
                nature: 'Benefic',
                strength: 9
            }));
        }
    }

    // ========================================================================
    // FORTUNE YOGAS
    // ========================================================================

    _checkFortuneYogas() {
        const ctx = this.ctx;

        // 1. Maha Bhagya Yoga
        const sunHouse = ctx.getHouse('Sun');
        const moonHouse = ctx.getHouse('Moon');
        const sunDig = ctx.getDignity('Sun');
        const moonDig = ctx.getDignity('Moon');

        if (kendras.includes(sunHouse) && kendras.includes(moonHouse)) {
            if (['Exalted', 'Own', 'Moolatrikona'].includes(sunDig) || ['Exalted', 'Own', 'Moolatrikona'].includes(moonDig)) {
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Maha_Bhagya.name'),
                    nameKey: 'Maha_Bhagya',
                    category: 'Fortune',
                    description: I18n.t('lists.yoga_list.Maha_Bhagya.effects'),
                    descriptionKey: 'Maha_Bhagya',
                    planets: ['Sun', 'Moon'],
                    nature: 'Benefic',
                    strength: 9
                }));
            }
        }

        // 2. Chatussagara Yoga
        const kendraOccupancy = kendras.map(h => ctx.getPlanetsInHouse(h).length > 0);
        if (kendraOccupancy.every(o => o)) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Chatussagara.name'),
                nameKey: 'Chatussagara',
                category: 'Fortune',
                description: I18n.t('lists.yoga_list.Chatussagara.effects'),
                descriptionKey: 'Chatussagara',
                planets: kendras.flatMap(h => ctx.getPlanetsInHouse(h)),
                nature: 'Benefic',
                strength: 8
            }));
        }

        // 3. Sunapha variants
        const moonRasi = ctx.moonRasi;
        const planetsIn2FromMoon = ctx.getPlanetsInHouse(2, moonRasi);

        const sunaphaPlanets = {
            'Mars': { key: 'Sunapha_Mars' },
            'Mercury': { key: 'Sunapha_Mercury' },
            'Jupiter': { key: 'Sunapha_Jupiter' },
            'Venus': { key: 'Sunapha_Venus' },
            'Saturn': { key: 'Sunapha_Saturn' }
        };

        for (const planet of planetsIn2FromMoon) {
            if (sunaphaPlanets[planet]) {
                const data = sunaphaPlanets[planet];
                ctx.addYoga(createYoga({
                    name: I18n.t(`lists.yoga_list.${data.key}.name`),
                    nameKey: data.key,
                    category: 'Fortune',
                    description: I18n.t(`lists.yoga_list.${data.key}.effects`),
                    descriptionKey: data.key,
                    planets: ['Moon', planet],
                    nature: 'Benefic',
                    strength: 6,
                    params: { planet: planet }
                }));
            }
        }

        // 4. Shubha Yoga (Adhi)
        const benefics = ctx.getNaturalBenefics();
        const beneficsIn678FromMoon = benefics.filter(p => [6, 7, 8].includes(ctx.getHouse(p, moonRasi)));

        if (beneficsIn678FromMoon.length >= 2) {
            const planetNames = beneficsIn678FromMoon.map(p => I18n.t('planets.' + p)).join(', ');
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Adhi.name'),
                nameKey: 'Adhi',
                category: 'Fortune',
                description: I18n.t('lists.yoga_list.Adhi.effects', { planets: planetNames }),
                descriptionKey: 'Adhi',
                planets: ['Moon', ...beneficsIn678FromMoon],
                nature: 'Benefic',
                strength: 7 + (beneficsIn678FromMoon.length - 2),
                params: { planets: beneficsIn678FromMoon.join(', ') }
            }));
        }
    }

    // ========================================================================
    // SPECIAL RAJA YOGAS
    // ========================================================================

    _checkSpecialRajaYogas() {
        const ctx = this.ctx;

        // 1. Akhanda Samrajya Yoga - Jupiter rules 2nd/5th/11th and in Kendra
        const lord2 = ctx.getHouseLord(2);
        const lord5 = ctx.getHouseLord(5);
        const lord11 = ctx.getHouseLord(11);
        const jupHouse = ctx.getHouse('Jupiter');

        if ([lord2, lord5, lord11].includes('Jupiter') && kendras.includes(jupHouse)) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Akhanda_Samrajya.name'),
                nameKey: 'Akhanda_Samrajya',
                category: 'Raja',
                description: I18n.t('lists.yoga_list.Akhanda_Samrajya.effects'),
                descriptionKey: 'Akhanda_Samrajya',
                planets: ['Jupiter'],
                nature: 'Benefic',
                strength: 9
            }));
        }

        // 2. Simhasana Yoga
        const lords = [2, 4, 5, 9, 10].map(h => ctx.getHouseLord(h));
        const lordsInKendras = lords.filter(l => kendras.includes(ctx.getHouse(l)));

        if (lordsInKendras.length >= 4) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Simhasana.name'),
                nameKey: 'Simhasana',
                category: 'Raja',
                description: I18n.t('lists.yoga_list.Simhasana.effects'),
                descriptionKey: 'Simhasana',
                planets: lordsInKendras,
                nature: 'Benefic',
                strength: 8
            }));
        }

        // 3. Makuta Yoga
        if (ctx.getHouse('Jupiter') === 9) {
            const beneficsInKendras = ctx.getNaturalBenefics().filter(p => kendras.includes(ctx.getHouse(p)));
            if (beneficsInKendras.length >= 2) {
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Makuta.name'),
                    nameKey: 'Makuta',
                    category: 'Raja',
                    description: I18n.t('lists.yoga_list.Makuta.effects'),
                    descriptionKey: 'Makuta',
                    planets: ['Jupiter', ...beneficsInKendras],
                    nature: 'Benefic',
                    strength: 8
                }));
            }
        }

        // 4. Parvata Yoga
        const lord1 = ctx.getHouseLord(1);
        const lord12 = ctx.getHouseLord(12);
        const lord1House = this.getHouse(lord1);
        const lord12House = this.getHouse(lord12);

        if (kendras.includes(lord1House) && kendras.includes(lord12House)) {
            const maleficsInKendraTrikona = ['Sun', 'Mars', 'Saturn'].filter(p => {
                const h = ctx.getHouse(p);
                return kendras.includes(h) || trikonas.includes(h);
            });

            if (maleficsInKendraTrikona.length === 0) {
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Parvata.name'),
                    nameKey: 'Parvata',
                    category: 'Raja',
                    description: I18n.t('lists.yoga_list.Parvata.effects'),
                    descriptionKey: 'Parvata',
                    planets: [lord1, lord12],
                    nature: 'Benefic',
                    strength: 7
                }));
            }
        }

        // 5. Chamara Yoga
        const lord1Dignity = ctx.getDignity(lord1);
        if (lord1Dignity === 'Exalted' && kendras.includes(ctx.getHouse(lord1))) {
            if (ctx.aspects('Jupiter', lord1)) {
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Chamara.name'),
                    nameKey: 'Chamara',
                    category: 'Raja',
                    description: I18n.t('lists.yoga_list.Chamara.effects', { planet: I18n.t('planets.' + lord1), ref: I18n.t('planets.Jupiter') }),
                    descriptionKey: 'Chamara',
                    planets: [lord1, 'Jupiter'],
                    nature: 'Benefic',
                    strength: 8,
                    params: { planet: lord1, ref: 'Jupiter' }
                }));
            }
        }

        // 6. Bheri Yoga
        const lord9 = ctx.getHouseLord(9);
        if (kendras.includes(ctx.getHouse(lord9))) {
            if (ctx.isStrong('Venus') && ctx.isStrong('Jupiter') && ctx.isStrong(lord1)) {
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Bheri.name'),
                    nameKey: 'Bheri',
                    category: 'Raja',
                    description: I18n.t('lists.yoga_list.Bheri.effects'),
                    descriptionKey: 'Bheri',
                    planets: ['Venus', 'Jupiter', lord1, lord9],
                    nature: 'Benefic',
                    strength: 8
                }));
            }
        }
    }

    // ========================================================================
    // PANCHAGRAHA YOGAS (Five Planet Combinations)
    // ========================================================================

    _checkPanchagrahaYogas() {
        const ctx = this.ctx;
        const sevenPlanetsList = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];

        // Count planets per house
        const houseCounts = {};
        for (let h = 1; h <= 12; h++) {
            houseCounts[h] = ctx.getPlanetsInHouse(h).filter(p => sevenPlanetsList.includes(p)).length;
        }

        // Find houses with 4+ planets
        for (let h = 1; h <= 12; h++) {
            if (houseCounts[h] >= 4) {
                const planetsInHouse = ctx.getPlanetsInHouse(h).filter(p => sevenPlanetsList.includes(p));

                // Check if mostly benefic or malefic
                const benefics = planetsInHouse.filter(p => ['Jupiter', 'Venus', 'Mercury', 'Moon'].includes(p));
                const nature = benefics.length >= 2 ? 'Benefic' : 'Neutral';

                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Sanghata.name'),
                    nameKey: 'Sanghata',
                    category: 'Nabhasa',
                    description: I18n.t('lists.yoga_list.Sanghata.effects'),
                    descriptionKey: 'Sanghata',
                    planets: planetsInHouse,
                    nature,
                    strength: 6 + (houseCounts[h] - 4),
                    params: { house: h }
                }));
            }
        }

        // 5 planet conjunction (Pancha Graha Yoga)
        for (let h = 1; h <= 12; h++) {
            if (houseCounts[h] >= 5) {
                const planetsInHouse = ctx.getPlanetsInHouse(h).filter(p => sevenPlanetsList.includes(p));
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Pancha_Graha.name'),
                    nameKey: 'Pancha_Graha',
                    category: 'Nabhasa',
                    description: I18n.t('lists.yoga_list.Pancha_Graha.effects'),
                    descriptionKey: 'Pancha_Graha',
                    planets: planetsInHouse,
                    nature: 'Neutral',
                    strength: 7,
                    params: { house: h }
                }));
            }
        }
    }

    // ========================================================================
    // ASHTAKA YOGAS (Eight-fold Combinations)
    // ========================================================================

    _checkAshtakaYogas() {
        const ctx = this.ctx;

        // Ashtalakshmi Yoga - All 8 directions (Kendras + Trikonas + 2 + 11) have benefics
        const auspiciousHouses = [1, 2, 4, 5, 7, 9, 10, 11];
        const benefics = ctx.getNaturalBenefics();

        const housesWithBenefics = auspiciousHouses.filter(h => {
            const planetsIn = ctx.getPlanetsInHouse(h);
            return planetsIn.some(p => benefics.includes(p));
        });

        if (housesWithBenefics.length >= 5) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Ashta_Lakshmi.name'),
                nameKey: 'Ashta_Lakshmi',
                category: 'Fortune',
                description: I18n.t('lists.yoga_list.Ashta_Lakshmi.effects'),
                descriptionKey: 'Ashta_Lakshmi',
                planets: benefics,
                nature: 'Benefic',
                strength: 5 + housesWithBenefics.length
            }));
        }
    }

    // ========================================================================
    // KAAL SARPA VARIANTS
    // ========================================================================

    _checkKalaSarpaVariants() {
        const ctx = this.ctx;

        const rahuRasi = ctx.getRasi('Rahu');
        const ketuRasi = ctx.getRasi('Ketu');

        if (rahuRasi === -1 || ketuRasi === -1) return;

        // Get all planets between Rahu and Ketu
        const sevenPlanetsList = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
        const planetSigns = sevenPlanetsList.map(p => ctx.getRasi(p));

        // Check if all planets are on one side of the axis
        let allOnRahuSide = true;
        let allOnKetuSide = true;

        for (const sign of planetSigns) {
            if (sign === -1) continue;

            // Calculate distance from Rahu going forward
            const distFromRahu = (sign - rahuRasi + 12) % 12;
            const distFromKetu = (sign - ketuRasi + 12) % 12;

            // If between Rahu and Ketu (Rahu side)
            if (distFromRahu > 0 && distFromRahu < 6) {
                allOnKetuSide = false;
            }
            // If between Ketu and Rahu (Ketu side)
            if (distFromKetu > 0 && distFromKetu < 6) {
                allOnRahuSide = false;
            }
        }

        // Only create yoga if there's some planets escaping the axis
        const escapingPlanets = sevenPlanetsList.filter(p => {
            const sign = ctx.getRasi(p);
            return sign === rahuRasi || sign === ketuRasi;
        });

        if (escapingPlanets.length > 0 && escapingPlanets.length < 7) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Partial_Kaal_Sarpa.name'),
                nameKey: 'Partial_Kaal_Sarpa',
                category: 'KaalSarpa',
                description: I18n.t('lists.yoga_list.Partial_Kaal_Sarpa.effects'),
                descriptionKey: 'Partial_Kaal_Sarpa',
                planets: ['Rahu', 'Ketu', ...escapingPlanets],
                nature: 'Neutral',
                strength: 5
            }));
        }
    }

    // ========================================================================
    // SPECIAL MOON YOGAS
    // ========================================================================

    _checkSpecialMoonYogas() {
        const ctx = this.ctx;

        // 1. Pushya Snana Yoga
        const moonRasi = ctx.moonRasi;
        if (moonRasi === 3) {
            const jupAspects = ctx.aspects('Jupiter', 'Moon') || ctx.isConjunct('Jupiter', 'Moon');
            if (jupAspects) {
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Pushya.name'),
                    nameKey: 'Pushya',
                    category: 'Lunar',
                    description: I18n.t('lists.yoga_list.Pushya.effects'),
                    descriptionKey: 'Pushya',
                    planets: ['Moon', 'Jupiter'],
                    nature: 'Benefic',
                    strength: 7
                }));
            }
        }

        // 2. Chandrika Yoga
        if (ctx.isWaxingMoon() && kendras.includes(ctx.getHouse('Moon'))) {
            const moonLon = ctx.getLongitude('Moon');
            const sunLon = ctx.getLongitude('Sun');
            const phase = (moonLon - sunLon + 360) % 360;

            if (phase >= 120 && phase <= 240) {
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Chandrika.name'),
                    nameKey: 'Chandrika',
                    category: 'Lunar',
                    description: I18n.t('lists.yoga_list.Chandrika.effects'),
                    descriptionKey: 'Chandrika',
                    planets: ['Moon'],
                    nature: 'Benefic',
                    strength: 7
                }));
            }
        }

        // 3. Someshwara Yoga
        const lord1 = ctx.getHouseLord(1);
        const moonHouse = ctx.getHouse('Moon');
        const lord1House = this.getHouse(lord1);

        if (kendras.includes(moonHouse) && kendras.includes(lord1House)) {
            if (ctx.aspects('Moon', lord1) || ctx.aspects(lord1, 'Moon')) {
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Someshwara.name'),
                    nameKey: 'Someshwara',
                    category: 'Lunar',
                    description: I18n.t('lists.yoga_list.Someshwara.effects'),
                    descriptionKey: 'Someshwara',
                    planets: ['Moon', lord1],
                    nature: 'Benefic',
                    strength: 7
                }));
            }
        }
    }

    // ========================================================================
    // BHAGA YOGAS (Fortune Point Yogas)
    // ========================================================================

    _checkBhagaYogas() {
        const ctx = this.ctx;

        // 1. Bhagya Yoga
        const lord9 = ctx.getHouseLord(9);
        if (ctx.getHouse(lord9) === 9) {
            const benefics = ctx.getNaturalBenefics();
            const hasBeneficAspect = benefics.some(b => ctx.aspects(b, lord9));

            if (hasBeneficAspect) {
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Bhagya.name'),
                    nameKey: 'Bhagya',
                    category: 'Fortune',
                    description: I18n.t('lists.yoga_list.Bhagya.effects'),
                    descriptionKey: 'Bhagya',
                    planets: [lord9],
                    nature: 'Benefic',
                    strength: 7
                }));
            }
        }

        // 2. Dridha Bhagya
        if (ctx.getDignity(lord9) === 'Exalted') {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Dridha_Bhagya.name'),
                nameKey: 'Dridha_Bhagya',
                category: 'Fortune',
                description: I18n.t('lists.yoga_list.Dridha_Bhagya.effects'),
                descriptionKey: 'Dridha_Bhagya',
                planets: [lord9],
                nature: 'Benefic',
                strength: 8
            }));
        }

        // 3. Sukha Yoga
        const lord4 = ctx.getHouseLord(4);
        if (ctx.getHouse(lord4) === 4 && ctx.isStrong(lord4)) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Sukha.name'),
                nameKey: 'Sukha',
                category: 'Fortune',
                description: I18n.t('lists.yoga_list.Sukha.effects'),
                descriptionKey: 'Sukha',
                planets: [lord4],
                nature: 'Benefic',
                strength: 7
            }));
        }
    }
}

export default SpecialClassicalYogas;
