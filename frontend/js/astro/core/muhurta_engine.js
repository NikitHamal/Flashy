/**
 * ============================================================================
 * Muhurta Selection Engine
 * ============================================================================
 * 
 * Implements algorithmic scoring for auspicious timings:
 * 1. Muhurta Quality Scoring
 * 2. Specialized Muhurtas (Marriage, Yatra, Griha Pravesh, etc.)
 * 3. Five-fold Dosha checks
 * 
 * References:
 * - Muhurta Chintamani
 * - BPHS
 * 
 * @module astro/muhurta_engine
 * @version 1.0.0
 */

import PanchangEngine from './panchang_engine.js';
import { KENDRAS, TRIKONAS, DUSTHANAS } from './constants.js';

class MuhurtaEngine {
    constructor() {}

    /**
     * Score a moment for a general auspicious activity
     * @param {Object} panchang - Panchang data
     * @param {Object} charts - Current moment charts
     * @param {Object} natalData - (Optional) User's natal data for Tara/Chandra Bala
     */
    scoreMoment(panchang, charts, natalData = null) {
        let score = 50; // Neutral start

        // 1. Tithi Check
        const { isRikta, isDagdha, index: tithiIdx } = panchang.tithi;
        if (isRikta) score -= 20;
        if (isDagdha) score -= 30;
        const tithiNum = (tithiIdx % 15) + 1;
        if ([4, 9, 14].includes(tithiNum)) score -= 15; // Rikta dates
        if (tithiNum === 1 && tithiIdx < 15) score -= 10; // Shukla Pratipada (generally avoided)
        if (tithiNum === 6 || tithiNum === 8 || tithiNum === 12) score += 10; // Nanda/Bhadra/Jaya good

        // 2. Vara Check
        const vara = panchang.vara;
        if (['Tuesday', 'Saturday', 'Sunday'].includes(vara)) score -= 10; // Malefic days
        if (['Monday', 'Wednesday', 'Thursday', 'Friday'].includes(vara)) score += 10;

        // 3. Nakshatra Check (General)
        const nakIdx = panchang.nakshatra.index;
        // Fixed (Dhruva) & Gentle (Mridu) are generally good
        const goodNaks = [11, 20, 25, 3, 4, 13, 26, 16]; 
        if (goodNaks.includes(nakIdx)) score += 15;
        // Ugra/Krura (Fierce)
        const badNaks = [1, 9, 18, 19, 24];
        if (badNaks.includes(nakIdx)) score -= 10;

        // 4. Karana Check
        if (panchang.karana.isVishti) score -= 40; // Bhadra Karana - Avoid!

        // 5. Yoga Check (Nitya Yoga)
        if (panchang.yoga.isShunya) score -= 20;
        const badYogas = [0, 5, 8, 9, 16, 26]; // Vishkumbha, Atiganda, Shula, Ganda, Vyatipata, Vaidhriti
        if (badYogas.includes(panchang.yoga.index)) score -= 15;

        // 6. Lagna Strength (Lagna Shuddhi)
        const lagnaIdx = charts.lagna.rasi.index;
        const lagnaLord = charts.houses[1].lord;
        const lordData = charts.planets[lagnaLord];
        
        // Lagna Lord strength (Exalted, Own, Kendra/Trikona)
        if (lordData) {
            const lordHouse = ((lordData.rasi.index - lagnaIdx + 12) % 12) + 1;
            if (KENDRAS.includes(lordHouse) || TRIKONAS.includes(lordHouse)) score += 15;
            if (DUSTHANAS.includes(lordHouse)) score -= 10;
        }

        // Benefics in Kendras (1, 4, 7, 10) increase score
        // Malefics in Kendras decrease score (except 3, 6, 11)
        Object.entries(charts.planets).forEach(([name, data]) => {
            const house = ((data.rasi.index - lagnaIdx + 12) % 12) + 1;
            const isBenefic = ['Jupiter', 'Venus', 'Moon', 'Mercury'].includes(name);
            const isMalefic = ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu'].includes(name);

            if (isBenefic && KENDRAS.includes(house)) score += 5;
            if (isMalefic && KENDRAS.includes(house)) score -= 5;
            
            // Malefics in 3, 6, 11 are good
            if (isMalefic && [3, 6, 11].includes(house)) score += 5;
            // 8th house should be empty
            if (house === 8) score -= 10;
        });

        // 7. Personalized Checks (Tara/Chandra Bala)
        if (natalData) {
            score += this.calculateTaraBala(natalData.nakshatraIndex, nakIdx);
            score += this.calculateChandraBala(natalData.rasiIndex, charts.planets.Moon.rasi.index);
        }

        return Math.max(0, Math.min(100, score));
    }

