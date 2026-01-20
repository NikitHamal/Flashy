export const RASI_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
];

export const NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
];

export const NAKSHATRA_SPAN = 13 + 20 / 60;

export const PLANET_ORDER = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"
];

export const PLANET_SYMBOLS = {
    Sun: "Su",
    Moon: "Mo",
    Mars: "Ma",
    Mercury: "Me",
    Jupiter: "Ju",
    Venus: "Ve",
    Saturn: "Sa",
    Rahu: "Ra",
    Ketu: "Ke",
    Lagna: "Asc"
};

export const PLANET_DIGNITIES = {
    Sun: { exalted: 0, debilitated: 6, own: [4] },
    Moon: { exalted: 1, debilitated: 7, own: [3] },
    Mars: { exalted: 9, debilitated: 3, own: [0, 7] },
    Mercury: { exalted: 5, debilitated: 11, own: [2, 5] },
    Jupiter: { exalted: 3, debilitated: 9, own: [8, 11] },
    Venus: { exalted: 11, debilitated: 5, own: [1, 6] },
    Saturn: { exalted: 6, debilitated: 0, own: [9, 10] },
    Rahu: { exalted: 1, debilitated: 7, own: [10] },
    Ketu: { exalted: 7, debilitated: 1, own: [8] }
};

export const AYANAMSA_SYSTEMS = {
    Lahiri: { j2000Value: 23.853056, coefficients: [23.853056, 1.396971, 0.000308] }
};
