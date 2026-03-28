from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def resolve_playwright_command() -> list[str]:
    for candidate in ("npx.cmd", "npx", "npx.exe"):
        resolved = shutil.which(candidate)
        if resolved:
            return [resolved, "playwright"]
    return ["npx", "playwright"]


def _run(command: list[str], *, timeout_ms: int = 60000) -> dict[str, object]:
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=timeout_ms / 1000,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
    }


def doctor(*, timeout_ms: int = 15000) -> dict[str, object]:
    playwright_command = resolve_playwright_command()
    node = _run(["node", "-v"], timeout_ms=timeout_ms)
    playwright = _run([*playwright_command, "--version"], timeout_ms=timeout_ms)
    return {
        "status": "PASS" if node["status"] == "PASS" and playwright["status"] == "PASS" else "FAIL",
        "checks": {
            "node": node,
            "playwright_cli": playwright,
        },
    }


def _context_args(
    *,
    browser: str,
    lang: str | None,
    device: str | None,
    timeout_ms: int | None,
) -> list[str]:
    args = [
        "-b",
        browser,
    ]
    if lang:
        args.extend(["--lang", lang])
    if device:
        args.extend(["--device", device])
    if timeout_ms is not None:
        args.extend(["--timeout", str(timeout_ms)])
    return args


def _storage_args(
    session: dict,
    *,
    save_storage: bool,
) -> list[str]:
    args: list[str] = []
    storage_state = Path(str(session["storage_state_path"]))
    if storage_state.exists():
        args.extend(["--load-storage", str(storage_state)])
    if save_storage:
        args.extend(["--save-storage", str(session["storage_state_path"])])
    return args


def _interactive_context_args(
    session: dict,
    *,
    browser: str,
    lang: str | None,
    device: str | None,
    timeout_ms: int | None,
) -> list[str]:
    args = _context_args(browser=browser, lang=lang, device=device, timeout_ms=timeout_ms)
    args.extend(["--user-data-dir", str(session["user_data_dir"])])
    args.extend(_storage_args(session, save_storage=True))
    return args


def screenshot(
    *,
    session: dict,
    url: str,
    output_path: Path,
    browser: str,
    lang: str | None,
    device: str | None,
    full_page: bool,
    wait_for_selector: str | None,
    wait_for_timeout: int | None,
    save_har_path: Path | None,
    timeout_ms: int | None,
) -> dict[str, object]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [*resolve_playwright_command(), "screenshot", url, str(output_path)]
    command.extend(_context_args(browser=browser, lang=lang, device=device, timeout_ms=timeout_ms))
    command.extend(_storage_args(session, save_storage=True))
    if full_page:
        command.append("--full-page")
    if wait_for_selector:
        command.extend(["--wait-for-selector", wait_for_selector])
    if wait_for_timeout is not None:
        command.extend(["--wait-for-timeout", str(wait_for_timeout)])
    if save_har_path is not None:
        save_har_path.parent.mkdir(parents=True, exist_ok=True)
        command.extend(["--save-har", str(save_har_path)])
    result = _run(command, timeout_ms=timeout_ms or 60000)
    result["output_path"] = str(output_path)
    result["har_path"] = str(save_har_path) if save_har_path is not None else None
    return result


def export_pdf(
    *,
    session: dict,
    url: str,
    output_path: Path,
    browser: str,
    lang: str | None,
    device: str | None,
    timeout_ms: int | None,
) -> dict[str, object]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [*resolve_playwright_command(), "pdf", url, str(output_path)]
    command.extend(_context_args(browser=browser, lang=lang, device=device, timeout_ms=timeout_ms))
    command.extend(_storage_args(session, save_storage=True))
    result = _run(command, timeout_ms=timeout_ms or 60000)
    result["output_path"] = str(output_path)
    return result


def open_browser(
    *,
    session: dict,
    url: str | None,
    browser: str,
    lang: str | None,
    device: str | None,
    timeout_ms: int | None,
) -> dict[str, object]:
    command = [*resolve_playwright_command(), "open"]
    command.extend(_interactive_context_args(session, browser=browser, lang=lang, device=device, timeout_ms=timeout_ms))
    if url:
        command.append(url)
    return _run(command, timeout_ms=timeout_ms or 60000)


def record_actions(
    *,
    session: dict,
    url: str | None,
    output_path: Path,
    target: str,
    browser: str,
    lang: str | None,
    device: str | None,
    timeout_ms: int | None,
) -> dict[str, object]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [*resolve_playwright_command(), "codegen", "-o", str(output_path), "--target", target]
    command.extend(_interactive_context_args(session, browser=browser, lang=lang, device=device, timeout_ms=timeout_ms))
    if url:
        command.append(url)
    result = _run(command, timeout_ms=timeout_ms or 60000)
    result["output_path"] = str(output_path)
    return result
