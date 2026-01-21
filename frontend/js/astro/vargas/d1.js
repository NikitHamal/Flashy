import BaseVargaAnalyzer from './base.js';
import I18n from '../../core/i18n.js';
import { VARGA_INFO } from '../varga_data.js';

class D1Analyzer extends BaseVargaAnalyzer {
    constructor() {
        super('D1', 'Sun');
        this.functionalBenefics = {
            Aries: ['Sun', 'Moon', 'Jupiter'], Taurus: ['Saturn', 'Mercury', 'Venus'],
            Gemini: ['Venus', 'Saturn'], Cancer: ['Mars', 'Jupiter', 'Moon'],
            Leo: ['Mars', 'Jupiter', 'Sun'], Virgo: ['Venus', 'Mercury'],
            Libra: ['Saturn', 'Mercury', 'Venus'], Scorpio: ['Jupiter', 'Moon', 'Sun'],
            Sagittarius: ['Sun', 'Mars', 'Jupiter'], Capricorn: ['Venus', 'Mercury', 'Saturn'],
            Aquarius: ['Venus', 'Mars', 'Saturn'], Pisces: ['Moon', 'Mars', 'Jupiter']
        };
        this.functionalMalefics = {
            Aries: ['Mercury', 'Saturn', 'Venus'], Taurus: ['Jupiter', 'Moon', 'Mars'],
            Gemini: ['Mars', 'Jupiter', 'Sun'], Cancer: ['Saturn', 'Venus', 'Mercury'],
            Leo: ['Saturn', 'Venus', 'Mercury'], Virgo: ['Mars', 'Moon', 'Jupiter'],
            Libra: ['Sun', 'Mars', 'Jupiter'], Scorpio: ['Mercury', 'Venus', 'Saturn'],
            Sagittarius: ['Saturn', 'Venus', 'Mercury'], Capricorn: ['Mars', 'Moon', 'Jupiter'],
            Aquarius: ['Moon', 'Mercury', 'Jupiter'], Pisces: ['Sun', 'Saturn', 'Venus', 'Mercury']
        };
    }

    analyzeCoreSignificance(data) {
        const lagnaName = I18n.t('rasis.' + data.lagna.sign);
        const lordName = I18n.t('planets.' + data.lagna.lord);
        const lagnaKeywords = I18n.t('analysis.keywords.' + data.lagna.sign);

        let narrative = `### Core Personality and Life Path Framework\n\n`;
        narrative += `The Ascendant (Lagna) is the most critical point in your chart, representing your physical constitution, innate temperament, and the lens through which you experience life. With **${lagnaName} rising**, you are naturally ${lagnaKeywords}. This sign establishes the fundamental tone of your entire existence.\n\n`;

        const elementType = this._getElement(data.lagna.sign);
        const modalityType = this._getModality(data.lagna.sign);
        narrative += `Your Lagna belongs to the **${elementType} element** and is of **${modalityType} modality**, indicating ${this._getElementModDescription(elementType, modalityType)}.\n\n`;

        narrative += `**Lagna Lord Analysis:** The ruler of your Ascendant, **${lordName}**, is positioned in the **${this._formatHouse(data.lagna.lordHouse)}**. This placement is ${this._evaluateLordPlacement(1, data.lagna.lordHouse)} and directs your life force toward ${this._getHouseThemes(data.lagna.lordHouse).toLowerCase()}.\n\n`;
        narrative += this._getLordInHouseDescription(1, data.lagna.lordHouse, data.lagna.lord) + "\n\n";

        const moonPos = data.vargaChart.planets.Moon;
        if (moonPos && moonPos.rasi) {
            const moonSign = this.signs[moonPos.rasi.index];
            const moonHouse = this._getPlanetHouse(data, 'Moon');
            narrative += `**Mind and Emotional Nature:** Your Moon is placed in **${I18n.t('rasis.' + moonSign)}** in the **${this._formatHouse(moonHouse)}**. `;
            narrative += this._getMoonAnalysis(moonSign, moonHouse, data) + "\n\n";
        }

        const sunPos = data.vargaChart.planets.Sun;
        if (sunPos && sunPos.rasi) {
            const sunHouse = this._getPlanetHouse(data, 'Sun');
            const sunSign = this.signs[sunPos.rasi.index];
            narrative += `**Soul Purpose (Atmakaraka Sun):** Your Sun illuminates the **${this._formatHouse(sunHouse)}** from **${I18n.t('rasis.' + sunSign)}**, `;
            narrative += this._getSunPurposeAnalysis(sunHouse, sunSign, data) + "\n\n";
        }

        return narrative;
    }


