from __future__ import annotations


TECHNICAL_STYLE = {
    "newbie": {
        "terminology_mode": "translated",
        "term_explanation_policy": "always",
        "acronym_policy": "avoid",
        "step_granularity": "small",
    },
    "basic": {
        "terminology_mode": "mixed",
        "term_explanation_policy": "first-use",
        "acronym_policy": "define-on-first-use",
        "step_granularity": "medium",
    },
    "technical": {
        "terminology_mode": "standard",
        "term_explanation_policy": "on-request",
        "acronym_policy": "standard",
        "step_granularity": "compact",
    },
}

DETAIL_STYLE = {
    "concise": {
        "response_verbosity": "concise",
        "context_depth": "minimal",
        "option_spread": "tight",
    },
    "balanced": {
        "response_verbosity": "balanced",
        "context_depth": "targeted",
        "option_spread": "focused",
    },
    "detailed": {
        "response_verbosity": "detailed",
        "context_depth": "thorough",
        "option_spread": "broad",
    },
}

AUTONOMY_STYLE = {
    "guided": {
        "decision_mode": "confirm-major-assumptions",
        "plan_visibility": "high",
        "execution_bias": "pause-at-branching-points",
    },
    "balanced": {
        "decision_mode": "state-assumptions-and-proceed-when-safe",
        "plan_visibility": "medium",
        "execution_bias": "execute-safe-slices",
    },
    "autonomous": {
        "decision_mode": "propose-best-path-and-execute-safe-slices",
        "plan_visibility": "targeted",
        "execution_bias": "move-forward-until-risky-boundary",
    },
}

PACE_STYLE = {
    "steady": {
        "delivery_pace": "steady",
        "iteration_rhythm": "pause-at-notable-branch-points",
    },
    "balanced": {
        "delivery_pace": "balanced",
        "iteration_rhythm": "default-checkpoints",
    },
    "fast": {
        "delivery_pace": "fast",
        "iteration_rhythm": "push-until-risk-boundary",
    },
}

FEEDBACK_STYLE = {
    "gentle": {
        "feedback_mode": "gentle",
        "critique_style": "encouraging-first",
    },
    "balanced": {
        "feedback_mode": "balanced",
        "critique_style": "direct-when-useful",
    },
    "direct": {
        "feedback_mode": "direct",
        "critique_style": "call-out-gaps-plainly",
    },
}

PERSONALITY_STYLE = {
    "default": {
        "tone": "pragmatic",
        "teaching_mode": "as-needed",
        "challenge_level": "measured",
    },
    "mentor": {
        "tone": "supportive-pragmatic",
        "teaching_mode": "explain-why",
        "challenge_level": "light",
    },
    "strict-coach": {
        "tone": "direct-high-standard",
        "teaching_mode": "best-practice-first",
        "challenge_level": "high",
    },
}


def resolve_response_style(preferences: dict[str, str]) -> dict[str, str]:
    technical_level = preferences["technical_level"]
    detail_level = preferences["detail_level"]
    autonomy_level = preferences["autonomy_level"]
    pace = preferences["pace"]
    feedback_style = preferences["feedback_style"]
    personality = preferences["personality"]

    style: dict[str, str] = {}
    style.update(TECHNICAL_STYLE[technical_level])
    style.update(DETAIL_STYLE[detail_level])
    style.update(AUTONOMY_STYLE[autonomy_level])
    style.update(PACE_STYLE[pace])
    style.update(FEEDBACK_STYLE[feedback_style])
    style.update(PERSONALITY_STYLE[personality])
    return style
