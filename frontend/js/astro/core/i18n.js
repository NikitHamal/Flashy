/**
 * i18n.js - Internationalization module for AstroWeb
 * Provides translation, number formatting, and locale management.
 */

class I18n {
    constructor() {
        this.locale = 'en';
        this.fallbackLocale = 'en';

        // Basic translations for Vedic Astrology
        this.translations = {
            en: {
                common: {
                    pada: 'Pada',
                    unknown: 'Unknown'
                },
                planets: {
                    Sun: 'Sun',
                    Moon: 'Moon',
                    Mars: 'Mars',
                    Mercury: 'Mercury',
                    Jupiter: 'Jupiter',
                    Venus: 'Venus',
                    Saturn: 'Saturn',
                    Rahu: 'Rahu',
                    Ketu: 'Ketu',
                    Asc: 'Ascendant',
                    Lagna: 'Lagna'
                },
                planet_symbols: {
                    Sun: 'Su',
                    Moon: 'Mo',
                    Mars: 'Ma',
                    Mercury: 'Me',
                    Jupiter: 'Ju',
                    Venus: 'Ve',
                    Saturn: 'Sa',
                    Rahu: 'Ra',
                    Ketu: 'Ke',
                    Asc: 'Asc'
                },
                rasis: {
                    Mesha: 'Aries',
                    Vrishabha: 'Taurus',
                    Mithuna: 'Gemini',
                    Karka: 'Cancer',
                    Simha: 'Leo',
                    Kanya: 'Virgo',
                    Tula: 'Libra',
                    Vrishchika: 'Scorpio',
                    Dhanu: 'Sagittarius',
                    Makara: 'Capricorn',
                    Kumbha: 'Aquarius',
                    Meena: 'Pisces'
                },
                kundali: {
                    nakshatra: 'Nakshatra',
                    dignity: 'Dignity',
                    retrograde_short: '(R)',
                    retrograde_full: 'Retrograde',
                    sign: 'Sign',
                    legend: 'Chart Legend',
                    exalted: 'Exalted',
                    debilitated: 'Debilitated',
                    own_sign: 'Own Sign',
                    mooltrikona: 'Mooltrikona',
                    neutral: 'Neutral',
                    combust: 'Combust',
                    vargottama: 'Vargottama',
                    ak: 'Atmakaraka',
                    amk: 'Amatyakaraka',
                    hover_details: 'Hover over planets for details'
                },
                lists: {
                    nakshatras: [
                        'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
                        'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
                        'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
                        'Moola', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishtha', 'Shatabhisha',
                        'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
                    ],
                    tithis: [
                        'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami', 'Shashti',
                        'Saptami', 'Ashtami', 'Navami', 'Dashami', 'Ekadashi', 'Dwadashi',
                        'Trayodashi', 'Chaturdashi', 'Purnima/Amavasya'
                    ],
                    paksha: {
                        Shukla: 'Shukla (Waxing)',
                        Krishna: 'Krishna (Waning)'
                    },
                    yogas: [
                        'Vishkumbha', 'Preeti', 'Ayushman', 'Saubhagya', 'Shobhana', 'Atiganda',
                        'Sukarma', 'Dhriti', 'Shoola', 'Ganda', 'Vriddhi', 'Dhruva',
                        'Vyaghata', 'Harshana', 'Vajra', 'Siddhi', 'Vyatipata', 'Variyan', 'Parigha',
                        'Shiva', 'Siddha', 'Sadhya', 'Shubha', 'Shukla', 'Brahma', 'Indra', 'Vaidhriti'
                    ]
                },
                analysis: {
                    overview: 'Life Overview',
                    personality: 'Personality & Nature',
                    career: 'Career & Ambition',
                    relationships: 'Marriage & Relationships',
                    wealth: 'Wealth & Prosperity',
                    remedies: 'Remedies & Guidance',
                    lords: 'House Lords',
                    lords_summary: 'Analysis of planetary ownership across houses.',
                    born_under: 'Born under {lagna} Lagna ({element} element), with Sun in {sun} and Moon in {moon}.',
                    birth_occurred: 'Birth occurred during {tithi} Tithi ({paksha} Paksha) in {yoga} Yoga and {nakshatra} Nakshatra (Pada {pada}).',
                    soul_planet: 'Soul Planet (AK)',
                    ak_desc: '{planet} acts as your Atmakaraka, representing the soul\'s deepest desires and karmic lessons.',
                    vargottama_notably: 'Notably, {planets} {verb} Vargottama (strong in both D1 and D9).',
                    personality_intro: 'Your personality is shaped by {lagna} Lagna and {nakshatra} Nakshatra.',
                    ruling_planet: 'Your ruling planet is {lord}, placed in House {house}.',
                    lord_attitude: 'Planetary Attitude',
                    strong_lord: '{lord} is strong, giving you confidence and vitality.',
                    weak_lord: '{lord} is weak, suggesting a need for conscious effort in self-expression.',
                    elemental_constitution: 'Dominant Element: {dominant}. {desc}',
                    special_distinction: 'You possess the special distinction of {yogas}: {desc}',
                    career_intro: 'Career is influenced by {lord}, ruler of the 10th house.',
                    career_placement: '{lord} is placed in House {house}, directing your professional focus there.',
                    career_dusthana: 'Placement in a challenge house suggests professional hurdles or service-oriented work.',
                    career_kendra: 'Strong placement in a pivot house indicates leadership potential.',
                    career_trikona: 'Placement in a fortune house suggests natural flow and success.',
                    planets_in_10: 'The 10th house is occupied by {planets}, adding diverse influences to your work.',
                    planet_career_influence: '{planet} suggests a career in {career}.',
                    no_occupants_10: 'No planets occupy the 10th house; focus on the lord {lord}.',
                    d10_intro: 'In the career chart (D10), you have {lagna} rising, indicating {keywords}.',
                    sun_10_digbala: 'The Sun in the 10th house gains directional strength (Digbala), promising authority.',
                    relationship_intro: 'Relationships are guided by {lord}, ruler of the 7th house.',
                    planets_in_7: 'Occupants of the 7th house: {planets}.',
                    malefics_7: 'Presence of intense planets may bring challenges or high-energy dynamics.',
                    spouse_nature: 'Benefic influence suggests a supportive and harmonious partner.',
                    d9_intro: 'In the marriage chart (D9), {lagna} is rising.',
                    recommendation: 'Guidance',
                    wealth_intro: 'Wealth potential is seen through {lord2} (Accumulation) and {lord11} (Gains).',
                    wealth_potential: '{lord} (2nd Lord) in House {house} shows how you save and build assets.',
                    income_flow: '{lord} (11th Lord) in House {house} defines your source of income.',
                    income_favorable: 'This favorable placement promises steady gains.',
                    jupiter_abundance: 'Jupiter, the significator of wealth, is {status} with a score of {score}.',
                    jupiter_strong: 'A strong Jupiter ensures wisdom and financial protection.',
                    jupiter_weak: 'A weak Jupiter suggests a need for better financial management.',
                    wealth_yogas: 'Wealth Yogas found: {yogas}.',
                    wealth_yogas_desc: 'These planetary combinations promise significant financial prosperity.',
                    dasha_intro: 'Currently running {md} Mahadasha and {ad} Antardasha.',
                    remedy_summary_none: 'No specific remedies needed at this time.',
                    remedy_summary_few: 'A few simple remedies are recommended for balance.',
                    remedy_summary_many: 'Several specific remedies are suggested to overcome planetary obstacles.',
                    elements: {
                        Fire: 'Fire',
                        Earth: 'Earth',
                        Air: 'Air',
                        Water: 'Water'
                    }
                },
                matching: {
                    manglik: 'Manglik Status',
                    manglik_analysis: 'Mangal Dosha (Manglik) Analysis',
                    intensities: {
                        None: 'None',
                        Low: 'Low',
                        Medium: 'Medium',
                        High: 'High',
                        Severe: 'Severe'
                    },
                    manglik_status: {
                        none: 'Not Manglik',
                        present: 'Manglik ({intensity} intensity)',
                        cancelled: 'Manglik but Cancelled',
                        cancelled_with_reason: 'Manglik Cancelled: {reason}'
                    }
                },
                dashas: {
                    systems: {
                        vimshottari: 'Vimshottari Dasha',
                        char: 'Chara Dasha',
                        yogini: 'Yogini Dasha'
                    },
                    period: 'Remaining Duration'
                },
                vargas: {
                    D1: 'Rasi', D2: 'Hora', D3: 'Drekkana', D4: 'Chaturthamsa',
                    D7: 'Saptamsa', D9: 'Navamsa', D10: 'Dasamsa', D12: 'Dwadasamsa',
                    D16: 'Shodasamsa', D20: 'Vimsamsa', D24: 'Chaturvimsamsa', D27: 'Saptavimsamsa',
                    D30: 'Trimsamsa', D40: 'Khavedamsa', D45: 'Akshavedamsa', D60: 'Shastiamsa'
                },
                panchang: {
                    nakshatra: 'Birth Nakshatra',
                    tithi: 'Birth Tithi'
                },
                shadbala: {
                    status: {
                        strong: 'Strong',
                        weak: 'Weak',
                        moderate: 'Moderate',
                        neutral: 'Neutral'
                    }
                }
            }
        };
    }

    /**
     * Set the current locale
     * @param {string} locale 
     */
    setLocale(locale) {
        if (this.translations[locale]) {
            this.locale = locale;
        }
    }

    /**
     * Get the current locale
     * @returns {string}
     */
    getLocale() {
        return this.locale;
    }

    /**
     * Translate a key with optional parameters
     * @param {string} key - Dot-separated key (e.g., 'planets.Sun')
     * @param {Object} params - Optional parameters for interpolation
     * @returns {string} 
     */
    t(key, params = {}) {
        let value = this._getValue(key, this.locale) || this._getValue(key, this.fallbackLocale) || key;

        if (typeof value === 'string' && params) {
            Object.entries(params).forEach(([k, v]) => {
                value = value.replace(`{${k}}`, v);
            });
        }

        return value;
    }

    /**
     * Format a number (optional: devanagari if locale is set)
     * @param {number|string} n 
     * @returns {string}
     */
    n(n) {
        return n.toString();
    }

    /**
     * Private helper to traverse the translation object
     */
    _getValue(key, locale) {
        try {
            return key.split('.').reduce((obj, k) => obj && obj[k], this.translations[locale]);
        } catch (e) {
            return null;
        }
    }
}

export default new I18n();
