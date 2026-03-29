from __future__ import annotations

import json
from pathlib import Path

from common import default_artifact_dir
from map_codebase_focus import build_focus_content


def _write(path: Path, content: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return str(path)


def persist_map_report(report: dict, output_dir: str | None, focus: str | None) -> dict[str, str]:
    root = default_artifact_dir(output_dir, "codebase")
    summary_md = "\n".join(
        [
            "# Codebase Summary",
            "",
            f"- Project: {report['project_name']}",
            f"- Languages: {', '.join(report['stack']['languages']) or '(none)'}",
            f"- Frameworks: {', '.join(report['stack']['frameworks']) or '(none)'}",
            f"- Companions: {', '.join(item['id'] for item in report.get('companions', [])) or '(none)'}",
            f"- Verification packs: {', '.join(item['verification_pack'] or '(none)' for item in report.get('companion_operator', [])) or '(none)'}",
            f"- Package managers: {', '.join(report['stack']['package_managers']) or '(none)'}",
            f"- Next actions: {', '.join(report['structure']['next_actions'])}",
        ]
    )
    architecture_md = "\n".join(["# Architecture", "", f"- Entrypoints: {', '.join(report['structure']['entrypoints']) or '(none)'}", f"- Top-level directories: {', '.join(report['structure']['top_level_dirs']) or '(none)'}"])
    conventions_md = "\n".join(["# Conventions", "", f"- Manifests: {', '.join(report['stack']['manifests']) or '(none)'}", f"- Testing paths: {', '.join(report['structure']['testing_paths']) or '(none)'}"])
    testing_md = "\n".join(["# Testing", "", f"- Test tools: {', '.join(report['stack']['test_tools']) or '(none)'}", f"- Testing paths: {', '.join(report['structure']['testing_paths']) or '(none)'}"])
    integrations_md = "\n".join(["# Integrations", "", *[f"- {item}" for item in (report['structure']['integrations'] or ['No obvious integrations detected.'])]])
    risks_md = "\n".join(["# Risks", "", *[f"- {item}" for item in (report['structure']['risks'] or ['No obvious risks detected from root markers.'])]])
    questions_md = "\n".join(["# Open Questions", "", *[f"- {item}" for item in (report['structure']['open_questions'] or ['No open questions detected.'])]])
    artifacts = {
        "summary_markdown": _write(root / "summary.md", summary_md),
        "summary_json": _write(root / "summary.json", json.dumps(report, indent=2, ensure_ascii=False)),
        "stack_json": _write(root / "stack.json", json.dumps(report["stack"], indent=2, ensure_ascii=False)),
        "architecture": _write(root / "architecture.md", architecture_md),
        "conventions": _write(root / "conventions.md", conventions_md),
        "testing": _write(root / "testing.md", testing_md),
        "integrations": _write(root / "integrations.md", integrations_md),
        "risks": _write(root / "risks.md", risks_md),
        "open_questions": _write(root / "open-questions.md", questions_md),
    }
    if focus:
        artifacts["focus"] = _write(root / "focus" / f"{focus}.md", build_focus_content(report, focus))
    return artifacts
