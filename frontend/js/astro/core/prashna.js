/**
 * ============================================================================
 * Horary (Prashna) Astrology Engine
 * ============================================================================
 * 
 * Implements Prashna techniques:
 * 1. Prashna Chart Casting (Moment of Query)
 * 2. Tajika Analysis (Ithasala, Easarpha, etc.)
 * 3. Karyesha (Significator) Determination
 * 4. Shatpanchasika & Mook Prashna analysis
 * 
 * References:
 * - Shatpanchasika (Prithuyashas)
 * - Prashna Marga
 * - Tajika Neelakanthi
 * 
 * @module astro/prashna
 * @version 2.0.0
 */

import Vedic from './vedic.js';
import { SAPTA_GRAHA, SIGN_LORDS, RASI_NAMES, NAKSHATRA_NAMES } from './constants.js';

// Tajika Aspects
const TAJIKA_ASPECTS = {
    conjunction: { min: 0, max: 12, name: 'Yuti', strength: 1 },
    sextile: { min: 48, max: 72, name: 'Shashtashtaka', strength: 0.5 }, // Friendly
    square: { min: 78, max: 102, name: 'Chaturasra', strength: 0.25 }, // Unfriendly
    trine: { min: 108, max: 132, name: 'Trikona', strength: 0.75 }, // Friendly
    opposition: { min: 168, max: 192, name: 'Pratiyuti', strength: 0.1 } // Unfriendly
};

// House Significators for Topics
const QUESTION_TOPICS = {
    'general': { house: 11, name: 'Fulfillment of Desire' },
    'health': { house: 6, name: 'Disease/Recovery' }, // Also 1st for patient
    'wealth': { house: 2, name: 'Financial Gain' },
    'marriage': { house: 7, name: 'Spouse/Partner' },
    'children': { house: 5, name: 'Progeny' },
    'job': { house: 10, name: 'Career/Status' },
    'travel': { house: 9, name: 'Journey' }, // Also 3rd for short, 7th for return
    'property': { house: 4, name: 'Land/Vehicle' },
    'litigation': { house: 6, name: 'Court Case' }, // Also 7th for opponent
    'missing': { house: 4, name: 'Missing Person/Item' }
};

class PrashnaEngine {
    constructor() {}

    /**
     * Cast a Prashna Chart for the current moment or query time
     * @param {Date} queryTime 
     * @param {Object} location 
     * @param {string} topic - Key from QUESTION_TOPICS
     * @param {number} userArudha - Optional user-defined Arudha
     */
    calculatePrashna(queryTime, location, topic = 'general', userArudha = null) {
        const data = Vedic.calculate(queryTime, location);
        
        const analysis = this.analyzePrashna(data, topic, userArudha);

        return {
            ...data,
            queryTopic: topic,
            analysis
        };
    }

    /**
     * Analyze Prashna Chart
     */
    analyzePrashna(data, topic, userArudha) {
        const lagnaIdx = data.lagna.rasi.index;
        const lagnaLord = SIGN_LORDS[lagnaIdx];
        
        // 1. Identify Karyesha (Significator)
        const topicInfo = QUESTION_TOPICS[topic] || QUESTION_TOPICS['general'];
        const houseQuery = topicInfo.house; // 1-based house number
        const karyeshaHouseIdx = (lagnaIdx + houseQuery - 1) % 12;
        const karyesha = SIGN_LORDS[karyeshaHouseIdx];

        // 2. Identify Moon (Chandra) - The Co-Significator
        const moon = data.planets.Moon;
        
        // 3. Analyze Tajika Yogas (Lagna Lord vs Karyesha)
        const llData = data.planets[lagnaLord];
        const klData = data.planets[karyesha];
        
        const yoga = this.checkTajikaYoga(llData, klData);
        
        // 4. Moon Analysis (Moon vs Karyesha)
        const moonYoga = this.checkTajikaYoga(moon, klData);

        // 5. Shatpanchasika / Classical Indicators
        const indicators = this.getClassicalIndicators(data, lagnaLord, karyesha, houseQuery);

        // 6. Final Verdict
        const score = this.calculateSuccessScore(yoga, moonYoga, indicators, llData, klData, moon);

        return {
            topic: topicInfo.name,
            lagnaLord,
            karyesha,
            karyeshaHouse: houseQuery,
            tajikaYoga: yoga,
            moonYoga: moonYoga,
            indicators,
            score,
            verdict: this.getVerdict(score),
            mookTopic: this.identifyQuestionTopic(data) // Keep Mook Prashna as secondary insight
        };
    }

