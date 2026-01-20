"""
Astro Tools

Provides local tool execution for managing kundali profiles.
State is passed in from the request (local storage mirror).
"""

from __future__ import annotations

import uuid
from typing import Dict, Any, List, Optional, Tuple


REQUIRED_PROFILE_FIELDS = [
    "name",
    "birthDate",
    "birthTime",
    "birthPlace",
    "latitude",
    "longitude",
    "timezone",
    "gender"
]


def _parse_timezone(val: Any) -> float:
    if isinstance(val, (int, float)):
        return float(val)
    
    # Clean string: remove UTC, GMT, and spaces
    s = str(val).strip().upper().replace("UTC", "").replace("GMT", "").replace(" ", "")
    if not s:
        return 0.0
    
    sign = -1.0 if s.startswith("-") else 1.0
    # Remove leading sign for parsing
    s_clean = s.lstrip("+-")
    
    if ":" in s_clean:
        parts = s_clean.split(":")
        hours = float(parts[0]) if parts[0] else 0.0
        minutes = float(parts[1]) if len(parts) > 1 and parts[1] else 0.0
        return sign * (hours + (minutes / 60.0))
    
    return float(s)

def _normalize_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(profile)

    if "id" not in normalized:
        normalized["id"] = f"kundali_{uuid.uuid4().hex[:10]}"

    # Normalize numeric fields
    for key in ("latitude", "longitude", "timezone"):
        if key in normalized and normalized[key] is not None:
            try:
                if key == "timezone":
                    normalized[key] = _parse_timezone(normalized[key])
                else:
                    normalized[key] = float(normalized[key])
            except (TypeError, ValueError):
                raise ValueError(f"Invalid {key}; must be numeric or HH:MM format.")

    # Normalize strings
    for key in ("name", "birthDate", "birthTime", "birthPlace", "gender"):
        if key in normalized and normalized[key] is not None:
            normalized[key] = str(normalized[key]).strip()

    return normalized


def _validate_profile(profile: Dict[str, Any]) -> List[str]:
    missing = []
    for field in REQUIRED_PROFILE_FIELDS:
        if not profile.get(field):
            missing.append(field)
    return missing


class AstroTools:
    """Executes tool calls for kundali management."""

    def get_available_tools(self) -> List[Dict[str, str]]:
        return [
            {"name": "list_kundalis", "description": "List all kundali profiles"},
            {"name": "get_kundali", "description": "Fetch full kundali by id"},
            {"name": "create_kundali", "description": "Create a new kundali profile"},
            {"name": "update_kundali", "description": "Update a kundali profile"},
            {"name": "delete_kundali", "description": "Delete a kundali profile"},
            {"name": "select_kundali", "description": "Select active kundali"}
        ]

    def execute(
        self,
        tool_name: str,
        kundalis: List[Dict[str, Any]],
        active_id: Optional[str],
        **kwargs: Any
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Optional[str]]:
        if tool_name == "list_kundalis":
            return self._list_kundalis(kundalis), kundalis, active_id
        if tool_name == "get_kundali":
            return self._get_kundali(kundalis, kwargs.get("id")), kundalis, active_id
        if tool_name == "create_kundali":
            # Support both nested {"profile": {...}} and flattened {...}
            profile = kwargs.get("profile") if "profile" in kwargs else kwargs
            return self._create_kundali(kundalis, profile), kundalis, active_id
        if tool_name == "update_kundali":
            # Support both nested {"updates": {...}} and flattened {...}
            kundali_id = kwargs.get("id")
            updates = kwargs.get("updates")
            if not updates:
                updates = {k: v for k, v in kwargs.items() if k != "id"}
            return self._update_kundali(kundalis, kundali_id, updates), kundalis, active_id
        if tool_name == "delete_kundali":
            return self._delete_kundali(kundalis, kwargs.get("id")), kundalis, active_id
        if tool_name == "select_kundali":
            return self._select_kundali(kundalis, kwargs.get("id")), kundalis, kwargs.get("id")
        raise ValueError(f"Unknown tool: {tool_name}")

    def _list_kundalis(self, kundalis: List[Dict[str, Any]]) -> Dict[str, Any]:
        summary = []
        for k in kundalis:
            summary.append({
                "id": k.get("id"),
                "name": k.get("name"),
                "birthDate": k.get("birthDate"),
                "birthTime": k.get("birthTime"),
                "birthPlace": k.get("birthPlace"),
                "gender": k.get("gender")
            })
        return {"kundalis": summary, "count": len(summary)}

    def _get_kundali(self, kundalis: List[Dict[str, Any]], kundali_id: Optional[str]) -> Dict[str, Any]:
        if not kundali_id:
            raise ValueError("id is required")
        for k in kundalis:
            if k.get("id") == kundali_id:
                return {"kundali": k}
        raise ValueError("Kundali not found")

    def _create_kundali(self, kundalis: List[Dict[str, Any]], profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not profile:
            raise ValueError("profile is required")
        normalized = _normalize_profile(profile)
        missing = _validate_profile(normalized)
        if missing:
            raise ValueError(f"Missing fields: {', '.join(missing)}")

        kundalis.append(normalized)
        return {"kundali": normalized, "message": "Kundali created"}

    def _update_kundali(
        self,
        kundalis: List[Dict[str, Any]],
        kundali_id: Optional[str],
        updates: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not kundali_id:
            raise ValueError("id is required")
        if not updates:
            raise ValueError("updates is required")
        normalized = _normalize_profile(updates)

        for item in kundalis:
            if item.get("id") == kundali_id:
                item.update({key: val for key, val in normalized.items() if val is not None})
                return {"kundali": item, "message": "Kundali updated"}
        raise ValueError("Kundali not found")

    def _delete_kundali(self, kundalis: List[Dict[str, Any]], kundali_id: Optional[str]) -> Dict[str, Any]:
        if not kundali_id:
            raise ValueError("id is required")
        for idx, k in enumerate(kundalis):
            if k.get("id") == kundali_id:
                removed = kundalis.pop(idx)
                return {"kundali": removed, "message": "Kundali deleted"}
        raise ValueError("Kundali not found")

    def _select_kundali(self, kundalis: List[Dict[str, Any]], kundali_id: Optional[str]) -> Dict[str, Any]:
        if not kundali_id:
            raise ValueError("id is required")
        for k in kundalis:
            if k.get("id") == kundali_id:
                return {"active_id": kundali_id, "kundali": k}
        raise ValueError("Kundali not found")