    analyzeHouseLordDynamics(data) {
        let narrative = `### Inter-House Dynamics and Life Pillars\n\n`;
        narrative += `The placement of house lords creates the intricate web of karma that defines your destiny. Each lord carries the significations of its house to another domain, creating cause-and-effect relationships across life themes.\n\n`;

        const priorityHouses = [1, 2, 4, 5, 7, 9, 10, 11, 6, 8, 12, 3];

        for (const h of priorityHouses) {
            const lordInfo = data.houseLords[h];
            const lordName = I18n.t('planets.' + lordInfo.planet);
            const sourceTheme = this._getHouseThemes(h);
            const targetTheme = this._getHouseThemes(lordInfo.placedInHouse);
            const evaluation = this._evaluateLordPlacement(h, lordInfo.placedInHouse);

            narrative += `**${I18n.n(h)}${this._getOrdinal(h)} Lord (${sourceTheme}):** ${lordName} → ${this._formatHouse(lordInfo.placedInHouse)}\n`;
            narrative += `This ${evaluation} placement connects ${sourceTheme.toLowerCase()} with ${targetTheme.toLowerCase()}. `;

            // Insight Card (Separated)
            narrative += `\n\n` + this._getLordInHouseDescription(h, lordInfo.placedInHouse, lordInfo.planet);

            if (lordInfo.dignity === 'Exalted') {
                narrative += ` Being exalted, this lord delivers exceptional results with minimal effort.`;
            } else if (lordInfo.dignity === 'Debilitated') {
                narrative += ` The debilitation indicates challenges that become strengths through conscious effort after age 28-32.`;
            } else if (lordInfo.dignity === 'Own') {
                narrative += ` Placed in own sign, this lord provides stable, self-sustaining results.`;
            }

            const aspects = this._getPlanetaryAspects(data, lordInfo.planet, lordInfo.placedInHouse);
            if (aspects.length > 0) {
                narrative += ` This lord receives aspects from ${aspects.join(', ')}, modifying its expression.`;
            }
            narrative += `\n\n`;
        }
        return narrative;
    }

    analyzePlanetaryInfluences(data) {
        let narrative = `### Planetary Functions and Behavioral Archetypes\n\n`;
        const planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
        const lagnaSign = data.lagna.sign;

        planets.forEach(p => {
            const houseNum = this._getPlanetHouse(data, p);
            if (!houseNum) return;

            const pos = data.vargaChart.planets[p];
            const signName = this.signs[pos.rasi.index];
            const planetName = I18n.t('planets.' + p);
            const houseTitle = this._formatHouse(houseNum) + ' (' + I18n.t('rasis.' + signName) + ')';
            const isFunctionalBenefic = this.functionalBenefics[lagnaSign]?.includes(p);
            const isFunctionalMalefic = this.functionalMalefics[lagnaSign]?.includes(p);

            narrative += `**Placement of ${planetName} in the ${houseTitle}:** `;
            narrative += `Functional nature: ${isFunctionalBenefic ? 'Benefic' : isFunctionalMalefic ? 'Malefic' : 'Neutral'} for ${lagnaSign} Lagna. `;
            narrative += this._getPlanetInHouseDescription(p, houseNum, signName, data);

            const dignity = this._getDignity(p, pos.rasi.index);
            if (dignity !== 'Neutral') {
                narrative += ` **Dignity:** ${dignity} - ${this._getDignityEffect(dignity, p)}.`;
            }

            if (pos.speed < 0) {
                narrative += ` **Retrograde:** ${planetName}'s energy is internalized and intensified, indicating karmic revisitation of ${this._getHouseThemes(houseNum).toLowerCase()} matters from past lives.`;
            }

            if (pos.isCombust && p !== 'Sun') {
                narrative += ` **Combust:** The soul's ego (Sun) overshadows ${planetName}'s external expression, requiring inner cultivation of its qualities.`;
            }
            narrative += `\n\n`;
        });

        if (data.vargaChart.planets.Rahu) {
            narrative += this._analyzeNodes(data);
        }
        return narrative;
    }

    analyzeAdvancedYogaLogic(data) {
        let narrative = `### Yoga Analysis (Planetary Combinations)\n\n`;
        const yogas = [];

        const rajaYogas = this._detectRajaYogas(data);
        if (rajaYogas.length > 0) {
            yogas.push({ category: 'Raja Yoga (Power & Status)', items: rajaYogas });
        }

        const dhanaYogas = this._detectDhanaYogas(data);
        if (dhanaYogas.length > 0) {
            yogas.push({ category: 'Dhana Yoga (Wealth)', items: dhanaYogas });
        }

        const panchangaYogas = this._detectPanchangaYogas(data);
        if (panchangaYogas.length > 0) {
            yogas.push({ category: 'Panchanga Yogas', items: panchangaYogas });
        }

        const negativeYogas = this._detectNegativeYogas(data);
        if (negativeYogas.length > 0) {
            yogas.push({ category: 'Challenging Combinations', items: negativeYogas });
        }

        const specialYogas = this._detectSpecialYogas(data);
        if (specialYogas.length > 0) {
            yogas.push({ category: 'Special Yogas', items: specialYogas });
        }

        if (yogas.length === 0) {
            narrative += `Your chart shows a balanced configuration without extreme yogas, indicating steady progress through consistent effort.\n\n`;
        } else {
            yogas.forEach(category => {
                narrative += `**${category.category}:**\n`;
                category.items.forEach(yoga => {
                    narrative += `• **${yoga.name}:** ${yoga.description}\n`;
                });
                narrative += `\n`;
            });
        }
        return narrative;
    }

    generatePredictions(data) {
        let narrative = `### Life Path Trajectory and Predictions\n\n`;

        const chartStrength = this._assessChartStrength(data);
        narrative += `**Destiny Pattern Assessment:** ${chartStrength.summary}\n\n`;

        narrative += `**Career Trajectory (10th House Analysis):**\n`;
        const l10 = data.houseLords[10];
        const tenthPlanets = this._getPlanetsInHouse(data, 10);
        narrative += this._getCareerPrediction(l10, tenthPlanets, data) + `\n\n`;

        narrative += `**Wealth Accumulation (2nd & 11th House Analysis):**\n`;
        narrative += this._getWealthPrediction(data) + `\n\n`;

        narrative += `**Relationship Dynamics (7th House Analysis):**\n`;
        narrative += this._getRelationshipPrediction(data) + `\n\n`;

        narrative += `**Health Constitution (Lagna & 6th House Analysis):**\n`;
        narrative += this._getHealthPrediction(data) + `\n\n`;

        narrative += `**Spiritual Evolution (9th & 12th House Analysis):**\n`;
        narrative += this._getSpiritualPrediction(data) + `\n`;

        return narrative;
    }

