from __future__ import annotations


REVIEW_PIPELINES = {"implementer-quality", "implementer-spec-quality", "deploy-gate"}


def choose_execution_pipeline(
    intent: str,
    complexity: str,
    quality_profile_key: str,
    forge_skills: list[str],
    registry: dict,
) -> tuple[str | None, dict | None]:
    if intent not in {"BUILD", "DEBUG", "OPTIMIZE", "DEPLOY"}:
        return None, None

    pipelines = registry.get("execution_pipelines", {})
    rules = registry.get("execution_pipeline_rules", {})
    high_risk_profiles = set(rules.get("high_risk_quality_profiles", []))
    spec_review_required = "spec-review" in forge_skills

    if intent == "BUILD":
        if spec_review_required:
            pipeline_key = "implementer-spec-quality"
        elif complexity in {"medium", "large"} or quality_profile_key in high_risk_profiles:
            pipeline_key = "implementer-quality"
        else:
            pipeline_key = rules.get("default", "single-lane")
    elif intent in {"DEBUG", "OPTIMIZE"}:
        if complexity in {"medium", "large"} or quality_profile_key in high_risk_profiles:
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


def lane_runtime_role(lane: str) -> str:
    if lane == "implementer":
        return "worker"
    if lane in {"spec-reviewer", "quality-reviewer"}:
        return "default"
    if lane == "navigator":
        return "explorer"
    return "default"


def lane_review_kind(lane: str) -> str | None:
    mapping = {
        "spec-reviewer": "spec-compliance",
        "quality-reviewer": "quality-pass",
        "deploy-reviewer": "release-review",
    }
    return mapping.get(lane)


def build_delegation_controller_steps(strategy_key: str, execution_pipeline_key: str | None) -> list[str]:
    if strategy_key == "parallel-split":
        return [
            "Lock independent slice boundaries before spawning.",
            "Spawn one worker packet per slice with explicit write ownership.",
            "Do non-overlapping controller work before waiting on workers.",
            "Integrate results and rerun shared verification after the merge.",
        ]
    if strategy_key == "independent-reviewer":
        if execution_pipeline_key == "implementer-spec-quality":
            return [
                "Let the implementer finish its slice and verification first.",
                "Dispatch the spec-reviewer as a spec-compliance lane with packet, changed files, and evidence.",
                "Only dispatch the quality-reviewer after spec-compliance returns clean.",
                "If spec-compliance finds drift, hand ownership back to the implementer before quality review.",
            ]
        return [
            "Let the implementer finish its slice and verification first.",
            "Dispatch reviewer packets with spec, changed files, and evidence.",
            "Collect findings before assigning any fix work.",
            "Hand ownership back to an implementer packet if follow-up changes are required.",
        ]
    return [
        "Keep distinct lanes as controller-managed sequential passes.",
        "Preserve the same packet fields and review boundaries even without spawning.",
        "Rerun shared verification after the final lane completes.",
    ]
