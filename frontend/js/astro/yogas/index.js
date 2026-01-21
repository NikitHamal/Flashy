/**
 * Yoga Engine Index
 * Main entry point that orchestrates all yoga module calculations
 */

import I18n from '../../core/i18n.js';
import {
    signLords, exaltation, debilitation, ownSigns, moolatrikona,
    combustionOrbs, planetaryAspects, sevenPlanets, fiveNonLuminaries,
    allPlanets, kendras, trikonas, dusthanas, upachayas, createYoga
} from './base.js';

// Import all yoga modules
import { KaalSarpaYogas } from './kaal_sarpa.js';
import { NabhasaAkritiYogas } from './nabhasa_akriti.js';
import { RajaYogas } from './raja.js';
import { DhanaYogas } from './dhana.js';
import { DoshaYogas } from './doshas.js';
import { KartariYogas } from './kartari.js';
import { SanyasaYogas } from './sanyasa.js';
import { LongevityYogas } from './longevity.js';
import { MarriageYogas } from './marriage.js';
import { ProgenyYogas } from './progeny.js';
import { EducationYogas } from './education.js';
import { CareerYogas } from './career.js';
import { PlanetaryCombinationYogas } from './planetary_combinations.js';
import { SpiritualYogas } from './spiritual.js';
import { VargottamaYogas } from './vargottama.js';
import { AdvancedYogas } from './advanced.js';
import { ArishtaYogas } from './arishta.js';
import { SpecialClassicalYogas } from './special_classical.js';
import { NabhasaSankhyaYogas } from './nabhasa_sankhya.js';
import { NeechaBhangaYogas } from './neecha_bhanga.js';
import { DaridraYogas } from './daridra.js';
import { RajaComprehensiveYogas } from './raja_comprehensive.js';
import { DhanaComprehensiveYogas } from './dhana_comprehensive.js';
import { BandhanaYogas } from './bandhana.js';
import { StrengthEngine } from './strength_engine.js';
import StrengthHierarchy from './strength_hierarchy.js';

/**
 * Main Yoga Engine class
 * Coordinates all yoga calculations
 */
class YogaEngine {
    constructor() {
        this.moduleClasses = [
            KaalSarpaYogas,
            NabhasaAkritiYogas,
            NabhasaSankhyaYogas,
            RajaYogas,
            RajaComprehensiveYogas,
            DhanaYogas,
            DhanaComprehensiveYogas,
            DoshaYogas,
            KartariYogas,
            SanyasaYogas,
            LongevityYogas,
            MarriageYogas,
            ProgenyYogas,
            EducationYogas,
            CareerYogas,
            PlanetaryCombinationYogas,
            SpiritualYogas,
            VargottamaYogas,
            AdvancedYogas,
            ArishtaYogas,
            SpecialClassicalYogas,
            NeechaBhangaYogas,
            DaridraYogas,
            BandhanaYogas
        ];
    }

    /**
     * Main check method - calculates all yogas
     * @param {Object} data - Chart data
     * @returns {Object} { yogas: [], summary: {} }
     */
    check(data) {
        let yogas = [];
        const ctx = this._buildContext(data, yogas);

        // Run all yoga modules
        for (const ModuleClass of this.moduleClasses) {
            try {
                const module = new ModuleClass(ctx);
                module.check();
            } catch (e) {
                console.warn(`Error in yoga module ${ModuleClass.name}:`, e);
            }
        }

        // Run remaining legacy yogas not yet modularized
        this._checkLegacyYogas(ctx);

        // Calculate Strength & Activation
        const strengthEngine = new StrengthEngine(ctx);
        yogas = strengthEngine.process(yogas);

        // Apply Hierarchy Ranking
        yogas = StrengthHierarchy.applyHierarchy(yogas);

        // Generate summary
        const summary = this._generateSummary(yogas);

        return { yogas, summary };
    }

    /**
     * Check legacy yogas that haven't been fully modularized yet
     */
    _checkLegacyYogas(ctx) {
        this._checkLunarYogas(ctx);
        this._checkVipareetaRajaYogas(ctx);
        this._checkParivartanaYoga(ctx);
        this._checkChandalYoga(ctx);
    }

