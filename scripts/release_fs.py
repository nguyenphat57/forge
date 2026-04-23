from __future__ import annotations

import shutil
import stat
import time
from pathlib import Path
from typing import Callable


IGNORE_NAMES = frozenset({".forge-artifacts", "__pycache__", ".pytest_cache"})
IGNORE_SUFFIXES = frozenset({".pyc"})
IGNORE_PATTERNS = shutil.ignore_patterns(".forge-artifacts", ".worktrees", "__pycache__", ".pytest_cache", "*.pyc")
RETRYABLE_ERRNOS = {13, 16, 39}
RETRYABLE_WINERRORS = {5, 32, 145}
DEFAULT_ATTEMPTS = 8
DEFAULT_DELAY_SECONDS = 0.2


def should_ignore_relative_path(path: Path) -> bool:
    if any(part in IGNORE_NAMES for part in path.parts):
        return True
    return path.suffix.lower() in IGNORE_SUFFIXES


def _is_retryable_error(exc: Exception) -> bool:
    if isinstance(exc, shutil.Error):
        return True
    if not isinstance(exc, OSError):
        return False
    if exc.errno in RETRYABLE_ERRNOS:
        return True
    return getattr(exc, "winerror", None) in RETRYABLE_WINERRORS


def _clear_readonly(path: str | Path) -> None:
    try:
        Path(path).chmod(stat.S_IWRITE | stat.S_IREAD)
    except OSError:
        return


def _on_rmtree_error(func: Callable[[str], None], path: str, excinfo: tuple[type[BaseException], BaseException, object]) -> None:
    _clear_readonly(path)
    try:
        func(path)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise exc


def run_with_retries(
    action: Callable[[], None],
    *,
    attempts: int = DEFAULT_ATTEMPTS,
    delay_seconds: float = DEFAULT_DELAY_SECONDS,
) -> None:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            action()
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt == attempts - 1 or not _is_retryable_error(exc):
                raise
            time.sleep(delay_seconds * (attempt + 1))
    if last_error is not None:
        raise last_error


def remove_tree(path: Path) -> None:
    if not path.exists():
        return
    run_with_retries(lambda: shutil.rmtree(path, onexc=_on_rmtree_error))
    if path.exists():
        raise OSError(f"Failed to remove directory cleanly: {path}")


def remove_file(path: Path) -> None:
    if not path.exists():
        return

    def _unlink() -> None:
        _clear_readonly(path)
        try:
            path.unlink()
        except FileNotFoundError:
            return

    run_with_retries(_unlink)


def remove_path(path: Path) -> None:
    if path.is_dir():
        remove_tree(path)
        return
    remove_file(path)


def copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    run_with_retries(lambda: shutil.copy2(source, destination))


def copy_tree(
    source: Path,
    destination: Path,
    *,
    dirs_exist_ok: bool = False,
    ignore: Callable[[str, list[str]], set[str] | list[str]] | None = None,
) -> None:
    run_with_retries(
        lambda: shutil.copytree(
            source,
            destination,
            dirs_exist_ok=dirs_exist_ok,
            ignore=ignore,
        )
    )


def _prune_extra_entries(source: Path, target: Path, relative_root: Path = Path()) -> None:
    if not target.exists() or not target.is_dir():
        return

    source_names = {
        item.name
        for item in source.iterdir()
        if not should_ignore_relative_path(relative_root / item.name)
    }
    for child in list(target.iterdir()):
        child_relative = relative_root / child.name
        if should_ignore_relative_path(child_relative):
            remove_path(child)
            continue
        if child.name in source_names:
            source_child = source / child.name
            if child.is_dir() and source_child.is_dir():
                _prune_extra_entries(source_child, child, child_relative)
            continue
        remove_path(child)


def sync_tree(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    _prune_extra_entries(source, target)
    copy_tree(source, target, dirs_exist_ok=True, ignore=IGNORE_PATTERNS)
