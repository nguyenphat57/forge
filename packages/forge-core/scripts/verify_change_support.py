from __future__ import annotations

import json
import re
from pathlib import Path

from change_artifacts_paths import resolve_change_paths
from common import default_artifact_dir, slugify, timestamp_slug


REQUIRED_ARTIFACT_KEYS = (
    "proposal",
    "design",
    "implementation_packet",
    "tasks",
    "verification",
    "resume",
    "status",
)
SPEC_SECTIONS = ("## Added Behavior", "## Modified Behavior", "## Acceptance Scenarios")
STRONG_EVIDENCE_MARKERS = (
    "pytest",
    "vitest",
    "jest",
    "playwright",
    "npm test",
    "pnpm test",
    "yarn test",
    "go test",
    "cargo test",
    "dotnet test",
    "mvn test",
    "gradle test",
    "build",
    "lint",
    "typecheck",
    "smoke",
    "manual scenario",
)
STOP_WORDS = {
    "about",
    "after",
    "before",
    "change",
    "feature",
    "implement",
    "medium",
    "large",
    "scope",
    "summary",
    "state",
    "tasks",
    "verification",
}


def _pick_latest_json(base_dir: Path) -> Path | None:
    if not base_dir.exists():
        return None
    candidates = sorted(base_dir.rglob("*.json"), key=lambda item: (item.stat().st_mtime, str(item).lower()))
    return candidates[-1] if candidates else None


def _read_json_object(path: Path | None) -> dict:
    if path is None or not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _score(checks: list[bool]) -> int:
    if not checks:
        return 0
    return round((sum(1 for item in checks if item) / len(checks)) * 100)


def _keywords(text: str) -> list[str]:
    values = re.findall(r"[a-z0-9]{4,}", text.lower())
    return [value for value in values if value not in STOP_WORDS][:8]


