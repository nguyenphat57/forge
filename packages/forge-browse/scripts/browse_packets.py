from __future__ import annotations

import json
from pathlib import Path

import browse_runtime
import browse_session_runtime
from browse_support import append_event, default_artifact_path, get_session, update_session, utc_now
from playwright_cli import screenshot


def _slug(value: str) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "-" for char in value)
    parts = [part for part in normalized.split("-") if part]
    return "-".join(parts) or "qa-packet"


def _packet_dir(session: dict) -> Path:
    return Path(str(session["artifacts_dir"])) / "qa-packets"


def _packet_path(session: dict, name: str) -> Path:
    return _packet_dir(session) / f"{_slug(name)}.json"


def _run_dir(session: dict) -> Path:
    return Path(str(session["artifacts_dir"])) / "qa-runs"


def _auth_metadata(
    *,
    auth_required: bool,
    login_url: str | None,
    storage_state_required: bool | None,
) -> dict[str, object] | None:
    if not auth_required and login_url is None and storage_state_required is None:
        return None
    return {
        "required": auth_required,
        "login_url": login_url,
        "storage_state_required": auth_required if storage_state_required is None else storage_state_required,
    }


def _preflight_checks(session: dict, packet: dict) -> list[dict[str, object]]:
    auth = packet.get("auth")
    if not isinstance(auth, dict):
        return []
    checks: list[dict[str, object]] = [
        {
            "id": "auth-request",
            "status": "PASS" if auth.get("required") else "WARN",
            "detail": "Authenticated flow requested." if auth.get("required") else "Auth metadata is present but optional.",
        }
    ]
    login_url = auth.get("login_url")
    if auth.get("required"):
        if isinstance(login_url, str) and login_url.strip():
            checks.append({"id": "login-url", "status": "PASS", "detail": f"Login flow starts at {login_url}."})
        else:
            checks.append({"id": "login-url", "status": "FAIL", "detail": "Authenticated packet is missing a login_url."})
        if auth.get("storage_state_required", True):
            state_value = session.get("storage_state_path")
            if isinstance(state_value, str) and state_value.strip():
                state_path = Path(state_value)
                if state_path.exists():
                    checks.append({"id": "storage-state", "status": "PASS", "detail": f"Storage state found at {state_path}."})
                else:
                    checks.append({"id": "storage-state", "status": "FAIL", "detail": f"Storage state file is missing: {state_path}."})
            else:
                checks.append({"id": "storage-state", "status": "FAIL", "detail": "Session is missing storage_state_path."})
    return checks


def _packet_status(checks: list[dict[str, object]]) -> str:
    if any(item["status"] == "FAIL" for item in checks):
        return "FAIL"
    if any(item["status"] == "WARN" for item in checks):
        return "WARN"
    return "PASS"


