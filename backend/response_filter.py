"""
Response Filter Module

This module provides comprehensive filtering and cleaning of AI responses
to remove unwanted content like YouTube links, tutorials, and other
non-essential text that detracts from agentic behavior.
"""

import re
from typing import Tuple, Optional

# ============================================================================
# URL PATTERNS TO FILTER
# ============================================================================

# YouTube and video links
YOUTUBE_PATTERNS = [
    r'https?://(?:www\.)?youtube\.com/watch\?v=[^\s\]\)]+',
    r'https?://(?:www\.)?youtu\.be/[^\s\]\)]+',
    r'https?://(?:www\.)?youtube\.com/embed/[^\s\]\)]+',
    r'https?://(?:www\.)?youtube\.com/v/[^\s\]\)]+',
    r'https?://(?:www\.)?vimeo\.com/[^\s\]\)]+',
    r'https?://(?:www\.)?dailymotion\.com/[^\s\]\)]+',
    # Google internal content URLs
    r'https?://googleusercontent\.com/youtube_content/\d+',
]

# External tutorial/reference links
EXTERNAL_LINK_PATTERNS = [
    r'https?://(?:www\.)?medium\.com/[^\s\]\)]+',
    r'https?://(?:www\.)?dev\.to/[^\s\]\)]+',
    r'https?://(?:www\.)?stackoverflow\.com/[^\s\]\)]+',
    r'https?://(?:www\.)?w3schools\.com/[^\s\]\)]+',
    r'https?://(?:www\.)?tutorials?point\.com/[^\s\]\)]+',
    r'https?://(?:www\.)?geeksforgeeks\.org/[^\s\]\)]+',
]

# ============================================================================
# TEXT PATTERNS TO FILTER
# ============================================================================

# Tutorial/educational phrasing that's not needed
TUTORIAL_PATTERNS = [
    r"here'?s?\s+(?:a\s+)?(?:step-by-step\s+)?(?:guide|tutorial|how)\s+(?:to|on)\s+[^.!?]+[.!?]",
    r"let me (?:show|explain|teach|walk) you (?:how|through|step)[^.!?]+[.!?]",
    r"in this (?:tutorial|guide|lesson)[^.!?]+[.!?]",
    r"first,?\s+let'?s?\s+understand\s+[^.!?]+[.!?]",
    r"before we (?:start|begin|proceed)[^.!?]+[.!?]",
    r"you (?:can|might|may) want to\s+(?:check out|watch|read|see)\s+[^.!?]+[.!?]",
    r"for more (?:information|details|examples),?\s+(?:see|visit|check|refer)[^.!?]+[.!?]",
    r"i recommend (?:watching|reading|checking)\s+[^.!?]+[.!?]",
]

# Excessive politeness/filler that reduces conciseness
FILLER_PATTERNS = [
    r"(?:^|\n)(?:certainly|sure|absolutely|of course)[,!.]?\s*",
    r"(?:^|\n)i'?d be (?:happy|glad|delighted) to\s+",
    r"(?:^|\n)great (?:question|idea|choice)[.!]?\s*",
    r"no problem[,!]?\s*",
    r"you'?re? welcome[,!]?\s*",
]

# Incomplete markdown link patterns (often from failed formatting)
BROKEN_LINK_PATTERNS = [
    r'\[([^\]]+)\]\([^)]*\)',  # Markdown links - will be handled specially
    r'<a\s+href=["\'][^"\']*["\'][^>]*>[^<]*</a>',  # HTML links
]

# ============================================================================
# CONTENT CLEANUP PATTERNS
# ============================================================================

# Multiple newlines cleanup
MULTIPLE_NEWLINES = r'\n{3,}'

# Multiple spaces cleanup
MULTIPLE_SPACES = r'[ \t]{2,}'

# Empty list items
EMPTY_LIST_ITEMS = r'^[\s]*[-*+]\s*$'

# Trailing/leading whitespace per line
LINE_WHITESPACE = r'^[ \t]+|[ \t]+$'


