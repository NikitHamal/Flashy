"""
Vedic Astrology Agent Module

This module provides the agent logic for parsing astrology tool calls
from Gemini responses and executing them on kundali data.

The agent embodies a blunt, truth-speaking Vedic astrologer persona
that delivers unfiltered interpretations with divine clarity.
"""

import re
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from .astro_tools import AstroTools
from .astro_prompts import (
    get_system_prompt,
    get_kundali_creation_prompt,
    get_no_chart_prompt,
    get_uncertain_time_prompt,
    PLANET_SIGNIFICATIONS,
    NAKSHATRA_LORDS,
    NAKSHATRA_NAMES,
    RASI_NAMES,
    RASI_LORDS
)


# Tool result template for formatted responses
ASTRO_TOOL_RESULT_TEMPLATE = """Tool: {tool_name}
Result: {output}

Continue with your analysis based on this data."""


class AstroAgent:
    """
    Manages the Vedic astrology agent loop: Inquire -> Analyze -> Advise.
    Parses tool calls from AI responses and executes astrology operations.

    Maintains session context for multi-turn chart analysis and
    remembers active kundalis for seamless conversation flow.
    """

    def __init__(self, ayanamsa: str = "Lahiri"):
        self.tools = AstroTools()
        self.tools.default_ayanamsa = ayanamsa
        self.conversation_history: List[Dict[str, Any]] = []
        self.max_iterations = 15  # Limit tool call loops
        self.session_id: Optional[str] = None

        # Active context for multi-turn conversations
        self.active_kundali_id: Optional[str] = None
        self.active_kundali_name: Optional[str] = None
        self.pending_birth_details: Dict[str, Any] = {}

    def get_system_prompt(self) -> str:
        """Get the system prompt with current context."""
        return get_system_prompt(
            kundali_count=len(self.tools.kundalis),
            ayanamsa_system=self.tools.default_ayanamsa
        )

    def get_kundali_count(self) -> int:
        """Get number of stored kundalis."""
        return len(self.tools.kundalis)

    def get_all_kundalis(self) -> List[Dict[str, Any]]:
        """Get list of all kundalis for frontend display."""
        result = json.loads(self.tools.list_kundalis())
        if result.get("status") == "success":
            return result.get("kundalis", [])
        return []

    def set_active_kundali(self, kundali_id: str) -> bool:
        """Set the active kundali for analysis context."""
        result = json.loads(self.tools.get_kundali(kundali_id))
        if result.get("status") == "success":
            kundali = result.get("kundali", {})
            self.active_kundali_id = kundali_id
            bd = kundali.get("birth_details", {})
            self.active_kundali_name = bd.get("name", "Unknown")
            return True
        return False

    def clear_active_kundali(self):
        """Clear active kundali context."""
        self.active_kundali_id = None
        self.active_kundali_name = None

    def sync_from_storage(self, kundalis_data: List[Dict[str, Any]]) -> str:
        """Sync kundalis from frontend localStorage."""
        return self.tools.sync_kundalis(kundalis_data)

    def export_to_storage(self) -> str:
        """Export all kundalis for frontend persistence."""
        return self.tools.export_kundalis()

    def parse_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse an astrology tool call from the model's output.

        Recognizes:
        1. ```json code blocks with action key
        2. Inline JSON objects with action key
        """
        if not text:
            return None

        # Get list of valid tool names
        valid_tools = {t['name'] for t in self.tools.get_available_tools()}

        # 1. Primary: Markdown Code Blocks
        if '```json' in text:
            blocks = text.split('```json')
            for block in blocks[1:]:
                if '```' not in block:
                    continue
                content = block.split('```')[0].strip()
                try:
                    data = json.loads(content)
                    result = self._validate_tool_call(data, valid_tools)
                    if result:
                        result["raw_match"] = f"```json\n{content}\n```"
                        return result
                except json.JSONDecodeError:
                    continue

        # 2. Secondary: Inline JSON with "action" key
        action_pattern = r'\{\s*"action"\s*:\s*"([^"]+)"'
        matches = list(re.finditer(action_pattern, text))

        for match in matches:
            tool_name = match.group(1)
            if tool_name not in valid_tools:
                continue

            # Find complete JSON object
            start_idx = match.start()
            brace_count = 0
            end_idx = start_idx

            for i, char in enumerate(text[start_idx:], start=start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break

            if end_idx > start_idx:
                potential_json = text[start_idx:end_idx]
                try:
                    data = json.loads(potential_json)
                    result = self._validate_tool_call(data, valid_tools)
                    if result:
                        result["raw_match"] = potential_json
                        return result
                except json.JSONDecodeError:
                    continue

        return None

    def _validate_tool_call(
        self, data: Dict[str, Any], valid_tools: set
    ) -> Optional[Dict[str, Any]]:
        """Validate that parsed JSON is a valid astrology tool call."""
        if not isinstance(data, dict):
            return None

        tool_name = data.get("action") or data.get("tool") or data.get("name")
        if not tool_name or tool_name not in valid_tools:
            return None

        args = data.get("args") or data.get("arguments") or {}

        return {
            "name": tool_name,
            "args": args
        }

    async def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Execute an astrology tool and return formatted result."""
        # If kundali_id not specified but we have active context, use it
        if "kundali_id" not in args and self.active_kundali_id:
            if tool_name in [
                "get_kundali", "get_planetary_positions", "get_planet_details",
                "get_house_details", "get_nakshatra_details", "get_current_dasha",
                "get_dasha_timeline", "get_dasha_analysis", "get_yogas",
                "get_yoga_details", "check_specific_yoga", "get_divisional_chart",
                "get_varga_positions", "get_manglik_status", "get_current_transits",
                "get_transit_analysis", "get_strength_analysis", "get_ashtakavarga",
                "get_chart_summary"
            ]:
                args["kundali_id"] = self.active_kundali_id

        result = await self.tools.execute(tool_name, **args)

        # If we just created a kundali, set it as active
        if tool_name == "create_kundali":
            try:
                result_data = json.loads(result)
                if result_data.get("status") == "success":
                    kundali = result_data.get("kundali", {})
                    self.active_kundali_id = kundali.get("id")
                    bd = kundali.get("birth_details", {})
                    self.active_kundali_name = bd.get("name")
            except json.JSONDecodeError:
                pass

        return ASTRO_TOOL_RESULT_TEMPLATE.format(
            tool_name=tool_name,
            output=result
        )

    def format_for_streaming(
        self, text: str, tool_call: Dict = None,
        tool_result: str = None, kundali_update: bool = False
    ) -> Dict[str, Any]:
        """Format response for streaming to frontend."""
        response = {
            "text": text,
            "tool_call": tool_call,
            "tool_result": tool_result,
            "is_complete": tool_call is None
        }

        if kundali_update:
            response["kundalis"] = self.get_all_kundalis()
            response["active_kundali"] = {
                "id": self.active_kundali_id,
                "name": self.active_kundali_name
            }

        return response

    def get_context_summary(self) -> str:
        """Get a brief summary of current context."""
        parts = []

        if self.active_kundali_id:
            parts.append(f"Analyzing: {self.active_kundali_name}")

        kundali_count = len(self.tools.kundalis)
        if kundali_count > 0:
            parts.append(f"Stored charts: {kundali_count}")

        parts.append(f"Ayanamsa: {self.tools.default_ayanamsa}")

        return " | ".join(parts) if parts else "No active context"

    def process_multiple_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """
        Process multiple tool calls from a single response.
        Returns list of tool call objects.
        """
        tool_calls = []
        valid_tools = {t['name'] for t in self.tools.get_available_tools()}

        # Find all ```json blocks
        if '```json' in text:
            blocks = text.split('```json')
            for block in blocks[1:]:
                if '```' not in block:
                    continue
                content = block.split('```')[0].strip()
                try:
                    data = json.loads(content)
                    result = self._validate_tool_call(data, valid_tools)
                    if result:
                        result["raw_match"] = f"```json\n{content}\n```"
                        tool_calls.append(result)
                except json.JSONDecodeError:
                    continue

        return tool_calls

    async def execute_multiple_tools(
        self, tool_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute multiple tool calls and return results."""
        results = []
        for tool_call in tool_calls:
            result = await self.execute_tool(tool_call["name"], tool_call["args"])
            results.append({
                "tool_call": tool_call,
                "result": result
            })
        return results

    def clean_response_text(self, text: str, raw_matches: List[str] = None) -> str:
        """Clean response text by removing tool call JSON."""
        if not text:
            return ""

        cleaned = text

        # Remove specific matches
        if raw_matches:
            for match in raw_matches:
                cleaned = cleaned.replace(match, "")

        # Remove any remaining ```json blocks that look like tool calls
        json_block_pattern = r'```json\s*\{[^`]*?"(?:action|tool|name)"\s*:[^`]*?\}\s*```'
        cleaned = re.sub(json_block_pattern, '', cleaned, flags=re.DOTALL)

        return cleaned.strip()

    def separate_thinking(self, text: str) -> tuple:
        """
        Separate thinking/reasoning from actual response text.
        Returns (thinking_content, clean_text)
        """
        if not text:
            return None, ""

        thinking_content = None
        clean_text = text

        # Pattern: <think>...</think>
        think_pattern = r'<think>(.*?)</think>'
        matches = re.findall(think_pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            thinking_content = '\n'.join(matches)
            clean_text = re.sub(
                think_pattern, '', clean_text,
                flags=re.DOTALL | re.IGNORECASE
            ).strip()

        # Pattern: [Thinking]...[/Thinking]
        bracket_pattern = r'\[Thinking\](.*?)\[/Thinking\]'
        bracket_matches = re.findall(
            bracket_pattern, clean_text,
            re.DOTALL | re.IGNORECASE
        )
        if bracket_matches:
            if thinking_content:
                thinking_content += '\n' + '\n'.join(bracket_matches)
            else:
                thinking_content = '\n'.join(bracket_matches)
            clean_text = re.sub(
                bracket_pattern, '', clean_text,
                flags=re.DOTALL | re.IGNORECASE
            ).strip()

        return thinking_content, clean_text

    # =========================================================================
    # BIRTH DETAIL EXTRACTION HELPERS
    # =========================================================================

    def extract_birth_details_from_message(
        self, message: str
    ) -> Dict[str, Any]:
        """
        Attempt to extract birth details from natural language message.
        Returns dict with whatever details could be extracted.
        """
        details = {}

        # Name extraction patterns
        name_patterns = [
            r"(?:my name is|i am|i'm|name[:\s]+)([A-Z][a-z]+ ?[A-Z]?[a-z]*)",
            r"(?:for|about|chart of|kundali (?:for|of))[\s:]+([A-Z][a-z]+ ?[A-Z]?[a-z]*)",
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                details["name"] = match.group(1).strip()
                break

        # Date extraction patterns (various formats)
        date_patterns = [
            # ISO format
            (r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", "ymd"),
            # Common formats
            (r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", "dmy"),
            (r"(\d{1,2})\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{4})", "dMy"),
            (r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2}),?\s+(\d{4})", "Mdy"),
        ]
        for pattern, format_type in date_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                try:
                    if format_type == "ymd":
                        details["date"] = f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
                    elif format_type == "dmy":
                        details["date"] = f"{match.group(3)}-{match.group(2).zfill(2)}-{match.group(1).zfill(2)}"
                    break
                except (ValueError, IndexError):
                    continue

        # Time extraction
        time_patterns = [
            r"(\d{1,2}):(\d{2})\s*(?:am|pm)?",
            r"(\d{1,2})\s*(?:am|pm)",
            r"(\d{1,2}):(\d{2}):(\d{2})",
        ]
        for pattern in time_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                groups = match.groups()
                hour = int(groups[0])
                minute = int(groups[1]) if len(groups) > 1 and groups[1] else 0

                # Check for AM/PM
                if "pm" in match.group().lower() and hour < 12:
                    hour += 12
                elif "am" in match.group().lower() and hour == 12:
                    hour = 0

                details["time"] = f"{hour:02d}:{minute:02d}"
                break

        # Place extraction (basic - real implementation would use geocoding)
        place_patterns = [
            r"(?:born (?:in|at)|from|place[:\s]+|city[:\s]+|location[:\s]+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*(?:India|USA|UK|Nepal|Sri Lanka|Bangladesh)",
        ]
        for pattern in place_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                details["place"] = match.group(1).strip()
                break

        # Gender extraction
        gender_patterns = [
            r"\b(male|female)\b",
            r"\b(man|woman|boy|girl)\b",
            r"\bgender[:\s]+(male|female|other)\b",
        ]
        for pattern in gender_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                gender_text = match.group(1).lower()
                if gender_text in ["male", "man", "boy"]:
                    details["gender"] = "male"
                elif gender_text in ["female", "woman", "girl"]:
                    details["gender"] = "female"
                else:
                    details["gender"] = "other"
                break

        return details

    def get_missing_birth_details(self, details: Dict[str, Any]) -> List[str]:
        """Get list of required birth details that are missing."""
        required = ["name", "date", "time", "place"]
        return [field for field in required if field not in details or not details[field]]

    def format_birth_details_request(
        self, missing: List[str], partial: Dict[str, Any] = None
    ) -> str:
        """Format a request for missing birth details in the persona's voice."""
        response_parts = []

        if partial:
            gathered = [f"**{k.title()}**: {v}" for k, v in partial.items()]
            response_parts.append(f"I have gathered: {', '.join(gathered)}")

        field_descriptions = {
            "name": "the seeker's **name** (or a name to identify this chart)",
            "date": "the **birth date** (YYYY-MM-DD format works best)",
            "time": "the **birth time** (HH:MM in 24-hour format - precision is power)",
            "place": "the **birth place** (city and country for coordinates)",
            "gender": "the **gender** (male/female/other - for certain classical interpretations)"
        }

        if missing:
            missing_desc = [field_descriptions.get(m, m) for m in missing]
            response_parts.append(f"\nI still need: {', '.join(missing_desc)}")

        return "\n".join(response_parts)

    # =========================================================================
    # INTERPRETATION HELPERS
    # =========================================================================

    def get_planet_info(self, planet: str) -> Dict[str, Any]:
        """Get signification data for a planet."""
        return PLANET_SIGNIFICATIONS.get(planet, {})

    def get_nakshatra_lord(self, nakshatra_index: int) -> str:
        """Get the lord of a nakshatra by index (0-26)."""
        if 0 <= nakshatra_index < 27:
            return NAKSHATRA_LORDS[nakshatra_index]
        return "Unknown"

    def get_nakshatra_name(self, nakshatra_index: int) -> str:
        """Get nakshatra name by index."""
        if 0 <= nakshatra_index < 27:
            return NAKSHATRA_NAMES[nakshatra_index]
        return "Unknown"

    def get_rasi_name(self, rasi_index: int) -> str:
        """Get rasi name by index (0-11)."""
        if 0 <= rasi_index < 12:
            return RASI_NAMES[rasi_index]
        return "Unknown"

    def get_rasi_lord(self, rasi_index: int) -> str:
        """Get lord of a rasi by index."""
        if 0 <= rasi_index < 12:
            return RASI_LORDS[rasi_index]
        return "Unknown"

    def format_degrees(self, longitude: float) -> str:
        """Format longitude as degrees/minutes/seconds string."""
        degrees = int(longitude % 30)
        remaining = (longitude % 30 - degrees) * 60
        minutes = int(remaining)
        seconds = int((remaining - minutes) * 60)
        return f"{degrees}° {minutes}' {seconds}\""

    def get_dignity(self, planet: str, rasi_index: int) -> str:
        """Determine planetary dignity based on rasi placement."""
        planet_info = PLANET_SIGNIFICATIONS.get(planet, {})

        exalted = planet_info.get("exalted", "")
        debilitated = planet_info.get("debilitated", "")
        own_signs = planet_info.get("own_signs", [])

        rasi_name = RASI_NAMES[rasi_index].split(" ")[0] if rasi_index < 12 else ""

        if rasi_name in exalted:
            return "Exalted"
        if rasi_name in debilitated:
            return "Debilitated"
        if rasi_name in own_signs:
            return "Own Sign"

        # Check friendship
        rasi_lord = RASI_LORDS[rasi_index] if rasi_index < 12 else ""
        friends = planet_info.get("friends", [])
        enemies = planet_info.get("enemies", [])

        if rasi_lord in friends:
            return "Friend's Sign"
        if rasi_lord in enemies:
            return "Enemy's Sign"

        return "Neutral"

    # =========================================================================
    # DASHA HELPERS
    # =========================================================================

    def calculate_dasha_balance(
        self, moon_longitude: float, birth_date: datetime
    ) -> Dict[str, Any]:
        """
        Calculate initial dasha balance at birth.
        Returns the starting dasha and balance remaining.
        """
        # Nakshatra span is 13°20' = 13.3333°
        nakshatra_span = 360 / 27

        # Get nakshatra index
        nak_index = int(moon_longitude / nakshatra_span)
        nak_lord = NAKSHATRA_LORDS[nak_index]

        # Position within nakshatra (0 to 1)
        pos_in_nak = (moon_longitude % nakshatra_span) / nakshatra_span

        # Vimshottari dasha periods in years
        dasha_periods = {
            "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
            "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
        }

        # Balance remaining = (1 - position) * full period
        full_period = dasha_periods.get(nak_lord, 0)
        balance_years = (1 - pos_in_nak) * full_period
        balance_days = balance_years * 365.25

        return {
            "starting_dasha": nak_lord,
            "balance_years": round(balance_years, 2),
            "balance_days": int(balance_days),
            "nakshatra": NAKSHATRA_NAMES[nak_index],
            "nakshatra_lord": nak_lord
        }

    # =========================================================================
    # YOGA QUICK CHECKS
    # =========================================================================

    def check_basic_yogas(self, chart_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Perform quick checks for major yogas.
        Returns list of detected yogas with names and descriptions.
        """
        yogas = []
        planets = chart_data.get("planets", {})
        lagna = chart_data.get("lagna", {})

        if not planets or not lagna:
            return yogas

        lagna_index = lagna.get("rasi", {}).get("index", 0)

        # Helper to get house position
        def get_house(planet_name: str) -> int:
            p = planets.get(planet_name, {})
            p_index = p.get("rasi", {}).get("index", 0)
            return ((p_index - lagna_index) % 12) + 1

        # Kemadruma Yoga - Moon with no planets in 2nd or 12th from it
        moon_index = planets.get("Moon", {}).get("rasi", {}).get("index", 0)
        planets_around_moon = False
        for p_name, p_data in planets.items():
            if p_name == "Moon":
                continue
            p_index = p_data.get("rasi", {}).get("index", 0)
            if (p_index - moon_index) % 12 in [1, 11]:  # 2nd or 12th from Moon
                planets_around_moon = True
                break
        if not planets_around_moon:
            yogas.append({
                "name": "Kemadruma Yoga",
                "type": "challenging",
                "description": "Moon isolated - may face struggles and need to be self-reliant"
            })

        # Gajakesari Yoga - Jupiter in Kendra from Moon
        jup_index = planets.get("Jupiter", {}).get("rasi", {}).get("index", 0)
        jup_from_moon = (jup_index - moon_index) % 12
        if jup_from_moon in [0, 3, 6, 9]:  # Kendra positions
            yogas.append({
                "name": "Gajakesari Yoga",
                "type": "auspicious",
                "description": "Jupiter in Kendra from Moon - wisdom, reputation, and protection"
            })

        # Check for Mahapurusha Yogas
        mahapurusha_planets = {
            "Mars": (["Aries", "Scorpio", "Capricorn"], "Ruchaka"),
            "Mercury": (["Gemini", "Virgo"], "Bhadra"),
            "Jupiter": (["Sagittarius", "Pisces", "Cancer"], "Hamsa"),
            "Venus": (["Taurus", "Libra", "Pisces"], "Malavya"),
            "Saturn": (["Capricorn", "Aquarius", "Libra"], "Shasha")
        }

        for planet, (strong_signs, yoga_name) in mahapurusha_planets.items():
            p_data = planets.get(planet, {})
            p_sign = p_data.get("rasi", {}).get("name", "")
            p_house = get_house(planet)

            if p_sign in strong_signs and p_house in [1, 4, 7, 10]:
                yogas.append({
                    "name": f"{yoga_name} Yoga",
                    "type": "mahapurusha",
                    "description": f"{planet} in {p_sign} in {p_house}th house - great person yoga"
                })

        return yogas

    # =========================================================================
    # STATE MANAGEMENT
    # =========================================================================

    def save_session_state(self) -> Dict[str, Any]:
        """Save current session state for persistence."""
        return {
            "session_id": self.session_id,
            "active_kundali_id": self.active_kundali_id,
            "active_kundali_name": self.active_kundali_name,
            "pending_birth_details": self.pending_birth_details,
            "ayanamsa": self.tools.default_ayanamsa,
            "kundalis": [k.to_dict() for k in self.tools.kundalis.values()]
        }

    def restore_session_state(self, state: Dict[str, Any]):
        """Restore session state from saved data."""
        self.session_id = state.get("session_id")
        self.active_kundali_id = state.get("active_kundali_id")
        self.active_kundali_name = state.get("active_kundali_name")
        self.pending_birth_details = state.get("pending_birth_details", {})
        self.tools.default_ayanamsa = state.get("ayanamsa", "Lahiri")

        # Restore kundalis
        kundalis_data = state.get("kundalis", [])
        if kundalis_data:
            self.tools.sync_kundalis(kundalis_data)

    def reset_session(self):
        """Reset session to clean state."""
        self.conversation_history = []
        self.active_kundali_id = None
        self.active_kundali_name = None
        self.pending_birth_details = {}
        self.session_id = None