    /**
     * Check Tajika Yoga between two planets
     */
    checkTajikaYoga(p1Data, p2Data) {
        if (!p1Data || !p2Data) return null;

        const diff = Math.abs(p1Data.lon - p2Data.lon);
        const dist = diff > 180 ? 360 - diff : diff;

        let aspect = null;
        for (const [key, val] of Object.entries(TAJIKA_ASPECTS)) {
            if (dist >= val.min && dist <= val.max) {
                aspect = val;
                break;
            }
        }

        if (!aspect) return { type: 'None', applying: false };

        // Determine Applying (Ithasala) or Separating (Easarpha)
        // Faster planet must be behind slower planet to apply
        const speed1 = Math.abs(p1Data.speed); // Use magnitude for speed comparison
        const speed2 = Math.abs(p2Data.speed);
        
        // Identify faster planet
        const faster = speed1 > speed2 ? p1Data : p2Data;
        const slower = speed1 > speed2 ? p2Data : p1Data;

        // Check relative position
        // If Faster is at 10 deg and Slower at 20 deg, Diff = 10.
        // If Faster is at 350 and Slower at 10, Diff (forward) = 20.
        
        let forwardDist = (slower.lon - faster.lon + 360) % 360;
        
        // Applying if forward distance matches the aspect target
        // Conjunction (0): Forward dist close to 0 or 360
        // Sextile (60): Forward dist close to 60 or 300? 
        // Tajika aspects work both ways, but Ithasala requires closing the gap.
        
        // Simplified: Applying if the orb is decreasing.
        // We know the aspect type. Is the faster planet moving TOWARDS exact aspect?
        
        // Let's use the standard "Faster planet is less advanced in longitude" rule for Conjunction
        // For aspects, it's complex. Let's use a simpler "Applying" check:
        // Applying if dist < exact_aspect_angle AND faster is "behind"
        // OR dist > exact_aspect_angle AND faster is "ahead" (retrograde logic makes this messy)
        
        // Robust way: Project positions forward in time.
        // If distance |p1 - p2 - aspect| decreases, it's applying.
        const t1 = p1Data.lon + (p1Data.speed);
        const t2 = p2Data.lon + (p2Data.speed);
        const nextDist = Math.abs(t1 - t2); // Rough check
        const nextDistNorm = nextDist > 180 ? 360 - nextDist : nextDist;
        
        // Compare deviation from ideal center of aspect
        const ideal = (aspect.min + aspect.max) / 2;
        const currentOrb = Math.abs(dist - ideal);
        const nextOrb = Math.abs(nextDistNorm - ideal);
        
        const applying = nextOrb < currentOrb;

        return {
            type: aspect.name, // Yuti, Trikona, etc.
            aspectKey: aspect,
            applying: applying,
            orb: currentOrb.toFixed(2),
            isIthasala: applying, // Applying Aspect
            isEasarpha: !applying // Separating Aspect
        };
    }

    /**
     * Get Classical Indicators (Shatpanchasika, etc.)
     */
    getClassicalIndicators(data, lagnaLord, karyesha, queryHouse) {
        const indicators = [];
        const lagnaIdx = data.lagna.rasi.index;
        const moon = data.planets.Moon;

        // 1. Lagna Lord in Query House?
        const llIdx = data.planets[lagnaLord].rasi.index;
        const qhIdx = (lagnaIdx + queryHouse - 1) % 12;
        if (llIdx === qhIdx) {
            indicators.push({ name: 'Lagna Lord in Query House', value: 1, desc: 'Strong success indicator' });
        }

        // 2. Moon in Lagna or Query House?
        const moonIdx = moon.rasi.index;
        if (moonIdx === lagnaIdx) indicators.push({ name: 'Moon in Lagna', value: 0.5, desc: 'Moon drives the query' });
        if (moonIdx === qhIdx) indicators.push({ name: 'Moon in Query House', value: 0.8, desc: 'Mind focused on result' });

        // 3. Shirshodaya Signs in Lagna (Head rising - Good for success)
        const shirshodaya = [2, 4, 5, 6, 7, 10]; // Gem, Leo, Vir, Lib, Sco, Aqu
        if (shirshodaya.includes(lagnaIdx)) {
            indicators.push({ name: 'Shirshodaya Lagna', value: 0.3, desc: 'Good for quick results' });
        }

        // 4. Benefics in Kendras/Trikonas
        const benefics = ['Jupiter', 'Venus', 'Mercury'];
        let beneficScore = 0;
        benefics.forEach(b => {
            const h = ((data.planets[b].rasi.index - lagnaIdx + 12) % 12) + 1;
            if ([1, 4, 7, 10, 5, 9].includes(h)) beneficScore++;
        });
        if (beneficScore >= 2) indicators.push({ name: 'Benefics in Kendra/Trikona', value: 0.5, desc: 'General auspiciousness' });

        return indicators;
    }

