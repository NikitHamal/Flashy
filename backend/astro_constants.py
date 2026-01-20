"""
Vedic Astrology Constants Module

This module contains all the fundamental constants, tables, and mappings
required for accurate Vedic astrology calculations including:
- Rasi (signs), Nakshatras, Planets
- Dignities (exaltation, debilitation, own signs)
- Dasha systems (Vimshottari, Yogini, etc.)
- Ayanamsa systems
- Friendship tables
- House classifications
"""

from enum import Enum
from typing import Dict, List, Tuple
from dataclasses import dataclass


# =============================================================================
# ENUMERATIONS
# =============================================================================

class Planet(Enum):
    """Nine planets (Navagraha) of Vedic Astrology."""
    SUN = "Sun"
    MOON = "Moon"
    MARS = "Mars"
    MERCURY = "Mercury"
    JUPITER = "Jupiter"
    VENUS = "Venus"
    SATURN = "Saturn"
    RAHU = "Rahu"
    KETU = "Ketu"


class Rasi(Enum):
    """Twelve signs (Rashis) of the Zodiac."""
    MESHA = 0      # Aries
    VRISHABHA = 1  # Taurus
    MITHUNA = 2    # Gemini
    KARKA = 3      # Cancer
    SIMHA = 4      # Leo
    KANYA = 5      # Virgo
    TULA = 6       # Libra
    VRISHCHIKA = 7 # Scorpio
    DHANU = 8      # Sagittarius
    MAKARA = 9     # Capricorn
    KUMBHA = 10    # Aquarius
    MEENA = 11     # Pisces


class Nakshatra(Enum):
    """Twenty-seven nakshatras (lunar mansions)."""
    ASHWINI = 0
    BHARANI = 1
    KRITTIKA = 2
    ROHINI = 3
    MRIGASHIRA = 4
    ARDRA = 5
    PUNARVASU = 6
    PUSHYA = 7
    ASHLESHA = 8
    MAGHA = 9
    PURVA_PHALGUNI = 10
    UTTARA_PHALGUNI = 11
    HASTA = 12
    CHITRA = 13
    SWATI = 14
    VISHAKHA = 15
    ANURADHA = 16
    JYESHTHA = 17
    MULA = 18
    PURVA_ASHADHA = 19
    UTTARA_ASHADHA = 20
    SHRAVANA = 21
    DHANISHTA = 22
    SHATABHISHA = 23
    PURVA_BHADRAPADA = 24
    UTTARA_BHADRAPADA = 25
    REVATI = 26


