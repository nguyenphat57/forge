from __future__ import annotations

import argparse
import json
from pathlib import Path

from _forge_skill_command import bootstrap_command_paths

bootstrap_command_paths()

from text_utils import configure_stdio, excerpt_text, normalize_text, read_text


FORMAT_CHOICES = ("text", "json")


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=FORMAT_CHOICES, default="text", help="Output format")


def _keyword_hit(text: str, keywords: tuple[str, ...], *, require_all: bool = False) -> bool:
    normalized = normalize_text(text)
    if require_all:
        return all(keyword in normalized for keyword in keywords)
    return any(keyword in normalized for keyword in keywords)


def _item(key: str, label: str, text: str, keywords: tuple[str, ...], *, require_all: bool = False) -> dict:
    return {
        "key": key,
        "label": label,
        "status": "PASS" if _keyword_hit(text, keywords, require_all=require_all) else "WARN",
    }


def _load_bundle(root: Path, extra_path: Path | None = None) -> tuple[list[str], str]:
    paths: list[Path] = []
    master = root / "MASTER.md"
    if master.exists():
        paths.append(master)
    if extra_path is not None and extra_path.exists():
        paths.append(extra_path)
    combined = "\n\n".join(read_text(path) for path in paths)
    return [str(path) for path in paths], combined


def detect_mode(source: Path, *, screen: str | None, surface: str | None, explicit_mode: str) -> str:
    if explicit_mode != "auto":
        return explicit_mode
    if screen or (source.is_dir() and (source / "pages").exists()):
        return "ui"
    if surface or (source.is_dir() and (source / "surfaces").exists()):
        return "backend"
    return "generic"


def load_source_text(source: Path, *, screen: str | None, surface: str | None) -> tuple[list[str], str]:
    if source.is_file():
        return [str(source)], read_text(source)
    if screen:
        return _load_bundle(source, source / "pages" / f"{screen}.md")
    if surface:
        return _load_bundle(source, source / "surfaces" / f"{surface}.md")
    return _load_bundle(source)


def build_ui_checklist(text: str) -> list[dict]:
    return [
        _item("scope", "Clear scope", text, ("scope", "screen", "flow", "goal")),
        _item("states", "Explicit states", text, ("default", "loading", "empty", "error"), require_all=True),
        _item("responsive", "Responsive or platform notes", text, ("responsive", "mobile", "tablet", "desktop", "platform")),
        _item("accessibility", "Accessibility boundaries", text, ("accessibility", "a11y", "keyboard", "focus", "contrast", "screen reader")),
        _item("watchouts", "Implementation watchouts", text, ("watchout", "constraint", "performance", "stack", "implementation")),
    ]


def build_backend_checklist(text: str) -> list[dict]:
    return [
        _item("contract", "Clear contract or surface definition", text, ("contract", "surface", "endpoint", "request", "response")),
        _item("compatibility", "Caller impact or compatibility notes", text, ("compatibility", "compatible", "caller", "consumer", "backward")),
        _item("data", "Migration or persistence notes", text, ("migration", "schema", "database", "persistence", "data model")),
        _item("retries", "Idempotency or retry guidance", text, ("idempotent", "retry", "replay", "async", "queue")),
        _item("rollback", "Observability or rollback notes", text, ("observability", "logging", "metrics", "tracing", "rollback")),
    ]


def build_generic_checklist(text: str) -> list[dict]:
    return [
        _item("problem", "Problem framing", text, ("problem", "context", "goal")),
        _item("scope", "Goals and non-goals", text, ("goal", "non-goal")),
        _item("requirements", "Concrete requirements or steps", text, ("requirement", "task", "step", "acceptance")),
        _item("verification", "Proof or verification notes", text, ("proof", "verification", "test", "smoke")),
    ]


def summarize_checklist(checklist: list[dict]) -> dict:
    warnings = [item["label"] for item in checklist if item["status"] != "PASS"]
    return {
        "status": "PASS" if not warnings else "WARN",
        "warnings": warnings,
    }


def build_requirements_result(
    *,
    source: Path,
    mode: str,
    screen: str | None,
    surface: str | None,
) -> dict:
    paths, text = load_source_text(source, screen=screen, surface=surface)
    if not paths:
        return {
            "status": "FAIL",
            "mode": mode,
            "source": str(source),
            "paths": [],
            "checklist": [],
            "message": "No readable markdown sources were found.",
        }
    builders = {
        "ui": build_ui_checklist,
        "backend": build_backend_checklist,
        "generic": build_generic_checklist,
    }
    checklist = builders.get(mode, build_generic_checklist)(text)
    summary = summarize_checklist(checklist)
    return {
        "status": summary["status"],
        "mode": mode,
        "source": str(source),
        "paths": paths,
        "checklist": checklist,
        "warnings": summary["warnings"],
        "excerpt": excerpt_text(text, max_lines=6, max_chars=360),
    }


def build_check_result(
    *,
    source: Path,
    mode: str,
    screen: str | None,
    surface: str | None,
) -> dict:
    result = build_requirements_result(source=source, mode=mode, screen=screen, surface=surface)
    if result["status"] == "FAIL":
        return result
    label = "screen" if screen else "surface" if surface else "brief"
    detail = screen or surface or source.name
    result["message"] = f"{mode} {label} checklist completed for {detail}"
    return result


def emit_result(result: dict, output_format: str) -> int:
    configure_stdio()
    if output_format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["status"] != "FAIL" else 1
    print(f"[{result['status']}] {result.get('message', result.get('source', 'brief check'))}")
    if result.get("paths"):
        print("paths:")
        for path in result["paths"]:
            print(f"- {path}")
    for item in result.get("checklist", []):
        print(f"- {item['status']}: {item['label']}")
    if result.get("warnings"):
        print("warnings:")
        for warning in result["warnings"]:
            print(f"- {warning}")
    excerpt = result.get("excerpt")
    if isinstance(excerpt, str) and excerpt:
        print("excerpt:")
        print(excerpt)
    return 0 if result["status"] != "FAIL" else 1
