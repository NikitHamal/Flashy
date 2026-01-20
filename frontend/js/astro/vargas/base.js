import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

class BaseVargaAnalyzer {
    constructor(key, defaultKaraka) {
        this.key = key;
        this.karaka = defaultKaraka;
        this.signs = [
            'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
            'Tula', 'Vrishchika', 'Dhanu', 'Makara', 'Kumbha', 'Meena'
        ];
        this.rulers = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter'];
        this.kendras = [1, 4, 7, 10];
        this.trikonas = [1, 5, 9];
        this.dusthanas = [6, 8, 12];
        this.upachayas = [3, 6, 10, 11];
        this.dhanaHouses = [2, 5, 9, 11];
    }

    /**
     * Primary entry point for analysis. 
     * Prepares a rich data object so subclasses (and future AI agents) 
     * have everything they need in one place.
     */
    analyze(vargaChart, ctx) {
        const { profile, chart: d1Chart } = ctx;
        const info = VARGA_INFO[this.key];
        
        // 1. Prepare User Context
        const birthDate = new Date(profile.datetime);
        const age = new Date().getFullYear() - birthDate.getFullYear();
        const gender = profile.gender || 'male';

        // 2. Prepare Varga Specifics
        const lagnaSignIdx = vargaChart.lagna.rasi.index;
        const lagnaSignName = this.signs[lagnaSignIdx];
        const lagnaLord = this.rulers[lagnaSignIdx];
        
        // 3. Assemble complete data package for the analyzer
        const vargaData = {
            key: this.key,
            name: info.name,
            description: info.desc,
            gender: gender,
            age: age,
            lifeStage: age < 25 ? 'Youth' : (age < 60 ? 'Adult' : 'Senior'),
            isYouth: age < 25,
            isAdult: age >= 25 && age < 60,
            isSenior: age >= 60,
            
            // Charts
            vargaChart: vargaChart, // The positions in THIS divisional chart
            d1Chart: d1Chart,       // The positions in the root Birth Chart (D1)
            
            // Core Components
            lagna: {
                sign: lagnaSignName,
                signIndex: lagnaSignIdx,
                lord: lagnaLord,
                lordHouse: 0, // Set below
                lordDignity: 'Neutral' // Set below
            },
            karaka: {
                name: this.karaka,
                house: 0, // Set below
                dignity: 'Neutral' // Set below
            },
            
            // Computed Analysis
            dignities: this._getDignities(vargaChart.planets),
            houseLords: this._getHouseLords(vargaChart, lagnaSignIdx),
            patterns: this._getHousePatterns(vargaChart, lagnaSignIdx)
        };

        // Set Lord and Karaka specifics safely
        const lordPos = vargaChart.planets[vargaData.lagna.lord];
        if (lordPos && lordPos.rasi) {
            vargaData.lagna.lordHouse = this._getHouse(lagnaSignIdx, lordPos.rasi.index);
            vargaData.lagna.lordDignity = this._getDignity(vargaData.lagna.lord, lordPos.rasi.index);
        }

        const karakaPos = vargaChart.planets[vargaData.karaka.name];
        if (karakaPos && karakaPos.rasi) {
            vargaData.karaka.house = this._getHouse(lagnaSignIdx, karakaPos.rasi.index);
            vargaData.karaka.dignity = this._getDignity(vargaData.karaka.name, karakaPos.rasi.index);
        }

        // 4. Generate Narrative using modular methods
        let narrative = '';
        
        narrative += this.analyzeCoreSignificance(vargaData);
        narrative += this.analyzePlanetaryInfluences(vargaData);
        narrative += this.analyzeAdvancedYogaLogic(vargaData);
        narrative += this.generatePredictions(vargaData);
        
        // Add personalized section
        const advice = this.getPersonalizedAdvice(vargaData);
        if (advice) {
            narrative += `

### ${I18n.t('analysis.recommendation')}
${advice}`;
        }

        return {
            key: this.key,
            name: info.name,
            desc: info.desc,
            lagna: I18n.t('rasis.' + lagnaSignName),
            lord: I18n.t('planets.' + lagnaLord),
            analysis: narrative.trim()
        };
    }

    /**
     * HOOKS FOR SUBCLASSES / AI AGENTS
     * These are intended to be overwritten with deep insights.
     */

