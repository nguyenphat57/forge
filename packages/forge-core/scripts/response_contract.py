from __future__ import annotations

import re

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

SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def _normalize_expected_skills(expected_skills: list[str] | None) -> list[str] | None:
    if expected_skills is None:
        return None

    normalized: list[str] = []
    seen: set[str] = set()
    for skill in expected_skills:
        candidate = skill.strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        normalized.append(candidate)
    return normalized


def validate_skill_usage_footer(
    text: str,
    *,
    footer_contract: dict[str, object],
    expected_skills: list[str] | None = None,
) -> dict[str, object]:
    prefix = str(footer_contract.get("prefix", "Skills used:"))
    none_token = str(footer_contract.get("none_token", "none"))
    separator = str(footer_contract.get("separator", ","))
    require_footer = bool(footer_contract.get("require_on_every_response", False))
    require_final_line = bool(footer_contract.get("require_final_line", True))
    require_unique_skills = bool(footer_contract.get("require_unique_skills", True))
    allow_none_token = bool(footer_contract.get("allow_none_token", True))

    findings: list[str] = []
    nonempty_lines = [line.strip() for line in text.splitlines() if line.strip()]
    footer_line = nonempty_lines[-1] if nonempty_lines else None
    normalized_expected = _normalize_expected_skills(expected_skills)
    if normalized_expected:
        require_footer = True

    if not footer_line:
        if require_footer:
            findings.append(f"Skill usage footer required as final non-empty line: `{prefix} ...`")
        return {
            "status": "PASS" if not findings else "FAIL",
            "footer_line": None,
            "skills": [],
            "findings": findings,
        }

    if require_final_line and not footer_line.casefold().startswith(prefix.casefold()):
        if require_footer:
            findings.append(f"Skill usage footer required as final non-empty line: `{prefix} ...`")
        return {
            "status": "PASS" if not findings else "FAIL",
            "footer_line": footer_line,
            "skills": [],
            "findings": findings,
        }

    if not footer_line.casefold().startswith(prefix.casefold()):
        return {
            "status": "PASS",
            "footer_line": footer_line,
            "skills": [],
            "findings": [],
        }

    payload = footer_line[len(prefix):].strip()
    if not payload:
        findings.append("Skill usage footer is missing the skill list or `none` marker.")
        return {
            "status": "FAIL",
            "footer_line": footer_line,
            "skills": [],
            "findings": findings,
        }

    if payload.casefold() == none_token.casefold():
        actual_skills: list[str] = []
        if not allow_none_token:
            findings.append("Skill usage footer must be omitted when no workflow skills were used.")
    else:
        actual_skills = []
        seen: set[str] = set()
        for raw_part in payload.split(separator):
            skill = raw_part.strip()
            if not skill:
                findings.append("Skill usage footer contains an empty skill name.")
                continue
            if not SKILL_NAME_PATTERN.fullmatch(skill):
                findings.append(f"Skill usage footer contains an invalid skill name: {skill}")
                continue
            if skill in seen:
                if require_unique_skills:
                    findings.append(f"Skill usage footer repeats a skill name: {skill}")
                continue
            seen.add(skill)
            actual_skills.append(skill)

    if normalized_expected is not None and actual_skills != normalized_expected:
        expected_label = ", ".join(normalized_expected) if normalized_expected else none_token
        actual_label = ", ".join(actual_skills) if actual_skills else none_token
        findings.append(
            f"Skill usage footer mismatch: expected `{prefix} {expected_label}`, got `{prefix} {actual_label}`."
        )

    return {
        "status": "PASS" if not findings else "FAIL",
        "footer_line": footer_line,
        "skills": actual_skills,
        "findings": findings,
    }


