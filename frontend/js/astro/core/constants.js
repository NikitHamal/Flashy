/**
 * ============================================================================
 * VEDIC ASTROLOGY CONSTANTS - Single Source of Truth
 * ============================================================================
 *
 * This module centralizes ALL astronomical and astrological constants used
 * throughout AstroWeb. Any modification to planetary dignities, sign data,
 * nakshatra information, or other Vedic astrological parameters should be
 * made ONLY in this file.
 *
 * References:
 * - Brihat Parashara Hora Shastra (BPHS)
 * - Phaladeepika
 * - Jataka Parijata
 * - Saravali
 *
 * @module constants
 * @version 2.0.0
 */

// ============================================================================
// SIGN (RASI) DATA
// ============================================================================

/**
 * Sign names in Sanskrit transliteration (canonical form)
 * Index 0 = Aries (Mesha), Index 11 = Pisces (Meena)
 */
export const RASI_NAMES = Object.freeze([
    'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
    'Tula', 'Vrishchika', 'Dhanu', 'Makara', 'Kumbha', 'Meena'
]);

/**
 * Sign names in English (Western equivalent)
 */
export const RASI_NAMES_ENGLISH = Object.freeze([
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]);

/**
 * Sign lordship - Maps sign index to ruling planet
 * Per BPHS Chapter 3
 */
export const SIGN_LORDS = Object.freeze({
    0: 'Mars',      // Aries
    1: 'Venus',     // Taurus
    2: 'Mercury',   // Gemini
    3: 'Moon',      // Cancer
    4: 'Sun',       // Leo
    5: 'Mercury',   // Virgo
    6: 'Venus',     // Libra
    7: 'Mars',      // Scorpio
    8: 'Jupiter',   // Sagittarius
    9: 'Saturn',    // Capricorn
    10: 'Saturn',   // Aquarius
    11: 'Jupiter'   // Pisces
});

/**
 * Element classification of signs
 * Fire (Agni), Earth (Prithvi), Air (Vayu), Water (Jala)
 */
export const SIGN_ELEMENTS = Object.freeze({
    0: 'Fire', 1: 'Earth', 2: 'Air', 3: 'Water',
    4: 'Fire', 5: 'Earth', 6: 'Air', 7: 'Water',
    8: 'Fire', 9: 'Earth', 10: 'Air', 11: 'Water'
});

/**
 * Element names for iteration
 */
export const ELEMENT_NAMES = Object.freeze(['Fire', 'Earth', 'Air', 'Water']);

/**
 * Modality (Quality) classification of signs
 * 0 = Movable (Chara), 1 = Fixed (Sthira), 2 = Dual (Dwiswabhava)
 */
export const SIGN_MODALITY = Object.freeze({
    0: 0, 1: 1, 2: 2, 3: 0,    // Aries-Cancer
    4: 1, 5: 2, 6: 0, 7: 1,    // Leo-Scorpio
    8: 2, 9: 0, 10: 1, 11: 2   // Sagittarius-Pisces
});

/**
 * Modality names
 */
export const MODALITY_NAMES = Object.freeze(['Chara', 'Sthira', 'Dwiswabhava']);

/**
 * Sign gender classification
 * Odd signs (1,3,5,7,9,11 in 1-indexed = 0,2,4,6,8,10) are Male/Odd
 * Even signs (2,4,6,8,10,12 in 1-indexed = 1,3,5,7,9,11) are Female/Even
 */
export const SIGN_GENDER = Object.freeze({
    0: 'Male', 1: 'Female', 2: 'Male', 3: 'Female',
    4: 'Male', 5: 'Female', 6: 'Male', 7: 'Female',
    8: 'Male', 9: 'Female', 10: 'Male', 11: 'Female'
});

// ============================================================================
// NAKSHATRA DATA
// ============================================================================

/**
 * 27 Nakshatras in order
 * Each nakshatra spans 13°20' (13.3333...°)
 */
export const NAKSHATRA_NAMES = Object.freeze([
    'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
    'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
    'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
    'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
    'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
]);

/**
 * Nakshatra span in degrees
 */
export const NAKSHATRA_SPAN = 13.333333333333334; // 360/27

