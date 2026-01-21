/**
 * Sanyasa (Renunciation) Yogas Module
 * Implements ascetic and spiritual renunciation combinations
 */

import { YogaModuleBase, createYoga, sevenPlanets, kendras } from './base.js';

export class SanyasaYogas extends YogaModuleBase {
    check() {
        this._checkParirvrajaYoga();
        this._checkBhikshukYoga();
        this._checkSakyaYoga();
        this._checkJeevitmukYoga();
        this._checkTapasviYoga();
        this._checkNisswaYoga();
        this._checkVanprasthaYoga();
        this._checkMoonSaturnSanyasa();
        this._checkFourPlanetConjunction();
    }

    /**
     * Parivraja Yoga
     * Saturn as 10th lord aspects Lagna with Moon
     */
    _checkParirvrajaYoga() {
        const lord10 = this.getHouseLord(10);

        if (lord10 === 'Saturn') {
            // Check if Saturn aspects Lagna (1st house)
            const saturnHouse = this.getHouse('Saturn');
            const aspectsLagna = this._aspectsHouse('Saturn', saturnHouse, 1);

            // Check Moon's connection
            const moonHouse = this.getHouse('Moon');
            const moonInLagna = moonHouse === 1;
            const saturnAspectsMoon = this.aspects('Saturn', 'Moon');

            if (aspectsLagna && (moonInLagna || saturnAspectsMoon)) {
                this.addYoga(createYoga({
                    name: 'Parivraja Yoga',
                    nameKey: 'Parivraja',
                    category: 'Sanyasa',
                    description: 'Saturn as 10th lord aspects Lagna with Moon connection. Wandering monk - renounces worldly life for spiritual pursuit.',
                    descriptionKey: 'Parivraja',
                    planets: ['Saturn', 'Moon'],
                    nature: 'Neutral',
                    strength: 6
                }));
            }
        }
    }

    /**
     * Helper to check if planet aspects a specific house
     */
    _aspectsHouse(planet, planetHouse, targetHouse) {
        const aspects = {
            'Sun': [7], 'Moon': [7], 'Mercury': [7], 'Venus': [7],
            'Mars': [4, 7, 8], 'Jupiter': [5, 7, 9], 'Saturn': [3, 7, 10],
            'Rahu': [5, 7, 9], 'Ketu': [5, 7, 9]
        };

        const planetAspects = aspects[planet] || [7];
        for (const asp of planetAspects) {
            const aspectedHouse = ((planetHouse - 1 + asp) % 12) + 1;
            if (aspectedHouse === targetHouse) return true;
        }
        return false;
    }

    /**
     * Bhikshuk Yoga
     * Four or more planets conjoined aspecting Lagna
     */
    _checkBhikshukYoga() {
        // Find houses with 4+ planets
        const houseCounts = {};
        for (const p of sevenPlanets) {
            const h = this.getHouse(p);
            if (h !== -1) {
                houseCounts[h] = (houseCounts[h] || []);
                houseCounts[h].push(p);
            }
        }

        for (const [house, planets] of Object.entries(houseCounts)) {
            if (planets.length >= 4) {
                // Check if any planet aspects Lagna
                const aspectsLagna = planets.some(p => this._aspectsHouse(p, parseInt(house), 1));

                if (aspectsLagna) {
                    this.addYoga(createYoga({
                        name: 'Bhikshuk Yoga',
                        nameKey: 'Bhikshuk',
                        category: 'Sanyasa',
                        description: `Four planets conjunct in ${house}th house aspecting Lagna. Beggar yogi - may renounce wealth for spiritual begging.`,
                        descriptionKey: 'Bhikshuk',
                        planets,
                        nature: 'Neutral',
                        strength: 5
                    }));
                }
            }
        }
    }

