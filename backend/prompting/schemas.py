from typing import Any, Dict

from .schemas_primary import TOOL_SCHEMAS_PRIMARY
from .schemas_extended import TOOL_SCHEMAS_EXTENDED

TOOL_SCHEMAS: Dict[str, Dict[str, Any]] = {**TOOL_SCHEMAS_PRIMARY, **TOOL_SCHEMAS_EXTENDED}
