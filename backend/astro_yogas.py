"""
Vedic Yoga Analysis Module

This module contains comprehensive yoga detection algorithms based on
classical Vedic astrology texts including Brihat Parashara Hora Shastra,
Phaladeepika, and Saravali.

Categories of Yogas:
- Pancha Mahapurusha Yogas (5 Great Person Yogas)
- Raja Yogas (Kingly Combinations)
- Dhana Yogas (Wealth Combinations)
- Arishta Yogas (Affliction Combinations)
- Chandra Yogas (Moon-based)
- Surya Yogas (Sun-based)
- Nabhasa Yogas (Celestial Pattern Yogas)
- Special Yogas (Kaal Sarpa, Manglik, etc.)
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .astro_constants import (
    RASI_NAMES, PLANET_NAMES, SIGN_LORDS, OWN_SIGNS,
    EXALTATION, DEBILITATION, MOOLATRIKONA,
    KENDRAS, TRIKONAS, DUSTHANAS,
    NATURAL_BENEFICS, NATURAL_MALEFICS,
    PLANETARY_ASPECTS, NATURAL_FRIENDS
)
from .astro_engine import BirthChart, PlanetPosition


@dataclass
class Yoga:
    """Represents a detected yoga in a chart."""
    name: str
    category: str
    nature: str  # 'benefic', 'malefic', 'neutral'
    planets: List[str]
    houses: List[int]
    description: str
    strength: int  # 0-100
    effects: str
    remedies: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "nature": self.nature,
            "planets": self.planets,
            "houses": self.houses,
            "description": self.description,
            "strength": self.strength,
            "effects": self.effects,
            "remedies": self.remedies
        }


class YogaAnalyzer:
    """
    Comprehensive yoga analysis engine.
    
    Analyzes a birth chart for the presence of various yogas
    and calculates their strength and effects.
    """
    
    def __init__(self):
        pass
    
    def analyze(self, chart: BirthChart) -> List[Yoga]:
        """
        Perform complete yoga analysis on a chart.
        Returns list of all detected yogas sorted by strength.
        """
        yogas = []
        
        # Build helper context
        ctx = self._build_context(chart)
        
        # Check all yoga categories
        yogas.extend(self._check_mahapurusha_yogas(chart, ctx))
        yogas.extend(self._check_raja_yogas(chart, ctx))
        yogas.extend(self._check_dhana_yogas(chart, ctx))
        yogas.extend(self._check_chandra_yogas(chart, ctx))
        yogas.extend(self._check_surya_yogas(chart, ctx))
        yogas.extend(self._check_nabhasa_yogas(chart, ctx))
        yogas.extend(self._check_special_yogas(chart, ctx))
        yogas.extend(self._check_arishta_yogas(chart, ctx))
        
        # Sort by strength (descending)
        yogas.sort(key=lambda y: y.strength, reverse=True)
        
        return yogas
    
    def _build_context(self, chart: BirthChart) -> Dict[str, Any]:
        """Build helper context for yoga analysis."""
        lagna_sign = chart.lagna.rasi_index
        
        # Map planets to houses
        planets_in_house = {i: [] for i in range(1, 13)}
        planet_houses = {}
        
        for name, planet in chart.planets.items():
            house = ((planet.rasi_index - lagna_sign) % 12) + 1
            planets_in_house[house].append(name)
            planet_houses[name] = house
        
        # Lagna lord
        lagna_lord = SIGN_LORDS[lagna_sign]
        
        # Moon sign lord
        moon_sign = chart.planets["Moon"].rasi_index
        moon_sign_lord = SIGN_LORDS[moon_sign]
        
        return {
            "lagna_sign": lagna_sign,
            "lagna_lord": lagna_lord,
            "moon_sign": moon_sign,
            "moon_sign_lord": moon_sign_lord,
            "planets_in_house": planets_in_house,
            "planet_houses": planet_houses,
            "chart": chart
        }
    
    def _get_house_lord(self, house: int, lagna_sign: int) -> str:
        """Get the lord of a house based on lagna."""
        sign = (lagna_sign + house - 1) % 12
        return SIGN_LORDS[sign]
    
    def _is_in_kendra(self, house: int) -> bool:
        """Check if house is a kendra (1, 4, 7, 10)."""
        return house in KENDRAS
    
    def _is_in_trikona(self, house: int) -> bool:
        """Check if house is a trikona (1, 5, 9)."""
        return house in TRIKONAS
    
    def _is_in_dusthana(self, house: int) -> bool:
        """Check if house is a dusthana (6, 8, 12)."""
        return house in DUSTHANAS
    
    def _is_exalted(self, planet: PlanetPosition) -> bool:
        """Check if planet is exalted."""
        return planet.dignity == "exalted"
    
    def _is_debilitated(self, planet: PlanetPosition) -> bool:
        """Check if planet is debilitated."""
        return planet.dignity == "debilitated"
    
    def _is_in_own_sign(self, planet: PlanetPosition) -> bool:
        """Check if planet is in own sign."""
        return planet.dignity in ["own", "moolatrikona"]
    
    def _are_conjunct(self, p1: PlanetPosition, p2: PlanetPosition) -> bool:
        """Check if two planets are in the same sign."""
        return p1.rasi_index == p2.rasi_index
    
    def _aspects(self, from_planet: str, to_house: int, ctx: Dict) -> bool:
        """Check if a planet aspects a house."""
        from_house = ctx["planet_houses"].get(from_planet)
        if from_house is None:
            return False
        
        aspects = PLANETARY_ASPECTS.get(from_planet, [7])
        for asp in aspects:
            aspected_house = ((from_house + asp - 1) % 12) + 1
            if aspected_house == to_house:
                return True
        return False
    
    # =========================================================================
    # PANCHA MAHAPURUSHA YOGAS
    # =========================================================================
    
    def _check_mahapurusha_yogas(self, chart: BirthChart, ctx: Dict) -> List[Yoga]:
        """
        Check for Pancha Mahapurusha Yogas.
        These form when Mars, Mercury, Jupiter, Venus, or Saturn
        are in a Kendra in their own or exaltation sign.
        """
        yogas = []
        
        mahapurusha_planets = {
            "Mars": ("Ruchaka", "Great warrior, commander, leader of armies"),
            "Mercury": ("Bhadra", "Eloquent speaker, learned scholar, diplomatic"),
            "Jupiter": ("Hamsa", "Righteous, spiritual, respected teacher"),
            "Venus": ("Malavya", "Artistic, luxurious lifestyle, romantic"),
            "Saturn": ("Shasha", "Powerful authority, disciplined, ruler")
        }
        
        for planet_name, (yoga_name, effects) in mahapurusha_planets.items():
            planet = chart.planets[planet_name]
            house = ctx["planet_houses"][planet_name]
            
            # Must be in Kendra
            if not self._is_in_kendra(house):
                continue
            
            # Must be in own or exaltation sign
            if not (self._is_exalted(planet) or self._is_in_own_sign(planet)):
                continue
            
            # Calculate strength
            strength = 80
            if self._is_exalted(planet):
                strength = 100
            if planet.is_retrograde:
                strength = max(strength - 10, 50)
            
            yogas.append(Yoga(
                name=f"{yoga_name} Yoga",
                category="Mahapurusha",
                nature="benefic",
                planets=[planet_name],
                houses=[house],
                description=f"{planet_name} in Kendra in {planet.dignity} sign",
                strength=strength,
                effects=effects
            ))
        
        return yogas
    
    # =========================================================================
    # RAJA YOGAS
    # =========================================================================
    
    def _check_raja_yogas(self, chart: BirthChart, ctx: Dict) -> List[Yoga]:
        """
        Check for Raja Yogas - combinations for power, authority, and success.
        """
        yogas = []
        
        lagna_sign = ctx["lagna_sign"]
        
        # 1. Kendra-Trikona Raja Yoga
        # Lords of Kendras and Trikonas in conjunction or mutual aspect
        kendra_lords = [self._get_house_lord(h, lagna_sign) for h in KENDRAS]
        trikona_lords = [self._get_house_lord(h, lagna_sign) for h in TRIKONAS]
        
        for kl in kendra_lords:
            for tl in trikona_lords:
                if kl == tl:
                    continue
                
                kl_pos = chart.planets.get(kl)
                tl_pos = chart.planets.get(tl)
                
                if kl_pos and tl_pos and self._are_conjunct(kl_pos, tl_pos):
                    kl_house = ctx["planet_houses"].get(kl, 0)
                    strength = 75
                    
                    # Stronger if in Kendra or Trikona
                    if self._is_in_kendra(kl_house) or self._is_in_trikona(kl_house):
                        strength = 90
                    
                    yogas.append(Yoga(
                        name="Raja Yoga (Kendra-Trikona)",
                        category="Raja",
                        nature="benefic",
                        planets=[kl, tl],
                        houses=[kl_house],
                        description=f"{kl} (Kendra lord) conjunct {tl} (Trikona lord)",
                        strength=strength,
                        effects="Rise in power, authority, recognition, leadership"
                    ))
        
        # 2. Dharma-Karma Adhipati Yoga (9th and 10th lords together)
        lord_9 = self._get_house_lord(9, lagna_sign)
        lord_10 = self._get_house_lord(10, lagna_sign)
        
        if lord_9 != lord_10:
            l9_pos = chart.planets.get(lord_9)
            l10_pos = chart.planets.get(lord_10)
            
            if l9_pos and l10_pos and self._are_conjunct(l9_pos, l10_pos):
                yogas.append(Yoga(
                    name="Dharma-Karma Adhipati Yoga",
                    category="Raja",
                    nature="benefic",
                    planets=[lord_9, lord_10],
                    houses=[ctx["planet_houses"].get(lord_9, 0)],
                    description=f"9th lord ({lord_9}) and 10th lord ({lord_10}) conjunct",
                    strength=95,
                    effects="Supreme success in career, righteous actions bring great fortune"
                ))
        
        # 3. Lakshmi Yoga
        # Venus in own/exalted in Kendra and 9th lord strong
        venus = chart.planets["Venus"]
        venus_house = ctx["planet_houses"]["Venus"]
        
        if self._is_in_kendra(venus_house) and self._is_in_own_sign(venus) or self._is_exalted(venus):
            lord_9_pos = chart.planets.get(lord_9)
            if lord_9_pos and (self._is_in_own_sign(lord_9_pos) or self._is_exalted(lord_9_pos)):
                yogas.append(Yoga(
                    name="Lakshmi Yoga",
                    category="Raja",
                    nature="benefic",
                    planets=["Venus", lord_9],
                    houses=[venus_house],
                    description="Venus in Kendra in own/exalted, 9th lord strong",
                    strength=90,
                    effects="Wealth, prosperity, all comforts of life, respected in society"
                ))
        
        # 4. Viparita Raja Yoga (lords of 6, 8, 12 in 6, 8, 12)
        dusthana_lords = [self._get_house_lord(h, lagna_sign) for h in DUSTHANAS]
        viparita_count = 0
        viparita_planets = []
        
        for dl in dusthana_lords:
            dl_house = ctx["planet_houses"].get(dl, 0)
            if self._is_in_dusthana(dl_house):
                viparita_count += 1
                viparita_planets.append(dl)
        
        if viparita_count >= 2:
            yogas.append(Yoga(
                name="Viparita Raja Yoga",
                category="Raja",
                nature="benefic",
                planets=viparita_planets,
                houses=DUSTHANAS,
                description="Lords of dusthanas (6,8,12) placed in dusthanas",
                strength=70 + (viparita_count * 10),
                effects="Success through unconventional means, victory over enemies"
            ))
        
        return yogas
    
    # =========================================================================
    # DHANA YOGAS
    # =========================================================================
    
    def _check_dhana_yogas(self, chart: BirthChart, ctx: Dict) -> List[Yoga]:
        """Check for Dhana Yogas - wealth combinations."""
        yogas = []
        lagna_sign = ctx["lagna_sign"]
        
        # 1. Basic Dhana Yoga: 2nd and 11th lords connected
        lord_2 = self._get_house_lord(2, lagna_sign)
        lord_11 = self._get_house_lord(11, lagna_sign)
        
        l2_pos = chart.planets.get(lord_2)
        l11_pos = chart.planets.get(lord_11)
        
        if l2_pos and l11_pos and self._are_conjunct(l2_pos, l11_pos):
            yogas.append(Yoga(
                name="Dhana Yoga",
                category="Dhana",
                nature="benefic",
                planets=[lord_2, lord_11],
                houses=[2, 11],
                description=f"2nd lord ({lord_2}) and 11th lord ({lord_11}) conjunct",
                strength=80,
                effects="Accumulation of wealth, financial prosperity"
            ))
        
        # 2. Chandra-Mangal Yoga (Moon-Mars conjunction)
        moon = chart.planets["Moon"]
        mars = chart.planets["Mars"]
        
        if self._are_conjunct(moon, mars):
            yogas.append(Yoga(
                name="Chandra-Mangal Yoga",
                category="Dhana",
                nature="benefic",
                planets=["Moon", "Mars"],
                houses=[ctx["planet_houses"]["Moon"]],
                description="Moon and Mars in conjunction",
                strength=75,
                effects="Wealth through business, real estate, courage in financial matters"
            ))
        
        # 3. Gajakesari Yoga (Jupiter-Moon in Kendra from each other)
        moon_house = ctx["planet_houses"]["Moon"]
        jupiter_house = ctx["planet_houses"]["Jupiter"]
        
        difference = abs(moon_house - jupiter_house)
        if difference in [0, 3, 6, 9]:  # Same sign or mutual kendras
            strength = 85
            if chart.planets["Jupiter"].dignity in ["exalted", "own"]:
                strength = 95
            
            yogas.append(Yoga(
                name="Gajakesari Yoga",
                category="Dhana",
                nature="benefic",
                planets=["Jupiter", "Moon"],
                houses=[moon_house, jupiter_house],
                description="Jupiter and Moon in Kendra from each other",
                strength=strength,
                effects="Fame, reputation, lasting wealth, wisdom, respected position"
            ))
        
        # 4. Budhaditya Yoga (Sun-Mercury conjunction)
        sun = chart.planets["Sun"]
        mercury = chart.planets["Mercury"]
        
        if self._are_conjunct(sun, mercury) and not mercury.is_retrograde:
            # Mercury should not be combust (within 14 degrees of Sun)
            diff = abs(sun.longitude - mercury.longitude)
            if diff > 14 or diff < 346:
                yogas.append(Yoga(
                    name="Budhaditya Yoga",
                    category="Dhana",
                    nature="benefic",
                    planets=["Sun", "Mercury"],
                    houses=[ctx["planet_houses"]["Sun"]],
                    description="Sun and Mercury conjunct (Mercury not combust)",
                    strength=70,
                    effects="Intelligence, communication skills, success in business"
                ))
        
        return yogas
    
    # =========================================================================
    # CHANDRA (MOON) YOGAS
    # =========================================================================
    
    def _check_chandra_yogas(self, chart: BirthChart, ctx: Dict) -> List[Yoga]:
        """Check for Moon-based yogas."""
        yogas = []
        
        moon = chart.planets["Moon"]
        moon_house = ctx["planet_houses"]["Moon"]
        
        # 1. Sunafa Yoga (planet other than Sun in 2nd from Moon)
        second_from_moon = ((moon.rasi_index + 1) % 12)
        sunafa_planets = []
        
        for name, planet in chart.planets.items():
            if name == "Sun":
                continue
            if planet.rasi_index == second_from_moon:
                sunafa_planets.append(name)
        
        if sunafa_planets:
            yogas.append(Yoga(
                name="Sunafa Yoga",
                category="Chandra",
                nature="benefic",
                planets=sunafa_planets,
                houses=[(moon_house % 12) + 1],
                description=f"Planets in 2nd from Moon: {', '.join(sunafa_planets)}",
                strength=65,
                effects="Self-earned wealth, good reputation"
            ))
        
        # 2. Anafa Yoga (planet other than Sun in 12th from Moon)
        twelfth_from_moon = ((moon.rasi_index - 1) % 12)
        anafa_planets = []
        
        for name, planet in chart.planets.items():
            if name == "Sun":
                continue
            if planet.rasi_index == twelfth_from_moon:
                anafa_planets.append(name)
        
        if anafa_planets:
            yogas.append(Yoga(
                name="Anafa Yoga",
                category="Chandra",
                nature="benefic",
                planets=anafa_planets,
                houses=[((moon_house - 2) % 12) + 1],
                description=f"Planets in 12th from Moon: {', '.join(anafa_planets)}",
                strength=65,
                effects="Health, virtues, comfortable life"
            ))
        
        # 3. Durudhara Yoga (both 2nd and 12th from Moon occupied)
        if sunafa_planets and anafa_planets:
            yogas.append(Yoga(
                name="Durudhara Yoga",
                category="Chandra",
                nature="benefic",
                planets=sunafa_planets + anafa_planets,
                houses=[(moon_house % 12) + 1, ((moon_house - 2) % 12) + 1],
                description="Planets on both sides of Moon (2nd and 12th)",
                strength=80,
                effects="Wealth, vehicles, comforts, charitable nature, enjoyments"
            ))
        
        # 4. Kemadruma Yoga (no planets in 2nd and 12th from Moon)
        if not sunafa_planets and not anafa_planets:
            # Check for cancellation
            cancelled = False
            if self._is_in_kendra(moon_house):
                cancelled = True
            if ctx["planet_houses"].get("Jupiter") == moon_house:
                cancelled = True
            
            if not cancelled:
                yogas.append(Yoga(
                    name="Kemadruma Yoga",
                    category="Chandra",
                    nature="malefic",
                    planets=["Moon"],
                    houses=[moon_house],
                    description="No planets in 2nd or 12th from Moon",
                    strength=60,
                    effects="Periods of hardship, mental stress, poverty at times",
                    remedies="Worship Moon, wear pearl, chant Chandra mantras"
                ))
        
        return yogas
    
    # =========================================================================
    # SURYA (SUN) YOGAS
    # =========================================================================
    
    def _check_surya_yogas(self, chart: BirthChart, ctx: Dict) -> List[Yoga]:
        """Check for Sun-based yogas."""
        yogas = []
        
        sun = chart.planets["Sun"]
        sun_house = ctx["planet_houses"]["Sun"]
        
        # Veshi Yoga (planet in 2nd from Sun)
        second_from_sun = ((sun.rasi_index + 1) % 12)
        veshi_planets = []
        
        for name, planet in chart.planets.items():
            if name == "Moon":
                continue
            if planet.rasi_index == second_from_sun:
                veshi_planets.append(name)
        
        if veshi_planets:
            yogas.append(Yoga(
                name="Veshi Yoga",
                category="Surya",
                nature="benefic",
                planets=veshi_planets,
                houses=[(sun_house % 12) + 1],
                description=f"Planets in 2nd from Sun: {', '.join(veshi_planets)}",
                strength=60,
                effects="Truthful speech, scholarly, balanced nature"
            ))
        
        # Voshi Yoga (planet in 12th from Sun)
        twelfth_from_sun = ((sun.rasi_index - 1) % 12)
        voshi_planets = []
        
        for name, planet in chart.planets.items():
            if name == "Moon":
                continue
            if planet.rasi_index == twelfth_from_sun:
                voshi_planets.append(name)
        
        if voshi_planets:
            yogas.append(Yoga(
                name="Voshi Yoga",
                category="Surya",
                nature="benefic",
                planets=voshi_planets,
                houses=[((sun_house - 2) % 12) + 1],
                description=f"Planets in 12th from Sun: {', '.join(voshi_planets)}",
                strength=60,
                effects="Skilled, charitable, good memory"
            ))
        
        # Ubhayachari Yoga (planets on both sides of Sun)
        if veshi_planets and voshi_planets:
            yogas.append(Yoga(
                name="Ubhayachari Yoga",
                category="Surya",
                nature="benefic",
                planets=veshi_planets + voshi_planets,
                houses=[(sun_house % 12) + 1, ((sun_house - 2) % 12) + 1],
                description="Planets on both sides of Sun",
                strength=75,
                effects="Kingly status, eloquent, handsome, prosperous"
            ))
        
        return yogas
    
    # =========================================================================
    # NABHASA YOGAS
    # =========================================================================
    
    def _check_nabhasa_yogas(self, chart: BirthChart, ctx: Dict) -> List[Yoga]:
        """Check for Nabhasa Yogas - celestial pattern yogas."""
        yogas = []
        
        # Count planets in each sign
        planets_by_sign = {i: [] for i in range(12)}
        for name, planet in chart.planets.items():
            planets_by_sign[planet.rasi_index].append(name)
        
        # Count occupied signs
        occupied_signs = [s for s, planets in planets_by_sign.items() if planets]
        num_occupied = len(occupied_signs)
        
        # 1. Sankhya Yogas (based on number of occupied signs)
        if num_occupied == 1:
            yogas.append(Yoga(
                name="Yuga Yoga (Gola)",
                category="Nabhasa",
                nature="mixed",
                planets=list(chart.planets.keys()),
                houses=[occupied_signs[0] + 1],
                description="All planets in one sign",
                strength=90,
                effects="Extremely focused life, poverty or great wealth depending on sign"
            ))
        elif num_occupied == 2:
            yogas.append(Yoga(
                name="Yuga Yoga (Shakata)",
                category="Nabhasa",
                nature="mixed",
                planets=list(chart.planets.keys()),
                houses=[s + 1 for s in occupied_signs],
                description="All planets in two signs",
                strength=70,
                effects="Fluctuating fortunes, ups and downs"
            ))
        elif num_occupied == 7:
            yogas.append(Yoga(
                name="Veena Yoga",
                category="Nabhasa",
                nature="benefic",
                planets=list(chart.planets.keys()),
                houses=[s + 1 for s in occupied_signs],
                description="Planets in seven signs",
                strength=65,
                effects="Musical talent, artistic inclination, prosperity"
            ))
        
        # 2. Check for Sarpa Yoga (all malefics in kendras)
        malefics_in_kendra = []
        for planet in NATURAL_MALEFICS:
            if planet in ctx["planet_houses"]:
                if self._is_in_kendra(ctx["planet_houses"][planet]):
                    malefics_in_kendra.append(planet)
        
        if len(malefics_in_kendra) >= 3:
            yogas.append(Yoga(
                name="Sarpa Yoga",
                category="Nabhasa",
                nature="malefic",
                planets=malefics_in_kendra,
                houses=KENDRAS,
                description="Multiple malefics in Kendra houses",
                strength=55,
                effects="Struggles, obstacles, need for patience",
                remedies="Worship Lord Shiva, perform Navagraha puja"
            ))
        
        return yogas
    
    # =========================================================================
    # SPECIAL YOGAS
    # =========================================================================
    
    def _check_special_yogas(self, chart: BirthChart, ctx: Dict) -> List[Yoga]:
        """Check for special yogas like Kaal Sarpa, Manglik, etc."""
        yogas = []
        
        rahu = chart.planets["Rahu"]
        ketu = chart.planets["Ketu"]
        
        # 1. Kaal Sarpa Yoga
        # All planets between Rahu and Ketu
        rahu_deg = rahu.longitude
        ketu_deg = ketu.longitude
        
        all_between = True
        planets_count = 0
        
        for name, planet in chart.planets.items():
            if name in ["Rahu", "Ketu"]:
                continue
            
            p_deg = planet.longitude
            
            # Check if planet is between Rahu and Ketu
            if rahu_deg < ketu_deg:
                if not (rahu_deg <= p_deg <= ketu_deg):
                    all_between = False
                    break
            else:
                if not (p_deg >= rahu_deg or p_deg <= ketu_deg):
                    all_between = False
                    break
            
            planets_count += 1
        
        if all_between and planets_count >= 5:
            yogas.append(Yoga(
                name="Kaal Sarpa Yoga",
                category="Special",
                nature="malefic",
                planets=["Rahu", "Ketu"],
                houses=[ctx["planet_houses"]["Rahu"], ctx["planet_houses"]["Ketu"]],
                description="All planets hemmed between Rahu and Ketu",
                strength=80,
                effects="Karmic struggles, delayed success, spiritual growth through hardship",
                remedies="Kaal Sarpa Dosh puja, Rahu-Ketu mantras, Naag puja"
            ))
        
        # 2. Manglik Dosha (Kuja Dosha)
        mars = chart.planets["Mars"]
        mars_house = ctx["planet_houses"]["Mars"]
        
        manglik_houses = [1, 2, 4, 7, 8, 12]
        
        if mars_house in manglik_houses:
            # Check for cancellation
            cancelled = False
            cancellation_reasons = []
            
            # Mars in own sign or exalted
            if mars.dignity in ["own", "exalted", "moolatrikona"]:
                cancelled = True
                cancellation_reasons.append("Mars in own/exalted sign")
            
            # Jupiter aspects Mars
            if self._aspects("Jupiter", mars_house, ctx):
                cancelled = True
                cancellation_reasons.append("Jupiter aspects Mars")
            
            # Mars in Leo or Aquarius
            if mars.rasi_index in [4, 10]:
                cancelled = True
                cancellation_reasons.append("Mars in Leo/Aquarius")
            
            if not cancelled:
                yogas.append(Yoga(
                    name="Manglik Dosha",
                    category="Special",
                    nature="malefic",
                    planets=["Mars"],
                    houses=[mars_house],
                    description=f"Mars in {mars_house}th house",
                    strength=70,
                    effects="Challenges in marriage, need for partner matching",
                    remedies="Kumbh Vivah, Mangal Shanti puja, Tuesday fasting"
                ))
            else:
                yogas.append(Yoga(
                    name="Manglik Dosha (Cancelled)",
                    category="Special",
                    nature="neutral",
                    planets=["Mars"],
                    houses=[mars_house],
                    description=f"Mars in {mars_house}th but cancelled: {', '.join(cancellation_reasons)}",
                    strength=30,
                    effects="Minor or no Manglik effects due to cancellation"
                ))
        
        # 3. Neecha Bhanga Raja Yoga (Debilitation Cancellation)
        for name, planet in chart.planets.items():
            if planet.dignity != "debilitated":
                continue
            
            # Check for cancellation conditions
            cancellation = False
            reason = ""
            
            # Lord of debilitation sign in Kendra from Lagna or Moon
            deb_sign = planet.rasi_index
            deb_lord = SIGN_LORDS[deb_sign]
            deb_lord_house = ctx["planet_houses"].get(deb_lord)
            
            if deb_lord_house and self._is_in_kendra(deb_lord_house):
                cancellation = True
                reason = f"{deb_lord} (lord of debilitation sign) in Kendra"
            
            # Exaltation lord in Kendra
            if name in EXALTATION:
                exalt_sign = EXALTATION[name]["sign"]
                exalt_lord = SIGN_LORDS[exalt_sign]
                exalt_lord_house = ctx["planet_houses"].get(exalt_lord)
                
                if exalt_lord_house and self._is_in_kendra(exalt_lord_house):
                    cancellation = True
                    reason = f"{exalt_lord} (exaltation lord) in Kendra"
            
            if cancellation:
                yogas.append(Yoga(
                    name=f"Neecha Bhanga Raja Yoga ({name})",
                    category="Special",
                    nature="benefic",
                    planets=[name, deb_lord],
                    houses=[ctx["planet_houses"][name]],
                    description=f"Debilitated {name} gets cancellation: {reason}",
                    strength=85,
                    effects="Rise from low position to greatness, transformation of weakness into strength"
                ))
        
        return yogas
    
    # =========================================================================
    # ARISHTA YOGAS
    # =========================================================================
    
    def _check_arishta_yogas(self, chart: BirthChart, ctx: Dict) -> List[Yoga]:
        """Check for Arishta Yogas - affliction combinations."""
        yogas = []
        
        # 1. Daridra Yoga (11th lord in 6th or 12th)
        lagna_sign = ctx["lagna_sign"]
        lord_11 = self._get_house_lord(11, lagna_sign)
        lord_11_house = ctx["planet_houses"].get(lord_11)
        
        if lord_11_house in [6, 12]:
            yogas.append(Yoga(
                name="Daridra Yoga",
                category="Arishta",
                nature="malefic",
                planets=[lord_11],
                houses=[lord_11_house],
                description=f"11th lord ({lord_11}) in {lord_11_house}th house",
                strength=50,
                effects="Financial struggles, blocked income sources",
                remedies="Donate to charity, strengthen Jupiter"
            ))
        
        # 2. Grahan Yoga (Sun/Moon with Rahu/Ketu)
        sun = chart.planets["Sun"]
        moon = chart.planets["Moon"]
        rahu = chart.planets["Rahu"]
        ketu = chart.planets["Ketu"]
        
        if self._are_conjunct(sun, rahu) or self._are_conjunct(sun, ketu):
            yogas.append(Yoga(
                name="Surya Grahan Yoga",
                category="Arishta",
                nature="malefic",
                planets=["Sun", "Rahu" if self._are_conjunct(sun, rahu) else "Ketu"],
                houses=[ctx["planet_houses"]["Sun"]],
                description="Sun eclipsed by node",
                strength=60,
                effects="Issues with father, authority, self-confidence struggles",
                remedies="Surya mantras, respect father/authority, Sunday fasting"
            ))
        
        if self._are_conjunct(moon, rahu) or self._are_conjunct(moon, ketu):
            yogas.append(Yoga(
                name="Chandra Grahan Yoga",
                category="Arishta",
                nature="malefic",
                planets=["Moon", "Rahu" if self._are_conjunct(moon, rahu) else "Ketu"],
                houses=[ctx["planet_houses"]["Moon"]],
                description="Moon eclipsed by node",
                strength=60,
                effects="Mental stress, issues with mother, emotional challenges",
                remedies="Chandra mantras, respect mother, Monday fasting"
            ))
        
        # 3. Shakat Yoga (Moon in 6th, 8th, or 12th from Jupiter)
        moon_house = ctx["planet_houses"]["Moon"]
        jupiter_house = ctx["planet_houses"]["Jupiter"]
        
        diff = ((moon_house - jupiter_house) % 12) + 1
        if diff in [6, 8, 12]:
            yogas.append(Yoga(
                name="Shakata Yoga",
                category="Arishta",
                nature="malefic",
                planets=["Moon", "Jupiter"],
                houses=[moon_house, jupiter_house],
                description=f"Moon in {diff}th from Jupiter",
                strength=55,
                effects="Fluctuating fortunes, periods of prosperity followed by downfall",
                remedies="Strengthen both Moon and Jupiter, charity on Thursdays"
            ))
        
        return yogas
