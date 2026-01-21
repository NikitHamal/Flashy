/**
 * ============================================================================
 * Advanced Panchang Engine
 * ============================================================================
 * 
 * Implements refined Panchang calculations:
 * 1. Tithi Shunya (Void Tithis)
 * 2. Dagdha Tithi/Rasi (Burnt combinations)
 * 3. Rikta Tithi Analysis
 * 4. Yoga Shunya Points
 * 5. Karana Classification (Chara, Sthira, Adhomukha)
 * 
 * References:
 * - Muhurta Chintamani
 * - Brihat Samhita
 * - BPHS
 * 
 * @module astro/panchang_engine
 * @version 1.0.0
 */

import Engine from './engine.js';
import { 
    RASI_NAMES, 
    TITHI_NAMES, 
    NITYA_YOGA_NAMES 
} from './constants.js';

class PanchangEngine {
    constructor() {}

    /**
     * Calculate complete Panchang
     * @param {Date} date - Date of calculation
     * @param {Object} location - { lat, lng }
     * @param {number} sunLon - Sun longitude
     * @param {number} moonLon - Moon longitude
     * @param {Object} moonNakshatra - Moon nakshatra object { index, name, pada }
     * @returns {Object} Complete Panchang data
     */
    calculate(date, location, sunLon, moonLon, moonNakshatra) {
        // 1. Tithi Calculation
        let diff = moonLon - sunLon;
        if (diff < 0) diff += 360;

        const tithiIndex = Math.floor(diff / 12) % 30;
        const tithiName = TITHI_NAMES[tithiIndex];
        const paksha = tithiIndex < 15 ? 'Shukla' : 'Krishna';
        const tithiLeft = 12 - (diff % 12); // Degrees left

        // 2. Yoga Calculation
        const sum = (moonLon + sunLon) % 360;
        const yogaIndex = Math.floor((sum * 27) / 360) % 27;
        const yogaName = NITYA_YOGA_NAMES[yogaIndex];

        // 3. Karana Calculation
        const karanaNum = Math.floor(diff / 6); // 0-59 range
        let karanaName = '';
        let karanaIndex = 0;

        // Precise Mapping of 60 Karanas:
        if (karanaNum === 0) {
            karanaName = 'Kimstughna';
            karanaIndex = 10; // Fixed index
        } else if (karanaNum >= 57) {
            const fixedIndices = [7, 8, 9]; // Shakuni, Chatushpada, Naga
            const fixedNames = ['Shakuni', 'Chatushpada', 'Naga'];
            karanaIndex = fixedIndices[karanaNum - 57];
            karanaName = fixedNames[karanaNum - 57];
        } else {
            const movingIndex = (karanaNum - 1) % 7;
            const movingKaranas = ['Bava', 'Balava', 'Kaulava', 'Taitila', 'Gara', 'Vanija', 'Vishti'];
            karanaName = movingKaranas[movingIndex];
            karanaIndex = movingIndex;
        }

        // 4. Vara (Weekday) Calculation - Sunrise based
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const { sunrise, sunset } = Engine.getSunriseSunset(date, location.lat, location.lng);
        
        let dayIdx = date.getDay();
        if (sunrise && date < sunrise) {
            // Before sunrise, it's the previous Vedic day
            dayIdx = (dayIdx + 6) % 7;
        }
        const vara = days[dayIdx];

        // 5. Advanced Analysis (Shunya, Dagdha, etc.)
        const shunyaRasis = this.getTithiShunyaRasis(tithiIndex);
        const isDagdha = this.isDagdhaTithi(tithiIndex, dayIdx);
        const rikta = this.getRiktaStatus(tithiIndex);
        const karanaClass = this.getKaranaClassification(karanaNum);
        const isYogaShunya = this.isYogaShunya(yogaIndex, sum);
        const panchaka = this.calculatePanchaka(tithiIndex, dayIdx, moonNakshatra.index);

        const specialPeriods = this.calculateSpecialMuhurtas(sunrise, sunset);
        const choghadiya = this.calculateChoghadiya(sunrise, sunset, dayIdx);
        const inauspicious = this.calculateInauspiciousPeriods(sunrise, sunset, dayIdx);
        const durmuhurtas = this.calculateDurmuhurtas(sunrise, sunset, dayIdx);

        return {
            tithi: { 
                name: tithiName, 
                paksha: paksha, 
                index: tithiIndex,
                shunyaRasis: shunyaRasis,
                isDagdha: isDagdha,
                isRikta: rikta.isRikta,
                timeLeftDegrees: tithiLeft
            },
            nakshatra: moonNakshatra,
            yoga: { 
                name: yogaName, 
                index: yogaIndex,
                isShunya: isYogaShunya
            },
            karana: { 
                name: karanaName, 
                index: karanaIndex,
                type: karanaClass.type,
                isAdhomukha: karanaClass.isAdhomukha,
                isVishti: karanaClass.isVishti
            },
            vara: vara,
            dayIndex: dayIdx,
            sunrise: sunrise,
            sunset: sunset,
            panchaka: panchaka,
            muhurta: {
                ...specialPeriods,
                choghadiya,
                inauspicious,
                durmuhurtas
            }
        };
    }

