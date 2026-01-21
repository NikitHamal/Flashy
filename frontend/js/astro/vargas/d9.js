import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

class D9Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D9', 'Venus');
    }

    analyzeCoreSignificance(data) {
        const lagnaName = I18n.t('rasis.' + data.lagna.sign);
        const lordName = I18n.t('planets.' + data.lagna.lord);
        const lagnaKeywords = I18n.t('analysis.keywords.' + data.lagna.sign);

        let narrative = `### The Soul's Purpose and Internal Strength\n\n`;
        narrative += `The Navamsha (D9) chart is the microscopic view of your soul's internal strength and the "fruitage" of your life. While D1 shows the tree, D9 shows the quality of the fruit. With **${lagnaName} rising in D9**, your inner core is characterized by ${lagnaKeywords}. This is who you are when all social masks are removed.\n\n`;

        narrative += `**Inner Self Ruler (L9 Lord):** The ruler of your Navamsha Ascendant, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This reveals that your soul's evolution and ultimate peace are found through ${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}\n\n`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        const moonPos = data.vargaChart.planets.Moon;
        if (moonPos && moonPos.rasi) {
            const moonSign = this.signs[moonPos.rasi.index];
            const moonHouseD9 = this._getPlanetHouse(data, 'Moon');
            narrative += `**Internal Emotional State:** Your Moon in Navamsha sits in **${I18n.t('rasis.' + moonSign)}** in the **${this._formatHouse(moonHouseD9)}**. This represents your true emotional contentment level. `;
            narrative += `With Moon in ${moonSign}, your inner mind processes reality through ${this._getElement(moonSign).toLowerCase()} energy.\n\n`;
        }

        return narrative;
    }

    analyzeHouseLordDynamics(data) {
        let narrative = `### Marital Destiny and Fruitage Matrix\n\n`;
        narrative += `In D9, house connections define the quality of your relationships and the strength of your internal life pillars.\n\n`;

        const priorityHouses = [7, 1, 9, 4, 5, 10, 2, 11, 8, 12, 6, 3];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);
            const evaluation = this._evaluateLordPlacement(h, lordInfo.placedInHouse);

            narrative += `**${this._getOrdinal(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}\n`;
            
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` The exaltation of this lord in D9 indicates that the fruits of this life area are exceptionally high-quality and manifest with ease.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` Debilitation here suggests internal struggles or delays in reaping the rewards of this area, often requiring significant soul-searching.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Internal Planetary Strengths\n\n`;
        const planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];

        planets.forEach(p => {
            const houseNum = this._getPlanetHouse(data, p);
            if (!houseNum) return;

            const pos = data.vargaChart.planets[p];
            const signName = this.signs[pos.rasi.index];
            const planetName = I18n.t('planets.' + p);
            
            const isVargottama = data.d1Chart.planets[p].rasi.index === pos.rasi.index;

            narrative += `**Placement of ${planetName} in the ${this._formatHouse(houseNum)} (${I18n.t('rasis.' + signName)}):** `;
            if (isVargottama) {
                narrative += `**VARGOTTAMA!** This planet is in the same sign in both D1 and D9, granting it extraordinary strength and the ability to deliver its results regardless of other afflictions. `;
            }
            
            narrative += this._getPlanetInHouseDescription(p, houseNum, signName, data);
            narrative += `\n\n`;
        });

        return narrative;
    }

    analyzeAdvancedYogaLogic(data) {
        let narrative = `### Specialized Navamsha Insights\n\n`;
        
        const pushkar = [];
        ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'].forEach(p => {
            const d1Pos = data.d1Chart.planets[p];
            const d9Pos = data.vargaChart.planets[p];
            if (!d1Pos || !d1Pos.rasi || !d9Pos || !d9Pos.rasi) return;

            const d1Rasi = d1Pos.rasi.index;
            const d9Rasi = d9Pos.rasi.index;
            let isPushkar = false;
            
            // Standard Pushkar Navamsha Signs:
            // Fire (Ar, Le, Sg) -> 7th (Libra) & 9th (Sagittarius)
            if ([0, 4, 8].includes(d1Rasi)) { 
                if ([6, 8].includes(d9Rasi)) isPushkar = true; 
            }
            // Earth (Ta, Vi, Cp) -> 3rd (Pisces) & 5th (Taurus)
            else if ([1, 5, 9].includes(d1Rasi)) { 
                if ([11, 1].includes(d9Rasi)) isPushkar = true; 
            }
            // Air (Ge, Li, Aq) -> 6th (Pisces) & 8th (Taurus)
            else if ([2, 6, 10].includes(d1Rasi)) { 
                if ([11, 1].includes(d9Rasi)) isPushkar = true; 
            }
            // Water (Cn, Sc, Pi) -> 1st (Cancer) & 3rd (Virgo)
            else if ([3, 7, 11].includes(d1Rasi)) { 
                if ([3, 5].includes(d9Rasi)) isPushkar = true; 
            }
            
            if (isPushkar) pushkar.push(I18n.t('planets.' + p));
        });

        if (pushkar.length > 0) {
            narrative += `**Pushkar Navamsha:** The planets **${pushkar.join(', ')}** are in Pushkar Navamsha. This is a highly auspicious state where the planet becomes capable of bestowing great healing, regeneration, and massive success in its Dasha.\n\n`;
        }

        const moonSignD9 = data.vargaChart.planets.Moon.rasi.index;
        const kharaSignIdx = (moonSignD9 + 7) % 12;
        const kharaLord = this.rulers[kharaSignIdx];
        narrative += `**64th Navamsha (Khara):** The ruler of your 64th Navamsha is **${I18n.t('planets.' + kharaLord)}**. In Vedic astrology, this planet represents areas of transformation and potential vulnerability. During its periods, extra caution in health and decision-making is advised.\n\n`;

        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Relationship and Inner Fulfillment Predictions\n\n`;

        const l7 = data.houseLords[7];
        const occupants7 = this._getPlanetsInHouse(data, 7);
        
        narrative += `**Marriage and Partnership Quality:**\n`;
        if (this.kendras.includes(l7.placedInHouse) || this.trikonas.includes(l7.placedInHouse)) {
            narrative += `Your 7th lord of Navamsha is well-placed, indicating that marriage will be a source of strength and internal growth. `;
        } else if (this.dusthanas.includes(l7.placedInHouse)) {
            narrative += `The 7th lord in a Dusthana suggests that relationships require conscious soul-work and may involve initial hurdles or transformational lessons. `;
        }
        
        if (occupants7.length > 0) {
            narrative += `With ${occupants7.map(p => I18n.t('planets.' + p)).join(', ')} in the 7th of D9, your spouse will strongly embody these planetary archetypes.\n\n`;
        } else {
            narrative += `The quality of your union is dictated by the ruler ${I18n.t('planets.' + l7.planet)}, suggesting a partnership based on ${this._getHouseThemes(l7.placedInHouse).toLowerCase()}.\n\n`;
        }

        narrative += `**Spiritual Strength:**\n`;
        const jupHouse = this._getPlanetHouse(data, 'Jupiter');
        if (jupHouse && [1, 5, 9, 4, 10].includes(jupHouse)) {
            narrative += `Jupiter is strongly placed in your inner chart, granting you a powerful moral compass and the ability to find wisdom in every life experience.\n`;
        } else {
            narrative += `Your spiritual growth comes through the practical application of your values in the material world.\n`;
        }

        return narrative;
    }

    getPersonalizedAdvice(data) {
        const l7 = data.houseLords[7];
        let advice = `**Navamsha Soul-Guidance:**\n`;
        
        if (l7.dignity === 'Debilitated') {
            advice += `• Strengthen your relationship karma by practicing selfless service toward your partner. Avoid being overly critical of their internal flaws.\n`;
        }
        
        const venHouse = this._getPlanetHouse(data, 'Venus');
        if (venHouse && this.dusthanas.includes(venHouse)) {
            advice += `• Venus in a complex house in D9 suggests that true happiness comes after internal purification. Meditation on beauty and harmony is recommended.\n`;
        }

        advice += `• Since your Navamsha Lagna is ${data.lagna.sign}, your internal strength is best cultivated through ${this._getElementalAdvice(this._getElement(data.lagna.sign))}`;

        return advice;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const d9Matrix = {
            1: {
                1: "Self-Vargottama influence. Strong inner character and unshakeable sense of self. Your soul knows exactly what it wants.",
                7: "Soul-mate connection potential. Your inner self is mirrored in your partner. Success through deep collaboration.",
                9: "Highly dharmic soul. You possess a natural spiritual grace that protects you during difficult times.",
                10: "Your soul finds its greatest expression through professional excellence and contribution to society."
            },
            7: {
                1: "Your identity and marital happiness are inseparable. A partner who is like a soul-double.",
                2: "Marriage brings financial stability and shared values. The spouse contributes to the family resources.",
                4: "Deep domestic peace through partnership. Your home becomes a sanctuary after marriage.",
                7: "Stable, balanced union. A self-sustaining relationship based on equality and mutual respect.",
                9: "Highly fortunate marriage. Your spouse acts as a guru or guide, bringing luck into your life.",
                10: "Marriage boosts your public status. A high-achieving partner who supports your career goals."
            }
        };

        const result = d9Matrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        const sourceTheme = this._getHouseThemes(house);
        const targetTheme = this._getHouseThemes(pos);
        
        if (house === pos) return `**Insight:** Internal stability in ${sourceTheme.toLowerCase()}. The "fruit" of this area is well-protected and reliable.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** The fruit of ${sourceTheme.toLowerCase()} requires internal transformation. Challenges here lead to profound soul-growth.`;
        
        return `**Insight:** Your soul's energy flows from ${sourceTheme.toLowerCase()} toward ${targetTheme.toLowerCase()}. These internal life areas are karmically linked.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const d9PlanetMatrix = {
            Venus: {
                1: "Natural internal charm and a soul that seeks beauty in all things. Highly attractive personality at a deep level.",
                7: "Excellent for marital harmony. You possess the internal capacity to love and be loved deeply.",
                4: "Peaceful inner world and a love for domestic comfort. A soul that finds joy in the home.",
                12: "Highly spiritual love or connections to foreign lands. A capacity for selfless devotion."
            },
            Jupiter: {
                1: "Inner wisdom and natural ethics. You are a 'guru' to yourself, always knowing the right path.",
                9: "High spiritual merit and protected fortune. Divine grace is active in your internal life.",
                5: "Creative intelligence and wisdom from past-life merits. A soul that loves to learn and teach."
            },
            Sun: {
                1: "Strong inner authority and solar vitality. A soul that is meant to lead and shine brightly.",
                10: "A destiny of high status and professional authority. Your soul finds fulfillment in being recognized."
            }
        };

        const result = d9PlanetMatrix[planet]?.[house];
        if (result) return result;

        return `${I18n.t('planets.' + planet)} in the ${this._formatHouse(house)} of D9 influences your internal ${this._getHouseThemes(house).toLowerCase()}, blending its essence with your soul's purpose.`;
    }

    _getHouseThemes(h) {
        return ['', 'Inner Self', 'Values/Assets', 'Effort/Skills', 'Peace/Home', 'Creativity/Logic', 'Obstacles/Health', 'Marriage/Partner', 'Transformation', 'Dharma/Luck', 'Status/Action', 'Gains/Networks', 'Liberation/Seclusion'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'maintaining your inner spark while grounding your enthusiasm in daily practice.',
            Earth: 'building stable internal foundations and trusting the slow process of growth.',
            Air: 'intellectual expansion and connecting with like-minded souls on a spiritual level.',
            Water: 'honoring your deep intuition and allowing your emotions to flow without judgment.'
        };
        return advice[element] || 'maintaining balance in your internal life.';
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

    _getPlanetsInHouse(data, house) {
        const planets = [];
        ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'].forEach(p => {
            if (this._getPlanetHouse(data, p) === house) planets.push(p);
        });
        return planets;
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
                lordHouse: 0 // Will be set below
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
            key: 'D9',
            name: VARGA_INFO['D9'].name,
            desc: VARGA_INFO['D9'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}

export default new D9Analyzer();
