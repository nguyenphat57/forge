from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from common import (
    configure_stdio,
    current_bundle_skill_name,
    default_artifact_dir,
    detect_runtimes,
    extract_skill_names,
    keyword_in_text,
    load_registry,
    normalize_text,
    read_text,
    reserved_skill_names,
    score_keywords,
    skill_aliases,
    slugify,
    timestamp_slug,
)


EDITING_INTENTS = {"BUILD", "DEBUG", "OPTIMIZE"}
REVIEW_PIPELINES = {"implementer-quality", "implementer-spec-quality", "deploy-gate"}


def uses_prompt_only_scope(intent: str, complexity: str, registry: dict, intent_key: str, small_key: str) -> bool:
    policy = registry.get("minimal_routing_policy", {})
    if intent in policy.get(intent_key, []):
        return True
    return complexity == "small" and policy.get("prompt_only_for_small", {}).get(small_key, False)


def keyword_position(keyword: str, text: str) -> int | None:
    if not keyword:
        return None
    if any(char in keyword for char in ("/", ".", "_")):
        position = text.find(keyword)
        return position if position >= 0 else None
    pattern = r"(?<!\w){0}(?!\w)".format(re.escape(keyword))
    match = re.search(pattern, text)
    return match.start() if match else None


def keyword_match_metadata(text: str, keywords: list[str]) -> tuple[int, int | None, int]:
    seen: set[str] = set()
    score = 0
    first_position: int | None = None
    longest_match = 0

    for keyword in keywords:
        normalized = normalize_text(keyword)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        position = keyword_position(normalized, text)
        if position is None:
            continue
        score += 1
        if first_position is None or position < first_position:
            first_position = position
        longest_match = max(longest_match, len(normalized))

    return score, first_position, longest_match


def detect_intent(prompt_text: str, registry: dict) -> tuple[str, dict]:
    normalized = normalize_text(prompt_text)
    best_intent = "BUILD"
    best_score = -1
    best_tiebreak = (-1, -1, -1)

    for intent, config in registry["intents"].items():
        keyword_score, first_position, longest_match = keyword_match_metadata(
            normalized,
            config.get("keywords", []),
        )
        shortcut_match = any(
            normalized.startswith(normalize_text(shortcut))
            for shortcut in config.get("shortcuts", [])
        )
        score = keyword_score + (10 if shortcut_match else 0)
        tiebreak = (
            1 if shortcut_match else 0,
            -(first_position if first_position is not None else len(normalized) + 1),
            longest_match,
        )
        if score > best_score or (score == best_score and score > 0 and tiebreak > best_tiebreak):
            best_intent = intent
            best_score = score
            best_tiebreak = tiebreak

    return best_intent, registry["intents"][best_intent]


def detect_complexity(prompt_text: str, changed_files: int | None, registry: dict) -> str:
    normalized = normalize_text(prompt_text)
    quick_requested = normalized.startswith("/quick")
    high_risk_keywords: list[str] = []
    high_risk_keywords.extend(registry["complexity"]["prompt_hints"].get("large", []))
    high_risk_keywords.extend(registry.get("spec_review_gate", {}).get("prompt_keywords", []))
    for profile_name in ("release-critical", "migration-critical", "external-interface"):
        high_risk_keywords.extend(
            registry.get("quality_profiles", {}).get(profile_name, {}).get("prompt_keywords", [])
        )
    quick_high_risk = score_keywords(normalized, high_risk_keywords) > 0

    if quick_requested and not quick_high_risk:
            return "small"

    if changed_files is not None:
        thresholds = registry["complexity"]["thresholds"]
        if changed_files <= thresholds["small_max_changed_files"]:
            return "small"
        if changed_files <= thresholds["medium_max_changed_files"]:
            return "medium"
        return "large"

    hints = registry["complexity"]["prompt_hints"]
    scores = {
        "small": score_keywords(normalized, hints.get("small", [])),
        "medium": score_keywords(normalized, hints.get("medium", [])),
        "large": score_keywords(normalized, hints.get("large", [])),
    }

    if quick_requested and quick_high_risk and scores["large"] == 0:
        return "medium"

    if scores["large"] > 0:
        return "large"
    if scores["small"] > 0 and scores["medium"] == 0:
        return "small"
    if scores["medium"] > 0:
        return "medium"
    return registry["complexity"]["default"]