/**
 * Nakshatra lords for Vimshottari Dasha
 * Standard sequence: Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury
 */
export const NAKSHATRA_LORDS_VIMSHOTTARI = Object.freeze([
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury'
]);

/**
 * Nakshatra deity mapping
 */
export const NAKSHATRA_DEITIES = Object.freeze([
    'Ashwini Kumaras', 'Yama', 'Agni', 'Brahma', 'Soma', 'Rudra',
    'Aditi', 'Brihaspati', 'Sarpa', 'Pitris', 'Bhaga', 'Aryaman',
    'Savitar', 'Tvashtar', 'Vayu', 'Indragni', 'Mitra', 'Indra',
    'Nirrti', 'Apas', 'Vishwadevas', 'Vishnu', 'Vasus', 'Varuna',
    'Ajaikapada', 'Ahirbudhnya', 'Pushan'
]);

/**
 * Gana (temperament) for each nakshatra
 * 0 = Deva (Divine), 1 = Manushya (Human), 2 = Rakshasa (Demonic)
 */
export const NAKSHATRA_GANA = Object.freeze([
    0, 1, 2, 1, 0, 1, 0, 0, 2,  // Ashwini to Ashlesha
    2, 1, 1, 0, 2, 0, 2, 0, 2,  // Magha to Jyeshtha
    2, 1, 1, 0, 2, 2, 1, 1, 0   // Mula to Revati
]);

/**
 * Gana names
 */
export const GANA_NAMES = Object.freeze(['Deva', 'Manushya', 'Rakshasa']);

/**
 * Yoni (animal) for each nakshatra
 * Used in matchmaking
 */
export const NAKSHATRA_YONI = Object.freeze([
    0,  // Ashwini - Horse
    1,  // Bharani - Elephant
    2,  // Krittika - Sheep
    3,  // Rohini - Snake
    3,  // Mrigashira - Snake
    4,  // Ardra - Dog
    5,  // Punarvasu - Cat
    2,  // Pushya - Sheep
    5,  // Ashlesha - Cat
    6,  // Magha - Rat
    6,  // Purva Phalguni - Rat
    7,  // Uttara Phalguni - Cow
    8,  // Hasta - Buffalo
    9,  // Chitra - Tiger
    8,  // Swati - Buffalo
    9,  // Vishakha - Tiger
    10, // Anuradha - Deer
    10, // Jyeshtha - Deer
    4,  // Mula - Dog
    11, // Purva Ashadha - Monkey
    12, // Uttara Ashadha - Mongoose
    11, // Shravana - Monkey
    13, // Dhanishta - Lion
    0,  // Shatabhisha - Horse
    13, // Purva Bhadrapada - Lion
    7,  // Uttara Bhadrapada - Cow
    1   // Revati - Elephant
]);

/**
 * Yoni animal names
 */
export const YONI_ANIMALS = Object.freeze([
    'Horse', 'Elephant', 'Sheep', 'Snake', 'Dog', 'Cat', 'Rat',
    'Cow', 'Buffalo', 'Tiger', 'Deer', 'Monkey', 'Mongoose', 'Lion'
]);

/**
 * Nadi classification for each nakshatra
 * 0 = Adi (Vata), 1 = Madhya (Pitta), 2 = Antya (Kapha)
 */
export const NAKSHATRA_NADI = Object.freeze([
    0, 1, 2, 2, 1, 0, 0, 1, 2,  // Ashwini to Ashlesha
    2, 1, 0, 0, 1, 2, 2, 1, 0,  // Magha to Jyeshtha
    0, 1, 2, 2, 1, 0, 0, 1, 2   // Mula to Revati
]);

/**
 * Nadi names
 */
export const NADI_NAMES = Object.freeze(['Adi', 'Madhya', 'Antya']);

// ============================================================================
// PLANET DATA
// ============================================================================

/**
 * Seven classical planets (Sapta Graha)
 */
export const SAPTA_GRAHA = Object.freeze([
    'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'
]);

/**
 * Nine planets including nodes (Navagraha)
 */
export const NAVAGRAHA = Object.freeze([
    'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'
]);

