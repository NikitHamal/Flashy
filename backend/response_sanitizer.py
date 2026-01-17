"""
Response Sanitizer

Centralized helpers to remove unwanted artifacts from model output.
Focuses on stripping YouTube links and tightening spacing while
preserving meaningful text content.
"""

from __future__ import annotations

import re
from typing import Optional


YOUTUBE_URL_PATTERN = re.compile(
    r'https?://(?:www\.)?(?:youtube\.com|youtu\.be)/[^\s)]+',
    flags=re.IGNORECASE
)
GOOGLE_CONTENT_PATTERN = re.compile(
    r'https?://googleusercontent\.com/youtube_content/\d+',
    flags=re.IGNORECASE
)
YOUTUBE_MARKDOWN_PATTERN = re.compile(
    r'\[([^\]]+)\]\((https?://(?:www\.)?(?:youtube\.com|youtu\.be)/[^\s)]+)\)',
    flags=re.IGNORECASE
)


def sanitize_response_text(text: Optional[str]) -> str:
    """Remove unwanted YouTube links and normalize spacing."""
    if not text:
        return ""

    cleaned = text
    cleaned = YOUTUBE_MARKDOWN_PATTERN.sub(r'\1', cleaned)
    cleaned = YOUTUBE_URL_PATTERN.sub('', cleaned)
    cleaned = GOOGLE_CONTENT_PATTERN.sub('', cleaned)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()