def detect_domain_skills(prompt_text: str, repo_signals: list[str], intent: str, complexity: str, registry: dict) -> list[str]:
    normalized_prompt = normalize_text(prompt_text)
    normalized_signals = normalize_text(" ".join(repo_signals))
    prompt_only = uses_prompt_only_scope(
        intent,
        complexity,
        registry,
        "prompt_only_domain_intents",
        "domains",
    )
    domains: list[str] = []
    for domain_name, config in registry.get("domains", {}).items():
        prompt_score = score_keywords(normalized_prompt, config.get("prompt_keywords", []))
        signal_score = score_keywords(normalized_signals, config.get("repo_signals", []))
        weak_signal_score = score_keywords(normalized_signals, config.get("weak_repo_signals", []))
        strong_signal_score = max(signal_score - weak_signal_score, 0)
        if prompt_score > 0 or (not prompt_only and strong_signal_score > 0):
            domains.append(domain_name)
    return domains


def should_insert_brainstorm(prompt_text: str, intent: str, complexity: str, registry: dict) -> bool:
    gate = registry.get("brainstorm_gate", {})
    if intent not in gate.get("eligible_intents", []):
        return False
    if complexity not in gate.get("eligible_complexities", []):
        return False
    normalized = normalize_text(prompt_text)
    return score_keywords(normalized, gate.get("prompt_keywords", [])) > 0


def should_insert_spec_review(prompt_text: str, repo_signals: list[str], intent: str, complexity: str, registry: dict) -> bool:
    gate = registry.get("spec_review_gate", {})
    if intent not in gate.get("eligible_intents", []):
        return False
    if complexity not in gate.get("eligible_complexities", []):
        return False
    if complexity == "large" and gate.get("always_large", False):
        return True

    haystack = normalize_text(" ".join([prompt_text, *repo_signals]))
    keyword_score = score_keywords(haystack, gate.get("prompt_keywords", []))
    signal_score = score_keywords(haystack, gate.get("repo_signals", []))
    return (keyword_score + signal_score) > 0


def infer_change_type(prompt_text: str, registry: dict) -> str:
    normalized = normalize_text(prompt_text)
    non_behavioral = score_keywords(normalized, registry["change_type_hints"]["non_behavioral_keywords"])
    behavioral = score_keywords(normalized, registry["change_type_hints"]["behavioral_keywords"])
    if non_behavioral > behavioral:
        return "non_behavioral"
    return "behavioral"


def infer_harness(has_harness: str, prompt_text: str, repo_signals: list[str]) -> bool:
    if has_harness == "yes":
        return True
    if has_harness == "no":
        return False

    haystack = normalize_text(" ".join([prompt_text, *repo_signals]))
    harness_markers = [
        "test",
        "spec",
        "vitest",
        "jest",
        "playwright",
        "cypress",
        "pytest",
        "junit",
        "__tests__",
        "tests/",
        ".test.",
        ".spec.",
    ]
    return any(marker in haystack for marker in harness_markers)


def choose_verification_profile(
    intent: str,
    prompt_text: str,
    repo_signals: list[str],
    registry: dict,
    has_harness: str,
) -> tuple[str | None, dict | None]:
    if intent not in EDITING_INTENTS:
        return None, None

    change_type = infer_change_type(prompt_text, registry)
    if change_type == "non_behavioral":
        key = "non_behavioral"
    elif infer_harness(has_harness, prompt_text, repo_signals):
        key = "behavioral_with_harness"
    else:
        key = "behavioral_reproduction_first"
    return key, registry["verification_profiles"][key]


