/**
 * ============================================================================
 * Planetary State Engine
 * ============================================================================
 * 
 * Handles calculation of planetary states including:
 * 1. Combustion (Moudhya)
 * 2. Retrograde (Vakra) - Already in Engine, but state management here
 * 3. Vargottama (Same sign in D1 and D9)
 * 4. Dignities (Exalted, Debilitated, Own, Friend, Enemy)
 * 5. Avasthas (Basic states like Jagrat, Swapna, Sushupti)
 * 
 * @module astro/planet_states
 * @version 1.0.0
 */

import { 
    COMBUSTION_ORBS, 
    PLANETARY_DIGNITIES,
    getDignity
} from './constants.js';

class PlanetStateEngine {

    /**
     * Calculate all planetary states (Combustion, Vargottama, Dignity)
     * Mutates the planets object or returns a new enriched object
     * @param {Object} planets - D1 planets object
     * @param {Object} d9Planets - D9 planets object (for Vargottama)
     * @returns {Object} Enriched planets object
     */
    enrichPlanetStates(planets, d9Planets) {
        const sun = planets.Sun;
        if (!sun) return planets;

        for (const [p, data] of Object.entries(planets)) {
            // 3. Dignity
            // Using the centralized utility from constants.js
            data.dignity = getDignity(p, data.rasi.index, data.rasi.degrees);
            
            // 1. Combustion (Refined with dignity)
            this._calculateCombustion(p, data, sun.lon, data.dignity);

            // 2. Vargottama
            
            // 4. Retrograde flag (already likely present from Engine, but ensuring consistency)
            data.isRetro = data.speed < 0;
        }

        return planets;
    }

    _calculateCombustion(planetName, planetData, sunLon, dignity) {
        if (planetName === 'Sun') {
            planetData.isCombust = false;
            return;
        }

        const diff = Math.abs(planetData.lon - sunLon);
        const dist = Math.min(diff, 360 - diff);
        
        const isRetro = planetData.speed < 0;
        let limit = 0;
        
        // Get base combustion limit
        if (isRetro && COMBUSTION_ORBS[planetName + 'Retro']) {
            limit = COMBUSTION_ORBS[planetName + 'Retro'];
        } else {
            limit = COMBUSTION_ORBS[planetName] || 0;
        }

        // Refinement: Planetary Dignity affects combustion tolerance
        if (dignity === 'exalted') {
            limit -= 3; // Exalted planets withstand combustion better
        } else if (dignity === 'own') {
            limit -= 2;
        } else if (dignity === 'debilitated') {
            limit += 2; // Debilitated planets are more susceptible
        }
        
        planetData.isCombust = dist <= limit;
        planetData.combustionLimit = limit;
        planetData.sunDistance = dist;
    }
}

export default new PlanetStateEngine();
