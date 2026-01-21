/**
 * Shadbala Engine - Six-Fold Planetary Strength Calculator
 * Based on Brihat Parashara Hora Shastra (BPHS) Chapter 27
 *
 * Components:
 * 1. Sthana Bala (Positional Strength)
 * 2. Dig Bala (Directional Strength)
 * 3. Kala Bala (Temporal Strength)
 * 4. Chesta Bala (Motional Strength)
 * 5. Naisargika Bala (Natural Strength)
 * 6. Drik Bala (Aspectual Strength)
 */

import {
    SAPTA_GRAHA,
    EXALTATION_POINTS,
    MOOLATRIKONA,
    OWN_SIGNS,
    SIGN_LORDS,
    NATURAL_FRIENDS,
    NATURAL_ENEMIES,
    NAISARGIKA_BALA,
    SHADBALA_REQUIREMENTS,
    SAPTAVARGA,
    NATURAL_BENEFICS,
    getDignity,
    getSignLord,
    getNaturalRelationship
} from './constants.js';
import Engine from './engine.js';

class ShadbalaEngine {
    constructor() {
        // Reference centralized constants
        this.planets = SAPTA_GRAHA;
        this.exaltationPoints = EXALTATION_POINTS;
        this.moolatrikona = MOOLATRIKONA;
        this.ownSigns = OWN_SIGNS;
        this.naisargikaBalaValues = NAISARGIKA_BALA;

        // Build natural relationships from constants
        this.naturalRel = {};
        for (const planet of this.planets) {
            this.naturalRel[planet] = {
                f: NATURAL_FRIENDS[planet] || [],
                n: [], // Will be computed
                e: NATURAL_ENEMIES[planet] || []
            };
            // Compute neutrals (planets not in friends or enemies)
            for (const other of this.planets) {
                if (other === planet) continue;
                if (!this.naturalRel[planet].f.includes(other) &&
                    !this.naturalRel[planet].e.includes(other)) {
                    this.naturalRel[planet].n.push(other);
                }
            }
        }
    }

    calculate(data) {
        if (!data || !data.planets) return null;

        const breakdown = {};
        const total = {};
        const componentBreakdown = {}; // Store individual components for Phala

        // Pre-calculate Relationships (Temporal & Compound)
        const relationships = this.calculateRelationships(data);

        this.planets.forEach(p => {
            // Calculate individual Sthana Bala components
            const uchchaBala = this.calculateUchchaBala(p, data.planets[p].lon);
            const saptavargaBala = this.calculateSaptavargaBala(p, data, relationships);
            const ojayugmaBala = this.calculateOjayugmaBala(p, data);
            const kendraBala = this.calculateKendraBala(p, data);
            const drekkanaBala = this.calculateDrekkanaBala(p, data);

            const sthanaBala = uchchaBala + saptavargaBala + ojayugmaBala + kendraBala + drekkanaBala;
            const chestaBala = this.calculateChestaBala(p, data);

            breakdown[p] = {
                sthana: sthanaBala,
                dig: this.calculateDigBala(p, data),
                kala: this.calculateKalaBala(p, data, relationships),
                chesta: chestaBala,
                naisargika: this.naisargikaBalaValues[p],
                drik: this.calculateDrikBala(p, data)
            };

            // Store individual components for Ishta/Kashta Phala calculation
            componentBreakdown[p] = {
                uchcha: uchchaBala,
                chesta: chestaBala
            };

            // Sum totals (Rupas = Virupas / 60)
            const sum = Object.values(breakdown[p]).reduce((a, b) => a + b, 0);
            total[p] = {
                virupas: sum,
                rupas: parseFloat((sum / 60).toFixed(2)),
                isStrong: this.checkStrengthRequirement(p, sum / 60)
            };
        });

        // Ishta/Kashta Phala (needs Uchcha and Chesta separately)
        const phala = this.calculatePhala(componentBreakdown);

        return { total, breakdown, phala, relationships };
    }

