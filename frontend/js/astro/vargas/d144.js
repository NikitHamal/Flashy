import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

class D144Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D144', 'Sun');
    }

    analyzeCoreSignificance(data) {
        const lagnaName = I18n.t('rasis.' + data.lagna.sign);
        const lordName = I18n.t('planets.' + data.lagna.lord);
        const lagnaKeywords = I18n.t('analysis.keywords.' + data.lagna.sign);

        let narrative = `### Deep Ancestral Roots and Generational Karma\n\n`;
        narrative += `The Dwadash-Dwadashamsha (D144) is the most microscopic standard divisional chart, providing a profound look into your deepest ancestral roots and the generational karma you carry. It represents the "Fine Print" of your soul's inheritance. With **${lagnaName} rising in D144**, your foundational ancestral patterns are characterized by ${lagnaKeywords}. This chart reveals the ultimate source-code of your life's outcomes.\n\n`;

        narrative += `**Lineage Ruler (L144 Lord):** The ruler of your ancestral inheritance, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This shows that the primary resolution of your generational karma is focused on **${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}**.\n\n`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        return narrative;
    }

    analyzeHouseLordDynamics(data) {
        let narrative = `### Pillars of Generational Influence and Lineage Matrix\n\n`;
        narrative += `The connections in D144 define how your ancestral patterns manifest in various life domains and where you are called to resolve generational knots.\n\n`;

        const priorityHouses = [1, 4, 9, 10, 2, 5, 11, 7, 3, 6, 8, 12];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);

            narrative += `**${I18n.n(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}\n`;
            
            // Insight Card
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` This area of your life is supported by significant ancestral merit and favorable generational patterns.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` Generational challenges in this area require your conscious effort to break old patterns and establish new ethical foundations.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Ancestral Archetypes and Generational Analysis\n\n`;
        const planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];

        planets.forEach(p => {
            const houseNum = this._getPlanetHouse(data, p);
            if (!houseNum) return;

            const pos = data.vargaChart.planets[p];
            const signName = this.signs[pos.rasi.index];
            const planetName = I18n.t('planets.' + p);

            narrative += `**Placement of ${planetName} in the ${this._formatHouse(houseNum)} (${I18n.t('rasis.' + signName)}):** `;
            narrative += this._getPlanetInHouseDescription(p, houseNum, signName, data);
            narrative += `\n\n`;
        });

        return narrative;
    }

    analyzeAdvancedYogaLogic(data) {
        let narrative = `### Specialized Generational Insights\n\n`;
        
        // Sun (Karaka for Paternal Lineage) & Moon (Karaka for Maternal Lineage)
        const sunHouse = this._getPlanetHouse(data, 'Sun');
        const moonHouse = this._getPlanetHouse(data, 'Moon');
        
        if (sunHouse) {
            narrative += `**Ancestral Power Point:** The Sun is in your ${this._formatHouse(sunHouse)} and the Moon is in your ${this._formatHouse(moonHouse)}. `;
            if ([1, 4, 9, 10].includes(sunHouse) && !data.vargaChart.planets.Sun.isCombust) {
                narrative += `The Sun's strong placement in D144 grants you the ability to positively transform and lead your paternal lineage into a new era of clarity.\n\n`;
            } else {
                narrative += `Your paternal lineage karma involves overcoming hidden challenges and achieving a new level of self-mastery.\n\n`;
            }
        }

        if (moonHouse && [1, 4, 2, 11].includes(moonHouse)) {
            narrative += `The Moon's placement suggests a deep, nurturing connection to your maternal roots and significant emotional support from your ancestors.\n\n`;
        }

        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Trajectory of Generational Resolution\n\n`;

        const l4 = data.houseLords[4];
        const l1 = data.houseLords[1];
        
        narrative += `**Resolution of Ancestral Patterns:**\n`;
        if (this.kendras.includes(l4.placedInHouse) || this.trikonas.includes(l4.placedInHouse)) {
            narrative += `You possess the capacity to resolve long-standing generational knots and establish a harmonious foundation for future lineages.\n\n`;
        } else {
            narrative += `Your resolution of ancestral karma is a private and intense journey. You gain the most by mastering your own internal state and breaking cycles of conditioning.\n\n`;
        }

        narrative += `**Final Generational Legacy:**\n`;
        if (this.kendras.includes(l1.placedInHouse) || this.trikonas.includes(l1.placedInHouse)) {
            narrative += `Your life journey results in a significant positive shift for your entire lineage. Your honorable actions become a new baseline for those who follow.\n\n`;
        } else {
            narrative += `Your legacy is one of deep internal work and spiritual refinement. You provide a template for resolving complex generational riddles through awareness.\n\n`;
        }

        return narrative;
    }

    getPersonalizedAdvice(data) {
        let advice = `**Guidance for Ancestral Harmony:**\n`;
        const l1 = data.houseLords[1];
        
        if (this.dusthanas.includes(l1.placedInHouse)) {
            advice += `• To harmonize your deepest generational currents, focus on honoring your ancestors through charitable acts and the purification of your own life intentions.\n`;
        }
        
        advice += `• Align your generational work with the qualities of ${I18n.t('rasis.' + data.lagna.sign)}, focusing on ${this._getElementalAdvice(this._getElement(data.lagna.sign))}`;

        return advice;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const d144Matrix = {
            1: {
                1: "Ancestral identity is strong and self-consistent. You carry a powerful and clear generational signal in your soul's journey.",
                4: "Your identity is heavily rooted in family foundations and ancestral happiness. You are the protector of the lineage heart.",
                9: "You are the dharmic beacon of your lineage. You carry the supreme blessings of your ancestors and find luck through their merits."
            },
            4: {
                1: "Your personality is the primary focus of ancestral resolution. You find yourself through the healing of generational patterns.",
                4: "Unshakeable family foundations. Your lineage heart is strong and provides a stable base for your entire life journey."
            }
        };

        const result = d144Matrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        const sourceTheme = this._getHouseThemes(house);
        const targetTheme = this._getHouseThemes(pos);
        
        if (house === pos) return `**Insight:** Foundational stability in ${sourceTheme.toLowerCase()}. Your generational roots in this domain are firm and reliable.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** Generational patterns in ${sourceTheme.toLowerCase()} are resolved through acts of release or profound inner transformation.`;
        
        return `**Insight:** Ancestral energy flows from ${sourceTheme.toLowerCase()} toward ${targetTheme.toLowerCase()}, linking your lineage karma across these domains.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const d144PlanetMatrix = {
            Sun: {
                1: "A powerful and honorable ancestral signal. You carry the best qualities of your paternal lineage into your current identity.",
                10: "Your soul's mission involves bringing honor and clarity to your professional and generational standing."
            },
            Moon: {
                4: "Deep emotional resolution of maternal roots. Your soul finds a profound sense of home and generational belonging."
            },
            Jupiter: {
                9: "Supreme ancestral wisdom and divine grace. Your lineage is supported by high dharmic merits and spiritual protection."
            }
        };

        const result = d144PlanetMatrix[planet]?.[house];
        if (result) return result;

        return `${I18n.t('planets.' + planet)} in the ${this._formatHouse(house)} of D144 influences your ${this._getHouseThemes(house).toLowerCase()}, shaping your generational results.`;
    }

    _getHouseThemes(h) {
        return ['', 'Lineage Persona', 'Ancestral Values', 'Generational Drive', 'Lineage Foundations', 'Ancestral Wisdom', 'Ancient Debts', 'Root Unions', 'Deep Transformation', 'Paternal Grace', 'Ancestral Karma', 'Lineage Gains', 'Dissolution'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'active leadership in resolving old family patterns and maintaining a visionary, enthusiastic inner world.',
            Earth: 'building reliable foundations for your lineage and focusing on practical, long-term generational results.',
            Air: 'leveraging strategic intellectual clarity and sharing ancestral wisdom to expand your lineage harmony.',
            Water: 'trusting your deep intuition and bringing emotional empathy and purification to your final generational results.'
        };
        return advice[element] || 'maintaining balance in your generational life.';
    }

    _formatHouse(h) {
        const ordinals = ['', '1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th', '11th', '12th'];
        return `${ordinals[h]} house`;
    }

    _getOrdinal(n) {
        const s = ['th', 'st', 'nd', 'rd'];
        const v = n % 100;
        return s[(v - 20) % 10] || s[v] || s[0];
    }

    analyze(vargaChart, ctx) {
        const { profile, chart: d1Chart } = ctx;
        const birthDate = new Date(profile.datetime);
        const age = new Date().getFullYear() - birthDate.getFullYear();
        const lagnaSignIdx = vargaChart.lagna.rasi.index;

        const data = {
            vargaChart, d1Chart,
            age,
            lagna: {
                signIndex: lagnaSignIdx,
                sign: this.signs[lagnaSignIdx],
                lord: this.rulers[lagnaSignIdx],
                lordHouse: 0 // Set below
            },
            houseLords: this._getHouseLords(vargaChart, lagnaSignIdx),
            dignities: this._getDignities(vargaChart.planets),
            patterns: this._getHousePatterns(vargaChart, lagnaSignIdx)
        };

        data.lagna.lordHouse = this._getPlanetHouse(data, data.lagna.lord);

        let report = '';
        report += this.analyzeCoreSignificance(data);
        report += this.analyzeHouseLordDynamics(data);
        report += this.analyzePlanetaryInfluences(data);
        report += this.analyzeAdvancedYogaLogic(data);
        report += this.generatePredictions(data);

        const advice = this.getPersonalizedAdvice(data);
        if (advice) report += `\n\n### Personalized Recommendations\n${advice}`;

        return {
            key: 'D144',
            name: VARGA_INFO['D144'].name,
            desc: VARGA_INFO['D144'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}
export default new D144Analyzer();
