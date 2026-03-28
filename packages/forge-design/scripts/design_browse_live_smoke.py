from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT_DIR = Path(__file__).resolve().parent.parent
DESIGN_CLI_PATH = ROOT_DIR / "scripts" / "forge_design.py"
BROWSE_CLI_PATH = ROOT_DIR.parent / "forge-browse" / "scripts" / "forge_browse.py"


def _run(command: list[str], *, env: dict[str, str]) -> dict[str, object]:
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        env=env,
    )
    stdout = completed.stdout.strip()
    payload = None
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


def _write_brief(root: Path) -> Path:
    brief_dir = root / "visualize"
    pages_dir = brief_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    (brief_dir / "MASTER.json").write_text(
        json.dumps(
            {
                "mode": "visualize",
                "title": "Review Packet",
                "project_name": "Forge Design Smoke",
                "screen": "dashboard",
                "summary": "Exercise the render-and-capture path with a persisted brief.",
                "stack": "generic-web",
                "platform": "web",
                "objective": "Confirm forge-design packets can be captured by forge-browse.",
                "sections": ["screen map", "state matrix"],
                "deliverables": ["review packet", "browse capture"],
                "stack_focus": ["clear first fold"],
                "stack_watchouts": ["do not hide primary actions"],
                "platform_notes": ["support laptop viewport"],
                "anti_patterns": ["flat hierarchy"],
                "notes": ["Use this only as a smoke fixture."],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (pages_dir / "dashboard.md").write_text(
        "# Dashboard Override\n\n- Hero card must lead the hierarchy.\n- Review artifacts should be easy to capture.\n",
        encoding="utf-8",
    )
    return brief_dir


def run_live_smoke(*, browser: str, timeout_ms: int) -> dict[str, object]:
    if not BROWSE_CLI_PATH.exists():
        return {"status": "FAIL", "error": f"forge-browse CLI not found at {BROWSE_CLI_PATH}"}
    with TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        brief_dir = _write_brief(temp_root / "briefs")
        packet_path = (temp_root / "review-packet.html").resolve()
        capture_path = (temp_root / "review-packet.png").resolve()
        design_state_root = (temp_root / "design-state").resolve()
        browse_state_root = (temp_root / "browse-state").resolve()
        env = os.environ.copy()
        env["FORGE_DESIGN_STATE_ROOT"] = str(design_state_root)
        env["FORGE_BROWSE_STATE_ROOT"] = str(browse_state_root)
        steps = [
            _run(
                [
                    sys.executable,
                    str(DESIGN_CLI_PATH),
                    "render-brief",
                    str(brief_dir),
                    "--screen",
                    "dashboard",
                    "--output",
                    str(packet_path),
                    "--format",
                    "json",
                ],
                env=env,
            ),
            _run([sys.executable, str(BROWSE_CLI_PATH), "doctor", "--format", "json"], env=env),
            _run(
                [
                    sys.executable,
                    str(BROWSE_CLI_PATH),
                    "session-create",
                    "--label",
                    "design-browse-smoke",
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
            return {"status": "FAIL", "steps": steps, "error": "Design smoke could not resolve browse session id."}
        steps.append(
            _run(
                [
                    sys.executable,
                    str(BROWSE_CLI_PATH),
                    "snapshot",
                    "--session",
                    session_id,
                    "--url",
                    packet_path.as_uri(),
                    "--output",
                    str(capture_path),
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
        renders_path = design_state_root / "state" / "renders.jsonl"
        session_store = browse_state_root / "state" / "sessions.json"
        payload = {
            "status": "PASS"
            if all(step["status"] == "PASS" for step in steps)
            and packet_path.exists()
            and capture_path.exists()
            and renders_path.exists()
            and session_store.exists()
            else "FAIL",
            "steps": steps,
            "evidence": {
                "packet_path": str(packet_path),
                "packet_exists": packet_path.exists(),
                "capture_path": str(capture_path),
                "capture_exists": capture_path.exists(),
                "design_renders_path": str(renders_path),
                "design_renders_exists": renders_path.exists(),
                "browse_session_store": str(session_store),
                "browse_session_store_exists": session_store.exists(),
            },
        }
        if payload["status"] != "PASS" and not capture_path.exists():
            payload["error"] = "Design browse smoke did not produce a capture artifact."
        return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a live smoke from forge-design render output into forge-browse capture.")
    parser.add_argument("--browser", default="chromium", help="Browser for Playwright CLI")
    parser.add_argument("--timeout-ms", type=int, default=30000, help="Playwright timeout in milliseconds")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()
    return _format(run_live_smoke(browser=args.browser, timeout_ms=args.timeout_ms), args.format)


if __name__ == "__main__":
    raise SystemExit(main())
