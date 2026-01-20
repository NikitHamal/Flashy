import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

class D30Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D30', 'Saturn');
    }

    analyzeCoreSignificance(data) {
        const lagnaName = I18n.t('rasis.' + data.lagna.sign);
        const lordName = I18n.t('planets.' + data.lagna.lord);
        const lagnaKeywords = I18n.t('analysis.keywords.' + data.lagna.sign);

        let narrative = `### Misfortune, Evils, and Karmic Resilience\n\n`;
        narrative += `The Trimshamsha (D30) chart is traditionally used to analyze misfortunes, chronic ailments, and the native's moral character or "inner demons." With **${lagnaName} rising in D30**, your capacity to resist external misfortunes and internal ethical challenges is characterized by ${lagnaKeywords}. This chart determines your "Karmic Immunity."\n\n`;

        narrative += `**Resistance Ruler (L30 Lord):** The ruler of your karmic defense, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This suggests that your primary arena for karmic refinement and overcoming obstacles is **${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}**.\n\n`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        return narrative;
    }

    analyzeHouseLordDynamics(data) {
        let narrative = `### Pillars of Resistance and Karmic Matrix\n\n`;
        narrative += `The house connections in D30 define how various life areas contribute to or help you overcome deep-seated karmic friction.\n\n`;

        const priorityHouses = [1, 6, 8, 12, 10, 4, 5, 9, 2, 7, 3, 11];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);

            narrative += `**${I18n.n(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}\n`;
            
            // Insight Card
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` The strength of this lord provides exceptional resistance against the misfortunes associated with this house.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` Vulnerability in this area suggests that specific ethical or physical discipline is required to navigate challenges here.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Karmic Friction and Behavioral Analysis\n\n`;
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
        let narrative = `### Specialized Karmic Insights\n\n`;
        
        // Saturn (Karaka for Misery) & Mars (Karaka for Misfortune)
        const satHouse = this._getPlanetHouse(data, 'Saturn');
        const marsHouse = this._getPlanetHouse(data, 'Mars');
        
        if (satHouse) {
            narrative += `**Karmic Pressure Point:** Saturn is in your ${this._formatHouse(satHouse)} and Mars is in your ${this._formatHouse(marsHouse)}. `;
            if ([6, 8, 12].includes(satHouse)) {
                narrative += `Saturn's placement in a dusthana in D30 actually helps in neutralizing long-term chronic misfortunes through disciplined endurance.\n\n`;
            } else {
                narrative += `Saturn's placement indicates that specific responsibilities in ${this._getHouseThemes(satHouse).toLowerCase()} are your primary karmic teachers.\n\n`;
            }
        }

        if (data.patterns && data.patterns.dusthanaMalefics && data.patterns.dusthanaMalefics.length > 0) {
            narrative += `**Harsha/Sarala/Vimala Influence:** Malefics in dusthanas in D30 can provide a "Viparita" effect, where you gain strength from the very challenges you face.\n\n`;
        }

        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Trajectory of Obstacles and Resilience\n\n`;

        const l6 = data.houseLords[6];
        const l8 = data.houseLords[8];
        
        narrative += `**Resistance to Chronic Issues:**\n`;
        if (l6.dignity === 'Exalted' || l6.dignity === 'Own Sign' || this.dusthanas.includes(l6.placedInHouse)) {
            narrative += `You possess high resilience against competitive friction and health-related obstacles. You tend to emerge stronger after every crisis.\n\n`;
        } else {
            narrative += `Your resilience is built through conscious lifestyle choices and ethical clarity. You must be proactive in managing stress and competitive environments.\n\n`;
        }

        narrative += `**Handling Transformative Crisis:**\n`;
        if (this.kendras.includes(l8.placedInHouse) || this.trikonas.includes(l8.placedInHouse)) {
            narrative += `Major life transformations are handled with grace and philosophical understanding. You find wisdom in the depths of challenge.\n\n`;
        } else {
            narrative += `Crisis management is a self-taught skill for you. You gain your greatest 'karmic immunity' by mastering the art of letting go and starting anew.\n\n`;
        }

        return narrative;
    }

    getPersonalizedAdvice(data) {
        let advice = `**Karmic Guidance:**\n`;
        const l1 = data.houseLords[1];
        
        if (this.dusthanas.includes(l1.placedInHouse)) {
            advice += `• Your primary spiritual task is to maintain ethical integrity even when faced with significant external pressure. Silence and meditation are your best shields.\n`;
        }
        
        advice += `• Strengthen your inner resistance by aligning with the qualities of ${I18n.t('rasis.' + data.lagna.sign)}, focusing on ${this._getElementalAdvice(this._getElement(data.lagna.sign))}`;

        return advice;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const d30Matrix = {
            1: {
                1: "Immense natural resistance to misfortune. You possess a strong ethical core and a soul that cannot be easily swayed by external evils.",
                8: "Life involves deep transformations. Your character is refined through the fires of intense experience and research into the self.",
                12: "Spiritual protection. You have a natural detachment that helps you navigate misfortunes with a sense of inner peace."
            },
            6: {
                6: "Excellent capacity to overcome enemies and competitors. You possess a natural 'service' orientation that neutralizes friction.",
                12: "Victory over secret enemies. Your challenges are resolved through spiritual means or by removing yourself from toxic environments."
            }
        };

        const result = d30Matrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        const sourceTheme = this._getHouseThemes(house);
        const targetTheme = this._getHouseThemes(pos);
        
        if (house === pos) return `**Insight:** Stability in ${sourceTheme.toLowerCase()}. Your defenses in this area are reliable and self-sustaining.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** Misfortune in ${sourceTheme.toLowerCase()} is converted into spiritual growth or service-oriented strength.`;
        
        return `**Insight:** Karmic energy flows from ${sourceTheme.toLowerCase()} toward ${targetTheme.toLowerCase()}, indicating how your challenges are linked across these domains.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const d30PlanetMatrix = {
            Saturn: {
                8: "Profound endurance and longevity in the face of crisis. You have the patience to outlast any misfortune.",
                12: "Spiritual discipline that protects against losses. You find strength in solitude and renunciation."
            },
            Mars: {
                6: "A powerful 'warrior' response to obstacles. You are highly effective at cutting through confusion and debt.",
                1: "Your identity is forged through struggle. You have an intense drive to overcome any limitation."
            },
            Jupiter: {
                9: "Divine grace that protects against most evils. Your wisdom and ethical conduct act as a powerful shield."
            }
        };

        const result = d30PlanetMatrix[planet]?.[house];
        if (result) return result;

        return `${I18n.t('planets.' + planet)} in the ${this._formatHouse(house)} of D30 influences your ${this._getHouseThemes(house).toLowerCase()}, defining how you process specific karmic frictions.`;
    }

    _getHouseThemes(h) {
        return ['', 'Karmic Immunity', 'Family/Financial Karma', 'Mental Grit', 'Inner Happiness', 'Moral Intelligence', 'Chronic Friction', 'Relational Karma', 'Transformative Evil', 'Philosophical Shield', 'Karmic Action', 'Gains from Hardship', 'Spiritual Release'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'using your natural enthusiasm and pioneering spirit to burn through obstacles. Maintain a visionary outlook.',
            Earth: 'building reliable, practical routines and focusing on long-term stability to ground your karmic challenges.',
            Air: 'leveraging communication, analytical clarity, and strategic networking to navigate through complex frictions.',
            Water: 'trusting your intuition and bringing deep emotional empathy and purification to your karmic experiences.'
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
            key: 'D30',
            name: VARGA_INFO['D30'].name,
            desc: VARGA_INFO['D30'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}
export default new D30Analyzer();