def validate_skill_selection_explanation(
    text: str,
    *,
    explanation_contract: dict[str, object],
    expected_skills: list[str] | None = None,
) -> dict[str, object]:
    heading = str(explanation_contract.get("heading", "Skill selection:"))
    none_prefix = str(explanation_contract.get("none_prefix", "none -"))
    bullet_prefix = str(explanation_contract.get("bullet_prefix", "- "))
    require_block = bool(explanation_contract.get("require_on_every_response", False))
    require_at_start = bool(explanation_contract.get("require_at_start", True))
    require_reason_text = bool(explanation_contract.get("require_reason_text", True))
    require_match_with_footer = bool(explanation_contract.get("require_match_with_footer", True))
    allow_explanation = bool(explanation_contract.get("allow_in_responses", True))

    findings: list[str] = []
    nonempty_lines = [line.strip() for line in text.splitlines() if line.strip()]
    normalized_expected = _normalize_expected_skills(expected_skills)

    if not allow_explanation:
        block_lines = [line for line in nonempty_lines if line.casefold().startswith(heading.casefold())]
        if block_lines:
            findings.append("Skill selection explanation is deprecated; report workflow skill names only in `Skills used:`.")
        return {
            "status": "PASS" if not findings else "FAIL",
            "mode": None,
            "skills": [],
            "block_lines": block_lines,
            "findings": findings,
        }

    if not nonempty_lines:
        if require_block:
            findings.append(
                "Skill selection explanation required at the start of the response."
            )
        return {
            "status": "PASS" if not findings else "FAIL",
            "mode": None,
            "skills": [],
            "block_lines": [],
            "findings": findings,
        }

    block_lines: list[str] = []
    mode: str | None = None
    actual_skills: list[str] = []

    candidate_line = nonempty_lines[0]
    if candidate_line.casefold().startswith(heading.casefold()):
        payload = candidate_line[len(heading):].strip()
        if payload.casefold().startswith(none_prefix.casefold()):
            mode = "none"
            reason_text = payload[len(none_prefix):].strip()
            if require_reason_text and not reason_text:
                findings.append("Skill selection `none` explanation is missing the reason text.")
            block_lines = [candidate_line]
        elif payload:
            findings.append("Skill selection heading should not include inline skill bullets.")
        else:
            cursor = 1
            collected: list[str] = []
            while cursor < len(nonempty_lines) and nonempty_lines[cursor].startswith(bullet_prefix):
                collected.append(nonempty_lines[cursor])
                cursor += 1
            if collected:
                mode = "skills"
                block_lines = [candidate_line, *collected]
                seen: set[str] = set()
                for line in block_lines[1:]:
                    payload = line[len(bullet_prefix):].strip()
                    skill, separator, reason = payload.partition(":")
                    skill = skill.strip()
                    reason = reason.strip()
                    if not separator:
                        findings.append(f"Skill selection bullet is missing `:` separator: {line}")
                        continue
                    if not SKILL_NAME_PATTERN.fullmatch(skill):
                        findings.append(f"Skill selection bullet contains an invalid skill name: {skill}")
                        continue
                    if skill in seen:
                        findings.append(f"Skill selection explanation repeats a skill name: {skill}")
                        continue
                    seen.add(skill)
                    actual_skills.append(skill)
                    if require_reason_text and not reason:
                        findings.append(f"Skill selection bullet is missing the reason text for `{skill}`.")
            else:
                findings.append("Skill selection block is missing bullet lines after the opening heading.")
    elif require_block:
        findings.append(
            "Skill selection explanation required at the start of the response."
        )

    if normalized_expected is not None and require_match_with_footer:
        if mode == "none":
            if normalized_expected:
                findings.append("Skill selection explanation says `none` but the footer lists Forge skills.")
        elif actual_skills != normalized_expected:
            expected_label = ", ".join(normalized_expected) if normalized_expected else "none"
            actual_label = ", ".join(actual_skills) if actual_skills else "none"
            findings.append(
                "Skill selection explanation mismatch: "
                f"expected `{expected_label}`, got `{actual_label}`."
            )

    return {
        "status": "PASS" if not findings else "FAIL",
        "mode": mode,
        "skills": actual_skills,
        "block_lines": block_lines,
        "findings": findings,
    }


def validate_response_contract(
    text: str,
    *,
    output_contract: dict[str, object] | None = None,
    registry: dict | None = None,
    require_evidence_response: bool = False,
    expected_skills: list[str] | None = None,
) -> dict[str, object]:
    resolved_output_contract = output_contract or {}
    resolved_registry = registry or load_registry()
    evidence_contract = resolved_registry.get("evidence_response_contract", {})
    skill_usage_contract = resolved_registry.get("skill_usage_footer_contract", {})
    skill_selection_contract = resolved_registry.get("skill_selection_explanation_contract", {})

    prose = strip_markdown_code(text)
    banned_hits = collect_phrase_hits(prose, evidence_contract.get("banned_phrases", []))
    rationalization_hits = collect_phrase_hits(prose, resolved_registry.get("rationalization_patterns", []))
    evidence_required = require_evidence_response or response_claims_completion(prose)

    evidence_report = validate_evidence_response(
        text,
        required=evidence_required,
    )
    skill_usage_report = validate_skill_usage_footer(
        text,
        footer_contract=skill_usage_contract,
        expected_skills=expected_skills,
    )
    skill_selection_report = validate_skill_selection_explanation(
        text,
        explanation_contract=skill_selection_contract,
        expected_skills=expected_skills if expected_skills is not None else skill_usage_report["skills"],
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
    findings.extend(skill_selection_report["findings"])
    findings.extend(skill_usage_report["findings"])
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
            "skill_selection_explanation": skill_selection_report,
            "skill_usage_footer": skill_usage_report,
            "vietnamese_output": vietnamese_report,
            "tone_detail_output": tone_detail_report,
        },
        "findings": findings,
        "warnings": warnings,
    }