    /**
     * Identify Tithi Shunya Rasis (Void Signs for a Tithi)
     * @param {number} tithiIdx - Tithi index (0-29)
     * @returns {string[]} Names of void signs
     */
    getTithiShunyaRasis(tithiIdx) {
        // Tithi indices are 0-14 (Shukla) and 15-29 (Krishna)
        const tithiNum = (tithiIdx % 15) + 1; // 1 to 15
        
        const shunyaMap = {
            1: [11, 2], // Pratipada: Meena, Mithuna? No, different texts say different.
            // Standard Muhurta Chintamani rules:
            2: [3, 11], // Dwitiya: Karka, Meena
            3: [1, 5],  // Tritiya: Vrishabha, Kanya
            4: [2, 11], // Chaturthi: Mithuna, Meena
            5: [2, 5],  // Panchami: Mithuna, Kanya
            6: [6, 10], // Shashthi: Tula, Kumbha
            7: [2, 11], // Saptami: Mithuna, Meena
            8: [2, 5],  // Ashtami: Mithuna, Kanya
            9: [3, 10], // Navami: Karka, Kumbha
            10: [3, 11], // Dashami: Karka, Meena
            11: [3, 11], // Ekadashi: Karka, Meena
            12: [6, 10], // Dwadashi: Tula, Kumbha
            13: [1, 5],  // Trayodashi: Vrishabha, Kanya
            14: [2, 5, 11, 8] // Chaturdashi: Mithuna, Kanya, Meena, Dhanu
        };

        // Note: Pratipada, Purnima and Amavasya don't have standard Shunya Rasis in all traditions
        // but some say 1: [11, 2]. 
        
        const rasiIndices = shunyaMap[tithiNum] || [];
        return rasiIndices.map(idx => RASI_NAMES[idx]);
    }

    /**
     * Identify Dagdha (Burnt) combinations of Tithi and Weekday
     * @param {number} tithiIdx - Tithi index (0-29)
     * @param {number} dayOfWeek - 0 (Sun) to 6 (Sat)
     * @returns {boolean}
     */
    isDagdhaTithi(tithiIdx, dayOfWeek) {
        const tithiNum = (tithiIdx % 15) + 1;
        
        const dagdhaMap = {
            0: 12, // Sunday: Dwadashi
            1: 11, // Monday: Ekadashi
            2: 5,  // Tuesday: Panchami
            3: 3,  // Wednesday: Tritiya
            4: 6,  // Thursday: Shashthi
            5: 8,  // Friday: Ashtami
            6: 9   // Saturday: Navami
        };

        return dagdhaMap[dayOfWeek] === tithiNum;
    }

    /**
     * Identify Rikta (Empty/Negative) Tithis
     * @param {number} tithiIdx - Tithi index (0-29)
     * @returns {Object} { isRikta: boolean, name: string }
     */
    getRiktaStatus(tithiIdx) {
        const tithiNum = (tithiIdx % 15) + 1;
        const riktaTithis = [4, 9, 14];
        return {
            isRikta: riktaTithis.includes(tithiNum),
            name: riktaTithis.includes(tithiNum) ? 'Rikta' : 'Nanda/Bhadra/Jaya/Purana'
        };
    }

