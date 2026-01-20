"""
Vedic Astrology Reference Data

Provides structured reference information for signs, houses, planets,
and nakshatras for the Flashy Astro agent.
"""

SIGNS = {
    "aries": {
        "sanskrit": "Mesha",
        "element": "Fire",
        "quality": "Movable",
        "ruler": "Mars",
        "exaltation": "Sun",
        "debilitation": "Saturn",
        "keywords": ["initiative", "courage", "action", "leadership"]
    },
    "taurus": {
        "sanskrit": "Vrishabha",
        "element": "Earth",
        "quality": "Fixed",
        "ruler": "Venus",
        "exaltation": "Moon",
        "debilitation": "None",
        "keywords": ["stability", "comfort", "values", "sensuality"]
    },
    "gemini": {
        "sanskrit": "Mithuna",
        "element": "Air",
        "quality": "Dual",
        "ruler": "Mercury",
        "exaltation": "None",
        "debilitation": "None",
        "keywords": ["communication", "curiosity", "learning", "adaptability"]
    },
    "cancer": {
        "sanskrit": "Karka",
        "element": "Water",
        "quality": "Movable",
        "ruler": "Moon",
        "exaltation": "Jupiter",
        "debilitation": "Mars",
        "keywords": ["nurturing", "emotions", "home", "protection"]
    },
    "leo": {
        "sanskrit": "Simha",
        "element": "Fire",
        "quality": "Fixed",
        "ruler": "Sun",
        "exaltation": "None",
        "debilitation": "None",
        "keywords": ["creativity", "authority", "vitality", "pride"]
    },
    "virgo": {
        "sanskrit": "Kanya",
        "element": "Earth",
        "quality": "Dual",
        "ruler": "Mercury",
        "exaltation": "Mercury",
        "debilitation": "Venus",
        "keywords": ["analysis", "service", "precision", "health"]
    },
    "libra": {
        "sanskrit": "Tula",
        "element": "Air",
        "quality": "Movable",
        "ruler": "Venus",
        "exaltation": "Saturn",
        "debilitation": "Sun",
        "keywords": ["balance", "relationships", "justice", "aesthetics"]
    },
    "scorpio": {
        "sanskrit": "Vrischika",
        "element": "Water",
        "quality": "Fixed",
        "ruler": "Mars",
        "exaltation": "None",
        "debilitation": "Moon",
        "keywords": ["transformation", "depth", "intensity", "secrets"]
    },
    "sagittarius": {
        "sanskrit": "Dhanu",
        "element": "Fire",
        "quality": "Dual",
        "ruler": "Jupiter",
        "exaltation": "None",
        "debilitation": "None",
        "keywords": ["wisdom", "faith", "expansion", "journeys"]
    },
    "capricorn": {
        "sanskrit": "Makara",
        "element": "Earth",
        "quality": "Movable",
        "ruler": "Saturn",
        "exaltation": "Mars",
        "debilitation": "Jupiter",
        "keywords": ["discipline", "structure", "ambition", "responsibility"]
    },
    "aquarius": {
        "sanskrit": "Kumbha",
        "element": "Air",
        "quality": "Fixed",
        "ruler": "Saturn",
        "exaltation": "None",
        "debilitation": "None",
        "keywords": ["innovation", "community", "vision", "detachment"]
    },
    "pisces": {
        "sanskrit": "Meena",
        "element": "Water",
        "quality": "Dual",
        "ruler": "Jupiter",
        "exaltation": "Venus",
        "debilitation": "Mercury",
        "keywords": ["compassion", "spirituality", "imagination", "surrender"]
    }
}

PLANETS = {
    "sun": {"sanskrit": "Surya", "nature": "Malefic", "significations": ["soul", "authority", "vitality"]},
    "moon": {"sanskrit": "Chandra", "nature": "Benefic", "significations": ["mind", "emotions", "mother"]},
    "mars": {"sanskrit": "Mangala", "nature": "Malefic", "significations": ["courage", "drive", "siblings"]},
    "mercury": {"sanskrit": "Budha", "nature": "Neutral", "significations": ["intellect", "speech", "commerce"]},
    "jupiter": {"sanskrit": "Guru", "nature": "Benefic", "significations": ["wisdom", "growth", "children"]},
    "venus": {"sanskrit": "Shukra", "nature": "Benefic", "significations": ["love", "art", "luxury"]},
    "saturn": {"sanskrit": "Shani", "nature": "Malefic", "significations": ["discipline", "karma", "longevity"]},
    "rahu": {"sanskrit": "Rahu", "nature": "Shadow", "significations": ["desires", "obsession", "foreign" ]},
    "ketu": {"sanskrit": "Ketu", "nature": "Shadow", "significations": ["detachment", "moksha", "mysticism"]}
}