/**
 * Five non-luminary planets (Pancha Bhuta Graha)
 */
export const PANCHA_GRAHA = Object.freeze([
    'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'
]);

/**
 * Natural benefics and malefics
 * Per BPHS - Moon is benefic in Shukla Paksha (waxing)
 * Mercury is benefic when alone/with benefics
 */
export const NATURAL_BENEFICS = Object.freeze(['Jupiter', 'Venus']);
export const NATURAL_MALEFICS = Object.freeze(['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu']);
export const CONDITIONAL_PLANETS = Object.freeze(['Moon', 'Mercury']); // Depend on conditions

// ============================================================================
// PLANETARY DIGNITIES - Per BPHS Chapter 3
// ============================================================================

/**
 * Exaltation data
 * Includes exact degree of maximum exaltation
 */
export const EXALTATION = Object.freeze({
    Sun:     { sign: 0,  degree: 10 },  // Aries 10°
    Moon:    { sign: 1,  degree: 3 },   // Taurus 3°
    Mars:    { sign: 9,  degree: 28 },  // Capricorn 28°
    Mercury: { sign: 5,  degree: 15 },  // Virgo 15°
    Jupiter: { sign: 3,  degree: 5 },   // Cancer 5°
    Venus:   { sign: 11, degree: 27 },  // Pisces 27°
    Saturn:  { sign: 6,  degree: 20 },  // Libra 20°
    Rahu:    { sign: 1,  degree: 20 },  // Taurus 20° (varies by text)
    Ketu:    { sign: 7,  degree: 20 }   // Scorpio 20° (varies by text)
});

/**
 * Exaltation points in absolute degrees (0-360)
 * Useful for Uchcha Bala calculations
 */
export const EXALTATION_POINTS = Object.freeze({
    Sun: 10,       // Aries 10°
    Moon: 33,      // Taurus 3°
    Mars: 298,     // Capricorn 28°
    Mercury: 165,  // Virgo 15°
    Jupiter: 95,   // Cancer 5°
    Venus: 357,    // Pisces 27°
    Saturn: 200    // Libra 20°
});

/**
 * Debilitation signs (opposite of exaltation)
 */
export const DEBILITATION = Object.freeze({
    Sun: 6,      // Libra
    Moon: 7,     // Scorpio
    Mars: 3,     // Cancer
    Mercury: 11, // Pisces
    Jupiter: 9,  // Capricorn
    Venus: 5,    // Virgo
    Saturn: 0,   // Aries
    Rahu: 7,     // Scorpio
    Ketu: 1      // Taurus
});

/**
 * Own signs for each planet
 */
export const OWN_SIGNS = Object.freeze({
    Sun:     [4],       // Leo
    Moon:    [3],       // Cancer
    Mars:    [0, 7],    // Aries, Scorpio
    Mercury: [2, 5],    // Gemini, Virgo
    Jupiter: [8, 11],   // Sagittarius, Pisces
    Venus:   [1, 6],    // Taurus, Libra
    Saturn:  [9, 10],   // Capricorn, Aquarius
    Rahu:    [10],      // Aquarius (varies by tradition)
    Ketu:    [7]        // Scorpio (varies by tradition)
});

/**
 * Moolatrikona ranges
 * The portion of a planet's own sign where it has special strength
 * Format: { sign: signIndex, start: startDegree, end: endDegree }
 */
export const MOOLATRIKONA = Object.freeze({
    Sun:     { sign: 4,  start: 0,  end: 20 },  // Leo 0-20°
    Moon:    { sign: 1,  start: 3,  end: 30 },  // Taurus 3-30°
    Mars:    { sign: 0,  start: 0,  end: 12 },  // Aries 0-12°
    Mercury: { sign: 5,  start: 15, end: 20 },  // Virgo 15-20°
    Jupiter: { sign: 8,  start: 0,  end: 10 },  // Sagittarius 0-10°
    Venus:   { sign: 6,  start: 0,  end: 15 },  // Libra 0-15°
    Saturn:  { sign: 10, start: 0,  end: 20 }   // Aquarius 0-20°
});

/**
 * Complete dignity data for each planet
 * Consolidated structure for easy lookup
 */
