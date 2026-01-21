import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

class D40Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D40', 'Moon');
    }

    analyzeCoreSignificance(data) {
        const lagnaName = I18n.t('rasis.' + data.lagna.sign);
        const lordName = I18n.t('planets.' + data.lagna.lord);
        const lagnaKeywords = I18n.t('analysis.keywords.' + data.lagna.sign);

        let narrative = `### General Auspiciousness and Divine Grace\n\n`;
        narrative += `The Khavedamsha (D40) chart is a microscopic lens into the general level of auspiciousness, divine grace, and the overall fruits of your actions in this lifetime. With **${lagnaName} rising in D40**, your experience of "Luck" and favorable events is characterized by ${lagnaKeywords}. This chart reveals the subtle blessings that carry you through life.\n\n`;

        narrative += `**Grace Ruler (L40 Lord):** The ruler of your general auspiciousness, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This shows that the primary channel through which divine grace manifests in your life is **${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}**.\n\n`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        return narrative;
    }

    analyzeHouseLordDynamics(data) {
        let narrative = `### Pillars of Fortune and Auspicious Matrix\n\n`;
        narrative += `The connections between houses in D40 define which areas of your life are naturally more "blessed" or where you encounter the most favorable results with the least effort.\n\n`;

        const priorityHouses = [9, 1, 5, 11, 2, 4, 10, 7, 3, 6, 8, 12];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);

            narrative += `**${I18n.n(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}\n`;
            
            // Insight Card
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` This area is marked by exceptional auspiciousness and natural ease of attainment.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` Favorable results here require consistent effort and the removal of subtle obstacles before grace can flow freely.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Style of Luck and Auspicious Manifestations\n\n`;
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
        let narrative = `### Specialized Prosperity and Grace Insights\n\n`;
        
        // Jupiter (Karaka for Grace) & Moon (Karaka for Motherly Blessing/Nurturing Luck)
        const jupHouse = this._getPlanetHouse(data, 'Jupiter');
        const moonHouse = this._getPlanetHouse(data, 'Moon');
        
        if (jupHouse) {
            narrative += `**Universal Blessing Point:** Jupiter is in your ${this._formatHouse(jupHouse)} and the Moon is in your ${this._formatHouse(moonHouse)}. `;
            if ([1, 5, 9, 4, 11].includes(jupHouse) && !data.vargaChart.planets.Jupiter.isCombust) {
                narrative += `Jupiter's strong placement in D40 acts as a "Great Protector," ensuring that even difficult periods lead to ultimately auspicious outcomes.\n\n`;
            } else {
                narrative += `Jupiter's influence indicates that your blessings are earned through wisdom and overcoming specific life riddles.\n\n`;
            }
        }

        if (moonHouse && [1, 4, 7, 10, 2, 11].includes(moonHouse)) {
            narrative += `The Moon's placement suggests a naturally rhythmic flow of favorable events and strong maternal/ancestral support.\n\n`;
        }

        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Trajectory of Auspicious Events\n\n`;

        const l9 = data.houseLords[9];
        const l11 = data.houseLords[11];
        
        narrative += `**General Level of Divine Fortune:**\n`;
        if (this.trikonas.includes(l9.placedInHouse) || this.kendras.includes(l9.placedInHouse)) {
            narrative += `You possess a high degree of natural 'Purva Punya' or past-life merit. Auspicious events often happen precisely when needed, without excessive struggle.\n\n`;
        } else {
            narrative += `Your fortune is built through consistent ethical action. You find that blessings manifest most clearly when you are in service to others or engaged in higher study.\n\n`;
        }

        narrative += `**Fulfillment of Gains and Desires:**\n`;
        if (this.kendras.includes(l11.placedInHouse) || this.trikonas.includes(l11.placedInHouse)) {
            narrative += `Your desires find easy fulfillment through the grace of your social and professional networks. Gains come from unexpected but favorable directions.\n\n`;
        } else {
            narrative += `The fruits of your actions manifest as steady, reliable progress. You gain most by focusing on the process rather than the immediate outcome.\n\n`;
        }

        return narrative;
    }

    getPersonalizedAdvice(data) {
        let advice = `**Actionable Guidance for Enhancing Grace:**\n`;
        const l1 = data.houseLords[1];
        
        if (this.dusthanas.includes(l1.placedInHouse)) {
            advice += `• To activate your hidden reserves of luck, focus on selfless service and regular charitable acts. Grace flows most freely when you are a conduit for the wellbeing of others.\n`;
        }
        
        advice += `• Your natural auspiciousness is best channeled by aligning with the qualities of ${I18n.t('rasis.' + data.lagna.sign)}, focusing on ${this._getElementalAdvice(this._getElement(data.lagna.sign))}`;

        return advice;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const d40Matrix = {
            1: {
                1: "Auspiciousness is self-generated. You carry an aura of luck and divine grace that influences everyone you meet.",
                9: "Fortune through ethics and higher learning. Your very identity is a magnet for auspicious events and dharmic success.",
                11: "Natural gains and fulfillment of desires. You are destined to see the positive fruits of your actions manifest frequently."
            },
            9: {
                1: "Your personality is heavily supported by past-life merits. Divine grace is a constant companion in your life journey.",
                9: "Unshakeable good fortune. Your path is naturally guided by dharmic principles, leading to sustained auspiciousness."
            }
        };

        const result = d40Matrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        const sourceTheme = this._getHouseThemes(house);
        const targetTheme = this._getHouseThemes(pos);
        
        if (house === pos) return `**Insight:** Stability in ${sourceTheme.toLowerCase()}. Your blessings in this area are foundational and reliable.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** Grace in ${sourceTheme.toLowerCase()} manifests after overcoming specific tests or through acts of selfless service.`;
        
        return `**Insight:** Auspicious energy flows from ${sourceTheme.toLowerCase()} toward ${targetTheme.toLowerCase()}, linking your blessings across these domains.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const d40PlanetMatrix = {
            Jupiter: {
                1: "A beacon of divine grace. You are naturally optimistic and protected by wisdom and ethical conduct.",
                9: "Supreme fortune and spiritual blessings. You find immense luck through teachers, travel, and philosophy."
            },
            Venus: {
                4: "Auspiciousness through home, comfort, and maternal blessings. You find grace in beautiful surroundings.",
                11: "Gains and favorable events through social popularity, artistic pursuits, and feminine support."
            },
            Moon: {
                1: "A nurturing and rhythmic flow of luck. You are publicly appealing and supported by a strong sense of internal peace."
            }
        };

        const result = d40PlanetMatrix[planet]?.[house];
        if (result) return result;

        return `${I18n.t('planets.' + planet)} in the ${this._formatHouse(house)} of D40 influences your ${this._getHouseThemes(house).toLowerCase()}, shaping your specific experience of luck.`;
    }

    _getHouseThemes(h) {
        return ['', 'Grace Persona', 'Wealth Blessings', 'Courageous Grace', 'Domestic Happiness', 'Meritorious Logic', 'Service Blessings', 'Relational Grace', 'Transformative Luck', 'Divine Fortune', 'Auspicious Action', 'Vast Gains', 'Inner Peace'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'active initiative and bold, visionary actions that create new opportunities for grace to manifest.',
            Earth: 'steady, practical routines and focusing on tangible long-term goals to ground your natural luck.',
            Air: 'strategic communication, networking, and sharing wisdom to expand your field of auspiciousness.',
            Water: 'trusting your intuition and bringing emotional depth and empathy to your interactions to attract divine grace.'
        };
        return advice[element] || 'maintaining balance in your luck.';
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
            key: 'D40',
            name: VARGA_INFO['D40'].name,
            desc: VARGA_INFO['D40'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}
export default new D40Analyzer();
