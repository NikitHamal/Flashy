import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

class D3Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D3', 'Mars');
    }

    analyzeCoreSignificance(data) {
        const lagnaName = I18n.t('rasis.' + data.lagna.sign);
        const lordName = I18n.t('planets.' + data.lagna.lord);
        const lagnaKeywords = I18n.t('analysis.keywords.' + data.lagna.sign);

        let narrative = `### Motivation, Courage, and Initiative\n\n`;
        narrative += `The Drekkana (D3) chart represents your innate drive, courage, and relationship with siblings and peers. With **${lagnaName} rising in D3**, your approach to challenges and new ventures is characterized by ${lagnaKeywords}. This chart shows how you 'fight' for your goals.\n\n`;

        narrative += `**Drive Ruler (L3 Lord):** The ruler of your motivation, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This indicates that your primary source of initiative and energy is focused on **${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}**.\n\n`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        return narrative;
    }

    analyzeHouseLordDynamics(data) {
        let narrative = `### Pillars of Effort and Peer Dynamics\n\n`;
        narrative += `The connections in D3 define how your efforts translate into success and how you interact with your immediate circle.\n\n`;

        const priorityHouses = [3, 1, 11, 10, 6, 5, 9, 4, 7, 2, 8, 12];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);

            narrative += `**${I18n.n(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}\n`;
            
            // Insight Card
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` This area of effort is backed by exceptional courage and natural skill.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` Initial hurdles in this area require you to develop deeper patience and refined skills.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Action Style and Skill Analysis\n\n`;
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
        let narrative = `### Specialized Drive Insights\n\n`;
        
        // Mars (Karaka for Courage)
        const marsHouse = this._getPlanetHouse(data, 'Mars');
        if (!marsHouse) return narrative;
        
        narrative += `**Mars's Courage Influence:** Mars is in your ${this._formatHouse(marsHouse)}. `;
        if ([1, 3, 6, 10, 11].includes(marsHouse) && !data.vargaChart.planets.Mars.isCombust) {
            narrative += `This is a powerful placement for D3, giving you the natural 'grit' and resilience to achieve your goals despite any obstacles.\n\n`;
        } else {
            narrative += `This suggests that your initiative is applied more toward intellectual, communicative, or service-oriented goals.\n\n`;
        }

        const l3 = data.houseLords[3];
        if (l3.dignity === 'Exalted' || l3.dignity === 'Own Sign') {
            narrative += `**High Sibling Support:** A strong 3rd lord in D3 indicates significant support and a harmonious relationship with your siblings or close peers.\n\n`;
        }

        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Success and Effort Trajectory Predictions\n\n`;

        const l10 = data.houseLords[10];
        const l1 = data.houseLords[1];
        
        narrative += `**Execution of Professional Goals:**\n`;
        if (this.kendras.includes(l10.placedInHouse) || this.trikonas.includes(l10.placedInHouse)) {
            narrative += `Your efforts lead to visible professional success. You are someone who 'finishes what they start,' and your actions significantly impact your social standing.\n\n`;
        } else {
            narrative += `Your success comes through specialized, focused effort. You prefer working on projects with deep personal meaning rather than those aimed solely at public fame.\n\n`;
        }

        narrative += `**Relationship with Siblings and Peers:**\n`;
        const l3 = data.houseLords[3];
        if (this.kendras.includes(l3.placedInHouse) || this.trikonas.includes(l3.placedInHouse)) {
            narrative += `You find great strength and collaborative success through your circle of siblings and close friends.\n\n`;
        } else {
            narrative += `Your peer relationships are built on shared duties and specific skills, requiring mutual effort to maintain harmony.\n\n`;
        }

        return narrative;
    }

    getPersonalizedAdvice(data) {
        let advice = `**Actionable Guidance:**\n`;
        const l3 = data.houseLords[3];
        
        if (this.dusthanas.includes(l3.placedInHouse)) {
            advice += `• Channel your restlessness into disciplined physical or skill-based activities. Your greatest initiatives often arise from overcoming limitations.\n`;
        }
        
        advice += `• Your initiative is most effective when you align your drive with the qualities of ${I18n.t('rasis.' + data.lagna.sign)}, focusing on ${this._getElementalAdvice(this._getElement(data.lagna.sign))}`;

        return advice;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const d3Matrix = {
            1: {
                1: "Self-driven motivation. You possess a clear internal compass for your efforts and don't require external validation to proceed.",
                3: "Highly skilled and communicative initiative. Your success comes through your own unique talents and networking abilities.",
                10: "Career-focused drive. Your professional goals are the primary engine for all your life's efforts."
            },
            3: {
                1: "Siblings or close peers have a major impact on your identity and choices. Collaboration is key to your self-actualization.",
                11: "Strong support from siblings and friends leads to significant gains and professional growth."
            }
        };

        const result = d3Matrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        const sourceTheme = this._getHouseThemes(house);
        const targetTheme = this._getHouseThemes(pos);
        
        if (house === pos) return `**Insight:** Unshakeable resolve in ${sourceTheme.toLowerCase()}. Your initiative in this area is stable and reliable.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** Efforts in ${sourceTheme.toLowerCase()} involve overcoming internal doubts or external friction. Victory comes through persistence.`;
        
        return `**Insight:** Your life energy regarding ${sourceTheme.toLowerCase()} flows into the area of ${targetTheme.toLowerCase()}, linking your drive with these domains.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const d3PlanetMatrix = {
            Mars: {
                3: "Exceptional courage and skill mastery. You are a natural leader in any venture requiring bold action.",
                1: "High vitality and a pioneering spirit. You are always the first to step forward in challenging situations.",
                10: "Professional warrior archetype. You execute your career tasks with military-like precision and drive."
            },
            Mercury: {
                3: "Skill through communication and intellect. Success in fields requiring dexterity, writing, or strategic trade."
            }
        };

        const result = d3PlanetMatrix[planet]?.[house];
        if (result) return result;

        return `${I18n.t('planets.' + planet)} in the ${this._formatHouse(house)} of D3 influences your ${this._getHouseThemes(house).toLowerCase()}, defining your specific style of action.`;
    }

    _getHouseThemes(h) {
        return ['', 'Motivation Persona', 'Accumulated Drive', 'Siblings/Skills', 'Resilience/Home', 'Creative Logic', 'Competition/Service', 'Collaboration', 'Transformative Effort', 'Fortune in Ventures', 'Professional Execution', 'Gains from Effort', 'Letting Go'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'taking bold, pioneering initiatives and maintaining a visionary outlook in all your ventures.',
            Earth: 'building reliable foundations for your efforts and focusing on long-term sustainability.',
            Air: 'leveraging communication, networking, and strategic intellectual moves to achieve your goals.',
            Water: 'trusting your intuition and allowing your emotions to fuel your creative and nurturing initiatives.'
        };
        return advice[element] || 'maintaining balance in your efforts.';
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
            key: 'D3',
            name: VARGA_INFO['D3'].name,
            desc: VARGA_INFO['D3'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}

export default new D3Analyzer();
