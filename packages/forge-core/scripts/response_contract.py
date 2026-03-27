from __future__ import annotations

import re
from typing import Iterable

from skill_routing import keyword_in_text, load_registry
from text_utils import normalize_text


MOJIBAKE_MARKERS = (
    "Ã",
    "á»",
    "Ä‘",
    "Æ°",
    "â€œ",
    "â€",
)

VIETNAMESE_DIACRITIC_CHARACTERS = set(
    "ăâđêôơư"
    "áàảãạắằẳẵặấầẩẫậ"
    "éèẻẽẹếềểễệ"
    "íìỉĩị"
    "óòỏõọốồổỗộớờởỡợ"
    "úùủũụứừửữự"
    "ýỳỷỹỵ"
    "ĂÂĐÊÔƠƯ"
    "ÁÀẢÃẠẮẰẲẴẶẤẦẨẪẬ"
    "ÉÈẺẼẸẾỀỂỄỆ"
    "ÍÌỈĨỊ"
    "ÓÒỎÕỌỐỒỔỖỘỚỜỞỠỢ"
    "ÚÙỦŨỤỨỪỬỮỰ"
    "ÝỲỶỸỴ"
)

VIETNAMESE_UNACCENTED_TOKENS = {
    "anh",
    "can",
    "chon",
    "chua",
    "dang",
    "da",
    "de",
    "duoc",
    "giai",
    "giu",
    "huong",
    "kiem",
    "khong",
    "lam",
    "loi",
    "luc",
    "neu",
    "ngay",
    "nguoc",
    "nhung",
    "phan",
    "ro",
    "sau",
    "sua",
    "them",
    "thich",
    "thu",
    "tiep",
    "toi",
    "tra",
    "truoc",
    "tuong",
    "va",
    "van",
    "vi",
    "viec",
    "voi",
    "xac",
}

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


def strip_markdown_code(text: str) -> str:
    stripped = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    stripped = re.sub(r"`[^`]*`", " ", stripped)
    return stripped


def prose_lines(text: str) -> list[str]:
    cleaned: list[str] = []
    for raw_line in strip_markdown_code(text).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^(?:[-*+]\s+|\d+\.\s+|>\s+)", "", line)
        if line:
            cleaned.append(line)
    return cleaned


def collect_phrase_hits(text: str, phrases: Iterable[str]) -> list[str]:
    normalized_text = normalize_text(text)
    hits: list[str] = []
    seen: set[str] = set()
    for phrase in phrases:
        normalized_phrase = normalize_text(phrase)
        if not normalized_phrase or normalized_phrase in seen:
            continue
        seen.add(normalized_phrase)
        if keyword_in_text(normalized_phrase, normalized_text):
            hits.append(phrase)
    return hits


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

    if mode == "verified":
        has_stance = any(keyword_in_text(marker, normalized_text) for marker in CHANGE_MARKERS)
    else:
        has_stance = any(keyword_in_text(marker, normalized_text) for marker in [*CHANGE_MARKERS, *NO_CHANGE_MARKERS])

    if not has_stance:
        findings.append("Structured response is missing a clear change or no-change stance.")

    return {
        "status": "PASS" if not findings else "FAIL",
        "mode": mode,
        "findings": findings,
    }


