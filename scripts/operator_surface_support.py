from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from release_registry import merge_json_overlay


ROOT_DIR = Path(__file__).resolve().parent.parent
CORE_REGISTRY_PATH = ROOT_DIR / "packages" / "forge-core" / "data" / "orchestrator-registry.json"
OVERLAY_REGISTRY_PATHS = {
    "forge-antigravity": ROOT_DIR / "packages" / "forge-antigravity" / "overlay" / "data" / "orchestrator-registry.json",
    "forge-codex": ROOT_DIR / "packages" / "forge-codex" / "overlay" / "data" / "orchestrator-registry.json",
}
HOST_BY_BUNDLE = {
    "forge-antigravity": "antigravity",
    "forge-codex": "codex",
}
SESSION_MODE_LABELS = {
    "restore": "resume",
    "save": "save context",
    "handover": "handover",
}
CODEX_OPERATOR_SHARED_TEMPLATE_PATH = "docs/architecture/generated-host-artifacts/codex/workflows/operator/_shared_wrapper.md"


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def load_core_registry() -> dict:
    registry = _load_json(CORE_REGISTRY_PATH)
    return registry if isinstance(registry, dict) else {}


@lru_cache(maxsize=None)
def load_bundle_registry(bundle_name: str) -> dict:
    registry = load_core_registry()
    overlay_path = OVERLAY_REGISTRY_PATHS.get(bundle_name)
    if overlay_path and overlay_path.exists():
        registry = merge_json_overlay(registry, _load_json(overlay_path))
    return registry


def _surface_section(registry: dict, section_name: str) -> dict:
    section = registry.get(section_name, {})
    if not isinstance(section, dict):
        return {"actions": {}, "session_modes": {}}
    actions = section.get("actions", {})
    session_modes = section.get("session_modes", {})
    return {
        "actions": actions if isinstance(actions, dict) else {},
        "session_modes": session_modes if isinstance(session_modes, dict) else {},
    }


def repo_operator_surface() -> dict:
    return _surface_section(load_core_registry(), "repo_operator_surface")


def host_operator_surface(bundle_name: str) -> dict:
    return _surface_section(load_bundle_registry(bundle_name), "host_operator_surface")


def host_name(bundle_name: str) -> str:
    return HOST_BY_BUNDLE[bundle_name]


def _host_values(metadata: dict, field: str, *, bundle_name: str) -> list[str]:
    values_by_host = metadata.get(field, {})
    if not isinstance(values_by_host, dict):
        return []
    values = values_by_host.get(host_name(bundle_name), [])
    if not isinstance(values, list):
        return []
    return [item for item in values if isinstance(item, str) and item.strip()]


def _workflow_label(path_text: str) -> str:
    return path_text.removeprefix("workflows/")


def _host_action_rows(bundle_name: str) -> list[tuple[str, dict]]:
    rows: list[tuple[str, dict]] = []
    for action_name, metadata in host_operator_surface(bundle_name)["actions"].items():
        if not isinstance(metadata, dict):
            continue
        hosts = metadata.get("hosts", [])
        if not isinstance(hosts, list) or host_name(bundle_name) not in hosts:
            continue
        rows.append((action_name, metadata))
    return rows


def render_operator_alias_rows(bundle_name: str) -> str:
    lines: list[str] = []
    for _, metadata in _host_action_rows(bundle_name):
        aliases = _host_values(metadata, "primary_aliases_by_host", bundle_name=bundle_name)
        if not aliases:
            continue
        alias = aliases[0]
        target = metadata.get("skill") or _workflow_label(metadata.get("workflow", ""))
        lines.append(f"| `{alias}` | `{target}` |")
    return "\n".join(lines)


def render_natural_language_examples(bundle_name: str) -> str:
    lines: list[str] = []
    for action_name, metadata in _host_action_rows(bundle_name):
        examples = _host_values(metadata, "natural_language_examples_by_host", bundle_name=bundle_name)
        if not examples:
            continue
        lines.append(f'- "{examples[0]}" -> `{action_name}`')
    return "\n".join(lines)


def render_repo_public_action_bullets() -> str:
    lines: list[str] = []
    for action_name in repo_operator_surface()["actions"]:
        lines.append(f"- `{action_name}`")
    return "\n".join(lines)


def render_session_request_examples(bundle_name: str) -> str:
    lines: list[str] = []
    for mode_name, metadata in host_operator_surface(bundle_name)["session_modes"].items():
        if not isinstance(metadata, dict):
            continue
        examples = _host_values(metadata, "natural_language_examples_by_host", bundle_name=bundle_name)
        if not examples:
            continue
        label = SESSION_MODE_LABELS.get(mode_name, mode_name)
        lines.append(f'- "{examples[0]}" -> `{label}`')
    return "\n".join(lines)


def _metadata_by_name(bundle_name: str, section_name: str, item_name: str) -> dict:
    section = host_operator_surface(bundle_name).get(section_name, {})
    metadata = section.get(item_name, {})
    return metadata if isinstance(metadata, dict) else {}


def _yaml_list(items: list[str]) -> str:
    return "\n".join(f"  - {item}" for item in items)


