import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

class D27Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D27', 'Mars');
    }

    analyzeCoreSignificance(data) {
        const lagnaName = I18n.t('rasis.' + data.lagna.sign);
        const lordName = I18n.t('planets.' + data.lagna.lord);
        const lagnaKeywords = I18n.t('analysis.keywords.' + data.lagna.sign);

        let narrative = `### Internal Strengths, Stamina, and Vitality\n\n`;
        narrative += `The Saptavimshamsha (D27) chart represents your internal physiological strengths, your physical stamina, and the hidden layers of your vitality. With **${lagnaName} rising in D27**, your approach to physical endurance and internal resilience is characterized by ${lagnaKeywords}. This chart determines the "Grit" of your being.\n\n`;

        narrative += `**Strength Ruler (L27 Lord):** The ruler of your internal vitality, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This shows that your core stamina and physiological strength are primarily channeled through **${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}**.\n\n`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        return narrative;
    }

    analyzeHouseLordDynamics(data) {
        let narrative = `### Pillars of Resilience and Vitality Matrix\n\n`;
        narrative += `The connections in D27 define the quality of your physical endurance and the ease with which you recover from internal or external tests.\n\n`;

        const priorityHouses = [1, 3, 6, 8, 10, 11, 5, 9, 4, 7, 2, 12];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);

            narrative += `**${I18n.n(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}\n`
            
            // Insight Card
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` This area of strength is backed by exceptional physiological merit, promising high endurance and natural resilience.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` Challenges in this area suggest that your stamina requires conscious cultivation and overcoming initial physiological hurdles.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Physiological Style and Endurance Analysis\n\n`;
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
        let narrative = `### Specialized Vitality Insights\n\n`;
        
        // Mars (Karaka for Strength) & Sun (Karaka for Vitality)
        const marsHouse = this._getPlanetHouse(data, 'Mars');
        const sunHouse = this._getPlanetHouse(data, 'Sun');
        
        if (marsHouse) {
            narrative += `**Strength Influence:** Mars is in your ${this._formatHouse(marsHouse)} and the Sun is in your ${this._formatHouse(sunHouse)}. `;
            if ([1, 3, 6, 10, 11].includes(marsHouse) && !data.vargaChart.planets.Mars.isCombust) {
                narrative += `Mars's strong placement grants you natural physical 'grit' and the capacity to overcome intense challenges.\n\n`;
            } else {
                narrative += `Mars's placement suggests success through specialized, disciplined effort or overcoming initial strength hurdles.\n\n`;
            }
        }

        if (sunHouse) {
            if ([1, 4, 7, 10, 5, 9, 11].includes(sunHouse) && !data.vargaChart.planets.Sun.isCombust) {
                narrative += `The Sun's influence provides you with robust physiological vitality and a powerful aura of leadership.\n\n`;
            } else {
                narrative += `Your vitality is built through practical self-care and solving health-related complexities.\n\n`;
            }
        }

        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Resilience and Vitality Trajectory Predictions\n\n`;

        const l1 = data.houseLords[1];
        const l10 = data.houseLords[10];
        
        narrative += `**Physical Endurance and Recovery:**\n`;
        if (this.kendras.includes(l1.placedInHouse) || this.trikonas.includes(l1.placedInHouse)) {
            narrative += `You possess a powerful internal capacity for recovery and physical endurance. Your grit will lead to significant breakthroughs.\n\n`;
        } else {
            narrative += `Your physical success requires conscious effort and disciplined self-care. You find strength through your own internal analysis and focused recovery.\n\n`;
        }

        narrative += `**Execution of Professional Grit:**\n`;
        if (this.kendras.includes(l10.placedInHouse) || this.trikonas.includes(l10.placedInHouse)) {
            narrative += `Your soul is destined for significant professional endurance. You find success through formal leadership and philosophical mastery of your craft.\n\n`;
        } else {
            narrative += `Your path to success is a self-directed journey of grit. You gain mastery by mastering specialized skills and solving complex professional riddles.\n\n`;
        }

        return narrative;
    }

    getPersonalizedAdvice(data) {
        let advice = `**Actionable Guidance for Grit:**\n`;
        const l1 = data.houseLords[1];
        
        if (this.dusthanas.includes(l1.placedInHouse)) {
            advice += `• To stabilize your vitality, focus on disciplined physical activity and regular purification of your health intentions. True strength emerges as ego dissolves.\n`;
        }
        
        advice += `• Your internal strength is best activated by aligning your actions with the qualities of ${I18n.t('rasis.' + data.lagna.sign)}, focusing on ${this._getElementalAdvice(this._getElement(data.lagna.sign))}`;

        return advice;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const d27Matrix = {
            1: {
                1: "Strength is self-actualized. You have a powerful internal drive for endurance and a soul that inherently knows its physical capacity.",
                10: "Professional grit. Your identity is inseparable from your creative physiological expressions and your capacity for concentrated effort.",
                11: "High vitality and gains. Your soul's purpose is deeply tied to higher learning, research, and the search for absolute strength."
            },
            3: {
                1: "Your identity is significantly shaped by your physical or peer achievements. You carry your strength with great internal dignity.",
                3: "Unshakeable effort. You possess immense capacity for concentration and stamina, aiding all your vital goals.",
                11: "Effort leads to significant gains. Your physical or creative reach is a major source of your professional prosperity."
            }
        };

        const result = d27Matrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        const sourceTheme = this._getHouseThemes(house);
        const targetTheme = this._getHouseThemes(pos);
        
        if (house === pos) return `**Insight:** Stability in ${sourceTheme.toLowerCase()}. Your vital foundations in this area are unshakeable and reliable.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** Strength in ${sourceTheme.toLowerCase()} requires intense self-care or overcoming physiological hurdles before it yields results.`;
        
        return `**Insight:** Your life's vital energy flows from ${sourceTheme.toLowerCase()} toward ${targetTheme.toLowerCase()}, linking these aspects of your resilience.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const d27PlanetMatrix = {
            Mars: {
                3: "A supreme physiological grit. You are blessed with profound concentration and a direct connection to strength systems.",
                1: "You carry a natural internal sense of action and curiosity that influences all your vital aspirations.",
                10: "Physical prominence. Your strength directly aids your career status and professional recognition."
            },
            Sun: {
                9: "Deep vitality and philosophical mastery. Your soul finds fulfillment in being a beacon of strength and higher vitality.",
                1: "Maternal influence is central to your personality and sense of physiological security."
            },
            Moon: {
                1: "Strong inner authority in strength. Your soul seeks to lead or shine brightly within your vital community."
            }
        };

        const result = d27PlanetMatrix[planet]?.[house];
        if (result) return result;

        return `${I18n.t('planets.' + planet)} in the ${this._formatHouse(house)} of D27 influences your ${this._getHouseThemes(house).toLowerCase()}, shaping your specific style of grit.`;
    }

    _getHouseThemes(h) {
        return ['', 'Grit Persona', 'Values/Stamina', 'Drive/Effort', 'Foundational Resilience', 'Physiological Insight', 'Research/Recovery', 'Collaborative Strength', 'Transformative Grit', 'Higher Vitality', 'Professional Endurance', 'Gains from Grit', 'Inner Release'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'active leadership in your vital community and maintaining an optimistic, pioneering outlook on resilience.',
            Earth: 'building reliable foundations for your health and focusing on tangible, long-term physiological discipline.',
            Air: 'leveraging communication, strategic information gathering, and networking with experts to expand your strength.',
            Water: 'trusting your intuition and bringing empathy and emotional depth to your recovery and connection to grit.'
        };
        return advice[element] || 'maintaining balance in your vitality.';
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
            key: 'D27',
            name: VARGA_INFO['D27'].name,
            desc: VARGA_INFO['D27'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}

export default new D27Analyzer();