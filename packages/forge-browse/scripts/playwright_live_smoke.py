from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT_DIR = Path(__file__).resolve().parent.parent
CLI_PATH = ROOT_DIR / "scripts" / "forge_browse.py"


def _run(command: list[str], *, env: dict[str, str]) -> dict[str, object]:
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        env=env,
    )
    payload = None
    stdout = completed.stdout.strip()
    if stdout:
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            payload = None
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": stdout,
        "stderr": completed.stderr.strip(),
        "payload": payload,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
    }


def _format(payload: dict[str, object], output_format: str) -> int:
    if output_format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(payload)
    return 0 if payload["status"] == "PASS" else 1


def run_live_smoke(*, browser: str, timeout_ms: int) -> dict[str, object]:
    with TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        site_root = temp_root / "site"
        site_root.mkdir(parents=True, exist_ok=True)
        (site_root / "index.html").write_text(
            (
                "<html><head><title>Forge Browse Live Smoke</title></head>"
                "<body><main>Forge Browse Live Smoke</main></body></html>"
            ),
            encoding="utf-8",
        )
        state_root = (temp_root / "state").resolve()
        output_path = (temp_root / "smoke.png").resolve()
        page_url = (site_root / "index.html").resolve().as_uri()
        env = os.environ.copy()
        env["FORGE_BROWSE_STATE_ROOT"] = str(state_root)
        steps = [
            _run([sys.executable, str(CLI_PATH), "doctor", "--format", "json"], env=env),
            _run(
                [
                    sys.executable,
                    str(CLI_PATH),
                    "session-create",
                    "--label",
                    "live-smoke",
                    "--browser",
                    browser,
                    "--format",
                    "json",
                ],
                env=env,
            ),
        ]
        create_payload = steps[-1]["payload"] if isinstance(steps[-1].get("payload"), dict) else {}
        session = create_payload.get("session") if isinstance(create_payload, dict) else {}
        session_id = session.get("id") if isinstance(session, dict) else None
        if not isinstance(session_id, str) or not session_id.strip():
            return {
                "status": "FAIL",
                "steps": steps,
                "error": "Live smoke could not resolve session id from session-create output.",
            }

        steps.append(
            _run(
                [
                    sys.executable,
                    str(CLI_PATH),
                    "snapshot",
                    "--session",
                    session_id,
                    "--url",
                    page_url,
                    "--output",
                    str(output_path),
                    "--browser",
                    browser,
                    "--timeout-ms",
                    str(timeout_ms),
                    "--format",
                    "json",
                ],
                env=env,
            )
        )
        steps.append(
            _run(
                [
                    sys.executable,
                    str(CLI_PATH),
                    "session-show",
                    "--session",
                    session_id,
                    "--format",
                    "json",
                ],
                env=env,
            )
        )

        snapshot_ok = output_path.exists()
        session_store_ok = (state_root / "state" / "sessions.json").exists()
        storage_state_ok = any(state_root.rglob("storage-state.json"))
        payload = {
            "status": "PASS" if all(step["status"] == "PASS" for step in steps) and snapshot_ok and session_store_ok else "FAIL",
            "steps": steps,
            "evidence": {
                "state_root": str(state_root),
                "snapshot_path": str(output_path),
                "snapshot_exists": snapshot_ok,
                "session_store_exists": session_store_ok,
                "storage_state_exists": storage_state_ok,
            },
        }
        if payload["status"] != "PASS" and not snapshot_ok:
            payload["error"] = "Live smoke did not produce a screenshot artifact."
        return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a live Playwright smoke through the forge-browse CLI.")
    parser.add_argument("--browser", default="chromium", help="Browser for Playwright CLI")
    parser.add_argument("--timeout-ms", type=int, default=30000, help="Playwright timeout in milliseconds")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()
    return _format(run_live_smoke(browser=args.browser, timeout_ms=args.timeout_ms), args.format)


if __name__ == "__main__":
    raise SystemExit(main())
