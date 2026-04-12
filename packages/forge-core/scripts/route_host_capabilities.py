from __future__ import annotations

from preferences_contract import DEFAULT_DELEGATION_PREFERENCE, normalize_delegation_preference


DELEGATION_TIER_ORDER = {
    "controller-baseline": 0,
    "review-lane-subagents": 1,
    "parallel-workers": 2,
}
DELEGATION_PREFERENCE_TO_TIER = {
    "off": "controller-baseline",
    "auto": "parallel-workers",
    "review-lanes": "review-lane-subagents",
    "parallel-workers": "parallel-workers",
}


def resolve_host_capability_tier(host_capabilities: dict | None) -> tuple[str, dict]:
    if not isinstance(host_capabilities, dict):
        host_capabilities = {}
    tiers = host_capabilities.get("tiers")
    active_tier = host_capabilities.get("active_tier")
    default_tier = host_capabilities.get("default_tier")
    if isinstance(tiers, dict):
        for tier_key in (active_tier, default_tier):
            if not isinstance(tier_key, str):
                continue
            tier = tiers.get(tier_key)
            if isinstance(tier, dict):
                return tier_key, tier

    supports_subagents = bool(host_capabilities.get("supports_subagents", False))
    supports_parallel_subagents = bool(host_capabilities.get("supports_parallel_subagents", supports_subagents))
    if supports_parallel_subagents:
        return (
            "parallel-workers",
            {
                "label": "Parallel workers",
                "supports_subagents": True,
                "supports_parallel_subagents": True,
                "dispatch_mode": "parallel-workers",
                "dispatch_reasons": ["host-supports-parallel-subagents"],
                "fallback_reasons": [],
            },
        )
    if supports_subagents:
        return (
            "review-lane-subagents",
            {
                "label": "Independent reviewers",
                "supports_subagents": True,
                "supports_parallel_subagents": False,
                "dispatch_mode": "independent-reviewers",
                "dispatch_reasons": ["host-supports-review-lane-subagents"],
                "fallback_reasons": ["parallel-safe packets run as sequential lanes on this host tier"],
            },
        )
    return (
        "controller-baseline",
        {
            "label": "Controller sequential lanes",
            "supports_subagents": False,
            "supports_parallel_subagents": False,
            "dispatch_mode": "controller-sequential",
            "dispatch_reasons": ["host-does-not-expose-subagents"],
            "fallback_reasons": ["review lanes stay packetized but execute sequentially"],
        },
    )


def resolve_delegation_preference(value: object) -> str:
    normalized = normalize_delegation_preference(value)
    if normalized is None:
        return DEFAULT_DELEGATION_PREFERENCE
    return normalized


def resolve_effective_delegation_mode(host_tier_key: str, delegation_preference: object) -> str:
    resolved_preference = resolve_delegation_preference(delegation_preference)
    preferred_tier_key = DELEGATION_PREFERENCE_TO_TIER[resolved_preference]
    host_rank = DELEGATION_TIER_ORDER.get(host_tier_key, 0)
    preference_rank = DELEGATION_TIER_ORDER.get(preferred_tier_key, 0)
    effective_rank = min(host_rank, preference_rank)
    for tier_key, rank in DELEGATION_TIER_ORDER.items():
        if rank == effective_rank:
            return tier_key
    return "controller-baseline"
