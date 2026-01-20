/**
 * Yoga Strength Engine
 * Calculates dynamic strength (potency) and activation timing for yogas.
 */

import { signLords, exaltation, debilitation, ownSigns, moolatrikona, sevenPlanets } from './base.js';

export class StrengthEngine {
    constructor(ctx) {
        this.ctx = ctx;
    }

    /**
     * Process a list of yogas and add strength/activation data
     * @param {Array} yogas - List of detected yogas
     * @returns {Array} Processed yogas
     */
    process(yogas) {
        return yogas.map(yoga => {
            const strengthData = this.calculateStrength(yoga);
            const activation = this.calculateActivation(yoga);

            return {
                ...yoga,
                strengthScore: strengthData.score,
                strengthDetails: strengthData.details,
                activationPeriods: activation
            };
        });
    }

    /**
     * Calculate potency score (0-100)
     */
    calculateStrength(yoga) {
        let score = 0;
        let count = 0;
        const details = [];

        // 1. Planet Strengths
        if (yoga.planets && yoga.planets.length > 0) {
            yoga.planets.forEach(p => {
                if (!sevenPlanets.includes(p)) return;
                
                let pScore = 0;
                
                // Shadbala (if available) - Max ~1.5 to 2.0 Rupas usually
                if (this.ctx.shadbala && this.ctx.shadbala[p]) {
                    const rupas = this.ctx.shadbala[p].rupas || 1.0;
                    pScore += Math.min(rupas * 10, 20); // Max 20 pts for Shadbala
                }

                // Dignity
                const dig = this.ctx.getDignity(p);
                if (dig === 'Exalted') { pScore += 20; details.push(`${p} Exalted`); }
                else if (dig === 'Moolatrikona') { pScore += 15; details.push(`${p} Moolatrikona`); }
                else if (dig === 'Own') { pScore += 10; details.push(`${p} Own Sign`); }
                else if (dig === 'Debilitated') { pScore -= 10; details.push(`${p} Debilitated`); }

                // Vargottama
                if (this.ctx.navamshaPositions && this.ctx.navamshaPositions[p] === this.ctx.getRasi(p)) {
                    pScore += 10;
                    details.push(`${p} Vargottama`);
                }

                // Avastha (Deepa/Bhojana etc)
                // (Assuming avastha data structure exists)
                
                score += pScore;
                count++;
            });
        }

        // Average planet score + Base strength
        let finalScore = (count > 0 ? score / count : 0) + (yoga.strength * 5); // Base strength 1-10 mapped to 5-50

        // Cap at 100
        return {
            score: Math.max(0, Math.min(100, Math.round(finalScore))),
            details
        };
    }

    /**
     * Determine Dasha/Antardasha activation
     */
    calculateActivation(yoga) {
        if (!yoga.planets || yoga.planets.length === 0) return [];

        // Yoga activates during Dasha/Antardasha of participating planets
        // Especially the strongest ones.
        return yoga.planets.filter(p => sevenPlanets.includes(p) || p === 'Rahu' || p === 'Ketu');
    }
}

export default StrengthEngine;
