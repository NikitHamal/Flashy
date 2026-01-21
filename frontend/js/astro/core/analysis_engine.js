import Vedic from './vedic.js';
import YogaEngine from './yogas.js';
import ShadbalaEngine from './shadbala.js';
import ManglikEngine from './manglik.js';
import AvasthaEngine from './avasthas.js';
import DashaAnalysis from './dasha_analysis.js';
import VargaAnalysis from './varga_analysis.js';
import RemediesEngine from './remedies_engine.js';
import I18n from '../core/i18n.js';
import WorkerManager from '../core/worker_manager.js';

class AnalysisEngine {
    constructor() {
        this.signs = [
            'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
            'Tula', 'Vrishchika', 'Dhanu', 'Makara', 'Kumbha', 'Meena'
        ];

        this.elements = {
            Fire: [0, 4, 8],
            Earth: [1, 5, 9],
            Air: [2, 6, 10],
            Water: [3, 7, 11]
        };

        this._workerInitialized = false;
    }

    /**
     * Initialize worker for async calculations
     * Call this once during app startup for best performance
     * @returns {Promise<boolean>} True if using worker, false if fallback
     */
    async initWorker() {
        if (!this._workerInitialized) {
            const result = await WorkerManager.init();
            this._workerInitialized = true;
            return result;
        }
        return WorkerManager.isUsingWorker();
    }

    /**
     * Set progress callback for async calculations
     * @param {Function} callback - Receives { step, total, message }
     */
    onProgress(callback) {
        WorkerManager.onProgress(callback);
    }

    /**
     * Async version of analyze that uses Web Worker for better UI performance
     * @param {Object} profile - Profile data
     * @returns {Promise<Object>} Analysis results
     */
    async analyzeAsync(profile) {
        if (!profile) return null;

        // Ensure worker is initialized
        await this.initWorker();

        const birthDate = new Date(profile.datetime);
        const location = { lat: profile.lat, lng: profile.lng };

        // Use WorkerManager for heavy calculations
        const workerResult = await WorkerManager.calculate(birthDate, location);

        const { chart: birthChart, shadbala, yogas, panchang } = workerResult;

        // Transits can be calculated in parallel or on main thread
        const now = new Date();
        const transitResult = await WorkerManager.calculateTransits(now, location);
        const transitChart = transitResult.transits;

        // Manglik calculation (lightweight, keep on main thread)
        const manglikData = this._calculateManglik(birthChart, profile);

        // Data Context for Analyzers
        const ctx = {
            profile,
            chart: birthChart,
            shadbala,
            yogas,
            panchang,
            transits: transitChart,
            manglik: manglikData,
            helpers: this._getHelpers(birthChart)
        };

        // Generate Sections (lightweight interpretations, keep on main thread)
        return {
            profile,
            chart: birthChart,
            shadbala,
            yogas,
            panchang,
            sections: {
                overview: this._analyzeOverview(ctx),
                personality: this._analyzePersonality(ctx),
                career: this._analyzeCareer(ctx),
                relationships: this._analyzeRelationships(ctx),
                wealth: this._analyzeWealth(ctx),
                dashas: this._analyzeMultiDashas(ctx),
                vargas: VargaAnalysis.analyzeAll(ctx),
                avasthas: this._analyzeAvasthas(ctx),
                lords: this._analyzeAllLords(ctx),
                remedies: this._analyzeRemedies(ctx)
            }
        };
    }

