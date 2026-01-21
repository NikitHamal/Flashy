import I18n from '../core/i18n.js';
import { RASI_NAMES, NAKSHATRA_NAMES } from './constants.js';

/**
 * Production-Grade Vedic Ashtakoota Matchmaking Calculator
 * 
 * Implements complete Ashtakoota (8 Koota) matching system with:
 * - All 8 koota calculations with verified matrices
 * - Nadi Dosha exception rules
 * - Bhakoot Dosha cancellation rules
 * - Detailed interpretations
 * 
 * Based on classical Vedic texts and standard astrological practices.
 */

// ============================================================================
// CONSTANTS AND DATA TABLES
// ============================================================================

/**
 * Maximum points for each Koota
 */
const KOOTA_MAX_POINTS = {
    varna: 1,
    vashya: 2,
    tara: 3,
    yoni: 4,
    maitri: 5,
    gana: 6,
    bhakoot: 7,
    nadi: 8
};

// Advanced/Additional Kootas (Non-point based overrides)
const ADDITIONAL_KOOTAS = {
    mahendra: { name: 'Mahendra', meaning: 'Longevity and Progeny' },
    stri_deergha: { name: 'Stri-Deergha', meaning: 'Wealth and Prosperity' },
    rajju: { name: 'Rajju', meaning: 'The most critical Dosha (Marriage stability)' }
};

/**
 * Total maximum points possible: 36
 */
const TOTAL_MAX_POINTS = 36;

// ----------------------------------------------------------------------------
// 1. VARNA (1 Point) - Spiritual/Social Compatibility
// ----------------------------------------------------------------------------
// Based on Moon Sign classification into 4 Varnas
// Brahmin (4) > Kshatriya (3) > Vaishya (2) > Shudra (1)
// Boy's Varna should be >= Girl's Varna for compatibility

const VARNA_BY_RASI = {
    // Cancer (3), Scorpio (7), Pisces (11) = Brahmin (Water signs)
    3: 4, 7: 4, 11: 4,
    // Aries (0), Leo (4), Sagittarius (8) = Kshatriya (Fire signs)
    0: 3, 4: 3, 8: 3,
    // Taurus (1), Virgo (5), Capricorn (9) = Vaishya (Earth signs)
    1: 2, 5: 2, 9: 2,
    // Gemini (2), Libra (6), Aquarius (10) = Shudra (Air signs)
    2: 1, 6: 1, 10: 1
};

const VARNA_NAMES = {
    4: 'Brahmin',
    3: 'Kshatriya',
    2: 'Vaishya',
    1: 'Shudra'
};

// ----------------------------------------------------------------------------
// 2. VASHYA (2 Points) - Dominance/Control Compatibility
// ----------------------------------------------------------------------------
// 5 Types: Chatushpad (Quadruped), Manav (Human), Jalchar (Aquatic), 
//          Vanchar (Wild), Keet (Insect)

const VASHYA_TYPES = {
    CHATUSHPAD: 0,  // Quadruped
    MANAV: 1,       // Human
    JALCHAR: 2,     // Aquatic
    VANCHAR: 3,     // Wild/Forest
    KEET: 4         // Insect/Reptile
};

// Rasi to Vashya Type mapping (0-indexed Rasi)
const RASI_VASHYA_TYPE = {
    0: VASHYA_TYPES.CHATUSHPAD,  // Aries - Quadruped (Ram)
    1: VASHYA_TYPES.CHATUSHPAD,  // Taurus - Quadruped (Bull)
    2: VASHYA_TYPES.MANAV,       // Gemini - Human
    3: VASHYA_TYPES.JALCHAR,     // Cancer - Aquatic (Crab)
    4: VASHYA_TYPES.VANCHAR,     // Leo - Wild (Lion)
    5: VASHYA_TYPES.MANAV,       // Virgo - Human
    6: VASHYA_TYPES.MANAV,       // Libra - Human
    7: VASHYA_TYPES.KEET,        // Scorpio - Insect (Scorpion)
    8: VASHYA_TYPES.MANAV,       // Sagittarius - Human (first half dominant)
    9: VASHYA_TYPES.JALCHAR,    // Capricorn - Aquatic (Sea-goat, latter half)
    10: VASHYA_TYPES.MANAV,      // Aquarius - Human
    11: VASHYA_TYPES.JALCHAR     // Pisces - Aquatic (Fish)
};

const VASHYA_TYPE_NAMES = ['Chatushpad', 'Manav', 'Jalchar', 'Vanchar', 'Keet'];

// Vashya compatibility matrix [Boy Type][Girl Type]
// Types: 0=Chatushpad, 1=Manav, 2=Jalchar, 3=Vanchar, 4=Keet
const VASHYA_MATRIX = [
    //       Chat  Man   Jal   Van   Keet
    /* Chat */[2, 1, 1, 0.5, 1],
    /* Man  */[1, 2, 0.5, 0, 1],
    /* Jal  */[1, 0.5, 2, 1, 1],
    /* Van  */[0, 0, 1, 2, 0],
    /* Keet */[1, 1, 1, 0, 2]
];

