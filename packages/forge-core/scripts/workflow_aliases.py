from __future__ import annotations

import re
from pathlib import Path

from common import ROOT_DIR, normalize_text


WORKFLOW_SECTIONS = ("design", "execution")


def workflow_entries(root_dir: Path | None = None) -> list[dict[str, str]]:
    base_root = Path(root_dir) if root_dir is not None else ROOT_DIR
    workflows_root = base_root / "workflows"
    entries: list[dict[str, str]] = []
    for section in WORKFLOW_SECTIONS:
        section_root = workflows_root / section
        if not section_root.exists():
            continue
        for path in sorted(section_root.glob("*.md")):
            entries.append(
                {
                    "workflow": path.stem,
                    "relative_path": f"{section}/{path.name}",
                    "legacy_alias": _parse_legacy_shortcut(path) or "",
                }
            )
    return entries


def resolve_explicit_workflow_alias(prompt_text: str, root_dir: Path | None = None) -> str | None:
    match = re.match(r"^\s*/forge:([^\s]+)", prompt_text)
    if not match:
        return None
    requested = normalize_text(match.group(1))
    for item in workflow_entries(root_dir):
        if normalize_text(item["workflow"]) == requested:
            return item["workflow"]
    return None


def strip_explicit_workflow_alias(prompt_text: str) -> str:
    return re.sub(r"^\s*/forge:[^\s]+\s*", "", prompt_text, count=1)


def _parse_legacy_shortcut(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"(?m)^\s*-\s+shortcut:\s*(/\S+)\s*$", text)
    if not match:
        return None
    shortcut = match.group(1).strip()
    return shortcut or None