def choose_execution_mode(prompt_text: str, intent: str, complexity: str, registry: dict) -> str | None:
    if intent not in {"BUILD", "DEBUG", "OPTIMIZE"}:
        return None

    if complexity == "small":
        return "single-track"

    normalized = normalize_text(prompt_text)
    modes = registry.get("execution_modes", {})
    best_mode = "single-track"
    best_score = -1

    for mode_name, config in modes.items():
        if complexity not in config.get("recommended_for", []):
            continue
        score = score_keywords(normalized, config.get("prompt_keywords", []))
        if complexity == "large" and mode_name == "checkpoint-batch":
            score += 1
        if score > best_score:
            best_mode = mode_name
            best_score = score

    return best_mode


def choose_execution_pipeline(intent: str, complexity: str, quality_profile_key: str, forge_skills: list[str], registry: dict) -> tuple[str | None, dict | None]:
    if intent not in {"BUILD", "DEBUG", "OPTIMIZE", "DEPLOY"}:
        return None, None

    pipelines = registry.get("execution_pipelines", {})
    rules = registry.get("execution_pipeline_rules", {})
    high_risk_profiles = set(rules.get("high_risk_quality_profiles", []))
    spec_review_required = "spec-review" in forge_skills

    if intent == "BUILD":
        if spec_review_required:
            pipeline_key = "implementer-spec-quality"
        elif complexity == "large" or quality_profile_key in high_risk_profiles:
            pipeline_key = "implementer-quality"
        else:
            pipeline_key = rules.get("default", "single-lane")
    elif intent in {"DEBUG", "OPTIMIZE"}:
        if complexity == "large" or quality_profile_key in high_risk_profiles:
            pipeline_key = "implementer-quality"
        else:
            pipeline_key = rules.get("default", "single-lane")
    else:
        pipeline_key = "deploy-gate"

    return pipeline_key, pipelines.get(pipeline_key)


def choose_lane_model_assignments(
    forge_skills: list[str],
    execution_pipeline_key: str | None,
    complexity: str,
    quality_profile_key: str,
    registry: dict,
) -> dict[str, str]:
    policy = registry.get("lane_model_policy", {})
    assignments: dict[str, str] = dict(policy.get("default", {}))
    assignments.update(policy.get("by_complexity", {}).get(complexity, {}))
    assignments.update(policy.get("quality_profile_upgrades", {}).get(quality_profile_key, {}))

    active_lanes: list[str] = []
    if any(skill in forge_skills for skill in ("brainstorm", "plan", "architect", "visualize")):
        active_lanes.append("navigator")

    if execution_pipeline_key:
        for lane in registry.get("execution_pipelines", {}).get(execution_pipeline_key, {}).get("lanes", []):
            if lane not in active_lanes:
                active_lanes.append(lane)

    return {lane: assignments.get(lane, "standard") for lane in active_lanes}


def choose_delegation_plan(
    intent: str,
    execution_mode: str | None,
    execution_pipeline_key: str | None,
    registry: dict,
) -> tuple[str | None, dict | None, list[str]]:
    if intent not in {"BUILD", "DEBUG", "OPTIMIZE", "DEPLOY"}:
        return None, None, []

    host_capabilities = registry.get("host_capabilities", {})
    supports_subagents = bool(host_capabilities.get("supports_subagents", False))
    supports_parallel_subagents = bool(
        host_capabilities.get("supports_parallel_subagents", supports_subagents)
    )
    activation_skill = host_capabilities.get("subagent_dispatch_skill")
    controller_contract = host_capabilities.get(
        "delegation_contract",
        [
            "Fresh packet per delegated slice.",
            "Explicit ownership and write scope.",
            "Return changed files, verification, and residual risk.",
        ],
    )

    uses_parallel_mode = execution_mode == "parallel-safe"
    uses_review_lane = execution_pipeline_key in REVIEW_PIPELINES

    if not uses_parallel_mode and not uses_review_lane:
        return None, None, []

    if uses_parallel_mode and supports_parallel_subagents:
        key = "parallel-split"
        label = "Parallel subagent split"
        summary = "Independent slices can run in parallel under isolated ownership."
    elif supports_subagents and uses_review_lane:
        key = "independent-reviewer"
        label = "Independent reviewer subagent"
        summary = "Reviewer lanes should run as separate subagents instead of collapsing into the implementer pass."
    else:
        key = "sequential-lanes"
        label = "Sequential lanes"
        if uses_parallel_mode:
            summary = "This task is parallel-safe, but the current bundle must keep slices as sequential lanes."
        else:
            summary = "This task needs distinct review lanes, but the current bundle must keep them as sequential passes."

    host_skills = [activation_skill] if key != "sequential-lanes" and isinstance(activation_skill, str) and activation_skill else []
    plan = {
        "label": label,
        "summary": summary,
        "activation_skill": activation_skill if host_skills else None,
        "controller_contract": controller_contract,
    }
    return key, plan, host_skills