def _code_block(commands: list[str]) -> str:
    normalized = [item for item in commands if item.strip()]
    rendered = [f"python {item}" if not item.startswith("python ") else item for item in normalized]
    return "```powershell\n" + "\n".join(rendered) + "\n```"


def _codex_action_config(action_name: str) -> dict:
    configs = {
        "help": {
            "heading": "Help - Codex Operator Wrapper",
            "goal": "keep `help` native to Codex, but still use Forge's core navigator.",
            "trigger": "natural-language request for guidance or what to do next",
            "quality_gates": [
                "Repo state inspected before advice",
                "One primary recommendation plus at most two alternatives",
                "Codex wrapper stays thin on top of the core navigator",
            ],
            "process": lambda command: "\n".join(
                [
                    "1. Resolve with:",
                    "",
                    "The resolver will prefer `.forge-artifacts/workflow-state/<project>/latest.json` when execution, chain, UI, run, or quality-gate tools have already persisted a current slice.",
                    "If the repo is Forge itself or multiple valid directions are available, use `docs/current/target-state.md` as the policy tie-break before answering.",
                    "",
                    _code_block([command]),
                    "",
                    "2. Short answer in Codex style:",
                    "   - Where are you?",
                    "   - next step to take",
                    "   - up to 2 other options if needed",
                ]
            ),
            "announcement": "Forge Codex: help | repo-first guidance, natural-language first",
        },
        "next": {
            "heading": "Next - Codex Operator Wrapper",
            "goal": "provide a clear next step for the Codex without creating an additional ceremony.",
            "trigger": "natural-language request for the next action",
            "quality_gates": [
                "Repo state inspected before advice",
                "One concrete next step only",
                "Codex wrapper stays thin on top of the core navigator",
            ],
            "process": lambda command: "\n".join(
                [
                    "1. Resolve with:",
                    "",
                    "The resolver will prefer `.forge-artifacts/workflow-state/<project>/latest.json` when execution, chain, UI, run, or quality-gate tools have already persisted a current slice.",
                    "If the repo is Forge itself and multiple next moves are plausible, use `docs/current/target-state.md` as the policy tie-break before choosing the main step.",
                    "",
                    _code_block([command]),
                    "",
                    "2. Short answer:",
                    "   - main next step",
                    "   - why this is the right step",
                    "   - up to 2 alternatives if needed",
                ]
            ),
            "announcement": "Forge Codex: next | one concrete next step from repo state",
        },
        "run": {
            "heading": "Run - Codex Operator Wrapper",
            "goal": "keep `run` natural in Codex, but still route according to evidence from core.",
            "trigger": "natural-language request to run a command, app, or check",
            "quality_gates": [
                "The command actually runs",
                "Key output or failure signal is reported",
                "The response ends with the next workflow when useful",
            ],
            "process": lambda command: "\n".join(
                [
                    "1. Close the command that needs to be run and have a reasonable timeout.",
                    "2. Run using core guidance:",
                    "",
                    _code_block([command]),
                    "",
                    "3. Short summary:",
                    "   - command was run",
                    "   - main signal",
                    "   - Error translation: include it when the command failed or timed out",
                    "   - next workflow (`test`, `debug`, or `deploy`) if needed",
                ]
            ),
            "announcement": "Forge Codex: run | execute, summarize, route from evidence",
        },
        "bump": {
            "heading": "Bump - Codex Operator Wrapper",
            "goal": "keep the bump flow short and clear for the Codex, but still follow the core's user-requested + justified semver contract.",
            "trigger": "explicit request to bump version or prepare a release",
            "quality_gates": [
                "User-requested only: do not treat generic wrap-up as a bump request",
                "Current version is stated and target version is either explicit or justified by inference",
                "Release verification steps are surfaced",
                "Wrapper does not hide core semver/change checklist",
            ],
            "process": lambda command: "\n".join(
                [
                    "1. If the user has not stated the bump level, infer from the diff repo and briefly state the reason.",
                    "2. Preview/apply using core planner:",
                    "",
                    _code_block(
                        [
                            "commands/prepare_bump.py --workspace <workspace>",
                            "commands/prepare_bump.py --workspace <workspace> --bump minor",
                            "commands/prepare_bump.py --workspace <workspace> --bump minor --apply --release-ready",
                        ]
                    ),
                    "",
                    "3. Short answer:",
                    "   - version from -> to",
                    "   - bump source: explicit or inferred",
                    "   - file changed",
                    "   - Which verification must be run?",
                ]
            ),
            "announcement": "Forge Codex: bump | release change with explicit or inferred semver",
        },
        "customize": {
            "heading": "Customize - Codex Preference Wrapper",
            "goal": "give Codex a short customization flow without inventing host-local preference schema.",
            "trigger": "natural-language request to change tone, detail, autonomy, pace, feedback style, or durable language rules",
            "quality_gates": [
                "Current preferences are inspected first",
                "Durable changes use the core canonical schema and writer",
                "Durable language rules live in the unified canonical preferences object; workspace `.brain/preferences.json` is a first-class repo-local scope",
                "The response states what changed and how interaction will feel different",
            ],
            "process": lambda command: "\n".join(
                [
                    "Fast path for language requests:",
                    "",
                    "- If the user only asks how to set language, Vietnamese diacritics, or writing conventions:",
                    "  - point first to durable updates through `commands/write_preferences.py`",
                    "  - only point to workspace `.brain/preferences.json` when they explicitly want repo-scoped overrides",
                    "  - reuse the short templates in `workflows/operator/references/personalization.md`",
                    "",
                    "1. Read current preferences:",
                    "",
                    _code_block(["commands/resolve_preferences.py --format json"]),
                    "",
                    "2. Map the request into canonical fields when it is about tone or delivery style:",
                    "   - `technical_level`",
                    "   - `detail_level`",
                    "   - `autonomy_level`",
                    "   - `pace`",
                    "   - `feedback_style`",
                    "   - `personality`",
                    "",
                    "3. If the user wants durable language, orthography, or host-native writing rules:",
                    "   - persist them through the unified canonical preferences file with `commands/write_preferences.py`",
                    "   - offer `--scope global|workspace|both` and keep workspace files sparse",
                    "   - use workspace `.brain/preferences.json` only for workspace-only overrides",
                    "",
                    "4. Preview or persist using the core writer:",
                    "",
                    _code_block(
                        [
                            "commands/write_preferences.py --detail-level concise --pace fast --feedback-style direct",
                            "commands/write_preferences.py --detail-level concise --pace fast --feedback-style direct --scope global --apply",
                            "commands/write_preferences.py --language vi --orthography vietnamese_diacritics --scope workspace --apply",
                        ]
                    ),
                    "",
                    "5. Persistence notes:",
                    "   - adapter-global preferences persist in `state/preferences.json`",
                    "   - workspace-local overrides persist in `.brain/preferences.json`",
                    "   - explicit `resolve_preferences.py --preferences-file ...` stays read-only",
                    "   - legacy split or native state may be migrated on `--apply`",
                    "",
                    "6. Short answer:",
                    "   - which fields changed",
                    "   - how the new response style will feel different",
                    "   - whether any workspace-only overrides remain separate from adapter-global state",
                ]
            ),
            "announcement": "Forge Codex: customize | update canonical preferences with minimal ceremony",
        },
    }
    return configs[action_name]