export const PLANETARY_DIGNITIES = Object.freeze({
    Sun: {
        exalted: 0,
        exaltedDeg: [0, 10],
        debilitated: 6,
        own: [4],
        moola: { sign: 4, start: 0, end: 20 }
    },
    Moon: {
        exalted: 1,
        exaltedDeg: [0, 3],
        debilitated: 7,
        own: [3],
        moola: { sign: 1, start: 3, end: 30 }
    },
    Mars: {
        exalted: 9,
        exaltedDeg: [0, 28],
        debilitated: 3,
        own: [0, 7],
        moola: { sign: 0, start: 0, end: 12 }
    },
    Mercury: {
        exalted: 5,
        exaltedDeg: [0, 15],
        debilitated: 11,
        own: [2, 5],
        moola: { sign: 5, start: 15, end: 20 }
    },
    Jupiter: {
        exalted: 3,
        exaltedDeg: [0, 5],
        debilitated: 9,
        own: [8, 11],
        moola: { sign: 8, start: 0, end: 10 }
    },
    Venus: {
        exalted: 11,
        exaltedDeg: [0, 27],
        debilitated: 5,
        own: [1, 6],
        moola: { sign: 6, start: 0, end: 15 }
    },
    Saturn: {
        exalted: 6,
        exaltedDeg: [0, 20],
        debilitated: 0,
        own: [9, 10],
        moola: { sign: 10, start: 0, end: 20 }
    },
    Rahu: {
        exalted: 1,
        exaltedDeg: null,
        debilitated: 7,
        own: [10],
        moola: null
    },
    Ketu: {
        exalted: 7,
        exaltedDeg: null,
        debilitated: 1,
        own: [7],
        moola: null
    }
});

// ============================================================================
// PLANETARY RELATIONSHIPS - Per BPHS Chapter 3
// ============================================================================

/**
 * Natural friendships between planets
 */
export const NATURAL_FRIENDS = Object.freeze({
    Sun:     ['Moon', 'Mars', 'Jupiter'],
    Moon:    ['Sun', 'Mercury'],
    Mars:    ['Sun', 'Moon', 'Jupiter'],
    Mercury: ['Sun', 'Venus'],
    Jupiter: ['Sun', 'Moon', 'Mars'],
    Venus:   ['Mercury', 'Saturn'],
    Saturn:  ['Mercury', 'Venus'],
    Rahu:    ['Saturn', 'Venus', 'Mercury'],
    Ketu:    ['Mars', 'Jupiter']
});

/**
 * Natural enemies between planets
 */
export const NATURAL_ENEMIES = Object.freeze({
    Sun:     ['Saturn', 'Venus'],
    Moon:    [],
    Mars:    ['Mercury'],
    Mercury: ['Moon'],
    Jupiter: ['Mercury', 'Venus'],
    Venus:   ['Sun', 'Moon'],
    Saturn:  ['Sun', 'Moon', 'Mars'],
    Rahu:    ['Sun', 'Moon', 'Mars'],
    Ketu:    ['Saturn', 'Venus', 'Mercury']
});

/**
 * Natural neutral relationships (derived from friends/enemies)
 */
export const NATURAL_NEUTRALS = Object.freeze({
    Sun:     ['Mercury'],
    Moon:    ['Mars', 'Jupiter', 'Venus', 'Saturn'],
    Mars:    ['Venus', 'Saturn'],
    Mercury: ['Mars', 'Jupiter', 'Saturn'],
    Jupiter: ['Saturn'],
    Venus:   ['Mars', 'Jupiter'],
    Saturn:  ['Jupiter'],
    Rahu:    ['Jupiter'],
    Ketu:    ['Moon']
});

// ============================================================================
// PLANETARY ASPECTS - Per BPHS Chapter 28
// ============================================================================

/**
 * Houses aspected by each planet (from its position)
 * All planets aspect the 7th house
 * Mars additionally aspects 4th and 8th
 * Jupiter additionally aspects 5th and 9th
 * Saturn additionally aspects 3rd and 10th
 */