    /**
     * Sakya Yoga (Buddhist monk)
     * Saturn alone strong, aspecting 4-planet conjunction
     */
    _checkSakyaYoga() {
        const saturnStrong = this.isStrong('Saturn') ||
            ['Exalted', 'Own', 'Moolatrikona'].includes(this.getDignity('Saturn'));

        if (!saturnStrong) return;

        // Find 4-planet conjunction
        const houseCounts = {};
        for (const p of sevenPlanets) {
            if (p === 'Saturn') continue;
            const h = this.getHouse(p);
            if (h !== -1) {
                houseCounts[h] = (houseCounts[h] || []);
                houseCounts[h].push(p);
            }
        }

        for (const [house, planets] of Object.entries(houseCounts)) {
            if (planets.length >= 4) {
                // Check if Saturn aspects this conjunction
                const saturnHouse = this.getHouse('Saturn');
                const aspectsConjunction = this._aspectsHouse('Saturn', saturnHouse, parseInt(house));

                if (aspectsConjunction) {
                    this.addYoga(createYoga({
                        name: 'Sakya Yoga',
                        nameKey: 'Sakya',
                        category: 'Sanyasa',
                        description: 'Strong Saturn aspects 4-planet conjunction. Buddhist path - disciplined renunciation, monastic life.',
                        descriptionKey: 'Sakya',
                        planets: ['Saturn', ...planets],
                        nature: 'Neutral',
                        strength: 6
                    }));
                }
            }
        }
    }

    /**
     * Jeevitmukt Yoga
     * All planets in 4th and 10th
     */
    _checkJeevitmukYoga() {
        const planetsIn4 = this.getPlanetsInHouse(4);
        const planetsIn10 = this.getPlanetsInHouse(10);

        const allPlanetsIn4_10 = sevenPlanets.every(p => {
            const h = this.getHouse(p);
            return h === 4 || h === 10;
        });

        if (allPlanetsIn4_10 && planetsIn4.length > 0 && planetsIn10.length > 0) {
            this.addYoga(createYoga({
                name: 'Jeevitmukt Yoga',
                nameKey: 'Jeevitmukt',
                category: 'Sanyasa',
                description: 'All planets in 4th and 10th houses. Liberated while living - extreme detachment, may live like a recluse.',
                descriptionKey: 'Jeevitmukt',
                planets: [...planetsIn4, ...planetsIn10],
                nature: 'Neutral',
                strength: 7
            }));
        }
    }

    /**
     * Tapasvi Yoga
     * Moon in Saturn's Navamsa, aspected by Saturn
     */
    _checkTapasviYoga() {
        // Simplified check: Moon in Capricorn/Aquarius aspected by Saturn
        const moonSign = this.getRasi('Moon');
        const saturnSigns = [9, 10]; // Capricorn, Aquarius

        const moonInSaturnSign = saturnSigns.includes(moonSign);
        const saturnAspectsMoon = this.aspects('Saturn', 'Moon');

        if (moonInSaturnSign && saturnAspectsMoon) {
            this.addYoga(createYoga({
                name: 'Tapasvi Yoga',
                nameKey: 'Tapasvi',
                category: 'Sanyasa',
                description: 'Moon in Saturn sign, aspected by Saturn. Ascetic yoga - severe penance, austere practices, spiritual discipline.',
                descriptionKey: 'Tapasvi',
                planets: ['Moon', 'Saturn'],
                nature: 'Neutral',
                strength: 5
            }));
        }
    }

    /**
     * Nisswa Yoga
     * Moon in Drekkana of Saturn, aspected by Saturn
     */
    _checkNisswaYoga() {
        // Drekkana (D3) - every sign has 3 drekkanas of 10 degrees each
        // Saturn rules Capricorn (9) and Aquarius (10)
        // Moon in Saturn's Drekkana = degrees 20-30 of Taurus/Virgo/Capricorn (for Cap drekkana)
        // or degrees 10-20 of Gemini/Libra/Aquarius (for Aqua drekkana)

        const moonDegree = this.getDegree('Moon');
        const moonSign = this.getRasi('Moon');

        // Simplified: Check if Moon is in last 10 degrees of earth signs
        // or middle 10 degrees of air signs (Saturn-ruled drekkanas)
        const saturnDrekkana = (
            ([1, 5, 9].includes(moonSign) && moonDegree >= 20 && moonDegree < 30) || // Capricorn drekkana
            ([2, 6, 10].includes(moonSign) && moonDegree >= 10 && moonDegree < 20)   // Aquarius drekkana
        );

        const saturnAspectsMoon = this.aspects('Saturn', 'Moon');

        if (saturnDrekkana && saturnAspectsMoon) {
            this.addYoga(createYoga({
                name: 'Nisswa Yoga',
                nameKey: 'Nisswa',
                category: 'Sanyasa',
                description: 'Moon in Saturn Drekkana, aspected by Saturn. Poverty yoga - may renounce possessions, live simply.',
                descriptionKey: 'Nisswa',
                planets: ['Moon', 'Saturn'],
                nature: 'Neutral',
                strength: 4
            }));
        }
    }

