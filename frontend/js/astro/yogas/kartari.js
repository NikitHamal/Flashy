/**
 * Kartari Yogas Module
 * Implements hemming yogas for houses and planets
 */

import { YogaModuleBase, createYoga, sevenPlanets, allPlanets } from './base.js';

export class KartariYogas extends YogaModuleBase {
    check() {
        this._checkLagnaKartari();
        this._checkChandraKartari();
        this._checkSuryaKartari();
        this._checkPlanetaryKartari();
        this._checkHouseKartari();
    }

    /**
     * Lagna Shubha/Papa Kartari
     * Benefics/Malefics in 2nd and 12th from Lagna
     */
    _checkLagnaKartari() {
        const benefics = this.getNaturalBenefics();
        const malefics = this.getNaturalMalefics();

        const planetsIn2 = this.getPlanetsInHouse(2);
        const planetsIn12 = this.getPlanetsInHouse(12);

        const beneficsIn2 = planetsIn2.filter(p => benefics.includes(p));
        const beneficsIn12 = planetsIn12.filter(p => benefics.includes(p));
        const maleficsIn2 = planetsIn2.filter(p => malefics.includes(p));
        const maleficsIn12 = planetsIn12.filter(p => malefics.includes(p));

        // Shubha Kartari Lagna - benefics on both sides
        if (beneficsIn2.length > 0 && beneficsIn12.length > 0 &&
            maleficsIn2.length === 0 && maleficsIn12.length === 0) {
            this.addYoga(createYoga({
                name: 'Shubha Kartari Lagna',
                nameKey: 'Shubha_Kartari_Lagna',
                category: 'Kartari',
                description: 'Benefics in 2nd and 12th from Lagna. Protected self - good health, fortunate circumstances, protected personality.',
                descriptionKey: 'Shubha_Kartari_Lagna',
                planets: [...beneficsIn2, ...beneficsIn12],
                nature: 'Benefic',
                strength: 7
            }));
        }

        // Papa Kartari Lagna - malefics on both sides
        if (maleficsIn2.length > 0 && maleficsIn12.length > 0 &&
            beneficsIn2.length === 0 && beneficsIn12.length === 0) {
            this.addYoga(createYoga({
                name: 'Papa Kartari Lagna',
                nameKey: 'Papa_Kartari_Lagna',
                category: 'Kartari',
                description: 'Malefics in 2nd and 12th from Lagna. Squeezed self - health challenges, obstacles, constrained circumstances.',
                descriptionKey: 'Papa_Kartari_Lagna',
                planets: [...maleficsIn2, ...maleficsIn12],
                nature: 'Malefic',
                strength: 3
            }));
        }

        // Mixed Kartari
        if ((beneficsIn2.length > 0 || beneficsIn12.length > 0) &&
            (maleficsIn2.length > 0 || maleficsIn12.length > 0)) {
            const hasBothSides = (beneficsIn2.length > 0 || maleficsIn2.length > 0) &&
                (beneficsIn12.length > 0 || maleficsIn12.length > 0);
            if (hasBothSides) {
                this.addYoga(createYoga({
                    name: 'Mishra Kartari Lagna',
                    nameKey: 'Mishra_Kartari_Lagna',
                    category: 'Kartari',
                    description: 'Mixed planets in 2nd and 12th from Lagna. Fluctuating fortunes - mix of protection and challenges.',
                    descriptionKey: 'Mishra_Kartari_Lagna',
                    planets: [...planetsIn2, ...planetsIn12],
                    nature: 'Neutral',
                    strength: 5
                }));
            }
        }
    }