export const PLANETARY_ASPECTS = Object.freeze({
    Sun:     [7],
    Moon:    [7],
    Mars:    [4, 7, 8],
    Mercury: [7],
    Jupiter: [5, 7, 9],
    Venus:   [7],
    Saturn:  [3, 7, 10],
    Rahu:    [5, 7, 9],  // Follows Jupiter's aspects
    Ketu:    [5, 7, 9]   // Follows Jupiter's aspects
});

/**
 * Aspect strength percentages
 * Full (100%), Three-quarter (75%), Half (50%), Quarter (25%)
 */
export const ASPECT_STRENGTH = Object.freeze({
    full: 1.0,
    threeQuarter: 0.75,
    half: 0.5,
    quarter: 0.25
});

// ============================================================================
// HOUSE CLASSIFICATIONS
// ============================================================================

/**
 * Kendra houses (Angular) - 1, 4, 7, 10
 */
export const KENDRAS = Object.freeze([1, 4, 7, 10]);

/**
 * Trikona houses (Trinal) - 1, 5, 9
 */
export const TRIKONAS = Object.freeze([1, 5, 9]);

/**
 * Dusthana houses (Evil) - 6, 8, 12
 */
export const DUSTHANAS = Object.freeze([6, 8, 12]);

/**
 * Upachaya houses (Growth) - 3, 6, 10, 11
 */
export const UPACHAYAS = Object.freeze([3, 6, 10, 11]);

/**
 * Panapara houses (Succedent) - 2, 5, 8, 11
 */
export const PANAPARAS = Object.freeze([2, 5, 8, 11]);

/**
 * Apoklima houses (Cadent) - 3, 6, 9, 12
 */
export const APOKLIMAS = Object.freeze([3, 6, 9, 12]);

/**
 * Maraka houses (Death-inflicting) - 2, 7
 */
export const MARAKAS = Object.freeze([2, 7]);

/**
 * Trik houses (Evil triad) - 6, 8, 12
 */
export const TRIKS = Object.freeze([6, 8, 12]);

// ============================================================================
// COMBUSTION DATA - Per BPHS
// ============================================================================

/**
 * Combustion orbs in degrees
 * When a planet is within this distance from the Sun, it is combust
 */
export const COMBUSTION_ORBS = Object.freeze({
    Moon: 12,
    Mars: 17,
    Mercury: 14,
    MercuryRetro: 12,  // When retrograde
    Jupiter: 11,
    Venus: 10,
    VenusRetro: 8,     // When retrograde
    Saturn: 15
});

// ============================================================================
// DASHA PERIODS - Per BPHS Chapter 46
// ============================================================================

/**
 * Vimshottari Dasha periods in years
 * Total cycle: 120 years
 */
export const VIMSHOTTARI_YEARS = Object.freeze({
    Ketu:    7,
    Venus:   20,
    Sun:     6,
    Moon:    10,
    Mars:    7,
    Rahu:    18,
    Jupiter: 16,
    Saturn:  19,
    Mercury: 17
});

/**
 * Vimshottari Dasha sequence
 */
export const VIMSHOTTARI_SEQUENCE = Object.freeze([
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury'
]);

/**
 * Yogini Dasha periods in years
 * Total cycle: 36 years
 */
export const YOGINI_YEARS = Object.freeze({
    Mangala:   1,
    Pingala:   2,
    Dhanya:    3,
    Bhramari:  4,
    Bhadrika:  5,
    Ulka:      6,
    Siddha:    7,
    Sankata:   8
});

/**
 * Ashtottari Dasha periods in years
 * Total cycle: 108 years
 */
export const ASHTOTTARI_YEARS = Object.freeze({
    Sun:     6,
    Moon:    15,
    Mars:    8,
    Mercury: 17,
    Saturn:  10,
    Jupiter: 19,
    Rahu:    12,
    Venus:   21
});

// ============================================================================
// PANCHANG DATA
// ============================================================================

/**
 * 30 Tithis (15 Shukla + 15 Krishna)
 */
export const TITHI_NAMES = Object.freeze([
    'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
    'Shashthi', 'Saptami', 'Ashtami', 'Navami', 'Dashami',
    'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Purnima',
    'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
    'Shashthi', 'Saptami', 'Ashtami', 'Navami', 'Dashami',
    'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Amavasya'
]);

