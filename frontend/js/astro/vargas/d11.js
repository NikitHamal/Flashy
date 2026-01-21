import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

/**
 * D11: RUDRAMSHA - THE CHART OF PROFITS AND EXTRAORDINARY GAINS
 */
class D11Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D11', 'Jupiter');
    }

    analyzeCoreSignificance(data) {
        const lagnaName = I18n.t('rasis.' + data.lagna.sign);
        const lordName = I18n.t('planets.' + data.lagna.lord);
        const lagnaKeywords = I18n.t('analysis.keywords.' + data.lagna.sign);

        let narrative = `### Extraordinary Gains and Profitability\n\n`;
        narrative += `The Rudramsha (D11) chart defines your capacity to attract high-level gains, your relationship with elder siblings, and your ultimate success in social or financial "markets." With **${lagnaName} rising in D11**, your style of accumulation and your "Prosperity Multiplier" are characterized by ${lagnaKeywords}. This chart determines the \"Abundance\" you can command.\n\n`;

        narrative += `**Gains Ruler (L11 Lord):** The ruler of your extraordinary gains, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This shows that the primary channel for your most significant material and social profits is focused on **${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}**.\n\n`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        return narrative;
    }

    analyzeHouseLordDynamics(data) {
        let narrative = `### Pillars of Abundance and Social Matrix\n\n`;
        narrative += `The connections in D11 define how your professional status and social networks translate into tangible gains and the fulfillment of your highest desires.\n\n`;

        const priorityHouses = [11, 1, 10, 2, 5, 9, 4, 7, 3, 6, 8, 12];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);

            narrative += `**${I18n.n(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}\n`;
            
            // Insight Card
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` The exaltation of this lord indicates exceptional profitability and natural ease in fulfilling your material goals.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` Fulfilling desires in this area requires consistent effort and the removal of specific social or financial obstacles.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Profit Style and Social Impact Analysis\n\n`;
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
        
        // Jupiter (Karaka for Gains) & Venus (Karaka for Luxuries/Wealth)
        const jupHouse = this._getPlanetHouse(data, 'Jupiter');
        const venHouse = this._getPlanetHouse(data, 'Venus');
        
        if (jupHouse) {
            narrative += `**Prosperity Focus Point:** Jupiter is in your ${this._formatHouse(jupHouse)} and Venus is in your ${this._formatHouse(venHouse)}. `;
            if ([1, 2, 5, 9, 11].includes(jupHouse) && !data.vargaChart.planets.Jupiter.isCombust) {
                narrative += `Jupiter's strong placement in D11 acts as a "Gains Magnifier," indicating that your wealth grows through wisdom, ethical social ties, and divine grace.\n\n`;
            } else {
                narrative += `Your extraordinary gains are built through specialized knowledge, service, and overcoming resource constraints.\n\n`;
            }
        }

        if (venHouse && [1, 4, 7, 10, 11].includes(venHouse)) {
            narrative += `Venus's influence grants you the capacity to enjoy the highest level of material comforts and gains through social popularity.\n\n`;
        }

        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Trajectory of Extraordinary Gains and Fulfillment\n\n`;

        const l11 = data.houseLords[11];
        const l1 = data.houseLords[1];
        
        narrative += `**Ability to Fulfill Highest Desires:**\n`;
        if (l11.dignity === 'Exalted' || l11.dignity === 'Own Sign' || this.kendras.includes(l11.placedInHouse)) {
            narrative += `You possess a powerful internal magnet for major material and social achievements. Your highest desires tend to find favorable realization through your networks.\n\n`;
        } else {
            narrative += `The fulfillment of your desires is a gradual, self-directed journey. You gain most by focusing on long-term sustainability and ethical social impact.\n\n`;
        }

        narrative += `**Relationship with Mentors and Elder Siblings:**\n`;
        if (this.kendras.includes(l1.placedInHouse) || this.trikonas.includes(l1.placedInHouse)) {
            narrative += `You find significant support and profit through your relationships with authority figures, mentors, and older peers. Your path is cleared by these connections.\n\n`;
        } else {
            narrative += `Your social gains grow through specialized expertise and your reputation for reliability within your professional community.\n\n`;
        }

        return narrative;
    }

    getPersonalizedAdvice(data) {
        let advice = `**Actionable Guidance for Abundance:**\n`;
        const l1 = data.houseLords[1];
        
        if (this.dusthanas.includes(l1.placedInHouse)) {
            advice += `• To stabilize your gains, focus on regular philanthropic acts and the support of those less fortunate. In D11, wealth flows most freely to those who are a conduit for the collective good.\n`;
        }
        
        advice += `• Your prosperity is best activated by aligning your actions with the qualities of ${I18n.t('rasis.' + data.lagna.sign)}, focusing on ${this._getElementalAdvice(this._getElement(data.lagna.sign))}`;

        return advice;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const d11Matrix = {
            1: {
                1: "Gains are self-actualized. You possess a natural profitability identity and a soul that inherently knows how to command abundance.",
                11: "Natural magnet for high-level gains. Your very presence in social and professional circles attracts major opportunities.",
                10: "Gains through professional action. Your status and reputation are the primary engines for your financial and social success."
            },
            11: {
                1: "Your personality is heavily supported by social and financial profits. You find your deepest self through the fulfillment of your aspirations.",
                11: "Supreme stability in gains. Your capacity to attract extraordinary abundance is unshakeable and self-sustaining."
            }
        };

        const result = d11Matrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        const sourceTheme = this._getHouseThemes(house);
        const targetTheme = this._getHouseThemes(pos);
        
        if (house === pos) return `**Insight:** Stability in ${sourceTheme.toLowerCase()}. Your foundations for abundance in this area are firm and reliable.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** Gains regarding ${sourceTheme.toLowerCase()} involve overcoming specific tests or through acts of selfless social service.`;
        
        return `**Insight:** Energy for abundance flows from ${sourceTheme.toLowerCase()} toward ${targetTheme.toLowerCase()}, linking your gains across these domains.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const d11PlanetMatrix = {
            Jupiter: {
                11: "Supreme capacity for gains and wisdom. Your social network is your greatest asset and brings you immense profit.",
                1: "A naturally fortunate and profitable soul. You find luck and abundance through ethical conduct and mentorship."
            },
            Venus: {
                11: "Extraordinary gains through aesthetic fields, luxury, and social popularity. Your desires for comfort are easily fulfilled.",
                2: "Abundant material resources and high-level savings. Your lineage wealth is a major source of prosperity."
            },
            Sun: {
                10: "Gains through high-level administrative status and professional recognition. You command respect and abundance in your field."
            }
        };

        const result = d11PlanetMatrix[planet]?.[house];
        if (result) return result;

        return `${I18n.t('planets.' + planet)} in the ${this._formatHouse(house)} of D11 influences your ${this._getHouseThemes(house).toLowerCase()}, shaping your style of accumulation.`;
    }

    _getHouseThemes(h) {
        return ['', 'Abundance Persona', 'Massive Savings', 'Scaling Drive', 'Asset Profits', 'Speculative Gains', 'Profitable Service', 'Partnership Gains', 'Sudden Gain Shifts', 'Fortunate Multipliers', 'Status from Profits', 'Supreme Gains', 'Philanthropy'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'active leadership in scaling your ventures and maintaining a visionary, enthusiastic outlook on abundance.',
            Earth: 'building reliable foundations for your wealth and focusing on practical, long-term financial results.',
            Air: 'leveraging strategic communication, networking, and the sharing of wisdom to expand your field of gains.',
            Water: 'trusting your intuition and bringing emotional empathy and ethical purification to your pursuit of abundance.'
        };
        return advice[element] || 'maintaining balance in your prosperity.';
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
            key: 'D11',
            name: VARGA_INFO['D11'].name,
            desc: VARGA_INFO['D11'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}
export default new D11Analyzer();
