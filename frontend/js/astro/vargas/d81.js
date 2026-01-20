import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

class D81Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D81', 'Venus');
    }

    analyzeCoreSignificance(data) {
        const lagnaName = I18n.t('rasis.' + data.lagna.sign);
        const lordName = I18n.t('planets.' + data.lagna.lord);
        const lagnaKeywords = I18n.t('analysis.keywords.' + data.lagna.sign);

        let narrative = `### Microscopic Resolution of Soul and Union\n\n`;
        narrative += `The Nava-Navamsha (D81) chart represents a further refinement of the Navamsha (D9), providing a microscopic look at the ultimate "fruitage" of your relationships, your spiritual depth, and the hidden strengths of your soul. With **${lagnaName} rising in D81**, the most subtle layers of your destiny are characterized by ${lagnaKeywords}. This chart reveals the final "DNA" of your karmic results.\n\n`;

        narrative += `**Subtle Ruler (L81 Lord):** The ruler of your microscopic destiny, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This indicates that the ultimate resolution of your soul's desires is focused on **${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}**.\n\n`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        return narrative;
    }

    analyzeHouseLordDynamics(data) {
        let narrative = `### Pillars of Subtle Influence and Destiny Matrix\n\n`;
        narrative += `The connections in D81 define the finest details of your life's outcomes, particularly in the realms of long-term stability and internal satisfaction.\n\n`;

        const priorityHouses = [1, 7, 9, 5, 4, 10, 11, 2, 3, 6, 8, 12];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);

            narrative += `**${I18n.n(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}\n`;
            
            // Insight Card
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` This subtle area of your destiny is marked by exceptional refinement and favorable resolution.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` Minor frictions in this area require subtle adjustment and ethical fine-tuning to reach full resolution.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Subtle Archetypes and Inner Satisfaction Analysis\n\n`;
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
        let narrative = `### Specialized Subtle Insights\n\n`;
        
        // Venus (Karaka for Union/Satisfaction) & Jupiter (Karaka for Spiritual Depth)
        const venHouse = this._getPlanetHouse(data, 'Venus');
        const jupHouse = this._getPlanetHouse(data, 'Jupiter');
        
        if (venHouse) {
            narrative += `**Inner Satisfaction Point:** Venus is in your ${this._formatHouse(venHouse)} and Jupiter is in your ${this._formatHouse(jupHouse)}. `;
            if ([1, 4, 7, 10, 5, 9, 11].includes(venHouse) && !data.vargaChart.planets.Venus.isCombust) {
                narrative += `Venus's strong placement in D81 indicates a deep, microscopic capacity for relationship satisfaction and aesthetic fulfillment.\n\n`;
            } else {
                narrative += `Inner satisfaction is reached through self-mastery and refining your subtle desires.\n\n`;
            }
        }

        if (jupHouse && [1, 5, 9, 4].includes(jupHouse)) {
            narrative += `Jupiter's influence provides a microscopic layer of spiritual protection and wisdom that guides your most subtle life choices.\n\n`;
        }

        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Trajectory of Final Soul Resolutions\n\n`;

        const l7 = data.houseLords[7];
        const l9 = data.houseLords[9];
        
        narrative += `**The Final Resolution of Partnerships:**\n`;
        if (this.kendras.includes(l7.placedInHouse) || this.trikonas.includes(l7.placedInHouse)) {
            narrative += `Your long-term unions find an auspicious and harmonious final resolution. You possess the subtle skills to maintain deep soul-connections over time.\n\n`;
        } else {
            narrative += `Your relationship fruitage is a result of consistent, subtle effort and adjustment. You find the most value in partnerships that challenge you to grow spiritually.\n\n`;
        }

        narrative += `**Ultimate Spiritual Fruitage:**\n`;
        if (this.kendras.includes(l9.placedInHouse) || this.trikonas.includes(l9.placedInHouse)) {
            narrative += `Your spiritual journey leads to a profound sense of inner completion and divine grace. Your most subtle actions are aligned with dharmic truth.\n\n`;
        } else {
            narrative += `Your spiritual completion is a private, self-directed journey. You find the deepest grace in quiet service and the solving of internal philosophical riddles.\n\n`;
        }

        return narrative;
    }

    getPersonalizedAdvice(data) {
        let advice = `**Guidance for Subtle Harmony:**\n`;
        const l1 = data.houseLords[1];
        
        if (this.dusthanas.includes(l1.placedInHouse)) {
            advice += `• To enhance your inner satisfaction, focus on regular periods of silence and the purification of your most subtle intentions. The finest details matter most in your life path.\n`;
        }
        
        advice += `• Align your subtle desires with the qualities of ${I18n.t('rasis.' + data.lagna.sign)}, focusing on ${this._getElementalAdvice(this._getElement(data.lagna.sign))}`;

        return advice;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const d81Matrix = {
            1: {
                1: "Your subtle identity is perfectly aligned with your soul's journey. You possess a natural self-consistency at the most microscopic level.",
                7: "The final resolution of your identity is heavily influenced by your relationships and your capacity for collaboration.",
                9: "Your most subtle self is a beacon of dharmic merit and spiritual wisdom. You carry the finest blessings of your past actions."
            },
            7: {
                1: "Partnerships are inseparable from your final identity resolution. You find your deepest self through the mirror of the other.",
                7: "Unshakeable stability in soul-unions. Your most subtle relationship karma is strong and harmonious."
            }
        };

        const result = d81Matrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        const sourceTheme = this._getHouseThemes(house);
        const targetTheme = this._getHouseThemes(pos);
        
        if (house === pos) return `**Insight:** Subtle stability in ${sourceTheme.toLowerCase()}. Your soul has reached a point of foundational peace in this domain.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** The final resolution of ${sourceTheme.toLowerCase()} involve acts of release or profound internal transformation.`;
        
        return `**Insight:** Subtle energy flows from ${sourceTheme.toLowerCase()} toward ${targetTheme.toLowerCase()}, linking your final soul-resolutions across these domains.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const d81PlanetMatrix = {
            Venus: {
                1: "A deeply aesthetic and harmonious inner soul. You find your ultimate satisfaction through beauty and balanced union.",
                7: "A soul here for deep, microscopic relationship resolution. You value the fine details of partnership above all else."
            },
            Jupiter: {
                9: "Supreme subtle wisdom. Your most private spiritual thoughts are aligned with high dharmic truths."
            },
            Moon: {
                4: "A profound sense of inner peace and domestic resolution. Your soul finds its ultimate home within itself."
            }
        };

        const result = d81PlanetMatrix[planet]?.[house];
        if (result) return result;

        return `${I18n.t('planets.' + planet)} in the ${this._formatHouse(house)} of D81 influences your ${this._getHouseThemes(house).toLowerCase()}, shaping your finest soul-results.`;
    }

    _getHouseThemes(h) {
        return ['', 'Subtle Persona', 'Fine Values', 'Detailed Skill', 'Inner Home', 'Subtle Wisdom', 'Minor Friction', 'Soul Union', 'Transformation', 'Fine Fortune', 'Final Status', 'Subtle Gains', 'Release'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'pioneering subtle initiatives and maintaining a visionary, enthusiastic inner world.',
            Earth: 'building reliable foundations for your subtle inner peace and focusing on tangible soul-results.',
            Air: 'leveraging strategic intellectual clarity and networking with soul-peers to expand your inner harmony.',
            Water: 'trusting your deep intuition and bringing emotional empathy and purification to your finest soul-resolutions.'
        };
        return advice[element] || 'maintaining balance in your subtle inner life.';
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
            key: 'D81',
            name: VARGA_INFO['D81'].name,
            desc: VARGA_INFO['D81'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}
export default new D81Analyzer();
