from __future__ import annotations

import argparse
import json
from pathlib import Path

from design_board import build_design_board
from design_packet import load_brief, load_page_override, render_packet_html, write_packet
from design_state import append_render_event, default_packet_path, ensure_state_layout, resolve_state_paths


def _emit(payload: dict[str, object], output_format: str) -> int:
    if output_format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(payload)
    return 0 if payload.get("status") == "PASS" else 1


def render_brief(source: str, *, screen: str | None, output: str | None, state_root: str | None) -> dict[str, object]:
    brief, master_json = load_brief(Path(source))
    override_path, override_text = load_page_override(master_json, screen)
    paths = ensure_state_layout(resolve_state_paths(state_root))
    packet_path = Path(output).expanduser().resolve() if output else default_packet_path(
        paths,
        project_name=str(brief.get("project_name") or "workspace"),
        mode=str(brief.get("mode") or "visualize"),
        screen=screen or str(brief.get("screen") or "shared"),
    )
    html_text = render_packet_html(brief, page_override=override_text)
    write_packet(packet_path, html_text)
    append_render_event(
        paths,
        {
            "source": str(master_json),
            "output": str(packet_path),
            "project_name": brief.get("project_name"),
            "mode": brief.get("mode"),
            "screen": screen or brief.get("screen"),
            "page_override": str(override_path) if override_path and override_text else None,
        },
    )
    return {
        "status": "PASS",
        "source": str(master_json),
        "output_path": str(packet_path),
        "state": paths,
        "brief": {
            "project_name": brief.get("project_name"),
            "mode": brief.get("mode"),
            "screen": brief.get("screen"),
            "title": brief.get("title"),
        },
        "page_override": str(override_path) if override_path and override_text else None,
    }


def build_board(
    brief_dir: str,
    *,
    screen: str | None,
    evidence: list[str],
    evidence_dir: str | None,
    output: str | None,
    title: str | None,
    state_root: str | None,
) -> dict[str, object]:
    report = build_design_board(
        brief_dir=brief_dir,
        screen=screen,
        evidence=evidence,
        evidence_dir=evidence_dir,
        output=output,
        title=title,
    )
    paths = ensure_state_layout(resolve_state_paths(state_root))
    append_render_event(
        paths,
        {
            "source": str(Path(brief_dir).expanduser().resolve()),
            "output": report["output_path"],
            "mode": "board",
            "screen": screen,
            "asset_count": report["asset_count"],
        },
    )
    report["state"] = paths
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Forge design runtime tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    render_parser = subparsers.add_parser("render-brief", help="Render a persisted UI brief into an HTML design packet")
    render_parser.add_argument("source", help="Persisted UI brief directory or MASTER.json")
    render_parser.add_argument("--screen", help="Optional screen override to include")
    render_parser.add_argument("--output", help="Explicit HTML output path")
    render_parser.add_argument("--state-root", help="Override runtime-tool state root")
    render_parser.add_argument("--format", choices=["text", "json"], default="text")

    board_parser = subparsers.add_parser("board", help="Build an evidence-oriented design board from a persisted brief")
    board_parser.add_argument("--brief-dir", required=True, help="Persisted UI brief directory containing MASTER.md")
    board_parser.add_argument("--screen", help="Optional page override to include")
    board_parser.add_argument("--evidence", action="append", default=[], help="Explicit evidence asset path. Repeatable.")
    board_parser.add_argument("--evidence-dir", help="Directory to scan for image assets")
    board_parser.add_argument("--output", help="Explicit HTML output path")
    board_parser.add_argument("--title", help="Optional board title")
    board_parser.add_argument("--state-root", help="Override runtime-tool state root")
    board_parser.add_argument("--format", choices=["text", "json"], default="text")

    args = parser.parse_args(argv)
    try:
        if args.command == "render-brief":
            return _emit(
                render_brief(args.source, screen=args.screen, output=args.output, state_root=args.state_root),
                args.format,
            )
        if args.command == "board":
            return _emit(
                build_board(
                    args.brief_dir,
                    screen=args.screen,
                    evidence=args.evidence,
                    evidence_dir=args.evidence_dir,
                    output=args.output,
                    title=args.title,
                    state_root=args.state_root,
                ),
                args.format,
            )
    except Exception as exc:  # pragma: no cover - CLI guard
        return _emit({"status": "FAIL", "error": str(exc)}, args.format)
    return _emit({"status": "FAIL", "error": f"Unknown command: {args.command}"}, "text")


if __name__ == "__main__":
    raise SystemExit(main())
