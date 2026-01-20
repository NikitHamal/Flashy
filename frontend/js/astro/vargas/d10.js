import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

class D10Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D10', 'Sun');
    }

    analyzeCoreSignificance(data) {
        const lagnaName = I18n.t('rasis.' + data.lagna.sign);
        const lordName = I18n.t('planets.' + data.lagna.lord);
        const lagnaKeywords = I18n.t('analysis.keywords.' + data.lagna.sign);

        let narrative = `### Professional Identity and Social Impact\n\n`;
        narrative += `The Dashamsha (D10) chart is the definitive map of your career, social status, and professional achievements. With **${lagnaName} rising in D10**, your professional persona is characterized by ${lagnaKeywords}. This chart determines the ultimate reach of your influence in the world.\n\n`;

        narrative += `**Career Ruler (L10 Lord):** The ruler of your professional self, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This is the "Engine" of your career, showing that your success is driven by your mastery over ${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}\n\n`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        return narrative;
    }

    analyzeHouseLordDynamics(data) {
        let narrative = `### Professional Pillars and Growth Matrix\n\n`;
        narrative += `In Dashamsha, house connections reveal how your professional efforts translate into status and gains.\n\n`;

        const priorityHouses = [10, 1, 11, 2, 9, 7, 5, 4, 6, 3, 12, 8];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);

            narrative += `**${I18n.n(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}\n`;
            
            // Insight Card
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` Your professional standing in this area is amplified by the planet's exaltation, promising high recognition.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` Challenges in this professional area require you to develop resilience and unconventional strategies.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Career Field and Authority Analysis\n\n`;
        const planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];

        planets.forEach(p => {
            const houseNum = this._getPlanetHouse(data, p);
            if (!houseNum) return;

            const pos = data.vargaChart.planets[p];
            const signName = this.signs[pos.rasi.index];
            const planetName = I18n.t('planets.' + p);

            narrative += `**Placement of ${planetName} in the ${this._formatHouse(houseNum)} (${I18n.t('rasis.' + signName)}):** `;
            narrative += this._getPlanetInHouseDescription(p, houseNum, signName, data);
            
            const dignity = this._getDignity(p, pos.rasi.index);
            if (dignity !== 'Neutral') {
                narrative += ` **Professional Strength:** ${dignity}.`;
            }
            narrative += `\n\n`;
        });

        return narrative;
    }

    analyzeAdvancedYogaLogic(data) {
        let narrative = `### Specialized Professional Insights\n\n`;
        
        // Success Links
        const l10 = data.houseLords[10];
        const l1 = data.houseLords[1];
        
        if (l10.placedInHouse === 1 || l1.placedInHouse === 10) {
            narrative += `**Powerful Career Signature:** A direct link between your professional self and your career house suggests a destiny of significant leadership and professional visibility.\n\n`;
        }

        const sunHouse = this._getPlanetHouse(data, 'Sun');
        if (sunHouse && sunHouse === 10) {
            narrative += `**Peak Administrative Status:** The Sun in the 10th of D10 is a signature for top-level authority, government favor, and widespread professional respect.\n\n`;
        }

        const satHouse = this._getPlanetHouse(data, 'Saturn');
        if (satHouse && satHouse === 10) {
            narrative += `**Steady Professional Rise:** Saturn in the 10th of D10 indicates that while success may come with time and labor, it will be unshakeable and long-lasting once achieved.\n\n`;
        }

        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Professional Trajectory Predictions\n\n`;

        const l10 = data.houseLords[10];
        const l11 = data.houseLords[11];
        
        narrative += `**Career Reach and Impact:**\n`;
        if (this.kendras.includes(l10.placedInHouse)) {
            narrative += `Your career is destined for high visibility. You have the capacity to manage large organizations or lead in the public sphere.\n\n`;
        } else {
            narrative += `Your career path is one of specialized expertise. You find fulfillment through mastering your craft and having a deep, focused impact.\n\n`;
        }

        narrative += `**Financial Rewards from Work:**\n`;
        if (l11.placedInHouse === 10 || l10.placedInHouse === 11) {
            narrative += `A direct link between professional action and gains indicates a highly profitable career path where your efforts are consistently rewarded.\n\n`;
        } else {
            narrative += `Your professional gains are steady and grow through your reputation for reliability and expertise.\n\n`;
        }

        return narrative;
    }

    getPersonalizedAdvice(data) {
        let advice = `**Professional Guidance:**\n`;
        const l10 = data.houseLords[10];
        
        if (this.dusthanas.includes(l10.placedInHouse)) {
            advice += `• Your career path involves solving complex problems or serving in challenging environments. Embrace these as opportunities for maximum growth.\n`;
        }
        
        advice += `• Success in your chosen field is best achieved by aligning your actions with the qualities of ${I18n.t('rasis.' + data.lagna.sign)}, emphasizing ${this._getElementalAdvice(this._getElement(data.lagna.sign))}`;

        return advice;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const d10Matrix = {
            1: {
                1: "Self-made professional path. You are a natural entrepreneur who creates their own status.",
                10: "Identity is synonymous with career. Professional achievement is the primary driver of your life.",
                11: "Natural magnet for professional gains. Your personality attracts networks and lucrative opportunities."
            },
            10: {
                1: "Career prominence. You will be known primarily for your professional contributions and leadership.",
                2: "Wealth-generating profession. Your career is directly focused on the accumulation of hard assets.",
                11: "Highly profitable career. Every professional milestone brings significant financial expansion."
            }
        };

        const result = d10Matrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        const sourceTheme = this._getHouseThemes(house);
        const targetTheme = this._getHouseThemes(pos);
        
        if (house === pos) return `**Insight:** Professional stability in ${sourceTheme.toLowerCase()}. You have unshakeable authority in this domain.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** Your career path in ${sourceTheme.toLowerCase()} requires overcoming competition or navigating complex organizational structures.`;
        
        return `**Insight:** Professional energy flows from ${sourceTheme.toLowerCase()} toward ${targetTheme.toLowerCase()}, linking your status with these life areas.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const d10PlanetMatrix = {
            Sun: {
                10: "Ultimate professional authority. Destined for a top position with significant command and fame.",
                1: "Natural leader. You carry yourself with professional dignity and command respect instantly."
            },
            Jupiter: {
                10: "Respected professional advisor or leader. Success through ethical conduct and wise decision-making.",
                11: "Vast professional gains and a supportive network of influential people."
            },
            Saturn: {
                10: "Unshakeable professional position built through time, discipline, and hard work. A late-blooming but massive status."
            }
        };

        const result = d10PlanetMatrix[planet]?.[house];
        if (result) return result;

        return `${I18n.t('planets.' + planet)} in the ${this._formatHouse(house)} of D10 influences your professional ${this._getHouseThemes(house).toLowerCase()}, defining your style of work.`;
    }

    _getHouseThemes(h) {
        return ['', 'Professional Persona', 'Income/Assets', 'Effort/Skills', 'Environment', 'Creativity/Logic', 'Competition/Service', 'Public Relations', 'Professional Shifts', 'Fortune/Luck', 'Status/Action', 'Gains/Networks', 'Service/Sacrifice'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'pioneering new initiatives and maintaining a visionary outlook in your industry.',
            Earth: 'building reliable structures and focusing on tangible results and sustainability.',
            Air: 'leveraging communication, networking, and intellectual strategies for professional growth.',
            Water: 'trusting your intuition and bringing empathy and emotional intelligence to your work environment.'
        };
        return advice[element] || 'maintaining professional balance.';
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
            key: 'D10',
            name: VARGA_INFO['D10'].name,
            desc: VARGA_INFO['D10'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}

export default new D10Analyzer();
