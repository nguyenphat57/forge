from __future__ import annotations

from response_contract_text import prose_lines, strip_markdown_code
from skill_routing import keyword_in_text
from text_utils import normalize_text


EVIDENCE_STARTERS = {
    "verified": [
        "i verified:",
        "verified:",
        "da xac minh:",
        "em da xac minh:",
        "da kiem chung:",
        "em da kiem chung:",
    ],
    "evaluated": [
        "i evaluated:",
        "i investigated:",
        "evaluated:",
        "investigated:",
        "da danh gia:",
        "em da danh gia:",
        "da dieu tra:",
        "em da dieu tra:",
    ],
    "clarification": [
        "clarification needed:",
        "can lam ro:",
        "em can lam ro:",
    ],
}

REASON_MARKERS = [
    "because",
    "reason",
    "correct because",
    "stays because",
    "vi",
    "ly do",
    "dung vi",
    "giu nguyen vi",
]

CHANGE_MARKERS = [
    "fixed:",
    "fixed",
    "changed:",
    "changed",
    "updated:",
    "updated",
    "da sua:",
    "da sua",
    "em da sua:",
    "em da sua",
    "da cap nhat:",
    "da cap nhat",
    "em da cap nhat:",
    "em da cap nhat",
]

NO_CHANGE_MARKERS = [
    "current code stays",
    "stays because",
    "no change",
    "keep current code",
    "giu nguyen",
    "khong doi code",
    "khong can doi code",
]

COMPLETION_MARKERS = [
    "done",
    "ready",
    "fixed",
    "resolved",
    "shipped",
    "deployed",
    "xong",
    "da sua",
    "da xong",
    "da trien khai",
    "san sang",
]


def detect_evidence_mode(text: str) -> dict[str, object]:
    for line in prose_lines(text):
        normalized_line = normalize_text(line)
        for mode, starters in EVIDENCE_STARTERS.items():
            for starter in starters:
                if normalized_line.startswith(starter):
                    return {
                        "mode": mode,
                        "line": line,
                        "normalized_line": normalized_line,
                    }
    return {
        "mode": None,
        "line": None,
        "normalized_line": None,
    }


def response_claims_completion(text: str) -> bool:
    normalized_text = normalize_text(strip_markdown_code(text))
    return any(keyword_in_text(marker, normalized_text) for marker in COMPLETION_MARKERS)


def validate_evidence_response(text: str, *, required: bool) -> dict[str, object]:
    mode_info = detect_evidence_mode(text)
    mode = mode_info["mode"]
    if not required and mode is None:
        return {
            "status": "PASS",
            "mode": None,
            "findings": [],
        }

    if mode is None:
        return {
            "status": "FAIL",
            "mode": None,
            "findings": [
                "Evidence response required but no structured lead-in was found.",
            ],
        }

    normalized_text = normalize_text(strip_markdown_code(text))
    findings: list[str] = []

    if mode == "clarification":
        if strip_markdown_code(text).count("?") != 1:
            findings.append("Clarification responses must contain exactly one question.")
        status = "PASS" if not findings else "FAIL"
        return {
            "status": status,
            "mode": mode,
            "findings": findings,
        }

    has_reason = any(keyword_in_text(marker, normalized_text) for marker in REASON_MARKERS)
    if not has_reason:
        findings.append("Structured response is missing an explicit reason marker.")

    stance_markers = CHANGE_MARKERS if mode == "verified" else [*CHANGE_MARKERS, *NO_CHANGE_MARKERS]
    has_stance = any(keyword_in_text(marker, normalized_text) for marker in stance_markers)
    if not has_stance:
        findings.append("Structured response is missing a clear change or no-change stance.")

    return {
        "status": "PASS" if not findings else "FAIL",
        "mode": mode,
        "findings": findings,
    }
