from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from common import (
    configure_stdio,
    reserved_skill_names,
    default_artifact_dir,
    extract_skill_names,
    read_text,
    slugify,
    timestamp_slug,
)


def router_candidate_rank(path: Path) -> tuple[int, int, str]:
    name = path.name.casefold()
    if "skill-map" in name:
        base = 0
    elif "router" in name:
        base = 1
    elif "routing" in name and "smoke" not in name:
        base = 2
    elif "map" in name and "smoke" not in name:
        base = 3
    else:
        base = 9

    penalty = 0
    if any(token in name for token in ("smoke", "test", "checklist", "guidance")):
        penalty += 10
    return (base + penalty, len(path.parts), name)


def detect_router_map(workspace: Path, agents_path: Path) -> Path | None:
    content = read_text(agents_path)
    candidates = re.findall(r"(?:\./)?\.agent/[^\s`\"')]+\.md", content)
    resolved: list[Path] = []
    for candidate in candidates:
        normalized_candidate = candidate.removeprefix("./")
        path = (workspace / normalized_candidate).resolve()
        if path.exists():
            resolved.append(path)
    if resolved:
        return sorted(resolved, key=router_candidate_rank)[0]

    agent_dir = workspace / ".agent"
    for pattern in ("*skill-map*.md", "*router*.md", "*routing*.md", "*map*.md"):
        matches = sorted(agent_dir.rglob(pattern), key=router_candidate_rank)
        if matches:
            return matches[0]

    fallback_candidates = sorted(agent_dir.rglob("*.md"), key=router_candidate_rank)
    return fallback_candidates[0] if len(fallback_candidates) == 1 else None


def local_skill_dirs(workspace: Path) -> dict[str, Path]:
    skills_dir = workspace / ".agent" / "skills"
    if not skills_dir.exists():
        return {}

    found: dict[str, Path] = {}
    for directory in skills_dir.iterdir():
        skill_md = directory / "SKILL.md"
        if directory.is_dir() and skill_md.exists():
            found[directory.name] = skill_md
    return found


def section_text(document: str, heading: str, next_heading: str | None = None) -> str:
    start = document.find(heading)
    if start == -1:
        return ""
    start += len(heading)
    if next_heading is None:
        return document[start:]
    end = document.find(next_heading, start)
    if end == -1:
        return document[start:]
    return document[start:end]


def record(findings: list[dict], level: str, code: str, message: str) -> None:
    findings.append({"level": level, "code": code, "message": message})


