from __future__ import annotations

from common import keyword_in_text, normalize_text, score_keywords


def prompt_structure_score(text: str, phrases: list[str]) -> int:
    return sum(1 for phrase in phrases if keyword_in_text(normalize_text(phrase), text))


def looks_like_direction_selection_request(prompt_text: str) -> bool:
    normalized = normalize_text(prompt_text)
    is_question = "?" in prompt_text or keyword_in_text("co nen", normalized) or keyword_in_text("should", normalized)
    if not is_question:
        return False

    choice_score = prompt_structure_score(normalized, ["hay", "hoac", "or", "vs", "between", "giua"])
    decision_score = prompt_structure_score(
        normalized,
        [
            "nen",
            "should",
            "chon",
            "use",
            "dung",
            "huong nao",
            "di huong",
            "di huong nao",
            "cach nao",
            "phuong an",
            "phuong an nao",
            "giai phap",
            "giai phap nao",
            "direction",
            "approach",
            "option",
            "tradeoff",
            "so sanh",
            "compare",
        ],
    )
    return choice_score > 0 and decision_score > 0


def matched_high_risk_categories(prompt_text: str, repo_signals: list[str]) -> list[str]:
    haystack = normalize_text(" ".join([prompt_text, *repo_signals]))
    categories = {
        "public_interface": [
            "api",
            "endpoint",
            "contract",
            "webhook",
            "rpc",
            "client",
            "consumer",
            "khach hang cu",
            "client hien tai",
            "client cu",
        ],
        "compatibility": [
            "compatible",
            "compatibility",
            "backward compatible",
            "backward compatibility",
            "tuong thich",
            "tuong thich nguoc",
            "giu tuong thich",
            "giu api cu",
            "giu client cu",
            "giu hanh vi cu",
            "giu contract cu",
            "khong pha api cu",
            "khong pha client cu",
            "khong vo api cu",
            "khong break",
            "khong vo",
        ],
        "auth_payment": ["auth", "payment", "checkout", "xac thuc", "thanh toan"],
        "data_schema": [
            "migration",
            "schema",
            "backfill",
            "policy",
            "rls",
            "database",
            "du lieu",
            "co so du lieu",
        ],
        "integration": ["integration", "third-party", "external", "partner", "tich hop"],
    }

    matched: list[str] = []
    for category, phrases in categories.items():
        if prompt_structure_score(haystack, phrases) > 0:
            matched.append(category)
    return matched


def looks_like_high_risk_boundary_change(prompt_text: str, repo_signals: list[str]) -> bool:
    matched = matched_high_risk_categories(prompt_text, repo_signals)
    if len(matched) >= 2:
        return True
    if "compatibility" in matched and "public_interface" in matched:
        return True
    if "public_interface" in matched and any(
        category in matched for category in ("auth_payment", "data_schema", "integration")
    ):
        return True
    return False


def should_insert_brainstorm(prompt_text: str, intent: str, complexity: str, registry: dict) -> bool:
    gate = registry.get("brainstorm_gate", {})
    if intent not in gate.get("eligible_intents", []):
        return False
    if complexity not in gate.get("eligible_complexities", []):
        return False
    normalized = normalize_text(prompt_text)
    if score_keywords(
        normalized,
        ["existing clients", "existing client", "backward compatibility", "keep backward", "compatibility"],
    ) > 0:
        greenfield_score = 0
    else:
        greenfield_score = score_keywords(
            normalized,
            [
                "new feature",
                "new flow",
                "new screen",
                "new endpoint",
                "new module",
                "add a new",
                "create a new",
                "greenfield",
            ],
        )
    return (
        score_keywords(normalized, gate.get("prompt_keywords", [])) > 0
        or looks_like_direction_selection_request(prompt_text)
        or (intent == "BUILD" and complexity in {"medium", "large"} and greenfield_score > 0)
    )


def should_insert_spec_review(
    prompt_text: str,
    repo_signals: list[str],
    intent: str,
    complexity: str,
    registry: dict,
) -> bool:
    gate = registry.get("spec_review_gate", {})
    if intent not in gate.get("eligible_intents", []):
        return False
    if complexity == "large" and gate.get("always_large", False):
        return True

    haystack = normalize_text(" ".join([prompt_text, *repo_signals]))
    non_behavioral = score_keywords(haystack, registry.get("change_type_hints", {}).get("non_behavioral_keywords", [])) > 0
    keyword_score = score_keywords(haystack, gate.get("prompt_keywords", []))
    signal_score = score_keywords(haystack, gate.get("repo_signals", []))
    packet_unclear = score_keywords(
        haystack,
        ["unclear", "ambiguous", "tbd", "to decide", "not sure", "figure out", "explore while building"],
    ) > 0
    boundary_risk = (keyword_score + signal_score) > 0 or looks_like_high_risk_boundary_change(prompt_text, repo_signals)
    if non_behavioral and not packet_unclear:
        return False
    return boundary_risk or packet_unclear
