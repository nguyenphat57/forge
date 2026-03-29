from __future__ import annotations

from pathlib import Path

from common import default_artifact_dir, slugify, timestamp_slug


def resolve_change_paths(workspace: Path, *, summary: str | None = None, slug: str | None = None) -> dict[str, Path]:
    change_slug = slugify(slug or summary or "change")
    root = default_artifact_dir(str(workspace), "changes")
    active_root = root / "active" / change_slug
    archive_root = root / "archive" / f"{timestamp_slug()}-{change_slug}"
    return {
        "root": root,
        "active_root": active_root,
        "archive_root": archive_root,
        "proposal": active_root / "proposal.md",
        "design": active_root / "design.md",
        "implementation_packet": active_root / "implementation-packet.md",
        "tasks": active_root / "tasks.md",
        "resume": active_root / "resume.md",
        "status": active_root / "status.json",
        "verification": active_root / "verification.md",
    }