class ResponseFilter:
    """
    Filters and cleans AI responses for better agentic behavior.

    Features:
    - Removes YouTube and external video links
    - Filters tutorial-style phrasing
    - Cleans up excessive whitespace
    - Maintains tool call integrity
    """

    def __init__(self, aggressive: bool = False):
        """
        Initialize the filter.

        Args:
            aggressive: If True, applies more aggressive filtering
        """
        self.aggressive = aggressive
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        # URL patterns
        self.youtube_regex = re.compile(
            '|'.join(YOUTUBE_PATTERNS),
            re.IGNORECASE
        )
        self.external_link_regex = re.compile(
            '|'.join(EXTERNAL_LINK_PATTERNS),
            re.IGNORECASE
        )

        # Text patterns
        self.tutorial_regex = re.compile(
            '|'.join(TUTORIAL_PATTERNS),
            re.IGNORECASE | re.MULTILINE
        )
        self.filler_regex = re.compile(
            '|'.join(FILLER_PATTERNS),
            re.IGNORECASE | re.MULTILINE
        )

        # Cleanup patterns
        self.multiple_newlines_regex = re.compile(MULTIPLE_NEWLINES)
        self.multiple_spaces_regex = re.compile(MULTIPLE_SPACES)
        self.empty_list_regex = re.compile(EMPTY_LIST_ITEMS, re.MULTILINE)

        # Tool call detection (to preserve)
        self.tool_call_regex = re.compile(
            r'```json\s*\{[^`]*?"action"\s*:[^`]*?\}\s*```',
            re.DOTALL
        )
        self.inline_tool_regex = re.compile(
            r'\{\s*"action"\s*:\s*"[^"]+"\s*,\s*"args"\s*:\s*\{[^}]*\}\s*\}',
            re.DOTALL
        )

    def filter(self, text: str) -> str:
        """
        Apply all filters to the text.

        Args:
            text: The raw AI response text

        Returns:
            Cleaned text with unwanted content removed
        """
        if not text:
            return ""

        # Preserve tool calls first
        tool_calls = self._extract_tool_calls(text)

        # Apply filters
        cleaned = self._remove_urls(text)
        cleaned = self._remove_tutorial_phrases(cleaned)

        if self.aggressive:
            cleaned = self._remove_filler(cleaned)

        cleaned = self._clean_whitespace(cleaned)

        # Restore tool calls
        cleaned = self._restore_tool_calls(cleaned, tool_calls)

        return cleaned.strip()

    def _extract_tool_calls(self, text: str) -> list:
        """Extract tool calls to preserve them during filtering."""
        calls = []

        # Extract ```json blocks
        for match in self.tool_call_regex.finditer(text):
            calls.append(match.group(0))

        # Extract inline tool calls
        for match in self.inline_tool_regex.finditer(text):
            if match.group(0) not in calls:
                calls.append(match.group(0))

        return calls

    def _restore_tool_calls(self, text: str, tool_calls: list) -> str:
        """Ensure tool calls are present in the output."""
        for call in tool_calls:
            if call not in text:
                # Append if missing (shouldn't normally happen)
                text = text.rstrip() + "\n\n" + call
        return text

    def _remove_urls(self, text: str) -> str:
        """Remove YouTube and external links."""
        # Remove YouTube links
        cleaned = self.youtube_regex.sub('', text)

        # Remove external tutorial links
        cleaned = self.external_link_regex.sub('', cleaned)

        # Clean up any resulting empty markdown links
        # [text]() or [](url) patterns
        cleaned = re.sub(r'\[([^\]]*)\]\(\s*\)', r'\1', cleaned)
        cleaned = re.sub(r'\[\s*\]\([^)]*\)', '', cleaned)

        # Clean up sentences that now end with "check out" or "visit" without a link
        cleaned = re.sub(
            r'(?:check out|visit|see|watch|read)\s*[.!?]?\s*$',
            '.',
            cleaned,
            flags=re.IGNORECASE | re.MULTILINE
        )

        return cleaned

    def _remove_tutorial_phrases(self, text: str) -> str:
        """Remove tutorial-style phrasing."""
        return self.tutorial_regex.sub('', text)

    def _remove_filler(self, text: str) -> str:
        """Remove filler words and excessive politeness."""
        return self.filler_regex.sub('', text)

    def _clean_whitespace(self, text: str) -> str:
        """Clean up excessive whitespace."""
        # Remove multiple consecutive newlines
        cleaned = self.multiple_newlines_regex.sub('\n\n', text)

        # Clean up multiple spaces
        cleaned = self.multiple_spaces_regex.sub(' ', cleaned)

        # Remove empty list items
        cleaned = self.empty_list_regex.sub('', cleaned)

        # Strip each line
        lines = cleaned.split('\n')
        lines = [line.strip() for line in lines]

        # Remove leading empty lines
        while lines and not lines[0]:
            lines.pop(0)

        # Remove trailing empty lines
        while lines and not lines[-1]:
            lines.pop()

        return '\n'.join(lines)


