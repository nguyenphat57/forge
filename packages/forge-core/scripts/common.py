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
    workspace: Path,
    updates: dict[str, str],
    strict: bool = False,
    replace: bool = False,
    apply: bool = False,
) -> dict:
    if not updates:
        raise ValueError("At least one preference update is required.")

    workspace = Path(workspace).resolve()
    existing = load_preferences(workspace=workspace, strict=strict)
    base = preference_defaults() if replace else existing["preferences"].copy()
    base.update(updates)
    preferences, warnings = normalize_preferences(base, strict=strict)
    path = resolve_workspace_preferences_path(workspace)

    changed_fields = [
        key for key in preferences if existing["preferences"].get(key) != preferences.get(key)
    ]
    created_file = not path.exists()
    if apply:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(preferences, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    status = "PASS" if changed_fields else "WARN"
    if warnings and status == "PASS":
        status = "WARN"

    return {
        "status": status,
        "workspace": str(workspace),
        "path": str(path),
        "applied": apply,
        "replace": replace,
        "created_file": created_file and apply,
        "previous_preferences": existing["preferences"],
        "preferences": preferences,
        "response_style": resolve_response_style(preferences),
        "changed_fields": changed_fields,
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