// ----------------------------------------------------------------------------
// 3. TARA (3 Points) - Destiny/Health Compatibility
// ----------------------------------------------------------------------------
// Based on Nakshatra positions, bidirectional counting
// Janma (1), Sampat (2), Vipat (3), Kshema (4), Pratyari (5), 
// Sadhana (6), Vadha (7), Mitra (8), Param Mitra (9)
// Positions 3, 5, 7 are inauspicious

const TARA_NAMES = [
    '', 'Janma', 'Sampat', 'Vipat', 'Kshema', 'Pratyari',
    'Sadhana', 'Vadha', 'Mitra', 'Param Mitra'
];

const INAUSPICIOUS_TARAS = [3, 5, 7]; // Vipat, Pratyari, Vadha

// ----------------------------------------------------------------------------
// 4. YONI (4 Points) - Physical/Sexual Compatibility  
// ----------------------------------------------------------------------------
// 14 Animal types mapped to 27 Nakshatras

const YONI_ANIMALS = {
    HORSE: 0,
    ELEPHANT: 1,
    SHEEP: 2,
    SNAKE: 3,
    DOG: 4,
    CAT: 5,
    RAT: 6,
    COW: 7,
    BUFFALO: 8,
    TIGER: 9,
    DEER: 10,
    MONKEY: 11,
    MONGOOSE: 12,
    LION: 13
};

const YONI_ANIMAL_NAMES = [
    'Horse', 'Elephant', 'Sheep', 'Snake', 'Dog', 'Cat', 'Rat',
    'Cow', 'Buffalo', 'Tiger', 'Deer', 'Monkey', 'Mongoose', 'Lion'
];

// Nakshatra (0-26) to Yoni Animal mapping
const NAKSHATRA_YONI = [
    /* 0  Ashwini      */ YONI_ANIMALS.HORSE,
    /* 1  Bharani      */ YONI_ANIMALS.ELEPHANT,
    /* 2  Krittika     */ YONI_ANIMALS.SHEEP,
    /* 3  Rohini       */ YONI_ANIMALS.SNAKE,
    /* 4  Mrigashira   */ YONI_ANIMALS.SNAKE,
    /* 5  Ardra        */ YONI_ANIMALS.DOG,
    /* 6  Punarvasu    */ YONI_ANIMALS.CAT,
    /* 7  Pushya       */ YONI_ANIMALS.SHEEP,
    /* 8  Ashlesha     */ YONI_ANIMALS.CAT,
    /* 9  Magha        */ YONI_ANIMALS.RAT,
    /* 10 Purva Phalguni */ YONI_ANIMALS.RAT,
    /* 11 Uttara Phalguni */ YONI_ANIMALS.COW,
    /* 12 Hasta        */ YONI_ANIMALS.BUFFALO,
    /* 13 Chitra       */ YONI_ANIMALS.TIGER,
    /* 14 Swati        */ YONI_ANIMALS.BUFFALO,
    /* 15 Vishakha     */ YONI_ANIMALS.TIGER,
    /* 16 Anuradha     */ YONI_ANIMALS.DEER,
    /* 17 Jyeshtha     */ YONI_ANIMALS.DEER,
    /* 18 Mula         */ YONI_ANIMALS.DOG,
    /* 19 Purva Ashadha */ YONI_ANIMALS.MONKEY,
    /* 20 Uttara Ashadha */ YONI_ANIMALS.MONGOOSE,
    /* 21 Shravana     */ YONI_ANIMALS.MONKEY,
    /* 22 Dhanishta    */ YONI_ANIMALS.LION,
    /* 23 Shatabhisha  */ YONI_ANIMALS.HORSE,
    /* 24 P.Bhadrapada */ YONI_ANIMALS.LION,
    /* 25 U.Bhadrapada */ YONI_ANIMALS.COW,
    /* 26 Revati       */ YONI_ANIMALS.ELEPHANT
];

