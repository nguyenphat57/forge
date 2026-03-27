from __future__ import annotations

import io
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path


def configure_stdio() -> None:
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name)
        encoding = getattr(stream, "encoding", None)
        if encoding and encoding.lower() != "utf-8":
            setattr(sys, name, io.TextIOWrapper(stream.buffer, encoding="utf-8"))


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.casefold()
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_choice_token(value: str) -> str:
    normalized = normalize_text(value)
    normalized = normalized.replace("_", "-")
    normalized = re.sub(r"\s+", "-", normalized)
    return normalized


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return slug or "artifact"


def timestamp_slug() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def extract_backtick_items(text: str) -> list[str]:
    return re.findall(r"`([^`]+)`", text)


def excerpt_text(text: str, *, max_lines: int = 8, max_chars: int = 500) -> str:
    trimmed = text.strip()
    if not trimmed:
        return ""
    lines = trimmed.splitlines()[:max_lines]
    joined = "\n".join(lines)
    if len(joined) > max_chars:
        return joined[: max_chars - 3].rstrip() + "..."
    return joined


def read_text(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def default_artifact_dir(output_dir: str | None, artifact_type: str) -> Path:
    base_dir = Path(output_dir).resolve() if output_dir else Path.cwd()
    return base_dir / ".forge-artifacts" / artifact_type
