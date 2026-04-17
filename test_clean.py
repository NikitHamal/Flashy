import re

def _clean_response_text(text: str, tool_call_raw: str = None) -> str:
    if not text:
        return ""

    cleaned = text

    # Remove specific tool call match
    if tool_call_raw:
        cleaned = cleaned.replace(tool_call_raw, "").strip()

    # Remove orphaned JSON blocks that look like tool calls
    json_block_pattern = (
        r'```json\s*\{[^`]*?"(?:action|tool|name)"\s*:[^`]*?\}\s*```'
    )
    cleaned = re.sub(json_block_pattern, "", cleaned, flags=re.DOTALL).strip()
    return cleaned

text = """
```json
{
  "action": "get_file_tree",
  "args": {
    "path": "F:\\Sketchware-Pro",
    "max_depth": 2
  }
}
```

```json
{
  "action": "get_dependencies",
  "args": {}
}
```
"""

print(repr(_clean_response_text(text)))