// Yoni compatibility matrix [Animal1][Animal2]
// 4 = Same animal (M/F pair), Enemy pairs = 0-1, Neutral = 2, Friendly = 3
const YONI_MATRIX = [
    //       Hrs  Elp  Shp  Snk  Dog  Cat  Rat  Cow  Buf  Tig  Der  Mon  Mgn  Lio
    /* Horse    */[4, 2, 2, 3, 2, 2, 2, 1, 0, 1, 3, 2, 2, 1],
    /* Elephant */[2, 4, 3, 3, 2, 2, 2, 2, 3, 1, 2, 3, 2, 0],
    /* Sheep    */[2, 3, 4, 2, 1, 2, 1, 3, 3, 1, 2, 0, 3, 1],
    /* Snake    */[3, 3, 2, 4, 2, 1, 1, 1, 1, 2, 2, 2, 0, 2],
    /* Dog      */[2, 2, 1, 2, 4, 2, 1, 2, 2, 1, 0, 2, 1, 1],
    /* Cat      */[2, 2, 2, 1, 2, 4, 0, 2, 2, 1, 2, 2, 2, 1],
    /* Rat      */[2, 2, 1, 1, 1, 0, 4, 2, 2, 2, 2, 2, 1, 2],
    /* Cow      */[1, 2, 3, 1, 2, 2, 2, 4, 3, 0, 3, 2, 2, 1],
    /* Buffalo  */[0, 3, 3, 1, 2, 2, 2, 3, 4, 1, 2, 2, 2, 1],
    /* Tiger    */[1, 1, 1, 2, 1, 1, 2, 0, 1, 4, 1, 1, 2, 1],
    /* Deer     */[3, 2, 2, 2, 0, 2, 2, 3, 2, 1, 4, 2, 2, 1],
    /* Monkey   */[2, 3, 0, 2, 2, 2, 2, 2, 2, 1, 2, 4, 3, 2],
    /* Mongoose */[2, 2, 3, 0, 1, 2, 1, 2, 2, 2, 2, 3, 4, 2],
    /* Lion     */[1, 0, 1, 2, 1, 1, 2, 1, 1, 1, 1, 2, 2, 4]
];

// ----------------------------------------------------------------------------
// 5. GRAHA MAITRI (5 Points) - Mental/Psychological Compatibility
// ----------------------------------------------------------------------------
// Based on friendship between lords of Moon signs

const RASI_LORD = {
    0: 'Mars',      // Aries
    1: 'Venus',     // Taurus
    2: 'Mercury',   // Gemini
    3: 'Moon',      // Cancer
    4: 'Sun',       // Leo
    5: 'Mercury',   // Virgo
    6: 'Venus',     // Libra
    7: 'Mars',      // Scorpio
    8: 'Jupiter',   // Sagittarius
    9: 'Saturn',   // Capricorn
    10: 'Saturn',   // Aquarius
    11: 'Jupiter'   // Pisces
};

// Planetary friendship: F=Friend, N=Neutral, E=Enemy
const PLANETARY_FRIENDSHIP = {
    'Sun': { 'Sun': 'F', 'Moon': 'F', 'Mars': 'F', 'Mercury': 'N', 'Jupiter': 'F', 'Venus': 'E', 'Saturn': 'E' },
    'Moon': { 'Sun': 'F', 'Moon': 'F', 'Mars': 'N', 'Mercury': 'F', 'Jupiter': 'N', 'Venus': 'N', 'Saturn': 'N' },
    'Mars': { 'Sun': 'F', 'Moon': 'F', 'Mars': 'F', 'Mercury': 'E', 'Jupiter': 'F', 'Venus': 'N', 'Saturn': 'N' },
    'Mercury': { 'Sun': 'F', 'Moon': 'E', 'Mars': 'N', 'Mercury': 'F', 'Jupiter': 'N', 'Venus': 'F', 'Saturn': 'N' },
    'Jupiter': { 'Sun': 'F', 'Moon': 'F', 'Mars': 'F', 'Mercury': 'E', 'Jupiter': 'F', 'Venus': 'E', 'Saturn': 'N' },
    'Venus': { 'Sun': 'E', 'Moon': 'E', 'Mars': 'N', 'Mercury': 'F', 'Jupiter': 'N', 'Venus': 'F', 'Saturn': 'F' },
    'Saturn': { 'Sun': 'E', 'Moon': 'E', 'Mars': 'E', 'Mercury': 'F', 'Jupiter': 'N', 'Venus': 'F', 'Saturn': 'F' }
};

// Maitri points based on mutual relationship
// Both Friends: 5, Friend+Neutral: 4, Both Neutral: 3
// Friend+Enemy: 1, Neutral+Enemy: 0.5, Both Enemy: 0
function getMaitriPoints(rel1, rel2) {
    if (rel1 === 'F' && rel2 === 'F') return 5;
    if ((rel1 === 'F' && rel2 === 'N') || (rel1 === 'N' && rel2 === 'F')) return 4;
    if (rel1 === 'N' && rel2 === 'N') return 3;
    if ((rel1 === 'F' && rel2 === 'E') || (rel1 === 'E' && rel2 === 'F')) return 1;
    if ((rel1 === 'N' && rel2 === 'E') || (rel1 === 'E' && rel2 === 'N')) return 0.5;
    if (rel1 === 'E' && rel2 === 'E') return 0;
    return 0;
}

// ----------------------------------------------------------------------------
// 6. GANA (6 Points) - Temperament Compatibility
// ----------------------------------------------------------------------------
// 3 Types: Deva (Divine), Manushya (Human), Rakshasa (Demon)