    analyzeCoreSignificance(data) {
        let n = I18n.t('vargas.intro_pattern', {
            chart: data.name,
            desc: data.description,
            lagna: I18n.t('rasis.' + data.lagna.sign)
        }) + ' ';

        n += I18n.t('vargas.lord_pattern', {
            lord: I18n.t('planets.' + data.lagna.lord),
            house: I18n.n(data.lagna.lordHouse),
            effect: this._getPlacementEffect(data.lagna.lordHouse)
        }) + ' ';

        return n;
    }

    analyzePlanetaryInfluences(data) {
        let n = '';
        if (data.dignities.exalted.length > 0) {
            n += `

### ${I18n.t('kundali.exalted')}
`;
            n += I18n.t('vargas.planets_exalted', { planets: data.dignities.exalted.map(p => I18n.t('planets.' + p)).join(', ') }) + ' ';
        }
        if (data.dignities.debilitated.length > 0) {
            n += `

### ${I18n.t('kundali.debilitated')}
`;
            n += I18n.t('vargas.planets_debilitated', { planets: data.dignities.debilitated.map(p => I18n.t('planets.' + p)).join(', ') }) + ' ';
        }
        return n;
    }

    analyzeHouseLordDynamics(data) {
        let n = `### Inter-House Dynamics\n\n`;
        const housesToAnalyze = [1, 2, 4, 5, 7, 9, 10, 11]; // Core pillars
        
        housesToAnalyze.forEach(h => {
            const info = data.houseLords[h];
            const sourceTitle = this._getHouseTitle(h);
            const targetTitle = this._getHouseTitle(info.placedInHouse);

            n += `**${sourceTitle} ➔ ${targetTitle}**\n`;
            n += `The ruler of your ${sourceTitle.toLowerCase()} (${I18n.t('planets.' + info.planet)}) is situated in the ${targetTitle.toLowerCase()}. `;
            
            n += this._getLordInHouseDescription(h, info.placedInHouse, info.planet);
            n += `\n\n`;
        });
        
        return n;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const sourceName = this._getHouseTitle(house);
        const targetName = this._getHouseTitle(pos);
        
        if (house === pos) return `Insight: The lord of ${sourceName.toLowerCase()} is in its own house, ensuring the final results of this area are stable and high-quality.`;
        
        if ([6, 8, 12].includes(pos)) {
            return `Insight: The manifestation of your ${sourceName.toLowerCase()} is linked to a challenging area. This suggests that the final results here come after a period of internal transformation or focused service.`;
        }

        return `Insight: The energy of your ${sourceName.toLowerCase()} flows into the area of ${targetName.toLowerCase()}, linking these two domains of your life path.`;
    }

    analyzeAdvancedYogaLogic(data) {
        let n = '';
        if (data.patterns.kendraBenefics.length > 0) {
            n += `

${I18n.t('vargas.benefics_favorable', { planets: data.patterns.kendraBenefics.map(p => I18n.t('planets.' + p)).join(', ') })} `;
        }
        return n;
    }

    generatePredictions(data) {
        return ''; // Deeply specific to each chart
    }

    getPersonalizedAdvice(data) {
        return I18n.t('vargas.advice.generic');
    }

    // =========================================================================
    // INTERNAL HELPERS
    // =========================================================================

    _getHouse(lagnaIdx, planetIdx) {
        return ((planetIdx - lagnaIdx + 12) % 12) + 1;
    }

    _getPlanetHouse(data, planet) {
        const pos = data.vargaChart.planets[planet];
        if (!pos || !pos.rasi) return null;
        return this._getHouse(data.lagna.signIndex, pos.rasi.index);
    }

    _evaluateLordPlacement(house, pos) {
        if (house === pos) return 'optimal (own house)';
        if (this.kendras.includes(pos)) return 'strong (Kendra)';
        if (this.trikonas.includes(pos)) return 'auspicious (Trikona)';
        if (this.dusthanas.includes(pos)) return 'challenging (Dusthana)';
        if (this.upachayas.includes(pos)) return 'growth-oriented (Upachaya)';
        return 'neutral';
    }

    _getDignity(planet, signIdx) {
        if (this._isExalted(planet, signIdx)) return 'Exalted';
        if (this._isDebilitated(planet, signIdx)) return 'Debilitated';
        if (this._isOwnSign(planet, signIdx)) return 'Own Sign';
        return 'Neutral';
    }