    calculateSuccessScore(yoga, moonYoga, indicators, llData, klData, moonData) {
        let score = 50; // Base score

        // 1. Tajika Yoga (Primary)
        if (yoga.type !== 'None') {
            let yogaScore = 0;
            // Aspect nature
            if (['Yuti', 'Trikona', 'Shashtashtaka'].includes(yoga.type)) yogaScore += 20; // Sextile is usually good in Tajika if friendly signs
            if (['Chaturasra', 'Pratiyuti'].includes(yoga.type)) yogaScore -= 10; // Square/Opposite usually bad

            // Application
            if (yoga.applying) yogaScore += 10; // Ithasala
            else yogaScore -= 5; // Easarpha (opportunity passed)

            score += yogaScore;
        }

        // 2. Moon Yoga (Secondary)
        if (moonYoga.type !== 'None' && moonYoga.applying) {
            score += 10; // Moon connecting is helpful
        }

        // 3. Planet Strength (Combustion/Retrograde)
        if (llData.isCombust) score -= 20;
        if (klData.isCombust) score -= 20;
        
        // Retrograde Karyesha often means delay or return
        if (klData.speed < 0) score -= 10; 

        // 4. Indicators
        indicators.forEach(i => score += (i.value * 10));

        // 5. Moon Strength
        if (moonData.isCombust) score -= 15;
        // Moon in 6/8/12 is bad
        // ... (can add house logic)

        return Math.max(0, Math.min(100, score));
    }

    getVerdict(score) {
        if (score >= 75) return 'Excellent - Success likely';
        if (score >= 60) return 'Good - Success with effort';
        if (score >= 40) return 'Average - Mixed results/Delay';
        if (score >= 25) return 'Weak - Difficulties indicated';
        return 'Poor - Unlikely to succeed';
    }

    /**
     * Mook Prashna (Silent Question)
     * Identifies the topic of question based on Lagna/Moon position
     */
    identifyQuestionTopic(data) {
        const lagnaIdx = data.lagna.rasi.index;
        const moonIdx = data.planets.Moon.rasi.index;
        
        const topics = {
            0: 'Self/Health',
            1: 'Wealth/Family',
            2: 'Siblings/Courage',
            3: 'Home/Mother',
            4: 'Children/Creativity',
            5: 'Illness/Enemies',
            6: 'Marriage/Partner',
            7: 'Longevity/Trouble',
            8: 'Fortune/Travel',
            9: 'Career/Status',
            10: 'Gains/Income',
            11: 'Losses/Expenses'
        };

        const dist = (moonIdx - lagnaIdx + 12) % 12;
        return topics[dist] || 'General Query';
    }

    /**
     * Random selection for Ashtamangala Prashna
     */
    getAshtamangalaNumber() {
        const r1 = Math.floor(Math.random() * 8) + 1;
        const r2 = Math.floor(Math.random() * 8) + 1;
        const r3 = Math.floor(Math.random() * 8) + 1;
        const total = (r1 * 100) + (r2 * 10) + r3;
        return { r1, r2, r3, total };
    }

    /**
     * Anka Prashna (Number Divination)
     * User picks a number between 1 and 249 (KP System) or 1 and 108 (Navamsha).
     * @param {number} number - User selection
     * @param {number} max - 108 or 249
     */
    getAnkaPrashna(number, max = 108) {
        if (number < 1 || number > max) return { error: 'Invalid number' };
        
        let signIdx, nakIdx;
        
        if (max === 108) {
            // Navamsha based (108 padas)
            // 1 sign = 9 padas
            signIdx = Math.floor((number - 1) / 9);
            const remainder = (number - 1) % 9;
            // Nakshatra? 1 Nak = 4 padas.
            nakIdx = Math.floor((number - 1) / 4);
            const pada = ((number - 1) % 4) + 1;
            
            return {
                system: 'Navamsha (1-108)',
                number,
                lagnaSign: RASI_NAMES[signIdx],
                nakshatra: NAKSHATRA_NAMES[nakIdx] || 'Unknown', // Need to import NAKSHATRA_NAMES if not avail
                pada
            };
        } else {
            // KP System (1-249 subs) - Simplified placeholder
            // In reality requires a lookup table of Subs.
            // We'll calculate roughly based on degree.
            const degPerSub = 360 / 249;
            const deg = (number - 1) * degPerSub;
            signIdx = Math.floor(deg / 30);
            return {
                system: 'KP (1-249)',
                number,
                approxDegree: deg.toFixed(2),
                sign: RASI_NAMES[signIdx]
            };
        }
    }
}

export default new PrashnaEngine();
