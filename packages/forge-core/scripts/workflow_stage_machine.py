from __future__ import annotations

from pathlib import Path

from workflow_stage_fields import transition_entry
from workflow_state_io import string_list


EXECUTION_CHOICE_PENDING_DECISIONS = {"execution-choice-required", "execution-choice-pending"}


def stage_entry(kind: str, report: dict | None, source_path: Path | None = None) -> tuple[str, dict] | None:
    transition = transition_entry(kind, report, str(source_path) if source_path else None)
    if not isinstance(transition, dict):
        return None
    snapshot = {
        "status": transition["stage_status"],
        "recorded_at": transition["recorded_at"],
        "updated_at": transition["recorded_at"],
        "transition_id": transition["transition_id"],
        "source_path": transition["source_path"],
        "event_ref": transition["event_ref"],
    }
    for key in (
        "summary",
        "activation_reason",
        "skip_reason",
        "decision",
        "disposition",
        "target",
        "release_artifact_id",
        "rollback_path",
        "next_stage_override",
        "profile",
        "intent",
        "review_iteration",
        "max_review_iterations",
    ):
        value = transition.get(key)
        if value is not None:
            snapshot[key] = value
    for key in ("artifact_refs", "evidence_refs", "notes", "next_actions", "post_deploy_verification"):
        values = transition.get(key)
        if isinstance(values, list) and values:
            snapshot[key] = values
    return transition["stage_name"], snapshot


def seed_required_stages(stages: dict, required_stage_chain: list[str], recorded_at: str) -> dict[str, dict]:
    seeded = dict(stages) if isinstance(stages, dict) else {}
    for stage_name in required_stage_chain:
        existing = seeded.get(stage_name)
        if isinstance(existing, dict):
            continue
        seeded[stage_name] = {
            "status": "required",
            "recorded_at": recorded_at,
            "updated_at": recorded_at,
            "transition_id": None,
            "source_path": None,
            "event_ref": None,
        }
    return seeded


def validate_transition(state: dict, transition: dict) -> None:
    expected_previous_stage = transition.get("expected_previous_stage")
    current_stage = state.get("current_stage")
    if isinstance(expected_previous_stage, str) and expected_previous_stage.strip():
        expected_previous_stage = expected_previous_stage.strip()
        if current_stage != expected_previous_stage:
            raise ValueError(
                "stale transition: expected_previous_stage='{0}' but current_stage='{1}'".format(
                    expected_previous_stage,
                    current_stage,
                )
            )

    transition_id = transition.get("transition_id")
    last_transition = state.get("last_transition")
    if (
        isinstance(transition_id, str)
        and transition_id.strip()
        and isinstance(last_transition, dict)
        and last_transition.get("transition_id") == transition_id
    ):
        raise ValueError(f"duplicate transition_id '{transition_id}' already recorded.")

    chain = string_list(transition.get("required_stage_chain")) or string_list(state.get("required_stage_chain"))
    stage_name = transition.get("stage_name")
    if chain and isinstance(stage_name, str) and stage_name not in chain and transition.get("kind") not in {"execution-progress", "ui-progress"}:
        raise ValueError(f"stage_name '{stage_name}' is not part of required_stage_chain.")
    override = transition.get("next_stage_override")
    if isinstance(override, str) and override.strip() and chain and override not in chain:
        raise ValueError(f"next_stage_override '{override}' is not part of required_stage_chain.")


def next_stage_after(stage_name: str, required_stage_chain: list[str], stages: dict) -> str | None:
    if stage_name not in required_stage_chain:
        return None
    for candidate in required_stage_chain[required_stage_chain.index(stage_name) + 1 :]:
        payload = stages.get(candidate)
        if isinstance(payload, dict) and payload.get("status") == "skipped":
            continue
        return candidate
    return None


def current_stage_after_transition(
    previous_stage: str | None,
    required_stage_chain: list[str],
    stages: dict,
    transition: dict | None,
) -> str | None:
    if not isinstance(transition, dict):
        return previous_stage
    override = transition.get("next_stage_override")
    if isinstance(override, str) and override.strip():
        return override.strip()
    stage_name = transition.get("stage_name")
    stage_status = transition.get("stage_status")
    if not isinstance(stage_name, str) or not stage_name.strip():
        return previous_stage
    if stage_status in {"completed", "skipped"}:
        if (
            stage_name == "plan"
            and stage_status == "completed"
            and transition.get("decision") in EXECUTION_CHOICE_PENDING_DECISIONS
        ):
            return stage_name
        return next_stage_after(stage_name, required_stage_chain, stages) or stage_name
    return stage_name
