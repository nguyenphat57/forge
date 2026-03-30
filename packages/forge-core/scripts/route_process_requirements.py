from __future__ import annotations


EDITING_INTENTS = {"BUILD", "DEBUG", "OPTIMIZE"}
VERIFY_CHANGE_INTENTS = {"BUILD"}


def requires_change_artifacts(intent: str, complexity: str) -> bool:
    return intent in EDITING_INTENTS and complexity in {"medium", "large"}


def verify_change_required(intent: str, complexity: str) -> bool:
    return intent in VERIFY_CHANGE_INTENTS and complexity in {"medium", "large"}


def review_artifact_required(intent: str, complexity: str, execution_pipeline_key: str | None) -> bool:
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