    getPersonalizedAdvice(data) {
        const weakAreas = [];
        const strongAreas = [];

        for (let h = 1; h <= 12; h++) {
            const lordInfo = data.houseLords[h];
            if (this.dusthanas.includes(lordInfo.placedInHouse) || lordInfo.dignity === 'Debilitated') {
                weakAreas.push({ house: h, theme: this._getHouseThemes(h), reason: lordInfo.dignity === 'Debilitated' ? 'debilitated lord' : 'lord in dusthana' });
            }
            if ((this.kendras.includes(lordInfo.placedInHouse) || this.trikonas.includes(lordInfo.placedInHouse)) &&
                (lordInfo.dignity === 'Exalted' || lordInfo.dignity === 'Own')) {
                strongAreas.push({ house: h, theme: this._getHouseThemes(h) });
            }
        }

        let advice = '';
        if (strongAreas.length > 0) {
            advice += `**Leverage Your Strengths:** Focus on ${strongAreas.slice(0, 3).map(a => a.theme).join(', ')} where you have natural advantages. These areas will yield results with minimal friction.\n\n`;
        }

        if (weakAreas.length > 0) {
            advice += `**Address Challenges:** ${weakAreas.slice(0, 2).map(a => `${a.theme} (${a.reason})`).join('; ')} require conscious effort. `;
            advice += `Remedial measures include strengthening the respective lords through gemstones, mantras, or charitable acts aligned with those planets.\n\n`;
        }

        const lagnaElement = this._getElement(data.lagna.sign);
        advice += `**Elemental Balance:** As a ${lagnaElement} sign native, ${this._getElementalAdvice(lagnaElement)}`;

        return advice;
    }

    _detectRajaYogas(data) {
        const yogas = [];
        const kendraLords = [1, 4, 7, 10].map(h => data.houseLords[h].planet);
        const trikonaLords = [5, 9].map(h => data.houseLords[h].planet);

        for (const kLord of kendraLords) {
            for (const tLord of trikonaLords) {
                const kPos = this._getPlanetHouse(data, kLord);
                const tPos = this._getPlanetHouse(data, tLord);

                if (kPos && tPos && kPos === tPos) {
                    yogas.push({
                        name: 'Kendra-Trikona Raja Yoga',
                        description: `${I18n.t('planets.' + kLord)} (Kendra lord) conjoins ${I18n.t('planets.' + tLord)} (Trikona lord) in the ${this._formatHouse(kPos)}, bestowing authority, recognition, and rise in status during their combined Dashas.`
                    });
                }
            }
        }

        const l9 = data.houseLords[9].planet;
        const l10 = data.houseLords[10].planet;
        const pos9 = this._getPlanetHouse(data, l9);
        const pos10 = this._getPlanetHouse(data, l10);

        if (pos9 && pos10 && (pos9 === pos10 || pos9 === 10 || pos10 === 9)) {
            yogas.push({
                name: 'Dharma-Karma Adhipati Yoga',
                description: `The lords of fortune (9th) and action (10th) are connected, creating one of the most powerful combinations for professional success, leadership, and lasting legacy.`
            });
        }

        const jupPos = this._getPlanetHouse(data, 'Jupiter');
        if (jupPos && this.kendras.includes(jupPos)) {
            yogas.push({
                name: 'Hamsa Yoga (Pancha Mahapurusha)',
                description: `Jupiter in Kendra bestows wisdom, ethics, good fortune, and respect from learned individuals. You attract opportunities through righteousness.`
            });
        }

        return yogas;
    }

    _detectDhanaYogas(data) {
        const yogas = [];
        const l2 = data.houseLords[2];
        const l11 = data.houseLords[11];
        const l5 = data.houseLords[5];
        const l9 = data.houseLords[9];

        if ([2, 5, 9, 11].includes(l2.placedInHouse) && [2, 5, 9, 11].includes(l11.placedInHouse)) {
            yogas.push({
                name: 'Dhana Yoga',
                description: `Lords of 2nd and 11th are well-placed, indicating strong wealth accumulation potential and multiple income sources.`
            });
        }

        if (l5.placedInHouse === l9.placedInHouse || l5.placedInHouse === 9 || l9.placedInHouse === 5) {
            yogas.push({
                name: 'Lakshmi Yoga',
                description: `Connection between 5th and 9th lords creates fortune through intelligence, speculation, and divine grace. Wealth comes through righteous means.`
            });
        }

        const jupHouse = this._getPlanetHouse(data, 'Jupiter');
        const venHouse = this._getPlanetHouse(data, 'Venus');
        if (jupHouse && venHouse && jupHouse === venHouse && [1, 2, 5, 9, 11].includes(jupHouse)) {
            yogas.push({
                name: 'Guru-Shukra Yoga',
                description: `Jupiter and Venus conjunction in an auspicious house indicates abundant wealth, luxury, and material comforts.`
            });
        }

        return yogas;
    }

