import I18n from '../core/i18n.js';

/**
 * DashaAnalysis Engine
 * Provides modular interpretations for all dasha systems and levels.
 */
class DashaAnalysis {
    constructor() {
        this.yoginiLords = {
            'Mangala': 'Moon',
            'Pingala': 'Sun',
            'Dhanya': 'Jupiter',
            'Bhramari': 'Mars',
            'Bhadrika': 'Mercury',
            'Ulka': 'Saturn',
            'Siddha': 'Venus',
            'Sankata': 'Rahu'
        };
    }

    /**
     * Analyzes a specific dasha system and its active path.
     * @param {string} system System ID (vimshottari, yogini, chara, etc.)
     * @param {Array} hierarchy The dasha list from Vedic.calculate()
     * @param {Object} ctx Analysis context (chart, helpers, etc.)
     * @returns {Object} Analysis sections
     */
    analyze(system, hierarchy, ctx) {
        if (!hierarchy || !hierarchy.length) return null;

        const now = new Date();
        const path = this._getActivePath(hierarchy, now);

        if (!path || path.length === 0) return null;

        switch (system) {
            case 'vimshottari':
            case 'ashtottari':
            case 'shodashottari':
            case 'dwadashottari':
                return this._analyzeStandard(system, path, ctx);
            case 'yogini':
                return this._analyzeYogini(path, ctx);
            case 'chara':
                return this._analyzeChara(path, ctx);
            default:
                return this._analyzeGeneric(system, path, ctx);
        }
    }

    /**
     * Finds the active dasha items at each level.
     */
    _getActivePath(list, now) {
        const path = [];
        let currentLevel = list;

        while (currentLevel) {
            const active = currentLevel.find(d => now >= d.start && now <= d.end);
            if (!active) break;
            path.push(active);
            currentLevel = active.antardashas && active.antardashas.length > 0 ? active.antardashas : null;
        }
        return path;
    }

    /**
     * Analysis for planet-based systems (Vimshottari, etc.)
     */
    _analyzeStandard(system, path, ctx) {
        const { chart, helpers } = ctx;
        const lagnaIdx = chart.lagna.rasi.index;

        return path.map((item, level) => {
            const planet = item.planet;
            const strength = helpers.getStrength(planet);
            const house = helpers.getHouse(chart.planets[planet] ? chart.planets[planet].lon : 0);
            const lordOf = this._getHousesLordedBy(planet, lagnaIdx);

            // Basic interpretation blocks
            let interpretation = '';

            if (level === 0) { // Mahadasha
                interpretation = I18n.t('analysis.md_lord_of', {
                    md: this._getDisplayName(planet),
                    houses: lordOf.map(h => I18n.n(h)).join(', ')
                }) + ' ' + I18n.t('analysis.md_placed_in', {
                    house: I18n.n(house),
                    status: I18n.t('shadbala.status.' + (strength ? strength.status : 'neutral'))
                });
            } else { // Sub periods
                interpretation = I18n.t('analysis.ad_lord_of', {
                    ad: this._getDisplayName(planet),
                    houses: lordOf.map(h => I18n.n(h)).join(', '),
                    house: I18n.n(house)
                });

                const themes = lordOf.map(h => I18n.t('analysis.house_themes.' + h)).join(', ');
                if (strength && strength.status === 'strong') {
                    interpretation += ' ' + I18n.t('analysis.ad_favorable', { themes });
                } else if (strength && strength.status === 'weak') {
                    interpretation += ' ' + I18n.t('analysis.ad_caution', { themes });
                }
            }

            return {
                level,
                planet,
                planetName: this._getDisplayName(planet),
                start: item.start,
                end: item.end,
                interpretation
            };
        });
    }

    /**
     * Specific analysis for Yogini Dasha
     */
    _analyzeYogini(path, ctx) {
        return path.map((item, level) => {
            const planet = item.planet; // This is the Yogini name (Mangala, etc.)
            const interpretation = I18n.t(`analysis.yogini_interpretations.${planet}`);

            return {
                level,
                planet,
                planetName: this._getDisplayName(planet),
                start: item.start,
                end: item.end,
                interpretation
            };
        });
    }

    /**
     * Specific analysis for Chara Dasha (Jaimini)
     */
    _analyzeChara(path, ctx) {
        return path.map((item, level) => {
            const rasi = item.planet; // For Chara, planet field holds Rasi name
            const interpretation = I18n.t(`analysis.chara_interpretations.${rasi}`);

            return {
                level,
                planet: rasi,
                planetName: this._getDisplayName(rasi),
                start: item.start,
                end: item.end,
                interpretation
            };
        });
    }

    _analyzeGeneric(system, path, ctx) {
        return path.map((item, level) => {
            return {
                level,
                planet: item.planet,
                planetName: this._getDisplayName(item.planet),
                start: item.start,
                end: item.end,
                interpretation: I18n.t('analysis.generic_dasha_period')
            };
        });
    }

    _getDisplayName(key) {
        if (!key) return '';
        const planetTrans = I18n.t('planets.' + key);
        if (planetTrans !== 'planets.' + key) return planetTrans;
        
        const rasiTrans = I18n.t('rasis.' + key);
        if (rasiTrans !== 'rasis.' + key) return rasiTrans;

        return key.charAt(0).toUpperCase() + key.slice(1);
    }

    _getHousesLordedBy(planet, lagnaIdx) {
        const rulers = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter'];
        const houses = [];
        for (let h = 1; h <= 12; h++) {
            const signIdx = (lagnaIdx + h - 1) % 12;
            if (rulers[signIdx] === planet) houses.push(h);
        }
        return houses;
    }
}

export default new DashaAnalysis();