def choose_quality_profile(prompt_text: str, repo_signals: list[str], intent: str, complexity: str, registry: dict) -> tuple[str, dict]:
    normalized_prompt = normalize_text(prompt_text)
    normalized_signals = normalize_text(" ".join(repo_signals))
    profiles = registry.get("quality_profiles", {})
    priority = registry.get("quality_profile_priority", list(profiles.keys()))
    intent_preferences = registry.get("quality_profile_intent_preference", {})
    priority_rank = {name: index for index, name in enumerate(priority)}
    prompt_only = uses_prompt_only_scope(
        intent,
        complexity,
        registry,
        "prompt_only_quality_profile_intents",
        "quality_profiles",
    )

    best_name = "standard"
    best_score = 0
    best_rank = priority_rank.get("standard", len(priority_rank))

    for profile_name, config in profiles.items():
        if profile_name == "standard":
            continue

        prompt_score = score_keywords(normalized_prompt, config.get("prompt_keywords", []))
        if prompt_only and prompt_score <= 0:
            continue

        evidence_score = prompt_score
        if not prompt_only or prompt_score > 0:
            evidence_score += score_keywords(normalized_signals, config.get("repo_signals", []))
        if evidence_score <= 0:
            continue

        score = evidence_score * 10
        if intent in config.get("intent_bias", []):
            score += config.get("intent_boost", 1)
        if profile_name in intent_preferences.get(intent, []):
            score += 100

        rank = priority_rank.get(profile_name, len(priority_rank))
        if score > best_score or (score == best_score and rank < best_rank):
            best_name = profile_name
            best_score = score
            best_rank = rank

    return best_name, profiles[best_name]


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


def resolve_workspace_router(router_doc: Path | None) -> Path | None:
    if router_doc is None:
        return None
    if not router_doc.exists():
        return router_doc
    if router_doc.name.casefold() != "agents.md":
        return router_doc

    from check_workspace_router import detect_router_map

    resolved = detect_router_map(router_doc.parent, router_doc)
    return resolved or router_doc


def infer_local_companions(
    prompt_text: str,
    repo_signals: list[str],
    router_doc: Path | None,
    intent: str,
    complexity: str,
    registry: dict,
) -> list[str]:
    if router_doc is None or not router_doc.exists():
        return []

    content = read_text(router_doc)
    scope_policy_section = section_text(content, "## Scope Policy", "## Local Skill Inventory")
    if not scope_policy_section:
        scope_policy_section = section_text(content, "## Scope Policy", "## Routing Map")
    excluded_skill_names = reserved_skill_names() | set(extract_skill_names(scope_policy_section))
    local_inventory = section_text(content, "## Local Skill Inventory", "## Routing Map")
    skill_source = local_inventory or content
    skills = [name for name in extract_skill_names(skill_source) if name not in excluded_skill_names]
    normalized_prompt = normalize_text(prompt_text)
    normalized_signals = normalize_text(" ".join(repo_signals))
    prompt_only = uses_prompt_only_scope(
        intent,
        complexity,
        registry,
        "prompt_only_local_companion_intents",
        "local_companions",
    )
    policy = registry.get("minimal_routing_policy", {})
    allow_runtime_only = intent in policy.get("runtime_signal_local_companion_intents", []) and not prompt_only
    score_floor = policy.get("repo_signal_companion_score_floor", {}).get(complexity, 1)
    max_companions = policy.get("max_local_companions", {}).get(complexity, 3)
    runtime_context: set[str] = set()
    for runtime in detect_runtimes(repo_signals, registry):
        runtime_context.add(normalize_text(runtime))
        runtime_context.update(skill_aliases(runtime))

    scored: list[tuple[int, str]] = []
    for skill_name in skills:
        aliases = skill_aliases(skill_name)
        prompt_score = 0
        signal_score = 0
        for alias in aliases:
            normalized_alias = normalize_text(alias)
            if keyword_in_text(normalized_alias, normalized_prompt):
                prompt_score += 1
            if keyword_in_text(normalized_alias, normalized_signals):
                signal_score += 1
        runtime_score = 2 if aliases & runtime_context else 0
        if prompt_only and prompt_score <= 0:
            continue
        if prompt_score <= 0 and not allow_runtime_only:
            continue
        if prompt_score <= 0 and (signal_score + runtime_score) < score_floor:
            continue
        score = (prompt_score * 10) + signal_score + runtime_score
        if score > 0:
            scored.append((score, skill_name))

    scored.sort(key=lambda item: (-item[0], item[1]))
    ordered: list[str] = []
    for _, skill_name in scored:
        if skill_name not in ordered:
            ordered.append(skill_name)
    return ordered[:max_companions]