    _detectPanchangaYogas(data) {
        const yogas = [];
        const sunHouse = this._getPlanetHouse(data, 'Sun');
        const moonHouse = this._getPlanetHouse(data, 'Moon');

        if (sunHouse && moonHouse && (Math.abs(sunHouse - moonHouse) === 6 || sunHouse + moonHouse === 13)) {
            yogas.push({ name: 'Purnima/Amavasya Born', description: `Born near Full/New Moon, intensifying lunar influence on mind and emotions.` });
        }

        if (moonHouse && this.kendras.includes(moonHouse) && !data.vargaChart.planets.Moon.isCombust) {
            yogas.push({ name: 'Sunapha/Anapha/Durudhara', description: `Moon supported by planetary positions, providing mental stability and resourcefulness.` });
        }

        return yogas;
    }

    _detectNegativeYogas(data) {
        const yogas = [];
        const l8 = data.houseLords[8];
        const l12 = data.houseLords[12];

        if (l8.placedInHouse === 1 || l12.placedInHouse === 1) {
            yogas.push({
                name: 'Viparita Energy on Lagna',
                description: `A dusthana lord influences the self, creating periodic upheavals that ultimately lead to spiritual growth and resilience.`
            });
        }

        const satHouse = this._getPlanetHouse(data, 'Saturn');
        const moonHouse = this._getPlanetHouse(data, 'Moon');
        if (satHouse && moonHouse && satHouse === moonHouse) {
            yogas.push({
                name: 'Punarphoo (Sade-Sati indicator)',
                description: `Saturn conjoins Moon, indicating periods of emotional discipline and delayed but stable mental development.`
            });
        }

        return yogas;
    }

    _detectSpecialYogas(data) {
        const yogas = [];
        const planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
        const houseOccupancy = {};

        planets.forEach(p => {
            const h = this._getPlanetHouse(data, p);
            if (h) houseOccupancy[h] = (houseOccupancy[h] || 0) + 1;
        });

        Object.entries(houseOccupancy).forEach(([house, count]) => {
            if (count >= 4) {
                yogas.push({
                    name: 'Sannyasa Yoga',
                    description: `${count} planets congregate in the ${this._formatHouse(parseInt(house))}, creating intense focus on that life area with potential for renunciation or single-pointed pursuit.`
                });
            }
        });

        const mercHouse = this._getPlanetHouse(data, 'Mercury');
        const jupHouse = this._getPlanetHouse(data, 'Jupiter');
        if (mercHouse && jupHouse && mercHouse === jupHouse) {
            yogas.push({
                name: 'Budh-Aditya/Guru-Budh Yoga',
                description: `Mercury-Jupiter conjunction bestows exceptional intelligence, communication skills, and success in education, writing, or advisory roles.`
            });
        }

        return yogas;
    }