    /**
     * Build calculation context from chart data
     */
    _buildContext(data, yogas) {
        const positions = data.planets || {};
        const lagnaRasi = data.lagnaRasi ?? 0;

        // Build sign-to-houses map
        const signToHouse = {};
        for (let i = 0; i < 12; i++) {
            signToHouse[(lagnaRasi + i) % 12] = i + 1;
        }

        // Pre-calculate Moon position
        const moonRasi = positions['Moon']?.sign ?? 0;
        const sunRasi = positions['Sun']?.sign ?? 0;

        // Build houses map
        const planetsByHouse = {};
        for (let h = 1; h <= 12; h++) {
            planetsByHouse[h] = [];
        }
        for (const [planet, pos] of Object.entries(positions)) {
            if (pos && typeof pos.sign === 'number') {
                const house = signToHouse[pos.sign];
                if (house) {
                    planetsByHouse[house].push(planet);
                }
            }
        }

        // Shadbala reference (if available)
        const shadbala = data.shadbala || {};
        
        // Avastha reference
        const avasthas = data.avasthas || {};

        // Context object with all helper methods
        const ctx = {
            positions,
            lagnaRasi,
            moonRasi,
            sunRasi,
            signToHouse,
            planetsByHouse,
            shadbala,
            avasthas,
            navamshaPositions: data.navamshaPositions || null,
            navamshaLagna: data.navamshaLagna ?? null,

            // Get sign index for planet (0-11)
            getRasi: (planet) => positions[planet]?.sign ?? -1,

            // Get house number from reference (default: Lagna)
            getHouse: (planet, ref = lagnaRasi) => {
                const sign = positions[planet]?.sign;
                if (sign === undefined) return -1;
                return ((sign - ref + 12) % 12) + 1;
            },

            // Get degree within sign
            getDegree: (planet) => positions[planet]?.degree ?? NaN,

            // Get absolute longitude
            getLongitude: (planet) => {
                const pos = positions[planet];
                if (!pos) return NaN;
                return (pos.sign * 30) + (pos.degree || 0);
            },

            // Check if planet is in specific houses
            inHouse: (planet, houses, ref = lagnaRasi) => {
                const h = ctx.getHouse(planet, ref);
                return houses.includes(h);
            },

            // Check conjunction (same sign)
            isConjunct: (p1, p2) => {
                const s1 = ctx.getRasi(p1);
                const s2 = ctx.getRasi(p2);
                return s1 !== -1 && s1 === s2;
            },

            // Check aspect
            aspects: (fromPlanet, toPlanet) => {
                const fromSign = ctx.getRasi(fromPlanet);
                const toSign = ctx.getRasi(toPlanet);
                if (fromSign === -1 || toSign === -1) return false;

                const aspectHouses = planetaryAspects[fromPlanet] || [7];
                for (const asp of aspectHouses) {
                    const aspectedSign = (fromSign + asp - 1) % 12;
                    if (aspectedSign === toSign) return true;
                }
                return false;
            },

            // Check mutual aspect
            mutualAspect: (p1, p2) => ctx.aspects(p1, p2) && ctx.aspects(p2, p1),

            // Check connection (conjunction or aspect)
            isConnected: (p1, p2) => ctx.isConjunct(p1, p2) || ctx.aspects(p1, p2) || ctx.aspects(p2, p1),

            // Get house lord
            getHouseLord: (house, ref = lagnaRasi) => {
                const sign = (ref + house - 1) % 12;
                return signLords[sign];
            },

            // Get sign lord
            getSignLord: (sign) => signLords[sign],

            // Check retrograde
            isRetrograde: (planet) => positions[planet]?.retrograde ?? false,

            // Get dignity
            getDignity: (planet) => {
                const sign = ctx.getRasi(planet);
                const deg = ctx.getDegree(planet);
                if (sign === -1) return 'Unknown';

                // Exaltation
                const exalt = exaltation[planet];
                if (exalt && exalt.sign === sign) return 'Exalted';

                // Debilitation
                if (debilitation[planet] === sign) return 'Debilitated';

                // Own sign
                if (ownSigns[planet]?.includes(sign)) return 'Own';

                // Moolatrikona
                const moola = moolatrikona[planet];
                if (moola && moola.sign === sign && deg >= moola.start && deg <= moola.end) {
                    return 'Moolatrikona';
                }

                return 'Neutral';
            },

            // Check combustion
            isCombust: (planet) => {
                if (planet === 'Sun' || planet === 'Rahu' || planet === 'Ketu') return false;
                const sunLon = ctx.getLongitude('Sun');
                const planetLon = ctx.getLongitude(planet);
                if (isNaN(sunLon) || isNaN(planetLon)) return false;

                let diff = Math.abs(sunLon - planetLon);
                if (diff > 180) diff = 360 - diff;

                const retro = ctx.isRetrograde(planet);
                let orb = combustionOrbs[planet];
                if (retro && planet === 'Mercury') orb = combustionOrbs['MercuryRetro'];
                if (retro && planet === 'Venus') orb = combustionOrbs['VenusRetro'];

                return diff <= (orb || 10);
            },

            // Get planets in house
            getPlanetsInHouse: (house, ref = lagnaRasi) => {
                const targetSign = (ref + house - 1) % 12;
                const result = [];
                for (const [planet, pos] of Object.entries(positions)) {
                    if (pos && pos.sign === targetSign) {
                        result.push(planet);
                    }
                }
                return result;
            },

            // Check waxing Moon
            isWaxingMoon: () => {
                const moonLon = ctx.getLongitude('Moon');
                const sunLon = ctx.getLongitude('Sun');
                if (isNaN(moonLon) || isNaN(sunLon)) return true; // Default
                const phase = (moonLon - sunLon + 360) % 360;
                return phase < 180;
            },

            // Get natural benefics
            getNaturalBenefics: () => {
                const result = ['Jupiter', 'Venus'];
                // Waxing Moon is benefic
                if (ctx.isWaxingMoon()) result.push('Moon');
                // Well-associated Mercury is benefic
                const mercSign = ctx.getRasi('Mercury');
                const jupSign = ctx.getRasi('Jupiter');
                const venSign = ctx.getRasi('Venus');
                if (mercSign === jupSign || mercSign === venSign) {
                    result.push('Mercury');
                }
                return result;
            },

            // Get natural malefics
            getNaturalMalefics: () => {
                const result = ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu'];
                // Waning Moon is malefic
                if (!ctx.isWaxingMoon()) result.push('Moon');
                return result;
            },

            // Get strength from Shadbala
            getStrength: (planets) => {
                if (!shadbala || Object.keys(shadbala).length === 0) {
                    return 5; // Default mid-strength
                }
                let total = 0;
                let count = 0;
                for (const p of planets) {
                    if (shadbala[p]?.total) {
                        total += shadbala[p].total;
                        count++;
                    }
                }
                return count > 0 ? Math.min(10, Math.max(1, total / count)) : 5;
            },

            // Check if planet is strong via Shadbala
            isStrong: (planet) => {
                if (!shadbala || !shadbala[planet]) {
                    // Fallback: check dignity
                    const dig = ctx.getDignity(planet);
                    return ['Exalted', 'Own', 'Moolatrikona'].includes(dig);
                }
                return shadbala[planet].total >= 1.0;
            },

            // Add yoga to results
            addYoga: (yoga) => {
                // Check for duplicates by name
                if (!yogas.some(y => y.name === yoga.name)) {
                    yogas.push(yoga);
                }
            }
        };

        return ctx;
    }

