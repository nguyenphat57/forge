from __future__ import annotations

import argparse
import json
from pathlib import Path

from companion_operator_context import collect_operator_context
from common import configure_stdio
from companion_invoke import invoke_companion_capability
from companion_matching import match_companions
from map_codebase_detect import detect_stack
from map_codebase_report import persist_map_report
from map_codebase_structure import scan_structure


def _merge_unique(items: list[str], additions: list[str]) -> list[str]:
    merged = list(items)
    for item in additions:
        if item not in merged:
            merged.append(item)
    return merged


def _apply_companion_enrichment(stack: dict, structure: dict, enrichment: dict) -> None:
    extra_stack = enrichment.get("stack")
    if isinstance(extra_stack, dict):
        for key, value in extra_stack.items():
            if isinstance(value, list):
                stack[key] = _merge_unique(list(stack.get(key, [])), [str(item) for item in value])
            else:
                stack[key] = value
    extra_structure = enrichment.get("structure")
    if isinstance(extra_structure, dict):
        for key, value in extra_structure.items():
            if isinstance(value, list):
                structure[key] = _merge_unique(list(structure.get(key, [])), [str(item) for item in value])
            else:
                structure[key] = value


def _format_text(report: dict) -> str:
    lines = [
        "Forge Map-Codebase",
        f"- Status: {report['status']}",
        f"- Workspace: {report['workspace']}",
        f"- Project: {report['project_name']}",
        f"- Languages: {', '.join(report['stack']['languages']) or '(none)'}",
        f"- Frameworks: {', '.join(report['stack']['frameworks']) or '(none)'}",
        f"- Entrypoints: {', '.join(report['brownfield']['entrypoints']) or '(none)'}",
        f"- Optional companions: {', '.join(item['id'] for item in report.get('companions', [])) or '(none)'}",
        f"- Optional verification packs: {', '.join(item['verification_pack'] or '(none)' for item in report.get('companion_operator', [])) or '(none)'}",
        "- Brownfield next actions:",
    ]
    for item in report["brownfield"]["next_actions"]:
        lines.append(f"  - {item}")
    lines.append("- Open questions:")
    for item in report["brownfield"]["open_questions"] or ["(none)"]:
        lines.append(f"  - {item}")
    lines.append("- Risks:")
    for item in report["brownfield"]["risks"] or ["(none)"]:
        lines.append(f"  - {item}")
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Build a durable brownfield codebase map for Forge.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root to inspect")
    parser.add_argument("--focus", default=None, help="Optional focus area such as api, auth, frontend, or deploy")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    stack = detect_stack(workspace)
    structure = scan_structure(workspace, stack)
    companions = match_companions(workspace=workspace)
    operator_context = {item["id"]: item for item in collect_operator_context(companions, workspace)}
    companion_summaries: list[dict] = []
    for companion in companions:
        enrichment = invoke_companion_capability(companion, "map_enrichers", workspace)
        if enrichment is not None:
            _apply_companion_enrichment(stack, structure, enrichment.get("enrichments", {}))
        companion_summaries.append(
            {
                "id": companion["id"],
                "strength": companion["strength"],
                "features": companion["features"],
                "reasons": companion["reasons"],
            }
        )
    report = {
        "status": "PASS",
        "workspace": str(workspace),
        "project_name": stack["project_name"],
        "stack": stack,
        "structure": structure,
        "brownfield": {
            "core_only_ready": True,
            "entrypoints": structure["entrypoints"],
            "next_actions": structure["next_actions"],
            "open_questions": structure["open_questions"],
            "risks": structure["risks"],
        },
        "companions": companion_summaries,
        "companion_operator": [operator_context[item["id"]] for item in companion_summaries if item["id"] in operator_context],
    }
    report["artifacts"] = persist_map_report(report, args.output_dir or str(workspace), args.focus)

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(_format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
