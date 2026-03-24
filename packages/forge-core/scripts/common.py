from __future__ import annotations

import io
import json
import re
import sys
import unicodedata
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Iterable


ROOT_DIR = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT_DIR / "data" / "orchestrator-registry.json"
PREFERENCES_SCHEMA_PATH = ROOT_DIR / "data" / "preferences-schema.json"

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

PREFERENCE_ALIASES = {
    "technical_level": {
        "newbie": "newbie",
        "beginner": "newbie",
        "basic": "basic",
        "default": "basic",
        "standard": "basic",
        "intermediate": "basic",
        "technical": "technical",
        "developer": "technical",
        "advanced": "technical",
        "expert": "technical",
    },
    "detail_level": {
        "concise": "concise",
        "brief": "concise",
        "short": "concise",
        "balanced": "balanced",
        "default": "balanced",
        "normal": "balanced",
        "standard": "balanced",
        "detailed": "detailed",
        "detail": "detailed",
        "verbose": "detailed",
        "deep": "detailed",
        "thorough": "detailed",
    },
    "autonomy_level": {
        "guided": "guided",
        "low": "guided",
        "careful": "guided",
        "balanced": "balanced",
        "default": "balanced",
        "standard": "balanced",
        "autonomous": "autonomous",
        "proactive": "autonomous",
        "high": "autonomous",
        "independent": "autonomous",
    },
    "personality": {
        "default": "default",
        "mentor": "mentor",
        "strict-coach": "strict-coach",
        "strict_coach": "strict-coach",
        "strict coach": "strict-coach",
    },
}

TECHNICAL_STYLE = {
    "newbie": {
        "terminology_mode": "translated",
        "term_explanation_policy": "always",
        "acronym_policy": "avoid",
        "step_granularity": "small",
    },
    "basic": {
        "terminology_mode": "mixed",
        "term_explanation_policy": "first-use",
        "acronym_policy": "define-on-first-use",
        "step_granularity": "medium",
    },
    "technical": {
        "terminology_mode": "standard",
        "term_explanation_policy": "on-request",
        "acronym_policy": "standard",
        "step_granularity": "compact",
    },
}

DETAIL_STYLE = {
    "concise": {
        "response_verbosity": "concise",
        "context_depth": "minimal",
        "option_spread": "tight",
    },
    "balanced": {
        "response_verbosity": "balanced",
        "context_depth": "targeted",
        "option_spread": "focused",
    },
    "detailed": {
        "response_verbosity": "detailed",
        "context_depth": "thorough",
        "option_spread": "broad",
    },
}

AUTONOMY_STYLE = {
    "guided": {
        "decision_mode": "confirm-major-assumptions",
        "plan_visibility": "high",
        "execution_bias": "pause-at-branching-points",
    },
    "balanced": {
        "decision_mode": "state-assumptions-and-proceed-when-safe",
        "plan_visibility": "medium",
        "execution_bias": "execute-safe-slices",
    },
    "autonomous": {
        "decision_mode": "propose-best-path-and-execute-safe-slices",
        "plan_visibility": "targeted",
        "execution_bias": "move-forward-until-risky-boundary",
    },
}

PERSONALITY_STYLE = {
    "default": {
        "tone": "pragmatic",
        "teaching_mode": "as-needed",
        "challenge_level": "measured",
    },
    "mentor": {
        "tone": "supportive-pragmatic",
        "teaching_mode": "explain-why",
        "challenge_level": "light",
    },
    "strict-coach": {
        "tone": "direct-high-standard",
        "teaching_mode": "best-practice-first",
        "challenge_level": "high",
    },
}


def configure_stdio() -> None:
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name)
        encoding = getattr(stream, "encoding", None)
        if encoding and encoding.lower() != "utf-8":
            setattr(sys, name, io.TextIOWrapper(stream.buffer, encoding="utf-8"))


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_preferences_schema() -> dict:
    return json.loads(PREFERENCES_SCHEMA_PATH.read_text(encoding="utf-8"))


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


def read_text(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def preference_defaults() -> dict[str, str]:
    schema = load_preferences_schema()
    defaults: dict[str, str] = {}
    for key, config in schema.get("properties", {}).items():
        default_value = config.get("default")
        if isinstance(default_value, str):
            defaults[key] = default_value
    return defaults


def resolve_workspace_preferences_path(workspace: Path | None = None) -> Path:
    root = Path(workspace).resolve() if workspace is not None else Path.cwd()
    return root / ".brain" / "preferences.json"


def normalize_preferences(payload: object, *, strict: bool = False) -> tuple[dict[str, str], list[str]]:
    defaults = preference_defaults()
    warnings: list[str] = []
    if payload is None:
        return defaults, warnings
    if not isinstance(payload, dict):
        raise ValueError("Preferences payload must be a JSON object.")

    properties = load_preferences_schema().get("properties", {})
    normalized = defaults.copy()
    allowed_keys = set(properties)

    for key in sorted(payload):
        if key not in allowed_keys:
            message = f"Ignored unknown preference '{key}'."
            if strict:
                raise ValueError(message)
            warnings.append(message)
            continue

        raw_value = payload[key]
        if not isinstance(raw_value, str):
            message = f"Preference '{key}' must be a string."
            if strict:
                raise ValueError(message)
            warnings.append(message)
            continue

        token = normalize_choice_token(raw_value)
        aliases = PREFERENCE_ALIASES.get(key, {})
        canonical = aliases.get(token)
        if canonical is None:
            allowed = ", ".join(properties[key].get("enum", []))
            message = f"Preference '{key}' must be one of: {allowed}."
            if strict:
                raise ValueError(message)
            warnings.append(message)
            continue

        normalized[key] = canonical

    return normalized, warnings


def load_preferences(
    *,
    preferences_file: Path | None = None,
    workspace: Path | None = None,
    strict: bool = False,
) -> dict:
    warnings: list[str] = []
    defaults = preference_defaults()

    if preferences_file is not None:
        path = Path(preferences_file).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Preferences file does not exist: {path}")
        source_type = "explicit"
    else:
        path = resolve_workspace_preferences_path(workspace)
        source_type = "workspace-local"
        if not path.exists():
            return {
                "preferences": defaults,
                "source": {"type": "defaults", "path": None},
                "warnings": warnings,
            }

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        if strict:
            raise ValueError(f"Invalid JSON in preferences file: {path}") from exc
        warnings.append(f"Invalid JSON in preferences file '{path.name}'. Using defaults.")
        payload = None

    preferences, normalization_warnings = normalize_preferences(payload, strict=strict)
    warnings.extend(normalization_warnings)
    return {
        "preferences": preferences,
        "source": {"type": source_type, "path": str(path)},
        "warnings": warnings,
    }


def resolve_response_style(preferences: dict[str, str]) -> dict[str, str]:
    technical_level = preferences["technical_level"]
    detail_level = preferences["detail_level"]
    autonomy_level = preferences["autonomy_level"]
    personality = preferences["personality"]

    style: dict[str, str] = {}
    style.update(TECHNICAL_STYLE[technical_level])
    style.update(DETAIL_STYLE[detail_level])
    style.update(AUTONOMY_STYLE[autonomy_level])
    style.update(PERSONALITY_STYLE[personality])
    return style


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


def default_artifact_dir(output_dir: str | None, artifact_type: str) -> Path:
    base_dir = Path(output_dir).resolve() if output_dir else Path.cwd()
    return base_dir / ".forge-artifacts" / artifact_type