    _getLordInHouseDescription(house, pos, planet) {
        const lordMatrix = {
            1: {
                1: "Self-Mastery position. Strong constitution, clear identity, and self-directed success. You are the architect of your own fortune.",
                2: "Identity through values and speech. Wealth accumulation becomes central to self-expression. Family traditions shape personality.",
                3: "Courage and communication define you. Restless energy seeks expression through skills, writing, or sibling relationships.",
                4: "Identity rooted in emotional security. Strong maternal influence. Physical health mirrors domestic happiness.",
                5: "Creative genius placement. Intelligence, children, and speculation bring self-actualization. Natural leadership abilities.",
                6: "Problem-solver identity. Life involves overcoming obstacles, which builds tremendous resilience and service orientation.",
                7: "Identity through relationships. Partnership-oriented existence. Success through collaboration and public dealings.",
                8: "Transformative life path. Interest in mysteries, research, and psychology. Multiple life reinventions.",
                9: "Dharmic soul. Fortune through ethics, higher learning, and spiritual pursuits. Blessed by teachers and mentors.",
                10: "Career-defined existence. Public recognition and professional achievement are inseparable from identity.",
                11: "Social visionary. Identity through networks, friendships, and collective goals. Natural prosperity magnetism.",
                12: "Spiritual seeker. Success in foreign lands or through seclusion. Rich inner life, possible institutional connections."
            },
            2: {
                1: "Self-effort generates wealth. Your personality is your primary asset. Strong speech and family values.",
                2: "Exceptional wealth placement. Natural resource management. Strong family lineage and accumulated wisdom.",
                3: "Income through communication, writing, or siblings. Multiple smaller income streams over one large source.",
                4: "Property and real estate generate wealth. Mother's influence on finances. Domestic comfort is priority.",
                5: "Speculative wealth. Earnings through creativity, children's success, or investment. Intelligence monetized.",
                6: "Wealth through service industries, healthcare, or overcoming debts. Initial struggles lead to financial discipline.",
                7: "Partnership brings wealth. Spouse contributes financially. Business partnerships favored.",
                8: "Sudden wealth through inheritance, insurance, or spouse's resources. Financial transformations.",
                9: "Fortune through ethics, teaching, or foreign connections. Luck plays role in prosperity.",
                10: "Income through profession and status. Government or corporate earnings. Recognition brings wealth.",
                11: "Primary wealth signature. Multiple income sources. Social network generates opportunity.",
                12: "Foreign earnings or institutional income. High expenses balanced by unconventional earning capacity."
            },
            5: {
                1: "Creative intelligence shapes personality. Children bring joy. Natural teacher and speculator.",
                5: "Powerful Poorvapunya. Past-life merits active. Strong creative output and intelligent children.",
                7: "Romance through partnerships. Creative collaborations. Children influence relationships.",
                9: "Supreme fortune yoga. Wisdom from children. Teaching lineage. Spiritual creativity.",
                10: "Career in creative fields. Recognition for intelligence. Children influence profession.",
                11: "Gains through creativity and speculation. Intelligent social circle. Children bring prosperity."
            },
            7: {
                1: "Partnership defines personality. Diplomatic nature. Success through collaboration.",
                4: "Spouse brings domestic happiness. Business from home. Partner influences property.",
                7: "Strong partnership karma. Prominent spouse. Public dealing success.",
                9: "Fortunate marriage. Spouse is dharmic. Partner brings wisdom and luck.",
                10: "Spouse influences career. Business partnerships. Public recognition through relationships.",
                12: "Foreign spouse possible. Relationship requires adjustment. Partner connected to institutions."
            },
            9: {
                1: "Dharmic personality. Natural luck and wisdom. Father's positive influence. Ethical core.",
                5: "Supreme fortune. Wise children. Teaching abilities. Speculative luck.",
                9: "Fortified fortune. Strong father. Spiritual inclinations. Long-distance success.",
                10: "Career built on ethics. Recognition for wisdom. Father influences profession."
            },
            10: {
                1: "Career-driven personality. Leadership destiny. Public figure potential.",
                9: "Ethical career. Recognition for righteousness. Professional success through wisdom.",
                10: "Administrative excellence. Top position destiny. Powerful professional karma.",
                11: "Profitable career. Professional success brings gains. Ambitious goal achievement."
            }
        };

        const result = lordMatrix[house]?.[pos];
        if (result) return `**Insight:** ${result}`;

        if (house === pos) return `**Insight:** Self-sustaining ${this._getHouseThemes(house).toLowerCase()}. Natural mastery over this life domain. Stable, self-directed results in this area.`;
        if (this.dusthanas.includes(pos)) return `**Insight:** ${this._getHouseThemes(house)} requires overcoming obstacles. Challenges in the ${this._formatHouse(pos)} must be addressed before ${this._getHouseThemes(house).toLowerCase()} flourishes. Character-building placement.`;
        if (this.kendras.includes(pos)) return `**Insight:** ${this._getHouseThemes(house)} becomes prominent through the foundational ${this._formatHouse(pos)}. Active, visible expression of these themes. Cannot be ignored.`;
        if (this.trikonas.includes(pos)) return `**Insight:** Fortunate flow from ${this._getHouseThemes(house).toLowerCase()} to ${this._getHouseThemes(pos).toLowerCase()}. Dharmic support between these life areas. Meritorious combination.`;

        return `**Insight:** Energy flows from ${this._getHouseThemes(house).toLowerCase()} to ${this._getHouseThemes(pos).toLowerCase()}. These life areas support each other. Progress in one advances the other.`;
    }

