import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

class D7Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D7', 'Jupiter');
    }

    analyzeCoreSignificance(data) {
        const lagnaName = I18n.t('rasis.' + data.lagna.sign);
        const lordName = I18n.t('planets.' + data.lagna.lord);
        const lagnaKeywords = I18n.t('analysis.keywords.' + data.lagna.sign);

        let narrative = `### Children, Creativity, and Progeny\n\n`;
        narrative += `The Saptamsha (D7) chart represents your destiny regarding children (progeny), creativity, and the continuation of your lineage. With **${lagnaName} rising in D7**, your relationship with your children and your creative output is characterized by ${lagnaKeywords}. This chart determines the "Joy" you derive from future generations.\n\n`;

        narrative += `**Progeny Ruler (L7 Lord):** The ruler of your creative legacy, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This indicates that the fulfillment you find through children or creative projects is primarily centered on **${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}**.\n\n`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        return narrative;
    }

    analyzeHouseLordDynamics(data) {
        let narrative = `### Pillars of Legacy and Creative Output\n\n`;
        narrative += `The connections in D7 define the quality of your relationships with children and the success of your creative ventures.\n\n`;

        const priorityHouses = [5, 1, 9, 2, 7, 10, 11, 4, 8, 12, 6, 3];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);

            narrative += `**${I18n.n(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}\n`;
            
            // Insight Card
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` The exaltation of this lord indicates high-vibrational results and exceptional joy in this area of legacy.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` Debilitation here suggests that this area of legacy requires conscious nurturing and patience.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Progeny and Creative Fulfillment Analysis\n\n`;
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
        let narrative = `### Specialized Legacy Insights\n\n`;
        
        // Jupiter (Karaka for Children)
        const jupHouse = this._getPlanetHouse(data, 'Jupiter');
        if (!jupHouse) return narrative;

        narrative += `**Jupiter's Progeny Influence:** Jupiter is in your ${this._formatHouse(jupHouse)}. `;
        if ([1, 4, 5, 7, 9, 10, 11].includes(jupHouse) && !data.vargaChart.planets.Jupiter.isCombust) {
            narrative += `This is a highly favorable signature for D7, indicating wisdom, ethics, and great joy through children and creative pursuits.\n\n`;
        } else {
            narrative += `This suggests that your relationship with progeny or creativity is focused on service and overcoming hurdles.\n\n`;
        }

        const l5 = data.houseLords[5];
        if (l5.dignity === 'Exalted' || l5.dignity === 'Own Sign') {
            narrative += `**Strong Lineage Potential:** A powerful 5th lord in D7 is an excellent indicator of successful and dutiful children.\n\n`;
        }

        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Progeny and Creative Trajectory Predictions\n\n`;

        const l5 = data.houseLords[5];
        const l9 = data.houseLords[9];
        
        narrative += `**Happiness from Children:**\n`;
        if (this.kendras.includes(l5.placedInHouse) || this.trikonas.includes(l5.placedInHouse)) {
            narrative += `You are likely to experience significant emotional and spiritual fulfillment through your children. Your legacy is well-supported.\n\n`;
        } else {
            narrative += `Your relationship with your children requires conscious effort and patience. Focus on building a deep, duty-bound connection.\n\n`;
        }

        narrative += `**Creative Output and Recognition:**\n`;
        if (this.kendras.includes(l9.placedInHouse) || this.trikonas.includes(l9.placedInHouse)) {
            narrative += `Your creative ventures are destined for success and likely bring you significant recognition and joy.\n\n`;
        } else {
            narrative += `Your creative fulfillment comes through specialized, focused efforts. You find joy in the process of creation itself.\n\n`;
        }

        return narrative;
    }

    getPersonalizedAdvice(data) {
        let advice = `**Actionable Guidance for Legacy:**\n`;
        const l5 = data.houseLords[5];
        
        if (this.dusthanas.includes(l5.placedInHouse)) {
            advice += `• Strengthen your relationship with children or your creative muse through selfless service and consistent nurturing.\n`;
        }
        
        advice += `• Your creative legacy is best cultivated by aligning your actions with the qualities of ${I18n.t('rasis.' + data.lagna.sign)}, focusing on ${this._getElementalAdvice(this._getElement(data.lagna.sign))}`;

        return advice;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const d7Matrix = {
            1: {
                1: "Legacy is self-actualized. You possess a clear sense of your creative purpose and your role in continuing your lineage.",
                5: "Intelligence and children are the core pillars of your identity. You are a natural mentor.",
                9: "You are exceptionally lucky regarding legacy. Your children or creative projects are supported by natural grace."
            },
            5: {
                1: "Your identity is deeply tied to your children's success and your own creative ventures. You are a natural mentor.",
                5: "Strong lineage strength. You have an unshakeable connection with your progeny and creative outputs.",
                11: "Creative projects and children lead to significant gains and social recognition. Your legacy is prosperous."
            }
        };

        const result = d7Matrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        const sourceTheme = this._getHouseThemes(house);
        const targetTheme = this._getHouseThemes(pos);
        
        if (house === pos) return `**Insight:** Stability in ${sourceTheme.toLowerCase()}. Your legacy in this area is well-protected and reliable.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** Joy regarding ${sourceTheme.toLowerCase()} requires internal growth or overcoming hurdles before it manifests fully.`;
        
        return `**Insight:** Your life's joy regarding legacy flows from ${sourceTheme.toLowerCase()} toward ${targetTheme.toLowerCase()}, linking your progeny with these domains.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const d7PlanetMatrix = {
            Jupiter: {
                5: "Abundant joy and wisdom through children. Your progeny are destined for ethical success and bring you great respect.",
                1: "You possess a natural internal sense of wisdom and grace regarding your creative legacy."
            },
            Venus: {
                5: "Creativity through beauty and harmony. Your children may be artistically inclined or bring aesthetic joy to your life.",
                11: "Gains through creative projects and a supportive network that recognizes your legacy."
            },
            Sun: {
                5: "Leadership and authority in your children. They may hold prominent positions or carry your lineage with great dignity."
            }
        };

        const result = d7PlanetMatrix[planet]?.[house];
        if (result) return result;

        return `${I18n.t('planets.' + planet)} in the ${this._formatHouse(house)} of D7 influences your ${this._getHouseThemes(house).toLowerCase()}, shaping your relationship with progeny.`;
    }

    _getHouseThemes(h) {
        return ['', 'Legacy Persona', 'Values/Assets', 'Effort/Drive', 'Domestic Peace', 'Children/Creativity', 'Service/Health', 'Partnerships', 'Transformation', 'General Fortune', 'Status/Action', 'Creative Gains', 'Inner Release'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'taking bold, pioneering initiatives in your creative life and maintaining a visionary outlook for your progeny.',
            Earth: 'building reliable foundations for your children and focusing on tangible long-term creative assets.',
            Air: 'leveraging communication, strategic information, and networking to expand your creative reach and lineage support.',
            Water: 'trusting your intuition and bringing empathy and emotional depth to your relationship with children and creative muse.'
        };
        return advice[element] || 'maintaining balance in your legacy.';
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
            key: 'D7',
            name: VARGA_INFO['D7'].name,
            desc: VARGA_INFO['D7'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}

export default new D7Analyzer();