class ThoughtFilter:
    """
    Filters and extracts thinking/reasoning from AI responses.
    Separates internal thoughts from user-facing content.
    """

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile thought extraction patterns."""
        # Various thinking block patterns
        self.think_block_regex = re.compile(
            r'<think>(.*?)</think>',
            re.DOTALL | re.IGNORECASE
        )
        self.thinking_block_regex = re.compile(
            r'\[Thinking\](.*?)\[/Thinking\]',
            re.DOTALL | re.IGNORECASE
        )
        self.internal_block_regex = re.compile(
            r'<internal>(.*?)</internal>',
            re.DOTALL | re.IGNORECASE
        )

        # Inline thinking patterns (lines starting with *)
        self.inline_thought_regex = re.compile(
            r'^\*(?:Thinking|Internal|Reasoning)[:\s].*$',
            re.MULTILINE | re.IGNORECASE
        )

    def extract_thoughts(self, text: str) -> Tuple[Optional[str], str]:
        """
        Extract thoughts from text.

        Args:
            text: The AI response text

        Returns:
            Tuple of (thoughts_content, clean_text)
        """
        if not text:
            return None, ""

        thoughts = []
        clean_text = text

        # Extract <think> blocks
        for match in self.think_block_regex.finditer(text):
            thoughts.append(match.group(1).strip())
        clean_text = self.think_block_regex.sub('', clean_text)

        # Extract [Thinking] blocks
        for match in self.thinking_block_regex.finditer(clean_text):
            thoughts.append(match.group(1).strip())
        clean_text = self.thinking_block_regex.sub('', clean_text)

        # Extract <internal> blocks
        for match in self.internal_block_regex.finditer(clean_text):
            thoughts.append(match.group(1).strip())
        clean_text = self.internal_block_regex.sub('', clean_text)

        # Extract inline thoughts
        for match in self.inline_thought_regex.finditer(clean_text):
            thoughts.append(match.group(0).strip())
        clean_text = self.inline_thought_regex.sub('', clean_text)

        # Combine thoughts
        combined_thoughts = '\n\n'.join(thoughts) if thoughts else None

        return combined_thoughts, clean_text.strip()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global filter instances
_response_filter = ResponseFilter(aggressive=False)
_aggressive_filter = ResponseFilter(aggressive=True)
_thought_filter = ThoughtFilter()


def clean_response(text: str, aggressive: bool = False) -> str:
    """
    Clean an AI response.

    Args:
        text: Raw AI response
        aggressive: Whether to apply aggressive filtering

    Returns:
        Cleaned text
    """
    if aggressive:
        return _aggressive_filter.filter(text)
    return _response_filter.filter(text)


def extract_and_clean(text: str) -> Tuple[Optional[str], str]:
    """
    Extract thoughts and clean response in one pass.

    Args:
        text: Raw AI response

    Returns:
        Tuple of (thoughts, cleaned_text)
    """
    thoughts, clean_text = _thought_filter.extract_thoughts(text)
    clean_text = clean_response(clean_text)
    return thoughts, clean_text


def remove_youtube_links(text: str) -> str:
    """Quick function to just remove YouTube links."""
    return _response_filter.youtube_regex.sub('', text)


def remove_external_links(text: str) -> str:
    """Remove external tutorial/reference links."""
    text = _response_filter.youtube_regex.sub('', text)
    return _response_filter.external_link_regex.sub('', text)
