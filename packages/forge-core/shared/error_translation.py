from __future__ import annotations

import re

from text_utils import excerpt_text


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
