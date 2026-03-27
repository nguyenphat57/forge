from __future__ import annotations

import io
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path


MOJIBAKE_FRAGMENTS = (
    "\u00c3",
    "\u00c2",
    "\u00c4",
    "\u00c6",
    "\u00e1\u00bb",
    "\u00e1\u00ba",
    "\u00e2\u20ac",
)

VIETNAMESE_REPAIR_HINTS = frozenset(
    "\u0103\u00e2\u0111\u00ea\u00f4\u01a1\u01b0"
    "\u00e1\u00e0\u1ea3\u00e3\u1ea1\u1eaf\u1eb1\u1eb3\u1eb5\u1eb7\u1ea5\u1ea7\u1ea9\u1eab\u1ead"
    "\u00e9\u00e8\u1ebb\u1ebd\u1eb9\u1ebf\u1ec1\u1ec3\u1ec5\u1ec7"
    "\u00ed\u00ec\u1ec9\u0129\u1ecb"
    "\u00f3\u00f2\u1ecf\u00f5\u1ecd\u1ed1\u1ed3\u1ed5\u1ed7\u1ed9\u1edb\u1edd\u1edf\u1ee1\u1ee3"
    "\u00fa\u00f9\u1ee7\u0169\u1ee5\u1ee9\u1eeb\u1eed\u1eef\u1ef1"
    "\u00fd\u1ef3\u1ef7\u1ef9\u1ef5"
    "\u0102\u00c2\u0110\u00ca\u00d4\u01a0\u01af"
    "\u00c1\u00c0\u1ea2\u00c3\u1ea0\u1eae\u1eb0\u1eb2\u1eb4\u1eb6\u1ea4\u1ea6\u1ea8\u1eaa\u1eac"
    "\u00c9\u00c8\u1eba\u1ebc\u1eb8\u1ebe\u1ec0\u1ec2\u1ec4\u1ec6"
    "\u00cd\u00cc\u1ec8\u0128\u1eca"
    "\u00d3\u00d2\u1ece\u00d5\u1ecc\u1ed0\u1ed2\u1ed4\u1ed6\u1ed8\u1eda\u1edc\u1ede\u1ee0\u1ee2"
    "\u00da\u00d9\u1ee6\u0168\u1ee4\u1ee8\u1eea\u1eec\u1eee\u1ef0"
    "\u00dd\u1ef2\u1ef6\u1ef8\u1ef4"
)


def configure_stdio() -> None:
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name)
        encoding = getattr(stream, "encoding", None)
        if encoding and encoding.lower() != "utf-8":
            setattr(sys, name, io.TextIOWrapper(stream.buffer, encoding="utf-8"))


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.replace("đ", "d").replace("Đ", "D")
    text = text.casefold()
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_choice_token(value: str) -> str:
    normalized = normalize_text(value)
    normalized = normalized.replace("_", "-")
    normalized = re.sub(r"\s+", "-", normalized)
    return normalized


def mojibake_artifact_score(value: str) -> int:
    return sum(value.count(fragment) for fragment in MOJIBAKE_FRAGMENTS) + (value.count("\ufffd") * 4)


def vietnamese_character_score(value: str) -> int:
    return sum(1 for char in value if char in VIETNAMESE_REPAIR_HINTS)


def repair_mojibake_text(value: str) -> str:
    if not value or not any(fragment in value for fragment in MOJIBAKE_FRAGMENTS):
        return value

    try:
        candidate = value.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value

    if candidate == value:
        return value

    original_score = mojibake_artifact_score(value)
    candidate_score = mojibake_artifact_score(candidate)
    if candidate_score > original_score:
        return value
    if candidate_score == original_score and vietnamese_character_score(candidate) <= vietnamese_character_score(value):
        return value
    return candidate


def repair_text_artifacts(value: object) -> object:
    if isinstance(value, str):
        return repair_mojibake_text(value)
    if isinstance(value, list):
        return [repair_text_artifacts(item) for item in value]
    if isinstance(value, dict):
        return {
            key: repair_text_artifacts(item)
            for key, item in value.items()
        }
    return value


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
