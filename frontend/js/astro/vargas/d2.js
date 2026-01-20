import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

class D2Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D2', 'Jupiter');
    }

    analyzeCoreSignificance(data) {
        const lagnaIdx = data.lagna.signIndex;
        const isSolar = lagnaIdx === 4; // Leo
        const isLunar = lagnaIdx === 3; // Cancer
        
        let narrative = `### Wealth Signature and Financial Temperament\n\n`;
        
        if (isSolar) {
            narrative += `Your Hora chart rises with a **Solar (Leo) influence**. This indicates a "Producer" temperament. You are someone who gains wealth through active leadership, administration, and by being in the limelight. Your financial growth is tied to your ability to take charge and manage resources with authority.\n\n`;
        } else if (isLunar) {
            narrative += `Your Hora chart is governed by a **Lunar (Cancer) influence**. This suggests a "Preserver" temperament. You tend to accumulate wealth through nurturing, service, and by managing the emotional or human aspect of resources. Your wealth grows through stability, family ties, and a more cautious, rhythmic approach to finance.\n\n`;
        } else {
            const lagnaName = I18n.t('rasis.' + data.lagna.sign);
            narrative += `Your Hora chart rises with **${lagnaName}**, blending the qualities of ${I18n.t('analysis.keywords.' + data.lagna.sign)} into your financial personality.\n\n`;
        }

        const lordName = I18n.t('planets.' + data.lagna.lord);
        narrative += `**Financial Ruler (L2 Lord):** The ruler of your wealth identity, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This shows that your core earning power is focused on **${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}**.\n\n`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        return narrative;
    }

    analyzeHouseLordDynamics(data) {
        let narrative = `### Financial Pillars and Resource Matrix\n\n`;
        narrative += `The connections in D2 define the flow and stability of your accumulated resources.\n\n`;

        const priorityHouses = [2, 1, 11, 5, 9, 8, 4, 10, 7, 6, 12, 3];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);

            narrative += `**${I18n.n(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}\n`;
            
            // Insight Card
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` The exaltation of this lord indicates high-quality resources and natural financial grace in this area.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` Debilitation here suggests that financial discipline and careful management are required to protect this area.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Resource Management and Assets Analysis\n\n`;
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
        let narrative = `### Specialized Prosperity Insights\n\n`;
        
        // Jupiter (Karaka for Wealth)
        const jupHouse = this._getPlanetHouse(data, 'Jupiter');
        if (!jupHouse) return narrative;
        
        narrative += `**Jupiter's Abundance Influence:** Jupiter is in your ${this._formatHouse(jupHouse)}. `;
        if ([1, 2, 4, 5, 9, 11].includes(jupHouse)) {
            narrative += `This is a highly supportive signature, indicating that your resources grow through wisdom, ethical conduct, and natural grace.\n\n`;
        } else {
            narrative += `This indicates that wealth is built through service, attention to detail, and overcoming initial resource constraints.\n\n`;
        }

        const l2 = data.houseLords[2];
        if (l2.dignity === 'Exalted' || l2.dignity === 'Own Sign') {
            narrative += `**Strong Accumulation Potential:** The strength of your 2nd lord in D2 suggests a powerful capacity to protect and multiply your family assets.\n\n`;
        }

        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Financial Trajectory Predictions\n\n`;

        const l11 = data.houseLords[11];
        const l2 = data.houseLords[2];
        
        narrative += `**Income Generation Power:**\n`;
        if (this.kendras.includes(l11.placedInHouse) || this.trikonas.includes(l11.placedInHouse)) {
            narrative += `You have a strong capacity to attract multiple income streams and liquid gains through your professional networks.\n\n`;
        } else {
            narrative += `Your income is steady and grows through your reputation for reliability and specialized expertise.\n\n`;
        }

        narrative += `**Asset Protection and Savings:**\n`;
        if (l2.placedInHouse === 11 || l11.placedInHouse === 2 || l2.placedInHouse === 9) {
            narrative += `You possess a powerful "Wealth Multiplier" effect, where your gains naturally translate into long-term family assets.\n\n`;
        } else {
            narrative += `Your wealth accumulation is a rhythmic process requiring consistent saving and ethical resource management.\n\n`;
        }

        return narrative;
    }

    getPersonalizedAdvice(data) {
        let advice = `**Financial Guidance:**\n`;
        const l2 = data.houseLords[2];
        
        if (this.dusthanas.includes(l2.placedInHouse)) {
            advice += `• Focus on debt management and disciplined budgeting. Your greatest financial strength comes from overcoming obstacles.\n`;
        }
        
        advice += `• Wealth accumulation is best achieved by channeling the energy of ${I18n.t('rasis.' + data.lagna.sign)}, focusing on ${this._getElementalAdvice(this._getElement(data.lagna.sign))}`;

        return advice;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const d2Matrix = {
            1: {
                1: "Your wealth is a direct reflection of your character. You are the sole architect of your financial destiny.",
                2: "Family values and traditions are the primary source of your financial stability and accumulation.",
                11: "Natural magnetism for gains. Your personality attracts profitable social and professional connections."
            },
            2: {
                2: "Strong family assets. You are destined to protect and grow a significant inheritance or family resource.",
                11: "Gains grow exponentially into long-term savings. Every profit is wisely reinvested into assets."
            },
            11: {
                1: "Magnetic earning capacity. Your very presence in professional circles generates financial opportunities.",
                11: "Multiple streams of income. You have an exceptional ability to capitalize on diverse opportunities."
            }
        };

        const result = d2Matrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        const sourceTheme = this._getHouseThemes(house);
        const targetTheme = this._getHouseThemes(pos);
        
        if (house === pos) return `**Insight:** Stability in ${sourceTheme.toLowerCase()}. Your financial foundations in this area are unshakeable.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** Wealth from ${sourceTheme.toLowerCase()} involves overcoming debts or navigating complex resource management.`;
        
        return `**Insight:** Financial energy flows from ${sourceTheme.toLowerCase()} toward ${targetTheme.toLowerCase()}, linking your assets with these life areas.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const d2PlanetMatrix = {
            Jupiter: {
                2: "Exceptional financial wisdom and family prosperity. You are blessed with an abundance of resources.",
                11: "Greatest capacity for gains. Your network brings you significant financial opportunities."
            },
            Venus: {
                2: "Wealth through artistic pursuits, luxury, or family harmony. Comfortable assets.",
                11: "Gains through partnerships, aesthetic fields, and social popularity."
            }
        };

        const result = d2PlanetMatrix[planet]?.[house];
        if (result) return result;

        return `${I18n.t('planets.' + planet)} in the ${this._formatHouse(house)} of D2 influences your ${this._getHouseThemes(house).toLowerCase()}, shaping your financial style.`;
    }

    _getHouseThemes(h) {
        return ['', 'Wealth Persona', 'Savings/Assets', 'Effort/Drive', 'Fixed Assets', 'Speculative Gains', 'Debts/Service', 'Partnerships', 'Hidden Resources', 'Grace/Fortune', 'Status/Action', 'Liquid Gains', 'Expenditure'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'active leadership and bold financial initiatives that create new resource streams.',
            Earth: 'steady accumulation, focusing on tangible assets like property and long-term security.',
            Air: 'leveraging networking, information, and strategic partnerships for financial growth.',
            Water: 'trusting your intuition and managing resources with empathy and emotional intelligence.'
        };
        return advice[element] || 'maintaining financial balance.';
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
            key: 'D2',
            name: VARGA_INFO['D2'].name,
            desc: VARGA_INFO['D2'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}

export default new D2Analyzer();