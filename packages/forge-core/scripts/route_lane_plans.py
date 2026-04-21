from __future__ import annotations


REVIEW_PIPELINES = {"implementer-quality", "deploy-gate"}


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

    if intent == "BUILD":
        if complexity in {"medium", "large"}:
            pipeline_key = "implementer-quality"
        else:
            pipeline_key = rules.get("default", "single-lane")
    elif intent in {"DEBUG", "OPTIMIZE"}:
        if complexity in {"medium", "large"}:
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
    if lane == "quality-reviewer":
        return "default"
    if lane == "navigator":
        return "explorer"
    return "default"


def lane_review_kind(lane: str) -> str | None:
    mapping = {
        "quality-reviewer": "quality-pass",
        "deploy-reviewer": "release-review",
    }
    return mapping.get(lane)


def build_delegation_controller_steps(strategy_key: str, execution_pipeline_key: str | None) -> list[str]:
    if strategy_key == "wave-execution":
        return [
            "Build or refresh the wave plan before spawning workers.",
            "Spawn one worker packet per ready slice in the current wave.",
            "After each worker result, advance the persisted wave state before spawning the next wave.",
            "Run shared verification when a wave completes before unlocking downstream packets.",
        ]
    if strategy_key == "parallel-split":
        return [
            "Lock independent slice boundaries before spawning.",
            "Spawn one worker packet per slice with explicit write ownership.",
            "Do non-overlapping controller work before waiting on workers.",
            "Integrate results and rerun shared verification after the merge.",
        ]
    if strategy_key == "independent-reviewer":
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
