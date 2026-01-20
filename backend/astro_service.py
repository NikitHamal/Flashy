"""
Astro Service Module

This module provides the main service layer for the Flashy Astro agent.
It manages sessions, coordinates with the Gemini API, and handles
the astrological consultation flow.
"""

import asyncio
import re
from typing import Dict, Any, List, Optional, AsyncGenerator
from gemini_webapi import GeminiClient
from gemini_webapi.constants import Model

from .config import load_config
from .astro_agent import AstroAgent
from .astro_prompts import ASTRO_TOOL_RESULT_TEMPLATE


class AstroService:
    """
    Service for Astro agent interactions with Gemini.
    
    Handles:
    - Session management
    - Streaming responses
    - Tool execution loop
    - Kundali data synchronization
    """
    
    def __init__(self):
        self.client = None
        self.config = load_config()
        self.sessions: Dict[str, Any] = {}  # Gemini chat sessions
        self.agents: Dict[str, AstroAgent] = {}  # Astro agents per session
        self.interrupted_sessions: set = set()
        self.active_tasks: Dict[str, asyncio.Task] = {}
    
    async def get_client(self):
        """Get or initialize Gemini client."""
        if self.client is None:
            self.config = load_config()
            
            self.client = GeminiClient(
                self.config["Secure_1PSID"],
                self.config["Secure_1PSIDTS"],
                proxy=None
            )
            
            if self.config.get("Secure_1PSIDCC"):
                self.client.cookies["__Secure-1PSIDCC"] = self.config["Secure_1PSIDCC"]
            
            await self.client.init(
                timeout=600,
                auto_close=False,
                close_delay=300,
                auto_refresh=True
            )
        
        return self.client
    
    def get_agent(self, session_id: str) -> AstroAgent:
        """Get or create an astro agent for a session."""
        if session_id not in self.agents:
            self.agents[session_id] = AstroAgent(ayanamsa="Lahiri")
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
        """Interrupt a running session."""
        self.interrupted_sessions.add(session_id)
        if session_id in self.active_tasks:
            task = self.active_tasks[session_id]
            if task and not task.done():
                task.cancel()
    
    def _is_interrupted(self, session_id: str) -> bool:
        """Check if session is interrupted."""
        return session_id in self.interrupted_sessions
    
    def _separate_thinking(self, text: str) -> tuple:
        """Separate thinking from response text."""
        if not text:
            return None, ""
        
        thinking_content = None
        clean_text = text
        
        think_pattern = r'<think>(.*?)</think>'
        matches = re.findall(think_pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            thinking_content = '\n'.join(matches)
            clean_text = re.sub(
                think_pattern, '', clean_text,
                flags=re.DOTALL | re.IGNORECASE
            ).strip()
        
        return thinking_content, clean_text
    
    def _clean_response_text(self, text: str, tool_call_raw: str = None) -> str:
        """Clean response text."""
        if not text:
            return ""
        
        cleaned = text
        
        if tool_call_raw:
            cleaned = cleaned.replace(tool_call_raw, "").strip()
        
        json_block_pattern = r'```json\s*\{[^`]*?"(?:action|tool|name)"\s*:[^`]*?\}\s*```'
        cleaned = re.sub(json_block_pattern, '', cleaned, flags=re.DOTALL).strip()
        
        return cleaned
    
    async def _send_with_retry(
        self, chat, message,
        max_retries: int = 3, timeout: int = 120
    ):
        """Send message with retry logic."""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = await asyncio.wait_for(
                    chat.send_message(message),
                    timeout=timeout
                )
                return response
            except asyncio.CancelledError:
                raise
            except asyncio.TimeoutError:
                last_error = f"Request timed out after {timeout}s"
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
        
        raise Exception(f"Failed after {max_retries} attempts: {last_error}")
    
    async def chat(
        self,
        message: str,
        session_id: str,
        profiles_data: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Handle a chat message and stream responses.
        
        Args:
            message: User message
            session_id: Session identifier
            profiles_data: Optional kundali profiles from frontend localStorage
        
        Yields:
            Response chunks with: thought, text, tool_call, tool_result, is_final, profiles_update
        """
        client = await self.get_client()
        agent = self.get_agent(session_id)
        chat = await self.get_session(session_id)
        
        try:
            # Clear previous interruption
            if session_id in self.interrupted_sessions:
                self.interrupted_sessions.remove(session_id)
            
            # Load profiles if provided
            if profiles_data:
                agent.load_profiles(profiles_data)
            
            # Build full prompt with system context
            system_context = agent.get_system_prompt()
            kundali_summary = agent.get_kundali_summary()
            
            full_prompt = f"""{system_context}

Current Session State:
{kundali_summary}

User Message:
{message}

Respond as Flashy Astro. Use tools when you need chart data. Be direct and insightful."""
            
            # Send to Gemini
            response = await self._send_with_retry(chat, full_prompt)
            
            # Process agent loop
            max_iterations = agent.max_iterations
            iteration = 0
            
            while iteration < max_iterations:
                # Check interruption
                if self._is_interrupted(session_id):
                    yield {"text": "*Session interrupted.*", "is_final": True}
                    break
                
                response_text = response.text or ""
                
                # Extract thinking
                api_thoughts = getattr(response, 'thoughts', None) or ""
                embedded_thinking, clean_response = self._separate_thinking(response_text)
                
                all_thoughts = ""
                if api_thoughts:
                    all_thoughts = api_thoughts
                if embedded_thinking:
                    all_thoughts = f"{all_thoughts}\n\n{embedded_thinking}".strip()
                
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
                            "profiles_update": agent.export_profiles()
                        }
                    else:
                        yield {
                            "text": "",
                            "is_final": True,
                            "profiles_update": agent.export_profiles()
                        }
                    break
                
                # Handle text before tool call
                display_text = self._clean_response_text(
                    clean_response, tool_call.get("raw_match")
                )
                if display_text:
                    yield {"text": display_text + "\n"}
                
                # Yield tool call
                yield {
                    "tool_call": {
                        "name": tool_call["name"],
                        "args": tool_call["args"]
                    }
                }
                
                # Check interruption before tool execution
                if self._is_interrupted(session_id):
                    yield {"text": "*Session interrupted.*", "is_final": True}
                    break
                
                # Execute tool
                try:
                    tool_result = await agent.execute_tool(
                        tool_call["name"],
                        tool_call["args"]
                    )
                    
                    yield {"tool_result": tool_result}
                    
                    # Check interruption
                    if self._is_interrupted(session_id):
                        yield {"text": "*Session interrupted.*", "is_final": True}
                        break
                    
                    # Feed result back to Gemini
                    response = await self._send_with_retry(chat, tool_result)
                    iteration += 1
                    
                except asyncio.CancelledError:
                    yield {"text": "*Session interrupted.*", "is_final": True}
                    break
                except Exception as e:
                    error_msg = f"Error executing '{tool_call['name']}': {str(e)}"
                    yield {"tool_result": error_msg}
                    
                    if self._is_interrupted(session_id):
                        yield {"text": "*Session interrupted.*", "is_final": True}
                        break
                    
                    response = await self._send_with_retry(chat, error_msg)
                    iteration += 1
            
            if iteration >= max_iterations:
                yield {
                    "text": "*Maximum iterations reached. Please continue the conversation.*",
                    "is_final": True,
                    "profiles_update": agent.export_profiles()
                }
        
        except asyncio.CancelledError:
            yield {"text": "*Session interrupted.*", "is_final": True}
        except Exception as e:
            yield {
                "error": str(e),
                "is_final": True,
                "profiles_update": agent.export_profiles()
            }
        finally:
            if session_id in self.interrupted_sessions:
                self.interrupted_sessions.remove(session_id)
    
    def get_profiles(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all profiles for a session."""
        agent = self.agents.get(session_id)
        if agent:
            return agent.export_profiles()
        return []
    
    def set_profiles(self, session_id: str, profiles: List[Dict[str, Any]]):
        """Set profiles for a session."""
        agent = self.get_agent(session_id)
        agent.load_profiles(profiles)
    
    def get_chart_data(self, session_id: str, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get chart data for frontend rendering."""
        agent = self.agents.get(session_id)
        if agent:
            return agent.get_chart_data_for_frontend(profile_id)
        return None
    
    async def quick_analysis(self, session_id: str, profile_id: str) -> Dict[str, Any]:
        """Get quick analysis without AI interpretation."""
        agent = self.get_agent(session_id)
        return await agent.quick_analysis(profile_id)
    
    def create_kundali_direct(
        self,
        session_id: str,
        name: str,
        birth_date: str,
        birth_time: str,
        latitude: float,
        longitude: float,
        place_name: str = "",
        timezone: str = "UTC",
        gender: str = "other"
    ) -> Dict[str, Any]:
        """
        Create a kundali directly without AI involvement.
        Used for manual creation from frontend.
        """
        agent = self.get_agent(session_id)
        
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                agent.tools._create_kundali(
                    name=name,
                    birth_date=birth_date,
                    birth_time=birth_time,
                    latitude=latitude,
                    longitude=longitude,
                    place_name=place_name,
                    timezone=timezone,
                    gender=gender
                )
            )
            
            # Get the newly created profile
            profiles = agent.tools.storage.list_profiles()
            if profiles:
                latest = profiles[-1]
                chart_data = agent.get_chart_data_for_frontend(latest.id)
                return {
                    "success": True,
                    "message": result,
                    "profile": latest.to_dict(),
                    "chart_data": chart_data
                }
            
            return {"success": True, "message": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            loop.close()
    
    def delete_kundali_direct(self, session_id: str, profile_id: str) -> Dict[str, Any]:
        """Delete a kundali directly."""
        agent = self.get_agent(session_id)
        success = agent.tools.storage.delete_profile(profile_id)
        
        return {
            "success": success,
            "profiles_update": agent.export_profiles()
        }
    
    async def reset(self):
        """Reset the service."""
        self.client = None
        self.sessions = {}
        self.agents = {}
