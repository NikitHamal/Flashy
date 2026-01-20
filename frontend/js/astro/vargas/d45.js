import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

class D45Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D45', 'Sun');
    }

    analyzeCoreSignificance(data) {
        const lagnaName = I18n.t('rasis.' + data.lagna.sign);
        const lordName = I18n.t('planets.' + data.lagna.lord);
        const lagnaKeywords = I18n.t('analysis.keywords.' + data.lagna.sign);

        let narrative = `### Character Integrity and Moral Conduct\n\n`;
        narrative += `The Akshavedamsha (D45) chart provides a deep look into your character, your moral conduct, and the underlying integrity of your soul. While earlier charts show what you *do* or *have*, D45 shows who you *are* at the most foundational level. With **${lagnaName} rising in D45**, your core character and approach to ethical questions are characterized by ${lagnaKeywords}.\n\n`;

        narrative += `**Integrity Ruler (L45 Lord):** The ruler of your foundational character, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This suggests that your sense of honor and integrity is most significantly tested and refined through **${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}**.\n\n`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        return narrative;
    }

    analyzeHouseLordDynamics(data) {
        let narrative = `### Pillars of Conduct and Ethical Matrix\n\n`;
        narrative += `The connections in D45 define how your inner character interacts with various life domains to produce your overall reputation and moral standing.\n\n`;

        const priorityHouses = [1, 9, 10, 4, 5, 2, 11, 7, 3, 6, 8, 12];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);

            narrative += `**${I18n.n(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}\n`;
            
            // Insight Card
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` The exaltation of this lord indicates a high level of nobility and unshakeable integrity in this area of life.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` Vulnerability here suggests that you must be extra vigilant in maintaining your ethical standards regarding these matters.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Behavioral Archetypes and Moral Style\n\n`;
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
        let narrative = `### Specialized Character Insights\n\n`;
        
        // Sun (Karaka for Soul/Integrity) & Jupiter (Karaka for Ethics)
        const sunHouse = this._getPlanetHouse(data, 'Sun');
        const jupHouse = this._getPlanetHouse(data, 'Jupiter');
        
        if (sunHouse) {
            narrative += `**Soul's Moral Core:** The Sun is in your ${this._formatHouse(sunHouse)} and Jupiter is in your ${this._formatHouse(jupHouse)}. `;
            if ([1, 4, 7, 10, 5, 9].includes(sunHouse) && !data.vargaChart.planets.Sun.isCombust) {
                narrative += `The Sun's strong placement in D45 grants you a natural sense of honor and a transparent character that earns the respect of others.\n\n`;
            } else {
                narrative += `The Sun's influence indicates that your character is forged through overcoming personal shadows and achieving self-mastery.\n\n`;
            }
        }

        if (jupHouse && [1, 5, 9, 2, 11].includes(jupHouse)) {
            narrative += `Jupiter's influence provides a strong ethical foundation and a commitment to dharmic principles throughout your life.\n\n`;
        }

        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Trajectory of Reputation and Character Success\n\n`;

        const l10 = data.houseLords[10];
        const l1 = data.houseLords[1];
        
        narrative += `**Long-term Reputation (Kirti):**\n`;
        if (this.kendras.includes(l10.placedInHouse) || this.trikonas.includes(l10.placedInHouse)) {
            narrative += `Your honorable deeds and consistent character will lead to a lasting positive reputation and professional respect.\n\n`;
        } else {
            narrative += `Your reputation is built quietly through reliable conduct and specialized expertise. You value inner integrity over external fame.\n\n`;
        }

        narrative += `**Innate Ethical Strength:**\n`;
        if (l1.dignity === 'Exalted' || l1.dignity === 'Own Sign' || this.trikonas.includes(l1.placedInHouse)) {
            narrative += `You possess an unshakeable moral compass. Even in difficult circumstances, your core integrity remains your greatest asset.\n\n`;
        } else {
            narrative += `Your ethical strength is a result of conscious learning and refinement. You gain character by analyzing your experiences and choosing the higher path.\n\n`;
        }

        return narrative;
    }

    getPersonalizedAdvice(data) {
        let advice = `**Guidance for Character Refinement:**\n`;
        const l1 = data.houseLords[1];
        
        if (this.dusthanas.includes(l1.placedInHouse)) {
            advice += `• Your primary life task is to maintain your moral center in the face of competitive or challenging environments. True integrity is proven in the shadows, not the light.\n`;
        }
        
        advice += `• Align your conduct with the qualities of ${I18n.t('rasis.' + data.lagna.sign)}, focusing on ${this._getElementalAdvice(this._getElement(data.lagna.sign))}`;

        return advice;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const d45Matrix = {
            1: {
                1: "Integrity is innate. You are a self-governing individual with a strong sense of personal honor and consistency.",
                9: "Character is built on wisdom and ethical study. You find your moral center through higher learning and spiritual truth.",
                10: "Your character is your career. You are destined for roles where integrity and public trust are paramount."
            },
            9: {
                1: "Your personality is deeply dharmic. You carry the ethical merits of your ancestors and find luck through righteous conduct.",
                10: "Ethical deeds lead to professional success. Your career thrives because of your reputation for honesty."
            }
        };

        const result = d45Matrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        const sourceTheme = this._getHouseThemes(house);
        const targetTheme = this._getHouseThemes(pos);
        
        if (house === pos) return `**Insight:** Stability in ${sourceTheme.toLowerCase()}. Your character traits in this area are foundational and unshakeable.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** Integrity in ${sourceTheme.toLowerCase()} is refined through overcoming personal tests or serving those in need.`;
        
        return `**Insight:** Your moral energy flows from ${sourceTheme.toLowerCase()} toward ${targetTheme.toLowerCase()}, showing how your character influences these domains.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const d45PlanetMatrix = {
            Sun: {
                1: "A transparent and honorable character. You lead by example and value truth above all else.",
                10: "Your soul's purpose is tied to honorable leadership and maintaining high standards in your profession."
            },
            Jupiter: {
                9: "A master of ethical conduct. You serve as a moral compass for others and find wisdom through dharmic living."
            },
            Saturn: {
                1: "A disciplined and serious character. You are known for your reliability, endurance, and sense of duty."
            }
        };

        const result = d45PlanetMatrix[planet]?.[house];
        if (result) return result;

        return `${I18n.t('planets.' + planet)} in the ${this._formatHouse(house)} of D45 influences your ${this._getHouseThemes(house).toLowerCase()}, defining your style of conduct.`;
    }

    _getHouseThemes(h) {
        return ['', 'Character Persona', 'Ethical Values', 'Moral Courage', 'Inner Integrity', 'Wise Conduct', 'Character Tests', 'Relational Honor', 'Transformative Conduct', 'Philosophical Roots', 'Honorable Deeds', 'Gains through Integrity', 'Ethical Release'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'pioneering moral leadership and maintaining a visionary, enthusiastic commitment to your truths.',
            Earth: 'building reliable foundations for your conduct and focusing on tangible, long-term ethical consistency.',
            Air: 'leveraging strategic communication, intellectual clarity, and networking to share and refine your values.',
            Water: 'trusting your intuition and bringing deep emotional empathy and purification to your moral choices.'
        };
        return advice[element] || 'maintaining balance in your conduct.';
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
            key: 'D45',
            name: VARGA_INFO['D45'].name,
            desc: VARGA_INFO['D45'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}
export default new D45Analyzer();