/**
 * 27 Nitya Yogas
 */
export const NITYA_YOGA_NAMES = Object.freeze([
    'Vishkumbha', 'Priti', 'Ayushman', 'Saubhagya', 'Shobhana',
    'Atiganda', 'Sukarma', 'Dhriti', 'Shula', 'Ganda',
    'Vriddhi', 'Dhruva', 'Vyaghata', 'Harshana', 'Vajra',
    'Siddhi', 'Vyatipata', 'Variyan', 'Parigha', 'Shiva',
    'Siddha', 'Sadhya', 'Shubha', 'Shukla', 'Brahma',
    'Indra', 'Vaidhriti'
]);

/**
 * 11 Karanas (7 moving + 4 fixed)
 */
export const KARANA_NAMES = Object.freeze([
    'Bava', 'Balava', 'Kaulava', 'Taitila', 'Gara', 'Vanija', 'Vishti',  // Moving
    'Shakuni', 'Chatushpada', 'Naga', 'Kimstughna'  // Fixed
]);

/**
 * Days of the week with planetary lords
 */
export const VARA_DATA = Object.freeze({
    0: { name: 'Sunday',    lord: 'Sun' },
    1: { name: 'Monday',    lord: 'Moon' },
    2: { name: 'Tuesday',   lord: 'Mars' },
    3: { name: 'Wednesday', lord: 'Mercury' },
    4: { name: 'Thursday',  lord: 'Jupiter' },
    5: { name: 'Friday',    lord: 'Venus' },
    6: { name: 'Saturday',  lord: 'Saturn' }
});

// ============================================================================
// SHADBALA REQUIREMENTS - Per BPHS Chapter 27
// ============================================================================

/**
 * Minimum Shadbala requirements in Rupas
 */
export const SHADBALA_REQUIREMENTS = Object.freeze({
    Sun:     6.5,
    Moon:    6.0,
    Mars:    5.0,
    Mercury: 7.0,
    Jupiter: 6.5,
    Venus:   5.5,
    Saturn:  5.0
});

/**
 * Naisargika Bala (Natural strength) in Virupas
 */
export const NAISARGIKA_BALA = Object.freeze({
    Sun:     60.00,
    Moon:    51.43,
    Venus:   42.86,
    Jupiter: 34.29,
    Mercury: 25.71,
    Mars:    17.14,
    Saturn:  8.57
});

/**
 * Directional strength points (Dig Bala)
 * House where each planet gets maximum directional strength
 */
export const DIG_BALA_HOUSES = Object.freeze({
    Sun:     10,  // 10th house (Midheaven)
    Mars:    10,  // 10th house
    Jupiter: 1,   // 1st house (Ascendant)
    Mercury: 1,   // 1st house
    Moon:    4,   // 4th house (IC)
    Venus:   4,   // 4th house
    Saturn:  7    // 7th house (Descendant)
});

// ============================================================================
// AYANAMSA DATA
// ============================================================================

/**
 * Ayanamsa values at J2000 epoch (Jan 1, 2000)
 * Different systems have different reference points
 */
export const AYANAMSA_J2000 = Object.freeze({
    Lahiri:        23.853056,   // Chitra Paksha - Most widely used
    Raman:         22.460000,   // B.V. Raman's system
    Krishnamurti:  23.780000,   // KP system
    Fagan:         24.040000,   // Fagan-Bradley
    DeLuce:        22.000000,   // Robert DeLuce
    Yukteshwar:    22.475000    // Sri Yukteshwar
});

/**
 * Annual precession rate in degrees
 * Approximate: 50.27" per year = 0.01397° per year
 */
export const PRECESSION_RATE = 0.01397;

// ============================================================================
// VARGA (DIVISIONAL) CHART DATA
// ============================================================================

/**
 * Standard divisional charts with their Sanskrit names
 */
