import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

class D12Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D12', 'Sun');
    }

    analyzeCoreSignificance(data) {
        const lagnaName = I18n.t('rasis.' + data.lagna.sign);
        const lordName = I18n.t('planets.' + data.lagna.lord);
        const lagnaKeywords = I18n.t('analysis.keywords.' + data.lagna.sign);

        let narrative = `### Parents, Lineage, and Ancestral Karma\n\n`;
        narrative += `The Dwadashamsha (D12) chart represents your relationship with your parents and the overall karma you've inherited from your lineage. With **${lagnaName} rising in D12**, your ancestral foundations and parental bonds are characterized by ${lagnaKeywords}. This chart determines the \"Support\" you receive from your roots.\n\n`;

        narrative += `**Lineage Ruler (L12 Lord):** The ruler of your ancestral identity, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This shows that the influence of your parents and lineage is primarily channeled through **${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}**.\n\n`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        return narrative;
    }

    analyzeHouseLordDynamics(data) {
        let narrative = `### Parental Pillars and Ancestral Matrix\n\n`;
        narrative += `The connections in D12 define the quality of support from your parents and the strength of your inherited legacy.\n\n`;

        const priorityHouses = [9, 4, 1, 10, 2, 5, 11, 7, 8, 12, 6, 3];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);

            narrative += `**${I18n.n(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}\n`;
            
            // Insight Card
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` The exaltation of this lord indicates high-vibrational ancestral support and natural grace in this area of lineage.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` Debilitation here suggests that this ancestral area requires conscious healing and transformation.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Ancestral Influence Analysis\n\n`;
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
        let narrative = `### Specialized Lineage Insights\n\n`;
        
        // Sun (Karaka for Father) & Moon (Karaka for Mother)
        const sunHouse = this._getPlanetHouse(data, 'Sun');
        const moonHouse = this._getPlanetHouse(data, 'Moon');
        
        if (sunHouse) {
            narrative += `**Parental Influence:** The Sun (Father) is in your ${this._formatHouse(sunHouse)} and the Moon (Mother) is in your ${this._formatHouse(moonHouse)}. `;
            if ([1, 4, 7, 10, 5, 9].includes(sunHouse)) {
                narrative += `The paternal influence in your life is strong and supportive, providing a foundation for your status.\n\n`;
            } else {
                narrative += `Paternal karma involves resolving complexities and overcoming hurdles.\n\n`;
            }
        }

        if (moonHouse && [1, 4, 7, 10, 5, 9].includes(moonHouse)) {
            narrative += `The maternal influence is deeply nurturing, providing you with significant emotional resilience.\n\n`;
        } else if (moonHouse) {
            narrative += `Maternal karma involves lessons in emotional independence and inner strength.\n\n`;
        }

        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Parental and Lineage Trajectory Predictions\n\n`;

        const l9 = data.houseLords[9];
        const l4 = data.houseLords[4];
        
        narrative += `**Support from Father and Lineage:**\n`;
        if (this.kendras.includes(l9.placedInHouse) || this.trikonas.includes(l9.placedInHouse)) {
            narrative += `You receive strong dharmic support from your father and paternal line, aiding your overall fortune.\n\n`;
        } else {
            narrative += `Your paternal support is built through shared duties and overcoming industry or life challenges together.\n\n`;
        }

        narrative += `**Support from Mother and Emotional Roots:**\n`;
        if (this.kendras.includes(l4.placedInHouse) || this.trikonas.includes(l4.placedInHouse)) {
            narrative += `Your maternal roots provide a sanctuary of emotional peace and unshakeable domestic support.\n\n`;
        } else {
            narrative += `Your relationship with your maternal roots requires conscious effort to find peace and emotional security.\n\n`;
        }

        return narrative;
    }

    getPersonalizedAdvice(data) {
        let advice = `**Actionable Guidance for Roots:**\n`;
        const l9 = data.houseLords[9];
        const l4 = data.houseLords[4];
        
        if (this.dusthanas.includes(l9.placedInHouse) || this.dusthanas.includes(l4.placedInHouse)) {
            advice += `• Perform ancestral rites or engage in family healing practices to resolve inherited karmic patterns.\n`;
        }
        
        advice += `• Your ancestral support is best accessed by aligning your life with the qualities of ${I18n.t('rasis.' + data.lagna.sign)}, focusing on ${this._getElementalAdvice(this._getElement(data.lagna.sign))}`;

        return advice;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const d12Matrix = {
            1: {
                1: "Your identity is a powerful reflection of your lineage. You carry your ancestral pride with dignity.",
                9: "Strong dharmic link to the father. Your soul's purpose is guided by ancestral wisdom and ethical foundations.",
                4: "Maternal influence defines your personality. Your sense of peace is rooted in your family traditions."
            },
            9: {
                1: "Your father significantly shapes your identity. You are likely to carry on his ethical or spiritual legacy.",
                9: "Unshakeable paternal fortune. Your father or paternal line provides great luck and dharmic protection."
            },
            4: {
                1: "Your mother significantly shapes your identity. You derive your internal strength from her nurturing presence.",
                4: "Excellent maternal happiness. Your mother or maternal line provides deep-seated emotional security."
            }
        };

        const result = d12Matrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        const sourceTheme = this._getHouseThemes(house);
        const targetTheme = this._getHouseThemes(pos);
        
        if (house === pos) return `**Insight:** Stability in ${sourceTheme.toLowerCase()}. Your ancestral support in this area is well-protected and reliable.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** Support from ${sourceTheme.toLowerCase()} requires healing inherited patterns or overcoming family hurdles.`;
        
        return `**Insight:** Your ancestral energy flows from ${sourceTheme.toLowerCase()} toward ${targetTheme.toLowerCase()}, linking your roots with these life areas.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const d12PlanetMatrix = {
            Sun: {
                9: "A powerful, dharmic father. You inherit authority, ethics, and strong leadership traits from your paternal line.",
                10: "Paternal support directly aids your career status and public recognition."
            },
            Moon: {
                4: "A deeply nurturing mother. You inherit emotional intelligence and the capacity for inner peace from your maternal line.",
                1: "Maternal influence is central to your personality and sense of emotional security."
            }
        };

        const result = d12PlanetMatrix[planet]?.[house];
        if (result) return result;

        return `${I18n.t('planets.' + planet)} in the ${this._formatHouse(house)} of D12 influences your ${this._getHouseThemes(house).toLowerCase()}, shaping your parental karma.`;
    }

    _getHouseThemes(h) {
        return ['', 'Lineage Persona', 'Values/Assets', 'Effort/Drive', 'Mother/Home', 'Creative Legacy', 'Service/Health', 'Partnerships', 'Transformation', 'Father/Fortune', 'Status/Action', 'Gains/Networks', 'Inner Release'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'active leadership in family matters and maintaining an optimistic, pioneering outlook on your lineage.',
            Earth: 'building reliable foundations for your family and focusing on tangible long-term ancestral security.',
            Air: 'leveraging communication, networking, and shared information to strengthen family ties and ancestral reach.',
            Water: 'trusting your intuition and bringing empathy and emotional depth to your parental relationships and family roots.'
        };
        return advice[element] || 'maintaining balance in your roots.';
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
            dignities: this._getDignities(vargaChart.planets)
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
            key: 'D12',
            name: VARGA_INFO['D12'].name,
            desc: VARGA_INFO['D12'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}

export default new D12Analyzer();