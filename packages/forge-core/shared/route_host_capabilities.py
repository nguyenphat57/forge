from __future__ import annotations


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