export const VARGA_CHARTS = Object.freeze({
    D1:  { name: 'Rasi',           division: 1,  signification: 'Physical Body, General Life' },
    D2:  { name: 'Hora',           division: 2,  signification: 'Wealth' },
    D3:  { name: 'Drekkana',       division: 3,  signification: 'Siblings, Courage' },
    D4:  { name: 'Chaturthamsha',  division: 4,  signification: 'Fortune, Property' },
    D5:  { name: 'Panchamsha',     division: 5,  signification: 'Fame, Spiritual Practice' },
    D6:  { name: 'Shashthamsha',   division: 6,  signification: 'Health' },
    D7:  { name: 'Saptamsha',      division: 7,  signification: 'Children, Progeny' },
    D8:  { name: 'Ashtamsha',      division: 8,  signification: 'Longevity, Sudden Events' },
    D9:  { name: 'Navamsha',       division: 9,  signification: 'Spouse, Dharma, Fortune' },
    D10: { name: 'Dashamsha',      division: 10, signification: 'Career, Profession' },
    D11: { name: 'Ekadashamsha',   division: 11, signification: 'Gains, Death' },
    D12: { name: 'Dwadashamsha',   division: 12, signification: 'Parents' },
    D16: { name: 'Shodashamsha',   division: 16, signification: 'Vehicles, Comforts' },
    D20: { name: 'Vimshamsha',     division: 20, signification: 'Spiritual Progress' },
    D24: { name: 'Siddhamsha',     division: 24, signification: 'Education, Learning' },
    D27: { name: 'Bhamsha',        division: 27, signification: 'Strength, Weakness' },
    D30: { name: 'Trimshamsha',    division: 30, signification: 'Misfortunes, Evil' },
    D40: { name: 'Khavedamsha',    division: 40, signification: 'Auspicious/Inauspicious' },
    D45: { name: 'Akshavedamsha',  division: 45, signification: 'General Indications' },
    D60: { name: 'Shashtyamsha',   division: 60, signification: 'Past Life, Karma' },
    D81: { name: 'Nava-Navamsha',  division: 81, signification: 'Microscopic Details' },
    D108: { name: 'Ashtottaransh', division: 108, signification: 'Whole Life' },
    D144: { name: 'Dwadash-Dwadashamsha', division: 144, signification: 'Ancestral Karma' }
});

/**
 * Shodashvarga (16 important vargas) for strength calculation
 */
export const SHODASHVARGA = Object.freeze([
    'D1', 'D2', 'D3', 'D4', 'D7', 'D9', 'D10', 'D12',
    'D16', 'D20', 'D24', 'D27', 'D30', 'D40', 'D45', 'D60'
]);

/**
 * Saptavarga (7 vargas for Shadbala)
 */
export const SAPTAVARGA = Object.freeze(['D1', 'D2', 'D3', 'D7', 'D9', 'D12', 'D30']);

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Get sign lord for a given sign index
 * @param {number} signIndex - Sign index (0-11)
 * @returns {string} Lord planet name
 */
export function getSignLord(signIndex) {
    return SIGN_LORDS[signIndex % 12];
}

/**
 * Check if a planet is in its own sign
 * @param {string} planet - Planet name
 * @param {number} signIndex - Sign index (0-11)
 * @returns {boolean}
 */
export function isOwnSign(planet, signIndex) {
    const own = OWN_SIGNS[planet];
    return own ? own.includes(signIndex) : false;
}

/**
 * Check if a planet is exalted in a sign
 * @param {string} planet - Planet name
 * @param {number} signIndex - Sign index (0-11)
 * @returns {boolean}
 */
export function isExalted(planet, signIndex) {
    const data = EXALTATION[planet];
    return data ? data.sign === signIndex : false;
}

/**
 * Check if a planet is debilitated in a sign
 * @param {string} planet - Planet name
 * @param {number} signIndex - Sign index (0-11)
 * @returns {boolean}
 */
export function isDebilitated(planet, signIndex) {
    return DEBILITATION[planet] === signIndex;
}

/**
 * Check if a planet is in Moolatrikona
 * @param {string} planet - Planet name
 * @param {number} signIndex - Sign index (0-11)
 * @param {number} degree - Degree within sign (0-30)
 * @returns {boolean}
 */
