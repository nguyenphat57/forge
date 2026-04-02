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

BROWSER_REQUIRED_MARKERS = (
    "browser",
    "screenshot",
    "playwright",
    "click through",
    "click-through",
    "multi-step",
    "walkthrough",
)

BROWSER_OPTIONAL_MARKERS = (
    "ui",
    "screen",
    "screens",
    "page",
    "pages",
    "form",
    "workflow",
    "flow",
    "responsive",
    "checkout",
)

FRONTEND_REPO_MARKERS = (
    ".tsx",
    ".jsx",
    "components",
    "pages",
    "app/",
    "src/",
)


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


def classify_browser_qa(
    prompt: str,
    *,
    intent: str,
    complexity: str,
    domain_skills: list[str],
    repo_signals: list[str],
) -> dict:
    prompt_lower = prompt.casefold()
    repo_signals_lower = [signal.casefold() for signal in repo_signals]
    has_frontend_signal = "frontend" in domain_skills or any(marker in prompt_lower for marker in BROWSER_OPTIONAL_MARKERS)
    has_frontend_repo = any(any(marker in signal for marker in FRONTEND_REPO_MARKERS) for signal in repo_signals_lower)
    explicit_browser = any(marker in prompt_lower for marker in BROWSER_REQUIRED_MARKERS)
    multi_surface = complexity == "large" or "parallel" in prompt_lower or "many screens" in prompt_lower

    if intent not in {"BUILD", "DEBUG", "OPTIMIZE", "VISUALIZE"}:
        return {"classification": "not-needed", "scope": []}

    if explicit_browser and (has_frontend_signal or has_frontend_repo):
        return {
            "classification": "required-for-this-packet",
            "scope": ["explicit browser reproduction"],
        }

    if has_frontend_signal or has_frontend_repo:
        scope = ["multi-surface frontend or workflow slice"] if multi_surface else ["ui or workflow verification"]
        return {
            "classification": "optional-accelerator",
            "scope": scope,
        }

    return {"classification": "not-needed", "scope": []}
