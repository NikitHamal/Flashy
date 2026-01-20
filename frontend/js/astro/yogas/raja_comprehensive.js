/**
 * ============================================================================
 * COMPREHENSIVE RAJA YOGAS - Classical Power Combinations
 * ============================================================================
 *
 * Raja Yogas confer kingship, authority, power, and high status. They are
 * formed primarily by the connection between Kendra and Trikona lords.
 * This module implements 100+ classical Raja Yogas from authoritative texts.
 *
 * References:
 * - Brihat Parashara Hora Shastra (BPHS) Chapters 36-41
 * - Phaladeepika Chapter 6
 * - Jataka Parijata
 * - Saravali
 *
 * @module yogas/raja_comprehensive
 * @version 1.0.0
 */

import I18n from '../../core/i18n.js';
import { YogaModuleBase, createYoga, kendras, trikonas, dusthanas } from './base.js';

export class RajaComprehensiveYogas extends YogaModuleBase {
    constructor(ctx) {
        super(ctx);
    }

    check() {
        this._checkKendraTrikona();
        this._checkDharmaKarmadhipati();
        this._checkViparitaRaja();
        this._checkSpecialRaja();
        this._checkParivartanaRaja();
        this._checkMahapurushaEnhanced();
        this._checkAdityadiYogas();
        this._checkNamedRajaYogas();
        this._checkAscendantSpecificRaja();
    }

    /**
     * Classic Kendra-Trikona Raja Yoga
     * Connection between Kendra and Trikona lords
     */
    _checkKendraTrikona() {
        const ctx = this.ctx;
        const kendraHouses = [1, 4, 7, 10];
        const trikonaHouses = [1, 5, 9];

        // Get all Kendra and Trikona lords
        const kendraLords = kendraHouses.map(h => ctx.getHouseLord(h));
        const trikonaLords = trikonaHouses.map(h => ctx.getHouseLord(h));

        // Check connections between Kendra and Trikona lords
        for (let i = 0; i < kendraHouses.length; i++) {
            const kendraLord = kendraLords[i];
            const kendraHouse = kendraHouses[i];

            for (let j = 0; j < trikonaHouses.length; j++) {
                const trikonaLord = trikonaLords[j];
                const trikonaHouse = trikonaHouses[j];

                // Skip if same lord or same house
                if (kendraLord === trikonaLord || kendraHouse === trikonaHouse) continue;

                // Check conjunction
                if (ctx.isConjunct(kendraLord, trikonaLord)) {
                    const house = this.getHouse(kendraLord);
                    let strength = this._calculateRajaStrength(kendraLord, trikonaLord, house);

                    const bName = I18n.t('planets.' + kendraLord);
                    const p2Name = I18n.t('planets.' + trikonaLord);

                    this.addYoga(createYoga({
                        name: I18n.t('lists.yoga_list.Raja_KT.name', { h1: I18n.n(kendraHouse), h2: I18n.n(trikonaHouse) }),
                        nameKey: 'Raja_KT',
                        category: 'Raja',
                        description: I18n.t('lists.yoga_list.Raja_KT.effects', {
                            h1: I18n.n(kendraHouse),
                            planet: bName,
                            h2: I18n.n(trikonaHouse),
                            p2: p2Name,
                            house: I18n.n(house)
                        }),
                        descriptionKey: 'Raja_KT',
                        planets: [kendraLord, trikonaLord],
                        nature: 'Benefic',
                        strength,
                        params: { h1: kendraHouse, h2: trikonaHouse, planet: kendraLord, p2: trikonaLord, house }
                    }));
                }

                // Check mutual aspect
                if (ctx.mutualAspect(kendraLord, trikonaLord)) {
                    let strength = this._calculateRajaStrength(kendraLord, trikonaLord) * 0.75;

                    const bName = I18n.t('planets.' + kendraLord);
                    const p2Name = I18n.t('planets.' + trikonaLord);

                    this.addYoga(createYoga({
                        name: I18n.t('lists.yoga_list.Raja_KT_Aspect.name', { h1: I18n.n(kendraHouse), h2: I18n.n(trikonaHouse) }),
                        nameKey: 'Raja_KT_Aspect',
                        category: 'Raja',
                        description: I18n.t('lists.yoga_list.Raja_KT_Aspect.effects', {
                            h1: I18n.n(kendraHouse),
                            planet: bName,
                            h2: I18n.n(trikonaHouse),
                            p2: p2Name
                        }),
                        descriptionKey: 'Raja_KT_Aspect',
                        planets: [kendraLord, trikonaLord],
                        nature: 'Benefic',
                        strength,
                        params: { h1: kendraHouse, h2: trikonaHouse, planet: kendraLord, p2: trikonaLord }
                    }));
                }
            }
        }
    }

