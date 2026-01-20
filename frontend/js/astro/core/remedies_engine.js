/**
 * ============================================================================
 * REMEDIES ENGINE - Personalized Vedic Remedial Analysis
 * ============================================================================
 * 
 * This module performs deep analysis of the chart to suggest remedies:
 * 1. Strength Correction: For weak functional benefics (Gemstones/Mantras)
 * 2. Affliction Mitigation: For combust/afflicted planets (Daana/Shanti)
 * 3. Specific Doshas: Sade Sati, Manglik, Kaal Sarpa, etc.
 * 4. Avastha Balancing: For planets in Vikala/Khala states.
 * 
 * References:
 * - BPHS (Remedial Chapters)
 * - Phaladeepika (Adhyaya 26)
 * - Jataka Parijata
 */

import { REMEDY_DATA } from './remedy_data.js';
import { SIGN_LORDS } from './constants.js';
import I18n from '../core/i18n.js';

class RemediesEngine {
    /**
     * Main calculation method
     * @param {Object} ctx - Full analysis context
     * @returns {Object} Categorized remedies
     */
    calculate(ctx) {
        const { chart, shadbala, avasthas, manglik, transits } = ctx;

        const recommendations = {
            gemstones: [],
            mantras: [],
            charity: [],
            fasting: [],
            rituals: [],
            summary: ""
        };

        // Standardize data access - handle both old/new formats and missing planets
        const getPlanetData = (p) => {
            const raw = REMEDY_DATA.planets[p];
            if (!raw) return null;
            return this._normalizePlanetData(raw, p);
        };

        // 1. Analyze Functional Nature for Gemstones
        this._analyzeGemstones(ctx, recommendations, getPlanetData);

        // 2. Analyze Afflictions for Mantras and Shanti
        this._analyzeAfflictions(ctx, recommendations, getPlanetData);

        // 3. Specific Doshas (Sade Sati, Manglik)
        this._analyzeSpecificDoshas(ctx, recommendations);

        // 4. Avastha Correction
        this._analyzeAvasthaRemedies(ctx, recommendations, getPlanetData);

        return recommendations;
    }

    /**
     * Resilient Data Normalization Layer
     * Maps diverse raw data formats to a strict internal interface
     */
    _normalizePlanetData(raw, planet) {
        // Safe Gemstone Mapping
        const gem = raw.gemstone || {};
        const normalizedGem = {
            name: gem.nameKey ? `remedies.data.gemstones.${gem.nameKey}` : (gem.primary || gem.name || `${planet} Stone`),
            isKey: !!gem.nameKey,
            weight: gem.weight || "3-6",
            metal: gem.metalKey ? `remedies.data.metals.${gem.metalKey}` : (gem.metal || "Gold"),
            metalKey: gem.metalKey ? `remedies.data.metals.${gem.metalKey}` : "",
            isMetalKey: !!gem.metalKey,
            finger: gem.fingerKey ? `remedies.data.fingers.${gem.fingerKey}` : (gem.finger || "Ring finger"),
            fingerKey: gem.fingerKey ? `remedies.data.fingers.${gem.fingerKey}` : "",
            isFingerKey: !!gem.fingerKey,
            day: gem.dayKey || gem.day || "Sunday",
            dayKey: gem.dayKey || "",
            alternates: Array.isArray(gem.alternates) ? gem.alternates : []
        };

        // Safe Mantra Mapping
        const mData = raw.mantra || {};
        const normalizedMantra = {
            beej: mData.beej || "",
            beej_np: mData.beej_np || "",
            gayatri: mData.gayatri || "",
            gayatri_np: mData.gayatri_np || "",
            count: mData.count || 108,
            japaDay: mData.japaDay || raw.fasting?.day || "Daily"
        };

        // Safe Charity Mapping
        const charity = raw.charity || {};
        const items = Array.isArray(charity.itemKeys) ? charity.itemKeys.map(k => `remedies.data.items.${k}`) : (charity.items || []);

        const normalizedCharity = {
            items: items,
            recipient: charity.recipientKey ? `remedies.recipients.${charity.recipientKey}` : (charity.recipient || "The Needy"),
            recipientKey: charity.recipientKey ? `remedies.recipients.${charity.recipientKey}` : "",
            isRecipientKey: !!charity.recipientKey,
            day: charity.dayKey || charity.day || "Specified Day",
            dayKey: charity.dayKey || ""
        };

        return {
            gemstone: normalizedGem,
            mantra: normalizedMantra,
            charity: normalizedCharity,
            fasting: raw.fasting || {},
            rituals: Array.isArray(raw.puja) ? raw.puja : []
        };
    }