    // ========== 1. STHANA BALA ==========
    calculateSthanaBala(p, data, rels) {
        const uchcha = this.calculateUchchaBala(p, data.planets[p].lon);
        const saptavarga = this.calculateSaptavargaBala(p, data, rels);
        const ojayugma = this.calculateOjayugmaBala(p, data);
        const kendra = this.calculateKendraBala(p, data);
        const drekkana = this.calculateDrekkanaBala(p, data);

        return uchcha + saptavarga + ojayugma + kendra + drekkana;
    }

    calculateUchchaBala(planet, lon) {
        // Exaltation Point
        const exaltPoint = this.exaltationPoints[planet];
        // Dist from debilitation (Exalt + 180)
        let debilPoint = (exaltPoint + 180) % 360;

        // Diff = |lon - debilPoint|
        let diff = Math.abs(lon - debilPoint);
        if (diff > 180) diff = 360 - diff;

        // Max 60 Virupas at 180 deg (Exaltation)
        // 0 Virupas at 0 deg (Debilitation)
        return (diff / 3) * 1; // 180/3 = 60
    }

    calculateSaptavargaBala(p, data, rels) {
        // D1, D2, D3, D7, D9, D12, D30
        const vargas = [
            { id: 'D1', w: 45 }, { id: 'D2', w: 45 }, { id: 'D3', w: 45 }, { id: 'D7', w: 45 },
            { id: 'D9', w: 45 }, { id: 'D12', w: 45 }, { id: 'D30', w: 45 }
            // Wait, weight is not 45. Standard is:
            // Friend=15, Neutral=10, Enemy=5, Own=30, Moolatrikona=45.
            // Uchcha is handled separately or as part of this? 
            // In Saptavargaja, we typically don't count exaltation again if UchchaBala is separate?
            // Actually, BPHS says: Exalted=45? No.
            // Standard: Moolatrikona=45, Own=30, G.Friend=22.5, Friend=15, Neutral=10, Enemy=3.75, G.Enemy=1.875, Debil=0?
            // Let's use simplified standard:
            // Moolatrikona: 45
            // Own: 30
            // Great Friend: 22.5
            // Friend: 15
            // Neutral: 10
            // Enemy: 3.75
            // Great Enemy: 1.875
        ];

        let totalScore = 0;

        vargas.forEach(v => {
            const chartOne = data.divisionals?.[v.id]?.planets?.[p] || (v.id === 'D1' ? data.planets[p] : null);
            if (!chartOne) return;

            const signIdx = Math.floor(chartOne.lon / 30);
            const degInSign = chartOne.lon % 30;
            const signLord = this.getLord(signIdx);

            // Check Moolatrikona (Only effectively in D1, but rules applied generally if sign matches)
            let score = 0;

            // Is it Moolatrikona?
            const mt = this.moolatrikona[p];
            if (mt && mt.sign === signIdx && degInSign >= mt.start && degInSign < mt.end) {
                score = 45;
            } else if (signLord === p) {
                score = 30; // Own sign
            } else {
                // Relationship
                const relation = rels[p][signLord]; // 'Great Friend', 'Friend', etc.
                if (relation === 'Great Friend') score = 22.5;
                else if (relation === 'Friend') score = 15;
                else if (relation === 'Neutral') score = 10;
                else if (relation === 'Enemy') score = 3.75;
                else if (relation === 'Great Enemy') score = 1.875;
            }
            totalScore += score;
        });

        return totalScore;
    }

    calculateOjayugmaBala(p, data) {
        // D1 and D9. 
        // Venus/Moon in Even signs = 15. Sun/Mars/Merc/Jup/Sat in Odd signs = 15.
        // Else 0.
        let score = 0;
        const d1Lon = data.planets[p].lon;
        const d9Lon = data.divisionals.D9.planets[p].lon;

        [d1Lon, d9Lon].forEach(l => {
            const signIdx = Math.floor(l / 30);
            const isOdd = signIdx % 2 === 0; // Aries(0) is Odd
            const isFemale = (p === 'Venus' || p === 'Moon');

            if (isFemale && !isOdd) score += 15;
            if (!isFemale && isOdd) score += 15;
        });

        return score;
    }