    /**
     * Synchronous analyze (original implementation for backward compatibility)
     * Use analyzeAsync for better UI performance
     */
    analyze(profile) {
        if (!profile) return null;

        const birthDate = new Date(profile.datetime);
        const location = { lat: profile.lat, lng: profile.lng };

        // 1. Core Calculations
        const birthChart = Vedic.calculate(birthDate, location);
        const shadbala = ShadbalaEngine.calculate(birthChart);
        const panchang = Vedic.calculatePanchang(birthDate, location);
        
        // Advanced: Calculate full Avasthas with Panchanag and Sun context
        const avasthaData = {
            planets: {},
            lagnaRasi: birthChart.lagna.rasi.index,
            date: birthDate,
            panchang: panchang,
            sunDistance: {}
        };
        
        const sunLon = birthChart.planets.Sun.lon;
        for (const p in birthChart.planets) {
            const pData = birthChart.planets[p];
            avasthaData.planets[p] = { 
                sign: pData.rasi.index, 
                degree: pData.rasi.degrees, 
                lon: pData.lon,
                nakshatra: pData.nakshatra
            };
            if (p !== 'Sun') {
                let dist = Math.abs(sunLon - pData.lon);
                if (dist > 180) dist = 360 - dist;
                avasthaData.sunDistance[p] = dist;
            }
        }
        
        const avasthas = AvasthaEngine.calculateChartAvasthas(avasthaData);
        
        // Pass Shadbala AND Avasthas to Yoga Engine for deeper analysis
        birthChart.shadbala = shadbala;
        birthChart.avasthas = avasthas;
        const yogas = YogaEngine.check(birthChart);

        // 2. Transits (Current Planetary Positions)
        const now = new Date();
        const transitChart = Vedic.calculate(now, location);

        // 3. Manglik Calculation
        const manglikData = this._calculateManglik(birthChart, profile);

        // 4. Data Context for Analyzers
        const ctx = {
            profile,
            chart: birthChart,
            shadbala,
            avasthas,
            yogas,
            panchang,
            transits: transitChart,
            manglik: manglikData,
            helpers: this._getHelpers(birthChart)
        };

        // 5. Generate Sections
        return {
            profile,
            chart: birthChart,
            shadbala,
            avasthas,
            yogas,
            panchang,
            sections: {
                overview: this._analyzeOverview(ctx),
                personality: this._analyzePersonality(ctx),
                career: this._analyzeCareer(ctx),
                relationships: this._analyzeRelationships(ctx),
                wealth: this._analyzeWealth(ctx),
                dashas: this._analyzeMultiDashas(ctx), // New multi-system analysis
                vargas: VargaAnalysis.analyzeAll(ctx),
                avasthas: this._analyzeAvasthas(ctx),
                lords: this._analyzeAllLords(ctx),
                remedies: this._analyzeRemedies(ctx)
            }
        };
    }

    // =========================================================================
    // SECTION ANALYZERS
    // =========================================================================

