from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
CORE_SKILL_PATH = ROOT_DIR / "packages" / "forge-core" / "SKILL.md"

SECTION_PATTERN = re.compile(r"^## ([^\n]+)\n", re.MULTILINE)

ADAPTER_SKILL_SPECS: dict[str, dict[str, object]] = {
    "forge-codex": {
        "delta_path": ROOT_DIR / "packages" / "forge-codex" / "overlay" / "SKILL.delta.md",
        "output_path": ROOT_DIR / "packages" / "forge-codex" / "overlay" / "SKILL.md",
        "section_order": [
            ("delta", "Host Boundary"),
            ("core", "Bootstrap Rules"),
            ("core", "Routing Contract"),
            ("delta", "Response Personalization"),
            ("delta", "Codex Operator Surface"),
            ("delta", "Codex Multi-Agent Delegation"),
            ("core", "Verification Contract"),
            ("core", "Solo Profile And Workflow-State Contract"),
            ("core", "Skill Laws"),
            ("core", "Reference Map"),
            ("delta", "Activation Announcement"),
        ],
    },
    "forge-antigravity": {
        "delta_path": ROOT_DIR / "packages" / "forge-antigravity" / "overlay" / "SKILL.delta.md",
        "output_path": ROOT_DIR / "packages" / "forge-antigravity" / "overlay" / "SKILL.md",
        "section_order": [
            ("delta", "Host Boundary"),
            ("delta", "Antigravity Protocol Bridge"),
            ("delta", "Antigravity Artifact Boundary"),
            ("core", "Bootstrap Rules"),
            ("core", "Routing Contract"),
            ("delta", "Response Personalization"),
            ("delta", "Antigravity Operator Surface"),
            ("core", "Verification Contract"),
            ("core", "Solo Profile And Workflow-State Contract"),
            ("core", "Skill Laws"),
            ("core", "Reference Map"),
            ("delta", "Activation Announcement"),
        ],
    },
}

SHARED_SECTION_HEADINGS = (
    "EXTREMELY-IMPORTANT",
    "Instruction Priority",
    "The Rule",
    "Red Flags",
    "Workflow Priority",
    "User Instructions",
)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        return "", text
    marker = "\n---\n"
    end = text.find(marker, 4)
    if end == -1:
        raise ValueError("Markdown frontmatter is not closed with `---`.")
    frontmatter = text[: end + len(marker)]
    body = text[end + len(marker) :]
    return frontmatter, body.lstrip("\n")


