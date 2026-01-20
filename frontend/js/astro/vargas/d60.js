import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

class D60Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D60', 'Jupiter');
    }

    analyzeCoreSignificance(data) {
        const lagnaName = I18n.t('rasis.' + data.lagna.sign);
        const lordName = I18n.t('planets.' + data.lagna.lord);
        const lagnaKeywords = I18n.t('analysis.keywords.' + data.lagna.sign);

        let narrative = `### The Supreme Resolution of Destiny\n\n`;
        narrative += `The Shashtyamsha (D60) is traditionally considered the most critical divisional chart after the Rasi (D1) and Navamsha (D9). It reveals the microscopic details of your soul's journey and the ultimate fruits of all your karmas. With **${lagnaName} rising in D60**, the final "flavor" of your destiny is characterized by ${lagnaKeywords}. This chart shows the root cause behind why things happen the way they do.\n\n`;

        narrative += `**Destiny Ruler (L60 Lord):** The ruler of your ultimate destiny, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This shows that the final purpose of your current incarnation is heavily channeled through the domain of **${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}**.\n\n`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        return narrative;
    }

    analyzeHouseLordDynamics(data) {
        let narrative = `### Pillars of Supreme Karma and Destiny Matrix\n\n`;
        narrative += `The connections in D60 define the "Fine Print" of your life path, showing which areas are most strongly supported by your past merits.\n\n`;

        const priorityHouses = [1, 9, 10, 5, 4, 2, 11, 7, 3, 6, 8, 12];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);

            narrative += `**${I18n.n(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}\n`;
            
            // Insight Card
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` This area of destiny is supported by supreme past-life merits, leading to almost effortless success.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` Unfinished karma in this area requires your deepest attention and conscious ethical refinement in this lifetime.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Soul Archetypes and Ultimate Influences\n\n`;
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
        let narrative = `### Specialized Destiny Insights\n\n`;
        
        // Jupiter (Karaka for Supreme Grace) & Saturn (Karaka for Final Karma)
        const jupHouse = this._getPlanetHouse(data, 'Jupiter');
        const satHouse = this._getPlanetHouse(data, 'Saturn');
        
        if (jupHouse) {
            narrative += `**Supreme Karmic Balance:** Jupiter is in your ${this._formatHouse(jupHouse)} and Saturn is in your ${this._formatHouse(satHouse)}. `;
            if ([1, 5, 9, 4, 10].includes(jupHouse) && !data.vargaChart.planets.Jupiter.isCombust) {
                narrative += `Jupiter's powerful influence in D60 provides a "Destiny Shield," ensuring that even the most difficult karmic debts are settled with minimal pain.\n\n`;
            } else {
                narrative += `Your path involves working through complex karmic knots with wisdom and patience.\n\n`;
            }
        }

        if (satHouse && [1, 4, 7, 10, 11].includes(satHouse)) {
            narrative += `Saturn's placement indicates that you have the internal discipline to successfully settle your major karmic debts in this lifetime.\n\n`;
        }

        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Trajectory of Supreme Purpose and Results\n\n`;

        const l1 = data.houseLords[1];
        const l10 = data.houseLords[10];
        
        narrative += `**The Ultimate Fruits of Action:**\n`;
        if (this.kendras.includes(l1.placedInHouse) || this.trikonas.includes(l1.placedInHouse)) {
            narrative += `Your soul is destined to see the positive fulfillment of its primary aspirations. Your life path is marked by significant accomplishments that stand the test of time.\n\n`;
        } else {
            narrative += `Your destiny is a path of deep internal realization. You gain the most 'karmic credit' by mastering your own internal state regardless of external results.\n\n`;
        }

        narrative += `**Final Professional and Social Legacy:**\n`;
        if (this.kendras.includes(l10.placedInHouse) || this.trikonas.includes(l10.placedInHouse)) {
            narrative += `Your professional journey is supported by significant auspicious karma, leading to roles of honor and lasting public contribution.\n\n`;
        } else {
            narrative += `Your legacy is built on solving complex, hidden professional challenges and achieving mastery in specialized fields.\n\n`;
        }

        return narrative;
    }

    getPersonalizedAdvice(data) {
        let advice = `**Actionable Guidance for Ultimate Success:**\n`;
        const l1 = data.houseLords[1];
        
        if (this.dusthanas.includes(l1.placedInHouse)) {
            advice += `• To harmonize your deepest karmic currents, focus on absolute honesty and selfless service. In D60, the intention behind the act is even more important than the act itself.\n`;
        }
        
        advice += `• Align your ultimate purpose with the qualities of ${I18n.t('rasis.' + data.lagna.sign)}, focusing on ${this._getElementalAdvice(this._getElement(data.lagna.sign))}`;

        return advice;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const d60Matrix = {
            1: {
                1: "Supreme self-mastery destiny. You are here to finalize a major chapter of your soul's evolution with authority and clarity.",
                9: "A destiny of wisdom and grace. Your life path is guided by high dharmic principles and significant past-life merits.",
                10: "Your soul is here for a mission of action and public contribution. Your identity is inseparable from your work for the world."
            },
            10: {
                1: "Professional destiny is tied to your very identity. You cannot separate your soul's growth from your life's work.",
                10: "Unshakeable professional success. You have the ultimate karmic support to reach the pinnacle of your chosen field."
            }
        };

        const result = d60Matrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        const sourceTheme = this._getHouseThemes(house);
        const targetTheme = this._getHouseThemes(pos);
        
        if (house === pos) return `**Insight:** Ultimate stability in ${sourceTheme.toLowerCase()}. Your soul has mastered this domain over many lifetimes.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** Supreme karma in ${sourceTheme.toLowerCase()} is resolved through intense transformation, service, or letting go.`;
        
        return `**Insight:** The ultimate energy of your life flows from ${sourceTheme.toLowerCase()} toward ${targetTheme.toLowerCase()}, linking your final results across these domains.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const d60PlanetMatrix = {
            Jupiter: {
                1: "The signature of a 'Grand Soul.' You are protected by supreme wisdom and find luck through ethical living.",
                9: "Maximum auspiciousness and divine grace. Your path is cleared of major obstacles through dharmic merit."
            },
            Sun: {
                1: "A soul here for powerful leadership and self-realization. You possess a transparent and authoritative character.",
                10: "Ultimate professional recognition and honor. Your deeds are illuminated by your soul's purpose."
            },
            Saturn: {
                12: "The end of a major karmic cycle. You find spiritual liberation through discipline, solitude, and letting go."
            }
        };

        const result = d60PlanetMatrix[planet]?.[house];
        if (result) return result;

        return `${I18n.t('planets.' + planet)} in the ${this._formatHouse(house)} of D60 influences your ${this._getHouseThemes(house).toLowerCase()}, defining your ultimate karmic results.`;
    }

    _getHouseThemes(h) {
        return ['', 'Supreme Soul Persona', 'Karmic Values', 'Karmic Effort', 'Ultimate Peace', 'Moral Logic', 'Service Karma', 'Soul Partnerships', 'Deep Transformation', 'Supreme Fortune', 'Final Actions', 'Ultimate Gains', 'Karmic Release'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'active leadership and visionary initiatives that burn through old karmic patterns.',
            Earth: 'building reliable foundations and practical routines to ground your soul\'s ultimate purpose.',
            Air: 'strategic communication, networking, and the sharing of wisdom to expand your karmic reach.',
            Water: 'trusting your intuition and bringing deep empathy and emotional purification to your final results.'
        };
        return advice[element] || 'maintaining balance in your final destiny.';
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
            key: 'D60',
            name: VARGA_INFO['D60'].name,
            desc: VARGA_INFO['D60'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}
export default new D60Analyzer();
