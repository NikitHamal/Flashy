"""
Astro Tools Module

This module provides the tool definitions for the Flashy Vedic Astrology Agent.
Handles kundali creation, retrieval, and various Vedic astrology calculations.

All calculations are performed client-side using the AstroWeb engine.
The backend stores and retrieves chart data while providing structured interfaces
for the AI agent to query astrological information.
"""

import uuid
import json
import requests
import traceback
import inspect
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class ChartStyle(Enum):
    NORTH_INDIAN = "north"
    SOUTH_INDIAN = "south"
    EAST_INDIAN = "east"


class AyanamsaSystem(Enum):
    LAHIRI = "Lahiri"
    RAMAN = "Raman"
    KRISHNAMURTI = "Krishnamurti"
    FAGAN_BRADLEY = "FaganBradley"
    YUKTESHWAR = "Yukteshwar"
    TRUE_CHITRA = "TrueChitra"
    PUSHYA_PAKSHA = "PushyaPaksha"


@dataclass
class BirthDetails:
    """Birth details for kundali creation."""
    name: str
    date: str  # ISO format: YYYY-MM-DD
    time: str  # 24-hour format: HH:MM
    place: str
    latitude: float
    longitude: float
    timezone: str  # e.g., "Asia/Kolkata", "+05:30"
    gender: str = "male"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Kundali:
    """Complete kundali data structure."""
    id: str
    birth_details: BirthDetails
    created_at: str
    updated_at: str
    ayanamsa_system: str = "Lahiri"
    chart_style: str = "north"

    # Calculated data (populated by frontend after calculation)
    chart_data: Optional[Dict[str, Any]] = None

    # User notes
    notes: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "birth_details": self.birth_details.to_dict() if isinstance(self.birth_details, BirthDetails) else self.birth_details,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "ayanamsa_system": self.ayanamsa_system,
            "chart_style": self.chart_style,
            "notes": self.notes,
            "tags": self.tags
        }
        if self.chart_data:
            data["chart_data"] = self.chart_data
        return data


