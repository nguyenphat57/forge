from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
BUILD_MANIFEST_PATH = ROOT_DIR / "BUILD-MANIFEST.json"
INSTALL_MANIFEST_PATH = ROOT_DIR / "INSTALL-MANIFEST.json"
STATE_ROOT_ENV = "FORGE_DESIGN_STATE_ROOT"
DEFAULT_RENDERS_RELATIVE_PATH = Path("state") / "renders.jsonl"
DEFAULT_PACKETS_RELATIVE_DIR = Path("packets")


def slugify(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return text or "design-packet"


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _default_state_root() -> Path:
    return (ROOT_DIR.parent / "forge-design-state").resolve()


def _materialize_state(state: dict | None, *, installed: bool) -> dict[str, str]:
    root = _default_state_root()
    if isinstance(state, dict):
        root_value = state.get("root")
        if installed and isinstance(root_value, str) and root_value.strip():
            root = Path(root_value).expanduser().resolve()
        else:
            dev_root = state.get("dev_root")
            if isinstance(dev_root, dict) and dev_root.get("strategy") == "bundle-parent-relative":
                relative = dev_root.get("path_relative")
                if isinstance(relative, str) and relative.strip():
                    root = (ROOT_DIR.parent / Path(relative)).resolve()
    return {
        "scope": (state or {}).get("scope") or "runtime-tool-global",
        "root": str(root),
        "renders_path": str((root / Path((state or {}).get("renders_relative_path") or DEFAULT_RENDERS_RELATIVE_PATH)).resolve()),
        "packets_dir": str((root / Path((state or {}).get("packets_relative_dir") or DEFAULT_PACKETS_RELATIVE_DIR)).resolve()),
    }


def resolve_state_paths(explicit_root: str | None = None) -> dict[str, str]:
    if explicit_root and explicit_root.strip():
        root = Path(explicit_root).expanduser().resolve()
        return {
            "scope": "runtime-tool-global",
            "root": str(root),
            "renders_path": str((root / DEFAULT_RENDERS_RELATIVE_PATH).resolve()),
            "packets_dir": str((root / DEFAULT_PACKETS_RELATIVE_DIR).resolve()),
        }
    override = os.environ.get(STATE_ROOT_ENV)
    if override and override.strip():
        return resolve_state_paths(override)
    install_manifest = _load_json(INSTALL_MANIFEST_PATH)
    if install_manifest is not None:
        return _materialize_state(install_manifest.get("state"), installed=True)
    build_manifest = _load_json(BUILD_MANIFEST_PATH)
    return _materialize_state((build_manifest or {}).get("state"), installed=False)


def ensure_state_layout(paths: dict[str, str]) -> dict[str, str]:
    Path(paths["root"]).mkdir(parents=True, exist_ok=True)
    renders_path = Path(paths["renders_path"])
    renders_path.parent.mkdir(parents=True, exist_ok=True)
    Path(paths["packets_dir"]).mkdir(parents=True, exist_ok=True)
    renders_path.touch(exist_ok=True)
    return paths


def append_render_event(paths: dict[str, str], event: dict[str, object]) -> None:
    payload = {"rendered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **event}
    with Path(paths["renders_path"]).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def default_packet_path(paths: dict[str, str], *, project_name: str, mode: str, screen: str | None) -> Path:
    stem = slugify("-".join(part for part in (project_name, mode, screen or "shared") if part))
    return (Path(paths["packets_dir"]) / f"{stem}.html").resolve()
