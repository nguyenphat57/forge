from __future__ import annotations

from route_host_capabilities import resolve_host_capability_tier
from route_lane_plans import REVIEW_PIPELINES, build_delegation_controller_steps, lane_review_kind, lane_runtime_role


DELEGATION_PACKET_FIELDS = [
    "packet_id",
    "packet_mode",
    "parent_packet",
    "source_of_truth",
    "goal",
    "current_slice_or_review_question",
    "exact_files_or_paths_in_scope",
    "owned_files_or_write_scope",
    "depends_on_packets",
    "unblocks_packets",
    "merge_target",
    "merge_strategy",
    "overlap_risk_status",
    "write_scope_conflicts",
    "review_readiness",
    "merge_readiness",
    "completion_gate",
    "baseline_or_clean_start_proof",
    "red_proof",
    "out_of_scope_for_this_slice",
    "reopen_conditions",
    "files_to_avoid",
    "allowed_reads_or_supporting_artifacts",
    "proof_before_progress",
    "verification_to_rerun",
    "browser_qa_classification",
    "browser_qa_scope",
    "browser_qa_status",
    "blockers",
    "residual_risk",
    "next_steps",
]
DELEGATION_RETURN_FIELDS = ["status", "changed_files", "verification", "residual_risk"]
DELEGATION_STATUS_VALUES = ["DONE", "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED"]
REVIEWER_RETURN_FIELDS = [
    "findings_by_severity",
    "clean_rationale_when_no_findings",
    "residual_risk_or_testing_gaps",
]


def build_delegation_packet_template() -> dict:
    return {
        "required_fields": list(DELEGATION_PACKET_FIELDS),
        "return_fields": list(DELEGATION_RETURN_FIELDS),
        "status_values": list(DELEGATION_STATUS_VALUES),
        "reviewer_return_fields": list(REVIEWER_RETURN_FIELDS),
        "fork_context_default": False,
    }


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return []


def _normalized_scopes(packet: dict) -> list[str]:
    scopes = _string_items(packet.get("owned_files_or_write_scope") or packet.get("owned_scope"))
    return [scope.replace("\\", "/").strip().lower() for scope in scopes]


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _scopes_overlap(left: str, right: str) -> bool:
    left_scope = left.rstrip("/")
    right_scope = right.rstrip("/")
    return (
        left_scope == right_scope
        or left_scope.startswith(f"{right_scope}/")
        or right_scope.startswith(f"{left_scope}/")
    )