def check_workspace(args: argparse.Namespace) -> dict:
    workspace = args.workspace.resolve()
    agents_path = args.agents.resolve() if args.agents else workspace / "AGENTS.md"
    router_map = args.router_map.resolve() if args.router_map else detect_router_map(workspace, agents_path)
    routing_smoke = workspace / ".agent" / "routing-smoke-tests.md"
    guidance_doc = workspace / ".agent" / "local-skill-guidance.md"
    findings: list[dict] = []

    if not agents_path.exists():
        record(findings, "fail", "missing_agents", f"AGENTS.md not found at {agents_path}")
        return build_report(workspace, agents_path, router_map, findings, {})

    agents_content = read_text(agents_path)
    if router_map is None or not router_map.exists():
        record(findings, "fail", "missing_router_map", "Workspace router map could not be resolved from AGENTS.md")
        return build_report(workspace, agents_path, router_map, findings, {})

    router_content = read_text(router_map)
    skills = local_skill_dirs(workspace)
    map_skill_names = set(extract_skill_names(router_content))
    local_inventory_section = section_text(router_content, "## Local Skill Inventory", "## Routing Map")
    local_inventory_names = set(extract_skill_names(local_inventory_section))
    scope_policy_section = section_text(router_content, "## Scope Policy", "## Local Skill Inventory")
    if not scope_policy_section:
        scope_policy_section = section_text(router_content, "## Scope Policy", "## Routing Map")
    global_scope_names = set(extract_skill_names(scope_policy_section))
    excluded_skill_names = reserved_skill_names() | global_scope_names

    record(findings, "pass", "agents_present", f"Using AGENTS.md: {agents_path}")
    record(findings, "pass", "router_present", f"Using router map: {router_map}")

    direct_skill_path_mentions = re.findall(r"\.agent/skills/[A-Za-z0-9._-]+/SKILL\.md", agents_content)
    if direct_skill_path_mentions:
        record(findings, "warn", "thick_agents", "AGENTS.md still mentions local skill paths directly; keep inventory in the router map.")
    else:
        record(findings, "pass", "thin_agents", "AGENTS.md stays thin and delegates routing detail to the router map.")

    if router_map.name not in agents_content and str(router_map.relative_to(workspace)).replace("\\", "/") not in agents_content:
        record(findings, "warn", "router_link_missing", "AGENTS.md does not explicitly point to the resolved router map.")
    else:
        record(findings, "pass", "router_linked", "AGENTS.md points to the router source-of-truth.")

    if not skills:
        record(findings, "warn", "no_local_skills", "No local skills detected under .agent/skills.")

    for skill_name, skill_path in sorted(skills.items()):
        skill_content = read_text(skill_path)
        if skill_name not in map_skill_names:
            record(findings, "warn", "skill_missing_from_map", f"Local skill `{skill_name}` exists but is not listed in the router map.")
        if "When Not To Use" not in skill_content:
            record(findings, "warn", "missing_when_not_to_use", f"Local skill `{skill_name}` is missing a `When Not To Use` section.")

    unknown_map_skills = sorted(
        name
        for name in map_skill_names
        if name not in excluded_skill_names and name not in skills
    )
    for skill_name in unknown_map_skills:
        severity = "warn" if skill_name in local_inventory_names else "pass"
        message = (
            f"Router map references `{skill_name}` but no local skill folder exists for it."
            if severity == "warn"
            else f"Router map references global or external skill `{skill_name}` outside local inventory."
        )
        record(findings, severity, "map_points_outside_local", message)

    if routing_smoke.exists():
        record(findings, "pass", "routing_smoke_present", f"Routing smoke tests found: {routing_smoke}")
    else:
        record(findings, "warn", "routing_smoke_missing", "Missing .agent/routing-smoke-tests.md")

    if guidance_doc.exists():
        record(findings, "pass", "guidance_doc_present", f"Local skill guidance found: {guidance_doc}")
    else:
        record(findings, "warn", "guidance_doc_missing", "Missing .agent/local-skill-guidance.md")

    if routing_smoke.exists():
        smoke_content = read_text(routing_smoke)
        if "AGENTS.md" in smoke_content and router_map.name in smoke_content:
            record(findings, "pass", "smoke_covers_router_docs", "Routing smoke tests mention both AGENTS.md and the router map.")
        else:
            record(findings, "warn", "smoke_missing_router_docs", "Routing smoke tests do not clearly cover router-doc consistency.")

    return build_report(workspace, agents_path, router_map, findings, skills)


def build_report(workspace: Path, agents_path: Path, router_map: Path | None, findings: list[dict], skills: dict[str, Path]) -> dict:
    counts = {
        "pass": sum(1 for item in findings if item["level"] == "pass"),
        "warn": sum(1 for item in findings if item["level"] == "warn"),
        "fail": sum(1 for item in findings if item["level"] == "fail"),
    }
    if counts["fail"] > 0:
        status = "FAIL"
    elif counts["warn"] > 0:
        status = "WARN"
    else:
        status = "PASS"

    return {
        "workspace": str(workspace),
        "agents": str(agents_path),
        "router_map": str(router_map) if router_map else None,
        "local_skill_count": len(skills),
        "status": status,
        "counts": counts,
        "findings": findings,
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Workspace Router Check",
        f"- Workspace: {report['workspace']}",
        f"- AGENTS.md: {report['agents']}",
        f"- Router map: {report['router_map'] or '(missing)'}",
        f"- Local skills detected: {report['local_skill_count']}",
        f"- Status: {report['status']}",
        f"- Counts: pass={report['counts']['pass']} warn={report['counts']['warn']} fail={report['counts']['fail']}",
        "- Findings:",
    ]
    for item in report["findings"]:
        lines.append(f"  - [{item['level'].upper()}] {item['message']}")
    return "\n".join(lines)


def persist_report(report: dict, output_dir: str | None) -> tuple[Path, Path]:
    artifact_dir = default_artifact_dir(output_dir, "router-checks")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{timestamp_slug()}-{slugify(Path(report['workspace']).name)}"
    json_path = artifact_dir / f"{stem}.json"
    md_path = artifact_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(format_text(report), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Check a workspace router for drift against local skills.")
    parser.add_argument("workspace", nargs="?", default=Path.cwd(), type=Path, help="Workspace root")
    parser.add_argument("--agents", type=Path, default=None, help="Optional AGENTS.md override")
    parser.add_argument("--router-map", type=Path, default=None, help="Optional workspace router map override")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--persist", action="store_true", help="Persist the report under .forge-artifacts/router-checks")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    args = parser.parse_args()

    report = check_workspace(args)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))

    if args.persist:
        json_path, md_path = persist_report(report, args.output_dir)
        print(f"\nPersisted router check:")
        print(f"- JSON: {json_path}")
        print(f"- Markdown: {md_path}")

    return 1 if report["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