def create_packet(
    *,
    paths: dict[str, str],
    session_id: str,
    name: str,
    url: str,
    mode: str,
    expected_text: list[str],
    note: list[str],
    wait_for_selector: str | None,
    wait_for_timeout: int | None,
    full_page: bool,
    auth_required: bool = False,
    login_url: str | None = None,
    storage_state_required: bool | None = None,
) -> dict[str, object]:
    session = get_session(paths, session_id)
    packet = {
        "name": name,
        "slug": _slug(name),
        "session_id": session_id,
        "url": url,
        "mode": mode,
        "expected_text": expected_text,
        "notes": note,
        "wait_for_selector": wait_for_selector,
        "wait_for_timeout": wait_for_timeout,
        "full_page": full_page,
        "created_at": utc_now(),
    }
    auth = _auth_metadata(
        auth_required=auth_required,
        login_url=login_url,
        storage_state_required=storage_state_required,
    )
    if auth is not None:
        packet["auth"] = auth
    path = _packet_path(session, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    append_event(paths, {"event": "qa-create", "at": utc_now(), "session_id": session_id, "packet": packet["slug"], "url": url})
    return {"status": "PASS", "packet": packet, "path": str(path.resolve())}


def create_authenticated_packet(
    *,
    paths: dict[str, str],
    session_id: str,
    name: str,
    url: str,
    login_url: str,
    expected_text: list[str],
    note: list[str],
    wait_for_selector: str | None,
    wait_for_timeout: int | None,
    full_page: bool,
    storage_state_required: bool = True,
) -> dict[str, object]:
    return create_packet(
        paths=paths,
        session_id=session_id,
        name=name,
        url=url,
        mode="html-smoke",
        expected_text=expected_text,
        note=note,
        wait_for_selector=wait_for_selector,
        wait_for_timeout=wait_for_timeout,
        full_page=full_page,
        auth_required=True,
        login_url=login_url,
        storage_state_required=storage_state_required,
    )


def list_packets(*, paths: dict[str, str], session_id: str) -> list[dict]:
    session = get_session(paths, session_id)
    packet_dir = _packet_dir(session)
    packets: list[dict] = []
    if not packet_dir.exists():
        return packets
    for path in sorted(packet_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload["path"] = str(path.resolve())
            packets.append(payload)
    return packets


def _load_packet(paths: dict[str, str], session_id: str, name: str) -> tuple[dict, dict, Path]:
    session = get_session(paths, session_id)
    path = _packet_path(session, name)
    if not path.exists():
        raise ValueError(f"Unknown QA packet for session {session_id}: {name}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid QA packet: {path}")
    return session, payload, path


def run_packet(*, paths: dict[str, str], session_id: str, name: str) -> dict[str, object]:
    session, packet, packet_path = _load_packet(paths, session_id, name)
    preflight = _preflight_checks(session, packet)
    preflight_status = _packet_status(preflight)
    if preflight_status == "FAIL":
        report = {
            "status": "FAIL",
            "session_id": session_id,
            "packet": packet,
            "packet_path": str(packet_path.resolve()),
            "preflight": preflight,
            "runtime": None,
            "assertions": [],
            "artifact_path": None,
            "recorded_at": utc_now(),
        }
        run_dir = _run_dir(session)
        run_dir.mkdir(parents=True, exist_ok=True)
        report_path = run_dir / f"{packet['slug']}-{report['recorded_at'].replace(':', '').replace('-', '')}.json"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        append_event(
            paths,
            {
                "event": "qa-run",
                "at": report["recorded_at"],
                "session_id": session_id,
                "packet": packet["slug"],
                "artifact": None,
                "status": report["status"],
            },
        )
        report["report_path"] = str(report_path.resolve())
        return report
    runtime: dict[str, object]
    assertions: list[dict[str, object]] = []
    artifact_path: str | None = None
    auth = packet.get("auth") if isinstance(packet.get("auth"), dict) else None
    if packet["mode"] == "playwright-snapshot":
        output_path = default_artifact_path(paths, session_id, "png")
        runtime = screenshot(
            session=session,
            url=str(packet["url"]),
            output_path=output_path,
            browser=str(session.get("browser") or "chromium"),
            lang=session.get("lang"),
            device=session.get("device"),
            full_page=bool(packet.get("full_page")),
            wait_for_selector=packet.get("wait_for_selector"),
            wait_for_timeout=packet.get("wait_for_timeout"),
            save_har_path=None,
            timeout_ms=None,
        )
        artifact_path = str(output_path)
    elif auth and auth.get("required"):
        runtime = browse_session_runtime.open_authenticated_url(
            state_root=paths["root"],
            session_id=session_id,
            url=str(packet["url"]),
            storage_state_path=str(session["storage_state_path"]),
        )
        if runtime["status"] == "PASS":
            artifact_path = str(runtime["tab"]["snapshot_path"])
    else:
        runtime = browse_runtime.open_url(state_root=paths["root"], session_id=session_id, url=str(packet["url"]))
        artifact_path = str(runtime["tab"]["snapshot_path"])
    if runtime["status"] == "PASS":
        for expected in packet.get("expected_text", []):
            assertion = browse_runtime.assert_text_contains(
                state_root=paths["root"],
                session_id=session_id,
                expected_text=str(expected),
            )
            assertions.append(
                {
                    "expected_text": expected,
                    "status": assertion["status"],
                    "matched": assertion["matched"],
                }
            )
    if artifact_path:
        update_session(paths, session_id, last_url=str(packet["url"]), last_artifact=artifact_path)
    passed = preflight_status != "FAIL" and runtime["status"] == "PASS" and all(item["status"] == "PASS" for item in assertions)
    report = {
        "status": "PASS" if passed else "FAIL",
        "session_id": session_id,
        "packet": packet,
        "packet_path": str(packet_path.resolve()),
        "preflight": preflight,
        "runtime": runtime,
        "assertions": assertions,
        "artifact_path": artifact_path,
        "recorded_at": utc_now(),
    }
    run_dir = _run_dir(session)
    run_dir.mkdir(parents=True, exist_ok=True)
    report_path = run_dir / f"{packet['slug']}-{report['recorded_at'].replace(':', '').replace('-', '')}.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    append_event(
        paths,
        {
            "event": "qa-run",
            "at": report["recorded_at"],
            "session_id": session_id,
            "packet": packet["slug"],
            "artifact": artifact_path,
            "status": report["status"],
        },
    )
    report["report_path"] = str(report_path.resolve())
    return report
