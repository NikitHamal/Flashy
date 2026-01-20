import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

/**
 * D5: PANCHAMSHA - THE CHART OF FAME, AUTHORITY, AND LEGACY
 */
class D5Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D5', 'Jupiter');
    }

    analyzeCoreSignificance(data) {
        const lagnaName = I18n.t('rasis.' + data.lagna.sign);
        const lordName = I18n.t('planets.' + data.lagna.lord);
        const lagnaKeywords = I18n.t('analysis.keywords.' + data.lagna.sign);

        let narrative = `### Authority, Fame, and Public Recognition\n\n`;
        narrative += `The Panchamsha (D5) chart defines how you handle power, your capacity for leadership, and the way the world recognizes your talents. With **${lagnaName} rising in D5**, your natural leadership style and public charisma are characterized by ${lagnaKeywords}. This chart determines the \"Impact\" you have on society.\n\n`;

        narrative += `**Authority Ruler (L5 Lord):** The ruler of your public recognition, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This shows that your primary path to authority and fame is centered on **${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}**.\n\n`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        return narrative;
    }

    analyzeHouseLordDynamics(data) {
        let narrative = `### Pillars of Power and Legacy Matrix\n\n`;
        narrative += `The connections in D5 define how your creative intelligence translates into public authority and where you find the most significant recognition.\n\n`;

        const priorityHouses = [5, 1, 10, 9, 11, 2, 4, 7, 3, 6, 8, 12];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);

            narrative += `**${I18n.n(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}\n`;
            
            // Insight Card
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` The exaltation of this lord indicates exceptional charisma and natural success in attaining authority in this area.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` Challenges in this area suggest that your public recognition requires consistent effort and the overcoming of specific rivalries.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Charisma and Leadership Style Analysis\n\n`;
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
        let narrative = `### Specialized Recognition Insights\n\n`;
        
        // Sun (Karaka for Authority) & Jupiter (Karaka for Wisdom/Fame)
        const sunHouse = this._getPlanetHouse(data, 'Sun');
        const jupHouse = this._getPlanetHouse(data, 'Jupiter');
        
        if (sunHouse) {
            narrative += `**Charismatic Focus Point:** The Sun is in your ${this._formatHouse(sunHouse)} and Jupiter is in your ${this._formatHouse(jupHouse)}. `;
            if ([1, 5, 10, 9].includes(sunHouse) && !data.vargaChart.planets.Sun.isCombust) {
                narrative += `The Sun's strong placement in D5 grants you a natural, commanding presence and a clear destiny for leadership.\n\n`;
            } else {
                narrative += `Your authority is built through service, technical expertise, and overcoming specific challenges to your status.\n\n`;
            }
        }

        if (jupHouse && [1, 5, 9, 11].includes(jupHouse)) {
            narrative += `Jupiter's influence indicates that your fame is built on wisdom, ethical conduct, and the guidance you provide to others.\n\n`;
        }

        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Trajectory of Power and Recognition\n\n`;

        const l10 = data.houseLords[10];
        const l5 = data.houseLords[5];
        
        narrative += `**Professional Authority and Status:**\n`;
        if (this.kendras.includes(l10.placedInHouse) || this.trikonas.includes(l10.placedInHouse)) {
            narrative += `Your actions lead to high-level administrative success and visible public honor. You are destined to hold positions of significant trust.\n\n`;
        } else {
            narrative += `Your professional status grows through specialized knowledge and the mastery of intricate details that others might overlook.\n\n`;
        }

        narrative += `**Creative Impact and Legacy:**\n`;
        if (this.kendras.includes(l5.placedInHouse) || this.trikonas.includes(l5.placedInHouse)) {
            narrative += `Your creative output or your descendants will bring you significant joy and lasting recognition. Your legacy is one of visible impact.\n\n`;
        } else {
            narrative += `Your legacy is built quietly through deep personal realizations and the refinement of your internal character.\n\n`;
        }

        return narrative;
    }

    getPersonalizedAdvice(data) {
        let advice = `**Actionable Guidance for Authority:**\n`;
        const l1 = data.houseLords[1];
        
        if (this.dusthanas.includes(l1.placedInHouse)) {
            advice += `• To stabilize your public status, focus on selfless service and the mentorship of others. Your greatest power comes from empowering your peers.\n`;
        }
        
        advice += `• Your charisma is best activated by aligning with the qualities of ${I18n.t('rasis.' + data.lagna.sign)}, focusing on ${this._getElementalAdvice(this._getElement(data.lagna.sign))}`;

        return advice;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const d5Matrix = {
            1: {
                1: "Authority is self-sustaining. You carry an innate dignity that requires no external titles to be recognized by others.",
                5: "Fame through creative intelligence. Your unique talents and original ideas are your primary source of public impact.",
                10: "Your identity is inseparable from your professional status. You are a natural leader in your chosen field."
            },
            5: {
                1: "Creative output defines your personality. You are known for your 'spark' and the original way you approach life's challenges.",
                9: "Fortune through ethics and teaching. Your recognition comes from your commitment to higher truths and spiritual wisdom.",
                10: "Recognition for administrative excellence. Your creative solutions significantly impact your professional standing."
            }
        };

        const result = d5Matrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        const sourceTheme = this._getHouseThemes(house);
        const targetTheme = this._getHouseThemes(pos);
        
        if (house === pos) return `**Insight:** Stability in ${sourceTheme.toLowerCase()}. Your status in this area is foundational and reliable.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** Recognition regarding ${sourceTheme.toLowerCase()} is achieved by overcoming rivals or through acts of quiet service.`;
        
        return `**Insight:** Energy flows from ${sourceTheme.toLowerCase()} toward ${targetTheme.toLowerCase()}, showing how your authority influences these domains.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const d5PlanetMatrix = {
            Sun: {
                1: "Powerful leadership aura. You lead by example and naturally command respect in any social or professional setting.",
                10: "Destined for high administrative status and professional recognition. You shine brightest in roles of authority."
            },
            Jupiter: {
                5: "Supreme intelligence and fame through wisdom. Your creative intelligence is your primary legacy.",
                9: "Fortune through teaching and ethical leadership. You are recognized as a beacon of wisdom and grace."
            },
            Mars: {
                6: "Winning over rivals and competitors. You possess the strategic grit to overcome obstacles to your status."
            }
        };

        const result = d5PlanetMatrix[planet]?.[house];
        if (result) return result;

        return `${I18n.t('planets.' + planet)} in the ${this._formatHouse(house)} of D5 influences your ${this._getHouseThemes(house).toLowerCase()}, shaping your leadership style.`;
    }

    _getHouseThemes(h) {
        return ['', 'Power Persona', 'Wealth from Status', 'Influential Drive', 'Domestic Recognition', 'Creative Legacy', 'Victory over Rivals', 'Public Alliances', 'Transformative Power', 'Divine Recognition', 'Administrative Action', 'Gains from Authority', 'Private Legacy'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'active leadership and bold, visionary actions that inspire and command respect from your peers.',
            Earth: 'building reliable foundations for your status and focusing on practical, long-term legacy results.',
            Air: 'leveraging strategic communication, networking, and the sharing of wisdom to expand your field of influence.',
            Water: 'trusting your intuition and bringing empathy and emotional intelligence to your roles of authority.'
        };
        return advice[element] || 'maintaining balance in your power.';
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
            key: 'D5',
            name: VARGA_INFO['D5'].name,
            desc: VARGA_INFO['D5'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}
export default new D5Analyzer();
