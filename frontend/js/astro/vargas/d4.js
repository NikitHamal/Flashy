import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

class D4Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D4', 'Mercury');
    }

    analyzeCoreSignificance(data) {
        const lagnaName = I18n.t('rasis.' + data.lagna.sign);
        const lordName = I18n.t('planets.' + data.lagna.lord);
        const lagnaKeywords = I18n.t('analysis.keywords.' + data.lagna.sign);

        let narrative = `### Fortune, Fixed Assets, and Inner Peace\n\n`;
        narrative += `The Chaturthansha (D4) chart represents your overall fortune (Bhagya) and your destiny regarding fixed assets like property and vehicles. With **${lagnaName} rising in D4**, your relationship with material security and emotional peace is characterized by ${lagnaKeywords}. This chart determines the \"Stability\" of your life.\n\n`;

        narrative += `**Fortune Ruler (L4 Lord):** The ruler of your stability, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This indicates that your life's fortune and material security are primarily found through **${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}**.\n\n`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        return narrative;
    }

    analyzeHouseLordDynamics(data) {
        let narrative = `### Material Pillars and Asset Matrix\n\n`;
        narrative += `The connections in D4 define the quality of your home life, your capacity to own property, and your overall sense of security.\n\n`;

        const priorityHouses = [4, 1, 9, 2, 5, 10, 11, 7, 8, 12, 6, 3];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);

            narrative += `**${I18n.n(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}\n`;
            
            // Insight Card
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` This area of fortune is exceptionally fortified, promising high-quality assets and deep inner peace.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` Challenges in this area suggest that your sense of security may be subject to periodic internal or material tests.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Happiness and Prosperity Analysis\n\n`;
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
        let narrative = `### Specialized Fortune Insights\n\n`;
        
        // Venus (Karaka for Vehicles and Comfort)
        const venHouse = this._getPlanetHouse(data, 'Venus');
        if (!venHouse) return narrative;
        
        narrative += `**Venus's Comfort Influence:** Venus is in your ${this._formatHouse(venHouse)}. `;
        if ([1, 4, 7, 10, 5, 9, 11].includes(venHouse)) {
            narrative += `This is a highly supportive placement for D4, indicating that luxury vehicles, aesthetic home environments, and overall life comfort will be readily available to you.\n\n`;
        } else {
            narrative += `This indicates that your sense of luxury is tied more to internal peace or foreign connections rather than just material assets.\n\n`;
        }

        const l4 = data.houseLords[4];
        if (l4.dignity === 'Exalted' || l4.dignity === 'Own Sign') {
            narrative += `**Strong Asset Potential:** A powerful 4th lord in D4 is an excellent signature for owning multiple properties and enjoying deep-seated emotional security.\n\n`;
        }

        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Fortune and Asset Trajectory Predictions\n\n`;

        const l9 = data.houseLords[9];
        const l4 = data.houseLords[4];
        
        narrative += `**Overall Life Fortune:**\n`;
        if (this.kendras.includes(l9.placedInHouse) || this.trikonas.includes(l9.placedInHouse)) {
            narrative += `Your overall life destiny is supported by consistent good fortune. Things tend to fall into place for you when you align your actions with your ethical core.\n\n`;
        } else {
            narrative += `Your fortune is built through your own persistent efforts and attention to the small details of life's foundation.\n\n`;
        }

        narrative += `**Property and Domestic Happiness:**\n`;
        if (this.kendras.includes(l4.placedInHouse) || this.trikonas.includes(l4.placedInHouse)) {
            narrative += `You are likely to experience great joy through your domestic life and will successfully acquire fixed assets that provide a sense of legacy.\n\n`;
        } else {
            narrative += `Your domestic peace requires conscious effort to maintain. Focus on building a stable inner world to support your external material security.\n\n`;
        }

        return narrative;
    }

    getPersonalizedAdvice(data) {
        let advice = `**Actionable Guidance for Prosperity:**\n`;
        const l4 = data.houseLords[4];
        
        if (this.dusthanas.includes(l4.placedInHouse)) {
            advice += `• To stabilize your fortune, focus on spiritual practices that build internal peace. Material assets will follow as your inner world becomes more grounded.\n`;
        }
        
        advice += `• Your fortune is best activated by aligning your environment with the qualities of ${I18n.t('rasis.' + data.lagna.sign)}, focusing on ${this._getElementalAdvice(this._getElement(data.lagna.sign))}`;

        return advice;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const d4Matrix = {
            1: {
                1: "Your fortune is self-generated. You have a powerful internal compass that leads you toward stability and material success.",
                4: "Happiness and property are the defining pillars of your life. Your soul finds its greatest peace in a stable home.",
                9: "You are exceptionally lucky. Divine grace and ethical foundations support all your material and emotional goals."
            },
            4: {
                1: "Your personality is deeply tied to your domestic happiness. You are a natural provider of security for yourself and your family.",
                4: "Unshakeable domestic peace. You possess an innate mastery over property and the creation of a sanctuary.",
                11: "Property and fixed assets lead to significant financial gains. Your home is a source of prosperity."
            }
        };

        const result = d4Matrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        const sourceTheme = this._getHouseThemes(house);
        const targetTheme = this._getHouseThemes(pos);
        
        if (house === pos) return `**Insight:** Stability in ${sourceTheme.toLowerCase()}. Your fortune in this area is well-protected and reliable.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** Fortune regarding ${sourceTheme.toLowerCase()} requires internal work or overcoming hurdles before it manifests fully.`;
        
        return `**Insight:** Your life's fortune flows from ${sourceTheme.toLowerCase()} toward ${targetTheme.toLowerCase()}, linking your security with these life domains.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const d4PlanetMatrix = {
            Venus: {
                4: "Excellent for domestic luxury and vehicles. You surround yourself with beauty and comfort.",
                1: "You have a natural internal sense of grace and aesthetic happiness that influences all your fortunes."
            },
            Jupiter: {
                4: "Abundant domestic happiness and property. Your home is a place of wisdom, learning, and blessing.",
                9: "High spiritual merit and protected material fortune. You are naturally lucky in life's major milestones."
            },
            Mercury: {
                4: "Intelligent management of assets. You find peace through learning and communication in your domestic life."
            }
        };

        const result = d4PlanetMatrix[planet]?.[house];
        if (result) return result;

        return `${I18n.t('planets.' + planet)} in the ${this._formatHouse(house)} of D4 influences your ${this._getHouseThemes(house).toLowerCase()}, defining your sense of fortune.`;
    }

    _getHouseThemes(h) {
        return ['', 'Fortune Persona', 'Financial Assets', 'Drive/Effort', 'Property/Home', 'Creative Peace', 'Health/Service', 'Partnerships', 'Transformation', 'General Fortune', 'Status/Action', 'Material Gains', 'Inner Peace'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'active leadership in securing your fortune and maintaining a visionary, optimistic outlook.',
            Earth: 'building reliable foundations for your material life and focusing on tangible long-term assets.',
            Air: 'leveraging communication, strategic information, and networking to stabilize your life destiny.',
            Water: 'trusting your intuition and bringing empathy and emotional depth to your home and inner peace.'
        };
        return advice[element] || 'maintaining balance in your fortune.';
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
            key: 'D4',
            name: VARGA_INFO['D4'].name,
            desc: VARGA_INFO['D4'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}

export default new D4Analyzer();
