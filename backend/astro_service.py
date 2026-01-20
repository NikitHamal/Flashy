"""
Astro Service Module

This module provides the main service for the Flashy Vedic Astrology Agent.
It manages sessions, coordinates with Gemini API, and handles
the astrological consultation loop with tool-based chart analysis.

The service embodies the ancient wisdom of Jyotish through a divine
truth-speaking agent that provides unfiltered cosmic insights.

Key Features:
- Multi-session management for concurrent consultations
- Streaming responses with tool call execution
- Kundali persistence and synchronization
- Context-aware astrological guidance
- Birth detail extraction and chart creation
"""

import asyncio
import re
import json
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime

from gemini_webapi import GeminiClient
from gemini_webapi.constants import Model

from .config import load_config
from .astro_agent import AstroAgent
from .astro_prompts import (
    get_system_prompt,
    get_kundali_creation_prompt,
    get_no_chart_prompt,
    PLANET_SIGNIFICATIONS
)
from .response_filter import ResponseFilter, ThoughtFilter


# Tool result template for feeding back to Gemini
ASTRO_TOOL_RESULT_TEMPLATE = """Tool: {tool_name}
Result: {output}

Continue with your analysis based on this data."""


class AstroService:
    """
    Service for Vedic astrology agent interactions with Gemini.

    Manages sessions, handles streaming responses, and coordinates
    kundali operations between frontend and AI agent.

    The service maintains:
    - Gemini chat sessions for continuous conversation
    - AstroAgent instances per session for state management
    - Kundali storage synchronized with frontend localStorage
    """

    def __init__(self):
        self.client = None
        self.config = load_config()
        self.sessions: Dict[str, Any] = {}  # Gemini chat sessions
        self.agents: Dict[str, AstroAgent] = {}  # Astro agents per session
        self.interrupted_sessions: set = set()
        self.active_tasks: Dict[str, asyncio.Task] = {}

        # Initialize filters for clean responses
        self.response_filter = ResponseFilter(aggressive=False)
        self.thought_filter = ThoughtFilter()

    async def get_client(self):
        """Get or initialize Gemini client."""
        if self.client is None:
            self.config = load_config()

            self.client = GeminiClient(
                self.config["Secure_1PSID"],
                self.config["Secure_1PSIDTS"],
                proxy=None
            )

            # Inject additional cookies if present
            if self.config.get("Secure_1PSIDCC"):
                self.client.cookies["__Secure-1PSIDCC"] = self.config["Secure_1PSIDCC"]

            await self.client.init(
                timeout=600,
                auto_close=False,
                close_delay=300,
                auto_refresh=True
            )

        return self.client

    def get_agent(self, session_id: str, ayanamsa: str = "Lahiri") -> AstroAgent:
        """Get or create an astro agent for a session."""
        if session_id not in self.agents:
            self.agents[session_id] = AstroAgent(ayanamsa=ayanamsa)
            self.agents[session_id].session_id = session_id
        return self.agents[session_id]

    async def get_session(self, session_id: str):
        """Get or create a Gemini chat session."""
        client = await self.get_client()

        if session_id not in self.sessions:
            model_name = self.config.get("model", "G_2_5_FLASH")
            model = getattr(Model, model_name, Model.G_2_5_FLASH)
            chat = client.start_chat(model=model)
            self.sessions[session_id] = chat

        return self.sessions[session_id]

    def interrupt_session(self, session_id: str):
        """Interrupt a running astrology session."""
        self.interrupted_sessions.add(session_id)
        if session_id in self.active_tasks:
            task = self.active_tasks[session_id]
            if task and not task.done():
                task.cancel()
                print(f"[AstroService] Cancelled task for session {session_id}")

    def _is_interrupted(self, session_id: str) -> bool:
        """Check if session is interrupted."""
        return session_id in self.interrupted_sessions

    def _clean_response_text(self, text: str, tool_call_raw: str = None) -> str:
        """Clean response text by removing tool call JSON and unwanted content."""
        if not text:
            return ""

        cleaned = text

        if tool_call_raw:
            cleaned = cleaned.replace(tool_call_raw, "").strip()

        # Remove orphaned JSON blocks that look like tool calls
        json_block_pattern = r'```json\s*\{[^`]*?"(?:action|tool|name)"\s*:[^`]*?\}\s*```'
        cleaned = re.sub(json_block_pattern, '', cleaned, flags=re.DOTALL).strip()

        # Apply response filter
        cleaned = self.response_filter.filter(cleaned)

        return cleaned

    def _separate_thinking(self, text: str) -> tuple:
        """Separate thinking from response text using enhanced filter."""
        if not text:
            return None, ""

        return self.thought_filter.extract_thoughts(text)

    async def _send_with_retry(
        self, chat, message, files=None,
        max_retries: int = 3, timeout: int = 120
    ):
        """Send message with retry logic."""
        last_error = None

        for attempt in range(max_retries):
            try:
                if files:
                    response = await asyncio.wait_for(
                        chat.send_message(message, files=files),
                        timeout=timeout
                    )
                else:
                    response = await asyncio.wait_for(
                        chat.send_message(message),
                        timeout=timeout
                    )
                return response
            except asyncio.CancelledError:
                raise
            except asyncio.TimeoutError:
                last_error = f"Request timed out after {timeout}s"
                print(f"[AstroService] Attempt {attempt + 1}/{max_retries}: {last_error}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
            except Exception as e:
                last_error = str(e)
                print(f"[AstroService] Attempt {attempt + 1}/{max_retries}: {last_error}")
                error_str = str(e).lower()
                if "invalid response" in error_str or "failed to generate" in error_str:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                raise

        raise Exception(f"Failed after {max_retries} attempts: {last_error}")

    def _build_context_summary(self, agent: AstroAgent) -> str:
        """Build a context string describing current session state for the AI."""
        parts = []

        if agent.active_kundali_id:
            kundali = agent.tools.kundalis.get(agent.active_kundali_id)
            if kundali:
                bd = kundali.birth_details
                if hasattr(bd, 'to_dict'):
                    bd = bd.to_dict()
                parts.append(f"**Active Chart**: {bd.get('name', 'Unknown')}")
                parts.append(f"  - Born: {bd.get('date')} at {bd.get('time')}")
                parts.append(f"  - Place: {bd.get('place')}")
                if kundali.chart_data:
                    lagna = kundali.chart_data.get("lagna", {})
                    moon = kundali.chart_data.get("planets", {}).get("Moon", {})
                    if lagna:
                        parts.append(f"  - Lagna: {lagna.get('rasi', {}).get('name', 'N/A')}")
                    if moon:
                        parts.append(f"  - Moon: {moon.get('rasi', {}).get('name', 'N/A')} in {moon.get('nakshatra', {}).get('name', 'N/A')}")

        kundali_count = len(agent.tools.kundalis)
        if kundali_count > 0:
            parts.append(f"\n**Stored Charts**: {kundali_count}")
            for kid, k in list(agent.tools.kundalis.items())[:5]:
                bd = k.birth_details
                if hasattr(bd, 'to_dict'):
                    bd = bd.to_dict()
                parts.append(f"  - {bd.get('name', 'Unknown')} ({kid})")
            if kundali_count > 5:
                parts.append(f"  - ... and {kundali_count - 5} more")

        parts.append(f"\n**Ayanamsa**: {agent.tools.default_ayanamsa}")

        if agent.pending_birth_details:
            parts.append("\n**Pending Birth Details** (incomplete):")
            for k, v in agent.pending_birth_details.items():
                parts.append(f"  - {k}: {v}")

        return "\n".join(parts) if parts else "No active context. Ready to create or analyze charts."

    def _detect_intent(self, message: str, agent: AstroAgent) -> Dict[str, Any]:
        """
        Detect user intent to provide better context to the AI.

        Returns hints about what the user might be asking for.
        """
        message_lower = message.lower()
        intent = {
            "type": "general",
            "hints": []
        }

        # Kundali creation intent
        creation_keywords = [
            "create", "generate", "make", "birth chart", "kundali", "kundli",
            "horoscope", "my chart", "chart for", "born on", "born in"
        ]
        if any(kw in message_lower for kw in creation_keywords):
            intent["type"] = "create_kundali"
            intent["hints"].append("User may want to create a new birth chart")

            # Check for birth details in message
            extracted = agent.extract_birth_details_from_message(message)
            if extracted:
                intent["extracted_details"] = extracted
                missing = agent.get_missing_birth_details(extracted)
                if missing:
                    intent["hints"].append(f"Missing birth details: {', '.join(missing)}")

        # Dasha/timing intent
        dasha_keywords = ["dasha", "mahadasha", "antardasha", "period", "timing", "when"]
        if any(kw in message_lower for kw in dasha_keywords):
            intent["type"] = "dasha_analysis"
            intent["hints"].append("User is asking about planetary periods/timing")

        # Compatibility intent
        compat_keywords = ["compatibility", "match", "matching", "marriage", "partner", "relationship"]
        if any(kw in message_lower for kw in compat_keywords):
            intent["type"] = "compatibility"
            intent["hints"].append("User is asking about relationship compatibility")

        # Career intent
        career_keywords = ["career", "job", "profession", "work", "business", "10th house"]
        if any(kw in message_lower for kw in career_keywords):
            intent["type"] = "career"
            intent["hints"].append("User is asking about career/profession")

        # Health intent
        health_keywords = ["health", "disease", "illness", "medical", "6th house", "8th house"]
        if any(kw in message_lower for kw in health_keywords):
            intent["type"] = "health"
            intent["hints"].append("User is asking about health matters")

        # Spiritual intent
        spiritual_keywords = ["spiritual", "moksha", "ketu", "12th house", "meditation", "yoga"]
        if any(kw in message_lower for kw in spiritual_keywords):
            intent["type"] = "spiritual"
            intent["hints"].append("User is asking about spiritual matters")

        return intent

    async def generate_reading(
        self,
        message: str,
        session_id: str,
        kundalis_data: Optional[List[Dict[str, Any]]] = None,
        active_kundali_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate astrological reading based on user message.
        Handles the agent loop with tool calls and chart analysis.

        Yields dictionaries with:
        - thought: AI thinking content (internal reasoning)
        - text: Response text to display to user
        - tool_call: Tool being called
        - tool_result: Tool execution result
        - kundalis: Updated list of kundalis
        - active_kundali: Currently active kundali info
        - is_final: Whether this is the final response
        """
        agent = self.get_agent(session_id)
        chat = await self.get_session(session_id)

        try:
            # Clear previous interruption
            if session_id in self.interrupted_sessions:
                self.interrupted_sessions.remove(session_id)

            # Sync kundalis from frontend localStorage
            if kundalis_data:
                agent.sync_from_storage(kundalis_data)

            # Set active kundali if provided
            if active_kundali_id:
                agent.set_active_kundali(active_kundali_id)

            # Detect user intent
            intent = self._detect_intent(message, agent)

            # Build system prompt with current context
            system_prompt = agent.get_system_prompt()
            context_summary = self._build_context_summary(agent)

            # Build full prompt
            full_prompt = f"""{system_prompt}

## Current Session Context
{context_summary}

## User Intent Analysis
Type: {intent.get('type', 'general')}
{chr(10).join('- ' + h for h in intent.get('hints', []))}

## User Message
{message}

Respond as the Vedic Jyotishi. If you need to use tools to analyze charts or create kundalis, do so.
Remember: Be blunt, truthful, and insightful. The stars do not lie, and neither should you."""

            # Send initial request
            response = await self._send_with_retry(chat, full_prompt)

            # Process agent loop
            max_iterations = agent.max_iterations
            iteration = 0

            while iteration < max_iterations:
                # Check for interruption
                if self._is_interrupted(session_id):
                    yield {
                        "text": "*Consultation interrupted by the seeker.*",
                        "is_final": True,
                        "kundalis": agent.get_all_kundalis(),
                        "active_kundali": {
                            "id": agent.active_kundali_id,
                            "name": agent.active_kundali_name
                        }
                    }
                    break

                response_text = response.text or ""

                # Extract thoughts
                api_thoughts = getattr(response, 'thoughts', None) or ""
                embedded_thinking, clean_response = self._separate_thinking(response_text)

                all_thoughts = ""
                if api_thoughts:
                    all_thoughts = api_thoughts
                if embedded_thinking:
                    if all_thoughts:
                        all_thoughts += "\n\n" + embedded_thinking
                    else:
                        all_thoughts = embedded_thinking

                # Yield thoughts (for debug/transparency)
                if all_thoughts:
                    yield {"thought": all_thoughts}

                # Parse tool call
                tool_call = agent.parse_tool_call(clean_response)

                if not tool_call:
                    # No tool call - final response
                    final_text = self._clean_response_text(clean_response)
                    if final_text:
                        yield {
                            "text": final_text,
                            "is_final": True,
                            "kundalis": agent.get_all_kundalis(),
                            "active_kundali": {
                                "id": agent.active_kundali_id,
                                "name": agent.active_kundali_name
                            }
                        }
                    else:
                        yield {
                            "text": "",
                            "is_final": True,
                            "kundalis": agent.get_all_kundalis(),
                            "active_kundali": {
                                "id": agent.active_kundali_id,
                                "name": agent.active_kundali_name
                            }
                        }
                    break

                # Handle text before tool call
                display_text = self._clean_response_text(
                    clean_response,
                    tool_call.get("raw_match")
                )
                if display_text:
                    yield {"text": display_text + "\n"}

                # Yield tool call info
                yield {
                    "tool_call": {
                        "name": tool_call["name"],
                        "args": tool_call["args"]
                    }
                }

                # Check interruption before tool execution
                if self._is_interrupted(session_id):
                    yield {
                        "text": "*Consultation interrupted by the seeker.*",
                        "is_final": True,
                        "kundalis": agent.get_all_kundalis(),
                        "active_kundali": {
                            "id": agent.active_kundali_id,
                            "name": agent.active_kundali_name
                        }
                    }
                    break

                # Execute tool
                try:
                    tool_result = await agent.execute_tool(
                        tool_call["name"],
                        tool_call["args"]
                    )

                    # Check if kundali was created/updated
                    kundali_update = tool_call["name"] in [
                        "create_kundali", "delete_kundali", "update_kundali",
                        "sync_kundalis"
                    ]

                    yield {
                        "tool_result": tool_result,
                        "kundalis": agent.get_all_kundalis() if kundali_update else None,
                        "active_kundali": {
                            "id": agent.active_kundali_id,
                            "name": agent.active_kundali_name
                        } if kundali_update else None
                    }

                    # Check interruption before next API call
                    if self._is_interrupted(session_id):
                        yield {
                            "text": "*Consultation interrupted by the seeker.*",
                            "is_final": True,
                            "kundalis": agent.get_all_kundalis(),
                            "active_kundali": {
                                "id": agent.active_kundali_id,
                                "name": agent.active_kundali_name
                            }
                        }
                        break

                    # Build result prompt for Gemini
                    result_prompt = ASTRO_TOOL_RESULT_TEMPLATE.format(
                        tool_name=tool_call["name"],
                        output=tool_result
                    )

                    # Feed result back to Gemini
                    response = await self._send_with_retry(chat, result_prompt)
                    iteration += 1

                except asyncio.CancelledError:
                    yield {
                        "text": "*Consultation interrupted.*",
                        "is_final": True,
                        "kundalis": agent.get_all_kundalis(),
                        "active_kundali": {
                            "id": agent.active_kundali_id,
                            "name": agent.active_kundali_name
                        }
                    }
                    break
                except Exception as e:
                    error_msg = f"Error executing '{tool_call['name']}': {str(e)}"
                    yield {"tool_result": error_msg}

                    if self._is_interrupted(session_id):
                        yield {
                            "text": "*Consultation interrupted.*",
                            "is_final": True,
                            "kundalis": agent.get_all_kundalis(),
                            "active_kundali": {
                                "id": agent.active_kundali_id,
                                "name": agent.active_kundali_name
                            }
                        }
                        break

                    # Feed error back to Gemini for graceful handling
                    response = await self._send_with_retry(chat, error_msg)
                    iteration += 1

            # Check iteration limit
            if iteration >= max_iterations:
                yield {
                    "text": "*The cosmic analysis has reached its natural boundary. "
                           "Ask further questions to continue the consultation.*",
                    "is_final": True,
                    "kundalis": agent.get_all_kundalis(),
                    "active_kundali": {
                        "id": agent.active_kundali_id,
                        "name": agent.active_kundali_name
                    }
                }

        except asyncio.CancelledError:
            yield {
                "text": "*Consultation interrupted.*",
                "is_final": True,
                "kundalis": agent.get_all_kundalis(),
                "active_kundali": {
                    "id": agent.active_kundali_id,
                    "name": agent.active_kundali_name
                }
            }
        except Exception as e:
            yield {
                "error": str(e),
                "is_final": True,
                "kundalis": agent.get_all_kundalis(),
                "active_kundali": {
                    "id": agent.active_kundali_id,
                    "name": agent.active_kundali_name
                }
            }
        finally:
            # Clean up interruption flag
            if session_id in self.interrupted_sessions:
                self.interrupted_sessions.remove(session_id)

    async def create_kundali_direct(
        self,
        session_id: str,
        name: str,
        date: str,
        time: str,
        place: str,
        latitude: float,
        longitude: float,
        timezone: str,
        gender: str = "male",
        notes: str = "",
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a kundali directly without AI involvement.
        Used for form-based chart creation from frontend.
        """
        agent = self.get_agent(session_id)

        result = agent.tools.create_kundali(
            name=name,
            date=date,
            time=time,
            place=place,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            gender=gender,
            notes=notes,
            tags=tags
        )

        result_data = json.loads(result)

        if result_data.get("status") == "success":
            kundali = result_data.get("kundali", {})
            agent.active_kundali_id = kundali.get("id")
            bd = kundali.get("birth_details", {})
            agent.active_kundali_name = bd.get("name")

        return {
            "result": result_data,
            "kundalis": agent.get_all_kundalis(),
            "active_kundali": {
                "id": agent.active_kundali_id,
                "name": agent.active_kundali_name
            }
        }

    async def update_chart_data(
        self,
        session_id: str,
        kundali_id: str,
        chart_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update chart data for a kundali after frontend calculation.

        The astronomical calculations are done client-side using AstroWeb.
        This method stores the calculated data for AI analysis.
        """
        agent = self.get_agent(session_id)

        result = agent.tools.update_kundali(
            kundali_id=kundali_id,
            chart_data=chart_data
        )

        return {
            "result": json.loads(result),
            "kundalis": agent.get_all_kundalis()
        }

    def sync_kundalis(
        self,
        session_id: str,
        kundalis_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Sync kundalis from frontend localStorage.
        Called on page load to restore session state.
        """
        agent = self.get_agent(session_id)
        result = agent.sync_from_storage(kundalis_data)

        return {
            "result": json.loads(result),
            "kundalis": agent.get_all_kundalis()
        }

    def export_kundalis(self, session_id: str) -> Dict[str, Any]:
        """
        Export all kundalis for frontend persistence.
        """
        agent = self.get_agent(session_id)
        result = agent.export_to_storage()

        return json.loads(result)

    def set_active_kundali(
        self,
        session_id: str,
        kundali_id: str
    ) -> Dict[str, Any]:
        """
        Set the active kundali for a session.
        """
        agent = self.get_agent(session_id)
        success = agent.set_active_kundali(kundali_id)

        return {
            "success": success,
            "active_kundali": {
                "id": agent.active_kundali_id,
                "name": agent.active_kundali_name
            }
        }

    def clear_active_kundali(self, session_id: str) -> Dict[str, Any]:
        """
        Clear the active kundali context for a session.
        """
        agent = self.get_agent(session_id)
        agent.clear_active_kundali()

        return {
            "success": True,
            "active_kundali": None
        }

    def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """
        Get current session state for persistence/debugging.
        """
        agent = self.agents.get(session_id)
        if not agent:
            return {
                "session_id": session_id,
                "active_kundali": None,
                "kundali_count": 0,
                "ayanamsa": "Lahiri"
            }

        return {
            "session_id": session_id,
            "active_kundali": {
                "id": agent.active_kundali_id,
                "name": agent.active_kundali_name
            },
            "kundali_count": len(agent.tools.kundalis),
            "ayanamsa": agent.tools.default_ayanamsa,
            "context_summary": agent.get_context_summary()
        }

    def set_ayanamsa(self, session_id: str, system: str) -> Dict[str, Any]:
        """
        Set the ayanamsa system for a session.
        """
        agent = self.get_agent(session_id)
        result = agent.tools.set_ayanamsa(system)

        return json.loads(result)

    def get_available_ayanamsas(self, session_id: str) -> Dict[str, Any]:
        """
        Get list of available ayanamsa systems.
        """
        agent = self.get_agent(session_id)
        result = agent.tools.get_available_ayanamsas()

        return json.loads(result)

    async def get_planet_info(self, planet: str) -> Dict[str, Any]:
        """
        Get signification data for a planet (static reference data).
        """
        info = PLANET_SIGNIFICATIONS.get(planet)
        if not info:
            return {"error": f"Planet '{planet}' not found"}

        return {
            "planet": planet,
            "info": info
        }

    def delete_kundali(
        self,
        session_id: str,
        kundali_id: str
    ) -> Dict[str, Any]:
        """
        Delete a kundali by ID.
        """
        agent = self.get_agent(session_id)

        # Clear active if deleting active chart
        if agent.active_kundali_id == kundali_id:
            agent.clear_active_kundali()

        result = agent.tools.delete_kundali(kundali_id)

        return {
            "result": json.loads(result),
            "kundalis": agent.get_all_kundalis(),
            "active_kundali": {
                "id": agent.active_kundali_id,
                "name": agent.active_kundali_name
            }
        }

    def search_kundalis(
        self,
        session_id: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Search kundalis by name or tags.
        """
        agent = self.get_agent(session_id)
        result = agent.tools.search_kundalis(query)

        return json.loads(result)

    async def reset(self):
        """Reset the service, clearing all sessions and agents."""
        self.client = None
        self.sessions = {}
        self.agents = {}
        self.interrupted_sessions = set()
        self.active_tasks = {}

    def save_session(self, session_id: str) -> Dict[str, Any]:
        """
        Save session state for later restoration.
        """
        agent = self.agents.get(session_id)
        if not agent:
            return {"error": "Session not found"}

        return agent.save_session_state()

    def restore_session(
        self,
        session_id: str,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Restore a saved session state.
        """
        agent = self.get_agent(session_id)
        agent.restore_session_state(state)

        return {
            "success": True,
            "session_id": session_id,
            "active_kundali": {
                "id": agent.active_kundali_id,
                "name": agent.active_kundali_name
            },
            "kundali_count": len(agent.tools.kundalis)
        }

    def reset_session(self, session_id: str) -> Dict[str, Any]:
        """
        Reset a specific session to clean state.
        """
        agent = self.agents.get(session_id)
        if agent:
            agent.reset_session()

        # Remove Gemini chat session to force fresh start
        if session_id in self.sessions:
            del self.sessions[session_id]

        return {
            "success": True,
            "session_id": session_id,
            "message": "Session reset to clean state"
        }
