from __future__ import annotations


EDITING_INTENTS = {"BUILD", "DEBUG", "OPTIMIZE"}
VERIFY_CHANGE_INTENTS = {"BUILD"}


def _stage_required(required_stages: list[dict] | None, stage_name: str) -> bool:
    if not isinstance(required_stages, list):
        return False
    return any(
        isinstance(item, dict) and item.get("stage") == stage_name and item.get("status") != "skipped"
        for item in required_stages
    )


def requires_change_artifacts(intent: str, complexity: str, required_stages: list[dict] | None = None) -> bool:
    if required_stages is not None:
        return _stage_required(required_stages, "change")
    return intent in EDITING_INTENTS and complexity in {"medium", "large"}


def verify_change_required(intent: str, complexity: str, required_stages: list[dict] | None = None) -> bool:
    if required_stages is not None:
        return _stage_required(required_stages, "verify-change")
    return intent in VERIFY_CHANGE_INTENTS and complexity in {"medium", "large"}


def review_artifact_required(
    intent: str,
    complexity: str,
    execution_pipeline_key: str | None,
    required_stages: list[dict] | None = None,
) -> bool:
    if required_stages is not None:
        return _stage_required(required_stages, "self-review") or _stage_required(required_stages, "review-pack")
    return intent in EDITING_INTENTS and (
        complexity in {"medium", "large"} or execution_pipeline_key in {"implementer-quality", "implementer-spec-quality"}
    )


def recommended_isolation_stance(
    intent: str,
    complexity: str,
    execution_mode: str | None,
    host_supports_subagents: bool,
) -> str | None:
    if intent not in EDITING_INTENTS:
        return None
    if complexity == "small":
        return "same-tree"
    if execution_mode == "parallel-safe" and host_supports_subagents:
        return "subagent-split"
    return "worktree"