    _getPlanetInHouseDescription(planet, house, sign, data) {
        const planetHouseMatrix = {
            Sun: {
                1: "Powerful presence, leadership aura, strong vitality. Guard against ego dominance. Authority comes naturally.",
                2: "Values-driven, authoritative speech, family pride. Wealth through status. Father influences finances.",
                3: "Courageous communicator, leader among peers. Success through initiative. Powerful self-expression.",
                4: "Heart centered in home. Seeks prominent domestic life. Inner authority. Government property possible.",
                5: "Creative brilliance, solar connection to children, recognition for intelligence. Speculation success.",
                6: "Competitive victor. Shines in challenging environments. Health generally robust. Service leadership.",
                7: "Seeks powerful partner. Ego balance in relationships needed. Public authority. Partner may be prominent.",
                8: "Transformation seeker. Research and hidden knowledge attract. Life direction shifts. Occult interests.",
                9: "Wisdom beacon. Ethical authority. Strong father. Travel for purpose. Teaching and mentoring.",
                10: "Career pinnacle placement. Destined for authority. Government or leadership roles. Maximum visibility.",
                11: "Influential network. Leadership in groups. Gains through authority. Social prominence.",
                12: "Internalized power. Foreign connections. Institutional leadership. Spiritual authority. Behind-scenes influence."
            },
            Moon: {
                1: "Sensitive, intuitive, publicly appealing. Fluctuating energy. Maternal nature. Adaptable personality.",
                2: "Emotional security through wealth. Pleasant speech. Family attachment. Fluctuating finances.",
                3: "Artistic communication. Sibling closeness. Short travels satisfy. Imaginative mind.",
                4: "Moon's joy. Deep maternal bond. Emotional fulfillment through home. Natural nurturer.",
                5: "Emotional creativity. Strong children connection. Intuitive speculation. Romantic nature.",
                6: "Service orientation. Emotional investment in work. Health tied to stress. Caring professional.",
                7: "Emotional partnerships. Public connection. Partner fluctuations. Relationship-dependent mood.",
                8: "Psychic depth. Emotional transformations. Hidden matters attract. Research intuition.",
                9: "Spiritual emotions. Wisdom seeking. Mother is guide. Emotional peace through philosophy.",
                10: "Public career. Popular appeal. Caring profession. Status fluctuates but recovers.",
                11: "Wide friend circle. Emotional gains. Women support success. Network-dependent happiness.",
                12: "Rich inner world. Solitude satisfies. Foreign residence possible. Spiritual emotions."
            },
            Jupiter: {
                1: "Wisdom embodied. Ethical nature. Natural respect. Optimistic outlook. Blessed existence.",
                2: "Wealthy speech. Family wisdom. Financial growth. Teaching lineage. Values expansion.",
                3: "Courageous wisdom. Fortunate siblings. Publishing success. Ethical communication.",
                4: "Domestic blessing. Property expansion. Educational home. Happiness through wisdom.",
                5: "Supreme intelligence. Blessed children. Teaching excellence. Speculation fortune.",
                6: "Service wisdom. Victory over enemies. Healthcare success. Debt resolution ability.",
                7: "Fortunate marriage. Wise partner. Business blessing. Legal success.",
                8: "Occult wisdom. Inheritance possible. Longevity. Research depth. Transformation guide.",
                9: "Dharma embodied. Maximum fortune. Guru quality. Long-distance blessing. Father's wisdom.",
                10: "Career blessing. Ethical leadership. Respected profession. Advisory success.",
                11: "Gains magnified. Fortunate network. Goal achievement. Elder sibling blessing.",
                12: "Spiritual liberation. Foreign fortune. Institutional wisdom. Meditation success."
            },
            Saturn: {
                1: "Disciplined personality. Mature outlook. Slow but lasting success. Responsibility-oriented.",
                2: "Careful wealth building. Speech measured. Family duties. Delayed but stable finances.",
                3: "Endurance in efforts. Structured communication. Sibling responsibilities. Skill mastery.",
                4: "Domestic responsibilities. Property through effort. Mother needs care. Late domestic peace.",
                5: "Delayed children or serious children. Disciplined creativity. Cautious speculation.",
                6: "Enemy victory. Service excellence. Health through discipline. Debt repayment ability.",
                7: "Mature partner. Delayed or serious marriage. Business discipline. Partnership duties.",
                8: "Longevity indicator. Research patience. Transformation through discipline. Hidden work.",
                9: "Practical wisdom. Late father blessing. Structured spirituality. Dharmic duty.",
                10: "Career excellence through time. Administrative rise. Government favor. Lasting authority.",
                11: "Delayed but massive gains. Serious network. Older friends. Goal achievement through patience.",
                12: "Spiritual discipline. Institutional work. Foreign difficulties then success. Solitude growth."
            }
        };

        const fallbackPlanetMatrix = {
            Mars: { kendras: "Dynamic action and energy directed toward visible achievements.", trikonas: "Fortunate courage and initiative.", dusthanas: "Competitive victories but health vigilance needed." },
            Mercury: { kendras: "Intellectual prominence and communication success.", trikonas: "Intelligent fortune and creative business.", dusthanas: "Analytical problem-solving abilities." },
            Venus: { kendras: "Relationship harmony and aesthetic success.", trikonas: "Fortunate pleasures and creative wealth.", dusthanas: "Relationship challenges teaching value and discrimination." }
        };

        const result = planetHouseMatrix[planet]?.[house];
        if (result) return result;

        if (fallbackPlanetMatrix[planet]) {
            if (this.kendras.includes(house)) return fallbackPlanetMatrix[planet].kendras;
            if (this.trikonas.includes(house)) return fallbackPlanetMatrix[planet].trikonas;
            if (this.dusthanas.includes(house)) return fallbackPlanetMatrix[planet].dusthanas;
        }

        return `${planet}'s energy influences ${this._getHouseThemes(house).toLowerCase()}, blending planetary significations with house themes.`;
    }

    _analyzeNodes(data) {
        const rahuHouse = this._getPlanetHouse(data, 'Rahu');
        const ketuHouse = this._getPlanetHouse(data, 'Ketu');

        let narrative = '';
        if (rahuHouse) {
            narrative += `**Rahu** (North Node) in ${this._formatHouse(rahuHouse)}:\n`;
            narrative += `Your soul's growth direction is toward ${this._getHouseThemes(rahuHouse).toLowerCase()}. Rahu amplifies desires and creates obsessive focus here, indicating areas requiring conscious development this lifetime.\n\n`;
        }

        if (ketuHouse) {
            narrative += `**Ketu** (South Node) in ${this._formatHouse(ketuHouse)}:\n`;
            narrative += `Past-life mastery exists in ${this._getHouseThemes(ketuHouse).toLowerCase()}. Ketu brings detachment and spiritual insight here, suggesting you already possess inherent wisdom in these matters but must learn non-attachment.\n\n`;
        }

        return narrative;
    }

    _getMoonAnalysis(sign, house, data) {
        const element = this._getElement(sign);
        return `This gives you a ${element.toLowerCase()}-based emotional nature, processing feelings through ${element === 'Fire' ? 'action and enthusiasm' : element === 'Earth' ? 'practical stability' : element === 'Air' ? 'intellectual analysis' : 'deep intuition'}. The ${this._formatHouse(house)} placement means your emotional security is tied to ${this._getHouseThemes(house).toLowerCase()}.`;
    }

    _getSunPurposeAnalysis(house, sign, data) {
        return `indicating your soul's purpose involves ${this._getHouseThemes(house).toLowerCase()}. The Sun here demands authentic expression through these themes, and suppressing this area creates existential dissatisfaction.`;
    }

