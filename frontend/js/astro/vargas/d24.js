import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

class D24Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D24', 'Mercury');
    }

    analyzeCoreSignificance(data) {
        const lagnaName = I18n.t('rasis.' + data.lagna.sign);
        const lordName = I18n.t('planets.' + data.lagna.lord);
        const lagnaKeywords = I18n.t('analysis.keywords.' + data.lagna.sign);

        let narrative = `### Learning, Knowledge, and Education\n\n`;
        narrative += `The Chaturvimshamsha (D24) chart represents your capacity for learning, your intellectual depth, and your destiny regarding formal and informal education. With **${lagnaName} rising in D24**, your relationship with knowledge and wisdom is characterized by ${lagnaKeywords}. This chart determines the \"Intellectual Reach\" of your mind.\n\n`;

        narrative += `**Knowledge Ruler (L24 Lord):** The ruler of your intellectual identity, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This shows that your mastery over subjects and acquisition of wisdom are primarily channeled through **${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}**.\n\n`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        return narrative;
    }

    analyzeHouseLordDynamics(data) {
        let narrative = `### Pillars of Learning and Intellectual Matrix\n\n`;
        narrative += `The connections in D24 define the quality of your educational experiences and the ease with which you absorb complex information.\n\n`;

        const priorityHouses = [5, 9, 1, 4, 2, 10, 11, 7, 8, 12, 6, 3];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);

            narrative += `**${I18n.n(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}\n`;
            
            // Insight Card
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` This area of knowledge is supported by extraordinary intelligence, promising deep mastery and natural academic grace.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` Challenges in this area suggest that your learning process requires conscious persistence and unconventional study methods.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Intellectual Style and Wisdom Analysis\n\n`;
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
        let narrative = `### Specialized Knowledge Insights\n\n`;
        
        // Mercury (Karaka for Learning) & Jupiter (Karaka for Wisdom)
        const mercHouse = this._getPlanetHouse(data, 'Mercury');
        const jupHouse = this._getPlanetHouse(data, 'Jupiter');
        
        if (mercHouse) {
            narrative += `**Intellectual Influence:** Mercury is in your ${this._formatHouse(mercHouse)} and Jupiter is in your ${this._formatHouse(jupHouse)}. `;
            if ([1, 4, 5, 7, 9, 10, 11].includes(mercHouse) && !data.vargaChart.planets.Mercury.isCombust) {
                narrative += `Mercury's strong placement indicates exceptional analytical skills and a fast, versatile learning capacity.\n\n`;
            } else {
                narrative += `Mercury's placement suggests success through specialized, deep research or overcoming initial learning hurdles.\n\n`;
            }
        }

        if (jupHouse) {
            if ([1, 4, 5, 7, 9, 10, 11].includes(jupHouse) && !data.vargaChart.planets.Jupiter.isCombust) {
                narrative += `Jupiter's influence grants you profound wisdom and the ability to synthesize vast amounts of knowledge into meaningful insights.\n\n`;
            } else {
                narrative += `Your wisdom is built through practical experience and solving ethical complexities within your field of study.\n\n`;
            }
        }

        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Educational and Wisdom Trajectory Predictions\n\n`;

        const l5 = data.houseLords[5];
        const l9 = data.houseLords[9];
        
        narrative += `**Academic and Creative Intelligence:**\n`;
        if (this.kendras.includes(l5.placedInHouse) || this.trikonas.includes(l5.placedInHouse)) {
            narrative += `You possess a powerful internal capacity for concentration and academic excellence. Your creative intellect will lead to significant breakthroughs.\n\n`;
        } else {
            narrative += `Your intellectual success requires conscious effort and disciplined study. You find truth through your own internal analysis and focused mastery.\n\n`;
        }

        narrative += `**Higher Learning and Research Depth:**\n`;
        if (this.kendras.includes(l9.placedInHouse) || this.trikonas.includes(l9.placedInHouse)) {
            narrative += `Your soul is destined for significant academic expansion. You will likely find great peace through formal higher learning, research, or philosophical mastery.\n\n`;
        } else {
            narrative += `Your path to higher wisdom is a self-directed journey. You gain mastery by mastering specialized subjects and solving complex intellectual riddles.\n\n`;
        }

        return narrative;
    }

    getPersonalizedAdvice(data) {
        let advice = `**Actionable Guidance for Knowledge:**\n`;
        const l5 = data.houseLords[5];
        
        if (this.dusthanas.includes(l5.placedInHouse)) {
            advice += `• To stabilize your learning, focus on disciplined research and regular purification of your intellectual intentions. True knowledge emerges as mental clutter is removed.\n`;
        }
        
        advice += `• Your intellectual potential is best activated by aligning your studies with the qualities of ${I18n.t('rasis.' + data.lagna.sign)}, focusing on ${this._getElementalAdvice(this._getElement(data.lagna.sign))}`;

        return advice;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const d24Matrix = {
            1: {
                1: "Intelligence is self-actualized. You have a powerful internal drive for learning and a mind that inherently seeks mastery.",
                5: "Creative intelligence. Your identity is inseparable from your creative intellectual expressions and your capacity for concentrated study.",
                9: "High wisdom and academic grace. Your soul's purpose is deeply tied to higher learning, research, and the search for absolute truth."
            },
            5: {
                1: "Your identity is significantly shaped by your intellectual or academic achievements. You carry your knowledge with great internal dignity.",
                5: "Unshakeable intellectual strength. You possess immense capacity for concentration and memory, aiding all your learning goals.",
                11: "Knowledge leads to significant gains. Your academic or creative intellectual reach is a major source of your professional prosperity."
            }
        };

        const result = d24Matrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        const sourceTheme = this._getHouseThemes(house);
        const targetTheme = this._getHouseThemes(pos);
        
        if (house === pos) return `**Insight:** Stability in ${sourceTheme.toLowerCase()}. Your intellectual foundations in this area are unshakeable and reliable.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** Mastery in ${sourceTheme.toLowerCase()} requires intense research or overcoming academic hurdles before it yields results.`;
        
        return `**Insight:** Your life's intellectual energy flows from ${sourceTheme.toLowerCase()} toward ${targetTheme.toLowerCase()}, linking these aspects of your wisdom.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const d24PlanetMatrix = {
            Mercury: {
                5: "A supreme analytical mind. You are blessed with profound concentration and a direct connection to intellectual systems.",
                1: "You carry a natural internal sense of logic and curiosity that influences all your academic aspirations.",
                10: "Intellectual prominence. Your knowledge directly aids your career status and professional recognition."
            },
            Jupiter: {
                9: "Deep wisdom and philosophical mastery. Your soul finds fulfillment in being a beacon of truth and higher learning.",
                1: "Maternal influence is central to your personality and sense of emotional security."
            },
            Sun: {
                1: "Strong inner authority in knowledge. Your soul seeks to lead or shine brightly within your intellectual community."
            }
        };

        const result = d24PlanetMatrix[planet]?.[house];
        if (result) return result;

        return `${I18n.t('planets.' + planet)} in the ${this._formatHouse(house)} of D24 influences your ${this._getHouseThemes(house).toLowerCase()}, shaping your specific intellectual style.`;
    }

    _getHouseThemes(h) {
        return ['', 'Knowledge Persona', 'Values/Memory', 'Drive/Effort', 'Foundational Study', 'Intelligence/Insight', 'Research/Seva', 'Collaborative Study', 'Transformative Knowledge', 'Higher Learning', 'Professional Mastery', 'Gains from Wisdom', 'Inner Release'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'active leadership in your intellectual community and maintaining an optimistic, pioneering outlook on learning.',
            Earth: 'building reliable foundations for your studies and focusing on tangible, long-term academic discipline.',
            Air: 'leveraging communication, strategic information gathering, and networking with experts to expand your wisdom.',
            Water: 'trusting your intuition and bringing empathy and emotional depth to your research and connection to knowledge.'
        };
        return advice[element] || 'maintaining balance in your learning.';
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
            key: 'D24',
            name: VARGA_INFO['D24'].name,
            desc: VARGA_INFO['D24'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}

export default new D24Analyzer();