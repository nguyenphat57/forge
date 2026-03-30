from __future__ import annotations


REVIEW_SEQUENCES = {
    "single-lane": [
        {"sequence_index": 1, "lane": "implementer", "review_kind": None, "depends_on": []},
    ],
    "implementer-quality": [
        {"sequence_index": 1, "lane": "implementer", "review_kind": None, "depends_on": []},
        {"sequence_index": 2, "lane": "quality-reviewer", "review_kind": "quality-pass", "depends_on": ["implementer"]},
    ],
    "implementer-spec-quality": [
        {"sequence_index": 1, "lane": "implementer", "review_kind": None, "depends_on": []},
        {"sequence_index": 2, "lane": "spec-reviewer", "review_kind": "spec-compliance", "depends_on": ["implementer"]},
        {"sequence_index": 3, "lane": "quality-reviewer", "review_kind": "quality-pass", "depends_on": ["spec-reviewer"]},
    ],
    "deploy-gate": [
        {"sequence_index": 1, "lane": "deploy-reviewer", "review_kind": "release-review", "depends_on": []},
        {"sequence_index": 2, "lane": "quality-reviewer", "review_kind": "quality-pass", "depends_on": ["deploy-reviewer"]},
    ],
}


def build_baseline_verification(required: bool, verification: dict | None) -> dict | None:
    if not required:
        return None
    first_step = "Record the current baseline command or failing reproduction before editing."
    if isinstance(verification, dict) and verification.get("steps"):
        first_step = verification["steps"][0]
    return {
        "required": True,
        "proof_target": first_step,
        "artifact_fields": ["baseline command or scenario", "latest result", "clean-start note"],
    }


def build_worktree_bootstrap(recommendation: str | None) -> dict | None:
    if recommendation != "worktree":
        return None
    return {
        "recommended": True,
        "helper": "prepare_worktree.py",
        "required_evidence": [
            "isolated worktree path",
            "ignore safety for project-local worktree roots",
            "baseline command result",
        ],
    }


def build_review_sequence(execution_pipeline_key: str | None) -> list[dict]:
    return [dict(item) for item in REVIEW_SEQUENCES.get(execution_pipeline_key or "", [])]