    _assessChartStrength(data) {
        let strength = 0;
        const factors = [];

        if (data.dignities.exalted.length >= 1) { strength += 2; factors.push('exalted planets'); }
        if (data.dignities.own.length >= 2) { strength += 2; factors.push('planets in own sign'); }
        if (data.dignities.debilitated.length >= 2) { strength -= 2; factors.push('debilitated planets requiring attention'); }

        const l1House = data.lagna.lordHouse;
        if (this.kendras.includes(l1House) || this.trikonas.includes(l1House)) { strength += 2; factors.push('well-placed lagna lord'); }

        if (strength >= 4) return { summary: `High-vibration destiny chart with ${factors.join(', ')}. Natural authority and reduced obstacles. Positive karma manifesting.` };
        if (strength <= -2) return { summary: `Spiritual warrior path with ${factors.join(', ')}. Challenges become wisdom. Greatest success after Saturn return (age 28-30).` };
        return { summary: `Balanced configuration with ${factors.length > 0 ? factors.join(', ') : 'steady planetary positions'}. Consistent effort yields proportional results. Middle-path life trajectory.` };
    }

    _getCareerPrediction(l10, tenthPlanets, data) {
        let pred = `The 10th lord ${I18n.t('planets.' + l10.planet)} in ${this._formatHouse(l10.placedInHouse)} `;
        if (this.kendras.includes(l10.placedInHouse)) pred += `indicates prominent, visible career with authority positions. `;
        else if (this.trikonas.includes(l10.placedInHouse)) pred += `suggests fortunate career with ethical foundations. `;
        else if (this.dusthanas.includes(l10.placedInHouse)) pred += `indicates career through service, healing, or overcoming industry challenges. `;
        else pred += `creates unique professional path based on ${this._getHouseThemes(l10.placedInHouse).toLowerCase()} themes. `;

        if (tenthPlanets.length > 0) pred += `With ${tenthPlanets.map(p => I18n.t('planets.' + p)).join(', ')} in the 10th, expect ${tenthPlanets.includes('Saturn') ? 'slow but steady rise' : tenthPlanets.includes('Jupiter') ? 'respected position' : tenthPlanets.includes('Sun') ? 'leadership roles' : 'dynamic career evolution'}.`;
        return pred;
    }

    _getWealthPrediction(data) {
        const l2 = data.houseLords[2];
        const l11 = data.houseLords[11];
        let pred = '';

        if (this.dhanaHouses.includes(l2.placedInHouse) || this.dhanaHouses.includes(l11.placedInHouse)) {
            pred = `Strong wealth yoga present. Lords of 2nd and 11th favorably placed indicate natural wealth magnetism and multiple income sources. Financial growth expected throughout life.`;
        } else if (this.dusthanas.includes(l2.placedInHouse) && this.dusthanas.includes(l11.placedInHouse)) {
            pred = `Wealth requires disciplined approach. Initial financial challenges build budgetary wisdom. Success through debt management, service industries, or inheritance.`;
        } else {
            pred = `Moderate wealth configuration. Steady accumulation through consistent effort. Avoid speculation; focus on reliable income sources.`;
        }
        return pred;
    }

    _getRelationshipPrediction(data) {
        const l7 = data.houseLords[7];
        const venusHouse = this._getPlanetHouse(data, 'Venus');

        let pred = `7th lord in ${this._formatHouse(l7.placedInHouse)} indicates ${this.kendras.includes(l7.placedInHouse) ? 'prominent partnership role' : this.trikonas.includes(l7.placedInHouse) ? 'fortunate relationship karma' : this.dusthanas.includes(l7.placedInHouse) ? 'relationship lessons requiring maturity' : 'partnership themes connected to ' + this._getHouseThemes(l7.placedInHouse).toLowerCase()}. `;
        if (venusHouse) {
            pred += `Venus in ${this._formatHouse(venusHouse)} ${venusHouse === 7 ? 'strongly supports marriage happiness' : this.dusthanas.includes(venusHouse) ? 'requires conscious relationship investment' : 'influences relationship style'}.`;
        }
        return pred;
    }

    _getHealthPrediction(data) {
        const l1Dignity = data.houseLords[1].dignity;
        const l6 = data.houseLords[6];

        let pred = `Lagna lord ${l1Dignity !== 'Neutral' ? l1Dignity.toLowerCase() : 'neutral'} indicates ${l1Dignity === 'Exalted' ? 'robust constitution' : l1Dignity === 'Debilitated' ? 'health requiring attention' : 'average vitality'}. `;
        pred += `6th lord in ${this._formatHouse(l6.placedInHouse)} ${this.dusthanas.includes(l6.placedInHouse) ? 'neutralizes disease potential' : this.kendras.includes(l6.placedInHouse) ? 'indicates health-conscious lifestyle needed' : 'suggests manageable health karma'}.`;
        return pred;
    }

    _getSpiritualPrediction(data) {
        const l9 = data.houseLords[9];
        const l12 = data.houseLords[12];
        const jupHouse = this._getPlanetHouse(data, 'Jupiter');

        let pred = `9th lord in ${this._formatHouse(l9.placedInHouse)} shapes your dharmic path through ${this._getHouseThemes(l9.placedInHouse).toLowerCase()}. `;
        pred += `12th lord placement indicates ${this.trikonas.includes(l12.placedInHouse) ? 'natural spiritual inclination' : this.kendras.includes(l12.placedInHouse) ? 'active spiritual practice' : 'gradual spiritual awakening'}. `;
        if (jupHouse) {
            pred += `Jupiter in ${this._formatHouse(jupHouse)} ${this.trikonas.includes(jupHouse) ? 'strongly supports spiritual growth' : 'guides wisdom development'}.`;
        }
        return pred;
    }

