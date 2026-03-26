from __future__ import annotations

import copy
import io
import json
import os
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
PREFERENCES_COMPAT_PATH = ROOT_DIR / "data" / "preferences-compat.json"
INSTALL_MANIFEST_PATH = ROOT_DIR / "INSTALL-MANIFEST.json"
DEFAULT_FALLBACK_STATE_ROOT = Path.home() / ".forge"
GLOBAL_PREFERENCES_RELATIVE_PATH = Path("state") / "preferences.json"
LEGACY_WORKSPACE_PREFERENCES_RELATIVE_PATH = Path(".brain") / "preferences.json"

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
    "pace": {
        "steady": "steady",
        "slow": "steady",
        "careful": "steady",
        "balanced": "balanced",
        "default": "balanced",
        "normal": "balanced",
        "standard": "balanced",
        "fast": "fast",
        "rapid": "fast",
        "quick": "fast",
        "push": "fast",
    },
    "feedback_style": {
        "gentle": "gentle",
        "soft": "gentle",
        "encouraging": "gentle",
        "balanced": "balanced",
        "default": "balanced",
        "standard": "balanced",
        "direct": "direct",
        "blunt": "direct",
        "strict": "direct",
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

PACE_STYLE = {
    "steady": {
        "delivery_pace": "steady",
        "iteration_rhythm": "pause-at-notable-branch-points",
    },
    "balanced": {
        "delivery_pace": "balanced",
        "iteration_rhythm": "default-checkpoints",
    },
    "fast": {
        "delivery_pace": "fast",
        "iteration_rhythm": "push-until-risk-boundary",
    },
}

FEEDBACK_STYLE = {
    "gentle": {
        "feedback_mode": "gentle",
        "critique_style": "encouraging-first",
    },
    "balanced": {
        "feedback_mode": "balanced",
        "critique_style": "direct-when-useful",
    },
    "direct": {
        "feedback_mode": "direct",
        "critique_style": "call-out-gaps-plainly",
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

ERROR_TRANSLATIONS = (
    {
        "label": "missing-module",
        "category": "module",
        "patterns": (r"cannot find module", r"module not found", r"no module named"),
        "human_message": "A required module or package is missing, or the import path is wrong.",
        "suggested_action": "Check the import path or install the missing dependency, then rerun the same failing command.",
    },
    {
        "label": "missing-database-relation",
        "category": "database",
        "patterns": (r"relation .+ does not exist", r"table .+ does not exist"),
        "human_message": "The app is querying a table or relation that does not exist in the current database schema.",
        "suggested_action": "Verify migrations ran in this environment and confirm the code points at the right database.",
    },
    {
        "label": "database-connection-refused",
        "category": "database",
        "patterns": (r"\beconnrefused\b", r"connection refused", r"could not connect to server"),
        "human_message": "The app could not reach the database or dependent service.",
        "suggested_action": "Start the dependency, then verify host, port, and credentials before retrying.",
    },
    {
        "label": "duplicate-data",
        "category": "database",
        "patterns": (r"duplicate key", r"unique constraint", r"already exists"),
        "human_message": "The write is colliding with data that must stay unique.",
        "suggested_action": "Inspect the existing record or unique constraint, then adjust the seed/data flow before retrying.",
    },
    {
        "label": "undefined-value",
        "category": "runtime",
        "patterns": (
            r"typeerror:\s*cannot read",
            r"cannot read (?:properties|property) of (?:undefined|null)",
            r"undefined is not an object",
        ),
        "human_message": "The code is trying to read a value that is missing at runtime.",
        "suggested_action": "Trace the null or undefined value back to its source and add the right guard or initialization.",
    },
    {
        "label": "missing-reference",
        "category": "runtime",
        "patterns": (r"\breferenceerror\b",),
        "human_message": "The code is using a variable or symbol that is not defined in this scope.",
        "suggested_action": "Check the symbol name, import, or scope, then rerun the failing command.",
    },
    {
        "label": "syntax-error",
        "category": "runtime",
        "patterns": (r"\bsyntaxerror\b",),
        "human_message": "The command failed because the code or config has invalid syntax.",
        "suggested_action": "Inspect the reported file and line for a malformed token, bracket, or separator, then rerun.",
    },
    {
        "label": "network-blocked",
        "category": "network",
        "patterns": (r"\bcors\b", r"fetch failed", r"\benotfound\b", r"failed to fetch"),
        "human_message": "The request could not reach the target service or was blocked by network policy.",
        "suggested_action": "Verify the URL, network reachability, and server policy such as CORS before retrying.",
    },
    {
        "label": "timeout",
        "category": "timeout",
        "patterns": (r"\betimedout\b", r"timed out", r"\btimeout\b"),
        "human_message": "The command or dependency took too long to respond.",
        "suggested_action": "Check whether the process is stalled, slow, or waiting on another service before rerunning.",
    },
    {
        "label": "test-assertion",
        "category": "test",
        "patterns": (r"expected .+ but received", r"before each hook", r"\bsnapshot\b", r"\bcoverage\b"),
        "human_message": "A test expectation or test setup does not match the current behavior.",
        "suggested_action": "Confirm whether the code is wrong or the test is outdated, then fix the failing expectation first.",
    },
    {
        "label": "build-lint-type",
        "category": "build",
        "patterns": (r"\btsc\b.*error", r"\beslint\b", r"build failed", r"out of memory", r"\bfatal error\b"),
        "human_message": "The build pipeline hit a type, lint, memory, or compile failure.",
        "suggested_action": "Read the first concrete compiler or lint error, fix that root issue, and rerun the build.",
    },
    {
        "label": "git-conflict",
        "category": "git",
        "patterns": (r"\bconflict\b", r"rejected", r"detached head", r"not a git repo"),
        "human_message": "Git state is blocking the workflow.",
        "suggested_action": "Resolve the git state first, then repeat the original command from a clean branch context.",
    },
    {
        "label": "deploy-gateway",
        "category": "deploy",
        "patterns": (r"502 bad gateway", r"503 service", r"quota exceeded"),
        "human_message": "The deployment target is unhealthy or out of capacity.",
        "suggested_action": "Inspect the hosting platform health, capacity, or service logs before retrying deployment.",
    },
)

SENSITIVE_ERROR_PATTERNS = (
    (re.compile(r"([a-z]+://)([^/\s:@]+):([^@\s]+)@", re.IGNORECASE), r"\1<redacted>@"),
    (re.compile(r"(Bearer\s+)[A-Za-z0-9._-]+", re.IGNORECASE), r"\1<redacted>"),
    (re.compile(r"((?:password|passwd|token|secret|apikey|api_key)[=:\s]+)[^\s'\"]+", re.IGNORECASE), r"\1<redacted>"),
    (re.compile(r"\b[A-Za-z]:\\[^\s'\"]+"), "<path>"),
    (re.compile(r"(?<![a-z])/(?:Users|home|var|tmp|opt|srv)[^\s'\"]*", re.IGNORECASE), "<path>"),
)


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


def preference_defaults() -> dict[str, str]:
    schema = load_preferences_schema()
    defaults: dict[str, str] = {}
    for key, config in schema.get("properties", {}).items():
        default_value = config.get("default")
        if isinstance(default_value, str):
            defaults[key] = default_value
    return defaults


@lru_cache(maxsize=1)
def load_install_manifest() -> dict | None:
    if not INSTALL_MANIFEST_PATH.exists():
        return None
    try:
        manifest = json.loads(INSTALL_MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return manifest if isinstance(manifest, dict) else None


@lru_cache(maxsize=1)
def load_preferences_compat() -> dict | None:
    if not PREFERENCES_COMPAT_PATH.exists():
        return None
    try:
        compat = json.loads(PREFERENCES_COMPAT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return compat if isinstance(compat, dict) else None


def compat_entry_paths(entry: dict) -> list[str]:
    raw_paths = entry.get("paths")
    if isinstance(raw_paths, list):
        return [path for path in raw_paths if isinstance(path, str) and path.strip()]
    raw_path = entry.get("path")
    if isinstance(raw_path, str) and raw_path.strip():
        return [raw_path]
    return []


def get_nested_value(payload: object, path: str) -> object:
    current = payload
    for segment in path.split("."):
        if not isinstance(current, dict) or segment not in current:
            return None
        current = current[segment]
    return current


def has_nested_value(payload: object, path: str) -> bool:
    current = payload
    for segment in path.split("."):
        if not isinstance(current, dict) or segment not in current:
            return False
        current = current[segment]
    return True


def set_nested_value(payload: dict, path: str, value: object) -> None:
    current = payload
    segments = path.split(".")
    for segment in segments[:-1]:
        next_value = current.get(segment)
        if not isinstance(next_value, dict):
            next_value = {}
            current[segment] = next_value
        current = next_value
    current[segments[-1]] = value


def canonical_preference_keys() -> set[str]:
    return set(load_preferences_schema().get("properties", {}))


def compat_canonical_paths(compat: dict | None) -> set[str]:
    if not isinstance(compat, dict):
        return set()

    read_config = compat.get("read")
    if not isinstance(read_config, dict):
        return set()

    fields = read_config.get("canonical_fields")
    if not isinstance(fields, dict):
        return set()

    paths: set[str] = set()
    for entry in fields.values():
        if isinstance(entry, dict):
            paths.update(compat_entry_paths(entry))
    return paths


def compat_extra_fields(compat: dict | None) -> dict[str, dict]:
    if not isinstance(compat, dict):
        return {}

    fields = compat.get("extra_fields")
    if not isinstance(fields, dict):
        return {}

    return {
        key: entry
        for key, entry in fields.items()
        if isinstance(key, str) and isinstance(entry, dict)
    }


def compat_extra_paths(compat: dict | None) -> set[str]:
    paths: set[str] = set()
    for entry in compat_extra_fields(compat).values():
        paths.update(compat_entry_paths(entry))
    return paths


def compat_default_extra(compat: dict | None) -> dict[str, object]:
    if not isinstance(compat, dict):
        return {}

    default_extra = compat.get("default_extra")
    if not isinstance(default_extra, dict):
        return {}

    return copy.deepcopy(default_extra)


def delete_nested_value(payload: dict, path: str) -> None:
    segments = path.split(".")
    current = payload
    parents: list[tuple[dict, str]] = []

    for segment in segments[:-1]:
        next_value = current.get(segment)
        if not isinstance(next_value, dict):
            return
        parents.append((current, segment))
        current = next_value

    if segments[-1] not in current:
        return

    del current[segments[-1]]

    for parent, segment in reversed(parents):
        child = parent.get(segment)
        if isinstance(child, dict) and not child:
            del parent[segment]
            continue
        break


def preferences_compat_matches(payload: object, compat: dict | None = None) -> bool:
    if not isinstance(payload, dict):
        return False
    compat = load_preferences_compat() if compat is None else compat
    if compat is None:
        return False

    read_config = compat.get("read")
    if not isinstance(read_config, dict):
        return False

    match_any = read_config.get("match_any_top_level_keys")
    if isinstance(match_any, list):
        if any(isinstance(key, str) and key in payload for key in match_any):
            return True

    match_all = read_config.get("match_all_top_level_keys")
    if isinstance(match_all, list):
        keys = [key for key in match_all if isinstance(key, str)]
        if keys and all(key in payload for key in keys):
            return True

    return False


def compat_read_value(raw_value: object, entry: dict) -> object:
    if not isinstance(raw_value, str):
        return raw_value

    token = normalize_choice_token(raw_value)
    read_map = entry.get("read_map")
    if isinstance(read_map, dict):
        mapped = read_map.get(token)
        if mapped is not None:
            return mapped
    return raw_value


def translate_preferences_payload(payload: object, compat: dict | None = None) -> object:
    compat = load_preferences_compat() if compat is None else compat
    if compat is None or not preferences_compat_matches(payload, compat):
        return payload

    read_config = compat.get("read")
    if not isinstance(read_config, dict):
        return payload

    fields = read_config.get("canonical_fields")
    if not isinstance(fields, dict):
        return payload

    translated: dict[str, object] = {}
    for key, entry in fields.items():
        if not isinstance(entry, dict):
            continue
        for path in compat_entry_paths(entry):
            raw_value = get_nested_value(payload, path)
            if raw_value is None:
                continue
            translated[key] = compat_read_value(raw_value, entry)
            break

    return translated


def extract_extras(raw_payload: object, compat_config: dict | None = None) -> dict[str, object]:
    if not isinstance(raw_payload, dict):
        return {}

    compat = load_preferences_compat() if compat_config is None else compat_config
    if preferences_compat_matches(raw_payload, compat):
        extras = copy.deepcopy(raw_payload)
        for path in compat_canonical_paths(compat):
            delete_nested_value(extras, path)
        compat_extras: dict[str, object] = {}
        for key, entry in compat_extra_fields(compat).items():
            for path in compat_entry_paths(entry):
                raw_value = get_nested_value(raw_payload, path)
                if raw_value is None:
                    continue
                compat_extras[key] = copy.deepcopy(compat_read_value(raw_value, entry))
                delete_nested_value(extras, path)
                break
        return merge_extra_preferences(extras, compat_extras)

    canonical_keys = canonical_preference_keys()
    return {
        key: copy.deepcopy(value)
        for key, value in raw_payload.items()
        if key not in canonical_keys
    }


def filter_canonical_preferences(raw_payload: object, compat_config: dict | None = None) -> object:
    if not isinstance(raw_payload, dict):
        return raw_payload

    compat = load_preferences_compat() if compat_config is None else compat_config
    if preferences_compat_matches(raw_payload, compat):
        return translate_preferences_payload(raw_payload, compat)

    allowed_keys = canonical_preference_keys()
    return {key: raw_payload[key] for key in raw_payload if key in allowed_keys}


def merge_extra_preferences(
    base: dict[str, object] | None,
    override: dict[str, object] | None,
) -> dict[str, object]:
    merged: dict[str, object] = copy.deepcopy(base or {})
    for key, value in (override or {}).items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = merge_extra_preferences(existing, value)
            continue
        merged[key] = copy.deepcopy(value)
    return merged


def resolve_extra_preferences(
    raw_payload: object,
    *,
    compat_config: dict | None = None,
    include_defaults: bool = True,
) -> dict[str, object]:
    compat = load_preferences_compat() if compat_config is None else compat_config
    extra = extract_extras(raw_payload, compat_config=compat)
    if not include_defaults:
        return extra
    return merge_extra_preferences(compat_default_extra(compat), extra)


def resolve_output_contract(extra: object) -> dict[str, object]:
    if not isinstance(extra, dict):
        return {}

    contract: dict[str, object] = {}

    language = extra.get("language")
    if isinstance(language, str) and language.strip():
        normalized_language = normalize_choice_token(language)
        contract["language"] = normalized_language
        if normalized_language == "vi":
            contract["user_facing_language"] = "vietnamese"
            contract["accent_policy"] = "required"
            contract["encoding"] = "utf-8"

    orthography = extra.get("orthography")
    if isinstance(orthography, str) and orthography.strip():
        normalized_orthography = normalize_choice_token(orthography)
        contract["orthography"] = normalized_orthography
        if normalized_orthography == "vietnamese-diacritics":
            contract["accent_policy"] = "required"
            contract.setdefault("encoding", "utf-8")

    tone_detail = extra.get("tone_detail")
    if isinstance(tone_detail, str) and tone_detail.strip():
        contract["tone_detail"] = tone_detail.strip()

    custom_rules = extra.get("custom_rules")
    if isinstance(custom_rules, list):
        normalized_rules = [item.strip() for item in custom_rules if isinstance(item, str) and item.strip()]
        if normalized_rules:
            contract["custom_rules"] = normalized_rules

    if contract.get("language") == "vi" and "orthography" not in contract:
        contract["orthography"] = "vietnamese-diacritics"

    return contract


def choose_compat_write_path(existing_payload: object, entry: dict) -> str | None:
    for path in compat_entry_paths(entry):
        if has_nested_value(existing_payload, path):
            return path
    paths = compat_entry_paths(entry)
    return paths[0] if paths else None


def compat_values_equivalent(existing_raw: object, desired_value: str, entry: dict) -> bool:
    existing_value = compat_read_value(existing_raw, entry)
    if not isinstance(existing_value, str):
        return False
    return normalize_choice_token(existing_value) == normalize_choice_token(desired_value)


def compat_write_value(existing_payload: object, desired_value: str, entry: dict) -> str:
    for path in compat_entry_paths(entry):
        existing_raw = get_nested_value(existing_payload, path)
        if compat_values_equivalent(existing_raw, desired_value, entry) and isinstance(existing_raw, str):
            return existing_raw

    token = normalize_choice_token(desired_value)
    write_map = entry.get("write_map")
    if isinstance(write_map, dict):
        mapped = write_map.get(token)
        if isinstance(mapped, str):
            return mapped
    return desired_value


def apply_extra_preferences(
    payload: object,
    extra_updates: dict[str, object] | None,
    *,
    existing_payload: object,
    compat: dict | None = None,
) -> object:
    if not isinstance(payload, dict) or not extra_updates:
        return payload

    compat_entries = compat_extra_fields(compat)
    for key, value in extra_updates.items():
        entry = compat_entries.get(key)
        if entry is not None:
            for path in compat_entry_paths(entry):
                delete_nested_value(payload, path)
            if value is None:
                continue
            path = choose_compat_write_path(existing_payload, entry)
            if path is None:
                continue
            if isinstance(value, str):
                serialized_value: object = compat_write_value(existing_payload, value, entry)
            else:
                serialized_value = copy.deepcopy(value)
            set_nested_value(payload, path, serialized_value)
            continue

        if value is None:
            payload.pop(key, None)
            continue
        payload[key] = copy.deepcopy(value)

    return payload


def serialize_preferences_payload(
    preferences: dict[str, str],
    *,
    existing_payload: object,
    replace: bool,
    extra_updates: dict[str, object] | None = None,
    compat_config: dict | None = None,
) -> object:
    compat = load_preferences_compat() if compat_config is None else compat_config
    if compat is None:
        serialized = copy.deepcopy(existing_payload) if isinstance(existing_payload, dict) else {}
        for key, value in preferences.items():
            serialized[key] = value
        return apply_extra_preferences(
            serialized,
            extra_updates,
            existing_payload=existing_payload,
        )

    write_config = compat.get("write")
    if not isinstance(write_config, dict):
        serialized = copy.deepcopy(existing_payload) if isinstance(existing_payload, dict) else {}
        for key, value in preferences.items():
            serialized[key] = value
        return apply_extra_preferences(
            serialized,
            extra_updates,
            existing_payload=existing_payload,
        )

    use_compat = False
    if preferences_compat_matches(existing_payload, compat):
        use_compat = True
    elif existing_payload is None and write_config.get("prefer_native_format"):
        use_compat = True

    if not use_compat:
        serialized = copy.deepcopy(existing_payload) if isinstance(existing_payload, dict) else {}
        for key, value in preferences.items():
            serialized[key] = value
        return apply_extra_preferences(
            serialized,
            extra_updates,
            existing_payload=existing_payload,
        )

    template = write_config.get("template")
    if isinstance(existing_payload, dict) and write_config.get("preserve_existing_payload", True):
        serialized = copy.deepcopy(existing_payload)
    elif isinstance(template, dict):
        serialized = copy.deepcopy(template)
    else:
        serialized = {}

    fields = write_config.get("canonical_fields")
    if not isinstance(fields, dict):
        return serialized

    for key, desired_value in preferences.items():
        entry = fields.get(key)
        if not isinstance(entry, dict):
            continue
        path = choose_compat_write_path(existing_payload if not replace else serialized, entry)
        if path is None:
            continue
        value = compat_write_value(existing_payload if not replace else serialized, desired_value, entry)
        set_nested_value(serialized, path, value)

    return apply_extra_preferences(
        serialized,
        extra_updates,
        existing_payload=existing_payload if isinstance(existing_payload, dict) else serialized,
        compat=compat,
    )


def resolve_installed_state_root() -> Path | None:
    manifest = load_install_manifest()
    if manifest is not None:
        state = manifest.get("state")
        if isinstance(state, dict):
            root = state.get("root")
            if isinstance(root, str) and root.strip():
                return Path(root).expanduser().resolve()

    if ROOT_DIR.parent.name == "skills":
        return (ROOT_DIR.parent.parent / ROOT_DIR.name).resolve()

    return None


def resolve_installed_preferences_path() -> Path | None:
    manifest = load_install_manifest()
    if manifest is not None:
        state = manifest.get("state")
        if isinstance(state, dict):
            path = state.get("preferences_path")
            if isinstance(path, str) and path.strip():
                return Path(path).expanduser().resolve()

    state_root = resolve_installed_state_root()
    if state_root is None:
        return None
    return state_root / GLOBAL_PREFERENCES_RELATIVE_PATH


def resolve_forge_home(forge_home: Path | str | None = None) -> Path:
    candidate = forge_home if forge_home is not None else os.environ.get("FORGE_HOME")
    if candidate is not None:
        return Path(candidate).expanduser().resolve()
    installed_state_root = resolve_installed_state_root()
    if installed_state_root is not None:
        return installed_state_root
    return DEFAULT_FALLBACK_STATE_ROOT.resolve()


def resolve_global_preferences_path(forge_home: Path | str | None = None) -> Path:
    if forge_home is None and os.environ.get("FORGE_HOME") is None:
        installed_preferences_path = resolve_installed_preferences_path()
        if installed_preferences_path is not None:
            return installed_preferences_path
    return resolve_forge_home(forge_home) / GLOBAL_PREFERENCES_RELATIVE_PATH


def resolve_workspace_preferences_path(workspace: Path | None = None) -> Path:
    root = Path(workspace).resolve() if workspace is not None else Path.cwd()
    return root / LEGACY_WORKSPACE_PREFERENCES_RELATIVE_PATH


def normalize_preferences(payload: object, *, strict: bool = False) -> tuple[dict[str, str], list[str]]:
    defaults = preference_defaults()
    warnings: list[str] = []
    if payload is None:
        return defaults, warnings

    payload = translate_preferences_payload(payload)
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
    forge_home: Path | str | None = None,
) -> dict:
    warnings: list[str] = []
    defaults = preference_defaults()

    if preferences_file is not None:
        path = Path(preferences_file).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Preferences file does not exist: {path}")
        source_type = "explicit"
    else:
        global_path = resolve_global_preferences_path(forge_home)
        if global_path.exists():
            path = global_path
            source_type = "global"
        else:
            path = resolve_workspace_preferences_path(workspace) if workspace is not None else None
            source_type = "workspace-legacy"
            if path is None or not path.exists():
                compat = load_preferences_compat()
                extra = resolve_extra_preferences(None, compat_config=compat)
                return {
                    "preferences": defaults,
                    "extra": extra,
                    "source": {"type": "defaults", "path": None},
                    "output_contract": resolve_output_contract(extra),
                    "warnings": warnings,
                }

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        if strict:
            raise ValueError(f"Invalid JSON in preferences file: {path}") from exc
        warnings.append(f"Invalid JSON in preferences file '{path.name}'. Using defaults.")
        payload = None

    compat = load_preferences_compat()
    extra = resolve_extra_preferences(payload, compat_config=compat)
    canonical_payload = filter_canonical_preferences(payload, compat_config=compat)
    preferences, normalization_warnings = normalize_preferences(canonical_payload, strict=strict)
    warnings.extend(normalization_warnings)
    return {
        "preferences": preferences,
        "extra": extra,
        "source": {"type": source_type, "path": str(path)},
        "output_contract": resolve_output_contract(extra),
        "warnings": warnings,
    }


def resolve_response_style(preferences: dict[str, str]) -> dict[str, str]:
    technical_level = preferences["technical_level"]
    detail_level = preferences["detail_level"]
    autonomy_level = preferences["autonomy_level"]
    pace = preferences["pace"]
    feedback_style = preferences["feedback_style"]
    personality = preferences["personality"]

    style: dict[str, str] = {}
    style.update(TECHNICAL_STYLE[technical_level])
    style.update(DETAIL_STYLE[detail_level])
    style.update(AUTONOMY_STYLE[autonomy_level])
    style.update(PACE_STYLE[pace])
    style.update(FEEDBACK_STYLE[feedback_style])
    style.update(PERSONALITY_STYLE[personality])
    return style


def write_preferences(
    *,
    workspace: Path | None = None,
    updates: dict[str, str],
    extra_updates: dict[str, object] | None = None,
    strict: bool = False,
    replace: bool = False,
    apply: bool = False,
    forge_home: Path | str | None = None,
) -> dict:
    if not updates and not extra_updates:
        raise ValueError("At least one preference update is required.")

    workspace_path = Path(workspace).resolve() if workspace is not None else None
    forge_home_path = resolve_forge_home(forge_home)
    existing = load_preferences(workspace=workspace_path, strict=strict, forge_home=forge_home_path)
    base = preference_defaults() if replace else existing["preferences"].copy()
    base.update(updates)
    preferences, warnings = normalize_preferences(base, strict=strict)
    path = resolve_global_preferences_path(forge_home_path)
    raw_payload = None
    if path.exists():
        try:
            raw_payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            raw_payload = None
    compat = load_preferences_compat()
    serialized_preferences = serialize_preferences_payload(
        preferences,
        existing_payload=raw_payload,
        replace=replace,
        extra_updates=extra_updates,
        compat_config=compat,
    )
    extra = resolve_extra_preferences(serialized_preferences, compat_config=compat)

    changed_fields = [
        key for key in preferences if existing["preferences"].get(key) != preferences.get(key)
    ]
    changed_extra_fields = [
        key for key in (extra_updates or {})
        if existing["extra"].get(key) != extra.get(key)
    ]
    created_file = not path.exists()
    if apply:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(serialized_preferences, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    status = "PASS" if changed_fields or changed_extra_fields else "WARN"
    if warnings and status == "PASS":
        status = "WARN"

    return {
        "status": status,
        "scope": "adapter-global",
        "state_root": str(forge_home_path),
        "forge_home": str(forge_home_path),
        "workspace": str(workspace_path) if workspace_path is not None else None,
        "path": str(path),
        "applied": apply,
        "replace": replace,
        "created_file": created_file and apply,
        "migrated_legacy_workspace_preferences": existing["source"]["type"] == "workspace-legacy",
        "previous_preferences": existing["preferences"],
        "previous_extra": existing["extra"],
        "preferences": preferences,
        "extra": extra,
        "output_contract": resolve_output_contract(extra),
        "response_style": resolve_response_style(preferences),
        "changed_fields": changed_fields,
        "changed_extra_fields": changed_extra_fields,
        "warnings": warnings,
    }


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


def sanitize_error_text(text: str) -> str:
    sanitized = text
    for pattern, replacement in SENSITIVE_ERROR_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def translate_error_text(text: str, *, include_empty_fallback: bool = False) -> dict | None:
    sanitized = sanitize_error_text(text)
    snippet = excerpt_text(sanitized, max_lines=5, max_chars=320)

    if not snippet:
        if not include_empty_fallback:
            return None
        return {
            "status": "WARN",
            "source": "empty-fallback",
            "label": "empty-error",
            "category": "generic",
            "human_message": "The command failed, but there was no visible error output to translate.",
            "suggested_action": "Rerun the same command with more logging or under the debug workflow to capture the missing signal.",
            "error_excerpt": "",
        }

    for entry in ERROR_TRANSLATIONS:
        for pattern in entry["patterns"]:
            if re.search(pattern, sanitized, re.IGNORECASE):
                return {
                    "status": "PASS",
                    "source": "pattern",
                    "label": entry["label"],
                    "category": entry["category"],
                    "human_message": entry["human_message"],
                    "suggested_action": entry["suggested_action"],
                    "matched_pattern": pattern,
                    "error_excerpt": snippet,
                }

    return {
        "status": "WARN",
        "source": "fallback",
        "label": "generic-error",
        "category": "generic",
        "human_message": "The command failed, but the error does not match a known Forge translation yet.",
        "suggested_action": "Use the failing command as the reproduction anchor, inspect the full stderr/stdout, and continue in debug mode.",
        "error_excerpt": snippet,
    }