def _has_keywords(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def _resolve_paths(workspace: Path, slug: str | None) -> dict[str, Path]:
    if slug:
        return resolve_change_paths(workspace, slug=slug)
    status_path = _pick_latest_json(default_artifact_dir(str(workspace), "changes") / "active")
    if status_path is None:
        raise FileNotFoundError("No active change artifacts found under .forge-artifacts/changes/active.")
    return resolve_change_paths(workspace, slug=status_path.parent.name)


def evaluate_change(workspace: Path, slug: str | None = None) -> dict:
    paths = _resolve_paths(workspace, slug)
    status_payload = _read_json_object(paths["status"])
    verification_state = status_payload.get("verification", {}) if isinstance(status_payload.get("verification"), dict) else {}
    summary = status_payload.get("summary") or paths["active_root"].name
    texts = {key: _read_text(paths[key]) for key in REQUIRED_ARTIFACT_KEYS if key in paths}
    spec_files = sorted(paths["specs_root"].rglob("spec.md")) if paths["specs_root"].exists() else []
    spec_text = "\n".join(path.read_text(encoding="utf-8") for path in spec_files)
    missing_artifacts = [key for key in REQUIRED_ARTIFACT_KEYS if not paths[key].exists()]
    if not spec_files:
        missing_artifacts.append("specs")

    completeness = _score([key not in missing_artifacts for key in (*REQUIRED_ARTIFACT_KEYS, "specs")])
    correctness_checks = [
        bool(summary),
        summary in texts["proposal"] or summary in texts["resume"],
        "- [ ]" in texts["tasks"] or "- [x]" in texts["tasks"].lower(),
        "specs/" in texts["implementation_packet"],
        all(section in spec_text for section in SPEC_SECTIONS),
        bool(status_payload.get("state")),
    ]
    if status_payload.get("state") in {"ready-for-review", "ready-for-merge", "archived"}:
        correctness_checks.append(bool(verification_state.get("latest_result")))
    correctness = _score(correctness_checks)

    summary_keywords = _keywords(summary)
    coherence = _score(
        [
            bool(summary_keywords),
            _has_keywords(texts["proposal"], summary_keywords),
            _has_keywords(texts["design"], summary_keywords),
            _has_keywords(texts["tasks"], summary_keywords),
            _has_keywords(spec_text, summary_keywords),
            _has_keywords(texts["implementation_packet"], summary_keywords),
        ]
    )

    latest_result = str(verification_state.get("latest_result", "")).strip()
    evidence_strength = _score(
        [
            bool(latest_result),
            "## Update" in texts["verification"],
            any(marker in latest_result.lower() for marker in STRONG_EVIDENCE_MARKERS),
            "Verification method not recorded yet." not in texts["verification"],
        ]
    )
    residual_risk = verification_state.get("residual_risk", [])
    residual_risk = residual_risk if isinstance(residual_risk, list) else []
    residual_risk_score = min(len(residual_risk) * 25, 100)

    recommendations: list[str] = []
    if missing_artifacts:
        recommendations.append(f"Restore missing change artifacts: {', '.join(missing_artifacts)}.")
    if not latest_result:
        recommendations.append("Record a fresh verification result before final handoff.")
    if residual_risk:
        recommendations.append("Review residual risk items before merge or deploy claims.")

    status = "PASS"
    if missing_artifacts or completeness < 100 or correctness < 70 or evidence_strength < 50:
        status = "FAIL"
    elif coherence < 60 or evidence_strength < 70 or residual_risk_score > 0:
        status = "WARN"

    return {
        "status": status,
        "decision": {"PASS": "ready", "WARN": "revise", "FAIL": "blocked"}[status],
        "workspace": str(workspace),
        "slug": status_payload.get("slug") or paths["active_root"].name,
        "summary": summary,
        "change_state": status_payload.get("state"),
        "active_root": str(paths["active_root"]),
        "spec_files": [str(path) for path in spec_files],
        "missing_artifacts": missing_artifacts,
        "scores": {
            "completeness": completeness,
            "correctness": correctness,
            "coherence": coherence,
            "evidence_strength": evidence_strength,
            "residual_risk": residual_risk_score,
        },
        "verification": {
            "latest_result": latest_result or None,
            "residual_risk_items": residual_risk,
        },
        "recommendations": recommendations,
    }


def format_report(report: dict) -> str:
    lines = [
        "Forge Verify Change",
        f"- Status: {report['status']}",
        f"- Decision: {report['decision']}",
        f"- Workspace: {report['workspace']}",
        f"- Change: {report['slug']}",
        f"- Summary: {report['summary']}",
        f"- State: {report['change_state'] or '(unknown)'}",
        "- Scores:",
    ]
    for key, value in report["scores"].items():
        lines.append(f"  - {key}: {value}")
    lines.append(f"- Spec files: {', '.join(report['spec_files']) or '(none)'}")
    lines.append(f"- Missing artifacts: {', '.join(report['missing_artifacts']) or '(none)'}")
    lines.append(f"- Latest verification: {report['verification']['latest_result'] or '(none)'}")
    if report["verification"]["residual_risk_items"]:
        lines.append("- Residual risk:")
        for item in report["verification"]["residual_risk_items"]:
            lines.append(f"  - {item}")
    if report["recommendations"]:
        lines.append("- Recommendations:")
        for item in report["recommendations"]:
            lines.append(f"  - {item}")
    return "\n".join(lines)


def persist_report(report: dict, output_dir: str | None) -> tuple[Path, Path]:
    artifact_dir = default_artifact_dir(output_dir, "verify-change") / slugify(report["slug"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{timestamp_slug()}-{slugify(report['summary'])[:48]}"
    json_path = artifact_dir / f"{stem}.json"
    md_path = artifact_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(format_report(report), encoding="utf-8")
    return json_path, md_path


def load_latest_verify_change(workspace: Path, slug: str | None = None) -> tuple[Path, dict] | None:
    base_dir = default_artifact_dir(str(workspace), "verify-change")
    target_dir = base_dir / slugify(slug) if slug else base_dir
    latest_path = _pick_latest_json(target_dir)
    payload = _read_json_object(latest_path)
    if latest_path is None or not payload:
        return None
    return latest_path, payload
