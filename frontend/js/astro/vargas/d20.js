import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

class D20Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D20', 'Jupiter');
    }

    analyzeCoreSignificance(data) {
        const lagnaName = I18n.t('rasis.' + data.lagna.sign);
        const lordName = I18n.t('planets.' + data.lagna.lord);
        const lagnaKeywords = I18n.t('analysis.keywords.' + data.lagna.sign);

        let narrative = `### Spirituality, Religious Inclinations, and Inner Growth

`;
        narrative += `The Vimshamsha (D20) chart represents your spiritual evolution, your connection to the divine, and the specific religious or meditative paths you are drawn to. With **${lagnaName} rising in D20**, your internal relationship with the sacred is characterized by ${lagnaKeywords}. This chart determines the "Spiritual Depth" of your soul.

`;

        narrative += `**Spiritual Ruler (L20 Lord):** The ruler of your spiritual identity, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This reveals that your soul's awakening and connection to higher consciousness are primarily found through **${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}**.

`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        return narrative;
    }

    analyzeHouseLordDynamics(data) {
        let narrative = `### Pillars of Faith and Meditative Matrix

`;
        narrative += `The connections in D20 define the quality of your spiritual practice and the ease with which you access higher states of awareness.

`;

        const priorityHouses = [9, 5, 1, 12, 4, 10, 11, 7, 8, 2, 6, 3];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);

            narrative += `**${I18n.n(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}
`;
            
            // Insight Card
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` This area of spiritual growth is backed by significant past-life merit, promising deep insights and natural grace.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` Challenges in this area suggest that your spiritual path requires conscious purification and overcoming internal doubts.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Divine Connection and Devotional Analysis

`;
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
        let narrative = `### Specialized Spiritual Insights\n\n`;
        
        // Jupiter (Karaka for Spirituality and Guru)
        const jupHouse = this._getPlanetHouse(data, 'Jupiter');
        if (!jupHouse) return narrative;
        
        narrative += `**Jupiter's Spiritual Influence:** Jupiter is in your ${this._formatHouse(jupHouse)}. `;
        if ([1, 4, 5, 9, 12].includes(jupHouse) && !data.vargaChart.planets.Jupiter.isCombust) {
            narrative += `This is a highly auspicious signature for D20, indicating that higher wisdom, a true guru, and profound spiritual realizations will find you with ease.

`;
        } else {
            narrative += `This suggests that your spiritual path is built through service, resolving ethical complexities, or through unconventional meditative techniques.

`;
        }

        const l9 = data.houseLords[9];
        if (l9.dignity === 'Exalted' || l9.dignity === 'Own Sign') {
            narrative += `**Strong Dharmic Foundation:** A powerful 9th lord in D20 is an excellent indicator of protected spiritual merit and high integrity in your faith.

`;
        }

        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Spiritual Trajectory Predictions

`;

        const l9 = data.houseLords[9];
        const l5 = data.houseLords[5];
        
        narrative += `**Growth in Higher Wisdom:**
`;
        if (this.kendras.includes(l9.placedInHouse) || this.trikonas.includes(l9.placedInHouse)) {
            narrative += `Your soul is destined for significant spiritual expansion. You will likely find great peace through formal higher learning, philosophy, or a specific religious lineage.

`;
        } else {
            narrative += `Your spiritual growth is a self-directed journey. You find truth through your own internal analysis and by solving the 'riddles' of existence.

`;
        }

        narrative += `**Meditative Depth and Mantra Power:**
`;
        if (this.kendras.includes(l5.placedInHouse) || this.trikonas.includes(l5.placedInHouse)) {
            narrative += `You possess a natural internal capacity for concentration and meditative depth. Mantras or creative spiritual expressions will be highly effective for you.

`;
        } else {
            narrative += `Your meditative peace requires conscious effort and disciplined practice. Focus on building a stable internal world to support your spiritual aspirations.

`;
        }

        return narrative;
    }

    getPersonalizedAdvice(data) {
        let advice = `**Actionable Guidance for Inner Growth:**