def analyze_parallel_packet_candidates(packet_candidates: object) -> dict:
    if packet_candidates is None:
        return {"present": False, "parallel_ready": False, "dispatch_reasons": [], "fallback_reasons": []}
    if not isinstance(packet_candidates, list):
        return {
            "present": True,
            "parallel_ready": False,
            "dispatch_reasons": [],
            "fallback_reasons": ["packet-candidates-not-a-list"],
        }

    fallback_reasons: list[str] = []
    seen_scopes: list[str] = []
    ready_packet_count = 0
    if len(packet_candidates) < 2:
        fallback_reasons.append("packet-candidates-below-parallel-threshold")

    for packet in packet_candidates:
        if not isinstance(packet, dict):
            _append_unique(fallback_reasons, "packet-candidate-not-an-object")
            continue
        scopes = _normalized_scopes(packet)
        if not scopes:
            _append_unique(fallback_reasons, "packet-missing-owned-scope")
        if not _string_items(packet.get("proof_before_progress")):
            _append_unique(fallback_reasons, "packet-missing-proof")
        if not _string_items(packet.get("verification_to_rerun")):
            _append_unique(fallback_reasons, "packet-missing-verification")
        if _string_items(packet.get("depends_on_packets")):
            _append_unique(fallback_reasons, "packet-dependencies-block-parallel-dispatch")
        if _string_items(packet.get("blockers")):
            _append_unique(fallback_reasons, "packet-has-blockers")
        if _string_items(packet.get("write_scope_conflicts")):
            _append_unique(fallback_reasons, "packet-write-scope-conflict")
        if packet.get("overlap_risk_status") not in (None, "", "none"):
            _append_unique(fallback_reasons, "packet-overlap-risk-not-clear")
        for scope in scopes:
            if any(_scopes_overlap(scope, seen_scope) for seen_scope in seen_scopes):
                _append_unique(fallback_reasons, "packet-write-scope-overlap")
            seen_scopes.append(scope)
        if scopes:
            ready_packet_count += 1

    if fallback_reasons or ready_packet_count < 2:
        if ready_packet_count < 2:
            _append_unique(fallback_reasons, "packet-candidates-below-parallel-threshold")
        return {"present": True, "parallel_ready": False, "dispatch_reasons": [], "fallback_reasons": fallback_reasons}
    return {
        "present": True,
        "parallel_ready": True,
        "dispatch_reasons": ["packet-candidates-parallel-ready"],
        "fallback_reasons": [],
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


def choose_delegation_plan(
    intent: str,
    execution_mode: str | None,
    execution_pipeline_key: str | None,
    registry: dict,
    packet_candidates: object = None,
) -> tuple[str | None, dict | None, list[str]]:
    if intent not in {"BUILD", "DEBUG", "OPTIMIZE", "DEPLOY"}:
        return None, None, []

    host_capabilities = registry.get("host_capabilities", {})
    tier_key, tier = resolve_host_capability_tier(host_capabilities)
    effective_tier_key = tier_key
    tiers = host_capabilities.get("tiers")
    if not isinstance(tiers, dict):
        tiers = {}
    effective_tier = tiers.get(effective_tier_key, {})
    supports_subagents = bool(
        effective_tier.get("supports_subagents", tier.get("supports_subagents", host_capabilities.get("supports_subagents", False)))
    )
    supports_parallel_subagents = bool(
        effective_tier.get(
            "supports_parallel_subagents",
            tier.get("supports_parallel_subagents", host_capabilities.get("supports_parallel_subagents", supports_subagents)),
        )
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
    tier_dispatch_reasons = [
        item for item in effective_tier.get("dispatch_reasons", tier.get("dispatch_reasons", []))
        if isinstance(item, str) and item.strip()
    ]
    tier_fallback_reasons = [
        item for item in effective_tier.get("fallback_reasons", tier.get("fallback_reasons", []))
        if isinstance(item, str) and item.strip()
    ]

    packet_analysis = analyze_parallel_packet_candidates(packet_candidates)
    uses_parallel_mode = execution_mode == "parallel-safe" or bool(packet_analysis["parallel_ready"])
    uses_review_lane = execution_pipeline_key in REVIEW_PIPELINES and not packet_analysis["present"]
    packet_fallback_required = bool(packet_analysis["present"] and not packet_analysis["parallel_ready"])

    if not uses_parallel_mode and not uses_review_lane and not packet_fallback_required:
        return None, None, []

    if packet_fallback_required:
        key = "sequential-lanes"
        label = "Sequential lanes"
        summary = "Packet candidates are not safe for automatic subagent dispatch."
    elif uses_parallel_mode and supports_parallel_subagents:
        key = "parallel-split"
        label = "Parallel split"
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

    if key != "sequential-lanes" and not (isinstance(activation_skill, str) and activation_skill):
        key = "sequential-lanes"
        label = "Sequential lanes"
        summary = "This task could delegate in theory, but the current bundle does not expose a dispatch skill."
        tier_fallback_reasons = [*tier_fallback_reasons, "host-tier-lacks-dispatch-skill"]

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
        "effective_delegation_mode": effective_tier_key,
        "host_capability_tier": tier_key,
        "activation_skill": activation_skill if host_skills else None,
        "controller_contract": controller_contract,
        "dispatch_reasons": [*tier_dispatch_reasons, *packet_analysis["dispatch_reasons"]],
        "fallback_reasons": [*tier_fallback_reasons, *packet_analysis["fallback_reasons"]],
        "controller_steps": build_delegation_controller_steps(key, execution_pipeline_key),
        "packet_template": build_delegation_packet_template(),
        "packet_blueprints": build_delegation_packet_blueprints(key, execution_pipeline_key, registry),
    }
    return key, plan, host_skills
