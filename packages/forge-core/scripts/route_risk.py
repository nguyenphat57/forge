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
