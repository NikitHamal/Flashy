"""Rename GeminiService → LLMService across the entire codebase."""
import os
import re

# Files to update
FILES = [
    'backend/app.py',
    'backend/gemini_service.py',
    'backend/agent.py',
    'backend/routers/git_routes.py',
    'backend/routers/config.py',
    'backend/routers/chat.py',
]

for filepath in FILES:
    if not os.path.exists(filepath):
        print(f'Skipping {filepath} (not found)')
        continue

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Rename imports
    content = content.replace('from .gemini_service import GeminiService',
                              'from .llm_service import LLMService')
    content = content.replace('from ..gemini_service import GeminiService',
                              'from ..llm_service import LLMService')

    # Rename class instantiation
    content = content.replace('gemini_service = GeminiService()',
                              'llm_service = LLMService()')

    # Rename app.state references
    content = content.replace('app.state.gemini_service', 'app.state.llm_service')

    # Rename variable references (but NOT inside strings/comments that describe old names)
    content = content.replace('gemini_service.', 'llm_service.')
    content = content.replace('request.app.state.gemini_service', 'request.app.state.llm_service')

    # Rename class definition
    content = content.replace('class GeminiService:', 'class LLMService:')

    # Rename log prefixes
    content = content.replace('[GeminiService]', '[LLMService]')

    # Update comments
    content = content.replace('GeminiService', 'LLMService')
    content = content.replace('gemini_service', 'llm_service')

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated: {filepath}')
    else:
        print(f'No changes: {filepath}')

# Rename the file itself
old_path = 'backend/gemini_service.py'
new_path = 'backend/llm_service.py'
if os.path.exists(old_path):
    os.rename(old_path, new_path)
    print(f'Renamed: {old_path} → {new_path}')

print('\nDone. All GeminiService references renamed to LLMService.')