    /**
     * Classify Karana into Chara, Sthira and Adhomukha
     * @param {number} karanaNum - 0-59
     * @returns {Object}
     */
    getKaranaClassification(karanaNum) {
        // Karana types
        // Sthira (Fixed): Shakuni(57), Chatushpada(58), Naga(59), Kimstughna(0)
        // Chara (Movable): Bava, Balava, Kaulava, Taitila, Gara, Vanija, Vishti (1-56)
        
        const isSthira = karanaNum === 0 || karanaNum >= 57;
        const type = isSthira ? 'Sthira' : 'Chara';
        
        // Adhomukha (Facing downwards) - Vishti is always Adhomukha
        const isAdhomukha = (karanaNum % 7 === 0 && karanaNum !== 0 && karanaNum < 57); // Vishti is the 7th in cycle
        
        return {
            type: type,
            isAdhomukha: isAdhomukha,
            isVishti: isAdhomukha
        };
    }

    /**
     * Yoga Shunya Points
     * Certain degrees within a Yoga are considered void.
     * @param {number} yogaIdx - 0-26
     * @param {number} yogaLon - Total Sun+Moon longitude (0-360)
     * @returns {boolean}
     */
    isYogaShunya(yogaIdx, yogaLon) {
        // Each Yoga is 13°20'
        const posInYoga = yogaLon % (360/27);
        // Standard rule: The last 1/6th of certain yogas are Shunya
        // For Vyatipata and Vaidhriti, the entire yoga is considered challenging.
        const sensitiveYogas = [0, 5, 8, 9, 12, 14, 16, 26]; // Vishkumbha, Atiganda, Shula, Ganda, Vyaghata, Vajra, Vyatipata, Vaidhriti
        
        if (sensitiveYogas.includes(yogaIdx)) {
            // Check if it's in the last 2 degrees (approx 1/6th)
            return posInYoga > (13.333 - 2.222);
        }
        
        return false;
    }

    /**
     * Calculate Choghadiya periods for a given day
     * @param {Date} sunrise 
     * @param {Date} sunset 
     * @param {number} dayOfWeek 
     */
    calculateChoghadiya(sunrise, sunset, dayOfWeek) {
        const dayDuration = (sunset.getTime() - sunrise.getTime()) / 8;
        const nextSunrise = new Date(sunrise.getTime() + 24 * 60 * 60 * 1000);
        const nightDuration = (nextSunrise.getTime() - sunset.getTime()) / 8;

        const daySequence = [
            [4, 5, 6, 0, 1, 2, 3, 4], // Sun: Udveg, Char, Labh, Amrit, Kaal, Shubh, Rog, Udveg
            [1, 2, 3, 4, 5, 6, 0, 1], // Mon
            [5, 6, 0, 1, 2, 3, 4, 5], // Tue
            [2, 3, 4, 5, 6, 0, 1, 2], // Wed
            [6, 0, 1, 2, 3, 4, 5, 6], // Thu
            [3, 4, 5, 6, 0, 1, 2, 3], // Fri
            [0, 1, 2, 3, 4, 5, 6, 0]  // Sat
        ];
        // Names: 0:Amrit (Good), 1:Shubh (Good), 2:Labh (Good), 3:Char (Neutral), 4:Udveg (Bad), 5:Kaal (Bad), 6:Rog (Bad)
        const types = ['Amrit', 'Shubh', 'Labh', 'Char', 'Udveg', 'Kaal', 'Rog'];
        const qualities = ['Good', 'Good', 'Good', 'Neutral', 'Bad', 'Bad', 'Bad'];

        const getPeriods = (start, duration, seqIdx) => {
            const seq = daySequence[dayOfWeek];
            // sequence shift for night is 5 slots
            const actualSeq = seqIdx === 'day' ? seq : seq.map((_, i) => seq[(i + 5) % 7]);
            
            return actualSeq.map((s, i) => ({
                name: types[s],
                quality: qualities[s],
                start: new Date(start.getTime() + i * duration),
                end: new Date(start.getTime() + (i + 1) * duration)
            }));
        };

        return {
            day: getPeriods(sunrise, dayDuration, 'day'),
            night: getPeriods(sunset, nightDuration, 'night')
        };
    }

