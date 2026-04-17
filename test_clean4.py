import re

def _clean_response_text(text: str, tool_call_raw: str = None) -> str:
    if not text:
        return ""

    cleaned = text

    if tool_call_raw:
        cleaned = cleaned.replace(tool_call_raw, "").strip()

    json_block_pattern = (
        r'```json\s*\{[^`]*?"(?:action|tool|name)"\s*:[^`]*?\}\s*```'
    )
    cleaned = re.sub(json_block_pattern, "", cleaned, flags=re.DOTALL).strip()

    # Remove incomplete JSON blocks at the end of the text
    incomplete_pattern = r'```json\s*\{[^`]*?(?:"action"|"tool"|"name")[^`]*$'
    cleaned = re.sub(incomplete_pattern, "", cleaned, flags=re.DOTALL).strip()

    return cleaned

text = """```json
{
  "action": "search_files",
  "args": {
    "pattern": "settings.gradle",
    "path": "F:\\Sketchware-Pro"
  }"""

print("Original length:", len(text))
cleaned = _clean_response_text(text)
print("Cleaned length:", len(cleaned))
print("Cleaned text:\n", cleaned)
