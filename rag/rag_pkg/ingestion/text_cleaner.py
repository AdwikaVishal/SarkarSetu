"""Text cleaning and normalization.

Removes irrelevant whitespace, normalizes line breaks, removes repeated
headers/footers when identifiable, and preserves meaningful numbering,
section headings, eligibility conditions, and tables.
"""

from __future__ import annotations

import re
from collections import Counter

from rag.config.logging_config import get_logger

logger = get_logger("text_cleaner")

# Match page-number-like standalone tokens and common header/footer noise.
_HEADER_FOOTER_PATTERNS = [
    re.compile(r"^\s*Page\s+\d+\s*$", re.IGNORECASE),
    re.compile(r"^\s*\d+\s*/\s*\d+\s*$"),
    re.compile(r"^\s*Government of India\s*$", re.IGNORECASE),
    re.compile(r"^\s*Ministry of.*\s*$", re.IGNORECASE),
]


def normalize_whitespace(text: str) -> str:
    """Collapse runs of whitespace while preserving paragraph breaks."""
    # Replace Windows/Mac line breaks with \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse horizontal whitespace (spaces/tabs) within a line
    lines = text.split("\n")
    cleaned_lines = [re.sub(r"[ \t]+", " ", line).rstrip() for line in lines]
    # Collapse 3+ consecutive blank lines to a single blank line
    result = "\n".join(cleaned_lines)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def _identify_repeated_lines(lines: list[str], min_pages: int = 3) -> set[str]:
    """Return lines that appear on many pages (likely headers/footers)."""
    if len(lines) < min_pages:
        return set()
    counts = Counter(lines)
    total = len(lines)
    repeated = {
        line
        for line, count in counts.items()
        if count >= min_pages and count >= total * 0.5 and line.strip()
    }
    return repeated


def remove_repeated_headers_footers(
    pages_text: list[tuple[int, str]],
) -> list[tuple[int, str]]:
    """Remove lines repeated across most pages (likely headers/footers).

    Args:
        pages_text: List of (page_number, text) tuples.

    Returns:
        List of (page_number, cleaned_text) tuples.
    """
    all_lines = []
    page_line_lists: list[list[str]] = []
    for _, text in pages_text:
        lines = text.split("\n")
        page_line_lists.append(lines)
        all_lines.extend(lines)

    repeated = _identify_repeated_lines(all_lines)
    if not repeated:
        return list(pages_text)

    cleaned: list[tuple[int, str]] = []
    for (page_number, _), lines in zip(pages_text, page_line_lists):
        kept = [
            line
            for line in lines
            if line not in repeated
            and not _looks_like_header_footer(line)
        ]
        cleaned.append((page_number, "\n".join(kept).strip()))
    return cleaned


def _looks_like_header_footer(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    for pattern in _HEADER_FOOTER_PATTERNS:
        if pattern.match(stripped):
            return True
    # Standalone short page number
    if re.fullmatch(r"\d{1,4}", stripped):
        return True
    return False


def clean_text(text: str) -> str:
    """Clean a single block of text: normalize whitespace only.

    Does not remove legal or numeric information.
    """
    return normalize_whitespace(text)


def clean_pages(
    pages_text: list[tuple[int, str]],
    remove_repeated: bool = True,
) -> list[tuple[int, str]]:
    """Clean a list of (page_number, text) pages.

    Args:
        pages_text: List of (page_number, raw_text).
        remove_repeated: Whether to remove repeated headers/footers.

    Returns:
        List of (page_number, cleaned_text).
    """
    cleaned = [(page, normalize_whitespace(text)) for page, text in pages_text]
    if remove_repeated:
        cleaned = remove_repeated_headers_footers(cleaned)
    return cleaned
