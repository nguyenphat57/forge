from __future__ import annotations

import argparse
from pathlib import Path

from prepare_bump_git import infer_bump_token, infer_confidence
from prepare_bump_semver import bump_version, detect_verify_command, parse_version, update_changelog_content


def build_report(args: argparse.Namespace) -> dict:
    workspace = args.workspace.resolve()
    version_path = workspace / "VERSION"
    changelog_path = workspace / "CHANGELOG.md"
    if not version_path.exists():
        raise FileNotFoundError(f"Missing VERSION file: {version_path}")
    if not changelog_path.exists():
        raise FileNotFoundError(f"Missing CHANGELOG.md: {changelog_path}")

    current_version = version_path.read_text(encoding="utf-8").strip()
    parse_version(current_version)
    requested_bump = (args.bump or "auto").strip()
    bump_source = "explicit"
    inferred_from = None
    inference_reasons: list[str] = []
    inference_confidence = None
    analysis_changed_files: list[str] = []
    warnings: list[str] = []

    if not requested_bump or requested_bump.lower() == "auto":
        selected_bump, inferred_from, inference_reasons, analysis_changed_files, warnings = infer_bump_token(workspace)
        inference_confidence = infer_confidence(selected_bump, warnings, inference_reasons, inferred_from)
        bump_source = "inferred"
    else:
        selected_bump = requested_bump

    target_version = bump_version(current_version, selected_bump)
    changelog_preview = update_changelog_content(changelog_path.read_text(encoding="utf-8"), target_version)

    changed_files = ["VERSION", "CHANGELOG.md"]
    verification_commands = [["git", "diff", "--stat"]]
    verify_command = detect_verify_command(workspace)
    if verify_command != verification_commands[0]:
        verification_commands.append(verify_command)
    if args.release_ready and verify_command not in verification_commands:
        verification_commands.append(verify_command)

    if args.apply:
        version_path.write_text(f"{target_version}\n", encoding="utf-8")
        changelog_path.write_text(changelog_preview, encoding="utf-8")

    status = "PASS"
    if target_version == current_version:
        status = "WARN"
        warnings.append("Target version matches the current version.")
    if bump_source == "inferred" and inference_confidence == "low":
        status = "WARN"
        warnings.append("Inferred bump has low confidence; consider overriding with --bump patch|minor|major.")

    return {
        "status": status,
        "workspace": str(workspace),
        "current_version": current_version,
        "target_version": target_version,
        "bump": requested_bump or "auto",
        "selected_bump": selected_bump,
        "bump_source": bump_source,
        "inference_confidence": inference_confidence,
        "inferred_from": inferred_from,
        "inference_reasons": inference_reasons,
        "analysis_changed_files": analysis_changed_files,
        "applied": args.apply,
        "changed_files": changed_files,
        "verification_commands": [" ".join(command) for command in verification_commands],
        "warnings": warnings,
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Bump Preparation",
        f"- Status: {report['status']}",
        f"- Workspace: {report['workspace']}",
        f"- Version: {report['current_version']} -> {report['target_version']}",
        f"- Bump source: {report['bump_source']}",
        f"- Selected bump: {report['selected_bump']}",
        f"- Applied: {'yes' if report['applied'] else 'no'}",
        "- Changed files:",
    ]
    for item in report["changed_files"]:
        lines.append(f"  - {item}")
    lines.append("- Verification commands:")
    for item in report["verification_commands"]:
        lines.append(f"  - {item}")
    if report["inference_reasons"]:
        lines.append("- Inference reasons:")
        for item in report["inference_reasons"]:
            lines.append(f"  - {item}")
    if report["analysis_changed_files"]:
        lines.append("- Analysis changed files:")
        for item in report["analysis_changed_files"][:10]:
            lines.append(f"  - {item}")
    if report["inference_confidence"]:
        lines.append(f"- Inference confidence: {report['inference_confidence']}")
    if report["inferred_from"]:
        lines.append(f"- Inferred from: {report['inferred_from']}")
    if report["warnings"]:
        lines.append("- Warnings:")
        for item in report["warnings"]:
            lines.append(f"  - {item}")
    else:
        lines.append("- Warnings: (none)")
    return "\n".join(lines)
