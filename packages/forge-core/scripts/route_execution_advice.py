from __future__ import annotations

from common import normalize_text, score_keywords


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

FAST_LANE_BLOCKER_KEYWORDS = (
    "migration",
    "schema",
    "auth",
    "payment",
    "public api",
    "public interface",
    "breaking",
    "rollout",
    "release",
    "deploy",
    "parallel",
    "many screens",
    "many endpoints",
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


def _ui_detection_scores(prompt: str, repo_signals: list[str], registry: dict) -> tuple[bool, bool]:
    ui_detection = registry.get("ui_detection", {})
    normalized_prompt = normalize_text(prompt)
    normalized_signals = normalize_text(" ".join(repo_signals))
    prompt_score = score_keywords(normalized_prompt, ui_detection.get("prompt_keywords", []))
    signal_score = score_keywords(normalized_signals, ui_detection.get("repo_signals", []))
    weak_signal_score = score_keywords(normalized_signals, ui_detection.get("weak_repo_signals", []))
    return prompt_score > 0, max(signal_score - weak_signal_score, 0) > 0


def classify_browser_qa(
    prompt: str,
    *,
    intent: str,
    complexity: str,
    repo_signals: list[str],
    registry: dict,
) -> dict:
    prompt_lower = prompt.casefold()
    has_ui_prompt, has_ui_repo = _ui_detection_scores(prompt, repo_signals, registry)
    has_frontend_signal = has_ui_prompt or any(marker in prompt_lower for marker in BROWSER_OPTIONAL_MARKERS)
    has_frontend_repo = has_ui_repo
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


def _required_stage_names(required_stages: list[dict] | None) -> list[str]:
    names: list[str] = []
    if not isinstance(required_stages, list):
        return names
    for item in required_stages:
        if not isinstance(item, dict):
            continue
        if item.get("status") == "skipped":
            continue
        stage_name = item.get("stage")
        if isinstance(stage_name, str) and stage_name.strip():
            names.append(stage_name.strip())
    return names


def classify_packet_mode(
    prompt: str,
    *,
    intent: str,
    complexity: str,
    execution_mode: str | None,
    execution_pipeline_key: str | None,
    required_stages: list[dict] | None,
    quality_profile_key: str,
) -> dict:
    active_stages = set(_required_stage_names(required_stages))
    reasons: list[str] = []
    eligible = True
    prompt_lower = prompt.casefold()

    if intent not in {"BUILD", "DEBUG", "OPTIMIZE"}:
        eligible = False
        reasons.append("Intent does not use packetized execution slices.")
    if complexity != "small":
        eligible = False
        reasons.append("Fast lane is restricted to small low-blast slices.")
    if execution_mode not in {None, "single-track"}:
        eligible = False
        reasons.append("Fast lane requires single-track execution.")
    if execution_pipeline_key not in {None, "single-lane"}:
        eligible = False
        reasons.append("Fast lane requires a single-lane packet.")
    if quality_profile_key != "standard":
        eligible = False
        reasons.append("High-risk quality profile requires the standard packet mode.")

    blocked_stages = {
        "spec-review",
        "self-review",
        "secure",
        "deploy",
    }
    if active_stages & blocked_stages:
        eligible = False
        reasons.append("Release or boundary stages require the full packet contract.")
    if any(keyword in prompt_lower for keyword in FAST_LANE_BLOCKER_KEYWORDS):
        eligible = False
        reasons.append("Prompt includes high-risk markers that require full packetization.")

    if eligible:
        return {
            "packet_mode": "fast-lane",
            "eligible": True,
            "assumptions_first_mode": True,
            "reasons": [
                "Small low-risk slice with single-track and single-lane execution.",
                "No release-tail or high-risk boundary stage is active.",
            ],
        }

    return {
        "packet_mode": "standard",
        "eligible": False,
        "assumptions_first_mode": False,
        "reasons": reasons or ["Fast lane guardrails were not met."],
    }