    /**
     * Dharma-Karmadhipati Yoga (9th-10th lord connection)
     * One of the most powerful Raja Yogas
     */
    _checkDharmaKarmadhipati() {
        const ctx = this.ctx;
        const lord9 = ctx.getHouseLord(9);
        const lord10 = ctx.getHouseLord(10);

        // Conjunction
        if (ctx.isConjunct(lord9, lord10)) {
            const house = this.getHouse(lord9);
            let strength = this._calculateRajaStrength(lord9, lord10, house) + 1;

            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Dharma_Karmadhipati.name'),
                nameKey: 'Dharma_Karmadhipati',
                category: 'Raja',
                description: I18n.t('lists.yoga_list.Dharma_Karmadhipati.effects', {
                    planet: I18n.t('planets.' + lord9),
                    p2: I18n.t('planets.' + lord10),
                    house: I18n.n(house)
                }),
                descriptionKey: 'Dharma_Karmadhipati',
                planets: [lord9, lord10],
                nature: 'Benefic',
                strength: Math.min(10, strength),
                params: { planet: lord9, p2: lord10, house }
            }));
        }

        // Exchange (Parivartana)
        const lord9House = this.getHouse(lord9);
        const lord10House = this.getHouse(lord10);
        if (lord9House === 10 && lord10House === 9) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Dharma_Karma_Exchange.name'),
                nameKey: 'Dharma_Karma_Exchange',
                category: 'Raja',
                description: I18n.t('lists.yoga_list.Dharma_Karma_Exchange.effects'),
                descriptionKey: 'Dharma_Karma_Exchange',
                planets: [lord9, lord10],
                nature: 'Benefic',
                strength: 9,
                params: { h1: 9, h2: 10, planet: lord9, p2: lord10 }
            }));
        }

        // Mutual aspect
        if (ctx.mutualAspect(lord9, lord10)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Dharma_Karma_Aspect.name'),
                nameKey: 'Dharma_Karma_Aspect',
                category: 'Raja',
                description: I18n.t('lists.yoga_list.Dharma_Karma_Aspect.effects', {
                    planet: I18n.t('planets.' + lord9),
                    p2: I18n.t('planets.' + lord10)
                }),
                descriptionKey: 'Dharma_Karma_Aspect',
                planets: [lord9, lord10],
                nature: 'Benefic',
                strength: 7,
                params: { planet: lord9, p2: lord10 }
            }));
        }
    }

    /**
     * Viparita Raja Yoga (Dusthana lords in Dusthanas)
     * Turning adversity into triumph
     */
    _checkViparitaRaja() {
        const ctx = this.ctx;
        const lord6 = ctx.getHouseLord(6);
        const lord8 = ctx.getHouseLord(8);
        const lord12 = ctx.getHouseLord(12);

        const dusthanaHouses = [6, 8, 12];

        // Harsha Yoga: 6th lord in 6th, 8th, or 12th
        const lord6House = this.getHouse(lord6);
        if (dusthanaHouses.includes(lord6House)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Harsha.name'),
                nameKey: 'Harsha',
                category: 'Vipareeta_Raja',
                description: I18n.t('lists.yoga_list.Harsha.effects', {
                    planet: I18n.t('planets.' + lord6),
                    lordHouse: I18n.n(lord6House)
                }),
                descriptionKey: 'Harsha',
                planets: [lord6],
                nature: 'Benefic',
                strength: 7,
                params: { house: 6, lordHouse: lord6House, planet: lord6 }
            }));
        }

        // Sarala Yoga: 8th lord in 6th, 8th, or 12th
        const lord8House = this.getHouse(lord8);
        if (dusthanaHouses.includes(lord8House)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Sarala.name'),
                nameKey: 'Sarala',
                category: 'Vipareeta_Raja',
                description: I18n.t('lists.yoga_list.Sarala.effects', {
                    planet: I18n.t('planets.' + lord8),
                    lordHouse: I18n.n(lord8House)
                }),
                descriptionKey: 'Sarala',
                planets: [lord8],
                nature: 'Benefic',
                strength: 7,
                params: { house: 8, lordHouse: lord8House, planet: lord8 }
            }));
        }

        // Vimala Yoga: 12th lord in 6th, 8th, or 12th
        const lord12House = this.getHouse(lord12);
        if (dusthanaHouses.includes(lord12House)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vimala.name'),
                nameKey: 'Vimala',
                category: 'Vipareeta_Raja',
                description: I18n.t('lists.yoga_list.Vimala.effects', {
                    planet: I18n.t('planets.' + lord12),
                    lordHouse: I18n.n(lord12House)
                }),
                descriptionKey: 'Vimala',
                planets: [lord12],
                nature: 'Benefic',
                strength: 7,
                params: { house: 12, lordHouse: lord12House, planet: lord12 }
            }));
        }

        // Combined Viparita Raja: Multiple Dusthana lords together
        if (ctx.isConjunct(lord6, lord8) && dusthanaHouses.includes(this.getHouse(lord6))) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vipareeta_68.name'),
                nameKey: 'Vipareeta_68',
                category: 'Vipareeta_Raja',
                description: I18n.t('lists.yoga_list.Vipareeta_68.effects'),
                descriptionKey: 'Vipareeta_68',
                planets: [lord6, lord8],
                nature: 'Benefic',
                strength: 8,
                params: { h1: 6, h2: 8, planet: lord6, p2: lord8 }
            }));
        }
    }

    /**
     * Special Raja Yogas from classical texts
     */
    _checkSpecialRaja() {
        const ctx = this.ctx;

        // Maha Bhagya Yoga
        this._checkMahaBhagya();

        // Amala Yoga: Benefic in 10th from Lagna or Moon
        const planetsIn10 = ctx.getPlanetsInHouse(10);
        const benefics = this.getNaturalBenefics();
        const beneficsIn10 = planetsIn10.filter(p => benefics.includes(p));

        if (beneficsIn10.length > 0) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Amala.name'),
                nameKey: 'Amala',
                category: 'Raja',
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

        // Parvata Yoga: Lagna and 12th lords in Kendras
        const lord1 = ctx.getHouseLord(1);
        const lord12 = ctx.getHouseLord(12);
        const lord1House = this.getHouse(lord1);
        const lord12House = this.getHouse(lord12);

        if (kendras.includes(lord1House) && kendras.includes(lord12House)) {
            // Additional: Benefics should aspect them or be with them
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Parvata.name'),
                nameKey: 'Parvata',
                category: 'Raja',
                description: I18n.t('lists.yoga_list.Parvata.effects', {
                    planet: I18n.t('planets.' + lord1),
                    p2: I18n.t('planets.' + lord12)
                }),
                descriptionKey: 'Parvata',
                planets: [lord1, lord12],
                nature: 'Benefic',
                strength: 7,
                params: { planet: lord1, p2: lord12 }
            }));
        }

        // Kahala Yoga: 4th lord and Jupiter in Kendras with strong Lagna lord
        const lord4 = ctx.getHouseLord(4);
        const lord4House = this.getHouse(lord4);
        const jupiterHouse = this.getHouse('Jupiter');

        if (kendras.includes(lord4House) && kendras.includes(jupiterHouse)) {
            if (this.isStrong(lord1)) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Kahala.name'),
                    nameKey: 'Kahala',
                    category: 'Raja',
                    description: I18n.t('lists.yoga_list.Kahala.effects', {
                        planet: I18n.t('planets.' + lord4),
                        p2: I18n.t('planets.Jupiter'),
                        p3: I18n.t('planets.' + lord1)
                    }),
                    descriptionKey: 'Kahala',
                    planets: [lord4, 'Jupiter', lord1],
                    nature: 'Benefic',
                    strength: 8,
                    params: { planet: lord4, p2: 'Jupiter', p3: lord1 }
                }));
            }
        }

        // Chamara Yoga: Lagna lord exalted in Kendra, aspected by Jupiter
        const lord1Dignity = this.getDignity(lord1);
        if (lord1Dignity === 'Exalted' && kendras.includes(lord1House)) {
            if (ctx.aspects('Jupiter', lord1)) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Chamara.name'),
                    nameKey: 'Chamara',
                    category: 'Raja',
                    description: I18n.t('lists.yoga_list.Chamara.effects', {
                        planet: I18n.t('planets.' + lord1),
                        ref: I18n.t('planets.Jupiter')
                    }),
                    descriptionKey: 'Chamara',
                    planets: [lord1, 'Jupiter'],
                    nature: 'Benefic',
                    strength: 9,
                    params: { planet: lord1, ref: 'Jupiter' }
                }));
            }
        }
    }

    /**
     * Check Maha Bhagya Yoga (Great Fortune)
     */
    _checkMahaBhagya() {
        const ctx = this.ctx;

        // Get birth details
        const sunRasi = this.getRasi('Sun');
        const moonRasi = this.getRasi('Moon');
        const lagnaRasi = ctx.lagnaRasi !== undefined ? ctx.lagnaRasi : this.getRasi('Asc');

        // Odd signs (male): 0, 2, 4, 6, 8, 10 (Aries, Gemini, Leo, Libra, Sagittarius, Aquarius)
        // Even signs (female): 1, 3, 5, 7, 9, 11 (Taurus, Cancer, Virgo, Scorpio, Capricorn, Pisces)
        const isOdd = (sign) => sign !== -1 && sign % 2 === 0;
        const isEven = (sign) => sign !== -1 && sign % 2 === 1;

        // For male birth during day: Sun, Moon, Lagna all in odd signs
        // For female birth during night: Sun, Moon, Lagna all in even signs
        const isDayBirth = ctx.isDaytime;

        if (isDayBirth !== null) {
            if (isDayBirth && isOdd(sunRasi) && isOdd(moonRasi) && isOdd(lagnaRasi)) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Maha_Bhagya.name'),
                    nameKey: 'Maha_Bhagya',
                    category: 'Raja',
                    description: I18n.t('lists.yoga_list.Maha_Bhagya.effects'),
                    descriptionKey: 'Maha_Bhagya',
                    planets: ['Sun', 'Moon'],
                    nature: 'Benefic',
                    strength: 9
                }));
            }

            if (!isDayBirth && isEven(sunRasi) && isEven(moonRasi) && isEven(lagnaRasi)) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Maha_Bhagya_F.name'),
                    nameKey: 'Maha_Bhagya_F',
                    category: 'Raja',
                    description: I18n.t('lists.yoga_list.Maha_Bhagya_F.effects'),
                    descriptionKey: 'Maha_Bhagya_F',
                    planets: ['Sun', 'Moon'],
                    nature: 'Benefic',
                    strength: 9
                }));
            }
        }
    }

    /**
     * Parivartana (Exchange) Raja Yogas
     */
    _checkParivartanaRaja() {
        const ctx = this.ctx;
        const houses = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];

        // Check all house pairs for exchange
        for (let i = 0; i < houses.length; i++) {
            for (let j = i + 1; j < houses.length; j++) {
                const house1 = houses[i];
                const house2 = houses[j];
                const lord1 = ctx.getHouseLord(house1);
                const lord2 = ctx.getHouseLord(house2);

                if (!lord1 || !lord2 || lord1 === lord2) continue;

                const lord1InHouse = this.getHouse(lord1);
                const lord2InHouse = this.getHouse(lord2);

                // Check for exchange
                if (lord1InHouse === house2 && lord2InHouse === house1) {
                    // Determine type of Parivartana
                    const isKendraExchange = kendras.includes(house1) && kendras.includes(house2);
                    const isTrikonaExchange = trikonas.includes(house1) && trikonas.includes(house2);
                    const isKendraTrikonaExchange =
                        (kendras.includes(house1) && trikonas.includes(house2)) ||
                        (trikonas.includes(house1) && kendras.includes(house2));
                    const isDusthanaInvolved = dusthanas.includes(house1) || dusthanas.includes(house2);

                    // Skip if dusthana involved (will create different yoga)
                    if (isDusthanaInvolved) continue;

                    let key, strength;
                    if (isKendraTrikonaExchange) {
                        key = 'Maha_Parivartana';
                        strength = 9;
                    } else if (isKendraExchange || isTrikonaExchange) {
                        key = 'Parivartana_Raja';
                        strength = 8;
                    } else {
                        key = 'Parivartana';
                        strength = 6;
                    }

                    this.addYoga(createYoga({
                        name: I18n.t(`lists.yoga_list.${key}.name`, { h1: I18n.n(house1), h2: I18n.n(house2) }),
                        nameKey: key,
                        category: 'Raja',
                        description: I18n.t(`lists.yoga_list.${key}.effects`, {
                            h1: I18n.n(house1),
                            planet: I18n.t('planets.' + lord1),
                            h2: I18n.n(house2),
                            p2: I18n.t('planets.' + lord2)
                        }),
                        descriptionKey: key,
                        planets: [lord1, lord2],
                        nature: 'Benefic',
                        strength,
                        params: { h1: house1, h2: house2, planet: lord1, p2: lord2 }
                    }));
                }
            }
        }
    }

    /**
     * Enhanced Mahapurusha Yogas with strength factors
     */
    _checkMahapurushaEnhanced() {
        const ctx = this.ctx;
        const mahapurushaConditions = {
            Mars: { yoga: 'Ruchaka', sign: [0, 7, 9], kendraReq: true },
            Mercury: { yoga: 'Bhadra', sign: [2, 5], kendraReq: true },
            Jupiter: { yoga: 'Hamsa', sign: [3, 8, 11], kendraReq: true },
            Venus: { yoga: 'Malavya', sign: [1, 6, 11], kendraReq: true },
            Saturn: { yoga: 'Shasha', sign: [6, 9, 10], kendraReq: true }
        };

        for (const [planet, config] of Object.entries(mahapurushaConditions)) {
            const sign = this.getRasi(planet);
            const house = this.getHouse(planet);
            const dignity = this.getDignity(planet);

            // Check if planet is in required sign and in Kendra
            if (config.sign.includes(sign) && kendras.includes(house)) {
                // Calculate strength enhancement
                let strength = 7;
                if (dignity === 'Exalted') strength = 9;
                else if (dignity === 'Moolatrikona') strength = 8;
                else if (dignity === 'Own') strength = 7.5;

                // Additional strength for aspects
                if (ctx.aspects('Jupiter', planet) && planet !== 'Jupiter') strength += 0.5;

                // Reduce for combustion/retrograde
                if (this.isCombust(planet)) strength -= 1;
                if (this.isRetrograde(planet)) strength += 0.5; // Retrograde in dignity = stronger

                this.addYoga(createYoga({
                    name: I18n.t(`lists.yoga_list.${config.yoga}.name`),
                    nameKey: config.yoga,
                    category: 'Mahapurusha',
                    description: I18n.t(`lists.yoga_list.${config.yoga}.effects`, {
                        planet: I18n.t('planets.' + planet),
                        dignity: I18n.t('kundali.' + (dignity || 'own').toLowerCase()),
                        house: I18n.n(house)
                    }),
                    descriptionKey: config.yoga,
                    planets: [planet],
                    nature: 'Benefic',
                    strength: Math.min(10, strength),
                    params: { planet, house, dignity: dignity || 'Own' }
                }));
            }
        }
    }

    /**
     * Get Mahapurusha yoga effects
     */
    _getMahapurushaEffect(yoga) {
        const effects = {
            Ruchaka: 'commanding presence, courage, military/athletic prowess, leadership in action.',
            Bhadra: 'sharp intellect, eloquent speech, success in commerce, skilled communication.',
            Hamsa: 'wisdom, righteous conduct, spiritual inclination, respected teacher/guide.',
            Malavya: 'artistic talents, luxury, attractive personality, success in arts/beauty.',
            Shasha: 'authority over masses, discipline, longevity, political/administrative success.'
        };
        return effects[yoga] || '';
    }

    /**
     * Aditya-di Yogas (Sun-based Raja Yogas)
     */
    _checkAdityadiYogas() {
        const ctx = this.ctx;
        const sunHouse = this.getHouse('Sun');
        const sunRasi = this.getRasi('Sun');

        // Vesi Yoga: Planet (not Moon) in 2nd from Sun
        const planetsIn2FromSun = this._getPlanetsInHouseFromPlanet('Sun', 2);
        const vesiPlanets = planetsIn2FromSun.filter(p => p !== 'Moon');
        if (vesiPlanets.length > 0) {
            const hasBenefic = vesiPlanets.some(p => ctx.getNaturalBenefics().includes(p));
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vesi.name'),
                nameKey: 'Vesi',
                category: 'Solar',
                description: I18n.t('lists.yoga_list.Vesi.effects', {
                    planets: vesiPlanets.map(p => I18n.t('planets.' + p)).join(', ')
                }),
                descriptionKey: 'Vesi',
                planets: ['Sun', ...vesiPlanets],
                nature: hasBenefic ? 'Benefic' : 'Neutral',
                strength: hasBenefic ? 7 : 5,
                params: { planet: 'Sun', planets: vesiPlanets.join(', ') }
            }));
        }

        // Vasi Yoga: Planet (not Moon) in 12th from Sun
        const planetsIn12FromSun = this._getPlanetsInHouseFromPlanet('Sun', 12);
        const vasiPlanets = planetsIn12FromSun.filter(p => p !== 'Moon');
        if (vasiPlanets.length > 0) {
            const hasBenefic = vasiPlanets.some(p => ctx.getNaturalBenefics().includes(p));
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vasi.name'),
                nameKey: 'Vasi',
                category: 'Solar',
                description: I18n.t('lists.yoga_list.Vasi.effects', {
                    planets: vasiPlanets.map(p => I18n.t('planets.' + p)).join(', ')
                }),
                descriptionKey: 'Vasi',
                planets: ['Sun', ...vasiPlanets],
                nature: hasBenefic ? 'Benefic' : 'Neutral',
                strength: hasBenefic ? 7 : 5,
                params: { planet: 'Sun', planets: vasiPlanets.join(', ') }
            }));
        }

        // Ubhayachari Yoga: Planets on both sides of Sun
        if (vesiPlanets.length > 0 && vasiPlanets.length > 0) {
            const allBenefic = [...vesiPlanets, ...vasiPlanets].every(p =>
                ctx.getNaturalBenefics().includes(p) || p === 'Mercury'
            );

            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Ubhayachari.name'),
                nameKey: 'Ubhayachari',
                category: 'Solar',
                description: I18n.t('lists.yoga_list.Ubhayachari.effects', {
                    planets: [...vesiPlanets, ...vasiPlanets].map(p => I18n.t('planets.' + p)).join(', ')
                }),
                descriptionKey: 'Ubhayachari',
                planets: ['Sun', ...vesiPlanets, ...vasiPlanets],
                nature: allBenefic ? 'Benefic' : 'Neutral',
                strength: allBenefic ? 8 : 6,
                params: { planet: 'Sun', planets: [...vesiPlanets, ...vasiPlanets].join(', ') }
            }));
        }
    }

    /**
     * Named Raja Yogas from classical texts
     */
    _checkNamedRajaYogas() {
        const ctx = this.ctx;

        // Akhanda Samrajya Yoga
        const lord2 = ctx.getHouseLord(2);
        const lord5 = ctx.getHouseLord(5);
        const lord9 = ctx.getHouseLord(9);
        const lord11 = ctx.getHouseLord(11);

        const jupiterRulesWealthHouse = (lord2 === 'Jupiter' || lord5 === 'Jupiter' || lord11 === 'Jupiter');
        const jupiterInKendra = kendras.includes(ctx.getHouse('Jupiter'));

        if (jupiterRulesWealthHouse && jupiterInKendra) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Akhanda_Samrajya.name'),
                nameKey: 'Akhanda_Samrajya',
                category: 'Raja',
                description: I18n.t('lists.yoga_list.Akhanda_Samrajya.effects'),
                descriptionKey: 'Akhanda_Samrajya',
                planets: ['Jupiter'],
                nature: 'Benefic',
                strength: 9,
                params: { planet: 'Jupiter' }
            }));
        }

        // Sankha Yoga: 5th and 6th lords in mutual Kendras
        const lord6 = ctx.getHouseLord(6);
        const lord5House = this.getHouse(lord5);
        const lord6House = this.getHouse(lord6);

        if (kendras.includes(lord5House) && kendras.includes(lord6House)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Sankha.name'),
                nameKey: 'Sankha',
                category: 'Raja',
                description: I18n.t('lists.yoga_list.Sankha.effects', {
                    planet: I18n.t('planets.' + lord5),
                    p2: I18n.t('planets.' + lord6)
                }),
                descriptionKey: 'Sankha',
                planets: [lord5, lord6],
                nature: 'Benefic',
                strength: 7,
                params: { planet: lord5, p2: lord6 }
            }));
        }

        // Bheri Yoga: Venus, Jupiter, and Lagna lord strong with 9th lord in Kendra
        const lord1 = ctx.getHouseLord(1);
        const lord9House = this.getHouse(lord9);

        if (kendras.includes(lord9House)) {
            const venusStrong = this.isStrong('Venus');
            const jupiterStrong = this.isStrong('Jupiter');
            const lord1Strong = this.isStrong(lord1);

            if ((venusStrong || jupiterStrong) && lord1Strong) {
                this.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Bheri.name'),
                    nameKey: 'Bheri',
                    category: 'Raja',
                    description: I18n.t('lists.yoga_list.Bheri.effects'),
                    descriptionKey: 'Bheri',
                    planets: ['Venus', 'Jupiter', lord1, lord9],
                    nature: 'Benefic',
                    strength: 8,
                    params: { planets: ['Venus', 'Jupiter', lord1, lord9].join(', ') }
                }));
            }
        }

        // Mridanga Yoga: All planets in Kendras or Trikonas
        const sevenPlanetsList = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
        const allInKendraTrikona = sevenPlanetsList.every(p => {
            const h = this.getHouse(p);
            return [...kendras, ...trikonas].includes(h);
        });

        if (allInKendraTrikona && this.isStrong(lord1)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Mridanga.name'),
                nameKey: 'Mridanga',
                category: 'Raja',
                description: I18n.t('lists.yoga_list.Mridanga.effects'),
                descriptionKey: 'Mridanga',
                planets: sevenPlanetsList,
                nature: 'Benefic',
                strength: 9,
                params: { planet: lord1 }
            }));
        }

        // Chatussagara Yoga: All Kendras occupied
        const kendraOccupancy = kendras.map(k => ctx.getPlanetsInHouse(k).length > 0);
        if (kendraOccupancy.every(Boolean)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Chatussagara.name'),
                nameKey: 'Chatussagara',
                category: 'Raja',
                description: I18n.t('lists.yoga_list.Chatussagara.effects'),
                descriptionKey: 'Chatussagara',
                planets: kendras.flatMap(k => ctx.getPlanetsInHouse(k)),
                nature: 'Benefic',
                strength: 8
            }));
        }
    }

    /**
     * Ascendant-specific Raja Yogas
     */
    _checkAscendantSpecificRaja() {
        const ctx = this.ctx;
        const lagnaSign = ctx.lagnaRasi !== undefined ? ctx.lagnaRasi : -1;

        if (lagnaSign === -1) return;

        // Yogakaraka planet check
        let yogakaraka = null;
        if (lagnaSign === 1 || lagnaSign === 6) { // Taurus or Libra
            yogakaraka = 'Saturn';
        } else if (lagnaSign === 3 || lagnaSign === 4) { // Cancer or Leo
            yogakaraka = 'Mars';
        }

        if (yogakaraka) {
            const ykHouse = this.getHouse(yogakaraka);
            const ykDignity = this.getDignity(yogakaraka);

            if (kendras.includes(ykHouse) || trikonas.includes(ykHouse)) {
                let strength = 7;
                if (['Exalted', 'Own', 'Moolatrikona'].includes(ykDignity)) strength = 9;

                const signNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];

                this.addYoga(createYoga({
                    name: `Yogakaraka ${yogakaraka} Yoga`,
                    nameKey: 'Yogakaraka',
                    category: 'Raja',
                    description: `${yogakaraka} is Yogakaraka for ${signNames[lagnaSign]} ascendant, placed in ${ykHouse}th house ${ykDignity !== 'neutral' ? `(${ykDignity})` : ''}. Rules both Kendra and Trikona - exceptional Raja Yoga results.`,
                    descriptionKey: 'Yogakaraka',
                    planets: [yogakaraka],
                    nature: 'Benefic',
                    strength
                }));
            }
        }
    }

    /**
     * Calculate Raja Yoga strength
     */
    _calculateRajaStrength(planet1, planet2, house = null) {
        let strength = 5;

        // House placement bonus
        if (house) {
            if (kendras.includes(house)) strength += 1.5;
            else if (trikonas.includes(house)) strength += 1;
            else if (dusthanas.includes(house)) strength -= 1;
        }

        // Dignity bonuses
        const dig1 = this.getDignity(planet1);
        const dig2 = this.getDignity(planet2);

        if (dig1 === 'Exalted') strength += 1.5;
        else if (dig1 === 'Own' || dig1 === 'Moolatrikona') strength += 1;
        else if (dig1 === 'Debilitated') strength -= 1;

        if (dig2 === 'Exalted') strength += 1.5;
        else if (dig2 === 'Own' || dig2 === 'Moolatrikona') strength += 1;
        else if (dig2 === 'Debilitated') strength -= 1;

        // Combustion penalty
        if (this.isCombust(planet1)) strength -= 0.5;
        if (this.isCombust(planet2)) strength -= 0.5;

        return Math.max(3, Math.min(10, strength));
    }

    /**
     * Get planets in house from reference planet
     */
    _getPlanetsInHouseFromPlanet(refPlanet, houseNumber) {
        const refRasi = this.getRasi(refPlanet);
        if (refRasi === -1) return [];

        const sevenPlanets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
        const result = [];

        for (const planet of sevenPlanets) {
            if (planet === refPlanet) continue;
            const planetRasi = this.getRasi(planet);
            if (planetRasi === -1) continue;

            let diff = planetRasi - refRasi;
            if (diff < 0) diff += 12;
            const house = diff + 1;

            if (house === houseNumber) {
                result.push(planet);
            }
        }

        return result;
    }
}

export default RajaComprehensiveYogas;