def render_codex_operator_wrapper(action_name: str) -> str:
    config = _codex_action_config(action_name)
    metadata = _metadata_by_name("forge-codex", "actions", action_name)
    command = metadata.get("core_engine_entrypoint", "")
    triggers = [config["trigger"]]
    source_text = (
        Path(ROOT_DIR / CODEX_OPERATOR_SHARED_TEMPLATE_PATH)
        .read_text(encoding="utf-8")
        .replace("{{FORGE_CODEX_OPERATOR_NAME}}", action_name)
        .replace("{{FORGE_CODEX_OPERATOR_TRIGGERS}}", _yaml_list(triggers))
        .replace("{{FORGE_CODEX_OPERATOR_QUALITY_GATES}}", _yaml_list(config["quality_gates"]))
        .replace("{{FORGE_CODEX_OPERATOR_HEADING}}", config["heading"])
        .replace("{{FORGE_CODEX_OPERATOR_GOAL}}", config["goal"])
        .replace("{{FORGE_CODEX_OPERATOR_PROCESS}}", config["process"](command))
        .replace("{{FORGE_CODEX_OPERATOR_ANNOUNCEMENT}}", config["announcement"])
    )
    return source_text


def render_contextual_placeholders(source_text: str, bundle_name: str, context: dict | None = None) -> str:
    context = context or {}
    action_name = context.get("action")
    if bundle_name == "forge-codex" and action_name in host_operator_surface(bundle_name)["actions"]:
        return render_codex_operator_wrapper(action_name)
    return source_text


def render_registry_placeholders(source_text: str, bundle_name: str, context: dict | None = None) -> str:
    rendered = render_contextual_placeholders(source_text, bundle_name, context=context)
    replacements = {
        "{{FORGE_REPO_PUBLIC_ACTIONS}}": render_repo_public_action_bullets(),
        "{{FORGE_CODEX_OPERATOR_ALIAS_ROWS}}": render_operator_alias_rows("forge-codex"),
        "{{FORGE_CODEX_SESSION_REQUEST_EXAMPLES}}": render_session_request_examples("forge-codex"),
        "{{FORGE_ANTIGRAVITY_PRIMARY_OPERATOR_ALIAS_ROWS}}": render_operator_alias_rows("forge-antigravity"),
        "{{FORGE_ANTIGRAVITY_SESSION_REQUEST_EXAMPLES}}": render_session_request_examples("forge-antigravity"),
        "{{FORGE_CODEX_NATURAL_LANGUAGE_EXAMPLES}}": render_natural_language_examples("forge-codex"),
        "{{FORGE_ANTIGRAVITY_NATURAL_LANGUAGE_EXAMPLES}}": render_natural_language_examples("forge-antigravity"),
    }
    for placeholder, replacement in replacements.items():
        rendered = rendered.replace(placeholder, replacement)
    return rendered