def _parse_document(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = _split_frontmatter(text)
    matches = list(SECTION_PATTERN.finditer(body))
    if matches:
        prelude = body[: matches[0].start()].rstrip()
    else:
        prelude = body.rstrip()
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[heading] = body[start:end].strip()
    return {
        "frontmatter": frontmatter.strip(),
        "prelude": prelude,
        "sections": sections,
        "text": text,
    }


def _sync_section_after(text: str, *, heading: str, section_text: str, after_heading: str) -> str:
    matches = list(SECTION_PATTERN.finditer(text))
    target_match = None
    after_match = None
    for match in matches:
        current_heading = match.group(1).strip()
        if current_heading == heading:
            target_match = match
        if current_heading == after_heading:
            after_match = match

    if target_match is not None:
        target_index = matches.index(target_match)
        start = target_match.start()
        end = matches[target_index + 1].start() if target_index + 1 < len(matches) else len(text)
        return text[:start].rstrip() + "\n\n" + section_text.strip() + "\n\n" + text[end:].lstrip("\n")

    if after_match is None:
        raise ValueError(f"Cannot insert section `{heading}` because `{after_heading}` was not found.")

    after_index = matches.index(after_match)
    insert_at = matches[after_index + 1].start() if after_index + 1 < len(matches) else len(text)
    return text[:insert_at].rstrip() + "\n\n" + section_text.strip() + "\n\n" + text[insert_at:].lstrip("\n")


def adapter_skill_specs() -> list[dict[str, object]]:
    return [
        {"bundle": bundle_name, **spec}
        for bundle_name, spec in ADAPTER_SKILL_SPECS.items()
    ]


def compose_adapter_skill(bundle_name: str, *, core_skill_path: Path = CORE_SKILL_PATH) -> str:
    if bundle_name not in ADAPTER_SKILL_SPECS:
        raise KeyError(f"Unknown adapter bundle for SKILL composition: {bundle_name}")

    spec = ADAPTER_SKILL_SPECS[bundle_name]
    output_path = Path(spec["output_path"])
    core_doc = _parse_document(core_skill_path)
    operating_biases = core_doc["sections"].get("Agent Operating Biases")
    if operating_biases is None:
        raise ValueError("Core SKILL is missing shared section `Agent Operating Biases`.")
    if output_path.exists():
        return _sync_section_after(
            output_path.read_text(encoding="utf-8"),
            heading="Agent Operating Biases",
            section_text=operating_biases,
            after_heading="Workflow Priority",
        )

    core_doc = _parse_document(core_skill_path)
    delta_doc = _parse_document(spec["delta_path"])
    core_sections = core_doc["sections"]
    delta_sections = delta_doc["sections"]

    missing_shared = [heading for heading in SHARED_SECTION_HEADINGS if heading not in core_sections]
    if missing_shared:
        raise ValueError(f"Core SKILL is missing shared sections required for composition: {missing_shared}")

    rendered_sections: list[str] = []
    for source_name, heading in spec["section_order"]:
        source_sections = core_sections if source_name == "core" else delta_sections
        if heading not in source_sections:
            raise ValueError(f"{bundle_name} is missing section `{heading}` in {source_name} source.")
        rendered_sections.append(source_sections[heading])

    parts: list[str] = []
    frontmatter = delta_doc["frontmatter"]
    if frontmatter:
        parts.append(frontmatter)
    prelude = str(delta_doc["prelude"]).strip()
    if prelude:
        parts.append(prelude)
    parts.extend(rendered_sections)
    return "\n\n".join(part.rstrip() for part in parts if part).strip() + "\n"


def write_composed_adapter_skill(bundle_name: str, output_path: Path) -> str:
    rendered = compose_adapter_skill(bundle_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    return rendered


def ensure_generated_overlay_skills(*, check: bool) -> dict[str, object]:
    artifacts: list[dict[str, object]] = []
    stale_outputs: list[dict[str, object]] = []

    for spec in adapter_skill_specs():
        output_path = Path(spec["output_path"])
        rendered = compose_adapter_skill(str(spec["bundle"]))
        current_text = output_path.read_text(encoding="utf-8") if output_path.exists() else None
        stale = current_text != rendered
        artifact = {
            "bundle": spec["bundle"],
            "delta_path": str(Path(spec["delta_path"]).relative_to(ROOT_DIR).as_posix()),
            "output_path": str(output_path.relative_to(ROOT_DIR).as_posix()),
            "output_exists": output_path.exists(),
            "stale": stale,
            "expected_sha256": _sha256(rendered),
            "output_sha256": _sha256(current_text) if current_text is not None else None,
        }
        artifacts.append(artifact)
        if stale:
            stale_outputs.append(
                {
                    "bundle": spec["bundle"],
                    "path": artifact["output_path"],
                }
            )
            if not check:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(rendered, encoding="utf-8")
                artifact["output_exists"] = True
                artifact["output_sha256"] = artifact["expected_sha256"]
                artifact["stale"] = False

    if not check:
        stale_outputs = []

    return {
        "status": "PASS" if not stale_outputs else "FAIL",
        "artifacts": artifacts,
        "stale_outputs": stale_outputs,
    }


def compose_to_json(bundle_name: str) -> str:
    payload = {
        "bundle": bundle_name,
        "output": compose_adapter_skill(bundle_name),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