const GANA_TYPES = {
    DEVA: 0,
    MANUSHYA: 1,
    RAKSHASA: 2
};

const GANA_NAMES = ['Deva', 'Manushya', 'Rakshasa'];

// Nakshatra (0-26) to Gana mapping
const NAKSHATRA_GANA = [
    /* 0  Ashwini      */ GANA_TYPES.DEVA,
    /* 1  Bharani      */ GANA_TYPES.MANUSHYA,
    /* 2  Krittika     */ GANA_TYPES.RAKSHASA,
    /* 3  Rohini       */ GANA_TYPES.MANUSHYA,
    /* 4  Mrigashira   */ GANA_TYPES.DEVA,
    /* 5  Ardra        */ GANA_TYPES.MANUSHYA,
    /* 6  Punarvasu    */ GANA_TYPES.DEVA,
    /* 7  Pushya       */ GANA_TYPES.DEVA,
    /* 8  Ashlesha     */ GANA_TYPES.RAKSHASA,
    /* 9  Magha        */ GANA_TYPES.RAKSHASA,
    /* 10 Purva Phalguni */ GANA_TYPES.MANUSHYA,
    /* 11 Uttara Phalguni */ GANA_TYPES.MANUSHYA,
    /* 12 Hasta        */ GANA_TYPES.DEVA,
    /* 13 Chitra       */ GANA_TYPES.RAKSHASA,
    /* 14 Swati        */ GANA_TYPES.DEVA,
    /* 15 Vishakha     */ GANA_TYPES.RAKSHASA,
    /* 16 Anuradha     */ GANA_TYPES.DEVA,
    /* 17 Jyeshtha     */ GANA_TYPES.RAKSHASA,
    /* 18 Mula         */ GANA_TYPES.RAKSHASA,
    /* 19 Purva Ashadha */ GANA_TYPES.MANUSHYA,
    /* 20 Uttara Ashadha */ GANA_TYPES.MANUSHYA,
    /* 21 Shravana     */ GANA_TYPES.DEVA,
    /* 22 Dhanishta    */ GANA_TYPES.RAKSHASA,
    /* 23 Shatabhisha  */ GANA_TYPES.RAKSHASA,
    /* 24 P.Bhadrapada */ GANA_TYPES.MANUSHYA,
    /* 25 U.Bhadrapada */ GANA_TYPES.MANUSHYA,
    /* 26 Revati       */ GANA_TYPES.DEVA
];

// Gana compatibility matrix [Boy Gana][Girl Gana]
const GANA_MATRIX = [
    //       Deva  Manushya  Rakshasa
    /* Deva     */[6, 6, 1],
    /* Manushya */[6, 6, 0],
    /* Rakshasa */[1, 0, 6]
];

// ----------------------------------------------------------------------------
// 7. BHAKOOT (7 Points) - Emotional/Financial Compatibility
// ----------------------------------------------------------------------------
// Based on Moon sign positions (rasi position from each other)
// Doshas: 2/12 (Dwi-Dwadash), 5/9 (Nav-Pancham), 6/8 (Shadashtak)

const BHAKOOT_DOSHA_TYPES = {
    NONE: 'none',
    DWI_DWADASH: '2/12',      // 2-12 relationship
    NAV_PANCHAM: '5/9',       // 5-9 relationship
    SHADASHTAK: '6/8'         // 6-8 relationship
};

// Distance to Bhakoot points (1=same sign, 7=opposite)
const BHAKOOT_POINTS_BY_DISTANCE = {
    1: 7,   // Same sign
    2: 0,   // 2/12 Dosha
    3: 7,   // 3/11 - Good
    4: 7,   // 4/10 - Good  
    5: 0,   // 5/9 Dosha
    6: 0,   // 6/8 Dosha
    7: 7,   // Opposite (7/7) - Good
    8: 0,   // 6/8 Dosha (reverse)
    9: 0,   // 5/9 Dosha (reverse)
    10: 7,  // 4/10 - Good
    11: 7,  // 3/11 - Good
    12: 0   // 2/12 Dosha (reverse)
};

// ----------------------------------------------------------------------------
// 8. NADI (8 Points) - Physiological/Health Compatibility
// ----------------------------------------------------------------------------
// 3 Nadis: Adi (Vata), Madhya (Pitta), Antya (Kapha)
// Same Nadi = Nadi Dosha (0 points)

const NADI_TYPES = {
    ADI: 0,
    MADHYA: 1,
    ANTYA: 2
};

const NADI_NAMES = ['Adi', 'Madhya', 'Antya'];

// Nakshatra (0-26) to Nadi mapping
const NAKSHATRA_NADI = [
    0, 1, 2, 2, 1, 0, 0, 1, 2, // Ashwini to Ashlesha
    2, 1, 0, 0, 1, 2, 2, 1, 0, // Magha to Jyeshtha
    0, 1, 2, 2, 1, 0, 0, 1, 2  // Mula to Revati
];

