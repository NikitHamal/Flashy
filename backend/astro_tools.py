"""
Astro Agent Tools Module

This module provides all the tools available to the Flashy Astro agent
for performing Vedic astrology operations including:
- Kundali (birth chart) management
- Chart calculations and analysis
- Dasha period queries
- Yoga detection
- Transit analysis
- Compatibility matching
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict

from .astro_engine import VedicEngine, BirthChart, Location
from .astro_yogas import YogaAnalyzer
from .astro_constants import (
    RASI_NAMES, RASI_NAMES_ENGLISH, NAKSHATRA_NAMES, PLANET_NAMES,
    HOUSE_SIGNIFICATIONS, VIMSHOTTARI_YEARS, Gender
)


@dataclass
class KundaliProfile:
    """A stored kundali profile."""
    id: str
    name: str
    datetime: str  # ISO format
    latitude: float
    longitude: float
    timezone: str
    place_name: str
    gender: str
    created_at: str
    updated_at: str
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KundaliProfile':
        return cls(**data)


class KundaliStorage:
    """
    In-memory storage for kundali profiles.
    In production, this syncs with frontend localStorage via API.
    """
    
    def __init__(self):
        self._profiles: Dict[str, KundaliProfile] = {}
        self._charts: Dict[str, BirthChart] = {}
    
    def create_profile(
        self,
        name: str,
        dt: datetime,
        latitude: float,
        longitude: float,
        timezone: str = "UTC",
        place_name: str = "",
        gender: str = "other",
        notes: str = ""
    ) -> KundaliProfile:
        """Create a new kundali profile."""
        profile_id = f"kundali_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        
        profile = KundaliProfile(
            id=profile_id,
            name=name,
            datetime=dt.isoformat(),
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            place_name=place_name,
            gender=gender,
            created_at=now,
            updated_at=now,
            notes=notes
        )
        
        self._profiles[profile_id] = profile
        return profile
    
    def get_profile(self, profile_id: str) -> Optional[KundaliProfile]:
        """Get a profile by ID."""
        return self._profiles.get(profile_id)
    
    def list_profiles(self) -> List[KundaliProfile]:
        """List all profiles."""
        return list(self._profiles.values())
    
    def update_profile(self, profile_id: str, updates: Dict[str, Any]) -> Optional[KundaliProfile]:
        """Update a profile."""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        
        for key, value in updates.items():
            if hasattr(profile, key) and key not in ['id', 'created_at']:
                setattr(profile, key, value)
        
        profile.updated_at = datetime.utcnow().isoformat()
        return profile
    
    def delete_profile(self, profile_id: str) -> bool:
        """Delete a profile."""
        if profile_id in self._profiles:
            del self._profiles[profile_id]
            if profile_id in self._charts:
                del self._charts[profile_id]
            return True
        return False
    
    def get_chart(self, profile_id: str) -> Optional[BirthChart]:
        """Get cached chart for a profile."""
        return self._charts.get(profile_id)
    
    def set_chart(self, profile_id: str, chart: BirthChart):
        """Cache a calculated chart."""
        self._charts[profile_id] = chart
    
    def load_from_data(self, profiles_data: List[Dict[str, Any]]):
        """Load profiles from external data (e.g., frontend)."""
        for data in profiles_data:
            try:
                profile = KundaliProfile.from_dict(data)
                self._profiles[profile.id] = profile
            except Exception:
                continue
    
    def export_data(self) -> List[Dict[str, Any]]:
        """Export all profiles as data."""
        return [p.to_dict() for p in self._profiles.values()]


class AstroTools:
    """
    Tool implementations for the Astro Agent.
    
    These tools enable the agent to:
    - Create and manage kundalis
    - Calculate and analyze charts
    - Query dasha periods
    - Check yogas
    - Perform compatibility analysis
    """
    
    def __init__(self, ayanamsa: str = "Lahiri"):
        self.engine = VedicEngine(ayanamsa=ayanamsa)
        self.yoga_analyzer = YogaAnalyzer()
        self.storage = KundaliStorage()
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Return list of available tools with their schemas."""
        return [
            {
                "name": "create_kundali",
                "description": "Create a new kundali (birth chart) profile for a person",
                "parameters": {
                    "name": {"type": "string", "description": "Name of the person"},
                    "birth_date": {"type": "string", "description": "Birth date in YYYY-MM-DD format"},
                    "birth_time": {"type": "string", "description": "Birth time in HH:MM format (24-hour)"},
                    "latitude": {"type": "number", "description": "Birth place latitude"},
                    "longitude": {"type": "number", "description": "Birth place longitude"},
                    "place_name": {"type": "string", "description": "Name of birth place"},
                    "timezone": {"type": "string", "description": "Timezone (e.g., 'Asia/Kolkata')"},
                    "gender": {"type": "string", "description": "Gender: male, female, or other"}
                },
                "required": ["name", "birth_date", "birth_time", "latitude", "longitude"]
            },
            {
                "name": "list_kundalis",
                "description": "List all saved kundali profiles",
                "parameters": {}
            },
            {
                "name": "get_kundali",
                "description": "Get detailed information about a specific kundali",
                "parameters": {
                    "profile_id": {"type": "string", "description": "The kundali profile ID"}
                },
                "required": ["profile_id"]
            },
            {
                "name": "delete_kundali",
                "description": "Delete a kundali profile",
                "parameters": {
                    "profile_id": {"type": "string", "description": "The kundali profile ID to delete"}
                },
                "required": ["profile_id"]
            },
            {
                "name": "get_planetary_positions",
                "description": "Get detailed planetary positions for a kundali",
                "parameters": {
                    "profile_id": {"type": "string", "description": "The kundali profile ID"}
                },
                "required": ["profile_id"]
            },
            {
                "name": "get_dasha_periods",
                "description": "Get Vimshottari Dasha periods for a kundali",
                "parameters": {
                    "profile_id": {"type": "string", "description": "The kundali profile ID"},
                    "include_current": {"type": "boolean", "description": "Include current running period analysis"}
                },
                "required": ["profile_id"]
            },
            {
                "name": "get_current_dasha",
                "description": "Get the currently running dasha period for a kundali",
                "parameters": {
                    "profile_id": {"type": "string", "description": "The kundali profile ID"},
                    "target_date": {"type": "string", "description": "Date to check (YYYY-MM-DD), defaults to today"}
                },
                "required": ["profile_id"]
            },
            {
                "name": "analyze_yogas",
                "description": "Analyze all yogas present in a kundali",
                "parameters": {
                    "profile_id": {"type": "string", "description": "The kundali profile ID"},
                    "category": {"type": "string", "description": "Filter by category: Raja, Dhana, Mahapurusha, etc."}
                },
                "required": ["profile_id"]
            },
            {
                "name": "get_house_analysis",
                "description": "Get detailed analysis of a specific house in the chart",
                "parameters": {
                    "profile_id": {"type": "string", "description": "The kundali profile ID"},
                    "house_number": {"type": "integer", "description": "House number (1-12)"}
                },
                "required": ["profile_id", "house_number"]
            },
            {
                "name": "get_divisional_chart",
                "description": "Get a specific divisional chart (Varga) positions",
                "parameters": {
                    "profile_id": {"type": "string", "description": "The kundali profile ID"},
                    "varga": {"type": "string", "description": "Varga chart: D1, D9, D10, D12, etc."}
                },
                "required": ["profile_id", "varga"]
            },
            {
                "name": "calculate_transit",
                "description": "Calculate current planetary transits and their effects",
                "parameters": {
                    "profile_id": {"type": "string", "description": "The kundali profile ID"},
                    "transit_date": {"type": "string", "description": "Date for transit (YYYY-MM-DD)"}
                },
                "required": ["profile_id"]
            },
            {
                "name": "check_compatibility",
                "description": "Check compatibility between two kundalis",
                "parameters": {
                    "profile_id_1": {"type": "string", "description": "First kundali profile ID"},
                    "profile_id_2": {"type": "string", "description": "Second kundali profile ID"}
                },
                "required": ["profile_id_1", "profile_id_2"]
            },
            {
                "name": "get_planet_strength",
                "description": "Get strength analysis for a specific planet",
                "parameters": {
                    "profile_id": {"type": "string", "description": "The kundali profile ID"},
                    "planet": {"type": "string", "description": "Planet name: Sun, Moon, Mars, etc."}
                },
                "required": ["profile_id", "planet"]
            },
            {
                "name": "calculate_chart_now",
                "description": "Calculate a chart for given birth details without saving",
                "parameters": {
                    "birth_date": {"type": "string", "description": "Birth date in YYYY-MM-DD format"},
                    "birth_time": {"type": "string", "description": "Birth time in HH:MM format"},
                    "latitude": {"type": "number", "description": "Birth place latitude"},
                    "longitude": {"type": "number", "description": "Birth place longitude"},
                    "timezone": {"type": "string", "description": "Timezone offset (e.g., '+05:30')"}
                },
                "required": ["birth_date", "birth_time", "latitude", "longitude"]
            },
            {
                "name": "get_remedies",
                "description": "Get astrological remedies based on chart analysis",
                "parameters": {
                    "profile_id": {"type": "string", "description": "The kundali profile ID"},
                    "focus_area": {"type": "string", "description": "Focus area: career, health, marriage, wealth, general"}
                },
                "required": ["profile_id"]
            }
        ]
    
    async def execute(self, tool_name: str, **kwargs) -> str:
        """Execute a tool by name with given arguments."""
        tool_map = {
            "create_kundali": self._create_kundali,
            "list_kundalis": self._list_kundalis,
            "get_kundali": self._get_kundali,
            "delete_kundali": self._delete_kundali,
            "get_planetary_positions": self._get_planetary_positions,
            "get_dasha_periods": self._get_dasha_periods,
            "get_current_dasha": self._get_current_dasha,
            "analyze_yogas": self._analyze_yogas,
            "get_house_analysis": self._get_house_analysis,
            "get_divisional_chart": self._get_divisional_chart,
            "calculate_transit": self._calculate_transit,
            "check_compatibility": self._check_compatibility,
            "get_planet_strength": self._get_planet_strength,
            "calculate_chart_now": self._calculate_chart_now,
            "get_remedies": self._get_remedies
        }
        
        if tool_name not in tool_map:
            return f"Error: Unknown tool '{tool_name}'"
        
        try:
            result = await tool_map[tool_name](**kwargs)
            return result
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
    
    async def _create_kundali(
        self,
        name: str,
        birth_date: str,
        birth_time: str,
        latitude: float,
        longitude: float,
        place_name: str = "",
        timezone: str = "UTC",
        gender: str = "other",
        **kwargs
    ) -> str:
        """Create a new kundali profile."""
        try:
            # Parse datetime
            dt_str = f"{birth_date} {birth_time}"
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            
            # Create profile
            profile = self.storage.create_profile(
                name=name,
                dt=dt,
                latitude=latitude,
                longitude=longitude,
                timezone=timezone,
                place_name=place_name,
                gender=gender
            )
            
            # Calculate chart
            location = Location(
                latitude=latitude,
                longitude=longitude,
                timezone=timezone,
                place_name=place_name
            )
            chart = self.engine.calculate_chart(dt, location)
            self.storage.set_chart(profile.id, chart)
            
            # Build summary
            lagna = chart.lagna
            moon = chart.planets["Moon"]
            sun = chart.planets["Sun"]
            
            summary = f"""Kundali Created Successfully!

Profile ID: {profile.id}
Name: {name}
Birth: {birth_date} at {birth_time}
Location: {place_name or f'{latitude}, {longitude}'}
Gender: {gender.capitalize()}

Chart Summary:
- Lagna (Ascendant): {lagna.rasi_name} ({lagna.rasi_name_english}) at {lagna.degree_in_sign:.2f}°
- Moon Sign: {moon.rasi_name} ({moon.rasi_name_english}) in {moon.nakshatra_name} Nakshatra, Pada {moon.nakshatra_pada}
- Sun Sign: {sun.rasi_name} ({sun.rasi_name_english})
- Ayanamsa: {chart.ayanamsa_name} ({chart.ayanamsa_value:.4f}°)

This kundali is now saved and ready for detailed analysis."""
            
            return summary
            
        except Exception as e:
            return f"Error creating kundali: {str(e)}"
    
    async def _list_kundalis(self, **kwargs) -> str:
        """List all saved kundalis."""
        profiles = self.storage.list_profiles()
        
        if not profiles:
            return "No kundalis found. Create one using create_kundali tool."
        
        lines = ["Saved Kundalis:", ""]
        for p in profiles:
            lines.append(f"- {p.name} (ID: {p.id})")
            lines.append(f"  Birth: {p.datetime[:10]} at {p.datetime[11:16]}")
            lines.append(f"  Place: {p.place_name or 'Not specified'}")
            lines.append(f"  Gender: {p.gender.capitalize()}")
            lines.append("")
        
        lines.append(f"Total: {len(profiles)} kundali(s)")
        return "\n".join(lines)
    
    async def _get_kundali(self, profile_id: str, **kwargs) -> str:
        """Get detailed kundali information."""
        profile = self.storage.get_profile(profile_id)
        if not profile:
            return f"Error: Kundali with ID '{profile_id}' not found"
        
        chart = self._ensure_chart(profile)
        if not chart:
            return f"Error: Could not calculate chart for '{profile_id}'"
        
        # Build comprehensive response
        lines = [
            f"Kundali: {profile.name}",
            f"ID: {profile.id}",
            "",
            "Birth Details:",
            f"  Date: {profile.datetime[:10]}",
            f"  Time: {profile.datetime[11:16]}",
            f"  Place: {profile.place_name}",
            f"  Coordinates: {profile.latitude:.4f}°, {profile.longitude:.4f}°",
            f"  Gender: {profile.gender.capitalize()}",
            "",
            "Chart Analysis:",
            f"  Ayanamsa: {chart.ayanamsa_name} ({chart.ayanamsa_value:.4f}°)",
            "",
            f"Lagna (Ascendant): {chart.lagna.rasi_name} at {chart.lagna.degree_in_sign:.2f}°",
            f"  Nakshatra: {chart.lagna.nakshatra_name}, Pada {chart.lagna.nakshatra_pada}",
            "",
            "Planetary Positions:",
        ]
        
        for name in PLANET_NAMES:
            p = chart.planets[name]
            retro = " (R)" if p.is_retrograde else ""
            dignity = f" [{p.dignity}]" if p.dignity != "neutral" else ""
            lines.append(f"  {name}: {p.rasi_name} at {p.degree_in_sign:.2f}°{retro}{dignity}")
            lines.append(f"    Nakshatra: {p.nakshatra_name}, Pada {p.nakshatra_pada}")
        
        return "\n".join(lines)
    
    async def _delete_kundali(self, profile_id: str, **kwargs) -> str:
        """Delete a kundali profile."""
        profile = self.storage.get_profile(profile_id)
        if not profile:
            return f"Error: Kundali with ID '{profile_id}' not found"
        
        name = profile.name
        success = self.storage.delete_profile(profile_id)
        
        if success:
            return f"Kundali '{name}' (ID: {profile_id}) has been deleted."
        else:
            return f"Error: Failed to delete kundali '{profile_id}'"
    
    async def _get_planetary_positions(self, profile_id: str, **kwargs) -> str:
        """Get detailed planetary positions."""
        profile = self.storage.get_profile(profile_id)
        if not profile:
            return f"Error: Kundali with ID '{profile_id}' not found"
        
        chart = self._ensure_chart(profile)
        if not chart:
            return f"Error: Could not calculate chart"
        
        lines = [f"Planetary Positions for {profile.name}:", ""]
        
        for name in PLANET_NAMES:
            p = chart.planets[name]
            lines.append(f"{name}:")
            lines.append(f"  Sign: {p.rasi_name} ({p.rasi_name_english})")
            lines.append(f"  Degree: {p.longitude:.4f}° ({p.degree_in_sign:.2f}° in sign)")
            lines.append(f"  Nakshatra: {p.nakshatra_name}, Pada {p.nakshatra_pada}")
            lines.append(f"  Nakshatra Lord: {p.nakshatra_lord}")
            lines.append(f"  Dignity: {p.dignity.capitalize()}")
            if p.is_retrograde:
                lines.append(f"  Status: RETROGRADE")
            lines.append(f"  Speed: {p.speed:.4f}°/day")
            lines.append("")
        
        return "\n".join(lines)
    
    async def _get_dasha_periods(
        self, profile_id: str, include_current: bool = True, **kwargs
    ) -> str:
        """Get Vimshottari Dasha periods."""
        profile = self.storage.get_profile(profile_id)
        if not profile:
            return f"Error: Kundali with ID '{profile_id}' not found"
        
        chart = self._ensure_chart(profile)
        if not chart:
            return f"Error: Could not calculate chart"
        
        lines = [f"Vimshottari Dasha for {profile.name}:", ""]
        
        # Current running period
        if include_current:
            current = self.engine.get_current_dasha(chart)
            if current["mahadasha"]:
                lines.append("Currently Running:")
                md = current["mahadasha"]
                lines.append(f"  Mahadasha: {md['planet']} ({md['start'][:10]} to {md['end'][:10]})")
                
                if current["antardasha"]:
                    ad = current["antardasha"]
                    lines.append(f"  Antardasha: {ad['planet']} ({ad['start'][:10]} to {ad['end'][:10]})")
                
                if current["pratyantardasha"]:
                    pd = current["pratyantardasha"]
                    lines.append(f"  Pratyantardasha: {pd['planet']} ({pd['start'][:10]} to {pd['end'][:10]})")
                
                lines.append("")
        
        lines.append("Mahadasha Periods:")
        for md in chart.vimshottari_dasha:
            lines.append(f"  {md.planet} Mahadasha: {md.start_date.strftime('%Y-%m-%d')} to {md.end_date.strftime('%Y-%m-%d')} ({md.duration_years:.1f} years)")
        
        return "\n".join(lines)
    
    async def _get_current_dasha(
        self, profile_id: str, target_date: str = None, **kwargs
    ) -> str:
        """Get current running dasha period."""
        profile = self.storage.get_profile(profile_id)
        if not profile:
            return f"Error: Kundali with ID '{profile_id}' not found"
        
        chart = self._ensure_chart(profile)
        if not chart:
            return f"Error: Could not calculate chart"
        
        target = datetime.utcnow()
        if target_date:
            try:
                target = datetime.strptime(target_date, "%Y-%m-%d")
            except ValueError:
                return f"Error: Invalid date format. Use YYYY-MM-DD"
        
        current = self.engine.get_current_dasha(chart, target)
        
        lines = [f"Dasha Period on {target.strftime('%Y-%m-%d')} for {profile.name}:", ""]
        
        if not current["mahadasha"]:
            lines.append("Could not determine dasha period for this date.")
            return "\n".join(lines)
        
        md = current["mahadasha"]
        lines.append(f"Mahadasha: {md['planet']}")
        lines.append(f"  Duration: {md['start'][:10]} to {md['end'][:10]}")
        lines.append(f"  Significations: {self._get_planet_significations(md['planet'])}")
        
        if current["antardasha"]:
            ad = current["antardasha"]
            lines.append(f"\nAntardasha: {ad['planet']}")
            lines.append(f"  Duration: {ad['start'][:10]} to {ad['end'][:10]}")
            lines.append(f"  Significations: {self._get_planet_significations(ad['planet'])}")
        
        if current["pratyantardasha"]:
            pd = current["pratyantardasha"]
            lines.append(f"\nPratyantardasha: {pd['planet']}")
            lines.append(f"  Duration: {pd['start'][:10]} to {pd['end'][:10]}")
        
        return "\n".join(lines)
    
    async def _analyze_yogas(
        self, profile_id: str, category: str = None, **kwargs
    ) -> str:
        """Analyze yogas in the chart."""
        profile = self.storage.get_profile(profile_id)
        if not profile:
            return f"Error: Kundali with ID '{profile_id}' not found"
        
        chart = self._ensure_chart(profile)
        if not chart:
            return f"Error: Could not calculate chart"
        
        all_yogas = self.yoga_analyzer.analyze(chart)
        
        # Filter by category if specified
        if category:
            all_yogas = [y for y in all_yogas if y.category.lower() == category.lower()]
        
        if not all_yogas:
            return f"No {'matching ' if category else ''}yogas found in the chart."
        
        lines = [f"Yoga Analysis for {profile.name}:", ""]
        
        # Group by category
        categories = {}
        for yoga in all_yogas:
            if yoga.category not in categories:
                categories[yoga.category] = []
            categories[yoga.category].append(yoga)
        
        for cat, yogas in categories.items():
            lines.append(f"{cat} Yogas:")
            for yoga in yogas:
                nature_icon = "+" if yoga.nature == "benefic" else "-" if yoga.nature == "malefic" else "~"
                lines.append(f"  [{nature_icon}] {yoga.name} (Strength: {yoga.strength}%)")
                lines.append(f"      Planets: {', '.join(yoga.planets)}")
                lines.append(f"      {yoga.description}")
                lines.append(f"      Effects: {yoga.effects}")
                if yoga.remedies:
                    lines.append(f"      Remedies: {yoga.remedies}")
                lines.append("")
        
        return "\n".join(lines)
    
    async def _get_house_analysis(
        self, profile_id: str, house_number: int, **kwargs
    ) -> str:
        """Get detailed house analysis."""
        if house_number < 1 or house_number > 12:
            return "Error: House number must be between 1 and 12"
        
        profile = self.storage.get_profile(profile_id)
        if not profile:
            return f"Error: Kundali with ID '{profile_id}' not found"
        
        chart = self._ensure_chart(profile)
        if not chart:
            return f"Error: Could not calculate chart"
        
        lagna_sign = chart.lagna.rasi_index
        house_sign = (lagna_sign + house_number - 1) % 12
        house_lord = SIGN_LORDS[house_sign]
        
        # Find planets in this house
        planets_in_house = []
        for name, planet in chart.planets.items():
            planet_house = ((planet.rasi_index - lagna_sign) % 12) + 1
            if planet_house == house_number:
                planets_in_house.append(name)
        
        # House lord position
        lord_pos = chart.planets.get(house_lord)
        lord_house = ((lord_pos.rasi_index - lagna_sign) % 12) + 1 if lord_pos else None
        
        lines = [
            f"House {house_number} Analysis for {profile.name}:",
            "",
            f"Sign: {RASI_NAMES[house_sign]} ({RASI_NAMES_ENGLISH[house_sign]})",
            f"Lord: {house_lord}",
            "",
            "Significations:",
        ]
        
        for sig in HOUSE_SIGNIFICATIONS.get(house_number, []):
            lines.append(f"  - {sig}")
        
        lines.append("")
        lines.append(f"Planets in House {house_number}:")
        if planets_in_house:
            for planet in planets_in_house:
                p = chart.planets[planet]
                lines.append(f"  - {planet} at {p.degree_in_sign:.2f}° ({p.dignity})")
        else:
            lines.append("  (Empty - no planets)")
        
        lines.append("")
        if lord_pos:
            lines.append(f"House Lord ({house_lord}) Position:")
            lines.append(f"  Placed in House {lord_house} ({lord_pos.rasi_name})")
            lines.append(f"  Dignity: {lord_pos.dignity}")
            if lord_pos.is_retrograde:
                lines.append("  Status: Retrograde")
        
        return "\n".join(lines)
    
    async def _get_divisional_chart(
        self, profile_id: str, varga: str = "D9", **kwargs
    ) -> str:
        """Get divisional chart positions."""
        profile = self.storage.get_profile(profile_id)
        if not profile:
            return f"Error: Kundali with ID '{profile_id}' not found"
        
        chart = self._ensure_chart(profile)
        if not chart:
            return f"Error: Could not calculate chart"
        
        varga = varga.upper()
        if varga not in chart.divisional_charts:
            available = ", ".join(chart.divisional_charts.keys())
            return f"Error: Varga '{varga}' not found. Available: {available}"
        
        varga_positions = chart.divisional_charts[varga]
        
        varga_names = {
            "D1": "Rasi (Birth Chart)",
            "D2": "Hora (Wealth)",
            "D3": "Drekkana (Siblings)",
            "D7": "Saptamsha (Children)",
            "D9": "Navamsha (Marriage/Dharma)",
            "D10": "Dasamsha (Career)",
            "D12": "Dwadashamsha (Parents)"
        }
        
        lines = [
            f"{varga} Chart - {varga_names.get(varga, 'Divisional Chart')}",
            f"For: {profile.name}",
            "",
            "Positions:"
        ]
        
        for planet, sign_idx in varga_positions.items():
            lines.append(f"  {planet}: {RASI_NAMES[sign_idx]} ({RASI_NAMES_ENGLISH[sign_idx]})")
        
        return "\n".join(lines)
    
    async def _calculate_transit(
        self, profile_id: str, transit_date: str = None, **kwargs
    ) -> str:
        """Calculate transits for a kundali."""
        profile = self.storage.get_profile(profile_id)
        if not profile:
            return f"Error: Kundali with ID '{profile_id}' not found"
        
        chart = self._ensure_chart(profile)
        if not chart:
            return f"Error: Could not calculate chart"
        
        # Parse transit date or use today
        transit_dt = datetime.utcnow()
        if transit_date:
            try:
                transit_dt = datetime.strptime(transit_date, "%Y-%m-%d")
            except ValueError:
                return "Error: Invalid date format. Use YYYY-MM-DD"
        
        # Calculate transit chart
        location = Location(
            latitude=profile.latitude,
            longitude=profile.longitude,
            timezone=profile.timezone,
            place_name=profile.place_name
        )
        transit_chart = self.engine.calculate_chart(transit_dt, location, include_dashas=False)
        
        lines = [
            f"Transit Analysis for {profile.name}",
            f"Date: {transit_dt.strftime('%Y-%m-%d')}",
            "",
            "Current Planetary Transits:"
        ]
        
        lagna_sign = chart.lagna.rasi_index
        
        for name in ["Saturn", "Jupiter", "Rahu", "Ketu", "Mars"]:
            natal = chart.planets[name]
            transit = transit_chart.planets[name]
            
            natal_house = ((natal.rasi_index - lagna_sign) % 12) + 1
            transit_house = ((transit.rasi_index - lagna_sign) % 12) + 1
            
            lines.append(f"\n{name}:")
            lines.append(f"  Natal: {natal.rasi_name} (House {natal_house})")
            lines.append(f"  Transit: {transit.rasi_name} (House {transit_house})")
            
            # Simple transit interpretation
            if transit_house == natal_house:
                lines.append(f"  Effect: Transiting over natal position - significant period")
            elif transit_house in [1, 4, 7, 10]:
                lines.append(f"  Effect: Transiting Kendra from Lagna - prominent influence")
        
        return "\n".join(lines)
    
    async def _check_compatibility(
        self, profile_id_1: str, profile_id_2: str, **kwargs
    ) -> str:
        """Check compatibility between two kundalis (Ashtakoota)."""
        profile1 = self.storage.get_profile(profile_id_1)
        profile2 = self.storage.get_profile(profile_id_2)
        
        if not profile1:
            return f"Error: Kundali with ID '{profile_id_1}' not found"
        if not profile2:
            return f"Error: Kundali with ID '{profile_id_2}' not found"
        
        chart1 = self._ensure_chart(profile1)
        chart2 = self._ensure_chart(profile2)
        
        if not chart1 or not chart2:
            return "Error: Could not calculate one or both charts"
        
        moon1 = chart1.planets["Moon"]
        moon2 = chart2.planets["Moon"]
        
        # Calculate Ashtakoota points (simplified)
        total_points = 0
        max_points = 36
        
        kootas = self._calculate_kootas(moon1, moon2)
        
        lines = [
            f"Compatibility Analysis",
            f"Person 1: {profile1.name} - Moon in {moon1.nakshatra_name}",
            f"Person 2: {profile2.name} - Moon in {moon2.nakshatra_name}",
            "",
            "Ashtakoota Matching:"
        ]
        
        for koota_name, (points, max_p, desc) in kootas.items():
            total_points += points
            lines.append(f"  {koota_name}: {points}/{max_p} - {desc}")
        
        lines.append("")
        lines.append(f"Total Score: {total_points}/{max_points} points")
        
        # Interpretation
        if total_points >= 25:
            lines.append("Result: EXCELLENT match - highly compatible")
        elif total_points >= 18:
            lines.append("Result: GOOD match - compatible with minor adjustments")
        elif total_points >= 12:
            lines.append("Result: AVERAGE match - some challenges expected")
        else:
            lines.append("Result: CHALLENGING match - significant differences")
        
        return "\n".join(lines)
    
    async def _get_planet_strength(
        self, profile_id: str, planet: str, **kwargs
    ) -> str:
        """Get strength analysis for a planet."""
        if planet not in PLANET_NAMES:
            return f"Error: Invalid planet name. Use: {', '.join(PLANET_NAMES)}"
        
        profile = self.storage.get_profile(profile_id)
        if not profile:
            return f"Error: Kundali with ID '{profile_id}' not found"
        
        chart = self._ensure_chart(profile)
        if not chart:
            return f"Error: Could not calculate chart"
        
        p = chart.planets[planet]
        lagna_sign = chart.lagna.rasi_index
        house = ((p.rasi_index - lagna_sign) % 12) + 1
        
        lines = [
            f"{planet} Strength Analysis for {profile.name}:",
            "",
            f"Position: {p.rasi_name} ({p.rasi_name_english}) at {p.degree_in_sign:.2f}°",
            f"House: {house}",
            f"Nakshatra: {p.nakshatra_name}, Pada {p.nakshatra_pada}",
            f"Nakshatra Lord: {p.nakshatra_lord}",
            "",
            "Strength Factors:"
        ]
        
        strength_score = 50  # Base score
        
        # Dignity
        if p.dignity == "exalted":
            lines.append("  [+] Exalted - Maximum strength (+30)")
            strength_score += 30
        elif p.dignity == "moolatrikona":
            lines.append("  [+] Moolatrikona - Very strong (+25)")
            strength_score += 25
        elif p.dignity == "own":
            lines.append("  [+] Own sign - Strong (+20)")
            strength_score += 20
        elif p.dignity == "debilitated":
            lines.append("  [-] Debilitated - Weakened (-25)")
            strength_score -= 25
        else:
            lines.append("  [~] Neutral dignity")
        
        # House placement
        if house in [1, 4, 7, 10]:
            lines.append(f"  [+] In Kendra (House {house}) - Angular strength (+10)")
            strength_score += 10
        elif house in [5, 9]:
            lines.append(f"  [+] In Trikona (House {house}) - Fortunate placement (+10)")
            strength_score += 10
        elif house in [6, 8, 12]:
            lines.append(f"  [-] In Dusthana (House {house}) - Challenged (-10)")
            strength_score -= 10
        
        # Retrograde
        if p.is_retrograde:
            lines.append("  [~] Retrograde - Internalized energy")
        
        # Final score
        strength_score = max(0, min(100, strength_score))
        lines.append("")
        lines.append(f"Overall Strength Score: {strength_score}/100")
        
        if strength_score >= 70:
            lines.append("Status: STRONG - This planet operates powerfully")
        elif strength_score >= 40:
            lines.append("Status: MODERATE - Average functioning")
        else:
            lines.append("Status: WEAK - May benefit from remedies")
        
        return "\n".join(lines)
    
    async def _calculate_chart_now(
        self,
        birth_date: str,
        birth_time: str,
        latitude: float,
        longitude: float,
        timezone: str = "+00:00",
        **kwargs
    ) -> str:
        """Calculate a chart without saving."""
        try:
            dt_str = f"{birth_date} {birth_time}"
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            
            location = Location(
                latitude=latitude,
                longitude=longitude,
                timezone=timezone
            )
            
            chart = self.engine.calculate_chart(dt, location)
            
            lines = [
                "Birth Chart Calculation:",
                f"Date/Time: {birth_date} {birth_time}",
                f"Location: {latitude:.4f}, {longitude:.4f}",
                "",
                f"Lagna: {chart.lagna.rasi_name} at {chart.lagna.degree_in_sign:.2f}°",
                f"Moon: {chart.planets['Moon'].rasi_name} in {chart.planets['Moon'].nakshatra_name}",
                f"Sun: {chart.planets['Sun'].rasi_name}",
                "",
                "All Planets:"
            ]
            
            for name in PLANET_NAMES:
                p = chart.planets[name]
                retro = " (R)" if p.is_retrograde else ""
                lines.append(f"  {name}: {p.rasi_name} {p.degree_in_sign:.1f}°{retro}")
            
            lines.append("")
            lines.append("Use create_kundali to save this chart for detailed analysis.")
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"Error calculating chart: {str(e)}"
    
    async def _get_remedies(
        self, profile_id: str, focus_area: str = "general", **kwargs
    ) -> str:
        """Get remedies based on chart analysis."""
        profile = self.storage.get_profile(profile_id)
        if not profile:
            return f"Error: Kundali with ID '{profile_id}' not found"
        
        chart = self._ensure_chart(profile)
        if not chart:
            return f"Error: Could not calculate chart"
        
        yogas = self.yoga_analyzer.analyze(chart)
        
        lines = [
            f"Astrological Remedies for {profile.name}",
            f"Focus Area: {focus_area.capitalize()}",
            "",
        ]
        
        # Find afflicted planets
        afflicted = []
        for name, planet in chart.planets.items():
            if planet.dignity == "debilitated":
                afflicted.append(name)
        
        # Find malefic yogas
        malefic_yogas = [y for y in yogas if y.nature == "malefic" and y.remedies]
        
        if afflicted:
            lines.append("Planetary Remedies:")
            for planet in afflicted:
                lines.append(f"\n{planet} (Debilitated):")
                lines.extend(self._get_planet_remedies(planet))
        
        if malefic_yogas:
            lines.append("\nYoga-Specific Remedies:")
            for yoga in malefic_yogas[:3]:  # Top 3
                lines.append(f"\n{yoga.name}:")
                lines.append(f"  {yoga.remedies}")
        
        # General recommendations
        lines.append("\nGeneral Recommendations:")
        lines.append("  - Perform regular meditation and spiritual practices")
        lines.append("  - Respect and serve parents and elders")
        lines.append("  - Practice charity and selfless service")
        lines.append("  - Wear appropriate gemstones after consultation")
        lines.append("  - Follow favorable muhurtas for important activities")
        
        return "\n".join(lines)
    
    # Helper methods
    
    def _ensure_chart(self, profile: KundaliProfile) -> Optional[BirthChart]:
        """Ensure chart is calculated for a profile."""
        chart = self.storage.get_chart(profile.id)
        if chart:
            return chart
        
        try:
            dt = datetime.fromisoformat(profile.datetime)
            location = Location(
                latitude=profile.latitude,
                longitude=profile.longitude,
                timezone=profile.timezone,
                place_name=profile.place_name
            )
            chart = self.engine.calculate_chart(dt, location)
            self.storage.set_chart(profile.id, chart)
            return chart
        except Exception:
            return None
    
    def _get_planet_significations(self, planet: str) -> str:
        """Get brief significations for a planet."""
        sigs = {
            "Sun": "Soul, father, authority, government, health",
            "Moon": "Mind, mother, emotions, public, liquids",
            "Mars": "Energy, courage, siblings, property, disputes",
            "Mercury": "Intelligence, communication, business, education",
            "Jupiter": "Wisdom, children, fortune, spirituality, expansion",
            "Venus": "Love, marriage, luxury, arts, vehicles",
            "Saturn": "Discipline, delays, labor, longevity, karma",
            "Rahu": "Ambition, foreign, unconventional, obsession",
            "Ketu": "Spirituality, detachment, past karma, liberation"
        }
        return sigs.get(planet, "")
    
    def _calculate_kootas(
        self, moon1: 'PlanetPosition', moon2: 'PlanetPosition'
    ) -> Dict[str, tuple]:
        """Calculate Ashtakoota matching points."""
        # Simplified Koota calculation
        nak1 = moon1.nakshatra_index
        nak2 = moon2.nakshatra_index
        sign1 = moon1.rasi_index
        sign2 = moon2.rasi_index
        
        kootas = {}
        
        # 1. Varna (1 point)
        varna_score = 1 if (sign1 % 4) >= (sign2 % 4) else 0
        kootas["Varna"] = (varna_score, 1, "Spiritual compatibility")
        
        # 2. Vashya (2 points)
        vashya_score = 1  # Simplified
        kootas["Vashya"] = (vashya_score, 2, "Mutual attraction")
        
        # 3. Tara (3 points)
        tara_diff = abs(nak1 - nak2) % 9
        tara_score = 3 if tara_diff not in [2, 4, 6] else 1
        kootas["Tara"] = (tara_score, 3, "Destiny compatibility")
        
        # 4. Yoni (4 points)
        yoni_score = 2  # Simplified
        kootas["Yoni"] = (yoni_score, 4, "Physical compatibility")
        
        # 5. Graha Maitri (5 points)
        maitri_score = 5 if sign1 == sign2 else 3
        kootas["Graha Maitri"] = (maitri_score, 5, "Mental compatibility")
        
        # 6. Gana (6 points)
        gana_score = 4  # Simplified
        kootas["Gana"] = (gana_score, 6, "Temperament match")
        
        # 7. Bhakoot (7 points)
        bhakoot_diff = abs(sign1 - sign2)
        bad_bhakoot = bhakoot_diff in [1, 4, 5, 6, 7, 11]
        bhakoot_score = 0 if bad_bhakoot else 7
        kootas["Bhakoot"] = (bhakoot_score, 7, "Family harmony")
        
        # 8. Nadi (8 points)
        nadi1 = nak1 % 3
        nadi2 = nak2 % 3
        nadi_score = 0 if nadi1 == nadi2 else 8
        kootas["Nadi"] = (nadi_score, 8, "Health/progeny")
        
        return kootas
    
    def _get_planet_remedies(self, planet: str) -> List[str]:
        """Get remedies for a planet."""
        remedies = {
            "Sun": [
                "  - Offer water to Sun at sunrise",
                "  - Chant Aditya Hridayam or Gayatri Mantra",
                "  - Wear Ruby after consultation",
                "  - Fast on Sundays"
            ],
            "Moon": [
                "  - Offer milk/water to Shiva on Mondays",
                "  - Chant Chandra mantras",
                "  - Wear Pearl after consultation",
                "  - Serve mother and respect women"
            ],
            "Mars": [
                "  - Worship Hanuman on Tuesdays",
                "  - Chant Mangal mantras",
                "  - Wear Red Coral after consultation",
                "  - Donate red items on Tuesdays"
            ],
            "Mercury": [
                "  - Worship Vishnu on Wednesdays",
                "  - Chant Budh mantras",
                "  - Wear Emerald after consultation",
                "  - Feed green vegetables to cows"
            ],
            "Jupiter": [
                "  - Worship Guru/Brihaspati on Thursdays",
                "  - Chant Guru mantras",
                "  - Wear Yellow Sapphire after consultation",
                "  - Respect teachers and elders"
            ],
            "Venus": [
                "  - Worship Lakshmi on Fridays",
                "  - Chant Shukra mantras",
                "  - Wear Diamond after consultation",
                "  - Donate white items on Fridays"
            ],
            "Saturn": [
                "  - Worship Shani on Saturdays",
                "  - Chant Shani mantras",
                "  - Wear Blue Sapphire after consultation",
                "  - Serve the poor and disabled"
            ]
        }
        return remedies.get(planet, ["  - Consult an astrologer for specific remedies"])
