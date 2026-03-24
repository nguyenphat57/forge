from __future__ import annotations

import io
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Iterable


ROOT_DIR = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT_DIR / "data" / "orchestrator-registry.json"

STOP_TOKENS = {
    "skill",
    "skills",
    "local",
    "global",
    "agent",
    "agents",
    "pro",
    "max",
    "core",
    "workspace",
}

TOKEN_ALIASES = {
    "react": {"react", "tsx", "jsx", "component", "hook", "web", "ui"},
    "vite": {"vite"},
    "typescript": {"typescript", "typed", "type-safe", "ts"},
    "capacitor": {"capacitor", "cap sync", "native shell", "mobile shell"},
    "android": {"android", "gradle", "manifest", "background", "resume", "device", "service"},
    "native": {"native", "plugin", "bridge", "foreground"},
    "bridge": {"bridge", "plugin", "register", "invoke"},
    "supabase": {"supabase", "rls", "rpc", "policy", "migration", "edge function", "sql"},
    "postgres": {"postgres", "sql", "migration", "query"},
    "dexie": {"dexie", "indexeddb", "offline", "outbox", "sync"},
    "offline": {"offline", "retry", "recovery", "outbox", "sync"},
    "sync": {"sync", "retry", "recovery", "outbox"},
    "cloudflare": {"cloudflare", "wrangler", "spa", "deploy", "workers", "fallback"},
    "wrangler": {"wrangler", "deploy", "fallback"},
    "onesignal": {"onesignal", "push", "notification", "token"},
    "push": {"push", "notification", "click", "deeplink", "route"},
    "receipt": {"receipt", "bill", "invoice", "print", "printer"},
    "printing": {"print", "printer", "receipt"},
    "ui": {"ui", "ux", "layout", "screen", "mockup", "design"},
    "ux": {"ux", "interaction", "layout", "flow", "design"},
}


def configure_stdio() -> None:
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name)
        encoding = getattr(stream, "encoding", None)
        if encoding and encoding.lower() != "utf-8":
            setattr(sys, name, io.TextIOWrapper(stream.buffer, encoding="utf-8"))


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.casefold()
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return slug or "artifact"


def timestamp_slug() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def extract_backtick_items(text: str) -> list[str]:
    return re.findall(r"`([^`]+)`", text)


def read_text(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def score_keywords(text: str, keywords: Iterable[str]) -> int:
    score = 0
    seen: set[str] = set()
    for keyword in keywords:
        normalized = normalize_text(keyword)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        if keyword_in_text(normalized, text):
            score += 1
    return score


def keyword_in_text(keyword: str, text: str) -> bool:
    if not keyword:
        return False
    if any(char in keyword for char in ("/", ".", "_")):
        return keyword in text
    pattern = r"(?<!\w){0}(?!\w)".format(re.escape(keyword))
    return re.search(pattern, text) is not None


def extract_skill_names(text: str) -> list[str]:
    seen: list[str] = []
    for item in extract_backtick_items(text):
        candidate = item.strip()
        if not candidate:
            continue
        if "/" in candidate or "\\" in candidate or "." in candidate:
            continue
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", candidate):
            continue
        if candidate not in seen:
            seen.append(candidate)
    return seen


def skill_aliases(skill_name: str) -> set[str]:
    aliases: set[str] = set()
    for token in skill_name.split("-"):
        token = token.strip().lower()
        if not token or token in STOP_TOKENS:
            continue
        aliases.add(token)
        aliases.update(TOKEN_ALIASES.get(token, set()))
    return aliases


def detect_runtimes(repo_signals: Iterable[str], registry: dict) -> list[str]:
    haystack = normalize_text(" ".join(repo_signals))
    detected: list[str] = []
    for runtime, patterns in registry.get("runtime_hints", {}).items():
        if any(normalize_text(pattern) in haystack for pattern in patterns):
            detected.append(runtime)
    return detected


def default_artifact_dir(output_dir: str | None, artifact_type: str) -> Path:
    base_dir = Path(output_dir).resolve() if output_dir else Path.cwd()
    return base_dir / ".forge-artifacts" / artifact_type