    /**
     * Vanprastha Yoga
     * Weak Moon in 9th or 10th, Saturn in Kendra
     */
    _checkVanprasthaYoga() {
        const moonHouse = this.getHouse('Moon');
        const moonWeak = !this.isWaxingMoon() || this.getDignity('Moon') === 'Debilitated';
        const moonIn9or10 = [9, 10].includes(moonHouse);

        const saturnHouse = this.getHouse('Saturn');
        const saturnInKendra = kendras.includes(saturnHouse);

        if (moonWeak && moonIn9or10 && saturnInKendra) {
            this.addYoga(createYoga({
                name: 'Vanprastha Yoga',
                nameKey: 'Vanprastha',
                category: 'Sanyasa',
                description: 'Weak Moon in 9th/10th, Saturn in Kendra. Forest dweller - retires from worldly life, especially in later years.',
                descriptionKey: 'Vanprastha',
                planets: ['Moon', 'Saturn'],
                nature: 'Neutral',
                strength: 5
            }));
        }
    }

    /**
     * Moon-Saturn Sanyasa patterns
     */
    _checkMoonSaturnSanyasa() {
        const moonConjunctSaturn = this.isConjunct('Moon', 'Saturn');
        const moonAspectedBySaturn = this.aspects('Saturn', 'Moon');
        const moonHouse = this.getHouse('Moon');
        const saturnHouse = this.getHouse('Saturn');

        // Moon in 12th from Saturn (spiritual imprisonment)
        const moonIn12FromSaturn = this.getHouse('Moon', this.getRasi('Saturn')) === 12;

        if (moonIn12FromSaturn && !this.isWaxingMoon()) {
            this.addYoga(createYoga({
                name: 'Sanyasa Yoga (Moon-Saturn)',
                nameKey: 'Sanyasa_Moon_Saturn',
                category: 'Sanyasa',
                description: 'Waning Moon in 12th from Saturn. Detachment tendency - mind inclined toward spiritual isolation.',
                descriptionKey: 'Sanyasa_Moon_Saturn',
                planets: ['Moon', 'Saturn'],
                nature: 'Neutral',
                strength: 5
            }));
        }

        // Ketu involvement with Moon-Saturn
        const ketuConjunctMoon = this.isConjunct('Ketu', 'Moon');
        if ((moonConjunctSaturn || moonAspectedBySaturn) && ketuConjunctMoon) {
            this.addYoga(createYoga({
                name: 'Vairagya Yoga',
                nameKey: 'Vairagya',
                category: 'Sanyasa',
                description: 'Moon connected to Saturn and Ketu. Dispassion yoga - deep detachment, past-life spiritual tendencies.',
                descriptionKey: 'Vairagya',
                planets: ['Moon', 'Saturn', 'Ketu'],
                nature: 'Neutral',
                strength: 6
            }));
        }
    }

    /**
     * Check four planet conjunctions for Sanyasa
     */
    _checkFourPlanetConjunction() {
        const houseCounts = {};
        for (const p of sevenPlanets) {
            const h = this.getHouse(p);
            if (h !== -1) {
                houseCounts[h] = (houseCounts[h] || []);
                houseCounts[h].push(p);
            }
        }

        for (const [house, planets] of Object.entries(houseCounts)) {
            if (planets.length >= 4) {
                // Check if this conjunction involves Saturn or Ketu
                const hasSaturn = planets.includes('Saturn');
                const hasKetu = this.getHouse('Ketu') === parseInt(house);

                // Check 10th lord involvement
                const lord10 = this.getHouseLord(10);
                const hasLord10 = planets.includes(lord10);

                if (hasSaturn || hasKetu || hasLord10) {
                    // Don't add if already added as Pravrajya in main yogas
                    // Check for specific spiritual houses
                    const spiritualHouses = [9, 12];
                    if (spiritualHouses.includes(parseInt(house))) {
                        this.addYoga(createYoga({
                            name: 'Pravrajya Yoga',
                            nameKey: 'Pravrajya',
                            category: 'Sanyasa',
                            description: `Multiple planets in ${house}th spiritual house. Strong renunciation potential - may take to religious/monastic life.`,
                            descriptionKey: 'Pravrajya',
                            planets,
                            nature: 'Neutral',
                            strength: 6
                        }));
                    }
                }
            }
        }
    }
}

export default SanyasaYogas;