class AstroTools:
    """
    Manages Vedic astrology tools and kundali storage.

    Note: Actual astronomical calculations are performed client-side
    using the AstroWeb JavaScript engine. This backend handles:
    - Kundali CRUD operations
    - Data formatting for AI interpretation
    - Query interfaces for astrological data
    """

    def __init__(self):
        # In-memory storage (synced with localStorage via API)
        self.kundalis: Dict[str, Kundali] = {}
        self.default_ayanamsa = AyanamsaSystem.LAHIRI.value
        self.default_chart_style = ChartStyle.NORTH_INDIAN.value

    def get_available_tools(self) -> List[Dict[str, str]]:
        """Get list of available astrology tools with descriptions."""
        return [
            # Kundali CRUD
            {"name": "create_kundali", "description": "Create a new kundali/birth chart with birth details"},
            {"name": "get_kundali", "description": "Get full kundali details by ID"},
            {"name": "list_kundalis", "description": "List all stored kundalis"},
            {"name": "update_kundali", "description": "Update kundali notes or tags"},
            {"name": "delete_kundali", "description": "Delete a kundali by ID"},
            {"name": "search_kundalis", "description": "Search kundalis by name or tags"},

            # Planetary Queries
            {"name": "get_planetary_positions", "description": "Get all planetary positions for a kundali"},
            {"name": "get_planet_details", "description": "Get detailed info about a specific planet"},
            {"name": "get_house_details", "description": "Get details about a specific house/bhava"},
            {"name": "get_nakshatra_details", "description": "Get nakshatra information for a planet or lagna"},

            # Dasha Queries
            {"name": "get_current_dasha", "description": "Get currently running dasha periods"},
            {"name": "get_dasha_timeline", "description": "Get dasha timeline for specified years"},
            {"name": "get_dasha_analysis", "description": "Get analysis of a specific dasha period"},

            # Yoga Queries
            {"name": "get_yogas", "description": "Get all yogas present in the chart"},
            {"name": "get_yoga_details", "description": "Get detailed interpretation of a specific yoga"},
            {"name": "check_specific_yoga", "description": "Check if a specific yoga is present"},

            # Divisional Charts
            {"name": "get_divisional_chart", "description": "Get a specific divisional chart (D1-D60)"},
            {"name": "get_varga_positions", "description": "Get planet positions in all or specific vargas"},

            # Compatibility
            {"name": "check_compatibility", "description": "Check Ashtakoot compatibility between two charts"},
            {"name": "get_manglik_status", "description": "Check Manglik/Kuja dosha status"},

            # Transit & Predictions
            {"name": "get_current_transits", "description": "Get current planetary transits over natal chart"},
            {"name": "get_transit_analysis", "description": "Analyze impact of transits on a chart"},

            # Panchang
            {"name": "get_panchang", "description": "Get panchang details for a specific date/location"},
            {"name": "get_muhurta", "description": "Find auspicious muhurta for specific activities"},

            # Analysis
            {"name": "get_strength_analysis", "description": "Get Shadbala planetary strength analysis"},
            {"name": "get_ashtakavarga", "description": "Get Ashtakavarga point analysis"},
            {"name": "get_chart_summary", "description": "Get AI-friendly summary of the chart"},

            # Settings
            {"name": "set_ayanamsa", "description": "Set the ayanamsa system for calculations"},
            {"name": "get_available_ayanamsas", "description": "List available ayanamsa systems"},

            # Geocoding
            {"name": "search_place", "description": "Search for a place to get its coordinates and timezone"}
        ]

    async def execute(self, tool_name: str, **kwargs) -> str:
        """Execute an astrology tool and return result."""
        method = getattr(self, tool_name, None)
        if method is None:
            return json.dumps({
                "status": "error",
                "message": f"Unknown tool '{tool_name}'"
            })

        try:
            # Check if method is async or sync
            if inspect.iscoroutinefunction(method):
                result = await method(**kwargs)
            else:
                result = method(**kwargs)
            return result
        except Exception as e:
            traceback.print_exc()
            return json.dumps({
                "status": "error",
                "message": f"Error executing {tool_name}: {str(e)}"
            }, indent=2)

    # =========================================================================
    # KUNDALI CRUD OPERATIONS
    # =========================================================================

    def create_kundali(
        self,
        name: str,
        date: str,
        time: str,
        place: str,
        latitude: Any = None,
        longitude: Any = None,
        timezone: str = None,
        gender: str = "male",
        notes: str = "",
        tags: List[str] = None
    ) -> str:
        """
        Create a new kundali with birth details.

        Args:
            name: Person's name
            date: Birth date in YYYY-MM-DD format
            time: Birth time in HH:MM format (24-hour)
            place: Birth place name
            latitude: Birth place latitude (float)
            longitude: Birth place longitude (float)
            timezone: Timezone string (e.g., "Asia/Kolkata" or "+05:30")
            gender: Gender (male/female/other)
            notes: Optional notes
            tags: Optional tags for organization

        Returns:
            JSON string with created kundali details
        """
        # Validate technical requirements
        missing = []
        if latitude is None: missing.append("latitude")
        if longitude is None: missing.append("longitude")
        if timezone is None: missing.append("timezone")

        if missing:
            return json.dumps({
                "status": "error",
                "message": f"I need the following technical details to cast the sacred chart for {name}: {', '.join(missing)}. "
                           f"Please use the 'search_place' tool for '{place}' to find these details before calling me again."
            }, indent=2)

        # Ensure numeric types
        try:
            lat_f = float(latitude)
            lon_f = float(longitude)
        except (ValueError, TypeError):
            return json.dumps({
                "status": "error",
                "message": "Latitude and longitude must be numbers. Use 'search_place' to get accurate coordinates."
            }, indent=2)

        kundali_id = f"kundali_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat() + "Z"

        birth_details = BirthDetails(
            name=name,
            date=date,
            time=time,
            place=place,
            latitude=lat_f,
            longitude=lon_f,
            timezone=timezone,
            gender=gender
        )

        kundali = Kundali(
            id=kundali_id,
            birth_details=birth_details,
            created_at=now,
            updated_at=now,
            ayanamsa_system=self.default_ayanamsa,
            chart_style=self.default_chart_style,
            notes=notes,
            tags=tags or []
        )

        self.kundalis[kundali_id] = kundali

        return json.dumps({
            "status": "success",
            "message": f"Created kundali for {name}",
            "kundali": kundali.to_dict()
        }, indent=2)

    def search_place(self, query: str) -> str:
        """
        Search for a place and get its coordinates and timezone.

        Args:
            query: City name or place description

        Returns:
            JSON string with place details (lat, lon, timezone)
        """
        try:
            # Use Nominatim for geocoding
            url = f"https://nominatim.openstreetmap.org/search?format=json&q={requests.utils.quote(query)}&limit=1"
            headers = {"User-Agent": "FlashyAstroAgent/1.0"}
            response = requests.get(url, headers=headers, timeout=10)
            results = response.json()

            if not results:
                return json.dumps({
                    "status": "error",
                    "message": f"I cannot find the coordinates for '{query}' in my cosmic records. Please provide a more specific city or country name."
                })

            place = results[0]
            lat = float(place["lat"])
            lon = float(place["lon"])

            # Simple timezone approximation based on longitude
            offset_hours = round(lon / 15.0)
            sign = "+" if offset_hours >= 0 else "-"
            # Format as UTC+HH:00
            timezone_approx = f"UTC{sign}{abs(offset_hours):02g}:00"

            # Region specific overrides
            display_name = place.get("display_name", "").lower()
            if "india" in display_name:
                timezone_approx = "Asia/Kolkata"
            elif "nepal" in display_name:
                timezone_approx = "Asia/Kathmandu"

            return json.dumps({
                "status": "success",
                "query": query,
                "display_name": place["display_name"],
                "latitude": lat,
                "longitude": lon,
                "timezone": timezone_approx
            }, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error searching place: {str(e)}"
            })

    def get_kundali(self, kundali_id: str) -> str:
        """Get full kundali details by ID."""
        if kundali_id not in self.kundalis:
            return json.dumps({
                "status": "error",
                "message": f"Kundali '{kundali_id}' not found"
            })

        kundali = self.kundalis[kundali_id]
        return json.dumps({
            "status": "success",
            "kundali": kundali.to_dict()
        }, indent=2)

    def list_kundalis(self, limit: int = 50, offset: int = 0) -> str:
        """List all stored kundalis."""
        kundalis_list = list(self.kundalis.values())
        # Sort by updated_at descending
        kundalis_list.sort(key=lambda k: k.updated_at, reverse=True)

        # Apply pagination
        paginated = kundalis_list[offset:offset + limit]

        # Return full kundali data so frontend can use it for chart display
        kundalis_data = []
        for k in paginated:
            kundalis_data.append(k.to_dict())

        return json.dumps({
            "status": "success",
            "total": len(self.kundalis),
            "showing": len(kundalis_data),
            "kundalis": kundalis_data
        }, indent=2)

    def update_kundali(
        self,
        kundali_id: str,
        notes: str = None,
        tags: List[str] = None,
        chart_data: Dict[str, Any] = None
    ) -> str:
        """Update kundali notes, tags, or chart data."""
        if kundali_id not in self.kundalis:
            return json.dumps({
                "status": "error",
                "message": f"Kundali '{kundali_id}' not found"
            })

        kundali = self.kundalis[kundali_id]

        if notes is not None:
            kundali.notes = notes
        if tags is not None:
            kundali.tags = tags
        if chart_data is not None:
            kundali.chart_data = chart_data

        kundali.updated_at = datetime.utcnow().isoformat() + "Z"

        return json.dumps({
            "status": "success",
            "message": f"Updated kundali '{kundali_id}'",
            "kundali": kundali.to_dict()
        }, indent=2)

    def delete_kundali(self, kundali_id: str) -> str:
        """Delete a kundali by ID."""
        if kundali_id not in self.kundalis:
            return json.dumps({
                "status": "error",
                "message": f"Kundali '{kundali_id}' not found"
            })

        name = self.kundalis[kundali_id].birth_details
        if isinstance(name, BirthDetails):
            name = name.name
        else:
            name = name.get("name", kundali_id)

        del self.kundalis[kundali_id]

        return json.dumps({
            "status": "success",
            "message": f"Deleted kundali for '{name}'"
        })

    def search_kundalis(self, query: str) -> str:
        """Search kundalis by name or tags."""
        query_lower = query.lower()
        results = []

        for kundali in self.kundalis.values():
            bd = kundali.birth_details if isinstance(kundali.birth_details, dict) else kundali.birth_details.to_dict()
            name = bd.get("name", "").lower()
            tags = [t.lower() for t in kundali.tags]

            if query_lower in name or any(query_lower in tag for tag in tags):
                results.append({
                    "id": kundali.id,
                    "name": bd.get("name"),
                    "date": bd.get("date"),
                    "place": bd.get("place"),
                    "tags": kundali.tags
                })

        return json.dumps({
            "status": "success",
            "query": query,
            "count": len(results),
            "results": results
        }, indent=2)

    # =========================================================================
    # PLANETARY QUERIES (Data formatting for AI interpretation)
    # =========================================================================

    def get_planetary_positions(self, kundali_id: str) -> str:
        """Get all planetary positions for a kundali."""
        if kundali_id not in self.kundalis:
            return json.dumps({"status": "error", "message": f"Kundali '{kundali_id}' not found"})

        kundali = self.kundalis[kundali_id]
        if not kundali.chart_data:
            return json.dumps({
                "status": "pending",
                "message": "Chart data not calculated yet. Frontend needs to compute and sync.",
                "kundali_id": kundali_id
            })

        planets = kundali.chart_data.get("planets", {})
        lagna = kundali.chart_data.get("lagna", {})

        formatted = {
            "lagna": {
                "longitude": lagna.get("lon"),
                "rasi": lagna.get("rasi", {}).get("name"),
                "nakshatra": lagna.get("nakshatra", {}).get("name"),
                "pada": lagna.get("nakshatra", {}).get("pada")
            },
            "planets": {}
        }

        for planet, data in planets.items():
            formatted["planets"][planet] = {
                "longitude": round(data.get("lon", 0), 4),
                "rasi": data.get("rasi", {}).get("name"),
                "rasi_degrees": round(data.get("rasi", {}).get("degrees", 0), 2),
                "nakshatra": data.get("nakshatra", {}).get("name"),
                "pada": data.get("nakshatra", {}).get("pada"),
                "is_retrograde": data.get("speed", 0) < 0,
                "is_combust": data.get("isCombust", False),
                "is_vargottama": data.get("isVargottama", False),
                "dignity": data.get("dignity"),
                "jaimini_karaka": data.get("jaiminiKaraka")
            }

        return json.dumps({
            "status": "success",
            "positions": formatted
        }, indent=2)

    def get_planet_details(self, kundali_id: str, planet: str) -> str:
        """Get detailed information about a specific planet."""
        if kundali_id not in self.kundalis:
            return json.dumps({"status": "error", "message": f"Kundali '{kundali_id}' not found"})

        kundali = self.kundalis[kundali_id]
        if not kundali.chart_data:
            return json.dumps({"status": "pending", "message": "Chart data not calculated yet"})

        planets = kundali.chart_data.get("planets", {})
        if planet not in planets:
            return json.dumps({"status": "error", "message": f"Planet '{planet}' not found"})

        data = planets[planet]
        lagna_rasi = kundali.chart_data.get("lagna", {}).get("rasi", {}).get("index", 0)
        planet_rasi = data.get("rasi", {}).get("index", 0)
        house = ((planet_rasi - lagna_rasi) % 12) + 1

        return json.dumps({
            "status": "success",
            "planet": planet,
            "details": {
                "longitude": round(data.get("lon", 0), 4),
                "rasi": data.get("rasi", {}).get("name"),
                "rasi_degrees": round(data.get("rasi", {}).get("degrees", 0), 2),
                "house": house,
                "nakshatra": data.get("nakshatra", {}).get("name"),
                "pada": data.get("nakshatra", {}).get("pada"),
                "speed": round(data.get("speed", 0), 4),
                "is_retrograde": data.get("speed", 0) < 0,
                "is_combust": data.get("isCombust", False),
                "is_vargottama": data.get("isVargottama", False),
                "dignity": data.get("dignity"),
                "jaimini_karaka": data.get("jaiminiKaraka"),
                "declination": round(data.get("dec", 0), 4)
            }
        }, indent=2)

    def get_house_details(self, kundali_id: str, house_number: int) -> str:
        """Get details about a specific house/bhava."""
        if kundali_id not in self.kundalis:
            return json.dumps({"status": "error", "message": f"Kundali '{kundali_id}' not found"})

        kundali = self.kundalis[kundali_id]
        if not kundali.chart_data:
            return json.dumps({"status": "pending", "message": "Chart data not calculated yet"})

        if house_number < 1 or house_number > 12:
            return json.dumps({"status": "error", "message": "House number must be between 1 and 12"})

        houses = kundali.chart_data.get("houses", {})
        house_data = houses.get(str(house_number), {})

        # Find planets in this house
        planets_in_house = []
        planets = kundali.chart_data.get("planets", {})
        lagna_rasi = kundali.chart_data.get("lagna", {}).get("rasi", {}).get("index", 0)

        for planet, data in planets.items():
            planet_rasi = data.get("rasi", {}).get("index", 0)
            planet_house = ((planet_rasi - lagna_rasi) % 12) + 1
            if planet_house == house_number:
                planets_in_house.append(planet)

        # House significances
        house_meanings = {
            1: "Self, personality, physical body, health, appearance",
            2: "Wealth, speech, family, food, right eye, face",
            3: "Siblings, courage, short travels, communication, skills",
            4: "Mother, home, comfort, vehicles, emotions, education",
            5: "Children, intelligence, creativity, romance, past merit",
            6: "Enemies, diseases, debts, service, daily work, maternal uncle",
            7: "Marriage, partnerships, business, public dealings, travel",
            8: "Longevity, transformation, inheritance, hidden matters, occult",
            9: "Father, dharma, luck, higher learning, long journeys, guru",
            10: "Career, fame, authority, karma, father, government",
            11: "Gains, income, friends, elder siblings, fulfillment of desires",
            12: "Losses, expenses, isolation, foreign lands, moksha, sleep"
        }

        return json.dumps({
            "status": "success",
            "house": house_number,
            "sign": house_data.get("sign"),
            "sign_index": house_data.get("signIndex"),
            "planets": planets_in_house,
            "signification": house_meanings.get(house_number, "")
        }, indent=2)

    def get_nakshatra_details(self, kundali_id: str, planet: str = "Moon") -> str:
        """Get nakshatra information for a planet or lagna."""
        if kundali_id not in self.kundalis:
            return json.dumps({"status": "error", "message": f"Kundali '{kundali_id}' not found"})

        kundali = self.kundalis[kundali_id]
        if not kundali.chart_data:
            return json.dumps({"status": "pending", "message": "Chart data not calculated yet"})

        # Get nakshatra data
        if planet.lower() == "lagna":
            nak_data = kundali.chart_data.get("lagna", {}).get("nakshatra", {})
        else:
            planets = kundali.chart_data.get("planets", {})
            if planet not in planets:
                return json.dumps({"status": "error", "message": f"Planet '{planet}' not found"})
            nak_data = planets[planet].get("nakshatra", {})

        # Nakshatra lords (Vimshottari)
        nak_lords = [
            "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
            "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
            "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
        ]

        nak_index = nak_data.get("index", 0)

        return json.dumps({
            "status": "success",
            "planet": planet,
            "nakshatra": {
                "name": nak_data.get("name"),
                "pada": nak_data.get("pada"),
                "lord": nak_lords[nak_index] if nak_index < 27 else "Unknown",
                "index": nak_index
            }
        }, indent=2)

    # =========================================================================
    # DASHA QUERIES
    # =========================================================================

    def get_current_dasha(self, kundali_id: str, dasha_system: str = "vimshottari") -> str:
        """Get currently running dasha periods."""
        if kundali_id not in self.kundalis:
            return json.dumps({"status": "error", "message": f"Kundali '{kundali_id}' not found"})

        kundali = self.kundalis[kundali_id]
        if not kundali.chart_data:
            return json.dumps({"status": "pending", "message": "Chart data not calculated yet"})

        dasha_details = kundali.chart_data.get("dashaDetails", {})
        dasha_data = dasha_details.get(dasha_system)

        if not dasha_data:
            return json.dumps({
                "status": "error",
                "message": f"Dasha system '{dasha_system}' not found",
                "available": list(dasha_details.keys())
            })

        now = datetime.utcnow()
        current_maha = None
        current_antar = None
        current_pratyantar = None

        periods = dasha_data.get("periods", [])
        for maha in periods:
            maha_start = datetime.fromisoformat(maha["start"].replace("Z", "+00:00"))
            maha_end = datetime.fromisoformat(maha["end"].replace("Z", "+00:00"))

            if maha_start <= now <= maha_end:
                current_maha = {
                    "planet": maha["planet"],
                    "start": maha["start"],
                    "end": maha["end"]
                }

                for antar in maha.get("antardasha", []):
                    antar_start = datetime.fromisoformat(antar["start"].replace("Z", "+00:00"))
                    antar_end = datetime.fromisoformat(antar["end"].replace("Z", "+00:00"))

                    if antar_start <= now <= antar_end:
                        current_antar = {
                            "planet": antar["planet"],
                            "start": antar["start"],
                            "end": antar["end"]
                        }

                        for pratyantar in antar.get("pratyantardasha", []):
                            p_start = datetime.fromisoformat(pratyantar["start"].replace("Z", "+00:00"))
                            p_end = datetime.fromisoformat(pratyantar["end"].replace("Z", "+00:00"))

                            if p_start <= now <= p_end:
                                current_pratyantar = {
                                    "planet": pratyantar["planet"],
                                    "start": pratyantar["start"],
                                    "end": pratyantar["end"]
                                }
                                break
                        break
                break

        return json.dumps({
            "status": "success",
            "dasha_system": dasha_system,
            "current": {
                "mahadasha": current_maha,
                "antardasha": current_antar,
                "pratyantardasha": current_pratyantar
            }
        }, indent=2)

    def get_dasha_timeline(
        self, kundali_id: str, years: int = 10, dasha_system: str = "vimshottari"
    ) -> str:
        """Get dasha timeline for specified years from now."""
        if kundali_id not in self.kundalis:
            return json.dumps({"status": "error", "message": f"Kundali '{kundali_id}' not found"})

        kundali = self.kundalis[kundali_id]
        if not kundali.chart_data:
            return json.dumps({"status": "pending", "message": "Chart data not calculated yet"})

        dasha_details = kundali.chart_data.get("dashaDetails", {})
        dasha_data = dasha_details.get(dasha_system)

        if not dasha_data:
            return json.dumps({"status": "error", "message": f"Dasha system '{dasha_system}' not found"})

        now = datetime.utcnow()
        end_date = datetime(now.year + years, now.month, now.day)

        timeline = []
        periods = dasha_data.get("periods", [])

        for maha in periods:
            maha_start = datetime.fromisoformat(maha["start"].replace("Z", "+00:00"))
            maha_end = datetime.fromisoformat(maha["end"].replace("Z", "+00:00"))

            if maha_end < now:
                continue
            if maha_start > end_date:
                break

            maha_entry = {
                "type": "mahadasha",
                "planet": maha["planet"],
                "start": maha["start"],
                "end": maha["end"],
                "antardasha": []
            }

            for antar in maha.get("antardasha", []):
                antar_start = datetime.fromisoformat(antar["start"].replace("Z", "+00:00"))
                antar_end = datetime.fromisoformat(antar["end"].replace("Z", "+00:00"))

                if antar_end < now:
                    continue
                if antar_start > end_date:
                    break

                maha_entry["antardasha"].append({
                    "planet": antar["planet"],
                    "start": antar["start"],
                    "end": antar["end"]
                })

            timeline.append(maha_entry)

        return json.dumps({
            "status": "success",
            "dasha_system": dasha_system,
            "years": years,
            "timeline": timeline
        }, indent=2)

    def get_dasha_analysis(
        self, kundali_id: str, planet: str, dasha_system: str = "vimshottari"
    ) -> str:
        """Get analysis hints for a specific dasha planet."""
        if kundali_id not in self.kundalis:
            return json.dumps({"status": "error", "message": f"Kundali '{kundali_id}' not found"})

        kundali = self.kundalis[kundali_id]
        if not kundali.chart_data:
            return json.dumps({"status": "pending", "message": "Chart data not calculated yet"})

        planets = kundali.chart_data.get("planets", {})
        if planet not in planets:
            return json.dumps({"status": "error", "message": f"Planet '{planet}' not found"})

        planet_data = planets[planet]
        lagna_rasi = kundali.chart_data.get("lagna", {}).get("rasi", {}).get("index", 0)
        planet_rasi = planet_data.get("rasi", {}).get("index", 0)
        house = ((planet_rasi - lagna_rasi) % 12) + 1

        # House lordships (simplified)
        house_lords = kundali.chart_data.get("houses", {})
        owned_houses = []
        for h in range(1, 13):
            h_data = house_lords.get(str(h), {})
            # Check if this planet is lord of this house
            # This would need sign->lord mapping which we have in frontend

        return json.dumps({
            "status": "success",
            "planet": planet,
            "dasha_analysis": {
                "natal_house": house,
                "rasi": planet_data.get("rasi", {}).get("name"),
                "nakshatra": planet_data.get("nakshatra", {}).get("name"),
                "dignity": planet_data.get("dignity"),
                "is_retrograde": planet_data.get("speed", 0) < 0,
                "is_combust": planet_data.get("isCombust", False),
                "jaimini_karaka": planet_data.get("jaiminiKaraka"),
                "interpretation_hints": self._get_planet_hints(planet, house, planet_data)
            }
        }, indent=2)

    def _get_planet_hints(self, planet: str, house: int, data: Dict) -> List[str]:
        """Generate interpretation hints for a planet."""
        hints = []

        dignity = data.get("dignity", "neutral")
        if dignity == "exalted":
            hints.append(f"{planet} is exalted - excellent results expected during its periods")
        elif dignity == "debilitated":
            hints.append(f"{planet} is debilitated - may face challenges during its periods")
        elif dignity == "own":
            hints.append(f"{planet} is in own sign - comfortable and strong")
        elif dignity == "moolatrikona":
            hints.append(f"{planet} is in moolatrikona - very strong placement")

        if data.get("isCombust"):
            hints.append(f"{planet} is combust - weakened by proximity to Sun")

        if data.get("isVargottama"):
            hints.append(f"{planet} is Vargottama - same sign in D1 and D9, extra strength")

        if data.get("speed", 0) < 0:
            hints.append(f"{planet} is retrograde - inner focus, revisiting past karma")

        karaka = data.get("jaiminiKaraka")
        if karaka:
            hints.append(f"{planet} is {karaka} (Jaimini Karaka) - significant role in life events")

        return hints

    # =========================================================================
    # YOGA QUERIES
    # =========================================================================

    def get_yogas(self, kundali_id: str, category: str = None) -> str:
        """Get all yogas present in the chart, optionally filtered by category."""
        if kundali_id not in self.kundalis:
            return json.dumps({"status": "error", "message": f"Kundali '{kundali_id}' not found"})

        kundali = self.kundalis[kundali_id]
        if not kundali.chart_data:
            return json.dumps({"status": "pending", "message": "Chart data not calculated yet"})

        # Yogas would be calculated by frontend and stored in chart_data
        yogas = kundali.chart_data.get("yogas", [])

        if category:
            yogas = [y for y in yogas if y.get("category", "").lower() == category.lower()]

        return json.dumps({
            "status": "success",
            "count": len(yogas),
            "yogas": yogas
        }, indent=2)

    def get_yoga_details(self, kundali_id: str, yoga_name: str) -> str:
        """Get detailed interpretation of a specific yoga."""
        if kundali_id not in self.kundalis:
            return json.dumps({"status": "error", "message": f"Kundali '{kundali_id}' not found"})

        kundali = self.kundalis[kundali_id]
        if not kundali.chart_data:
            return json.dumps({"status": "pending", "message": "Chart data not calculated yet"})

        yogas = kundali.chart_data.get("yogas", [])
        yoga = next((y for y in yogas if y.get("name", "").lower() == yoga_name.lower()), None)

        if not yoga:
            return json.dumps({
                "status": "error",
                "message": f"Yoga '{yoga_name}' not found in this chart"
            })

        return json.dumps({
            "status": "success",
            "yoga": yoga
        }, indent=2)

    def check_specific_yoga(self, kundali_id: str, yoga_name: str) -> str:
        """Check if a specific yoga is present in the chart."""
        if kundali_id not in self.kundalis:
            return json.dumps({"status": "error", "message": f"Kundali '{kundali_id}' not found"})

        kundali = self.kundalis[kundali_id]
        if not kundali.chart_data:
            return json.dumps({"status": "pending", "message": "Chart data not calculated yet"})

        yogas = kundali.chart_data.get("yogas", [])
        yoga = next((y for y in yogas if y.get("name", "").lower() == yoga_name.lower()), None)

        return json.dumps({
            "status": "success",
            "yoga": yoga_name,
            "present": yoga is not None,
            "details": yoga if yoga else None
        }, indent=2)

    # =========================================================================
    # DIVISIONAL CHARTS
    # =========================================================================

    def get_divisional_chart(self, kundali_id: str, varga: str = "D9") -> str:
        """Get a specific divisional chart."""
        if kundali_id not in self.kundalis:
            return json.dumps({"status": "error", "message": f"Kundali '{kundali_id}' not found"})

        kundali = self.kundalis[kundali_id]
        if not kundali.chart_data:
            return json.dumps({"status": "pending", "message": "Chart data not calculated yet"})

        divisionals = kundali.chart_data.get("divisionals", {})
        chart = divisionals.get(varga)

        if not chart:
            return json.dumps({
                "status": "error",
                "message": f"Varga '{varga}' not found",
                "available": list(divisionals.keys())
            })

        return json.dumps({
            "status": "success",
            "varga": varga,
            "chart": chart
        }, indent=2)

    def get_varga_positions(self, kundali_id: str, vargas: List[str] = None) -> str:
        """Get planet positions in specified vargas."""
        if kundali_id not in self.kundalis:
            return json.dumps({"status": "error", "message": f"Kundali '{kundali_id}' not found"})

        kundali = self.kundalis[kundali_id]
        if not kundali.chart_data:
            return json.dumps({"status": "pending", "message": "Chart data not calculated yet"})

        divisionals = kundali.chart_data.get("divisionals", {})

        if vargas is None:
            vargas = ["D1", "D9", "D10", "D7"]  # Common vargas

        result = {}
        for varga in vargas:
            chart = divisionals.get(varga)
            if chart:
                result[varga] = {}
                for planet, data in chart.get("planets", {}).items():
                    result[varga][planet] = data.get("rasi", {}).get("name")

        return json.dumps({
            "status": "success",
            "varga_positions": result
        }, indent=2)

    # =========================================================================
    # COMPATIBILITY
    # =========================================================================

    def check_compatibility(self, kundali_id_1: str, kundali_id_2: str) -> str:
        """Check Ashtakoot compatibility between two charts."""
        if kundali_id_1 not in self.kundalis:
            return json.dumps({"status": "error", "message": f"Kundali '{kundali_id_1}' not found"})
        if kundali_id_2 not in self.kundalis:
            return json.dumps({"status": "error", "message": f"Kundali '{kundali_id_2}' not found"})

        k1 = self.kundalis[kundali_id_1]
        k2 = self.kundalis[kundali_id_2]

        if not k1.chart_data or not k2.chart_data:
            return json.dumps({"status": "pending", "message": "Chart data not calculated for one or both charts"})

        # Compatibility would be calculated by frontend
        compatibility = k1.chart_data.get("compatibility", {}).get(kundali_id_2)

        if not compatibility:
            return json.dumps({
                "status": "needs_calculation",
                "message": "Compatibility not yet calculated. Frontend needs to compute Ashtakoot.",
                "kundali_1": kundali_id_1,
                "kundali_2": kundali_id_2
            })

        return json.dumps({
            "status": "success",
            "compatibility": compatibility
        }, indent=2)

    def get_manglik_status(self, kundali_id: str) -> str:
        """Check Manglik/Kuja dosha status."""
        if kundali_id not in self.kundalis:
            return json.dumps({"status": "error", "message": f"Kundali '{kundali_id}' not found"})

        kundali = self.kundalis[kundali_id]
        if not kundali.chart_data:
            return json.dumps({"status": "pending", "message": "Chart data not calculated yet"})

        # Manglik status would be in chart_data
        manglik = kundali.chart_data.get("manglik", {})

        return json.dumps({
            "status": "success",
            "manglik": manglik
        }, indent=2)

    # =========================================================================
    # PANCHANG
    # =========================================================================

    def get_panchang(self, date: str, latitude: float, longitude: float, timezone: str) -> str:
        """
        Get panchang details for a specific date and location.
        Note: Actual calculation done on frontend, this is a request format.
        """
        return json.dumps({
            "status": "calculation_request",
            "type": "panchang",
            "params": {
                "date": date,
                "latitude": latitude,
                "longitude": longitude,
                "timezone": timezone
            },
            "message": "Frontend should calculate panchang with these parameters"
        }, indent=2)

    def get_muhurta(self, activity: str, date: str, latitude: float, longitude: float) -> str:
        """Find auspicious muhurta for specific activities."""
        return json.dumps({
            "status": "calculation_request",
            "type": "muhurta",
            "params": {
                "activity": activity,
                "date": date,
                "latitude": latitude,
                "longitude": longitude
            },
            "message": "Frontend should calculate muhurta with these parameters"
        }, indent=2)

    # =========================================================================
    # ANALYSIS
    # =========================================================================

    def get_strength_analysis(self, kundali_id: str) -> str:
        """Get Shadbala planetary strength analysis."""
        if kundali_id not in self.kundalis:
            return json.dumps({"status": "error", "message": f"Kundali '{kundali_id}' not found"})

        kundali = self.kundalis[kundali_id]
        if not kundali.chart_data:
            return json.dumps({"status": "pending", "message": "Chart data not calculated yet"})

        shadbala = kundali.chart_data.get("shadbala", {})

        return json.dumps({
            "status": "success",
            "shadbala": shadbala
        }, indent=2)

    def get_ashtakavarga(self, kundali_id: str, planet: str = None) -> str:
        """Get Ashtakavarga point analysis."""
        if kundali_id not in self.kundalis:
            return json.dumps({"status": "error", "message": f"Kundali '{kundali_id}' not found"})

        kundali = self.kundalis[kundali_id]
        if not kundali.chart_data:
            return json.dumps({"status": "pending", "message": "Chart data not calculated yet"})

        ashtakavarga = kundali.chart_data.get("ashtakavarga", {})

        if planet:
            planet_av = ashtakavarga.get(planet)
            return json.dumps({
                "status": "success",
                "planet": planet,
                "ashtakavarga": planet_av
            }, indent=2)

        return json.dumps({
            "status": "success",
            "ashtakavarga": ashtakavarga
        }, indent=2)

    def get_chart_summary(self, kundali_id: str) -> str:
        """Get AI-friendly summary of the chart."""
        if kundali_id not in self.kundalis:
            return json.dumps({"status": "error", "message": f"Kundali '{kundali_id}' not found"})

        kundali = self.kundalis[kundali_id]
        bd = kundali.birth_details if isinstance(kundali.birth_details, dict) else kundali.birth_details.to_dict()

        if not kundali.chart_data:
            return json.dumps({
                "status": "partial",
                "birth_details": bd,
                "message": "Chart data not yet calculated"
            })

        planets = kundali.chart_data.get("planets", {})
        lagna = kundali.chart_data.get("lagna", {})

        # Build summary
        summary = {
            "name": bd.get("name"),
            "gender": bd.get("gender"),
            "birth": f"{bd.get('date')} at {bd.get('time')} in {bd.get('place')}",
            "lagna": {
                "sign": lagna.get("rasi", {}).get("name"),
                "nakshatra": lagna.get("nakshatra", {}).get("name")
            },
            "moon": {
                "sign": planets.get("Moon", {}).get("rasi", {}).get("name"),
                "nakshatra": planets.get("Moon", {}).get("nakshatra", {}).get("name")
            },
            "sun": {
                "sign": planets.get("Sun", {}).get("rasi", {}).get("name")
            },
            "key_placements": [],
            "yoga_count": len(kundali.chart_data.get("yogas", []))
        }

        # Identify key placements
        for planet, data in planets.items():
            dignity = data.get("dignity")
            if dignity in ["exalted", "debilitated"]:
                summary["key_placements"].append(f"{planet} is {dignity} in {data.get('rasi', {}).get('name')}")
            if data.get("isVargottama"):
                summary["key_placements"].append(f"{planet} is Vargottama")

        return json.dumps({
            "status": "success",
            "summary": summary
        }, indent=2)

    # =========================================================================
    # SETTINGS
    # =========================================================================

    def set_ayanamsa(self, system: str) -> str:
        """Set the ayanamsa system for calculations."""
        valid_systems = [a.value for a in AyanamsaSystem]

        if system not in valid_systems:
            return json.dumps({
                "status": "error",
                "message": f"Invalid ayanamsa system '{system}'",
                "available": valid_systems
            })

        self.default_ayanamsa = system

        return json.dumps({
            "status": "success",
            "message": f"Ayanamsa set to {system}",
            "current": self.default_ayanamsa
        })

    def get_available_ayanamsas(self) -> str:
        """List available ayanamsa systems."""
        systems = [
            {"name": "Lahiri", "description": "Chitra Paksha - Government of India standard"},
            {"name": "Raman", "description": "B.V. Raman's system based on Surya Siddhanta"},
            {"name": "Krishnamurti", "description": "KP system - Star Spica at 179° Virgo"},
            {"name": "FaganBradley", "description": "Fagan-Bradley - Western sidereal"},
            {"name": "Yukteshwar", "description": "Sri Yukteshwar Giri's calculations"},
            {"name": "TrueChitra", "description": "Spica at exactly 180°"},
            {"name": "PushyaPaksha", "description": "Pushya star reference - precise timing"}
        ]

        return json.dumps({
            "status": "success",
            "current": self.default_ayanamsa,
            "systems": systems
        }, indent=2)

    # =========================================================================
    # TRANSIT ANALYSIS
    # =========================================================================

    def get_current_transits(self, kundali_id: str) -> str:
        """Get current planetary transits over natal chart."""
        if kundali_id not in self.kundalis:
            return json.dumps({"status": "error", "message": f"Kundali '{kundali_id}' not found"})

        return json.dumps({
            "status": "calculation_request",
            "type": "transits",
            "kundali_id": kundali_id,
            "message": "Frontend should calculate current transits and overlay on natal chart"
        }, indent=2)

    def get_transit_analysis(self, kundali_id: str, planet: str) -> str:
        """Analyze impact of a specific transit on the chart."""
        if kundali_id not in self.kundalis:
            return json.dumps({"status": "error", "message": f"Kundali '{kundali_id}' not found"})

        return json.dumps({
            "status": "calculation_request",
            "type": "transit_analysis",
            "kundali_id": kundali_id,
            "planet": planet,
            "message": f"Frontend should analyze {planet} transit impact on this chart"
        }, indent=2)

    # =========================================================================
    # BULK DATA SYNC (For localStorage sync)
    # =========================================================================

    def sync_kundalis(self, kundalis_data: List[Dict[str, Any]]) -> str:
        """Sync kundalis from localStorage."""
        synced = 0
        for k_data in kundalis_data:
            k_id = k_data.get("id")
            if not k_id:
                continue

            bd = k_data.get("birth_details", {})
            birth_details = BirthDetails(
                name=bd.get("name", "Unknown"),
                date=bd.get("date", ""),
                time=bd.get("time", "00:00"),
                place=bd.get("place", ""),
                latitude=bd.get("latitude", 0),
                longitude=bd.get("longitude", 0),
                timezone=bd.get("timezone", "UTC"),
                gender=bd.get("gender", "male")
            )

            kundali = Kundali(
                id=k_id,
                birth_details=birth_details,
                created_at=k_data.get("created_at", datetime.utcnow().isoformat() + "Z"),
                updated_at=k_data.get("updated_at", datetime.utcnow().isoformat() + "Z"),
                ayanamsa_system=k_data.get("ayanamsa_system", self.default_ayanamsa),
                chart_style=k_data.get("chart_style", self.default_chart_style),
                chart_data=k_data.get("chart_data"),
                notes=k_data.get("notes", ""),
                tags=k_data.get("tags", [])
            )

            self.kundalis[k_id] = kundali
            synced += 1

        return json.dumps({
            "status": "success",
            "synced": synced,
            "total": len(self.kundalis)
        })

    def export_kundalis(self) -> str:
        """Export all kundalis for localStorage persistence."""
        export_data = [k.to_dict() for k in self.kundalis.values()]

        return json.dumps({
            "status": "success",
            "count": len(export_data),
            "kundalis": export_data
        }, indent=2)