// ============================================================================
// CORE ASHTAKOOTA CALCULATIONS
// ============================================================================

/**
 * Calculate Varna Koota (1 point max)
 */
function calculateVarna(boyRasi, girlRasi) {
    const boyVarna = VARNA_BY_RASI[boyRasi];
    const girlVarna = VARNA_BY_RASI[girlRasi];
    const score = boyVarna >= girlVarna ? 1 : 0;

    const bName = I18n.t(`matching.names.varna.${boyVarna}`);
    const gName = I18n.t(`matching.names.varna.${girlVarna}`);

    return {
        score: score,
        max: KOOTA_MAX_POINTS.varna,
        boyVarna: boyVarna,
        girlVarna: girlVarna,
        boyVarnaName: bName,
        girlVarnaName: gName,
        description: score === 1
            ? I18n.t('matching.varna.compatible', { boy: bName, girl: gName })
            : I18n.t('matching.varna.low', { boy: bName, girl: gName })
    };
}

/**
 * Calculate Vashya Koota (2 points max)
 */
function calculateVashya(boyRasi, girlRasi) {
    const boyType = RASI_VASHYA_TYPE[boyRasi];
    const girlType = RASI_VASHYA_TYPE[girlRasi];
    const score = VASHYA_MATRIX[boyType][girlType];

    const bTypeName = I18n.t(`matching.names.vashya.${boyType}`);
    const gTypeName = I18n.t(`matching.names.vashya.${girlType}`);

    return {
        score: score,
        max: KOOTA_MAX_POINTS.vashya,
        boyType: boyType,
        girlType: girlType,
        boyTypeName: bTypeName,
        girlTypeName: gTypeName,
        description: I18n.t('matching.vashya.desc', { boy: bTypeName, girl: gTypeName })
    };
}

/**
 * Calculate Tara Koota (3 points max)
 */
function calculateTara(boyNak, girlNak) {
    let countGB = ((boyNak - girlNak + 27) % 27) + 1;
    let countBG = ((girlNak - boyNak + 27) % 27) + 1;

    const taraGB = ((countGB - 1) % 9) + 1;
    const taraBG = ((countBG - 1) % 9) + 1;

    const isGBBad = INAUSPICIOUS_TARAS.includes(taraGB);
    const isBGBad = INAUSPICIOUS_TARAS.includes(taraBG);

    let score = 3;
    if (isGBBad && isBGBad) score = 0;
    else if (isGBBad || isBGBad) score = 1.5;

    return {
        score: score,
        max: KOOTA_MAX_POINTS.tara,
        boyTara: taraBG,
        girlTara: taraGB,
        boyTaraName: TARA_NAMES[taraBG],
        girlTaraName: TARA_NAMES[taraGB],
        description: I18n.t('matching.tara.desc', { boy: TARA_NAMES[taraBG], girl: TARA_NAMES[taraGB] })
    };
}

/**
 * Calculate Yoni Koota (4 points max)
 */
function calculateYoni(boyNak, girlNak) {
    const boyYoni = NAKSHATRA_YONI[boyNak];
    const girlYoni = NAKSHATRA_YONI[girlNak];
    const score = YONI_MATRIX[boyYoni][girlYoni];

    const bAnimal = YONI_ANIMAL_NAMES[boyYoni];
    const gAnimal = YONI_ANIMAL_NAMES[girlYoni];

    return {
        score: score,
        max: KOOTA_MAX_POINTS.yoni,
        boyYoni: boyYoni,
        girlYoni: girlYoni,
        boyAnimal: bAnimal,
        girlAnimal: gAnimal,
        description: I18n.t('matching.yoni.desc', { boy: bAnimal, girl: gAnimal })
    };
}

/**
 * Calculate Graha Maitri Koota (5 points max)
 */
function calculateMaitri(boyRasi, girlRasi) {
    const boyLord = RASI_LORD[boyRasi];
    const girlLord = RASI_LORD[girlRasi];

    const bLordName = I18n.t(`planets.${boyLord}`);
    const gLordName = I18n.t(`planets.${girlLord}`);

    if (boyLord === girlLord) {
        return {
            score: 5,
            max: KOOTA_MAX_POINTS.maitri,
            boyLord: boyLord,
            girlLord: girlLord,
            sameLord: true,
            relationship: 'Same Lord',
            description: I18n.t('matching.maitri.same_lord', { lord: bLordName })
        };
    }

    const boyToGirl = PLANETARY_FRIENDSHIP[boyLord][girlLord];
    const girlToBoy = PLANETARY_FRIENDSHIP[girlLord][boyLord];
    const score = getMaitriPoints(boyToGirl, girlToBoy);

    let relKey = '';
    if (boyToGirl === 'F' && girlToBoy === 'F') relKey = 'mutual_friends';
    else if (boyToGirl === 'E' && girlToBoy === 'E') relKey = 'mutual_enemies';
    else if (boyToGirl === 'N' && girlToBoy === 'N') relKey = 'mutual_neutrals';
    
    let relationship = relKey ? I18n.t(`matching.maitri.${relKey}`) : `${getRelationshipName(boyToGirl)}, ${getRelationshipName(girlToBoy)}`;

    return {
        score: score,
        max: KOOTA_MAX_POINTS.maitri,
        boyLord: boyLord,
        girlLord: girlLord,
        sameLord: false,
        boyToGirl: boyToGirl,
        girlToBoy: girlToBoy,
        relationship: relationship,
        description: I18n.t('matching.maitri.desc', { boy: bLordName, girl: gLordName, rel: relationship })
    };
}