    _analyzeOverview(ctx) {
        const { chart, panchang, helpers } = ctx;
        const jaimini = chart.jaimini;
        const lagna = helpers.getSign(chart.lagna.lon);
        const moon = helpers.getSign(chart.planets.Moon.lon);
        const sun = helpers.getSign(chart.planets.Sun.lon);
        const nakshatra = I18n.t('lists.nakshatras.' + chart.planets.Moon.nakshatra.index);
        const nakshatraPada = chart.planets.Moon.nakshatra.pada;
        
        // Jaimini Atmakaraka (AK)
        const akPlanet = jaimini?.charaKarakas?.karakas?.AK?.planet;
        const akName = akPlanet ? I18n.t('planets.' + akPlanet) : '';

        // Vargottama Check
        const vargottama = [];
        ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'].forEach(p => {
            const d1 = chart.planets[p].rasi.index;
            const d9 = chart.divisionals.D9.planets[p].rasi.index;
            if (d1 === d9) vargottama.push(I18n.t('planets.' + p));
        });

        // Life Path Summary
        let summary = `
            ${I18n.t('analysis.born_under', {
            lagna: I18n.t('rasis.' + lagna.name),
            element: I18n.t('analysis.elements.' + lagna.element),
            sun: I18n.t('rasis.' + sun.name),
            moon: I18n.t('rasis.' + moon.name)
        })}
            
            ${I18n.t('analysis.birth_occurred', {
            tithi: I18n.t('lists.tithis.' + panchang.tithi.index),
            paksha: I18n.t('lists.paksha.' + panchang.tithi.paksha),
            yoga: I18n.t('lists.yogas.' + panchang.yoga.index),
            nakshatra: nakshatra,
            pada: nakshatraPada
        })}
        `;

        if (akPlanet) {
            summary += `\n\n**${I18n.t('analysis.soul_planet')}:** ${I18n.t('analysis.ak_desc', { planet: akName })}`;
        }

        if (vargottama.length > 0) {
            summary += `\n\n${I18n.t('analysis.vargottama_notably', {
                planets: vargottama.join(', '),
                verb: vargottama.length > 1 ? (I18n.getLocale() === 'ne' ? 'छन्' : 'are') : (I18n.getLocale() === 'ne' ? 'छ' : 'is')
            })}`;
        }

        return {
            title: I18n.t('analysis.overview'),
            summary: summary.trim(),
            stats: [
                { label: I18n.t('planets.Asc'), value: I18n.t('rasis.' + lagna.name) },
                { label: I18n.t('analysis.soul_planet'), value: akName },
                { label: I18n.t('panchang.nakshatra'), value: `${nakshatra} (${I18n.n(nakshatraPada)})` },
                { label: I18n.t('panchang.tithi'), value: I18n.t('lists.tithis.' + panchang.tithi.index) }
            ]
        };
    }

    _analyzePersonality(ctx) {
        const { chart, helpers, yogas } = ctx;
        const lagna = helpers.getSign(chart.lagna.lon);
        const lagnaLord = lagna.ruler;
        const lordStrength = helpers.getStrength(lagnaLord);
        const lagnaLordHouse = helpers.getHouse(chart.planets[lagnaLord].lon);
        const lagnaNakshatraIdx = chart.lagna.nakshatra.index;
        const lagnaNakshatraName = I18n.t('lists.nakshatras.' + lagnaNakshatraIdx);

        let text = I18n.t('analysis.personality_intro', {
            lagna: I18n.t('rasis.' + lagna.name),
            nakshatra: lagnaNakshatraName
        }) + ' ' + I18n.t('analysis.keywords.' + lagna.name) + '. ';

        text += `\n\n### ${I18n.t('analysis.lords')}\n`;
        text += I18n.t('analysis.ruling_planet', {
            lord: I18n.t('planets.' + lagnaLord),
            house: lagnaLordHouse
        }) + ' ';

        // Advanced: Use Deeptadi Avastha name
        const lordDeeptadi = ctx.avasthas?.[lagnaLord]?.deeptadi;
        if (lordDeeptadi) {
            text += `\n\n**${I18n.t('analysis.lord_attitude')}:** ${lordDeeptadi.name}. ${lordDeeptadi.description} `;
        }

        if (lordStrength.status === 'strong') {
            text += I18n.t('analysis.strong_lord', { lord: I18n.t('planets.' + lagnaLord) });
        } else if (lordStrength.status === 'weak') {
            text += I18n.t('analysis.weak_lord', { lord: I18n.t('planets.' + lagnaLord) });
        }

        // Element Analysis
        const balance = helpers.getElementalBalance();
        const dominant = Object.keys(balance.elements).reduce((a, b) => balance.elements[a] > balance.elements[b] ? a : b);
        text += `\n\n### ${I18n.t('analysis.elemental_constitution', { dominant: dominant, desc: '' }).split('.')[0]}\n`;
        text += I18n.t('analysis.elemental_constitution', {
            dominant: dominant,
            desc: I18n.t('analysis.element_descs.' + dominant)
        });

        // Mahapurusha Yoga check
        const mahapurusha = yogas.yogas.filter(y => y.category === 'Mahapurusha');
        if (mahapurusha.length > 0) {
            const yoga = mahapurusha[0];
            const localizedYogaName = yoga.nameKey ? I18n.t('lists.yoga_list.' + yoga.nameKey + '.name', yoga.params || {}) : yoga.name;
            const localizedYogaDesc = yoga.descriptionKey ? I18n.t('lists.yoga_list.' + yoga.descriptionKey + '.effects', yoga.params || {}) : yoga.description;

            text += `\n\n### ${I18n.t('yogas.mahapurusha')}\n`;
            text += I18n.t('analysis.special_distinction', {
                yogas: localizedYogaName,
                desc: localizedYogaDesc
            });
        }

        return {
            title: I18n.t('analysis.personality'),
            content: text,
            details: [
                { label: I18n.t('analysis.lords'), value: I18n.t('planets.' + lagnaLord) },
                { label: I18n.t('kundali.nakshatra'), value: lagnaNakshatraName },
                { label: I18n.t('analysis.shadbala'), value: I18n.t('shadbala.status.' + lordStrength.status) }
            ]
        };
    }

    _analyzeCareer(ctx) {
        const { chart, helpers, yogas } = ctx;
        const lord10 = helpers.getLordOfHouse(10);
        const lord10House = helpers.getHouse(chart.planets[lord10].lon);
        const planetsIn10 = helpers.getPlanetsInHouse(10);

        // D10 Check
        const d10Lagna = helpers.getSign(chart.divisionals.D10.lagna.lon);

        let text = I18n.t('analysis.career_intro', { lord: I18n.t('planets.' + lord10) });

        // 10th Lord Analysis
        text += I18n.t('analysis.career_placement', { lord: I18n.t('planets.' + lord10), house: lord10House }) + ' ';
        if ([6, 8, 12].includes(lord10House)) {
            text += I18n.t('analysis.career_dusthana');
        } else if ([1, 4, 7, 10].includes(lord10House)) {
            text += I18n.t('analysis.career_kendra');
        } else if ([1, 5, 9].includes(lord10House)) {
            text += I18n.t('analysis.career_trikona');
        }

        if (planetsIn10.length > 0) {
            const planetNames = planetsIn10.map(p => I18n.t('planets.' + p)).join(', ');
            text += `\n\n${I18n.t('analysis.planets_in_10', { planets: planetNames })} `;
            text += I18n.t('analysis.planet_career_influence', {
                planet: I18n.t('planets.' + planetsIn10[0]),
                career: I18n.t('analysis.planet_careers.' + planetsIn10[0])
            });
        } else {
            text += `\n\n${I18n.t('analysis.no_occupants_10', { lord: I18n.t('planets.' + lord10) })}`;
        }

        text += `\n\n**${I18n.t('vargas.D10')} (D10):** ${I18n.t('analysis.d10_intro', {
            lagna: I18n.t('rasis.' + d10Lagna.name),
            keywords: I18n.t('analysis.keywords.' + d10Lagna.name)
        })}`;

        // Sun and Saturn (Karaka) check
        const sunHouse = helpers.getHouse(chart.planets.Sun.lon);
        if (sunHouse === 10) text += ` \n\n${I18n.t('analysis.sun_10_digbala')}`;

        return {
            title: I18n.t('analysis.career'),
            content: text,
            details: [
                { label: I18n.t('vargas.D10') + ' ' + I18n.t('kundali.sign'), value: I18n.t('rasis.' + d10Lagna.name) },
                { label: I18n.t('analysis.lords'), value: I18n.t('planets.' + lord10) }
            ]
        };
    }

    _analyzeRelationships(ctx) {
        const { chart, helpers, manglik } = ctx;
        const lord7 = helpers.getLordOfHouse(7);
        const planetsIn7 = helpers.getPlanetsInHouse(7);
        const venusStrength = helpers.getStrength('Venus');
        const d9Lagna = helpers.getSign(chart.divisionals.D9.lagna.lon);

        let text = I18n.t('analysis.relationship_intro', { lord: I18n.t('planets.' + lord7) });

        if (planetsIn7.length > 0) {
            const planetNames = planetsIn7.map(p => I18n.t('planets.' + p)).join(', ');
            text += `\n\n${I18n.t('analysis.planets_in_7', { planets: planetNames })} `;
            if (planetsIn7.includes('Saturn') || planetsIn7.includes('Mars')) {
                text += I18n.t('analysis.malefics_7') + ' ';
            } else {
                text += I18n.t('analysis.spouse_nature') + ' ';
            }
        }

        let manglikDesc = manglik.description;
        if (typeof manglik.description === 'object') {
            const d = manglik.description;
            if (d.key === 'cancelled_with_reason' && d.params.descKey) {
                const p = d.params.params || {};
                if (p.signIndex) {
                    p.sign = I18n.t('rasis.' + this.signs[p.signIndex - 1]);
                }
                const localizedReason = I18n.t('analysis.manglik_rules.' + d.params.descKey, p);
                manglikDesc = I18n.t('analysis.manglik_status.cancelled_with_reason', { reason: localizedReason });
            } else if (d.key === 'present') {
                const intensityValue = d.intensity || 'None';
                const localizedIntensity = I18n.t('matching.intensities.' + intensityValue);
                manglikDesc = I18n.t('analysis.manglik_status.present', { intensity: localizedIntensity });
            } else {
                manglikDesc = I18n.t('analysis.manglik_status.' + d.key, d.params);
            }
        }

        text += `\n\n**${I18n.t('matching.manglik_analysis')}:** ${manglikDesc} `;

        text += `\n\n**${I18n.t('vargas.D9')} (D9):** ${I18n.t('analysis.d9_intro', { lagna: I18n.t('rasis.' + d9Lagna.name) })}`;

        if (manglik.recommendations && manglik.recommendations.length > 0) {
            const rec = manglik.recommendations[0];
            const localizedRec = rec.key ? I18n.t('analysis.manglik_recommendations.' + rec.key) : rec;
            text += `\n\n**${I18n.t('analysis.recommendation')}:** ${localizedRec}`;
        }

        return {
            title: I18n.t('analysis.relationships'),
            content: text,
            details: [
                { label: I18n.t('matching.manglik'), value: I18n.t('matching.intensities.' + manglik.intensity) },
                { label: I18n.t('planets.Venus'), value: I18n.t('shadbala.status.' + venusStrength.status) }
            ]
        };
    }

    _analyzeWealth(ctx) {
        const { chart, helpers, yogas } = ctx;
        const lord2 = helpers.getLordOfHouse(2);
        const lord11 = helpers.getLordOfHouse(11);
        const house2LordPos = helpers.getHouse(chart.planets[lord2].lon);
        const house11LordPos = helpers.getHouse(chart.planets[lord11].lon);

        const jupiter = helpers.getStrength('Jupiter');
        const dhanaYogas = yogas.yogas.filter(y => y.category === 'Dhana');
        
        // Advanced: Use Ashtakavarga Shuddha Pinda for wealth potential
        const jupPinda = chart.ashtakavarga?.pindas?.Jupiter?.shuddhaPinda || 0;
        const potentialScore = (jupPinda / 200) * 10; // Normalized potential

        let text = I18n.t('analysis.wealth_intro', {
            lord2: I18n.t('planets.' + lord2),
            lord11: I18n.t('planets.' + lord11)
        });

        // 2nd Lord Analysis
        text += `\n\n${I18n.t('analysis.wealth_potential', {
            lord: I18n.t('planets.' + lord2),
            house: house2LordPos
        })} `;
        
        if (jupPinda > 150) {
            text += `\n\n**${I18n.t('analysis.wealth_pinda_high')}:** ${I18n.t('analysis.pinda_wealth_desc')}`;
        }

        if ([1, 4, 7, 10, 5, 9, 11].includes(house2LordPos)) {
            text += I18n.t('analysis.wealth_kendra_trikona');
        } else if ([6, 8, 12].includes(house2LordPos)) {
            text += I18n.t('analysis.wealth_dusthana');
        }

        // 11th Lord Analysis
        text += `\n\n${I18n.t('analysis.income_flow', {
            lord: I18n.t('planets.' + lord11),
            house: house11LordPos
        })} `;
        if ([1, 2, 4, 5, 7, 9, 10, 11].includes(house11LordPos)) {
            text += I18n.t('analysis.income_favorable');
        }

        text += `\n\n${I18n.t('analysis.jupiter_abundance', {
            status: I18n.t('shadbala.status.' + jupiter.status),
            score: I18n.n(jupiter.score.toFixed(1))
        })} `;
        text += jupiter.score > 6 ? I18n.t('analysis.jupiter_strong') : I18n.t('analysis.jupiter_weak');

        if (dhanaYogas.length > 0) {
            const yogaNames = dhanaYogas.map(y => y.nameKey ? I18n.t('lists.yoga_list.' + y.nameKey + '.name', y.params || {}) : y.name).join(', ');
            text += `\n\n${I18n.t('analysis.wealth_yogas', { yogas: yogaNames })} `;
            text += I18n.t('analysis.wealth_yogas_desc');
        }

        return {
            title: I18n.t('analysis.wealth'),
            content: text,
            details: [
                { label: I18n.t('planets.Jupiter'), value: I18n.t('shadbala.status.' + jupiter.status) },
                { label: I18n.t('yogas.dhana'), value: I18n.n(dhanaYogas.length) }
            ]
        };
    }

    _analyzeMultiDashas(ctx) {
        const { chart } = ctx;
        const dashaDetails = chart.dashaDetails || {};
        const systems = Object.keys(dashaDetails);
        const analysis = {};

        systems.forEach(sys => {
            const hierarchy = dashaDetails[sys];
            const interpretationPath = DashaAnalysis.analyze(sys, hierarchy, ctx);

            if (interpretationPath) {
                const mainItem = interpretationPath[0];
                const activeSub = interpretationPath[1] || mainItem;

                analysis[sys] = {
                    id: sys,
                    title: I18n.t(`dashas.systems.${sys}`),
                    path: interpretationPath,
                    summary: I18n.t('analysis.dasha_intro', {
                        md: mainItem.planetName,
                        ad: activeSub.planetName
                    }),
                    stats: [
                        { label: I18n.t('dashas.period'), value: this._formatDuration(mainItem.end - new Date()) }
                    ]
                };
            }
        });

        return analysis;
    }

    _analyzeAllLords(ctx) {
        const { helpers, chart } = ctx;
        const details = [];

        for (let i = 1; i <= 12; i++) {
            const lord = helpers.getLordOfHouse(i);
            const lordObj = chart.planets[lord];
            const placedIn = helpers.getHouse(lordObj.lon);
            const strength = helpers.getStrength(lord);
            
            // Advanced: Include Ishta/Kashta Phala (Net Beneficence)
            const phala = chart.shadbala?.phala?.[lord];
            const netPhala = phala ? phala.net : 0;

            details.push({
                house: I18n.n(i),
                lord: I18n.t('planets.' + lord),
                placed: I18n.n(placedIn),
                status: I18n.t('shadbala.status.' + strength.status),
                netPhala: netPhala.toFixed(1),
                rawStatus: strength.status 
            });
        }

        return {
            title: I18n.t('analysis.lords'),
            summary: I18n.t('analysis.lords_summary'),
            lords: details
        };
    }

    _analyzeRemedies(ctx) {
        const fullRemedies = RemediesEngine.calculate(ctx);
        const list = [];

        // Flatten the categorized remedies into a single list for the overview section
        if (fullRemedies.gemstones.length > 0) {
            fullRemedies.gemstones.forEach(g => {
                list.push({
                    planet: I18n.t('planets.' + g.planet),
                    reason: g.reason,
                    action: `Wear ${g.name} on ${g.finger} in ${g.metal}.`
                });
            });
        }

        if (fullRemedies.rituals.length > 0) {
            fullRemedies.rituals.forEach(r => {
                list.push({
                    planet: r.deity,
                    reason: r.reason,
                    action: r.name
                });
            });
        }

        // Add a few more from other categories for the summary
        if (fullRemedies.mantras.length > 0) {
            const m = fullRemedies.mantras[0];
            list.push({
                planet: I18n.t('planets.' + m.planet),
                reason: m.reason,
                action: `Chant Beej Mantra: ${m.text}`
            });
        }

        let summary = I18n.t('analysis.remedy_summary_none');
        if (list.length > 0 && list.length <= 2) summary = I18n.t('analysis.remedy_summary_few');
        else if (list.length > 2) summary = I18n.t('analysis.remedy_summary_many');

        return {
            title: I18n.t('analysis.remedies'),
            summary: summary,
            list: list
        };
    }

    _analyzeAvasthas(ctx) {
        const { chart } = ctx;
        const planets = {};
        const saptaGraha = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];

        // Adapt chart data for AvasthsEngine
        saptaGraha.forEach(p => {
            if (chart.planets[p]) {
                planets[p] = {
                    sign: chart.planets[p].rasi.index,
                    degree: chart.planets[p].rasi.degrees
                };
            }
        });

        const avasthaData = {
            planets,
            lagnaRasi: chart.lagna.rasi.index
        };

        const results = AvasthaEngine.calculateChartAvasthas(avasthaData);
        const list = [];

        // 1. Baladi (Age)
        let baladiContent = '<div class="grid-2 gap-2">';
        saptaGraha.forEach(p => {
            const res = results[p].baladi;
            baladiContent += `
                <div class="d-flex justify-content-between align-items-center border-bottom-light pb-1 mb-1">
                    <span>${I18n.t('planets.' + p)}</span>
                    <span class="font-weight-medium">${I18n.t(res.nameKey)}</span>
                </div>
            `;
        });
        baladiContent += '</div>';

        list.push({
            planet: I18n.t('avasthas.title_baladi'),
            reason: I18n.t('avasthas.types.baladi'),
            action: baladiContent
        });

        // 2. Jagratadi (Consciousness)
        let jagratadiContent = '<div class="grid-2 gap-2">';
        saptaGraha.forEach(p => {
            const res = results[p].jagratadi;
            jagratadiContent += `
                <div class="d-flex justify-content-between align-items-center border-bottom-light pb-1 mb-1">
                    <span>${I18n.t('planets.' + p)}</span>
                    <span class="font-weight-medium">${I18n.t(res.nameKey)}</span>
                </div>
            `;
        });
        jagratadiContent += '</div>';

        list.push({
            planet: I18n.t('avasthas.title_jagratadi'),
            reason: I18n.t('avasthas.types.jagratadi'),
            action: jagratadiContent
        });

        // 3. Lajjitadi (Mood)
        let lajjitadiContent = '';
        let hasLajjitadi = false;

        saptaGraha.forEach(p => {
            const states = results[p].lajjitadi;
            if (states && states.length > 0) {
                hasLajjitadi = true;
                const stateNames = states.map(s => {
                    const colorClass = s.nature === 'Malefic' ? 'text-error' : (s.nature === 'Highly Benefic' ? 'text-success' : 'text-primary');
                    return `<span class="${colorClass}">${I18n.t(s.nameKey)}</span>`;
                }).join(', ');

                lajjitadiContent += `
                    <div class="mb-2 border-bottom-light pb-2">
                        <div class="d-flex justify-content-between font-weight-bold mb-1">
                            <span>${I18n.t('planets.' + p)}</span>
                        </div>
                        <div class="text-body-small">${stateNames}</div>
                    </div>
                `;
            }
        });

        if (!hasLajjitadi) {
            lajjitadiContent = `<div>${I18n.t('avasthas.no_lajjitadi')}</div>`;
        }

        list.push({
            planet: I18n.t('avasthas.title_lajjitadi'),
            reason: I18n.t('avasthas.types.lajjitadi'),
            action: lajjitadiContent + `<div class="mt-2 text-body-small opacity-60"><i>${I18n.t('avasthas.intro_lajjitadi')}</i></div>`
        });

        return {
            title: I18n.t('avasthas.title'),
            summary: I18n.t('avasthas.intro'),
            list: list
        };
    }

    _getSadeSatiPhase(moonSign, saturnSign) {
        const diff = (saturnSign - moonSign + 12) % 12;
        if (diff === 11) return 'Rising';
        if (diff === 0) return 'Peak';
        if (diff === 1) return 'Setting';
        return null;
    }

    // =========================================================================
    // HELPERS
    // =========================================================================

    _calculateManglik(chart, profile) {
        const getSignIdx = (p) => chart.planets[p].rasi.index + 1;
        const data = {
            lagnaSign: chart.lagna.rasi.index + 1,
            moonSign: getSignIdx('Moon'),
            venusSign: getSignIdx('Venus'),
            marsSign: getSignIdx('Mars'),
            jupiterSign: getSignIdx('Jupiter'),
            saturnSign: getSignIdx('Saturn'),
            rahuSign: getSignIdx('Rahu'),
            ketuSign: getSignIdx('Ketu'),
            sunSign: getSignIdx('Sun'),
            gender: 'male',
            age: (new Date().getFullYear()) - (new Date(profile.datetime).getFullYear())
        };
        return ManglikEngine.calculate(data);
    }

    _getHelpers(chart) {
        const self = this;
        const lagnaLon = chart.lagna.lon;
        const lagnaIdx = chart.lagna.rasi.index;

        return {
            getSign: (lon) => {
                const idx = Math.floor(lon / 30);
                return {
                    name: self.signs[idx],
                    element: Object.keys(self.elements).find(k => self.elements[k].includes(idx)),
                    ruler: self._getLordOfSign(idx)
                };
            },
            getHouse: (lon) => {
                return Math.floor(((lon - lagnaLon + 360) % 360) / 30) + 1;
            },
            getLordOfHouse: (h) => {
                const signIdx = (lagnaIdx + h - 1) % 12;
                return self._getLordOfSign(signIdx);
            },
            getPlanetsInHouse: (h) => {
                const planets = [];
                for (const [p, data] of Object.entries(chart.planets)) {
                    if (Math.floor(((data.lon - lagnaLon + 360) % 360) / 30) + 1 === h) planets.push(p);
                }
                return planets;
            },
            getStrength: (planet) => {
                const s = chart.shadbala.total[planet];
                if (!s) return { score: 0, status: 'neutral' };
                let status = 'moderate';
                if (s.rupas > 6.5) status = 'strong';
                else if (s.rupas < 5.0) status = 'weak';
                return { score: s.rupas, status };
            },
            getElementalBalance: () => {
                const counts = { Fire: 0, Earth: 0, Air: 0, Water: 0 };
                const points = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
                points.forEach(p => {
                    const idx = chart.planets[p].rasi.index;
                    const el = Object.keys(self.elements).find(k => self.elements[k].includes(idx));
                    counts[el]++;
                });
                const lagnaEl = Object.keys(self.elements).find(k => self.elements[k].includes(lagnaIdx));
                counts[lagnaEl]++;
                return { elements: counts };
            }
        };
    }

    _getLordOfSign(idx) {
        const rulers = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter'];
        return rulers[idx];
    }

    _getFunctionalNature(lagnaIdx) {
        const rulers = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter'];
        const getLord = (house) => rulers[(lagnaIdx + house - 1) % 12];
        const nature = {};
        const sevenPlanets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
        sevenPlanets.forEach(p => nature[p] = 'Neutral');
        nature[getLord(5)] = 'Benefic';
        nature[getLord(9)] = 'Benefic';
        nature[getLord(1)] = 'Benefic';
        nature[getLord(6)] = 'Malefic';
        nature[getLord(8)] = 'Malefic';
        nature[getLord(12)] = 'Malefic';
        if (nature[getLord(3)] !== 'Benefic') nature[getLord(3)] = 'Malefic';
        const naturalBenefics = ['Jupiter', 'Venus', 'Mercury', 'Moon'];
        [4, 7, 10].forEach(h => {
            const lord = getLord(h);
            if (naturalBenefics.includes(lord) && nature[lord] !== 'Benefic') nature[lord] = 'Neutral';
        });
        if (lagnaIdx === 1 || lagnaIdx === 6) nature['Saturn'] = 'Benefic';
        if (lagnaIdx === 3) nature['Mars'] = 'Benefic';
        if (lagnaIdx === 4) nature['Mars'] = 'Benefic';
        if (lagnaIdx === 9 || lagnaIdx === 10) nature['Venus'] = 'Benefic';
        return nature;
    }

    _getHousesLordedBy(planet, lagnaIdx) {
        const rulers = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter'];
        const houses = [];
        for (let h = 1; h <= 12; h++) {
            const signIdx = (lagnaIdx + h - 1) % 12;
            if (rulers[signIdx] === planet) houses.push(h);
        }
        return houses;
    }

    _formatDuration(milliseconds) {
        const totalDays = Math.floor(milliseconds / (1000 * 60 * 60 * 24));
        const years = Math.floor(totalDays / 365);
        const months = Math.floor((totalDays % 365) / 30);
        const days = totalDays % 30;

        const ySign = I18n.t('common.year_short');
        const mSign = I18n.t('common.month_short');
        const dSign = I18n.t('common.day_short');
        const sep = I18n.t('common.duration_separator') || ' ';

        const y = I18n.n(years);
        const m = I18n.n(months);
        const d = I18n.n(days);

        if (years > 0) return `${y} ${ySign}${sep}${m} ${mSign}`;
        else if (months > 0) return `${m} ${mSign}${sep}${d} ${dSign}`;
        else return `${d} ${dSign}`;
    }
}

export default new AnalysisEngine();