def build_report(args: argparse.Namespace) -> dict:
    registry = load_registry()
    host_capabilities = registry.get("host_capabilities", {})
    intent, intent_config = detect_intent(args.prompt, registry)
    complexity = detect_complexity(args.prompt, args.changed_files, registry)
    workspace_router = resolve_workspace_router(args.workspace_router)
    forge_skills = list(intent_config["chains"][complexity])
    if should_insert_brainstorm(args.prompt, intent, complexity, registry) and "brainstorm" not in forge_skills:
        forge_skills.insert(0, "brainstorm")
    if should_insert_spec_review(args.prompt, args.repo_signal, intent, complexity, registry) and "spec-review" not in forge_skills:
        build_index = forge_skills.index("build") if "build" in forge_skills else len(forge_skills)
        forge_skills.insert(build_index, "spec-review")
    domain_skills = detect_domain_skills(args.prompt, args.repo_signal, intent, complexity, registry)
    verification_key, verification = choose_verification_profile(
        intent,
        args.prompt,
        args.repo_signal,
        registry,
        args.has_harness,
    )
    execution_mode = choose_execution_mode(args.prompt, intent, complexity, registry)
    quality_profile_key, quality_profile = choose_quality_profile(args.prompt, args.repo_signal, intent, complexity, registry)
    execution_pipeline_key, execution_pipeline = choose_execution_pipeline(
        intent,
        complexity,
        quality_profile_key,
        forge_skills,
        registry,
    )
    lane_model_assignments = choose_lane_model_assignments(
        forge_skills,
        execution_pipeline_key,
        complexity,
        quality_profile_key,
        registry,
    )
    delegation_strategy, delegation_plan, host_skills = choose_delegation_plan(
        intent,
        execution_mode,
        execution_pipeline_key,
        registry,
    )
    local_companions = infer_local_companions(
        args.prompt,
        args.repo_signal,
        workspace_router,
        intent,
        complexity,
        registry,
    )
    runtimes = detect_runtimes(args.repo_signal, registry)

    return {
        "prompt": args.prompt,
        "repo_signals": args.repo_signal,
        "workspace_router": str(workspace_router) if workspace_router else None,
        "detected": {
            "intent": intent,
            "complexity": complexity,
            "forge_skills": forge_skills,
            "host_skills": host_skills,
            "host_supports_subagents": bool(host_capabilities.get("supports_subagents", False)),
            "domain_skills": domain_skills,
            "local_companions": local_companions,
            "runtimes": runtimes,
            "verification_profile": verification_key,
            "execution_mode": execution_mode,
            "execution_pipeline": execution_pipeline_key,
            "lane_model_assignments": lane_model_assignments,
            "quality_profile": quality_profile_key,
            "delegation_strategy": delegation_strategy,
        },
        "verification": verification,
        "execution_pipeline": execution_pipeline,
        "delegation_plan": delegation_plan,
        "quality_profile": quality_profile,
        "activation_line": "Forge: {intent} | {complexity} | Skills: {skills}".format(
            intent=intent,
            complexity=complexity,
            skills=" + ".join([*forge_skills, *host_skills, *domain_skills, *local_companions]) or current_bundle_skill_name(),
        ),
        "registry_source": "data/orchestrator-registry.json",
    }