/**
 * Calculate Gana Koota (6 points max)
 */
function calculateGana(boyNak, girlNak) {
    const boyGana = NAKSHATRA_GANA[boyNak];
    const girlGana = NAKSHATRA_GANA[girlNak];
    const score = GANA_MATRIX[boyGana][girlGana];

    const bName = GANA_NAMES[boyGana];
    const gName = GANA_NAMES[girlGana];

    return {
        score: score,
        max: KOOTA_MAX_POINTS.gana,
        boyGana: boyGana,
        girlGana: girlGana,
        boyGanaName: bName,
        girlGanaName: gName,
        description: I18n.t('matching.gana.desc', { boy: bName, girl: gName })
    };
}

/**
 * Calculate Bhakoot Koota (7 points max)
 */
function calculateBhakoot(boyRasi, girlRasi) {
    // 0-indexed distance calculation (1-12)
    const distBG = ((girlRasi - boyRasi + 12) % 12) + 1;
    let score = BHAKOOT_POINTS_BY_DISTANCE[distBG];

    let doshaType = BHAKOOT_DOSHA_TYPES.NONE;
    if (distBG === 2 || distBG === 12) doshaType = BHAKOOT_DOSHA_TYPES.DWI_DWADASH;
    else if (distBG === 5 || distBG === 9) doshaType = BHAKOOT_DOSHA_TYPES.NAV_PANCHAM;
    else if (distBG === 6 || distBG === 8) doshaType = BHAKOOT_DOSHA_TYPES.SHADASHTAK;

    let cancelled = false;
    let cancellationReason = null;

    if (doshaType !== BHAKOOT_DOSHA_TYPES.NONE) {
        const boyLord = RASI_LORD[boyRasi];
        const girlLord = RASI_LORD[girlRasi];

        if (boyLord === girlLord) {
            cancelled = true;
            cancellationReason = I18n.t('matching.bhakoot.same_lord_reason', { lord: I18n.t(`planets.${boyLord}`) });
            score = 7;
        }

        if (!cancelled) {
            const boyToGirl = PLANETARY_FRIENDSHIP[boyLord][girlLord];
            const girlToBoy = PLANETARY_FRIENDSHIP[girlLord][boyLord];
            if (boyToGirl === 'F' && girlToBoy === 'F') {
                cancelled = true;
                cancellationReason = I18n.t('matching.bhakoot.mutual_friends_reason', { bLord: I18n.t(`planets.${boyLord}`), gLord: I18n.t(`planets.${girlLord}`) });
                score = 7;
            }
        }
    }

    return {
        score: score,
        max: KOOTA_MAX_POINTS.bhakoot,
        distance: distBG,
        doshaType: doshaType,
        hasDosha: doshaType !== BHAKOOT_DOSHA_TYPES.NONE && !cancelled,
        cancelled: cancelled,
        cancellationReason: cancellationReason,
        description: cancelled 
            ? I18n.t('matching.bhakoot.cancelled', { reason: cancellationReason })
            : (score === 0 ? I18n.t('matching.bhakoot.dosha', { type: doshaType }) : I18n.t('matching.bhakoot.safe'))
    };
}

/**
 * Calculate Nadi Koota (8 points max)
 */
