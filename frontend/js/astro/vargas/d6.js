import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

/**
 * D6: SHASHTAMSHA - THE CHART OF CHALLENGES, HEALTH, AND VICTORY
 */
class D6Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D6', 'Mars');
    }

    analyzeCoreSignificance(data) {
        const lagnaName = I18n.t('rasis.' + data.lagna.sign);
        const lordName = I18n.t('planets.' + data.lagna.lord);
        const lagnaKeywords = I18n.t('analysis.keywords.' + data.lagna.sign);

        let narrative = `### Resilience, Challenges, and Victory\n\n`;
        narrative += `The Shashtamsha (D6) chart defines your capacity to handle acute challenges, manage debts, and emerge victorious over enemies or competitors. With **${lagnaName} rising in D6**, your defensive style and ability to manage obstacles are characterized by ${lagnaKeywords}. This chart determines your \"Grit\" in the face of friction.\n\n`;

        narrative += `**Resilience Ruler (L6 Lord):** The ruler of your ability to overcome hurdles, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This shows that your primary source of strength in the face of conflict is focused on **${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}**.\n\n`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        return narrative;
    }

    analyzeHouseLordDynamics(data) {
        let narrative = `### Pillars of Strength and Conflict Matrix\n\n`;
        narrative += `The connections in D6 define how your various life areas contribute to your overall immunity and your success in competitive environments.\n\n`;

        const priorityHouses = [6, 1, 10, 3, 11, 2, 4, 7, 5, 9, 8, 12];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);

            narrative += `**${I18n.n(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}\n`;
            
            // Insight Card
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` The exaltation of this lord indicates exceptional defensive strength and high probability of success in overcoming challenges related to this area.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` Vulnerability here suggests that you must be proactive and disciplined in managing the friction associated with this domain.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Defensive Style and Victory Analysis\n\n`;
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
        let narrative = `### Specialized Victory Insights\n\n`;
        
        // Mars (Karaka for Victory/Strength) & Saturn (Karaka for Endurance/Debts)
        const marsHouse = this._getPlanetHouse(data, 'Mars');
        const satHouse = this._getPlanetHouse(data, 'Saturn');
        
        if (marsHouse) {
            narrative += `**Defensive Focus Point:** Mars is in your ${this._formatHouse(marsHouse)} and Saturn is in your ${this._formatHouse(satHouse)}. `;
            if ([1, 3, 6, 10, 11].includes(marsHouse) && !data.vargaChart.planets.Mars.isCombust) {
                narrative += `Mars's strong placement in D6 grants you the natural 'warrior' energy to crush obstacles and succeed in competitive fields.\n\n`;
            } else {
                narrative += `Your victory is achieved through strategy, technical precision, and overcoming initial strength constraints.\n\n`;
            }
        }

        if (satHouse && [6, 8, 12].includes(satHouse)) {
            narrative += `Saturn's placement in a dusthana in D6 acts as a 'Harsha Yoga' effect, where you find peace by successfully managing your duties and debts.\n\n`;
        }

        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Trajectory of Victories and Obstacles\n\n`;

        const l6 = data.houseLords[6];
        const l1 = data.houseLords[1];
        
        narrative += `**Capacity to Overcome Enemies:**\n`;
        if (l6.dignity === 'Exalted' || l6.dignity === 'Own Sign' || this.dusthanas.includes(l6.placedInHouse)) {
            narrative += `You possess a powerful internal capacity to neutralize competition and resolve disputes in your favor. Your rivals often become your unwitting supporters.\n\n`;
        } else {
            narrative += `Your success over challenges is a self-directed journey of grit. You gain mastery by analyzing the roots of conflict and solving them through discipline.\n\n`;
        }

        narrative += `**Health Resilience and Immunity:**\n`;
        if (l1.dignity === 'Exalted' || l1.dignity === 'Own Sign' || this.kendras.includes(l1.placedInHouse)) {
            narrative += `You possess a robust internal constitution. Your 'immunity signature' is strong, allowing for quick recovery from physical or competitive stress.\n\n`;
        } else {
            narrative += `Your health and resilience require conscious maintenance. You find your greatest strength through regular purification and disciplined self-care.\n\n`;
        }

        return narrative;
    }

    getPersonalizedAdvice(data) {
        let advice = `**Actionable Guidance for Resilience:**\n`;
        const l1 = data.houseLords[1];
        
        if (this.dusthanas.includes(l1.placedInHouse)) {
            advice += `• To stabilize your defensive energy, focus on disciplined daily routines and the active management of your debts. Your greatest victories arise from your willingness to face obstacles head-on.\n`;
        }
        
        advice += `• Your grit is best activated by aligning with the qualities of ${I18n.t('rasis.' + data.lagna.sign)}, focusing on ${this._getElementalAdvice(this._getElement(data.lagna.sign))}`;

        return advice;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const d6Matrix = {
            1: {
                1: "Your identity is fortified by self-discipline. You have a powerful internal drive to overcome any limitation or health challenge.",
                6: "You are a natural 'Healer' or 'Fighter.' Your personality is strengthened by the very obstacles you face and resolve.",
                10: "Victory through professional action. Your status is built on your ability to solve complex problems and overcome industry friction."
            },
            6: {
                1: "Challenges find you, but you have the inherent strength to consume them and grow stronger. You thrive in competitive environments.",
                11: "Friction leads to gains. Your rivals unknowingly act as catalysts for your professional and financial prosperity."
            }
        };

        const result = d6Matrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        const sourceTheme = this._getHouseThemes(house);
        const targetTheme = this._getHouseThemes(pos);
        
        if (house === pos) return `**Insight:** Stability in ${sourceTheme.toLowerCase()}. Your defenses in this area are unshakeable and reliable.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** Victory regarding ${sourceTheme.toLowerCase()} manifests through acts of service or profound internal transformation.`;
        
        return `**Insight:** Defensive energy flows from ${sourceTheme.toLowerCase()} toward ${targetTheme.toLowerCase()}, linking your victories across these domains.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const d6PlanetMatrix = {
            Mars: {
                6: "A supreme 'victory' placement. You have the strategic grit to cut through any competition or obstacle with ease.",
                1: "High vitality and a pioneering defensive style. You are always the first to face a challenge directly."
            },
            Saturn: {
                6: "Endurance through long-term challenges. You outlast your rivals and find stability through disciplined service.",
                12: "Victory over hidden enemies and a profound capacity to settle karmic debts through solitude and release."
            },
            Jupiter: {
                9: "Victory through wisdom and grace. Your ethical conduct acts as a shield against most forms of competition or health friction."
            }
        };

        const result = d6PlanetMatrix[planet]?.[house];
        if (result) return result;

        return `${I18n.t('planets.' + planet)} in the ${this._formatHouse(house)} of D6 influences your ${this._getHouseThemes(house).toLowerCase()}, defining your defensive style.`;
    }

    _getHouseThemes(h) {
        return ['', 'Immunity Persona', 'Financial Resilience', 'Grit/Drive', 'Domestic Security', 'Strategic Wisdom', 'Victory/Service', 'Partnership Strength', 'Chronic Resilience', 'Dharmic Defense', 'Professional Victory', 'Gains from Friction', 'Dispute Resolution'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'active leadership in facing obstacles and maintaining an optimistic, pioneering outlook on competition.',
            Earth: 'building reliable foundations for your health and focusing on tangible long-term goals to ground your defensive energy.',
            Air: 'leveraging communication, strategic information, and networking to navigate through complex life frictions.',
            Water: 'trusting your intuition and bringing deep empathy and emotional purification to your resolution of challenges.'
        };
        return advice[element] || 'maintaining balance in your resilience.';
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
            key: 'D6',
            name: VARGA_INFO['D6'].name,
            desc: VARGA_INFO['D6'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}
export default new D6Analyzer();
