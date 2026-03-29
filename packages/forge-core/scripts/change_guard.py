from __future__ import annotations

from common import normalize_text


BLOCK_KEYWORDS = ("git reset --hard", "checkout --", "remove-item", "rm -rf", "delete", "drop table", "truncate")
WARN_KEYWORDS = ("deploy", "production", "publish", "secret", "token", "password", "api key", "credential")


def guard_change(summary: str, actions: list[str]) -> dict:
    haystack = normalize_text(" ".join([summary, *actions]))
    for keyword in BLOCK_KEYWORDS:
        if normalize_text(keyword) in haystack:
            return {
                "status": "FAIL",
                "classification": "block",
                "reason": f"Matched destructive action keyword: {keyword}",
            }
    for keyword in WARN_KEYWORDS:
        if normalize_text(keyword) in haystack:
            return {
                "status": "WARN",
                "classification": "warn",
                "reason": f"Matched sensitive action keyword: {keyword}",
            }
    return {"status": "PASS", "classification": "allow", "reason": "No guarded risky action detected."}