    /**
     * Chandra Kartari
     * Moon hemmed between planets
     */
    _checkChandraKartari() {
        const moonSign = this.ctx.moonRasi;
        const benefics = this.getNaturalBenefics();
        const malefics = this.getNaturalMalefics().filter(p => p !== 'Moon');

        const planetsIn2 = this.getPlanetsInHouse(2, moonSign).filter(p => p !== 'Moon');
        const planetsIn12 = this.getPlanetsInHouse(12, moonSign).filter(p => p !== 'Moon');

        const beneficsIn2 = planetsIn2.filter(p => benefics.includes(p));
        const beneficsIn12 = planetsIn12.filter(p => benefics.includes(p));
        const maleficsIn2 = planetsIn2.filter(p => malefics.includes(p));
        const maleficsIn12 = planetsIn12.filter(p => malefics.includes(p));

        // Shubha Kartari Moon
        if (beneficsIn2.length > 0 && beneficsIn12.length > 0 &&
            maleficsIn2.length === 0 && maleficsIn12.length === 0) {
            this.addYoga(createYoga({
                name: 'Shubha Kartari Chandra',
                nameKey: 'Shubha_Kartari_Chandra',
                category: 'Kartari',
                description: 'Moon hemmed by benefics. Protected mind - emotional stability, mental peace, supportive environment.',
                descriptionKey: 'Shubha_Kartari_Chandra',
                planets: ['Moon', ...beneficsIn2, ...beneficsIn12],
                nature: 'Benefic',
                strength: 7
            }));
        }

        // Papa Kartari Moon
        if (maleficsIn2.length > 0 && maleficsIn12.length > 0 &&
            beneficsIn2.length === 0 && beneficsIn12.length === 0) {
            this.addYoga(createYoga({
                name: 'Papa Kartari Chandra',
                nameKey: 'Papa_Kartari_Chandra',
                category: 'Kartari',
                description: 'Moon hemmed by malefics. Stressed mind - anxiety, mental challenges, difficult emotional environment.',
                descriptionKey: 'Papa_Kartari_Chandra',
                planets: ['Moon', ...maleficsIn2, ...maleficsIn12],
                nature: 'Malefic',
                strength: 3
            }));
        }
    }

    /**
     * Surya Kartari
     * Sun hemmed between planets
     */
    _checkSuryaKartari() {
        const sunSign = this.ctx.sunRasi;
        const benefics = this.getNaturalBenefics();
        const malefics = this.getNaturalMalefics().filter(p => p !== 'Sun');

        const planetsIn2 = this.getPlanetsInHouse(2, sunSign).filter(p => p !== 'Sun');
        const planetsIn12 = this.getPlanetsInHouse(12, sunSign).filter(p => p !== 'Sun');

        const beneficsIn2 = planetsIn2.filter(p => benefics.includes(p));
        const beneficsIn12 = planetsIn12.filter(p => benefics.includes(p));
        const maleficsIn2 = planetsIn2.filter(p => malefics.includes(p));
        const maleficsIn12 = planetsIn12.filter(p => malefics.includes(p));

        // Shubha Kartari Sun
        if (beneficsIn2.length > 0 && beneficsIn12.length > 0 &&
            maleficsIn2.length === 0 && maleficsIn12.length === 0) {
            this.addYoga(createYoga({
                name: 'Shubha Kartari Surya',
                nameKey: 'Shubha_Kartari_Surya',
                category: 'Kartari',
                description: 'Sun hemmed by benefics. Protected soul - strong vitality, supported authority, blessed father.',
                descriptionKey: 'Shubha_Kartari_Surya',
                planets: ['Sun', ...beneficsIn2, ...beneficsIn12],
                nature: 'Benefic',
                strength: 7
            }));
        }

        // Papa Kartari Sun
        if (maleficsIn2.length > 0 && maleficsIn12.length > 0 &&
            beneficsIn2.length === 0 && beneficsIn12.length === 0) {
            this.addYoga(createYoga({
                name: 'Papa Kartari Surya',
                nameKey: 'Papa_Kartari_Surya',
                category: 'Kartari',
                description: 'Sun hemmed by malefics. Challenged vitality - ego struggles, father issues, authority conflicts.',
                descriptionKey: 'Papa_Kartari_Surya',
                planets: ['Sun', ...maleficsIn2, ...maleficsIn12],
                nature: 'Malefic',
                strength: 3
            }));
        }
    }