`;
        const l9 = data.houseLords[9];
        
        if (this.dusthanas.includes(l9.placedInHouse)) {
            advice += `• To stabilize your spiritual connection, focus on selfless service (Seva) and regular purification of your intentions. Truth emerges as ego dissolves.
`;
        }
        
        advice += `• Your spiritual potential is best activated by aligning your practice with the qualities of ${I18n.t('rasis.' + data.lagna.sign)}, focusing on ${this._getElementalAdvice(this._getElement(data.lagna.sign))}`;

        return advice;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const d20Matrix = {
            1: {
                1: "Spiritual path is self-actualized. You have a powerful internal moral compass and a soul that inherently knows its divine connection.",
                9: "High dharma and grace. Your soul's purpose is deeply tied to higher wisdom, ethics, and the search for absolute truth.",
                5: "Meditative intelligence. Your identity is inseparable from your creative spiritual expressions and your capacity for insight."
            },
            9: {
                1: "Your identity is significantly shaped by your spiritual or religious convictions. You carry your faith with great internal dignity.",
                9: "Unshakeable spiritual fortune. You possess immense merit from past lives that protects your dharmic path in this lifetime.",
                12: "Spiritual liberation is the goal. Your faith leads you toward seclusion, deep meditation, or foreign spiritual systems."
            }
        };

        const result = d20Matrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        const sourceTheme = this._getHouseThemes(house);
        const targetTheme = this._getHouseThemes(pos);
        
        if (house === pos) return `**Insight:** Stability in ${sourceTheme.toLowerCase()}. Your spiritual foundations in this area are unshakeable and reliable.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** Growth in ${sourceTheme.toLowerCase()} requires internal purification or overcoming karmic hurdles before it yields peace.`;
        
        return `**Insight:** Your soul's spiritual energy flows from ${sourceTheme.toLowerCase()} toward ${targetTheme.toLowerCase()}, linking these aspects of your inner growth.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const d20PlanetMatrix = {
            Jupiter: {
                9: "A supreme spiritual guide. You are blessed with profound higher wisdom and a direct connection to dharmic lineages.",
                1: "You carry a natural internal sense of grace and wisdom that influences all your spiritual aspirations.",
                12: "Deep meditative peace and connection to the infinite. A capacity for profound spiritual seclusion."
            },
            Sun: {
                1: "Strong inner authority in faith. Your soul seeks to lead or shine brightly within your spiritual community.",
                9: "High spiritual status and recognized wisdom. You find fulfillment in being a beacon of truth for others."
            },
            Moon: {
                4: "Deep emotional peace through spirituality. Your connection to the divine is nurturing and provides immense resilience.",
                1: "Your personality is deeply sensitive to spiritual vibrations and divine beauty."
            }
        };

        const result = d20PlanetMatrix[planet]?.[house];
        if (result) return result;

        return `${I18n.t('planets.' + planet)} in the ${this._formatHouse(house)} of D20 influences your ${this._getHouseThemes(house).toLowerCase()}, shaping your specific spiritual style.`;
    }

    _getHouseThemes(h) {
        return ['', 'Spiritual Persona', 'Values/Scriptures', 'Drive/Practice', 'Inner Peace/Home', 'Insight/Mantra', 'Purification/Seva', 'Devotional Bonds', 'Transformation', 'Dharma/Guru', 'Spiritual Action', 'Gains/Sangha', 'Liberation/Solitude'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'active leadership in your spiritual community and maintaining an optimistic, pioneering outlook on inner growth.',
            Earth: 'building reliable foundations for your practice and focusing on tangible, long-term spiritual discipline.',
            Air: 'leveraging communication, strategic study of scriptures, and networking with like-minded souls to expand your awareness.',
            Water: 'trusting your intuition and bringing empathy and emotional depth to your meditative practice and connection to the sacred.'
        };
        return advice[element] || 'maintaining balance in your inner growth.';
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
            key: 'D20',
            name: VARGA_INFO['D20'].name,
            desc: VARGA_INFO['D20'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}

export default new D20Analyzer();