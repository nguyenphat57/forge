from __future__ import annotations

from pathlib import Path

from common import (
    detect_runtimes,
    extract_skill_names,
    keyword_in_text,
    normalize_text,
    read_text,
    reserved_skill_names,
    skill_aliases,
)
from route_analysis import uses_prompt_only_scope


def section_text(document: str, heading: str, next_heading: str | None = None) -> str:
    start = document.find(heading)
    if start == -1:
        return ""
    start += len(heading)
    if next_heading is None:
        return document[start:]
    end = document.find(next_heading, start)
    if end == -1:
        return document[start:]
    return document[start:end]


def resolve_workspace_router(router_doc: Path | None) -> Path | None:
    if router_doc is None:
        return None
    if not router_doc.exists():
        return router_doc
    if router_doc.name.casefold() != "agents.md":
        return router_doc

    from check_workspace_router import detect_router_map

    resolved = detect_router_map(router_doc.parent, router_doc)
    return resolved or router_doc


def infer_local_companions(
    prompt_text: str,
    repo_signals: list[str],
    router_doc: Path | None,
    intent: str,
    complexity: str,
    registry: dict,
) -> list[str]:
    if router_doc is None or not router_doc.exists():
        return []

    content = read_text(router_doc)
    scope_policy_section = section_text(content, "## Scope Policy", "## Local Skill Inventory")
    if not scope_policy_section:
        scope_policy_section = section_text(content, "## Scope Policy", "## Routing Map")
    excluded_skill_names = reserved_skill_names() | set(extract_skill_names(scope_policy_section))
    local_inventory = section_text(content, "## Local Skill Inventory", "## Routing Map")
    skill_source = local_inventory or content
    skills = [name for name in extract_skill_names(skill_source) if name not in excluded_skill_names]
    normalized_prompt = normalize_text(prompt_text)
    normalized_signals = normalize_text(" ".join(repo_signals))
    prompt_only = uses_prompt_only_scope(
        intent,
        complexity,
        registry,
        "prompt_only_local_companion_intents",
        "local_companions",
    )
    policy = registry.get("minimal_routing_policy", {})
    allow_runtime_only = intent in policy.get("runtime_signal_local_companion_intents", []) and not prompt_only
    score_floor = policy.get("repo_signal_companion_score_floor", {}).get(complexity, 1)
    max_companions = policy.get("max_local_companions", {}).get(complexity, 3)
    runtime_context: set[str] = set()
    for runtime in detect_runtimes(repo_signals, registry):
        runtime_context.add(normalize_text(runtime))
        runtime_context.update(skill_aliases(runtime))

    scored: list[tuple[int, str]] = []
    for skill_name in skills:
        aliases = skill_aliases(skill_name)
        prompt_score = 0
        signal_score = 0
        for alias in aliases:
            normalized_alias = normalize_text(alias)
            if keyword_in_text(normalized_alias, normalized_prompt):
                prompt_score += 1
            if keyword_in_text(normalized_alias, normalized_signals):
                signal_score += 1
        runtime_score = 2 if aliases & runtime_context else 0
        if prompt_only and prompt_score <= 0:
            continue
        if prompt_score <= 0 and not allow_runtime_only:
            continue
        if prompt_score <= 0 and (signal_score + runtime_score) < score_floor:
            continue
        score = (prompt_score * 10) + signal_score + runtime_score
        if score > 0:
            scored.append((score, skill_name))

    scored.sort(key=lambda item: (-item[0], item[1]))
    ordered: list[str] = []
    for _, skill_name in scored:
        if skill_name not in ordered:
            ordered.append(skill_name)
    return ordered[:max_companions]
