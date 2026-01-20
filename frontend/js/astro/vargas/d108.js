import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

class D108Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D108', 'Moon');
    }

    analyzeCoreSignificance(data) {
        const lagnaName = I18n.t('rasis.' + data.lagna.sign);
        const lordName = I18n.t('planets.' + data.lagna.lord);
        const lagnaKeywords = I18n.t('analysis.keywords.' + data.lagna.sign);

        let narrative = `### Holistic Soul Strength and Life Completion\n\n`;
        narrative += `The Ashtottaransh (D108) chart is a rare and profound divisional chart that represents the holistic strength of your soul and the ultimate fulfillment of your life's journey. 108 is a sacred number in Vedic tradition, representing cosmic completion. With **${lagnaName} rising in D108**, your soul's holistic frequency is characterized by ${lagnaKeywords}. This chart reveals the total sum of your life's spiritual evolution.\n\n`;

        narrative += `**Total Ruler (L108 Lord):** The ruler of your holistic fulfillment, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This shows that the final synthesis of your life's experiences is centered on **${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}**.\n\n`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        return narrative;
    }

    analyzeHouseLordDynamics(data) {
        let narrative = `### Pillars of Holistic Growth and Cosmic Matrix\n\n`;
        narrative += `The connections in D108 define the foundational pillars of your soul's strength and how they contribute to your ultimate fulfillment.\n\n`;

        const priorityHouses = [1, 9, 12, 5, 4, 10, 11, 2, 7, 3, 6, 8];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);

            narrative += `**${I18n.n(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}\n`;
            
            // Insight Card
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` This holistic area of your life is blessed with exceptional strength and divine alignment.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` Final resolution in this area requires deep internal work and the integration of challenging soul-lessons.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Holistic Archetypes and Cosmic Frequencies\n\n`;
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
        let narrative = `### Specialized Holistic Insights\n\n`;
        
        // Moon (Karaka for Soul Peace) & Jupiter (Karaka for Wisdom/Completion)
        const moonHouse = this._getPlanetHouse(data, 'Moon');
        const jupHouse = this._getPlanetHouse(data, 'Jupiter');
        
        if (moonHouse) {
            narrative += `**Cosmic Fulfillment Point:** The Moon is in your ${this._formatHouse(moonHouse)} and Jupiter is in your ${this._formatHouse(jupHouse)}. `;
            if ([1, 4, 9, 12].includes(moonHouse)) {
                narrative += `The Moon's strong placement in D108 grants you a profound capacity for inner peace and a nurturing connection to the cosmic whole.\n\n`;
            } else {
                narrative += `Holistic peace is found through self-discipline and the solving of internal emotional riddles.\n\n`;
            }
        }

        if (jupHouse && [1, 5, 9, 11].includes(jupHouse)) {
            narrative += `Jupiter's influence ensures that your life journey is guided by a higher sense of purpose and divine wisdom.\n\n`;
        }

        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Trajectory of Holistic Life Fulfillment\n\n`;

        const l12 = data.houseLords[12];
        const l1 = data.houseLords[1];
        
        narrative += `**Ultimate Spiritual Resolution (Moksha):**\n`;
        if (this.dusthanas.includes(l12.placedInHouse) || this.trikonas.includes(l12.placedInHouse)) {
            narrative += `Your soul finds a clear and auspicious path toward spiritual liberation and inner release. You possess the holistic strength to let go of earthly attachments with grace.\n\n`;
        } else {
            narrative += `Your spiritual resolution is a gradual process of integration and service. You find 'Moksha' in the quality of your daily actions and ethical choices.\n\n`;
        }

        narrative += `**Total Life Fulfillment:**\n`;
        if (this.kendras.includes(l1.placedInHouse) || this.trikonas.includes(l1.placedInHouse)) {
            narrative += `Your life journey is marked by a deep sense of total fulfillment. You are destined to see the positive fruits of your long-term evolution manifest in this lifetime.\n\n`;
        } else {
            narrative += `Fulfillment for you is a self-directed and private achievement. You gain the most by mastering your internal state and achieving holistic balance within the self.\n\n`;
        }

        return narrative;
    }

    getPersonalizedAdvice(data) {
        let advice = `**Guidance for Holistic Completion:**\n`;
        const l1 = data.houseLords[1];
        
        if (this.dusthanas.includes(l1.placedInHouse)) {
            advice += `• To stabilize your soul's holistic strength, focus on selfless service and regular periods of spiritual retreat. True completion comes from within.\n`;
        }
        
        advice += `• Align your holistic growth with the qualities of ${I18n.t('rasis.' + data.lagna.sign)}, focusing on ${this._getElementalAdvice(this._getElement(data.lagna.sign))}`;

        return advice;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const d108Matrix = {
            1: {
                1: "Your soul's strength is self-sustaining. You possess a rare holistic consistency and a powerful aura of completion.",
                9: "Holistic growth through wisdom and grace. Your life is underpinned by supreme dharmic merit and divine support.",
                12: "Your soul is here for final resolution and liberation. You find your ultimate strength through detachment and spiritual depth."
            },
            12: {
                1: "Liberation and soul-peace are tied to your very identity. You are naturally detached and focused on the ultimate truth.",
                12: "Unshakeable spiritual peace. Your most subtle karmic debts are settled, leading to holistic liberation."
            }
        };

        const result = d108Matrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        const sourceTheme = this._getHouseThemes(house);
        const targetTheme = this._getHouseThemes(pos);
        
        if (house === pos) return `**Insight:** Holistic stability in ${sourceTheme.toLowerCase()}. Your soul has reached a point of foundational peace in this cosmic domain.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** Holistic growth in ${sourceTheme.toLowerCase()} involve acts of profound transformation or selfless service to the whole.`;
        
        return `**Insight:** Holistic energy flows from ${sourceTheme.toLowerCase()} toward ${targetTheme.toLowerCase()}, linking your total fulfillment across these domains.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const d108PlanetMatrix = {
            Moon: {
                1: "A nurturing and holistic inner soul. You find your ultimate peace through empathy and cosmic connection.",
                4: "A profound sense of domestic and emotional resolution. Your soul is at home in the universe."
            },
            Jupiter: {
                9: "Supreme holistic wisdom. Your life journey is guided by high spiritual truths and divine grace."
            },
            Saturn: {
                12: "The discipline of liberation. You find your ultimate strength through solitude, renunciation, and settling final debts."
            }
        };

        const result = d108PlanetMatrix[planet]?.[house];
        if (result) return result;

        return `${I18n.t('planets.' + planet)} in the ${this._formatHouse(house)} of D108 influences your ${this._getHouseThemes(house).toLowerCase()}, shaping your total life fulfillment.`;
    }

    _getHouseThemes(h) {
        return ['', 'Holistic Persona', 'Cosmic Values', 'Soul Drive', 'Inner Completion', 'Higher Intuition', 'Life Service', 'Dharmic Union', 'Ultimate Shift', 'Cosmic Grace', 'Final Action', 'Total Fulfillment', 'Moksha/Release'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'pioneering spiritual leadership and maintaining a visionary, enthusiastic inner world.',
            Earth: 'building reliable foundations for your holistic growth and focusing on practical, long-term spiritual results.',
            Air: 'leveraging strategic intellectual clarity and networking with cosmic-peers to expand your holistic peace.',
            Water: 'trusting your deep intuition and bringing emotional empathy and purification to your final life fulfillment.'
        };
        return advice[element] || 'maintaining balance in your holistic life.';
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
            key: 'D108',
            name: VARGA_INFO['D108'].name,
            desc: VARGA_INFO['D108'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}
export default new D108Analyzer();