    calculateKendraBala(p, data) {
        const lagnaLon = data.lagna.lon;
        const pLon = data.planets[p].lon;
        const house = Math.floor(((pLon - lagnaLon + 360) % 360) / 30) + 1;

        if ([1, 4, 7, 10].includes(house)) return 60;
        if ([2, 5, 8, 11].includes(house)) return 30; // Panapara
        if ([3, 6, 9, 12].includes(house)) return 15; // Apoklima
        return 15;
    }

    calculateDrekkanaBala(p, data) {
        // Male planets (Sun, Jup, Mars) strong in 1st decanate
        // Female (Moon, Ven) strong in 2nd
        // Neutral (Mer, Sat) strong in 3rd
        const signPos = data.planets[p].lon % 30;
        let decanate = 1;
        if (signPos >= 10) decanate = 2;
        if (signPos >= 20) decanate = 3;

        const type = {
            'Sun': 'M', 'Jupiter': 'M', 'Mars': 'M',
            'Moon': 'F', 'Venus': 'F',
            'Mercury': 'N', 'Saturn': 'N'
        }[p];

        if ((type === 'M' && decanate === 1) ||
            (type === 'F' && decanate === 2) ||
            (type === 'N' && decanate === 3)) {
            return 15;
        }
        return 0;
    }

    // ========== 2. DIG BALA ==========
    calculateDigBala(p, data) {
        const pLon = data.planets[p].lon;
        const lagna = data.lagna.lon;
        // Powerful Points:
        // Sun/Mars: 10th (Lagna + 270)
        // Moon/Venus: 4th (Lagna + 90)
        // Mercury/Jupiter: 1st (Lagna)
        // Saturn: 7th (Lagna + 180)

        let powerPoint = 0;
        if (['Sun', 'Mars'].includes(p)) powerPoint = (lagna + 270) % 360;
        else if (['Moon', 'Venus'].includes(p)) powerPoint = (lagna + 90) % 360;
        else if (['Mercury', 'Jupiter'].includes(p)) powerPoint = lagna;
        else if (['Saturn'].includes(p)) powerPoint = (lagna + 180) % 360;

        // Arc distance to powerless point (Power point + 180)
        let diff = Math.abs(pLon - powerPoint);
        if (diff > 180) diff = 360 - diff;

        // At power point (diff=0) -> 60. At opp (diff=180) -> 0.
        // Wait, standard is: Strength = (180 - DistFromPowerPoint) / 3
        return (180 - diff) / 3;
    }

    // ========== 3. KALA BALA ==========
    calculateKalaBala(p, data, rels) {
        const natonnata = this.calculateNatonnataBala(p, data);
        const paksha = this.calculatePakshaBala(p, data);
        const tribhaga = this.calculateTribhagaBala(p, data);
        
        // Varsha and Maasa Bala based on Ahargana
        const ahargana = Engine.getAhargana(data.date);
        const varshaMasa = this.calculateVarshaMaasaBala(p, ahargana);
        
        const vara = this.calculateVaraBala(p, data);
        const hora = this.calculateHoraBala(p, data);
        const ayana = this.calculateAyanaBala(p, data);
        
        // Planetary War (Yuddha)
        const yuddha = this.calculateYuddhaBala(p, data, rels);

        return natonnata + paksha + tribhaga + varshaMasa.varsha + varshaMasa.masa + vara + hora + ayana + yuddha;
    }

    /**
     * Calculate Varsha and Maasa lords and their strengths
     * @param {string} p - Planet
     * @param {number} ahargana - Days since Kali Yuga
     */
    calculateVarshaMaasaBala(p, ahargana) {
        const lords = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
        
        // Varsha Lord: Lord of the first day of the year
        const varshaIdx = Math.floor((Math.floor(ahargana / 360) * 3 + 1) % 7);
        const varshaLord = lords[varshaIdx];
        
        // Maasa Lord: Lord of the first day of the month
        const masaIdx = Math.floor((Math.floor(ahargana / 30) * 2 + 1) % 7);
        const masaLord = lords[masaIdx];
        
        return {
            varsha: p === varshaLord ? 15 : 0,
            masa: p === masaLord ? 30 : 0
        };
    }

