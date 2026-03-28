from __future__ import annotations

import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
PACKAGE_MATRIX_PATH = ROOT_DIR / "docs" / "release" / "package-matrix.json"


def _load_entries() -> list[dict]:
    payload = json.loads(PACKAGE_MATRIX_PATH.read_text(encoding="utf-8"))
    bundles = payload.get("bundles")
    if not isinstance(bundles, list) or not bundles:
        raise ValueError(f"Package matrix must define a non-empty bundles list: {PACKAGE_MATRIX_PATH}")
    return bundles


def load_package_matrix() -> dict[str, dict]:
    matrix: dict[str, dict] = {}
    for index, item in enumerate(_load_entries()):
        if not isinstance(item, dict):
            raise ValueError(f"Package matrix entry #{index} must be an object")
        name = item.get("name")
        host = item.get("host")
        strategy = item.get("default_target_strategy")
        required_paths = item.get("required_bundle_paths")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Package matrix entry #{index} is missing a bundle name")
        if name in matrix:
            raise ValueError(f"Duplicate package matrix entry: {name}")
        if not isinstance(host, str) or not host.strip():
            raise ValueError(f"Package matrix entry {name} is missing host")
        if strategy not in {"explicit", "codex_home_skill", "gemini_home_skill"}:
            raise ValueError(f"Package matrix entry {name} has invalid default_target_strategy: {strategy}")
        if not isinstance(required_paths, list) or not required_paths:
            raise ValueError(f"Package matrix entry {name} must define required_bundle_paths")
        normalized_paths: list[str] = []
        for raw_path in required_paths:
            if not isinstance(raw_path, str) or not raw_path.strip():
                raise ValueError(f"Package matrix entry {name} has invalid required bundle path: {raw_path!r}")
            path_text = Path(raw_path).as_posix()
            if Path(path_text).is_absolute():
                raise ValueError(f"Package matrix entry {name} has absolute required bundle path: {raw_path}")
            normalized_paths.append(path_text)
        matrix[name] = {
            "name": name,
            "host": host.strip(),
            "default_target_strategy": strategy,
            "host_global_template": item.get("host_global_template"),
            "required_bundle_paths": normalized_paths,
        }
    return matrix


def bundle_names() -> list[str]:
    return list(load_package_matrix())


def bundle_package_spec(bundle_name: str) -> dict:
    matrix = load_package_matrix()
    if bundle_name not in matrix:
        raise KeyError(f"Unknown bundle in package matrix: {bundle_name}")
    return matrix[bundle_name]


def bundle_required_path_texts(bundle_name: str) -> list[str]:
    return list(bundle_package_spec(bundle_name)["required_bundle_paths"])


def bundle_required_paths(bundle_name: str, root: Path) -> list[Path]:
    return [root / Path(path_text) for path_text in bundle_required_path_texts(bundle_name)]


def resolve_default_install_target(bundle_name: str, *, codex_home: Path, gemini_home: Path) -> Path | None:
    strategy = bundle_package_spec(bundle_name)["default_target_strategy"]
    if strategy == "explicit":
        return None
    if strategy == "codex_home_skill":
        return codex_home / "skills" / bundle_name
    if strategy == "gemini_home_skill":
        return gemini_home / "antigravity" / "skills" / bundle_name
    raise ValueError(f"Unsupported default target strategy for {bundle_name}: {strategy}")


def default_install_targets(*, codex_home: Path, gemini_home: Path) -> dict[str, Path]:
    targets: dict[str, Path] = {}
    for bundle_name in load_package_matrix():
        target = resolve_default_install_target(bundle_name, codex_home=codex_home, gemini_home=gemini_home)
        if target is not None:
            targets[bundle_name] = target.resolve()
    return targets
