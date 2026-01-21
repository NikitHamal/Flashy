/**
 * ============================================================================
 * Upagrahas & Apogees Engine
 * ============================================================================
 * 
 * Implements calculation of secondary planets (Upagrahas) and 
 * sub-planets (Mandi/Gulika) per BPHS and other classical texts.
 * 
 * Upagrahas:
 * 1. Dhuma
 * 2. Vyatipata
 * 3. Parivesha
 * 4. Indrachapa (Kodanda)
 * 5. Upaketu (Shikhi)
 * 
 * Sub-planets:
 * 1. Mandi
 * 2. Gulika
 * 
 * References:
 * - BPHS Chapter 3 (Calculation of Mandi/Gulika)
 * - BPHS Chapter 4 (Upagrahas)
 * 
 * @module astro/upagrahas
 * @version 1.0.0
 */

import Engine from './engine.js';
import { RASI_NAMES, NAKSHATRA_NAMES, NAKSHATRA_SPAN } from './constants.js';

class UpagrahaEngine {
    constructor() {}

    /**
     * Calculate all Upagrahas based on Sun's position
     * @param {number} sunLon - Sidereal Sun longitude
     * @returns {Object} Upagraha positions
     */
    calculateUpagrahas(sunLon) {
        // 1. Dhuma = Sun + 133°20'
        const dhuma = (sunLon + 133 + 20/60) % 360;

        // 2. Vyatipata = 360° - Dhuma
        const vyatipata = (360 - dhuma) % 360;

        // 3. Parivesha = Vyatipata + 180°
        const parivesha = (vyatipata + 180) % 360;

        // 4. Indrachapa = 360° - Parivesha
        const indrachapa = (360 - parivesha) % 360;

        // 5. Upaketu = Indrachapa + 16°40'
        const upaketu = (indrachapa + 16 + 40/60) % 360;

        return {
            Dhuma: this._formatPosition(dhuma),
            Vyatipata: this._formatPosition(vyatipata),
            Parivesha: this._formatPosition(parivesha),
            Indrachapa: this._formatPosition(indrachapa),
            Upaketu: this._formatPosition(upaketu)
        };
    }

    /**
     * Calculate Mandi and Gulika
     * These depend on the weekday and day/night duration.
     * 
     * @param {Date} date - Birth date/time
     * @param {Object} location - Location {lat, lng}
     * @param {number} ayanamsa - Ayanamsa
     * @returns {Object} Mandi and Gulika positions
     */
    calculateMandiGulika(date, location, ayanamsa) {
        const { sunrise, sunset, dayDuration, nightDuration, isDaytime } = Engine.getDayNightDuration(date, location.lat, location.lng);
        
        // Day of week (0=Sunday, 1=Monday, ..., 6=Saturday)
        const dayOfWeek = date.getDay();
        
        // Parts of day/night when Gulika/Mandi rise (per weekday)
        // Lord of the part: Sun(1), Mon(2), ..., Sat(7)
        // Gulika rises at the START of the Saturn part.
        // Mandi rises at the END of the Saturn part (or start of 8th part).
        // Standard rule for 8 parts:
        // Weekday: Sun Mon Tue Wed Thu Fri Sat
        // Gulika (Part #): 7 6 5 4 3 2 1
        
        const gulikaPartsDay = [7, 6, 5, 4, 3, 2, 1];
        const gulikaPartsNight = [3, 2, 1, 7, 6, 5, 4]; // Night sequence starts from 5th lord

        let partNum;
        let partDuration;
        let startTime;

        if (isDaytime) {
            partNum = gulikaPartsDay[dayOfWeek];
            partDuration = dayDuration / 8;
            startTime = sunrise.getTime();
        } else {
            partNum = gulikaPartsNight[dayOfWeek];
            partDuration = nightDuration / 8;
            startTime = sunset.getTime();
        }

        // Gulika rises at the beginning of the part
        const gulikaTimeMs = startTime + (partNum - 1) * partDuration * 60000;
        const gulikaDate = new Date(gulikaTimeMs);
        const gulikaLagnaTropical = Engine.calculateLagna(gulikaDate, location.lat, location.lng);
        const gulikaLon = (gulikaLagnaTropical - ayanamsa + 360) % 360;

        // Mandi rises at the end of the Saturn part (which is start of Gulika's part + duration)
        // Some traditions say Mandi and Gulika are the same, some say they differ.
        // BPHS implies Mandi rises at the end of the Saturn part.
        const mandiTimeMs = startTime + (partNum) * partDuration * 60000;
        const mandiDate = new Date(mandiTimeMs);
        const mandiLagnaTropical = Engine.calculateLagna(mandiDate, location.lat, location.lng);
        const mandiLon = (mandiLagnaTropical - ayanamsa + 360) % 360;

        return {
            Gulika: this._formatPosition(gulikaLon),
            Mandi: this._formatPosition(mandiLon)
        };
    }

    _formatPosition(lon) {
        const signIdx = Math.floor(lon / 30);
        const degInSign = lon % 30;
        const nakIdx = Math.floor(lon / NAKSHATRA_SPAN);
        const pada = Math.floor((lon % NAKSHATRA_SPAN) / (NAKSHATRA_SPAN / 4)) + 1;

        return {
            lon: lon,
            rasi: {
                index: signIdx,
                name: RASI_NAMES[signIdx],
                degrees: degInSign
            },
            nakshatra: {
                index: nakIdx,
                name: NAKSHATRA_NAMES[nakIdx],
                pada: pada
            }
        };
    }
}

export default new UpagrahaEngine();
