"""Utility to reorder provider <option> entries in frontend/index.html."""
from pathlib import Path

INDEX = Path("frontend/index.html")

FIRST_ORDER = [
    ("qwen", "Qwen (Alibaba)"),
    ("deepinfra", "DeepInfra"),
    ("gemini", "Google Gemini (Web)"),
    ("grok", "Grok (xAI)"),
    ("zai-free", "Z.ai Free (No Auth)"),
    ("kimi", "Kimi (Moonshot)"),
    ("zai", "Z.ai (Token)"),
    ("glm", "GLM (Zhipu)"),
    ("airforce", "Airforce"),
    ("gradient", "Gradient Network"),
    ("chat2api", "Chat2API (Local)"),
    ("lmarena", "LMArena (Free Models)"),
]

SECOND_ORDER = [
    ("qwen", "Qwen"),
    ("deepinfra", "DeepInfra"),
    ("gemini", "Google Gemini"),
    ("grok", "Grok (xAI)"),
    ("zai-free", "Z.ai Free"),
    ("kimi", "Kimi"),
    ("zai", "Z.ai (Token)"),
    ("glm", "GLM (Zhipu)"),
    ("airforce", "Airforce"),
    ("gradient", "Gradient Network"),
    ("lmarena", "LMArena"),
]


def append_options(output: list[str], options: list[tuple[str, str]], indent: str) -> None:
    for value, label in options:
        output.append(f'{indent}<option value="{value}">{label}</option>\n')


def reorder() -> None:
    lines = INDEX.read_text(encoding="utf-8").splitlines(keepends=True)
    output: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        output.append(line)
        if 'id="settings-active-provider"' in line:
            i += 1
            indent = "" if i >= len(lines) else lines[i][: len(lines[i]) - len(lines[i].lstrip())]
            while i < len(lines) and "<option" in lines[i]:
                i += 1
            append_options(output, FIRST_ORDER, indent or "                                ")
            continue
        if 'id="agent-provider-selector"' in line:
            i += 1
            indent = "" if i >= len(lines) else lines[i][: len(lines[i]) - len(lines[i].lstrip())]
            while i < len(lines) and "<option" in lines[i]:
                i += 1
            append_options(output, SECOND_ORDER, indent or "                                ")
            continue
        i += 1

    INDEX.write_text("".join(output), encoding="utf-8")


if __name__ == "__main__":
    reorder()
    print("Done")