    /**
     * Calculate Rahu Kalam, Yamagandam and Gulika Kalam
     */
    calculateInauspiciousPeriods(sunrise, sunset, dayOfWeek) {
        const dayDuration = (sunset.getTime() - sunrise.getTime()) / 8;
        
        // Parts (1-8) for each day
        const rahuMap = [8, 2, 7, 5, 6, 4, 3]; // Sun to Sat
        const yamaMap = [5, 4, 3, 2, 1, 7, 6];
        const guliMap = [7, 6, 5, 4, 3, 2, 1];

        const getRange = (part) => ({
            start: new Date(sunrise.getTime() + (part - 1) * dayDuration),
            end: new Date(sunrise.getTime() + part * dayDuration)
        });

        return {
            rahuKalam: getRange(rahuMap[dayOfWeek]),
            yamagandam: getRange(yamaMap[dayOfWeek]),
            gulikaKalam: getRange(guliMap[dayOfWeek])
        };
    }

    /**
     * Calculate Abhijit and Brahma Muhurta
     */
    calculateSpecialMuhurtas(sunrise, sunset) {
        const dayLen = sunset - sunrise;
        const nightLen = (24 * 60 * 60 * 1000) - dayLen;
        
        // Abhijit is the 8th Muhurta of the day (total 15)
        const abhijitStart = new Date(sunrise.getTime() + (dayLen / 15) * 7);
        const abhijitEnd = new Date(sunrise.getTime() + (dayLen / 15) * 8);

        // Brahma Muhurta is the 2nd to last Muhurta of the night (total 15)
        // Starts 2 Muhurtas before sunrise (approx 1hr 36m)
        const muhurtaLen = 48 * 60 * 1000; // Standard fixed 48m or 1/15th of night
        const brahmaStart = new Date(sunrise.getTime() - 2 * (nightLen / 15));
        const brahmaEnd = new Date(sunrise.getTime() - (nightLen / 15));

        return {
            abhijit: { start: abhijitStart, end: abhijitEnd },
            brahma: { start: brahmaStart, end: brahmaEnd }
        };
    }

    /**
     * Calculate Durmuhurta periods
     * Inauspicious Muhurtas based on weekday
     */
    calculateDurmuhurtas(sunrise, sunset, dayOfWeek) {
        const muhurtaLen = (sunset.getTime() - sunrise.getTime()) / 15;
        
        // Muhurta indices (1-15) that are Durmuhurta for each day
        const durMap = {
            0: [14],    // Sun: 14th
            1: [9, 15], // Mon: 9th, 15th
            2: [2, 7],  // Tue: 2nd, 7th
            3: [7],     // Wed: 7th
            4: [12, 13],// Thu: 12th, 13th
            5: [9, 15], // Fri: 9th, 15th
            6: [1]      // Sat: 1st
        };

        const indices = durMap[dayOfWeek] || [];
        return indices.map(idx => ({
            index: idx,
            start: new Date(sunrise.getTime() + (idx - 1) * muhurtaLen),
            end: new Date(sunrise.getTime() + idx * muhurtaLen)
        }));
    }

    /**
     * Calculate Panchaka Dosha (Inauspicious Nakshatra periods)
     * Based on Tithi, Vara, Nakshatra
     */
    calculatePanchaka(tithiIdx, dayOfWeek, nakIdx) {
        // Rule: If Moon is in Dhanishta(last 2 padas) to Revati
        // indices: Dhanishta(22), Shatabhisha(23), P.Bhadrapada(24), U.Bhadrapada(25), Revati(26)
        if (nakIdx >= 22 && nakIdx <= 26) {
            const names = ['Rog', 'Agni', 'Nrpa', 'Chora', 'Mrtyu'];
            // Specific types of Panchaka based on weekday
            const type = dayOfWeek === 0 ? 'Roga' : (dayOfWeek === 1 ? 'Raj' : 'Agni');
            return { isPanchaka: true, type: type };
        }
        return { isPanchaka: false };
    }
}

export default new PanchangEngine();