def validate_vietnamese_output(text: str, output_contract: dict[str, object]) -> dict[str, object]:
    language = output_contract.get("language")
    user_facing_language = output_contract.get("user_facing_language")
    orthography = output_contract.get("orthography")
    accent_policy = output_contract.get("accent_policy")

    requires_vietnamese = language == "vi" or user_facing_language == "vietnamese"
    requires_diacritics = orthography == "vietnamese-diacritics" or accent_policy == "required"
    if not requires_vietnamese and not requires_diacritics:
        return {
            "status": "PASS",
            "findings": [],
            "warnings": [],
        }

    findings: list[str] = []
    warnings: list[str] = []
    prose = strip_markdown_code(text)
    normalized_prose = normalize_text(prose)
    word_count = len(re.findall(r"[a-zA-Z]+", normalized_prose))
    has_diacritics = any(char in VIETNAMESE_DIACRITIC_CHARACTERS for char in prose)
    matched_unaccented_tokens = sorted(
        {
            token
            for token in re.findall(r"[a-z]+", normalized_prose)
            if token in VIETNAMESE_UNACCENTED_TOKENS
        }
    )

    if any(marker in prose for marker in MOJIBAKE_MARKERS):
        findings.append("Output appears mojibake; Vietnamese text must stay valid UTF-8.")

    if requires_vietnamese and not has_diacritics:
        if len(matched_unaccented_tokens) >= 2:
            findings.append(
                "Output appears to be accent-stripped Vietnamese while the contract requires full diacritics."
            )
        elif word_count >= 8:
            findings.append("Output does not appear to be Vietnamese prose even though the contract requires it.")
        else:
            warnings.append("Not enough prose to confidently validate Vietnamese orthography.")

    return {
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
        "warnings": warnings,
        "matched_unaccented_tokens": matched_unaccented_tokens,
    }


def validate_tone_detail_output(text: str, output_contract: dict[str, object]) -> dict[str, object]:
    tone_detail = output_contract.get("tone_detail")
    if not isinstance(tone_detail, str) or not tone_detail.strip():
        return {
            "status": "PASS",
            "findings": [],
            "warnings": [],
        }

    normalized_tone = normalize_text(tone_detail)
    normalized_prose = normalize_text(strip_markdown_code(text))
    findings: list[str] = []
    warnings: list[str] = []

    if "goi sep" in normalized_tone and "xung em" in normalized_tone:
        if not re.search(r"\bsep\b", normalized_prose):
            findings.append("Tone detail requires addressing the user as 'Sếp'.")
        if re.search(r"\banh\b", normalized_prose):
            findings.append("Tone detail requires xưng 'Em'; found 'anh' in the response prose.")
        if not re.search(r"\bem\b", normalized_prose):
            warnings.append("Tone detail prefers explicit self-reference as 'Em'.")

    return {
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
        "warnings": warnings,
    }


def validate_response_contract(
    text: str,
    *,
    output_contract: dict[str, object] | None = None,
    registry: dict | None = None,
    require_evidence_response: bool = False,
) -> dict[str, object]:
    resolved_output_contract = output_contract or {}
    resolved_registry = registry or load_registry()
    evidence_contract = resolved_registry.get("evidence_response_contract", {})

    prose = strip_markdown_code(text)
    banned_hits = collect_phrase_hits(prose, evidence_contract.get("banned_phrases", []))
    rationalization_hits = collect_phrase_hits(prose, resolved_registry.get("rationalization_patterns", []))
    evidence_required = require_evidence_response or response_claims_completion(prose)

    evidence_report = validate_evidence_response(
        text,
        required=evidence_required,
    )
    vietnamese_report = validate_vietnamese_output(text, resolved_output_contract)
    tone_detail_report = validate_tone_detail_output(text, resolved_output_contract)

    findings: list[str] = []
    warnings: list[str] = []

    for phrase in banned_hits:
        findings.append(f"Banned phrase detected: {phrase}")
    for phrase in rationalization_hits:
        findings.append(f"Weak rationalization detected: {phrase}")
    findings.extend(evidence_report["findings"])
    findings.extend(vietnamese_report["findings"])
    findings.extend(tone_detail_report["findings"])
    warnings.extend(vietnamese_report.get("warnings", []))
    warnings.extend(tone_detail_report.get("warnings", []))

    if findings:
        status = "FAIL"
    elif warnings:
        status = "WARN"
    else:
        status = "PASS"

    return {
        "status": status,
        "output_contract": resolved_output_contract,
        "evidence_required": evidence_required,
        "checks": {
            "banned_phrases": banned_hits,
            "rationalization_patterns": rationalization_hits,
            "evidence_response": evidence_report,
            "vietnamese_output": vietnamese_report,
            "tone_detail_output": tone_detail_report,
        },
        "findings": findings,
        "warnings": warnings,
    }