    /**
     * Calculate Planetary War (Yuddha)
     * Occurs between non-luminary planets within 1 degree
     * Per BPHS: The one in the North (higher latitude) is the winner.
     * Exception: Venus is usually the winner regardless.
     * Modern Refinement: Brightness comparison (magnitude/distance).
     */
    calculateYuddhaBala(p, data, rels) {
        if (['Sun', 'Moon'].includes(p)) return 0;

        const taraGrahas = ['Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
        let yuddhaBala = 0;

        taraGrahas.forEach(other => {
            if (p === other) return;

            const p1 = data.planets[p];
            const p2 = data.planets[other];

            const diff = Math.abs(p1.lon - p2.lon);
            const dist = Math.min(diff, 360 - diff);

            if (dist < 1.0) {
                // Planetary War!
                
                // 1. Venus Rule: Venus always wins unless specifically contested otherwise
                let isWinner = false;
                if (p === 'Venus') isWinner = true;
                else if (other === 'Venus') isWinner = false;
                else {
                    // 2. Latitude Rule (BPHS): The one in the North wins
                    // Higher latitude (elat) means further North
                    if (p1.lat !== p2.lat) {
                        isWinner = p1.lat > p2.lat;
                    } else {
                        // 3. Brightness/Distance Rule: Closer to Earth/Larger diameter
                        // dist is distance from Earth. Smaller dist = Brighter.
                        isWinner = p1.dist < p2.dist;
                    }
                }

                // Difference in Shadbala (Sthana + Dig + Kala - current Yuddha)
                // We use basic strengths to determine the magnitude of gain/loss
                const s1 = this.calculateSthanaBala(p, data, rels) + this.calculateDigBala(p, data);
                const s2 = this.calculateSthanaBala(other, data, rels) + this.calculateDigBala(other, data);
                const shadbalaDiff = Math.abs(s1 - s2);

                if (isWinner) {
                    yuddhaBala += shadbalaDiff; // Gains difference
                } else {
                    yuddhaBala -= shadbalaDiff; // Loses difference
                }
            }
        });

        return yuddhaBala;
    }

    calculateNatonnataBala(p, data) {
        // Diurnal/Nocturnal
        // Day Birth?
        // Approx: Sun in 7-12 houses? Or simple 6am-6pm logic?
        // Let's use Ascendant-Sun angle.
        const sunH = this.getHouseIndex(data.planets.Sun.lon, data.lagna.lon);
        // Houses 7,8,9,10,11,12 are Day (Visible half) usually?
        // Better: Check if Sun is above horizon using Astronomy engine altitude?
        // Or assume 6am-6pm local time.
        // Let's use isDaytime from Sun-Asc relation.
        // If Sun is in house 12, 11, 10, 9, 8, 7 -> Day.
        // Houses 1, 2, 3, 4, 5, 6 -> Night.
        const dayHouses = [7, 8, 9, 10, 11, 12];
        const isDay = dayHouses.includes(sunH);

        // Day: Sun, Jup, Ven get 60.
        // Night: Moon, Mars, Sat get 60.
        // Merc: Always 60.

        if (p === 'Mercury') return 60;
        if (['Sun', 'Jupiter', 'Venus'].includes(p)) return isDay ? 60 : 0;
        if (['Moon', 'Mars', 'Saturn'].includes(p)) return !isDay ? 60 : 0;
        return 0;
    }

    calculatePakshaBala(p, data) {
        // Moon - Sun angle
        let diff = data.planets.Moon.lon - data.planets.Sun.lon;
        if (diff < 0) diff += 360;

        // Max (180 deg) = 60 for Benefics.
        // Benefics: Jup, Ven, Moon (Standard). Merc? Usually.
        // Malefics: Sun, Mars, Sat. (Get 60 - Paksha)

        const pakshaScore = (diff / 180) * 60;
        const validPaksha = diff > 180 ? 120 - pakshaScore : pakshaScore; // 0 at 0, 60 at 180, 0 at 360.

        const benefics = ['Jupiter', 'Venus', 'Moon', 'Mercury'];
        // Moon is benefic if strong paksha, but here we just give it the score.
        // BPHS: Benefics get Paksha. Malefics get (60 - Paksha).
        if (benefics.includes(p)) return validPaksha;
        return 60 - validPaksha;
    }

    calculateTribhagaBala(p, data) {
        /**
         * Tribhaga Bala - Strength based on the three parts of day/night
         * Per BPHS Chapter 27:
         *
         * Day is divided into 3 parts (Tribhagas):
         *   Part 1 (Sunrise to ~4 hrs): Mercury gets 60 Virupas
         *   Part 2 (Mid-day ~4-8 hrs): Sun gets 60 Virupas
         *   Part 3 (Afternoon ~8-12 hrs): Saturn gets 60 Virupas
         *
         * Night is divided into 3 parts:
         *   Part 1 (Sunset to ~4 hrs): Moon gets 60 Virupas
         *   Part 2 (Midnight ~4-8 hrs): Venus gets 60 Virupas
         *   Part 3 (Pre-dawn ~8-12 hrs): Mars gets 60 Virupas
         *
         * Jupiter ALWAYS gets 60 Virupas (rules all times)
         */

        // Jupiter always strong in all Tribhagas
        if (p === 'Jupiter') return 60;

        // Need location data for proper sunrise/sunset calculation
        if (!data.location || !data.date) {
            // Fallback to house-based approximation
            return this._tribhagaFallback(p, data);
        }

        const { lat, lng } = data.location;
        const birthDate = new Date(data.date);

        // Get sunrise/sunset for this date and location
        const sunTimes = Engine.getSunriseSunset(birthDate, lat, lng);

        if (!sunTimes.sunrise || !sunTimes.sunset) {
            return this._tribhagaFallback(p, data);
        }

        const birthMs = birthDate.getTime();
        const sunriseMs = sunTimes.sunrise.getTime();
        const sunsetMs = sunTimes.sunset.getTime();

        // Calculate day and night duration
        const dayDuration = sunsetMs - sunriseMs;
        const tribhagaDayDuration = dayDuration / 3;

        // Determine if birth is during day or night, and which Tribhaga
        let tribhagaPart = 0;
        let isDaytime = false;

        if (birthMs >= sunriseMs && birthMs < sunsetMs) {
            // Daytime
            isDaytime = true;
            const elapsed = birthMs - sunriseMs;
            tribhagaPart = Math.floor(elapsed / tribhagaDayDuration) + 1;
            if (tribhagaPart > 3) tribhagaPart = 3;
        } else {
            // Nighttime
            isDaytime = false;
            // Get next sunrise for night duration
            const nextSunriseMs = sunriseMs + 24 * 60 * 60 * 1000;
            const nightDuration = nextSunriseMs - sunsetMs;
            const tribhagaNightDuration = nightDuration / 3;

            let elapsed;
            if (birthMs >= sunsetMs) {
                elapsed = birthMs - sunsetMs;
            } else {
                // Before sunrise (early morning)
                const prevSunsetMs = sunsetMs - 24 * 60 * 60 * 1000;
                elapsed = birthMs - prevSunsetMs;
            }

            tribhagaPart = Math.floor(elapsed / tribhagaNightDuration) + 1;
            if (tribhagaPart > 3) tribhagaPart = 3;
        }

        // Assign Tribhaga lords based on day/night and part
        // Day: Mercury (1), Sun (2), Saturn (3)
        // Night: Moon (1), Venus (2), Mars (3)
        const dayLords = { 1: 'Mercury', 2: 'Sun', 3: 'Saturn' };
        const nightLords = { 1: 'Moon', 2: 'Venus', 3: 'Mars' };

        const currentLord = isDaytime ? dayLords[tribhagaPart] : nightLords[tribhagaPart];

        return p === currentLord ? 60 : 0;
    }

    /**
     * Fallback Tribhaga calculation when location data unavailable
     * Uses Sun's house position as approximation
     */
    _tribhagaFallback(p, data) {
        if (p === 'Jupiter') return 60;

        const sunH = this.getHouseIndex(data.planets.Sun.lon, data.lagna.lon);
        const isDay = [7, 8, 9, 10, 11, 12].includes(sunH);

        // Rough approximation based on Sun's house
        // Day: Houses 12-11 (Part 1), 10-9 (Part 2), 8-7 (Part 3)
        // Night: Houses 6-5 (Part 1), 4-3 (Part 2), 2-1 (Part 3)
        let part = 1;
        if (isDay) {
            if ([12, 11].includes(sunH)) part = 1;
            else if ([10, 9].includes(sunH)) part = 2;
            else part = 3;
        } else {
            if ([6, 5].includes(sunH)) part = 1;
            else if ([4, 3].includes(sunH)) part = 2;
            else part = 3;
        }

        const dayLords = { 1: 'Mercury', 2: 'Sun', 3: 'Saturn' };
        const nightLords = { 1: 'Moon', 2: 'Venus', 3: 'Mars' };

        const currentLord = isDay ? dayLords[part] : nightLords[part];
        return p === currentLord ? 60 : 0;
    }

    calculateVaraBala(p, data) {
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const date = new Date(data.date);
        const dayIdx = date.getDay();
        const lord = { 0: 'Sun', 1: 'Moon', 2: 'Mars', 3: 'Mercury', 4: 'Jupiter', 5: 'Venus', 6: 'Saturn' }[dayIdx];

        return p === lord ? 45 : 0;
    }

    calculateHoraBala(p, data) {
        /**
         * Hora Bala - Strength based on planetary hour lord
         * Per BPHS Chapter 27:
         *
         * The lord of the current Hora (planetary hour) gets 60 Virupas.
         * Hora sequence follows Chaldean order starting from day lord.
         *
         * Day/Night are each divided into 12 Horas (unequal hours).
         * Sequence: Saturn -> Jupiter -> Mars -> Sun -> Venus -> Mercury -> Moon
         */

        // Need location data for proper Hora calculation
        if (!data.location || !data.date) {
            return 0; // Cannot calculate without location
        }

        const { lat, lng } = data.location;
        const birthDate = new Date(data.date);

        // Use Engine's calculateHora for accurate Hora lord
        const hora = Engine.calculateHora(birthDate, lat, lng);

        if (!hora || !hora.lord) {
            return 0;
        }

        // Planet ruling the current Hora gets full strength
        return p === hora.lord ? 60 : 0;
    }

    calculateAyanaBala(p, data) {
        // Based on Declination + 24.
        // Formula: (24 +/- Dec) * Coeff?
        // Standard: 
        // Sun, Mars, Jup, Ven (North): Strong.
        // Sat, Moon (South): Strong.
        // Merc: Always strong?
        // Value = (23.44 + Declination) * ValueFactor.
        // Range 0 to 60.
        // Max Dec = +24. Min = -24.

        const dec = data.planets[p].dec || 0;
        // Direction:
        // Sun/Mars/Jup/Ven: South declination is bad? No.
        // Sun, Mars, Jupiter, Venus: North is best. (+Dec)
        // Moon, Saturn: South is best. (-Dec)
        // Mercury: Always 30.

        if (p === 'Mercury') return 30;

        let val;
        let maxDec = 24;

        const northLovers = ['Sun', 'Mars', 'Jupiter', 'Venus'];

        if (northLovers.includes(p)) {
            // +24 = 60 strength. -24 = 0 strength.
            val = ((dec + maxDec) / (2 * maxDec)) * 60;
        } else {
            // -24 = 60 strength. +24 = 0 strength.
            val = ((maxDec - dec) / (2 * maxDec)) * 60;
        }

        // Sun gets 2x AyanaBala
        if (p === 'Sun') val *= 2;

        return Math.max(0, Math.min(60, val));
    }

    // ========== 4. CHESTA BALA ==========
    calculateChestaBala(p, data) {
        // Speed based logic is standard when mean lon is unknown.
        // Vakra (Retrograde): 60
        // Anuvakra (Retro entering previous sign): 30
        // Vikala (Stationary): 15
        // Mandatara (Slow): 30
        // Manda (Avg): 15

        if (['Sun', 'Moon'].includes(p)) return this.calculatePakshaBala(p, data); // Sun/Moon have no Chesta? Usually calculate differently or 0.

        const speed = data.planets[p].speed || 0;
        const avgSpeed = { 'Mercury': 1.4, 'Venus': 1.2, 'Mars': 0.52, 'Jupiter': 0.08, 'Saturn': 0.033 }[p] || 1;

        if (speed < 0) return 60; // Retrograde (Vakra)
        if (Math.abs(speed) < 0.1 * avgSpeed) return 15; // Stationary (Vikala)
        if (speed > avgSpeed * 1.5) return 45; // Fast
        if (speed < avgSpeed * 0.5) return 30; // Slow
        return 15; // Normal
    }

    // ========== 6. DRIK BALA ==========
    calculateDrikBala(p, data) {
        // Aspect strength from others
        let aspectScore = 0;
        const pLon = data.planets[p].lon;

        this.planets.forEach(other => {
            if (p === other) return;

            const oLon = data.planets[other].lon;
            let dist = (pLon - oLon); // Angle from Other TO Planet
            if (dist < 0) dist += 360;

            // Standard Drishthi points:
            // 30-60: Virupa = (Dist-30)/2
            // 60-90: Virupa = (Dist-60) + 15
            // 90-120: Virupa = (120-Dist)/2 + 30
            // 120-150: Virupa = (150-Dist)
            // 150-180: Virupa = (Dist-150)*2
            // 180-300: 0

            let val = 0;
            if (dist >= 30 && dist < 60) val = (dist - 30) / 2;
            else if (dist >= 60 && dist < 90) val = (dist - 60) + 15;
            else if (dist >= 90 && dist < 120) val = (120 - dist) / 2 + 30;
            else if (dist >= 120 && dist < 150) val = 150 - dist;
            else if (dist >= 150 && dist < 180) val = (dist - 150) * 2;
            else if (dist >= 180 && dist < 300) val = 0;
            // Special Aspects
            // Mars: 4th (90 deg), 8th (210) -> Full
            // Jup: 5th (120), 9th (240) -> Full
            // Sat: 3rd (60), 10th (270) -> Full

            // Override standard curve for special aspects
            if (other === 'Mars') {
                if (Math.abs(dist - 90) < 10) val = 60; // 4th
                if (Math.abs(dist - 210) < 10) val = 60; // 8th
            }
            if (other === 'Jupiter') {
                if (Math.abs(dist - 120) < 10) val = 60;
                if (Math.abs(dist - 240) < 10) val = 60;
            }
            if (other === 'Saturn') {
                if (Math.abs(dist - 60) < 10) val = 60;
                if (Math.abs(dist - 270) < 10) val = 60;
            }

            // Apply Benefic/Malefic sign
            // Benefics (Jup, Ven, Mer*, Moon*) give +Strength
            // Malefics (Sun, Mars, Sat) give -Strength
            // Simple Natural benefic list:
            const isBenefic = ['Jupiter', 'Venus', 'Mercury', 'Moon'].includes(other);
            if (isBenefic) aspectScore += val / 4; // 1/4th of drishti value added
            else aspectScore -= val / 4; // Subtracted
        });

        return aspectScore; // Can be negative
    }

    // ========== UTILS ==========
    calculateRelationships(data) {
        // Temporal Friends: 2, 3, 4, 10, 11, 12 positions
        const rels = {};
        const getH = (p1, p2) => Math.floor(((data.planets[p2].lon - data.planets[p1].lon + 360) % 360) / 30) + 1;

        this.planets.forEach(p1 => {
            rels[p1] = {};
            this.planets.forEach(p2 => {
                if (p1 === p2) return;

                // 1. Natural
                const nat = this.naturalRel[p1];
                let score = 0; // 1 = Friend, 0 = Neutral, -1 = Enemy
                if (nat.f.includes(p2)) score = 1;
                else if (nat.e.includes(p2)) score = -1;

                // 2. Temporal
                const h = getH(p1, p2);
                const isTempFriend = [2, 3, 4, 10, 11, 12].includes(h);
                const tempScore = isTempFriend ? 1 : -1;

                // 3. Compund
                const total = score + tempScore;
                // 2 = G.Friend, 1 = Friend, 0 = Neutral, -1 = Enemy, -2 = G.Enemy
                let status = 'Neutral';
                if (total === 2) status = 'Great Friend';
                if (total === 1) status = 'Friend';
                if (total === 0) status = 'Neutral';
                if (total === -1) status = 'Enemy';
                if (total === -2) status = 'Great Enemy';

                rels[p1][p2] = status;
            });
        });
        return rels;
    }

    getHouseIndex(pLon, ascLon) {
        return Math.floor(((pLon - ascLon + 360) % 360) / 30) + 1;
    }

    getLord(signIdx) {
        return getSignLord(signIdx);
    }

    checkStrengthRequirement(p, rupas) {
        // Min requirements per BPHS Chapter 27
        return rupas >= (SHADBALA_REQUIREMENTS[p] || 5.0);
    }

    calculatePhala(componentBreakdown) {
        /**
         * Ishta Phala (Benefic Results) & Kashta Phala (Malefic Results)
         * Per BPHS Chapter 27:
         *
         * These are derived from Uchcha Bala (Exaltation Strength) and
         * Chesta Bala (Motional Strength).
         *
         * Standard Formulas (per B.V. Raman's interpretation):
         *
         * Shubha Pinda (Benefic Point) = (Uchcha Bala + Chesta Bala) / 2
         * Ashubha Pinda (Malefic Point) = (60 - Uchcha Bala + 60 - Chesta Bala) / 2
         *                                = 60 - Shubha Pinda
         *
         * Ishta Phala = √(Shubha Pinda × Chesta Bala)
         * Kashta Phala = √(Ashubha Pinda × (60 - Chesta Bala))
         *
         * Alternative BPHS Formula:
         * Ishta = √(Uchcha × Chesta)
         * Kashta = √((60 - Uchcha) × (60 - Chesta))
         *
         * We implement the BPHS formula for accuracy.
         */
        const phala = {};

        this.planets.forEach(p => {
            const uchcha = componentBreakdown[p].uchcha;
            const chesta = componentBreakdown[p].chesta;

            // Ensure values are within valid range (0-60 Virupas)
            const uchchaClamped = Math.max(0, Math.min(60, uchcha));
            const chestaClamped = Math.max(0, Math.min(60, chesta));

            // BPHS Formula for Ishta Phala
            // Ishta = √(Uchcha Bala × Chesta Bala)
            const ishta = Math.sqrt(uchchaClamped * chestaClamped);

            // BPHS Formula for Kashta Phala
            // Kashta = √((60 - Uchcha) × (60 - Chesta))
            const uchchaDeficit = 60 - uchchaClamped;
            const chestaDeficit = 60 - chestaClamped;
            const kashta = Math.sqrt(uchchaDeficit * chestaDeficit);

            // Subha Pinda (Benefic Point) - for reference
            const subhaPinda = (uchchaClamped + chestaClamped) / 2;

            // Ashubha Pinda (Malefic Point) - for reference
            const ashubhaPinda = (uchchaDeficit + chestaDeficit) / 2;

            phala[p] = {
                ishta: parseFloat(ishta.toFixed(2)),
                kashta: parseFloat(kashta.toFixed(2)),
                subhaPinda: parseFloat(subhaPinda.toFixed(2)),
                ashubhaPinda: parseFloat(ashubhaPinda.toFixed(2)),
                // Net effect: positive = more benefic results
                net: parseFloat((ishta - kashta).toFixed(2))
            };
        });

        return phala;
    }
}

export default new ShadbalaEngine();
