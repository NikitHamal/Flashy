import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

class D16Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D16', 'Venus');
    }

    analyzeCoreSignificance(data) {
        const lagnaName = I18n.t('rasis.' + data.lagna.sign);
        const lordName = I18n.t('planets.' + data.lagna.lord);
        const lagnaKeywords = I18n.t('analysis.keywords.' + data.lagna.sign);

        let narrative = `### Vehicles, Luxuries, and General Comforts\n\n`;
        narrative += `The Shodashamsha (D16) chart represents your overall life comforts, your destiny regarding vehicles, and the pleasure you derive from material luxuries. With **${lagnaName} rising in D16**, your relationship with pleasure and physical comfort is characterized by ${lagnaKeywords}. This chart determines the "Quality of Living" you experience.\n\n`;

        narrative += `**Comfort Ruler (L16 Lord):** The ruler of your comfort persona, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This shows that your enjoyment of material comforts and vehicles is primarily channeled through **${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}**.\n\n`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        return narrative;
    }

    analyzeHouseLordDynamics(data) {
        let narrative = `### Pillars of Comfort and Material Joy\n\n`;
        narrative += `The connections in D16 define your capacity to enjoy life's pleasures and the ease with which you acquire luxuries.\n\n`;

        const priorityHouses = [4, 1, 11, 2, 5, 9, 10, 7, 8, 12, 6, 3];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);

            narrative += `**${I18n.n(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}\n`;
            
            // Insight Card
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` This area of luxury is amplified by natural grace, promising high-quality comforts and aesthetic pleasure.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` Challenges in this area suggest that your sense of comfort may require conscious moderation or overcome initial hurdles.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Luxury and Aesthetic Enjoyment Analysis\n\n`;
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
        let narrative = `### Specialized Luxury Insights\n\n`;
        
        // Venus (Karaka for Luxuries and Vehicles)
        const venHouse = this._getPlanetHouse(data, 'Venus');
        if (!venHouse) return narrative;
        
        narrative += `**Venus's Influence on Comfort:** Venus is in your ${this._formatHouse(venHouse)}. `;
        if ([1, 4, 7, 10, 5, 9, 11].includes(venHouse) && !data.vargaChart.planets.Venus.isCombust) {
            narrative += `This is a supreme signature for D16, indicating natural access to high-end vehicles, aesthetic living spaces, and profound material enjoyment.\n\n`;
        } else {
            narrative += `This suggests that your enjoyment of luxury is tied more to intellectual or spiritual pursuits rather than pure material display.\n\n`;
        }

        const l4 = data.houseLords[4];
        if (l4.dignity === 'Exalted' || l4.dignity === 'Own Sign') {
            narrative += `**Strong Vehicle Potential:** A powerful 4th lord in D16 is an excellent indicator of owning reliable and prestigious vehicles throughout life.\n\n`;
        }

        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Comfort and Pleasure Trajectory Predictions\n\n`;

        const l4 = data.houseLords[4];
        const l11 = data.houseLords[11];
        
        narrative += `**Acquisition of Vehicles and Properties:**\n`;
        if (this.kendras.includes(l4.placedInHouse) || this.trikonas.includes(l4.placedInHouse)) {
            narrative += `You are likely to experience significant ease in acquiring properties and vehicles that enhance your social status.\n\n`;
        } else {
            narrative += `Your acquisition of luxuries requires disciplined saving and focused effort. You find joy in well-earned material rewards.\n\n`;
        }

        narrative += `**Overall Life Satisfaction:**\n`;
        if (this.kendras.includes(l11.placedInHouse) || this.trikonas.includes(l11.placedInHouse)) {
            narrative += `Your life is blessed with consistent comforts and the ability to fulfill your material desires with relative ease.\n\n`;
        } else {
            narrative += `Your life satisfaction is built through specialized experiences and finding beauty in the simple, refined details of daily life.\n\n`;
        }

        return narrative;
    }

    getPersonalizedAdvice(data) {
        let advice = `**Actionable Guidance for Comfort:**\n`;
        const l4 = data.houseLords[4];
        
        if (this.dusthanas.includes(l4.placedInHouse)) {
            advice += `• To enhance your comforts, focus on gratitude and maintaining your vehicles and home with extra care. Material ease follows internal appreciation.\n`;
        }
        
        advice += `• Your material joy is best cultivated by aligning your lifestyle with the qualities of ${I18n.t('rasis.' + data.lagna.sign)}, focusing on ${this._getElementalAdvice(this._getElement(data.lagna.sign))}`;

        return advice;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const d16Matrix = {
            1: {
                1: "Comfort is self-actualized. You possess a clear sense of what brings you joy and don't rely on external trends to define your luxury.",
                4: "Domestic happiness and vehicles are the core pillars of your identity. Your soul finds its greatest peace in a refined home environment.",
                11: "Natural magnet for gains and social luxuries. Your personality attracts networks that provide access to high-end experiences."
            },
            4: {
                1: "Your identity is deeply tied to your vehicles and domestic luxury. You are a natural connoisseur of the 'good life.'",
                4: "Unshakeable material security. You possess an innate mastery over creating comfortable and aesthetic spaces.",
                11: "Vehicles and luxuries lead to significant social gains. Your refined taste is a source of prosperity."
            }
        };

        const result = d16Matrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        const sourceTheme = this._getHouseThemes(house);
        const targetTheme = this._getHouseThemes(pos);
        
        if (house === pos) return `**Insight:** Stability in ${sourceTheme.toLowerCase()}. Your comforts in this area are well-protected and reliable.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** Enjoyment of ${sourceTheme.toLowerCase()} requires internal balance or overcoming hurdles before it manifests fully.`;
        
        return `**Insight:** Your life's pleasure regarding comfort flows from ${sourceTheme.toLowerCase()} toward ${targetTheme.toLowerCase()}, linking your luxuries with these domains.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const d16PlanetMatrix = {
            Venus: {
                4: "Excellent for luxury vehicles and aesthetic home environments. You surround yourself with beauty, comfort, and grace.",
                1: "You have a natural internal sense of refinement and aesthetic pleasure that influences all your fortunes."
            },
            Jupiter: {
                4: "Abundant domestic peace and wise investment in properties. Your home is a place of wisdom and protected comfort.",
                11: "Vast gains and social luxuries through wise conduct and ethical networking."
            },
            Mercury: {
                4: "Intelligent enjoyment of comforts. You find joy in learning and strategic communication within your domestic life."
            }
        };

        const result = d16PlanetMatrix[planet]?.[house];
        if (result) return result;

        return `${I18n.t('planets.' + planet)} in the ${this._formatHouse(house)} of D16 influences your ${this._getHouseThemes(house).toLowerCase()}, defining your sense of luxury.`;
    }

    _getHouseThemes(h) {
        return ['', 'Comfort Persona', 'Financial Joy', 'Drive/Effort', 'Vehicles/Home', 'Creative Pleasure', 'Service/Health', 'Partnerships', 'Transformation', 'General Fortune', 'Status/Action', 'Gains/Networks', 'Inner Release'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'active leadership in acquiring luxuries and maintaining a visionary, optimistic outlook on life comforts.',
            Earth: 'building reliable foundations for your material life and focusing on tangible long-term aesthetic assets.',
            Air: 'leveraging communication, strategic information, and networking to expand your access to high-end experiences.',
            Water: 'trusting your intuition and bringing empathy and emotional depth to your home and inner sense of pleasure.'
        };
        return advice[element] || 'maintaining balance in your comforts.';
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
            key: 'D16',
            name: VARGA_INFO['D16'].name,
            desc: VARGA_INFO['D16'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}

export default new D16Analyzer();