HOUSES = {
    "1": {"name": "Lagna", "significations": ["self", "body", "identity"]},
    "2": {"name": "Dhana", "significations": ["wealth", "speech", "family"]},
    "3": {"name": "Sahaja", "significations": ["siblings", "effort", "courage"]},
    "4": {"name": "Sukha", "significations": ["home", "mother", "comforts"]},
    "5": {"name": "Putra", "significations": ["children", "creativity", "intelligence"]},
    "6": {"name": "Ripu", "significations": ["health", "service", "enemies"]},
    "7": {"name": "Yuvati", "significations": ["partnerships", "marriage", "public"]},
    "8": {"name": "Randhra", "significations": ["transformation", "longevity", "occult"]},
    "9": {"name": "Dharma", "significations": ["fortune", "guru", "faith"]},
    "10": {"name": "Karma", "significations": ["career", "status", "authority"]},
    "11": {"name": "Labha", "significations": ["gains", "network", "desires"]},
    "12": {"name": "Vyaya", "significations": ["loss", "isolation", "moksha"]}
}

NAKSHATRAS = [
    {"name": "Ashwini", "ruler": "Ketu", "deity": "Ashwini Kumaras", "range": "0°-13°20' Aries"},
    {"name": "Bharani", "ruler": "Venus", "deity": "Yama", "range": "13°20'-26°40' Aries"},
    {"name": "Krittika", "ruler": "Sun", "deity": "Agni", "range": "26°40' Aries-10° Taurus"},
    {"name": "Rohini", "ruler": "Moon", "deity": "Brahma", "range": "10°-23°20' Taurus"},
    {"name": "Mrigashirsha", "ruler": "Mars", "deity": "Soma", "range": "23°20' Taurus-6°40' Gemini"},
    {"name": "Ardra", "ruler": "Rahu", "deity": "Rudra", "range": "6°40'-20° Gemini"},
    {"name": "Punarvasu", "ruler": "Jupiter", "deity": "Aditi", "range": "20° Gemini-3°20' Cancer"},
    {"name": "Pushya", "ruler": "Saturn", "deity": "Brihaspati", "range": "3°20'-16°40' Cancer"},
    {"name": "Ashlesha", "ruler": "Mercury", "deity": "Nagas", "range": "16°40'-30° Cancer"},
    {"name": "Magha", "ruler": "Ketu", "deity": "Pitrs", "range": "0°-13°20' Leo"},
    {"name": "Purva Phalguni", "ruler": "Venus", "deity": "Bhaga", "range": "13°20'-26°40' Leo"},
    {"name": "Uttara Phalguni", "ruler": "Sun", "deity": "Aryaman", "range": "26°40' Leo-10° Virgo"},
    {"name": "Hasta", "ruler": "Moon", "deity": "Savitar", "range": "10°-23°20' Virgo"},
    {"name": "Chitra", "ruler": "Mars", "deity": "Vishvakarma", "range": "23°20' Virgo-6°40' Libra"},
    {"name": "Swati", "ruler": "Rahu", "deity": "Vayu", "range": "6°40'-20° Libra"},
    {"name": "Vishakha", "ruler": "Jupiter", "deity": "Indra-Agni", "range": "20° Libra-3°20' Scorpio"},
    {"name": "Anuradha", "ruler": "Saturn", "deity": "Mitra", "range": "3°20'-16°40' Scorpio"},
    {"name": "Jyeshtha", "ruler": "Mercury", "deity": "Indra", "range": "16°40'-30° Scorpio"},
    {"name": "Mula", "ruler": "Ketu", "deity": "Nirriti", "range": "0°-13°20' Sagittarius"},
    {"name": "Purva Ashadha", "ruler": "Venus", "deity": "Apah", "range": "13°20'-26°40' Sagittarius"},
    {"name": "Uttara Ashadha", "ruler": "Sun", "deity": "Vishvadevas", "range": "26°40' Sagittarius-10° Capricorn"},
    {"name": "Shravana", "ruler": "Moon", "deity": "Vishnu", "range": "10°-23°20' Capricorn"},
    {"name": "Dhanishta", "ruler": "Mars", "deity": "Vasus", "range": "23°20' Capricorn-6°40' Aquarius"},
    {"name": "Shatabhisha", "ruler": "Rahu", "deity": "Varuna", "range": "6°40'-20° Aquarius"},
    {"name": "Purva Bhadrapada", "ruler": "Jupiter", "deity": "Aja Ekapada", "range": "20° Aquarius-3°20' Pisces"},
    {"name": "Uttara Bhadrapada", "ruler": "Saturn", "deity": "Ahir Budhnya", "range": "3°20'-16°40' Pisces"},
    {"name": "Revati", "ruler": "Mercury", "deity": "Pushan", "range": "16°40'-30° Pisces"}
]


def get_reference(topic: str):
    if not topic:
        return {"signs": SIGNS, "planets": PLANETS, "houses": HOUSES, "nakshatras": NAKSHATRAS}

    key = topic.strip().lower()
    if key in ("signs", "rashis", "zodiac"):
        return SIGNS
    if key in ("planets", "grahas"):
        return PLANETS
    if key in ("houses", "bhavas"):
        return HOUSES
    if key in ("nakshatras", "stars"):
        return NAKSHATRAS

    if key in SIGNS:
        return {key: SIGNS[key]}
    if key in PLANETS:
        return {key: PLANETS[key]}

    for nakshatra in NAKSHATRAS:
        if nakshatra["name"].lower() == key:
            return nakshatra

    return {"message": "No reference found for topic", "topic": topic}