    /**
     * Suggest Gemstones based on Functional Benefics and Atmakaraka
     */
    _analyzeGemstones(ctx, recs, getPlanetData) {
        const lagnaIdx = ctx.chart.lagna.rasi.index;
        const functionalNature = this._getFunctionalNature(lagnaIdx);

        const akPlanet = ctx.chart.jaimini?.charaKarakas?.karakas?.AK?.planet;

        Object.entries(functionalNature).forEach(([planet, nature]) => {
            const isAK = planet === akPlanet;
            const strength = ctx.helpers.getStrength(planet);

            // Recommend if functional benefic and weak, OR if it's the AK
            if ((nature === 'Benefic' && strength.score < 6.0) || isAK) {
                const data = getPlanetData(planet);
                if (data && data.gemstone) {
                    recs.gemstones.push({
                        planet,
                        ...data.gemstone,
                        reasonKey: isAK ? 'atmakaraka_support' : 'weak_benefic',
                        params: { score: strength.score.toFixed(1), planet: I18n.t('planets.' + planet) }
                    });
                }
            }
        });
    }

    /**
     * Suggest Mantras and Shanti for Malefics or Afflictions
     */
    _analyzeAfflictions(ctx, recs, getPlanetData) {
        const { chart } = ctx;
        const planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];

        planets.forEach(p => {
            const isCombust = ctx.helpers.isCombust ? ctx.helpers.isCombust(p) : false;
            const isDebilitated = chart.planets[p]?.rasi?.index === this._getDebilitationSign(p);

            if (isCombust || isDebilitated) {
                const data = getPlanetData(p);
                if (data) {
                    if (data.mantra.beej) {
                        recs.mantras.push({
                            planet: p,
                            text: data.mantra.beej,
                            beej_np: data.mantra.beej_np,
                            gayatri: data.mantra.gayatri,
                            gayatri_np: data.mantra.gayatri_np,
                            count: data.mantra.count,
                            reasonKey: isCombust ? 'combust' : 'debilitated'
                        });
                    }

                    if (data.charity.items.length > 0) {
                        recs.charity.push({
                            planet: p,
                            ...data.charity,
                            reasonKey: 'pacify'
                        });
                    }
                }
            }
        });
    }

    /**
     * Targeted Dosha Analysis
     */
    _analyzeSpecificDoshas(ctx, recs) {
        const { manglik, transits, chart } = ctx;

        // Manglik
        if (manglik.isEffectiveManglik) {
            recs.rituals.push({
                name: I18n.t('remedies.specific.manglik_shanti'),
                deity: I18n.t('remedies.deities.Hanuman'),
                reasonKey: "manglik",
                priority: "High"
            });
        }

        // Sade Sati
        const moonSign = chart.planets.Moon.rasi.index;
        const saturnSign = transits.planets.Saturn.rasi.index;
        const diff = (saturnSign - moonSign + 12) % 12;
        if ([11, 0, 1].includes(diff)) {
            recs.rituals.push({
                name: I18n.t('remedies.specific.shani_shanti'),
                deity: I18n.t('remedies.deities.Shani'),
                reasonKey: "sade_sati",
                priority: "Medium"
            });
            recs.fasting.push({
                day: "Saturday",
                dayKey: "Saturday",
                reasonKey: "saturn_mitigation"
            });
        }
    }

    /**
     * Avastha based psychological remedies
     */
    _analyzeAvasthaRemedies(ctx, recs, getPlanetData) {
        const planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
        planets.forEach(p => {
            const deeptadi = ctx.avasthas?.[p]?.deeptadi?.state;
            if (['VIKALA', 'KHALA', 'KHOBHITA'].includes(deeptadi)) {
                const data = getPlanetData(p);
                if (data && data.mantra.beej) {
                    recs.mantras.push({
                        planet: p,
                        text: data.mantra.beej,
                        beej_np: data.mantra.beej_np,
                        gayatri: data.mantra.gayatri,
                        gayatri_np: data.mantra.gayatri_np,
                        count: data.mantra.count,
                        reasonKey: 'avastha_state',
                        params: { state: I18n.t('avasthas.deeptadi.' + deeptadi.toLowerCase()) }
                    });
                }
            }
        });
    }

    // --- INTERNAL HELPERS ---

    _getFunctionalNature(lagnaIdx) {
        const rulers = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter'];
        const getLord = (house) => rulers[(lagnaIdx + house - 1) % 12];
        const nature = {};
        const sevenPlanets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
        sevenPlanets.forEach(p => nature[p] = 'Neutral');

        // Benefics: Lords of 1, 5, 9
        nature[getLord(1)] = 'Benefic';
        nature[getLord(5)] = 'Benefic';
        nature[getLord(9)] = 'Benefic';

        // Malefics: Lords of 3, 6, 11 (Upachaya but tough)
        // Also 8 and 12 are tricky
        const malefics = [3, 6, 8, 11, 12];
        malefics.forEach(h => {
            const lord = getLord(h);
            if (nature[lord] !== 'Benefic') nature[lord] = 'Malefic';
        });

        return nature;
    }

    _getDebilitationSign(planet) {
        const deb = { Sun: 6, Moon: 7, Mars: 3, Mercury: 11, Jupiter: 9, Venus: 5, Saturn: 0 };
        return deb[planet];
    }
}

export default new RemediesEngine();