function calculateNadi(boyNak, girlNak, boyRasi, girlRasi, bPada, gPada) {
    const boyNadi = NAKSHATRA_NADI[boyNak];
    const girlNadi = NAKSHATRA_NADI[girlNak];
    const sameNadi = boyNadi === girlNadi;
    
    let score = sameNadi ? 0 : 8;
    let hasDosha = sameNadi;
    let exception = false;
    let exceptionReason = null;

    if (sameNadi) {
        if (boyNak === girlNak) {
            if (boyRasi !== girlRasi) {
                exception = true;
                exceptionReason = 'Same Nakshatra but different Rasi';
            } else if (bPada !== gPada) {
                exception = true;
                exceptionReason = 'Same Nakshatra and Rasi but different Padas';
            }
        }

        if (!exception) {
            const boyLord = RASI_LORD[boyRasi];
            const girlLord = RASI_LORD[girlRasi];
            const beneficLords = ['Jupiter', 'Venus', 'Mercury'];

            if (beneficLords.includes(boyLord) && beneficLords.includes(girlLord)) {
                exception = true;
                exceptionReason = I18n.t('matching.nadi.benefic_lord_exception', { bLord: I18n.t(`planets.${boyLord}`), gLord: I18n.t(`planets.${girlLord}`) });
            }
        }

        if (exception) {
            score = 8;
            hasDosha = false;
        }
    }

    const bNadiName = NADI_NAMES[boyNadi];

    return {
        score: score,
        max: KOOTA_MAX_POINTS.nadi,
        boyNadi: boyNadi,
        girlNadi: girlNadi,
        boyNadiName: bNadiName,
        girlNadiName: I18n.t(`matching.names.nadi.${girlNadi}`),
        sameNadi: sameNadi,
        hasDosha: hasDosha,
        exception: exception,
        exceptionReason: exceptionReason,
        description: exception
            ? I18n.t('matching.nadi.exception', { reason: exceptionReason })
            : (sameNadi
                ? I18n.t('matching.nadi.dosha', { nadi: bNadiName })
                : I18n.t('matching.nadi.safe'))
    };
}

// ============================================================================
// ADDITIONAL KOOTA CALCULATIONS (Professional Grade)
// ============================================================================

/**
 * Calculate Mahendra Koota
 * Rule: Distance from Girl's Nak to Boy's should be 4, 7, 10, 13, 16, 19, 22, 25
 */
function calculateMahendra(boyNak, girlNak) {
    const dist = ((boyNak - girlNak + 27) % 27) + 1;
    const compatible = [4, 7, 10, 13, 16, 19, 22, 25].includes(dist);
    return {
        name: 'Mahendra',
        compatible,
        description: compatible 
            ? I18n.t('matching.mahendra.compatible') 
            : I18n.t('matching.mahendra.not_compatible')
    };
}

/**
 * Calculate Stri-Deergha Koota
 * Rule: Boy's Nak should be more than 13 nakshatras away from Girl's
 */
function calculateStriDeergha(boyNak, girlNak) {
    const dist = ((boyNak - girlNak + 27) % 27) + 1;
    const compatible = dist > 13;
    return {
        name: 'Stri-Deergha',
        compatible,
        description: compatible 
            ? I18n.t('matching.stri_deergha.compatible') 
            : I18n.t('matching.stri_deergha.not_compatible')
    };
}

/**
 * Calculate Rajju Koota (The critical "Death" check)
 * Based on 5 groups: Padarajju, Katirajju, Nabhirajju, Kantharajju, Shirorajju
 * Same group = Extreme Dosha
 */
function calculateRajju(boyNak, girlNak) {
    // Rajju group mapping (0-indexed nakshatra)
    // 0: Pada, 1: Kati, 2: Nabhi, 3: Kantha, 4: Shiro
    const rajjuGroups = [
        0, 1, 2, 3, 4, 3, 2, 1, 0, // 0-8 (Ashwini to Ashlesha)
        0, 1, 2, 3, 4, 3, 2, 1, 0, // 9-17 (Magha to Jyeshtha)
        0, 1, 2, 3, 4, 3, 2, 1, 0  // 18-26 (Mula to Revati)
    ];
    
    const boyG = rajjuGroups[boyNak];
    const girlG = rajjuGroups[girlNak];
    const hasDosha = boyG === girlG;
    
    const groupNames = ['Pada', 'Kati', 'Nabhi', 'Kantha', 'Shiro'];
    
    return {
        name: 'Rajju',
        hasDosha,
        boyGroup: groupNames[boyG],
        girlGroup: groupNames[girlG],
        description: hasDosha 
            ? I18n.t('matching.rajju.dosha', { group: groupNames[boyG] }) 
            : I18n.t('matching.rajju.safe')
    };
}

function getRelationshipName(rel) {
    const key = rel === 'F' ? 'friend' : (rel === 'E' ? 'enemy' : 'neutral');
    return I18n.t(`matching.maitri.${key}`);
}

// ============================================================================
// MAIN KOOTA CLASS
// ============================================================================