    /**
     * Lunar Yogas (Sunapha, Anapha, Durudhara, Kemadruma)
     */
    _checkLunarYogas(ctx) {
        const moonSign = ctx.moonRasi;
        const planetsExceptSun = sevenPlanets.filter(p => p !== 'Sun' && p !== 'Moon');

        const in2ndFromMoon = planetsExceptSun.filter(p => ctx.getHouse(p, moonSign) === 2);
        const in12thFromMoon = planetsExceptSun.filter(p => ctx.getHouse(p, moonSign) === 12);

        if (in2ndFromMoon.length > 0 && in12thFromMoon.length > 0) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Durudhara.name'),
                nameKey: 'Durudhara',
                category: 'Lunar',
                description: I18n.t('lists.yoga_list.Durudhara.effects'),
                descriptionKey: 'Durudhara',
                planets: ['Moon', ...in2ndFromMoon, ...in12thFromMoon],
                nature: 'Benefic',
                strength: 7
            }));
        } else if (in2ndFromMoon.length > 0) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Sunapha.name'),
                nameKey: 'Sunapha',
                category: 'Lunar',
                description: I18n.t('lists.yoga_list.Sunapha.effects', { planets: in2ndFromMoon.map(p => I18n.t('planets.' + p)).join(', ') }),
                descriptionKey: 'Sunapha',
                planets: ['Moon', ...in2ndFromMoon],
                nature: 'Benefic',
                strength: 6,
                params: { planets: in2ndFromMoon.join(', ') }
            }));
        } else if (in12thFromMoon.length > 0) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Anapha.name'),
                nameKey: 'Anapha',
                category: 'Lunar',
                description: I18n.t('lists.yoga_list.Anapha.effects', { planets: in12thFromMoon.map(p => I18n.t('planets.' + p)).join(', ') }),
                descriptionKey: 'Anapha',
                planets: ['Moon', ...in12thFromMoon],
                nature: 'Benefic',
                strength: 6,
                params: { planets: in12thFromMoon.join(', ') }
            }));
        } else {
            // Kemadruma Yoga
            const moonInKendra = kendras.includes(ctx.getHouse('Moon'));
            const jupInKendra = kendras.includes(ctx.getHouse('Jupiter'));

            if (moonInKendra || jupInKendra) {
                const planet = moonInKendra ? I18n.t('planets.Moon') : I18n.t('planets.Jupiter');
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Kemadruma_Bhanga.name'),
                    nameKey: 'Kemadruma_Bhanga',
                    category: 'Lunar',
                    description: I18n.t('lists.yoga_list.Kemadruma_Bhanga.effects', { planet }),
                    descriptionKey: 'Kemadruma_Bhanga',
                    planets: ['Moon'],
                    nature: 'Neutral',
                    strength: 5,
                    params: { planet: moonInKendra ? 'Moon' : 'Jupiter' }
                }));
            } else {
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Kemadruma.name'),
                    nameKey: 'Kemadruma',
                    category: 'Lunar',
                    description: I18n.t('lists.yoga_list.Kemadruma.effects', { planet: I18n.t('planets.Moon') }),
                    descriptionKey: 'Kemadruma',
                    planets: ['Moon'],
                    nature: 'Malefic',
                    strength: 3,
                    params: { planet: 'Moon' }
                }));
            }
        }

        // Chandra-Mangala Yoga
        if (ctx.isConjunct('Moon', 'Mars')) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Chandra_Mangala.name'),
                nameKey: 'Chandra_Mangala',
                category: 'Lunar',
                description: I18n.t('lists.yoga_list.Chandra_Mangala.effects', { planet: I18n.t('planets.Moon'), p2: I18n.t('planets.Mars') }),
                descriptionKey: 'Chandra_Mangala',
                planets: ['Moon', 'Mars'],
                nature: 'Benefic',
                strength: ctx.getStrength(['Moon', 'Mars']),
                params: { planet: 'Moon', p2: 'Mars' }
            }));
        }
    }

    /**
     * Vipareeta Raja Yogas
     */
    _checkVipareetaRajaYogas(ctx) {
        const viparitaDefs = [
            { house: 6, key: 'Harsha' },
            { house: 8, key: 'Sarala' },
            { house: 12, key: 'Vimala' }
        ];

        for (const { house, key } of viparitaDefs) {
            const lord = ctx.getHouseLord(house);
            const lordHouse = ctx.getHouse(lord);

            if (dusthanas.includes(lordHouse) && !ctx.isCombust(lord)) {
                ctx.addYoga(createYoga({
                    name: I18n.t(`lists.yoga_list.${key}.name`),
                    nameKey: key,
                    category: 'Vipareeta_Raja',
                    description: I18n.t(`lists.yoga_list.${key}.effects`, { planet: I18n.t('planets.' + lord), lordHouse: I18n.n(lordHouse) }),
                    descriptionKey: key,
                    planets: [lord],
                    nature: 'Benefic',
                    strength: 6,
                    params: { house, lordHouse, planet: lord }
                }));
            }
        }
    }

    /**
     * Parivartana Yoga (Exchange of signs)
     */
    _checkParivartanaYoga(ctx) {
        const exchanges = [];

        for (let h1 = 1; h1 <= 12; h1++) {
            const lord1 = ctx.getHouseLord(h1);
            const lord1House = ctx.getHouse(lord1);

            if (lord1House !== h1 && lord1House >= 1 && lord1House <= 12) {
                const lord2 = ctx.getHouseLord(lord1House);
                if (ctx.getHouse(lord2) === h1) {
                    const h2 = lord1House;
                    if (h1 < h2) {
                        exchanges.push({ h1, h2, lord1, lord2 });
                    }
                }
            }
        }

        for (const { h1, h2, lord1, lord2 } of exchanges) {
            const kendraTrikona = [...kendras, ...trikonas];
            const bothGood = kendraTrikona.includes(h1) && kendraTrikona.includes(h2);
            const bothBad = dusthanas.includes(h1) && dusthanas.includes(h2);
            const oneBad = dusthanas.includes(h1) || dusthanas.includes(h2);

            let key, nature;
            if (bothGood) {
                key = 'Maha_Parivartana';
                nature = 'Benefic';
            } else if (bothBad) {
                key = 'Viparita_Parivartana';
                nature = 'Benefic';
            } else if (oneBad) {
                key = 'Dainya_Parivartana';
                nature = 'Neutral';
            } else {
                key = 'Parivartana';
                nature = 'Benefic';
            }

            ctx.addYoga(createYoga({
                name: I18n.t(`lists.yoga_list.${key}.name`, { h1: I18n.n(h1), h2: I18n.n(h2) }),
                nameKey: key,
                category: 'Parivartana',
                description: I18n.t(`lists.yoga_list.${key}.effects`, { 
                    h1: I18n.n(h1), 
                    h2: I18n.n(h2), 
                    planet: I18n.t('planets.' + lord1), 
                    p2: I18n.t('planets.' + lord2) 
                }),
                descriptionKey: key,
                planets: [lord1, lord2],
                nature,
                strength: bothGood ? 8 : 6,
                params: { h1, h2, planet: lord1, p2: lord2 }
            }));
        }
    }

    /**
     * Chandal Yoga (Guru Chandal, Grahan)
     */
    _checkChandalYoga(ctx) {
        // Guru Chandal
        const jupRahuConj = ctx.isConjunct('Jupiter', 'Rahu');
        const jupKetuConj = ctx.isConjunct('Jupiter', 'Ketu');

        if (jupRahuConj) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Guru_Chandal_Rahu.name'),
                nameKey: 'Guru_Chandal_Rahu',
                category: 'Chandal',
                description: I18n.t('lists.yoga_list.Guru_Chandal_Rahu.effects', { planet: I18n.t('planets.Rahu') }),
                descriptionKey: 'Guru_Chandal_Rahu',
                planets: ['Jupiter', 'Rahu'],
                nature: 'Neutral',
                strength: 4,
                params: { planet: 'Rahu' }
            }));
        }

        if (jupKetuConj) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Guru_Chandal_Ketu.name'),
                nameKey: 'Guru_Chandal_Ketu',
                category: 'Chandal',
                description: I18n.t('lists.yoga_list.Guru_Chandal_Ketu.effects', { planet: I18n.t('planets.Ketu') }),
                descriptionKey: 'Guru_Chandal_Ketu',
                planets: ['Jupiter', 'Ketu'],
                nature: 'Neutral',
                strength: 5,
                params: { planet: 'Ketu' }
            }));
        }
    }

    /**
     * Generate summary of all yogas
     */
    _generateSummary(yogas) {
        const benefic = yogas.filter(y => y.nature === 'Benefic').length;
        const malefic = yogas.filter(y => y.nature === 'Malefic').length;
        const neutral = yogas.filter(y => y.nature === 'Neutral').length;

        const raja = yogas.filter(y => y.category === 'Raja' || y.category === 'Mahapurusha').length;
        const dhana = yogas.filter(y => y.category === 'Dhana').length;

        const strengths = yogas.map(y => y.strength).filter(s => !isNaN(s));
        const avgStrength = strengths.length > 0
            ? strengths.reduce((a, b) => a + b, 0) / strengths.length
            : 5;

        // Determine overall mood
        let mood = 'Balanced';
        if (benefic > malefic * 2 && raja >= 2) {
            mood = 'Highly_Auspicious';
        } else if (benefic > malefic) {
            mood = 'Auspicious';
        } else if (malefic > benefic * 2) {
            mood = 'Challenging';
        } else if (malefic > benefic) {
            mood = 'Mixed_Challenges';
        }

        return {
            count: yogas.length,
            benefic,
            malefic,
            neutral,
            raja,
            dhana,
            avgStrength: parseFloat(avgStrength.toFixed(2)),
            mood
        };
    }
}

// Export singleton instance
export default new YogaEngine();
