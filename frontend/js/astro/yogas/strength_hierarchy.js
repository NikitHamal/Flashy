/**
 * Yoga Hierarchy & Ranking System
 * Implements a standardized ranking system for Yogas to sort them by importance.
 * 
 * Hierarchy Levels (Rank 1 is highest):
 * 1. Mahapurusha Yogas (Pancha Mahapurusha)
 * 2. Primary Raja Yogas (Dharma-Karma Adhipati, Vishnu-Lakshmi)
 * 3. Powerful Wealth Yogas (Dhana, Lakshmi)
 * 4. Neecha Bhanga Raja Yogas (Cancellation of Debilitation)
 * 5. Parivartana Yogas (Exchange of Signs)
 * 6. Vipareeta Raja Yogas
 * 7. Major Lunar Yogas (Gajakesari, Chandra-Mangala, Adhi)
 * 8. Solar Yogas (Vesi, Vasi, Ubhayachari, Budhaditya)
 * 9. Other Auspicious Yogas
 * 10. Neutral/Mixed Yogas
 * 11. Minor Doshas
 * 12. Major Doshas (Kaal Sarpa, Kemadruma, Pitru)
 * 
 * @module yogas/strength_hierarchy
 */

export const YOGA_HIERARCHY = Object.freeze({
    'Mahapurusha': 1,
    'Raja': 2,
    'Dhana': 3,
    'Neecha_Bhanga': 4,
    'Parivartana': 5,
    'Vipareeta_Raja': 6,
    'Gajakesari': 7,
    'Chandra_Mangala': 7,
    'Adhi': 7,
    'Solar': 8,
    'Lunar': 8,
    'Nabhasa': 9,
    'Knowledge': 9,
    'Spiritual': 9,
    'Benefic': 9,
    'Neutral': 10,
    'Dosha': 12,
    'Kaal_Sarpa': 12,
    'Kemadruma': 12,
    'Arishta': 12
});

export class StrengthHierarchy {
    
    /**
     * Apply hierarchy ranking to yogas
     * @param {Array} yogas - List of yogas with calculated strengthScore
     * @returns {Array} Sorted yogas
     */
    applyHierarchy(yogas) {
        return yogas.map(yoga => {
            const rank = this._getRank(yoga);
            return {
                ...yoga,
                rank: rank,
                // Composite score for sorting: (100 - Rank * 5) + (StrengthScore * 0.5)
                // This prioritizes Rank but allows very strong lower-rank yogas to bubble up slightly
                sortScore: (100 - (rank * 5)) + ((yoga.strengthScore || 0) * 0.5)
            };
        }).sort((a, b) => b.sortScore - a.sortScore);
    }

    _getRank(yoga) {
        // Direct category match
        if (YOGA_HIERARCHY[yoga.category]) return YOGA_HIERARCHY[yoga.category];
        
        // Name key match (for specific yogas like Gajakesari that might be categorized as 'Lunar')
        if (YOGA_HIERARCHY[yoga.nameKey]) return YOGA_HIERARCHY[yoga.nameKey];

        // Fallback based on nature
        if (yoga.nature === 'Benefic') return 9;
        if (yoga.nature === 'Malefic') return 12;
        
        return 10; // Neutral default
    }
}

export default new StrengthHierarchy();