class Koota {
    /**
     * Calculate complete Ashtakoota matching
     * 
     * @param {Object} boy - Boy's data { rasi: 0-11, nakshatra: 0-26, pada: 1-4 }
     * @param {Object} girl - Girl's data { rasi: 0-11, nakshatra: 0-26, pada: 1-4 }
     * @returns {Object} Complete matching results with all 8 kootas and exceptions
     */
    calculate(boy, girl) {
        // Validate inputs
        if (!this.validateInput(boy, 'Boy') || !this.validateInput(girl, 'Girl')) {
            throw new Error('Invalid input data for matching calculation');
        }

        const bRasi = boy.rasi;
        const gRasi = girl.rasi;
        const bNak = boy.nakshatra;
        const gNak = girl.nakshatra;
        const bPada = boy.pada || 1;
        const gPada = girl.pada || 1;

        // Calculate all 8 Kootas
        const varna = calculateVarna(bRasi, gRasi);
        const vashya = calculateVashya(bRasi, gRasi);
        const tara = calculateTara(bNak, gNak);
        const yoni = calculateYoni(bNak, gNak);
        const maitri = calculateMaitri(bRasi, gRasi);
        const gana = calculateGana(bNak, gNak);
        const bhakoot = calculateBhakoot(bRasi, gRasi);
        const nadi = calculateNadi(bNak, gNak, bRasi, gRasi, bPada, gPada);

        // Calculate Advanced Kootas (No points, but critical binary checks)
        const mahendra = calculateMahendra(bNak, gNak);
        const striDeergha = calculateStriDeergha(bNak, gNak);
        const rajju = calculateRajju(bNak, gNak);

        // Apply additional Nadi dosha mitigation if strong scores elsewhere
        let finalNadi = { ...nadi };
        if (nadi.hasDosha && !nadi.exception) {
            const strongTara = tara.score >= 2.5;
            const strongMaitri = maitri.score >= 4;
            const strongYoni = yoni.score >= 3;

            if (strongTara && strongMaitri && strongYoni) {
                finalNadi = {
                    ...nadi,
                    exception: true,
                    exceptionReason: 'Strong Tara, Maitri, and Yoni scores mitigate Nadi Dosha',
                    hasDosha: false,
                    score: 4 // Partial restoration
                };
            }
        }

        // Calculate total
        const finalTotal = varna.score + vashya.score + tara.score + yoni.score +
            maitri.score + gana.score + bhakoot.score + finalNadi.score;

        // Check for critical doshas
        const doshas = this.checkDoshas(bhakoot, finalNadi, maitri, rajju);

        // Generate recommendation
        const recommendation = this.getRecommendation(finalTotal, doshas, bhakoot, finalNadi);

        return {
            total: finalTotal,
            max: TOTAL_MAX_POINTS,
            percentage: Math.round((finalTotal / TOTAL_MAX_POINTS) * 100),
            details: {
                varna, vashya, tara, yoni, maitri, gana, bhakoot, 
                nadi: finalNadi,
                mahendra, striDeergha, rajju
            },
            doshas: doshas,
            recommendation: recommendation,
            boyDetails: {
                rasi: RASI_NAMES[bRasi],
                rasiIndex: bRasi,
                nakshatra: NAKSHATRA_NAMES[bNak],
                nakshatraIndex: bNak,
                pada: bPada
            },
            girlDetails: {
                rasi: RASI_NAMES[gRasi],
                rasiIndex: gRasi,
                nakshatra: NAKSHATRA_NAMES[gNak],
                nakshatraIndex: gNak,
                pada: gPada
            }
        };
    }

    validateInput(data, label) {
        if (!data || typeof data !== 'object') {
            console.error(`${label} data is missing or invalid`);
            return false;
        }
        if (data.rasi < 0 || data.rasi > 11) {
            console.error(`${label} rasi ${data.rasi} is out of range (0-11)`);
            return false;
        }
        if (data.nakshatra < 0 || data.nakshatra > 26) {
            console.error(`${label} nakshatra ${data.nakshatra} is out of range (0-26)`);
            return false;
        }
        return true;
    }

    /**
     * Identify major Doshas based on calculations
     */
    checkDoshas(bhakoot, nadi, maitri, rajju) {
        const doshas = [];
        if (bhakoot.hasDosha) doshas.push('Bhakoot Dosha');
        if (nadi.hasDosha) doshas.push('Nadi Dosha');
        if (maitri.score === 0) doshas.push('Graha Maitri Dosha');
        if (rajju.hasDosha) doshas.push('Rajju Dosha');
        return doshas;
    }

    /**
     * Generate final compatibility recommendation
     */
    getRecommendation(total, doshas, bhakoot, nadi) {
        if (total >= 28) return I18n.t('matching.recommendations.excellent');
        if (total >= 21 && !nadi.hasDosha) return I18n.t('matching.recommendations.good');
        if (total >= 18 && !nadi.hasDosha) return I18n.t('matching.recommendations.average');
        return I18n.t('matching.recommendations.low');
    }

    /**
     * Get rasi details
     */
    getRasiInfo(index) {
        const vashyaTypeNames = ['Chatushpad', 'Manav', 'Jalchar', 'Vanchar', 'Keet'];
        const varnaNames = ['Shudra', 'Vaishya', 'Kshatriya', 'Brahmin'];
        return {
            name: RASI_NAMES[index],
            lord: RASI_LORD[index],
            varna: varnaNames[VARNA_BY_RASI[index] - 1],
            vashya: vashyaTypeNames[RASI_VASHYA_TYPE[index]]
        };
    }
}

export default new Koota();