    /**
     * Calculate Tara Bala (Star Strength)
     * Groups of 9 nakshatras from Janma Nakshatra
     * 1 (Janma) - Danger/Mixed
     * 2 (Sampat) - Wealth/Good (+10)
     * 3 (Vipat) - Danger (-10)
     * 4 (Kshema) - Prosperity (+10)
     * 5 (Pratyak) - Obstacles (-10)
     * 6 (Sadhana) - Achievement (+10)
     * 7 (Naidhana) - Danger/Death (-15)
     * 8 (Mitra) - Friend (+10)
     * 9 (Parama Mitra) - Best Friend (+15)
     */
    calculateTaraBala(birthNakIdx, currentNakIdx) {
        if (birthNakIdx === undefined || currentNakIdx === undefined) return 0;
        
        // Count from Birth to Current
        let count = (currentNakIdx - birthNakIdx + 27) % 27 + 1;
        let remainder = count % 9;
        if (remainder === 0) remainder = 9;

        const scores = {
            1: -5,  // Janma
            2: 10,  // Sampat
            3: -10, // Vipat
            4: 10,  // Kshema
            5: -10, // Pratyak
            6: 10,  // Sadhana
            7: -15, // Naidhana (Vadhas)
            8: 10,  // Mitra
            9: 15   // Parama Mitra
        };

        return scores[remainder] || 0;
    }

    /**
     * Calculate Chandra Bala (Moon Strength)
     * Moon's transit position relative to Natal Moon
     * Good: 1, 3, 6, 7, 10, 11
     * Bad: 4, 8, 12
     * Neutral: 2, 5, 9
     */
    calculateChandraBala(birthRasiIdx, currentRasiIdx) {
        if (birthRasiIdx === undefined || currentRasiIdx === undefined) return 0;

        const house = ((currentRasiIdx - birthRasiIdx + 12) % 12) + 1;
        
        if ([1, 3, 6, 7, 10, 11].includes(house)) return 15;
        if ([4, 8, 12].includes(house)) return -15; // Chandrashtama (8) is worst
        return 0; // 2, 5, 9 are neutral/mixed
    }

    /**
     * Specialized Marriage Muhurta Scoring
     */
    scoreMarriage(panchang, charts, natalData = null) {
        let base = this.scoreMoment(panchang, charts, natalData);
        
        // Marriage Specifics
        const lagnaIdx = charts.lagna.rasi.index;
        const house7Idx = (lagnaIdx + 6) % 12;
        const venus = charts.planets.Venus;
        const jupiter = charts.planets.Jupiter;

        // 1. 7th House must be pure
        let maleficIn7 = false;
        Object.values(charts.planets).forEach(p => {
            if (p.rasi.index === house7Idx && ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu'].includes(p.name)) {
                maleficIn7 = true;
            }
        });
        if (maleficIn7) base -= 40; // Critical flaw

        // 2. Venus not combust or retrograde (essential for marriage)
        if (venus.isCombust) base -= 20;
        if (venus.speed < 0) base -= 10;

        // 3. Jupiter Strength
        if (jupiter.isCombust) base -= 10;

        // 4. Godhuli Lagna (Cow dust time - Sunset) is often considered auspicious fallback
        // Check if close to sunset? (Omitted for now, needs exact timing)

        return Math.max(0, Math.min(100, base));
    }
}

export default new MuhurtaEngine();