    /**
     * Check Kartari for other planets
     */
    _checkPlanetaryKartari() {
        const planetsToCheck = ['Jupiter', 'Venus', 'Mercury', 'Mars', 'Saturn'];
        const benefics = this.getNaturalBenefics();
        const malefics = this.getNaturalMalefics();

        for (const planet of planetsToCheck) {
            const planetSign = this.getRasi(planet);
            if (planetSign === -1) continue;

            const planetsIn2 = this.getPlanetsInHouse(2, planetSign).filter(p => p !== planet);
            const planetsIn12 = this.getPlanetsInHouse(12, planetSign).filter(p => p !== planet);

            if (planetsIn2.length === 0 || planetsIn12.length === 0) continue;

            const beneficsIn2 = planetsIn2.filter(p => benefics.includes(p));
            const beneficsIn12 = planetsIn12.filter(p => benefics.includes(p));
            const maleficsIn2 = planetsIn2.filter(p => malefics.includes(p));
            const maleficsIn12 = planetsIn12.filter(p => malefics.includes(p));

            // Only report for significant planets with clear kartari
            if (beneficsIn2.length > 0 && beneficsIn12.length > 0 &&
                maleficsIn2.length === 0 && maleficsIn12.length === 0) {

                const significances = {
                    'Jupiter': 'wisdom, children, fortune',
                    'Venus': 'relationships, arts, luxury',
                    'Mercury': 'communication, intellect, business',
                    'Mars': 'courage, property, siblings',
                    'Saturn': 'discipline, longevity, service'
                };

                this.addYoga(createYoga({
                    name: `Shubha Kartari ${planet}`,
                    nameKey: 'Shubha_Kartari_Planet',
                    category: 'Kartari',
                    description: `${planet} protected by benefics. Enhanced ${significances[planet]}.`,
                    descriptionKey: 'Shubha_Kartari_Planet',
                    params: { planet },
                    planets: [planet, ...beneficsIn2, ...beneficsIn12],
                    nature: 'Benefic',
                    strength: 6
                }));
            }

            if (maleficsIn2.length > 0 && maleficsIn12.length > 0 &&
                beneficsIn2.length === 0 && beneficsIn12.length === 0) {

                const challenges = {
                    'Jupiter': 'wisdom blocked, children issues, fortune delayed',
                    'Venus': 'relationship troubles, artistic blocks, luxury denied',
                    'Mercury': 'communication issues, learning difficulties, business challenges',
                    'Mars': 'courage suppressed, property disputes, sibling issues',
                    'Saturn': 'excessive hardship, health issues, service exploitation'
                };

                this.addYoga(createYoga({
                    name: `Papa Kartari ${planet}`,
                    nameKey: 'Papa_Kartari_Planet',
                    category: 'Kartari',
                    description: `${planet} squeezed by malefics. ${challenges[planet]}.`,
                    descriptionKey: 'Papa_Kartari_Planet',
                    params: { planet },
                    planets: [planet, ...maleficsIn2, ...maleficsIn12],
                    nature: 'Malefic',
                    strength: 3
                }));
            }
        }
    }

    /**
     * Check Kartari for important houses
     */
    _checkHouseKartari() {
        const benefics = this.getNaturalBenefics();
        const malefics = this.getNaturalMalefics();
        const beneficHouses = new Set(benefics.map(p => this.getHouse(p)).filter(h => h !== -1));
        const maleficHouses = new Set(malefics.map(p => this.getHouse(p)).filter(h => h !== -1));

        const importantHouses = [
            { house: 4, name: 'Sukha Sthana (4th)', area: 'happiness, home, mother' },
            { house: 5, name: 'Putra Sthana (5th)', area: 'children, creativity, intelligence' },
            { house: 7, name: 'Kalatra Sthana (7th)', area: 'marriage, partnerships, public' },
            { house: 9, name: 'Bhagya Sthana (9th)', area: 'fortune, father, dharma' },
            { house: 10, name: 'Karma Sthana (10th)', area: 'career, status, authority' }
        ];

        for (const { house, name, area } of importantHouses) {
            const prev = house === 1 ? 12 : house - 1;
            const next = house === 12 ? 1 : house + 1;

            // Skip if already covered by Lagna Kartari (houses 2 and 12 around 1)
            if (house === 1) continue;

            const prevHasBenefic = beneficHouses.has(prev);
            const nextHasBenefic = beneficHouses.has(next);
            const prevHasMalefic = maleficHouses.has(prev);
            const nextHasMalefic = maleficHouses.has(next);

            // Shubha Kartari for house
            if (prevHasBenefic && nextHasBenefic && !prevHasMalefic && !nextHasMalefic) {
                this.addYoga(createYoga({
                    name: `Shubha Kartari ${name}`,
                    nameKey: 'Shubha_Kartari_House',
                    category: 'Kartari',
                    description: `${name} protected by benefics. Prosperity in ${area}.`,
                    descriptionKey: 'Shubha_Kartari_House',
                    params: { house },
                    planets: benefics.filter(p => [prev, next].includes(this.getHouse(p))),
                    nature: 'Benefic',
                    strength: 6
                }));
            }

            // Papa Kartari for house - already covered in doshas.js
            // Skip to avoid duplication
        }
    }
}

export default KartariYogas;
