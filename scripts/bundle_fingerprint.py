from __future__ import annotations

import hashlib
from pathlib import Path

from release_fs import run_with_retries


EXCLUDED_FILE_NAMES = {"BUILD-MANIFEST.json", "INSTALL-MANIFEST.json"}
EXCLUDED_DIR_NAMES = {"__pycache__"}
EXCLUDED_SUFFIXES = {".pyc"}
FINGERPRINT_MODE = "path-content-sha256-v1"
PATH_SET_FINGERPRINT_MODE = "path-set-content-sha256-v1"


def _iter_bundle_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
            continue
        if path.name in EXCLUDED_FILE_NAMES:
            continue
        if path.suffix in EXCLUDED_SUFFIXES:
            continue
        files.append(path)
    return files


def _read_bytes_with_retries(path: Path) -> bytes:
    payload: bytes | None = None

    def _read() -> None:
        nonlocal payload
        payload = path.read_bytes()

    run_with_retries(_read)
    if payload is None:
        raise FileNotFoundError(path)
    return payload


def _iter_path_set_files(paths: list[Path], *, relative_to: Path) -> list[tuple[str, Path]]:
    normalized_base = relative_to.resolve()
    files: dict[str, Path] = {}
    for root in sorted({path.resolve() for path in paths if path.exists()}, key=lambda item: item.as_posix()):
        candidates = [root] if root.is_file() else sorted(root.rglob("*"))
        for path in candidates:
            if path.is_dir():
                continue
            if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
                continue
            if path.name in EXCLUDED_FILE_NAMES:
                continue
            if path.suffix in EXCLUDED_SUFFIXES:
                continue
            try:
                relative = path.relative_to(normalized_base).as_posix()
            except ValueError:
                relative = path.as_posix()
            files[relative] = path
    return [(relative, files[relative]) for relative in sorted(files)]


def fingerprint_matches(expected: dict | None, actual: dict | None) -> bool:
    if not isinstance(expected, dict) or not isinstance(actual, dict):
        return False
    return (
        expected.get("mode") == actual.get("mode")
        and expected.get("sha256") == actual.get("sha256")
        and expected.get("file_count") == actual.get("file_count")
    )


def compute_bundle_fingerprint(root: Path) -> dict[str, object]:
    normalized_root = root.resolve()
    hasher = hashlib.sha256()
    file_count = 0
    for path in _iter_bundle_files(normalized_root):
        relative = path.relative_to(normalized_root).as_posix()
        hasher.update(relative.encode("utf-8"))
        hasher.update(b"\0")
        try:
            hasher.update(_read_bytes_with_retries(path))
        except FileNotFoundError:
            continue
        hasher.update(b"\0")
        file_count += 1
    return {
        "mode": FINGERPRINT_MODE,
        "sha256": hasher.hexdigest(),
        "file_count": file_count,
    }


def compute_path_fingerprint(paths: list[Path], *, relative_to: Path) -> dict[str, object]:
    hasher = hashlib.sha256()
    file_count = 0
    for relative, path in _iter_path_set_files(paths, relative_to=relative_to):
        hasher.update(relative.encode("utf-8"))
        hasher.update(b"\0")
        try:
            hasher.update(_read_bytes_with_retries(path))
        except FileNotFoundError:
            continue
        hasher.update(b"\0")
        file_count += 1
    return {
        "mode": PATH_SET_FINGERPRINT_MODE,
        "sha256": hasher.hexdigest(),
        "file_count": file_count,
    }


def bundle_fingerprint_matches_manifest(root: Path, manifest: dict) -> tuple[bool, dict[str, object], dict[str, object] | None]:
    expected = manifest.get("bundle_fingerprint")
    actual = compute_bundle_fingerprint(root)
    if not isinstance(expected, dict):
        return False, actual, None
    return (fingerprint_matches(expected, actual), actual, expected)
