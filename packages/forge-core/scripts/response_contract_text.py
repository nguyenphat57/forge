from __future__ import annotations

import re
from typing import Iterable

from skill_routing import keyword_in_text
from text_utils import normalize_text


def strip_markdown_code(text: str) -> str:
    stripped = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    stripped = re.sub(r"`[^`]*`", " ", stripped)
    return stripped


def prose_lines(text: str) -> list[str]:
    cleaned: list[str] = []
    for raw_line in strip_markdown_code(text).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^(?:[-*+]\s+|\d+\.\s+|>\s+)", "", line)
        if line:
            cleaned.append(line)
    return cleaned


def collect_phrase_hits(text: str, phrases: Iterable[str]) -> list[str]:
    normalized_text = normalize_text(text)
    hits: list[str] = []
    seen: set[str] = set()
    for phrase in phrases:
        normalized_phrase = normalize_text(phrase)
        if not normalized_phrase or normalized_phrase in seen:
            continue
        seen.add(normalized_phrase)
        if keyword_in_text(normalized_phrase, normalized_text):
            hits.append(phrase)
    return hits
