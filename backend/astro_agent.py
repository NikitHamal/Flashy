"""
Astro Agent Module

This module provides the agent logic for the Flashy Astro system.
It manages the conversation flow, tool execution, and integration
with the Vedic astrology calculation engine.
"""

import re
import json
from typing import Optional, Dict, Any, List
from .astro_tools import AstroTools
from .astro_prompts import get_system_prompt, ASTRO_TOOL_RESULT_TEMPLATE


class AstroAgent:
    """
    Flashy Astro Agent - A blunt, honest Vedic astrologer.
    
    This agent:
    - Manages kundali (birth chart) profiles
    - Performs accurate Vedic calculations
    - Provides interpretations based on classical texts
    - Uses tools to access and analyze astrological data
    """
    
    def __init__(self, ayanamsa: str = "Lahiri"):
        self.tools = AstroTools(ayanamsa=ayanamsa)
        self.conversation_history: List[Dict[str, Any]] = []
        self.max_iterations = 15
        self.session_id: Optional[str] = None
    
    def get_system_prompt(self) -> str:
        """Get the system prompt with current context."""
        kundali_count = len(self.tools.storage.list_profiles())
        available_tools = self.tools.get_available_tools()
        return get_system_prompt(kundali_count=kundali_count, tools=available_tools)
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Get the schema of available tools."""
        return self.tools.get_available_tools()
    
    def parse_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse a tool call from the model's output.
        
        Recognizes:
        1. ```json code blocks with action key
        2. Inline JSON objects with action key
        """
        if not text:
            return None
        
        valid_tools = {t['name'] for t in self.tools.get_available_tools()}
        
        # 1. Markdown code blocks
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
        
        # 2. Inline JSON with "action" key
        action_pattern = r'\{\s*"action"\s*:\s*"([^"]+)"'
        matches = list(re.finditer(action_pattern, text))
        
        for match in matches:
            tool_name = match.group(1)
            if tool_name not in valid_tools:
                continue
            
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
        """Validate that parsed JSON is a valid tool call."""
        if not isinstance(data, dict):
            return None
        
        tool_name = data.get("action") or data.get("tool") or data.get("name")
        if not tool_name or tool_name not in valid_tools:
            return None
        
        args = data.get("args") or data.get("arguments") or data.get("parameters") or {}
        
        return {
            "name": tool_name,
            "args": args
        }
    
    async def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Execute a tool and return formatted result."""
        result = await self.tools.execute(tool_name, **args)
        return ASTRO_TOOL_RESULT_TEMPLATE.format(
            tool_name=tool_name,
            output=result
        )
    
    def clean_response_text(self, text: str, raw_match: str = None) -> str:
        """Clean response text by removing tool call JSON."""
        if not text:
            return ""
        
        cleaned = text
        
        if raw_match:
            cleaned = cleaned.replace(raw_match, "")
        
        # Remove any remaining tool call JSON blocks
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
        
        return thinking_content, clean_text
    
    def get_kundali_summary(self) -> str:
        """Get a summary of available kundalis for context."""
        profiles = self.tools.storage.list_profiles()
        if not profiles:
            return "No kundalis currently stored."
        
        lines = [f"Stored Kundalis ({len(profiles)}):"]
        for p in profiles:
            lines.append(f"  - {p.name} (ID: {p.id})")
        return "\n".join(lines)
    
    def load_profiles(self, profiles_data: List[Dict[str, Any]]):
        """Load profiles from external data (e.g., frontend localStorage)."""
        self.tools.storage.load_from_data(profiles_data)
    
    def export_profiles(self) -> List[Dict[str, Any]]:
        """Export all profiles for storage."""
        return self.tools.storage.export_data()
    
    def get_chart_data_for_frontend(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        Get chart data formatted for frontend rendering.
        Returns position data suitable for drawing charts.
        """
        profile = self.tools.storage.get_profile(profile_id)
        if not profile:
            return None
        
        chart = self.tools.storage.get_chart(profile_id)
        if not chart:
            # Calculate if not cached
            from datetime import datetime
            from .astro_engine import Location
            
            dt = datetime.fromisoformat(profile.datetime)
            location = Location(
                latitude=profile.latitude,
                longitude=profile.longitude,
                timezone=profile.timezone,
                place_name=profile.place_name
            )
            chart = self.tools.engine.calculate_chart(dt, location)
            self.tools.storage.set_chart(profile_id, chart)
        
        # Format for frontend
        return {
            "profile": profile.to_dict(),
            "chart": chart.to_dict(),
            "current_dasha": self.tools.engine.get_current_dasha(chart)
        }
    
    def format_streaming_response(
        self,
        text: str = None,
        thought: str = None,
        tool_call: Dict = None,
        tool_result: str = None,
        is_final: bool = False,
        profiles_update: List[Dict] = None
    ) -> Dict[str, Any]:
        """Format response for streaming to frontend."""
        response = {}
        
        if text:
            response["text"] = text
        if thought:
            response["thought"] = thought
        if tool_call:
            response["tool_call"] = tool_call
        if tool_result:
            response["tool_result"] = tool_result
        if is_final:
            response["is_final"] = True
        if profiles_update is not None:
            response["profiles_update"] = profiles_update
        
        return response
    
    def extract_birth_details_prompt(self) -> str:
        """Return a prompt asking for birth details."""
        return """To provide you with an accurate Vedic astrological reading, I need your complete birth details:

1. **Full Name**: As you wish to be identified
2. **Birth Date**: DD-MM-YYYY format
3. **Birth Time**: As precise as possible (check birth certificate if available)
4. **Birth Place**: City/Town name (I'll get the coordinates)
5. **Gender**: Male/Female/Other

Please provide these details, and I will create your Kundali for analysis.

Note: The more accurate your birth time, the more precise the reading. Even a few minutes can affect the Ascendant and house positions."""
    
    def needs_birth_details(self, message: str) -> bool:
        """Check if the message requires birth details for a reading."""
        reading_keywords = [
            "my chart", "my kundali", "my horoscope", "my birth",
            "reading for me", "analyze my", "my dasha", "my yoga",
            "predict for me", "my future", "my career", "my marriage",
            "will i", "when will i", "should i", "what about my"
        ]
        
        message_lower = message.lower()
        
        for keyword in reading_keywords:
            if keyword in message_lower:
                # Check if we have any profiles
                if not self.tools.storage.list_profiles():
                    return True
                break
        
        return False
    
    async def quick_analysis(self, profile_id: str) -> Dict[str, Any]:
        """
        Perform a quick analysis of a kundali and return structured data.
        Useful for frontend display without AI interpretation.
        """
        profile = self.tools.storage.get_profile(profile_id)
        if not profile:
            return {"error": "Profile not found"}
        
        chart = self.tools.storage.get_chart(profile_id)
        if not chart:
            return {"error": "Chart not calculated"}
        
        # Get current dasha
        current_dasha = self.tools.engine.get_current_dasha(chart)
        
        # Analyze yogas
        yogas = self.tools.yoga_analyzer.analyze(chart)
        
        # Format yogas for frontend
        yoga_summary = []
        for yoga in yogas[:10]:  # Top 10 yogas
            yoga_summary.append({
                "name": yoga.name,
                "category": yoga.category,
                "nature": yoga.nature,
                "strength": yoga.strength,
                "planets": yoga.planets
            })
        
        return {
            "profile": profile.to_dict(),
            "lagna": {
                "sign": chart.lagna.rasi_name,
                "sign_english": chart.lagna.rasi_name_english,
                "degree": round(chart.lagna.degree_in_sign, 2),
                "nakshatra": chart.lagna.nakshatra_name,
                "pada": chart.lagna.nakshatra_pada
            },
            "planets": {
                name: {
                    "sign": p.rasi_name,
                    "sign_english": p.rasi_name_english,
                    "degree": round(p.degree_in_sign, 2),
                    "nakshatra": p.nakshatra_name,
                    "pada": p.nakshatra_pada,
                    "retrograde": p.is_retrograde,
                    "dignity": p.dignity
                }
                for name, p in chart.planets.items()
            },
            "houses": [round(h, 2) for h in chart.houses],
            "current_dasha": current_dasha,
            "yogas": yoga_summary,
            "divisional_charts": chart.divisional_charts
        }