export function isMoolatrikona(planet, signIndex, degree) {
    const mt = MOOLATRIKONA[planet];
    if (!mt) return false;
    return mt.sign === signIndex && degree >= mt.start && degree < mt.end;
}

/**
 * Get the dignity status of a planet
 * @param {string} planet - Planet name
 * @param {number} signIndex - Sign index (0-11)
 * @param {number} degree - Degree within sign (0-30)
 * @returns {string} 'exalted' | 'debilitated' | 'moolatrikona' | 'own' | 'neutral'
 */
export function getDignity(planet, signIndex, degree = 15) {
    if (isExalted(planet, signIndex)) return 'exalted';
    if (isDebilitated(planet, signIndex)) return 'debilitated';
    if (isMoolatrikona(planet, signIndex, degree)) return 'moolatrikona';
    if (isOwnSign(planet, signIndex)) return 'own';
    return 'neutral';
}

/**
 * Get natural relationship between two planets
 * @param {string} planet1 - First planet
 * @param {string} planet2 - Second planet
 * @returns {string} 'Friend' | 'Enemy' | 'Neutral'
 */
export function getNaturalRelationship(planet1, planet2) {
    if (NATURAL_FRIENDS[planet1]?.includes(planet2)) return 'Friend';
    if (NATURAL_ENEMIES[planet1]?.includes(planet2)) return 'Enemy';
    return 'Neutral';
}

/**
 * Calculate house number from one longitude to another
 * @param {number} fromLon - Starting longitude
 * @param {number} toLon - Target longitude
 * @returns {number} House number (1-12)
 */
export function getHouseNumber(fromLon, toLon) {
    let diff = toLon - fromLon;
    if (diff < 0) diff += 360;
    return Math.floor(diff / 30) + 1;
}

/**
 * Get Nakshatra index from longitude
 * @param {number} longitude - Sidereal longitude (0-360)
 * @returns {number} Nakshatra index (0-26)
 */
export function getNakshatraIndex(longitude) {
    return Math.floor(longitude / NAKSHATRA_SPAN);
}

/**
 * Get Nakshatra pada (quarter) from longitude
 * @param {number} longitude - Sidereal longitude (0-360)
 * @returns {number} Pada (1-4)
 */
export function getNakshatraPada(longitude) {
    const posInNak = longitude % NAKSHATRA_SPAN;
    return Math.floor(posInNak / (NAKSHATRA_SPAN / 4)) + 1;
}

/**
 * Check if a house is a Kendra
 * @param {number} house - House number (1-12)
 * @returns {boolean}
 */
export function isKendra(house) {
    return KENDRAS.includes(house);
}

/**
 * Check if a house is a Trikona
 * @param {number} house - House number (1-12)
 * @returns {boolean}
 */
export function isTrikona(house) {
    return TRIKONAS.includes(house);
}

/**
 * Check if a house is a Dusthana
 * @param {number} house - House number (1-12)
 * @returns {boolean}
 */
export function isDusthana(house) {
    return DUSTHANAS.includes(house);
}

/**
 * Check if a planet is naturally benefic
 * @param {string} planet - Planet name
 * @param {boolean} moonWaxing - Is Moon in Shukla Paksha
 * @param {boolean} mercuryWithBenefics - Is Mercury with benefics only
 * @returns {boolean}
 */
export function isNaturalBenefic(planet, moonWaxing = true, mercuryWithBenefics = true) {
    if (NATURAL_BENEFICS.includes(planet)) return true;
    if (planet === 'Moon' && moonWaxing) return true;
    if (planet === 'Mercury' && mercuryWithBenefics) return true;
    return false;
}

/**
 * Check if a planet is naturally malefic
 * @param {string} planet - Planet name
 * @param {boolean} moonWaning - Is Moon in Krishna Paksha
 * @param {boolean} mercuryWithMalefics - Is Mercury with malefics
 * @returns {boolean}
 */
export function isNaturalMalefic(planet, moonWaning = false, mercuryWithMalefics = false) {
    if (NATURAL_MALEFICS.includes(planet)) return true;
    if (planet === 'Moon' && moonWaning) return true;
    if (planet === 'Mercury' && mercuryWithMalefics) return true;
    return false;
}