    _getPlanetsInHouse(data, house) {
        const planets = [];
        ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'].forEach(p => {
            if (this._getPlanetHouse(data, p) === house) planets.push(p);
        });
        return planets;
    }

    _getPlanetaryAspects(data, planet, house) {
        const aspects = [];
        ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'].forEach(p => {
            if (p === planet) return;
            const pHouse = this._getPlanetHouse(data, p);
            if (!pHouse) return;
            const diff = ((house - pHouse + 12) % 12) || 12;
            if (diff === 7) aspects.push(I18n.t('planets.' + p));
            if (p === 'Mars' && (diff === 4 || diff === 8)) aspects.push(I18n.t('planets.' + p));
            if (p === 'Jupiter' && (diff === 5 || diff === 9)) aspects.push(I18n.t('planets.' + p));
            if (p === 'Saturn' && (diff === 3 || diff === 10)) aspects.push(I18n.t('planets.' + p));
        });
        return aspects;
    }



    _getDignityEffect(dignity, planet) {
        const effects = {
            'Exalted': `${planet}'s significations flourish effortlessly`,
            'Debilitated': `${planet}'s themes require conscious cultivation`,
            'Own Sign': `${planet} operates with natural authority`
        };
        return effects[dignity] || '';
    }

    _getHouseThemes(h) {
        return ['', 'Self/Identity', 'Wealth/Family', 'Courage/Siblings', 'Home/Mother', 'Intelligence/Children', 'Service/Health', 'Partnership/Marriage', 'Transformation/Longevity', 'Dharma/Fortune', 'Career/Status', 'Gains/Networks', 'Liberation/Losses'][h] || '';
    }

    _getElement(sign) {
        const elements = { Aries: 'Fire', Leo: 'Fire', Sagittarius: 'Fire', Taurus: 'Earth', Virgo: 'Earth', Capricorn: 'Earth', Gemini: 'Air', Libra: 'Air', Aquarius: 'Air', Cancer: 'Water', Scorpio: 'Water', Pisces: 'Water' };
        return elements[sign] || 'Unknown';
    }

    _getModality(sign) {
        const modalities = { Aries: 'Cardinal', Cancer: 'Cardinal', Libra: 'Cardinal', Capricorn: 'Cardinal', Taurus: 'Fixed', Leo: 'Fixed', Scorpio: 'Fixed', Aquarius: 'Fixed', Gemini: 'Mutable', Virgo: 'Mutable', Sagittarius: 'Mutable', Pisces: 'Mutable' };
        return modalities[sign] || 'Unknown';
    }

    _getElementModDescription(element, modality) {
        const desc = {
            'Fire-Cardinal': 'pioneering initiative and leadership drive',
            'Fire-Fixed': 'sustained willpower and creative determination',
            'Fire-Mutable': 'adaptable enthusiasm and philosophical expansion',
            'Earth-Cardinal': 'practical ambition and material initiative',
            'Earth-Fixed': 'persistent accumulation and sensory stability',
            'Earth-Mutable': 'analytical adaptability and service orientation',
            'Air-Cardinal': 'relationship initiative and social leadership',
            'Air-Fixed': 'fixed ideas and humanitarian determination',
            'Air-Mutable': 'intellectual versatility and communicative adaptability',
            'Water-Cardinal': 'emotional initiative and nurturing leadership',
            'Water-Fixed': 'emotional depth and transformative intensity',
            'Water-Mutable': 'intuitive adaptability and spiritual sensitivity'
        };
        return desc[`${element}-${modality}`] || 'balanced elemental expression';
    }

    _getElementalAdvice(element) {
        const advice = {
            Fire: 'channel your natural enthusiasm through structured goals. Avoid burnout through regular rest. Physical activity is essential for balance.',
            Earth: 'trust your practical instincts but remain open to change. Material security supports your wellbeing. Nature connection grounds your energy.',
            Air: 'your ideas need grounding through action. Social connection is vital but ensure quality over quantity. Mental rest prevents overthinking.',
            Water: 'honor your emotional intelligence without drowning in feelings. Creative expression processes emotions. Boundaries protect your sensitivity.'
        };
        return advice[element] || 'maintain balance across all life areas.';
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
            gender: profile.gender || 'male',
            age,
            lagna: {
                signIndex: lagnaSignIdx,
                sign: this.signs[lagnaSignIdx],
                lord: this.rulers[lagnaSignIdx],
                lordHouse: 0 // Set below
            },
            houseLords: this._getHouseLords(vargaChart, lagnaSignIdx),
            dignities: this._getDignities(vargaChart.planets),
            karaka: { house: 0 }, // Set below
            patterns: this._getHousePatterns(vargaChart, lagnaSignIdx)
        };

        data.lagna.lordHouse = this._getPlanetHouse(data, data.lagna.lord);
        data.karaka.house = this._getPlanetHouse(data, this.karaka);

        let report = '';
        report += this.analyzeCoreSignificance(data);
        report += this.analyzeHouseLordDynamics(data);
        report += this.analyzePlanetaryInfluences(data);
        report += this.analyzeAdvancedYogaLogic(data);
        report += this.generatePredictions(data);

        const advice = this.getPersonalizedAdvice(data);
        if (advice) report += `\n\n### Personalized Recommendations\n${advice}`;

        return {
            key: 'D1',
            name: VARGA_INFO['D1'].name,
            desc: VARGA_INFO['D1'].desc,
            lagna: I18n.t('rasis.' + data.lagna.sign),
            lord: I18n.t('planets.' + data.lagna.lord),
            analysis: report.trim()
        };
    }
}

export default new D1Analyzer();