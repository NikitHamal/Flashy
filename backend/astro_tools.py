"""
Astro Tools

Provides kundali CRUD operations and Vedic reference lookups.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .vedic_reference import get_reference


def _timestamp() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _deep_update(target: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_update(target[key], value)
        else:
            target[key] = value
    return target


class AstroTools:
    def __init__(self):
        self.kundalis: List[Dict[str, Any]] = []

    def set_state(self, kundalis: List[Dict[str, Any]]):
        self.kundalis = kundalis or []

    def get_state(self) -> List[Dict[str, Any]]:
        return self.kundalis

    def _find_kundali(self, kundali_id: str) -> Optional[Dict[str, Any]]:
        return next((k for k in self.kundalis if k.get("id") == kundali_id), None)

    def _normalize_kundali(self, kundali: Dict[str, Any]) -> Dict[str, Any]:
        profile = kundali.get("profile", {})
        chart = kundali.get("chart", {})
        normalized = {
            "id": kundali.get("id") or f"kundali_{uuid.uuid4().hex[:10]}",
            "profile": {
                "name": profile.get("name") or "Unnamed",
                "gender": profile.get("gender") or "unspecified",
                "birth": profile.get("birth") or {},
                "location": profile.get("location") or {},
                "timezone": profile.get("timezone") or "",
                "notes": profile.get("notes") or ""
            },
            "chart": {
                "lagna": chart.get("lagna") or {},
                "rashi": chart.get("rashi") or {},
                "navamsa": chart.get("navamsa") or {},
                "planets": chart.get("planets") or {},
                "houses": chart.get("houses") or {},
                "dashas": chart.get("dashas") or {},
                "ashtakavarga": chart.get("ashtakavarga") or {},
                "yogas": chart.get("yogas") or []
            },
            "predictions": kundali.get("predictions") or {},
            "notes": kundali.get("notes") or "",
            "createdAt": kundali.get("createdAt") or _timestamp(),
            "updatedAt": _timestamp()
        }
        return normalized

    def get_available_tools(self) -> List[Dict[str, str]]:
        return [
            {"name": "create_kundali", "description": "Create a new kundali profile with chart data"},
            {"name": "list_kundalis", "description": "List all kundalis with ids and names"},
            {"name": "get_kundali", "description": "Get a full kundali by id"},
            {"name": "update_kundali", "description": "Update fields of a kundali by id"},
            {"name": "delete_kundali", "description": "Delete a kundali by id"},
            {"name": "search_kundalis", "description": "Search kundalis by name or notes"},
            {"name": "get_kundali_parameter", "description": "Get a specific parameter from a kundali by dot path"},
            {"name": "vedic_reference", "description": "Get Vedic reference data for signs, planets, houses, or nakshatras"}
        ]

    async def execute(self, tool_name: str, **kwargs) -> str:
        method = getattr(self, tool_name, None)
        if not method:
            return f"Error: Unknown tool '{tool_name}'"
        try:
            return method(**kwargs)
        except Exception as exc:
            return f"Error executing {tool_name}: {exc}"

    def create_kundali(self, profile: Dict[str, Any], chart: Dict[str, Any] = None, notes: str = "") -> str:
        kundali = self._normalize_kundali({
            "profile": profile,
            "chart": chart or {},
            "notes": notes
        })
        self.kundalis.append(kundali)
        return json.dumps({"message": "Kundali created", "kundali": kundali}, indent=2)

    def list_kundalis(self) -> str:
        summaries = [
            {
                "id": k.get("id"),
                "name": k.get("profile", {}).get("name"),
                "gender": k.get("profile", {}).get("gender"),
                "createdAt": k.get("createdAt"),
                "updatedAt": k.get("updatedAt")
            }
            for k in self.kundalis
        ]
        return json.dumps({"kundalis": summaries}, indent=2)

    def get_kundali(self, kundali_id: str) -> str:
        kundali = self._find_kundali(kundali_id)
        if not kundali:
            return json.dumps({"error": "Kundali not found", "id": kundali_id})
        return json.dumps({"kundali": kundali}, indent=2)

    def update_kundali(self, kundali_id: str, updates: Dict[str, Any]) -> str:
        kundali = self._find_kundali(kundali_id)
        if not kundali:
            return json.dumps({"error": "Kundali not found", "id": kundali_id})
        _deep_update(kundali, updates)
        kundali["updatedAt"] = _timestamp()
        return json.dumps({"message": "Kundali updated", "kundali": kundali}, indent=2)

    def delete_kundali(self, kundali_id: str) -> str:
        kundali = self._find_kundali(kundali_id)
        if not kundali:
            return json.dumps({"error": "Kundali not found", "id": kundali_id})
        self.kundalis = [k for k in self.kundalis if k.get("id") != kundali_id]
        return json.dumps({"message": "Kundali deleted", "id": kundali_id}, indent=2)

    def search_kundalis(self, query: str) -> str:
        q = (query or "").lower()
        results = []
        for kundali in self.kundalis:
            profile = kundali.get("profile", {})
            name = profile.get("name", "").lower()
            notes = (kundali.get("notes") or "").lower()
            if q in name or q in notes:
                results.append({"id": kundali.get("id"), "name": profile.get("name")})
        return json.dumps({"query": query, "results": results}, indent=2)

    def get_kundali_parameter(self, kundali_id: str, path: str) -> str:
        kundali = self._find_kundali(kundali_id)
        if not kundali:
            return json.dumps({"error": "Kundali not found", "id": kundali_id})
        value = kundali
        for part in (path or "").split("."):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return json.dumps({"error": "Path not found", "path": path})
        return json.dumps({"path": path, "value": value}, indent=2)

    def vedic_reference(self, topic: str = "") -> str:
        return json.dumps(get_reference(topic), indent=2)