    _getDignities(planets) {
        const res = { exalted: [], debilitated: [], own: [] };
        ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'].forEach(p => {
            const pos = planets[p];
            if (pos && pos.rasi) {
                const sIdx = pos.rasi.index;
                if (this._isExalted(p, sIdx)) res.exalted.push(p);
                else if (this._isDebilitated(p, sIdx)) res.debilitated.push(p);
                else if (this._isOwnSign(p, sIdx)) res.own.push(p);
            }
        });
        return res;
    }

    _getHouseLords(vargaChart, lagnaIdx) {
        const lords = {};
        for (let h = 1; h <= 12; h++) {
            const signIdx = (lagnaIdx + h - 1) % 12;
            const lord = this.rulers[signIdx];
            const pos = vargaChart.planets[lord];
            
            lords[h] = {
                planet: lord,
                placedInHouse: (pos && pos.rasi) ? this._getHouse(lagnaIdx, pos.rasi.index) : 0,
                dignity: (pos && pos.rasi) ? this._getDignity(lord, pos.rasi.index) : 'Neutral'
            };
        }
        return lords;
    }

    _getHousePatterns(vargaChart, lagnaSignIdx) {
        const kendraBenefics = [];
        const dusthanaMalefics = [];
        const naturalBenefics = ['Jupiter', 'Venus', 'Mercury', 'Moon'];
        const naturalMalefics = ['Mars', 'Saturn', 'Rahu', 'Ketu', 'Sun'];

        ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'].forEach(p => {
            const pos = vargaChart.planets[p];
            if (pos && pos.rasi) {
                const h = this._getHouse(lagnaSignIdx, pos.rasi.index);
                if ([1, 4, 7, 10, 5, 9].includes(h) && naturalBenefics.includes(p)) kendraBenefics.push(p);
                if ([6, 8, 12].includes(h) && naturalMalefics.includes(p)) dusthanaMalefics.push(p);
            }
        });

        return { kendraBenefics, dusthanaMalefics };
    }

    _getPlacementEffect(house) {
        if ([1, 4, 7, 10].includes(house)) return I18n.t('vargas.effects.kendra');
        if ([5, 9].includes(house)) return I18n.t('vargas.effects.trikona');
        if ([6, 8, 12].includes(house)) return I18n.t('vargas.effects.dusthana');
        if ([2, 11].includes(house)) return I18n.t('vargas.effects.dhana');
        return I18n.t('vargas.effects.neutral');
    }

    _isExalted(planet, signIdx) {
        const exaltation = { Sun: 0, Moon: 1, Mars: 9, Mercury: 5, Jupiter: 3, Venus: 11, Saturn: 6 };
        return exaltation[planet] === signIdx;
    }

    _isDebilitated(planet, signIdx) {
        const debilitation = { Sun: 6, Moon: 7, Mars: 3, Mercury: 11, Jupiter: 9, Venus: 5, Saturn: 0 };
        return debilitation[planet] === signIdx;
    }

    _isOwnSign(planet, signIdx) {
        const ownership = {
            Sun: [4], Moon: [3], Mars: [0, 7], Mercury: [2, 5],
            Jupiter: [8, 11], Venus: [1, 6], Saturn: [9, 10]
        };
        return ownership[planet] && ownership[planet].includes(signIdx);
    }

    _getHouseTitle(h) {
        const key = 'h' + h;
        const themes = {
            h1: "Self and Identity",
            h2: "Wealth and Family",
            h3: "Courage and Communication",
            h4: "Home and Happiness",
            h5: "Intelligence and Children",
            h6: "Service and Challenges",
            h7: "Partnerships and Marriage",
            h8: "Longevity and Transformation",
            h9: "Wisdom and Fortune",
            h10: "Career and Reputation",
            h11: "Gains and Social Circles",
            h12: "Spirituality and Liberation"
        };
        return themes[key];
    }

    _formatHouse(h) {
        const suffixes = ["st", "nd", "rd", "th", "th", "th", "th", "th", "th", "th", "th", "th"];
        return I18n.n(h) + (suffixes[h - 1] || "th") + " house";
    }
}

export default BaseVargaAnalyzer;