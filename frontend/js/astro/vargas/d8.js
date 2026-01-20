import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

/**
 * D8: ASHTAMSHA - THE CHART OF TRANSFORMATIONS AND LONGEVITY
 */
class D8Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D8', 'Saturn');
    }

    analyzeCoreSignificance(data) {
        const lagnaName = I18n.t('rasis.' + data.lagna.sign);
        const lordName = I18n.t('planets.' + data.lagna.lord);
        const lagnaKeywords = I18n.t('analysis.keywords.' + data.lagna.sign);

        let narrative = `### Transformation, Longevity, and Hidden Strength\n\n`;
        narrative += `The Ashtamsha (D8) chart defines how you navigate the most intense, hidden, and transformative parts of life. It reveals your capacity for resilience, your longevity, and your ability to "rise from the ashes." With **${lagnaName} rising in D8**, your transformative style and survival instincts are characterized by ${lagnaKeywords}. This chart determines the \"Phoenix\" quality of your soul.\n\n`;

        narrative += `**Survival Ruler (L8 Lord):** The ruler of your transformative path, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This shows that your primary arena for deep metamorphosis and evolutionary growth is **${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}**.\n\n`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        return narrative;
    }

    analyzeHouseLordDynamics(data) {
        let narrative = `### Pillars of Resilience and Transformation Matrix\n\n`;
        narrative += `The connections in D8 define which areas of your life are most subject to sudden shifts and how those shifts contribute to your long-term survival.\n\n`;

        const priorityHouses = [8, 1, 12, 4, 10, 2, 11, 7, 5, 9, 6, 3];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);

            narrative += `**${I18n.n(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}\n`;
            
            // Insight Card
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` The exaltation of this lord indicates exceptional resilience and a natural grace in navigating the most intense life reboots.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` Vulnerability here suggests that sudden shifts in this area require your deepest attention and the conscious cultivation of detachment.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Response to Crisis and Evolutionary Analysis\n\n`;
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
        let narrative = `### Specialized Survival Insights\n\n`;
        
        // Saturn (Karaka for Longevity) & Mars (Karaka for Resilience)
        const satHouse = this._getPlanetHouse(data, 'Saturn');
        const marsHouse = this._getPlanetHouse(data, 'Mars');
        
        if (satHouse) {
            narrative += `**Survival Focus Point:** Saturn is in your ${this._formatHouse(satHouse)} and Mars is in your ${this._formatHouse(marsHouse)}. `;
            if ([1, 8, 12, 10, 11].includes(satHouse) && !data.vargaChart.planets.Saturn.isCombust) {
                narrative += `Saturn's strong placement in D8 indicates a powerful 'endurance signature' and the capacity to outlast most crises.\n\n`;
            } else {
                narrative += `Your survival requires conscious discipline, ethical clarity, and overcoming initial resource reboots.\n\n`;
            }
        }

        if (marsHouse && [1, 3, 6, 8, 10].includes(marsHouse)) {
            narrative += `Mars's influence grants you a rapid 'Phoenix' response to challenges, allowing you to transform and pivot quickly.\n\n`;
        }

        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Trajectory of Transformation and Longevity\n\n`;

        const l8 = data.houseLords[8];
        const l1 = data.houseLords[1];
        
        narrative += `**Major Life Reboots and Evolutions:**\n`;
        if (l8.dignity === 'Exalted' || l8.dignity === 'Own Sign' || this.kendras.includes(l8.placedInHouse)) {
            narrative += `Your major life transformations are supported by significant internal strength. You tend to emerge from every crisis with a more refined and powerful sense of purpose.\n\n`;
        } else {
            narrative += `Your transformations are deeply personal and involve acts of profound release. You gain the most by mastering your own internal state regardless of external shifts.\n\n`;
        }

        narrative += `**Foundational Vitality and Survival:**\n`;
        if (this.kendras.includes(l1.placedInHouse) || this.trikonas.includes(l1.placedInHouse)) {
            narrative += `You possess a robust internal core that provides long-term survival. Your path is marked by significant endurance and the ability to maintain stability through change.\n\n`;
        } else {
            narrative += `Your vitality grows through specialized knowledge and the mastery of hidden or research-based domains. You find strength in the unknown.\n\n`;
        }

        return narrative;
    }

    getPersonalizedAdvice(data) {
        let advice = `**Actionable Guidance for Resilience:**\n`;
        const l1 = data.houseLords[1];
        
        if (this.dusthanas.includes(l1.placedInHouse)) {
            advice += `• To stabilize your survival energy, focus on meditation, detachment, and the active study of life's hidden cycles. True power comes from your willingness to evolve.\n`;
        }
        
        advice += `• Your resilience is best activated by aligning with the qualities of ${I18n.t('rasis.' + data.lagna.sign)}, focusing on ${this._getElementalAdvice(this._getElement(data.lagna.sign))}`;

        return advice;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const d8Matrix = {
            1: {
                1: "Survival is self-actualized. You possess a rare internal unshakeability and a soul that thrives on the challenge of transformation.",
                8: "You are destined for deep research or occult reboots. Your identity is forged in the fires of the unknown and hidden.",
                12: "Transformation through release and solitude. You find your greatest strength when you let go of the old to make room for the new."
            },
            8: {
                1: "Major reboots are inseparable from your identity. You are like a Phoenix, constantly refining your sense of self through intense experiences.",
                8: "Ultimate survival stability. Your capacity to navigate the deepest life shifts is unshakeable and self-sustaining."
            }
        };

        const result = d8Matrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        const sourceTheme = this._getHouseThemes(house);
        const targetTheme = this._getHouseThemes(pos);
        
        if (house === pos) return `**Insight:** Stability in ${sourceTheme.toLowerCase()}. Your survival foundations in this area are reliable and well-protected.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** Transformation regarding ${sourceTheme.toLowerCase()} manifests through acts of service or profound internal release.`;
        
        return `**Insight:** Evolutionary energy flows from ${sourceTheme.toLowerCase()} toward ${targetTheme.toLowerCase()}, linking your major reboots across these domains.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const d8PlanetMatrix = {
            Saturn: {
                8: "Maximum endurance and longevity signature. You have the patience to outlast any crisis and find wisdom in hidden things.",
                12: "Longevity through detachment and spiritual discipline. You find your ultimate survival strength in solitude."
            },
            Mars: {
                1: "A powerful survival instinct. You meet major life shifts with bold action and pioneering grit.",
                8: "A soul here for deep research and handling secret or intense challenges with strategic precision."
            },
            Jupiter: {
                9: "Transformation through grace and wisdom. Your ethical conduct and spiritual alignment act as a protector during major shifts."
            }
        };

        const result = d8PlanetMatrix[planet]?.[house];
        if (result) return result;

        return `${I18n.t('planets.' + planet)} in the ${this._formatHouse(house)} of D8 influences your ${this._getHouseThemes(house).toLowerCase()}, shaping your survival style.`;
    }

    _getHouseThemes(h) {
        return ['', 'Survival Persona', 'Shared Assets', 'Crisis Drive', 'Inner Resilience', 'Occult Wisdom', 'Managing Shifts', 'Shared Depth', 'Deep Transformation', 'Grace in Change', 'Professional Reboot', 'Gains from Shifts', 'Final Surrender'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'taking bold leadership during crises and maintaining a visionary, enthusiastic commitment to your own evolution.',
            Earth: 'building reliable foundations for your resilience and focusing on practical, long-term survival results.',
            Air: 'leveraging strategic intellectual clarity and networking with experts to navigate through complex life shifts.',
            Water: 'trusting your deep intuition and bringing emotional empathy and purification to your most intense reboots.'
        };
        return advice[element] || 'maintaining balance in your transformations.';
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
            key: 'D8',
            name: VARGA_INFO['D8'].name,
            desc: VARGA_INFO['D8'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}
export default new D8Analyzer();
