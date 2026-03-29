from __future__ import annotations

import json
from pathlib import Path

from common import keyword_in_text, normalize_text
from companion_catalog import load_companion_specs


def _workspace_dependencies(workspace: Path | None) -> tuple[set[str], set[str]]:
    if workspace is None:
        return set(), set()
    package_json = workspace / "package.json"
    if not package_json.exists():
        return set(), set()
    payload = json.loads(package_json.read_text(encoding="utf-8"))
    dependencies = payload.get("dependencies")
    dev_dependencies = payload.get("devDependencies")
    return (
        set(dependencies) if isinstance(dependencies, dict) else set(),
        set(dev_dependencies) if isinstance(dev_dependencies, dict) else set(),
    )


def _feature_match(rule: dict, prompt_text: str, repo_text: str, workspace: Path | None, dependencies: set[str], dev_dependencies: set[str]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    for keyword in rule.get("prompt_keywords_any", []):
        normalized = normalize_text(str(keyword))
        if normalized and keyword_in_text(normalized, prompt_text):
            reasons.append(f"prompt:{keyword}")
            break
    for dependency in rule.get("package_dependencies_any", []):
        if dependency in dependencies:
            reasons.append(f"dependency:{dependency}")
            break
    for dependency in rule.get("package_dev_dependencies_any", []):
        if dependency in dev_dependencies:
            reasons.append(f"devDependency:{dependency}")
            break
    for marker in rule.get("file_markers_any", []):
        if workspace is not None and (workspace / str(marker)).exists():
            reasons.append(f"file:{marker}")
            break
    for signal in rule.get("repo_signals_any", []):
        normalized = normalize_text(str(signal))
        if normalized and normalized in repo_text:
            reasons.append(f"signal:{signal}")
            break
    return bool(reasons), reasons


def _match_strength(features: dict[str, bool], capabilities: dict) -> str:
    quality_bands = capabilities.get("quality_bands", {})
    strong = quality_bands.get("strong", [])
    baseline = quality_bands.get("baseline", [])
    if isinstance(strong, list) and strong and all(features.get(item, False) for item in strong):
        return "strong"
    if isinstance(baseline, list) and baseline and all(features.get(item, False) for item in baseline):
        return "baseline"
    return "activation-only"


def match_companions(prompt_text: str = "", repo_signals: list[str] | None = None, workspace: Path | None = None) -> list[dict]:
    prompt_normalized = normalize_text(prompt_text)
    repo_text = normalize_text(" ".join(repo_signals or []))
    dependencies, dev_dependencies = _workspace_dependencies(workspace)
    matches: list[dict] = []
    for spec in load_companion_specs():
        capabilities = spec["capabilities"]
        feature_rules = capabilities.get("feature_rules", {})
        features: dict[str, bool] = {}
        reasons: list[str] = []
        for feature_name, rule in feature_rules.items():
            matched, feature_reasons = _feature_match(rule, prompt_normalized, repo_text, workspace, dependencies, dev_dependencies)
            features[str(feature_name)] = matched
            reasons.extend(feature_reasons)
        activation_any = capabilities.get("activation_any", [])
        if not isinstance(activation_any, list) or not any(features.get(item, False) for item in activation_any):
            continue
        matches.append(
            {
                "id": capabilities.get("id") or spec["name"],
                "package": spec["name"],
                "root": str(spec["package_dir"]),
                "strength": _match_strength(features, capabilities),
                "features": features,
                "reasons": reasons,
                "spec": spec,
            }
        )
    matches.sort(key=lambda item: ({"strong": 0, "baseline": 1, "activation-only": 2}.get(item["strength"], 3), item["id"]))
    return matches


def resolve_companion_preset(selector: str) -> dict:
    exact_match: dict | None = None
    short_matches: list[dict] = []
    for spec in load_companion_specs():
        capabilities = spec["capabilities"]
        companion_id = str(capabilities.get("id") or spec["name"])
        for preset in capabilities.get("init_presets", []):
            if not isinstance(preset, dict) or not preset.get("id"):
                continue
            full_id = f"{companion_id}/{preset['id']}"
            candidate = {"companion_id": companion_id, "preset": preset, "spec": spec, "full_id": full_id}
            if selector == full_id:
                exact_match = candidate
            if selector == preset["id"]:
                short_matches.append(candidate)
    if exact_match is not None:
        return exact_match
    if len(short_matches) == 1:
        return short_matches[0]
    if len(short_matches) > 1:
        raise ValueError(f"Preset '{selector}' is ambiguous across multiple companions.")
    raise ValueError(f"Unknown companion preset: {selector}")