class Gender(Enum):
    """Gender for chart calculations."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


# =============================================================================
# SIGN NAMES AND PROPERTIES
# =============================================================================

RASI_NAMES = [
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena"
]

RASI_NAMES_ENGLISH = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

RASI_ELEMENTS = {
    0: "Fire", 1: "Earth", 2: "Air", 3: "Water",
    4: "Fire", 5: "Earth", 6: "Air", 7: "Water",
    8: "Fire", 9: "Earth", 10: "Air", 11: "Water"
}

RASI_QUALITIES = {
    0: "Movable", 1: "Fixed", 2: "Dual", 3: "Movable",
    4: "Fixed", 5: "Dual", 6: "Movable", 7: "Fixed",
    8: "Dual", 9: "Movable", 10: "Fixed", 11: "Dual"
}


# =============================================================================
# NAKSHATRA DATA
# =============================================================================

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
    "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati"
]

NAKSHATRA_SPAN = 13.333333333333334  # degrees (360/27)
PADA_SPAN = 3.333333333333333       # degrees (13.33.../4)

# Nakshatra lords for Vimshottari Dasha
NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury", "Ketu", "Venus", "Sun",
    "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury"
]

# Nakshatra Deities
NAKSHATRA_DEITIES = [
    "Ashwini Kumara", "Yama", "Agni", "Brahma", "Soma", "Rudra",
    "Aditi", "Brihaspati", "Sarpa", "Pitris", "Bhaga", "Aryaman",
    "Savitar", "Tvashtar", "Vayu", "Indra-Agni", "Mitra", "Indra",
    "Nirrti", "Apah", "Vishve Devas", "Vishnu", "Vasu", "Varuna",
    "Ajaikapada", "Ahirbudhnya", "Pushan"
]

# Nakshatra Ganas
NAKSHATRA_GANAS = {
    "Deva": [0, 4, 6, 7, 12, 14, 20, 21, 26],      # Ashwini, Mrigashira, etc.
    "Manushya": [1, 3, 5, 10, 11, 13, 18, 19, 24], # Bharani, Rohini, etc.
    "Rakshasa": [2, 8, 9, 15, 16, 17, 22, 23, 25]  # Krittika, Ashlesha, etc.
}

# Nakshatra Yonis (animal symbols)
NAKSHATRA_YONIS = [
    ("Horse", "Male"), ("Elephant", "Male"), ("Sheep", "Female"),
    ("Serpent", "Male"), ("Serpent", "Female"), ("Dog", "Female"),
    ("Cat", "Female"), ("Sheep", "Male"), ("Cat", "Male"),
    ("Rat", "Male"), ("Rat", "Female"), ("Cow", "Male"),
    ("Buffalo", "Female"), ("Tiger", "Female"), ("Buffalo", "Male"),
    ("Tiger", "Male"), ("Deer", "Female"), ("Deer", "Male"),
    ("Dog", "Male"), ("Monkey", "Male"), ("Mongoose", "Male"),
    ("Monkey", "Female"), ("Lion", "Female"), ("Horse", "Female"),
    ("Lion", "Male"), ("Cow", "Female"), ("Elephant", "Female")
]


# =============================================================================
# PLANET DATA
# =============================================================================

PLANET_NAMES = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
SAPTA_GRAHA = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
NAVAGRAHA = PLANET_NAMES

# Sign lords (ruler of each sign)
SIGN_LORDS = {
    0: "Mars",     # Aries
    1: "Venus",    # Taurus
    2: "Mercury",  # Gemini
    3: "Moon",     # Cancer
    4: "Sun",      # Leo
    5: "Mercury",  # Virgo
    6: "Venus",    # Libra
    7: "Mars",     # Scorpio (traditional, some use Ketu)
    8: "Jupiter",  # Sagittarius
    9: "Saturn",   # Capricorn
    10: "Saturn",  # Aquarius (traditional, some use Rahu)
    11: "Jupiter"  # Pisces
}

# Own signs for each planet
OWN_SIGNS = {
    "Sun": [4],           # Leo
    "Moon": [3],          # Cancer
    "Mars": [0, 7],       # Aries, Scorpio
    "Mercury": [2, 5],    # Gemini, Virgo
    "Jupiter": [8, 11],   # Sagittarius, Pisces
    "Venus": [1, 6],      # Taurus, Libra
    "Saturn": [9, 10],    # Capricorn, Aquarius
    "Rahu": [10],         # Aquarius (modern)
    "Ketu": [7]           # Scorpio (modern)
}

# Exaltation points (sign index and exact degree)
EXALTATION = {
    "Sun": {"sign": 0, "degree": 10},      # Aries 10°
    "Moon": {"sign": 1, "degree": 3},      # Taurus 3°
    "Mars": {"sign": 9, "degree": 28},     # Capricorn 28°
    "Mercury": {"sign": 5, "degree": 15},  # Virgo 15°
    "Jupiter": {"sign": 3, "degree": 5},   # Cancer 5°
    "Venus": {"sign": 11, "degree": 27},   # Pisces 27°
    "Saturn": {"sign": 6, "degree": 20},   # Libra 20°
    "Rahu": {"sign": 1, "degree": 20},     # Taurus 20° (or Gemini per some)
    "Ketu": {"sign": 7, "degree": 20}      # Scorpio 20° (or Sagittarius per some)
}

# Debilitation signs (opposite of exaltation)
DEBILITATION = {
    "Sun": 6,      # Libra
    "Moon": 7,     # Scorpio
    "Mars": 3,     # Cancer
    "Mercury": 11, # Pisces
    "Jupiter": 9,  # Capricorn
    "Venus": 5,    # Virgo
    "Saturn": 0,   # Aries
    "Rahu": 7,     # Scorpio
    "Ketu": 1      # Taurus
}

# Moolatrikona ranges (sign, start degree, end degree)
MOOLATRIKONA = {
    "Sun": {"sign": 4, "start": 0, "end": 20},     # Leo 0-20°
    "Moon": {"sign": 1, "start": 4, "end": 30},    # Taurus 4-30°
    "Mars": {"sign": 0, "start": 0, "end": 12},    # Aries 0-12°
    "Mercury": {"sign": 5, "start": 16, "end": 20},# Virgo 16-20°
    "Jupiter": {"sign": 8, "start": 0, "end": 10}, # Sagittarius 0-10°
    "Venus": {"sign": 6, "start": 0, "end": 15},   # Libra 0-15°
    "Saturn": {"sign": 10, "start": 0, "end": 20}  # Aquarius 0-20°
}


# =============================================================================
# PLANETARY FRIENDSHIPS
# =============================================================================

# Natural friendships (Naisargika Maitri)
NATURAL_FRIENDS = {
    "Sun": ["Moon", "Mars", "Jupiter"],
    "Moon": ["Sun", "Mercury"],
    "Mars": ["Sun", "Moon", "Jupiter"],
    "Mercury": ["Sun", "Venus"],
    "Jupiter": ["Sun", "Moon", "Mars"],
    "Venus": ["Mercury", "Saturn"],
    "Saturn": ["Mercury", "Venus"],
    "Rahu": ["Mercury", "Venus", "Saturn"],
    "Ketu": ["Mars", "Venus", "Saturn"]
}

NATURAL_ENEMIES = {
    "Sun": ["Venus", "Saturn"],
    "Moon": [],
    "Mars": ["Mercury"],
    "Mercury": ["Moon"],
    "Jupiter": ["Mercury", "Venus"],
    "Venus": ["Sun", "Moon"],
    "Saturn": ["Sun", "Moon", "Mars"],
    "Rahu": ["Sun", "Moon", "Mars"],
    "Ketu": ["Sun", "Moon"]
}

# Planets not in friends or enemies are neutral
NATURAL_NEUTRALS = {
    "Sun": ["Mercury"],
    "Moon": ["Mars", "Jupiter", "Venus", "Saturn"],
    "Mars": ["Venus", "Saturn"],
    "Mercury": ["Mars", "Jupiter", "Saturn"],
    "Jupiter": ["Saturn"],
    "Venus": ["Mars", "Jupiter"],
    "Saturn": ["Jupiter"],
    "Rahu": ["Jupiter"],
    "Ketu": ["Mercury", "Jupiter"]
}


# =============================================================================
# DASHA SYSTEMS
# =============================================================================

# Vimshottari Dasha (120 years total)
VIMSHOTTARI_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
VIMSHOTTARI_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
}
VIMSHOTTARI_TOTAL = 120

# Yogini Dasha (36 years total)
YOGINI_ORDER = ["Mangala", "Pingala", "Dhanya", "Bhramari", "Bhadrika", "Ulka", "Siddha", "Sankata"]
YOGINI_YEARS = {
    "Mangala": 1, "Pingala": 2, "Dhanya": 3, "Bhramari": 4,
    "Bhadrika": 5, "Ulka": 6, "Siddha": 7, "Sankata": 8
}
YOGINI_PLANETS = {
    "Mangala": "Moon", "Pingala": "Sun", "Dhanya": "Jupiter",
    "Bhramari": "Mars", "Bhadrika": "Mercury", "Ulka": "Saturn",
    "Siddha": "Venus", "Sankata": "Rahu"
}
YOGINI_TOTAL = 36

# Ashtottari Dasha (108 years total)
ASHTOTTARI_ORDER = ["Sun", "Moon", "Mars", "Mercury", "Saturn", "Jupiter", "Rahu", "Venus"]
ASHTOTTARI_YEARS = {
    "Sun": 6, "Moon": 15, "Mars": 8, "Mercury": 17,
    "Saturn": 10, "Jupiter": 19, "Rahu": 12, "Venus": 21
}
ASHTOTTARI_TOTAL = 108


# =============================================================================
# AYANAMSA SYSTEMS
# =============================================================================

@dataclass
class AyanamsaSystem:
    """Ayanamsa calculation parameters."""
    name: str
    j2000_value: float
    annual_precession: float
    # Polynomial coefficients: a0, a1, a2 for A = a0 + a1*T + a2*T²
    coefficients: Tuple[float, float, float]


AYANAMSA_SYSTEMS = {
    "Lahiri": AyanamsaSystem(
        name="Lahiri",
        j2000_value=23.853056,
        annual_precession=50.2388475,
        coefficients=(23.853056, 1.396971, 0.000308)
    ),
    "Raman": AyanamsaSystem(
        name="Raman",
        j2000_value=22.460000,
        annual_precession=50.27,
        coefficients=(22.460000, 1.3949, 0.000308)
    ),
    "Krishnamurti": AyanamsaSystem(
        name="Krishnamurti",
        j2000_value=23.780000,
        annual_precession=50.2388475,
        coefficients=(23.780000, 1.396971, 0.000308)
    ),
    "TrueChitra": AyanamsaSystem(
        name="True Chitrapaksha",
        j2000_value=23.9762,
        annual_precession=50.2388475,
        coefficients=(23.9762, 1.396971, 0.000308)
    ),
    "Yukteshwar": AyanamsaSystem(
        name="Yukteshwar",
        j2000_value=22.475000,
        annual_precession=54.0,
        coefficients=(22.475000, 1.5, 0.0)
    ),
    "FaganBradley": AyanamsaSystem(
        name="Fagan-Bradley",
        j2000_value=24.044000,
        annual_precession=50.2388475,
        coefficients=(24.044000, 1.396971, 0.000308)
    )
}


# =============================================================================
# HOUSE CLASSIFICATIONS
# =============================================================================

KENDRAS = [1, 4, 7, 10]           # Angular houses (strongest)
TRIKONAS = [1, 5, 9]             # Trinal houses (fortune)
DUSTHANAS = [6, 8, 12]           # Malefic houses
UPACHAYA = [3, 6, 10, 11]        # Growth houses
MARAKA = [2, 7]                  # Death-inflicting houses
TRISHADAYA = [3, 6, 11]          # Houses of struggle

HOUSE_NAMES = [
    "Lagna/Tanu", "Dhana", "Sahaja", "Sukha", "Putra", "Ripu/Roga",
    "Yuvati/Kalatra", "Randhra/Mrityu", "Dharma/Bhagya", "Karma",
    "Labha", "Vyaya/Moksha"
]

HOUSE_SIGNIFICATIONS = {
    1: ["Self", "Body", "Appearance", "Personality", "Health", "Beginnings"],
    2: ["Wealth", "Family", "Speech", "Food", "Values", "Face", "Right Eye"],
    3: ["Siblings", "Courage", "Communication", "Short Journeys", "Arms", "Ears"],
    4: ["Mother", "Home", "Property", "Vehicles", "Education", "Happiness", "Chest"],
    5: ["Children", "Intelligence", "Creativity", "Romance", "Speculation", "Stomach"],
    6: ["Enemies", "Disease", "Debts", "Service", "Daily Work", "Maternal Uncle"],
    7: ["Spouse", "Partnership", "Business", "Public", "Lower Abdomen", "Legal Matters"],
    8: ["Longevity", "Hidden", "Inheritance", "Occult", "Transformation", "Genitals"],
    9: ["Father", "Guru", "Religion", "Fortune", "Higher Learning", "Long Journeys"],
    10: ["Career", "Fame", "Authority", "Government", "Knees", "Actions"],
    11: ["Gains", "Income", "Friends", "Desires", "Elder Siblings", "Ankles"],
    12: ["Losses", "Expenses", "Foreign", "Moksha", "Bed Pleasures", "Feet", "Sleep"]
}


# =============================================================================
# ASPECTS (DRISHTIS)
# =============================================================================

# Planetary aspects (special aspects)
PLANETARY_ASPECTS = {
    "Sun": [7],
    "Moon": [7],
    "Mars": [4, 7, 8],      # 4th, 7th, 8th aspects
    "Mercury": [7],
    "Jupiter": [5, 7, 9],   # 5th, 7th, 9th aspects
    "Venus": [7],
    "Saturn": [3, 7, 10],   # 3rd, 7th, 10th aspects
    "Rahu": [5, 7, 9],      # Same as Jupiter
    "Ketu": [5, 7, 9]       # Same as Jupiter
}


# =============================================================================
# BENEFIC/MALEFIC CLASSIFICATION
# =============================================================================

NATURAL_BENEFICS = ["Jupiter", "Venus", "Moon", "Mercury"]  # Mercury conditional
NATURAL_MALEFICS = ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]

# Strong Moon (Shukla Paksha) is benefic, weak Moon is malefic
# Mercury with malefics becomes malefic


# =============================================================================
# YOGA DEFINITIONS (Basic)
# =============================================================================

# Pancha Mahapurusha Yogas (5 Great Personality Yogas)
MAHAPURUSHA_YOGAS = {
    "Hamsa": {"planet": "Jupiter", "condition": "Jupiter in Kendra in own/exaltation sign"},
    "Malavya": {"planet": "Venus", "condition": "Venus in Kendra in own/exaltation sign"},
    "Ruchaka": {"planet": "Mars", "condition": "Mars in Kendra in own/exaltation sign"},
    "Bhadra": {"planet": "Mercury", "condition": "Mercury in Kendra in own/exaltation sign"},
    "Shasha": {"planet": "Saturn", "condition": "Saturn in Kendra in own/exaltation sign"}
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_rasi_index(longitude: float) -> int:
    """Get rasi (sign) index from longitude (0-359.99...)."""
    return int(longitude // 30) % 12


def get_nakshatra_index(longitude: float) -> int:
    """Get nakshatra index from longitude (0-26)."""
    return int(longitude // NAKSHATRA_SPAN) % 27


def get_nakshatra_pada(longitude: float) -> int:
    """Get nakshatra pada (1-4) from longitude."""
    nak_pos = longitude % NAKSHATRA_SPAN
    return int(nak_pos // PADA_SPAN) + 1


def get_degree_in_sign(longitude: float) -> float:
    """Get degree within sign (0-29.99...)."""
    return longitude % 30


def get_sign_lord(sign_index: int) -> str:
    """Get the ruling planet of a sign."""
    return SIGN_LORDS[sign_index]


def get_dignity(planet: str, sign_index: int, degree_in_sign: float) -> str:
    """
    Determine the dignity of a planet in a sign.
    Returns: 'exalted', 'debilitated', 'moolatrikona', 'own', or 'neutral'
    """
    # Check exaltation
    if planet in EXALTATION:
        exalt = EXALTATION[planet]
        if sign_index == exalt["sign"]:
            return "exalted"
    
    # Check debilitation
    if planet in DEBILITATION:
        if sign_index == DEBILITATION[planet]:
            return "debilitated"
    
    # Check moolatrikona
    if planet in MOOLATRIKONA:
        mt = MOOLATRIKONA[planet]
        if sign_index == mt["sign"] and mt["start"] <= degree_in_sign <= mt["end"]:
            return "moolatrikona"
    
    # Check own sign
    if planet in OWN_SIGNS:
        if sign_index in OWN_SIGNS[planet]:
            return "own"
    
    return "neutral"


def normalize_longitude(lon: float) -> float:
    """Normalize longitude to 0-360 range."""
    lon = lon % 360
    if lon < 0:
        lon += 360
    return lon
