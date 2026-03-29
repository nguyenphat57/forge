from __future__ import annotations

import argparse
import json
from pathlib import Path

from browse_packets import create_packet, list_packets as list_qa_packets, run_packet
from browse_support import (
    append_event,
    close_session,
    create_session,
    default_artifact_path,
    ensure_state_layout,
    get_session,
    list_sessions,
    resolve_state_paths,
    update_session,
    utc_now,
)
from playwright_cli import doctor, export_pdf, open_browser, record_actions, screenshot


def _emit(payload: dict[str, object], output_format: str) -> int:
    if output_format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(payload)
    return 0 if payload.get("status") == "PASS" else 1


def _runtime_payload(paths: dict[str, str], session: dict | None = None, *, result: dict | None = None) -> dict[str, object]:
    payload: dict[str, object] = {"status": "PASS", "state": paths}
    if session is not None:
        payload["session"] = session
    if result is not None:
        payload["runtime"] = result
        payload["status"] = str(result.get("status", "FAIL"))
    return payload


def _session_browser(session: dict, explicit_browser: str | None) -> str:
    return explicit_browser or str(session.get("browser") or "chromium")


def _record_event(paths: dict[str, str], name: str, *, session_id: str, url: str | None, artifact: str | None) -> None:
    append_event(
        paths,
        {
            "event": name,
            "at": utc_now(),
            "session_id": session_id,
            "url": url,
            "artifact": artifact,
        },
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Forge browser runtime tool")
    subparsers = parser.add_subparsers(dest="command", required=True)
    format_kwargs = {"choices": ["text", "json"], "default": "text", "help": "Output format"}

    doctor_parser = subparsers.add_parser("doctor", help="Check runtime prerequisites")
    doctor_parser.add_argument("--timeout-ms", type=int, default=15000)
    doctor_parser.add_argument("--format", **format_kwargs)

    create_parser = subparsers.add_parser("session-create", help="Create a persistent logical browsing session")
    create_parser.add_argument("--label", required=True)
    create_parser.add_argument("--browser", default="chromium")
    create_parser.add_argument("--lang")
    create_parser.add_argument("--device")
    create_parser.add_argument("--format", **format_kwargs)

    show_parser = subparsers.add_parser("session-show", help="Show one session")
    show_parser.add_argument("--session", required=True)
    show_parser.add_argument("--format", **format_kwargs)

    close_parser = subparsers.add_parser("session-close", help="Mark one session closed")
    close_parser.add_argument("--session", required=True)
    close_parser.add_argument("--format", **format_kwargs)

    list_parser = subparsers.add_parser("session-list", help="List known sessions")
    list_parser.add_argument("--format", **format_kwargs)

    snapshot_parser = subparsers.add_parser("snapshot", help="Capture a screenshot through Playwright CLI")
    snapshot_parser.add_argument("--session", required=True)
    snapshot_parser.add_argument("--url", required=True)
    snapshot_parser.add_argument("--output")
    snapshot_parser.add_argument("--browser")
    snapshot_parser.add_argument("--lang")
    snapshot_parser.add_argument("--device")
    snapshot_parser.add_argument("--har")
    snapshot_parser.add_argument("--full-page", action="store_true")
    snapshot_parser.add_argument("--wait-for-selector")
    snapshot_parser.add_argument("--wait-for-timeout", type=int)
    snapshot_parser.add_argument("--timeout-ms", type=int)
    snapshot_parser.add_argument("--format", **format_kwargs)

    pdf_parser = subparsers.add_parser("pdf", help="Export a PDF through Playwright CLI")
    pdf_parser.add_argument("--session", required=True)
    pdf_parser.add_argument("--url", required=True)
    pdf_parser.add_argument("--output")
    pdf_parser.add_argument("--browser")
    pdf_parser.add_argument("--lang")
    pdf_parser.add_argument("--device")
    pdf_parser.add_argument("--timeout-ms", type=int)
    pdf_parser.add_argument("--format", **format_kwargs)

    open_parser = subparsers.add_parser("open", help="Open an interactive browser with the saved session")
    open_parser.add_argument("--session", required=True)
    open_parser.add_argument("--url")
    open_parser.add_argument("--browser")
    open_parser.add_argument("--lang")
    open_parser.add_argument("--device")
    open_parser.add_argument("--timeout-ms", type=int)
    open_parser.add_argument("--format", **format_kwargs)

    record_parser = subparsers.add_parser("record", help="Launch Playwright codegen with the saved session")
    record_parser.add_argument("--session", required=True)
    record_parser.add_argument("--url")
    record_parser.add_argument("--output")
    record_parser.add_argument("--target", default="python")
    record_parser.add_argument("--browser")
    record_parser.add_argument("--lang")
    record_parser.add_argument("--device")
    record_parser.add_argument("--timeout-ms", type=int)
    record_parser.add_argument("--format", **format_kwargs)

    qa_create_parser = subparsers.add_parser("qa-create", help="Persist a reusable QA packet for a session")
    qa_create_parser.add_argument("--session", required=True)
    qa_create_parser.add_argument("--name", required=True)
    qa_create_parser.add_argument("--url", required=True)
    qa_create_parser.add_argument("--mode", choices=["html-smoke", "playwright-snapshot"], default="html-smoke")
    qa_create_parser.add_argument("--auth-required", action="store_true", help="Mark the packet as requiring an authenticated session")
    qa_create_parser.add_argument("--login-url", help="Optional login entrypoint for authenticated packets")
    qa_create_parser.add_argument(
        "--storage-state-required",
        dest="storage_state_required",
        action="store_true",
        help="Require a persisted storage state file before running the packet",
    )
    qa_create_parser.add_argument(
        "--no-storage-state-required",
        dest="storage_state_required",
        action="store_false",
        help="Allow the packet to run without a persisted storage state file",
    )
    qa_create_parser.set_defaults(storage_state_required=None)
    qa_create_parser.add_argument("--expect-text", action="append", default=[])
    qa_create_parser.add_argument("--note", action="append", default=[])
    qa_create_parser.add_argument("--wait-for-selector")
    qa_create_parser.add_argument("--wait-for-timeout", type=int)
    qa_create_parser.add_argument("--full-page", action="store_true")
    qa_create_parser.add_argument("--format", **format_kwargs)

    qa_list_parser = subparsers.add_parser("qa-list", help="List persisted QA packets for a session")
    qa_list_parser.add_argument("--session", required=True)
    qa_list_parser.add_argument("--format", **format_kwargs)

    qa_run_parser = subparsers.add_parser("qa-run", help="Run a persisted QA packet")
    qa_run_parser.add_argument("--session", required=True)
    qa_run_parser.add_argument("--name", required=True)
    qa_run_parser.add_argument("--format", **format_kwargs)

    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            return _emit(doctor(timeout_ms=args.timeout_ms), args.format)

        paths = ensure_state_layout(resolve_state_paths())
        if args.command == "session-create":
            session = create_session(paths, label=args.label, browser=args.browser, lang=args.lang, device=args.device)
            return _emit(_runtime_payload(paths, session), args.format)
        if args.command == "session-list":
            return _emit({"status": "PASS", "state": paths, "sessions": list_sessions(paths)}, args.format)
        if args.command == "session-show":
            return _emit(_runtime_payload(paths, get_session(paths, args.session)), args.format)
        if args.command == "session-close":
            return _emit(_runtime_payload(paths, close_session(paths, args.session)), args.format)
        if args.command == "qa-create":
            payload = create_packet(
                paths=paths,
                session_id=args.session,
                name=args.name,
                url=args.url,
                mode=args.mode,
                expected_text=args.expect_text,
                note=args.note,
                wait_for_selector=args.wait_for_selector,
                wait_for_timeout=args.wait_for_timeout,
                full_page=args.full_page,
                auth_required=args.auth_required,
                login_url=args.login_url,
                storage_state_required=args.storage_state_required,
            )
            return _emit({"status": "PASS", "state": paths, **payload}, args.format)
        if args.command == "qa-list":
            return _emit({"status": "PASS", "state": paths, "packets": list_qa_packets(paths=paths, session_id=args.session)}, args.format)
        if args.command == "qa-run":
            return _emit({"state": paths, **run_packet(paths=paths, session_id=args.session, name=args.name)}, args.format)

        session = get_session(paths, args.session)
        browser = _session_browser(session, getattr(args, "browser", None))
        lang = getattr(args, "lang", None) or session.get("lang")
        device = getattr(args, "device", None) or session.get("device")

        if args.command == "snapshot":
            output_path = Path(args.output).expanduser().resolve() if args.output else default_artifact_path(paths, args.session, "png")
            har_path = Path(args.har).expanduser().resolve() if args.har else None
            runtime = screenshot(
                session=session,
                url=args.url,
                output_path=output_path,
                browser=browser,
                lang=lang,
                device=device,
                full_page=args.full_page,
                wait_for_selector=args.wait_for_selector,
                wait_for_timeout=args.wait_for_timeout,
                save_har_path=har_path,
                timeout_ms=args.timeout_ms,
            )
        elif args.command == "pdf":
            output_path = Path(args.output).expanduser().resolve() if args.output else default_artifact_path(paths, args.session, "pdf")
            runtime = export_pdf(
                session=session,
                url=args.url,
                output_path=output_path,
                browser=browser,
                lang=lang,
                device=device,
                timeout_ms=args.timeout_ms,
            )
        elif args.command == "open":
            output_path = None
            runtime = open_browser(
                session=session,
                url=args.url,
                browser=browser,
                lang=lang,
                device=device,
                timeout_ms=args.timeout_ms,
            )
        else:
            output_path = Path(args.output).expanduser().resolve() if args.output else default_artifact_path(paths, args.session, "py")
            runtime = record_actions(
                session=session,
                url=args.url,
                output_path=output_path,
                target=args.target,
                browser=browser,
                lang=lang,
                device=device,
                timeout_ms=args.timeout_ms,
            )

        artifact = str(output_path) if "output_path" in runtime else None
        if runtime["status"] == "PASS":
            session = update_session(paths, args.session, last_url=getattr(args, "url", None), last_artifact=artifact)
        _record_event(paths, args.command, session_id=args.session, url=getattr(args, "url", None), artifact=artifact)
        return _emit(_runtime_payload(paths, session, result=runtime), args.format)
    except Exception as exc:  # pragma: no cover - CLI guard
        return _emit({"status": "FAIL", "error": str(exc)}, args.format)


if __name__ == "__main__":
    raise SystemExit(main())
