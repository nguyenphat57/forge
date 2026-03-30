from __future__ import annotations


REVIEW_PIPELINES = {"implementer-quality", "implementer-spec-quality", "deploy-gate"}
DELEGATION_PACKET_FIELDS = [
    "source_of_truth",
    "goal",
    "current_slice_or_review_question",
    "exact_files_or_paths_in_scope",
    "owned_files_or_write_scope",
    "baseline_or_clean_start_proof",
    "out_of_scope_for_this_slice",
    "reopen_conditions",
    "files_to_avoid",
    "allowed_reads_or_supporting_artifacts",
    "proof_before_progress",
    "verification_to_rerun",
]
DELEGATION_RETURN_FIELDS = ["status", "changed_files", "verification", "residual_risk"]
DELEGATION_STATUS_VALUES = ["DONE", "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED"]
REVIEWER_RETURN_FIELDS = [
    "findings_by_severity",
    "clean_rationale_when_no_findings",
    "residual_risk_or_testing_gaps",
]


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


def build_delegation_packet_template() -> dict:
    return {
        "required_fields": list(DELEGATION_PACKET_FIELDS),
        "return_fields": list(DELEGATION_RETURN_FIELDS),
        "status_values": list(DELEGATION_STATUS_VALUES),
        "reviewer_return_fields": list(REVIEWER_RETURN_FIELDS),
        "fork_context_default": False,
    }


def build_delegation_packet_blueprints(
    strategy_key: str,
    execution_pipeline_key: str | None,
    registry: dict,
) -> list[dict]:
    if strategy_key == "parallel-split":
        return [
            {
                "lane": "implementer",
                "packet_type": "slice-worker",
                "runtime_role": "worker",
                "read_only": False,
                "scope_rule": "One packet per independent slice with non-overlapping write ownership.",
                "review_kind": None,
                "sequence_index": 1,
                "depends_on": [],
            }
        ]

    if strategy_key != "independent-reviewer":
        return []

    lanes = registry.get("execution_pipelines", {}).get(execution_pipeline_key, {}).get("lanes", [])
    blueprints: list[dict] = []
    previous_lane: str | None = None
    for index, lane in enumerate(lanes, start=1):
        if lane == "navigator":
            continue
        runtime_role = lane_runtime_role(lane)
        read_only = lane.endswith("reviewer")
        scope_rule = (
            "Read-only findings pass over implementer evidence and changed files."
            if read_only
            else "Owns the implementation slice with explicit file scope."
        )
        blueprints.append(
            {
                "lane": lane,
                "packet_type": "reviewer-pass" if read_only else "implementer-pass",
                "runtime_role": runtime_role,
                "read_only": read_only,
                "scope_rule": scope_rule,
                "review_kind": lane_review_kind(lane),
                "sequence_index": index,
                "depends_on": [previous_lane] if previous_lane else [],
            }
        )
        previous_lane = lane
    return blueprints


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

    host_skills = (
        [activation_skill]
        if key != "sequential-lanes" and isinstance(activation_skill, str) and activation_skill
        else []
    )
    plan = {
        "label": label,
        "summary": summary,
        "dispatch_mode": (
            "parallel-workers"
            if key == "parallel-split"
            else "independent-reviewers"
            if key == "independent-reviewer"
            else "controller-sequential"
        ),
        "activation_skill": activation_skill if host_skills else None,
        "controller_contract": controller_contract,
        "controller_steps": build_delegation_controller_steps(key, execution_pipeline_key),
        "packet_template": build_delegation_packet_template(),
        "packet_blueprints": build_delegation_packet_blueprints(key, execution_pipeline_key, registry),
    }
    return key, plan, host_skills