def format_text(report: dict) -> str:
    detected = report["detected"]
    lines = [
        "Forge Route Preview",
        f"- Prompt: {report['prompt']}",
        f"- Intent: {detected['intent']}",
        f"- Complexity: {detected['complexity']}",
        f"- Forge skills: {' -> '.join(detected['forge_skills'])}",
        f"- Execution mode: {detected['execution_mode'] or '(n/a)'}",
        f"- Execution pipeline: {report['execution_pipeline']['label'] if report['execution_pipeline'] else '(n/a)'}",
        f"- Delegation strategy: {report['delegation_plan']['label'] if report['delegation_plan'] else '(n/a)'}",
        f"- Quality profile: {report['quality_profile']['label']}",
        f"- Host skills: {', '.join(detected['host_skills']) or '(none)'}",
        f"- Domain skills: {', '.join(detected['domain_skills']) or '(none)'}",
        f"- Local companions: {', '.join(detected['local_companions']) or '(none)'}",
        f"- Runtimes from repo signals: {', '.join(detected['runtimes']) or '(none)'}",
        f"- Verification profile: {report['verification']['label'] if report['verification'] else '(n/a)'}",
        "- Lane model tiers:",
    ]
    if detected["lane_model_assignments"]:
        for lane, tier in detected["lane_model_assignments"].items():
            lines.append(f"  - {lane}: {tier}")
    else:
        lines.append("  - (none)")
    if detected["execution_pipeline"] == "implementer-spec-quality":
        max_revisions = report["execution_pipeline"].get("max_revisions") if report["execution_pipeline"] else None
        if max_revisions is None:
            max_revisions = 3
        lines.append(f"- Spec-review loop cap: {max_revisions}")
    if report["delegation_plan"]:
        lines.append(f"- Delegation summary: {report['delegation_plan']['summary']}")
        lines.append("- Delegation controller contract:")
        for item in report["delegation_plan"]["controller_contract"]:
            lines.append(f"  - {item}")
    lines.extend([
        "- Quality profile evidence:",
    ])
    for item in report["quality_profile"]["required_evidence"]:
        lines.append(f"  - {item}")
    if report["verification"]:
        lines.extend([
            "- Verification-first plan:",
        ])
        for step in report["verification"]["steps"]:
            lines.append(f"  - {step}")
    if report["workspace_router"]:
        lines.append(f"- Workspace router: {report['workspace_router']}")
    lines.append(f"- Registry source: {report['registry_source']}")
    lines.append(f"- Activation line: {report['activation_line']}")
    return "\n".join(lines)


def persist_report(report: dict, output_dir: str | None) -> tuple[Path, Path]:
    artifact_dir = default_artifact_dir(output_dir, "route-previews")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{timestamp_slug()}-{slugify(report['prompt'])[:48]}"
    json_path = artifact_dir / f"{stem}.json"
    md_path = artifact_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(format_text(report), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Preview Forge routing decisions.")
    parser.add_argument("prompt", help="User prompt or task summary")
    parser.add_argument("--repo-signal", action="append", default=[], help="Repo artifact, path, or signal. Repeatable.")
    parser.add_argument("--workspace-router", type=Path, default=None, help="Optional AGENTS.md or workspace skill map")
    parser.add_argument("--changed-files", type=int, default=None, help="Optional changed file count to guide complexity")
    parser.add_argument("--has-harness", choices=["auto", "yes", "no"], default="auto", help="Whether a usable test harness is known")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--persist", action="store_true", help="Persist the preview under .forge-artifacts/route-previews")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    args = parser.parse_args()

    report = build_report(args)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))

    if args.persist:
        json_path, md_path = persist_report(report, args.output_dir)
        print(f"\nPersisted route preview:")
        print(f"- JSON: {json_path}")
        print(f"- Markdown: {md_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
