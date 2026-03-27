from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

from text_utils import extract_backtick_items, normalize_text, read_text


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


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def current_bundle_skill_name() -> str:
    skill_match = re.search(
        r"(?m)^name:\s*['\"]?([a-z0-9][a-z0-9-]*)['\"]?\s*$",
        read_text(ROOT_DIR / "SKILL.md"),
    )
    if skill_match:
        return skill_match.group(1)

    manifest_path = ROOT_DIR / "BUILD-MANIFEST.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        package_name = manifest.get("package")
        if isinstance(package_name, str) and package_name:
            return package_name

    return ROOT_DIR.name


def reserved_skill_names() -> set[str]:
    names = {ROOT_DIR.name, current_bundle_skill_name()}
    return {name for name in names if name}


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
