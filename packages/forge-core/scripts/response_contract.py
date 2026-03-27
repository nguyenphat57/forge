from __future__ import annotations

from response_contract_evidence import (
    CHANGE_MARKERS,
    COMPLETION_MARKERS,
    EVIDENCE_STARTERS,
    NO_CHANGE_MARKERS,
    REASON_MARKERS,
    detect_evidence_mode,
    response_claims_completion,
    validate_evidence_response,
)
from response_contract_locale import (
    MOJIBAKE_MARKERS,
    VIETNAMESE_DIACRITIC_CHARACTERS,
    VIETNAMESE_UNACCENTED_TOKENS,
    validate_tone_detail_output,
    validate_vietnamese_output,
)
from response_contract_text import collect_phrase_hits, prose_lines, strip_markdown_code
from skill_routing import load_registry


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
