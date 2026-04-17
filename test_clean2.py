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

text = """```json
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

```json
{
  "action": "git_status",
  "args": {}
}
```

```json
{
  "action": "git_branches",
  "args": {}
}
```

```json
{
  "action": "git_log",
  "args": {
    "limit": 10
  }
}
```

```json
{
  "action": "search_files",
  "args": {
    "pattern": "build.gradle",
    "path": "F:\\Sketchware-Pro"
  }
}
```

```json
{
  "action": "search_files",
  "args": {
    "pattern": "settings.gradle",
    "path": "F:\\Sketchware-Pro"
  }
```"""

print("Original length:", len(text))
cleaned = _clean_response_text(text)
print("Cleaned length:", len(cleaned))
print("Cleaned text:\n", cleaned)
