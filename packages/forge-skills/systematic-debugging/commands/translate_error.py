from __future__ import annotations

from _forge_skill_command import bootstrap_command_paths

bootstrap_command_paths()

import argparse
import json
from pathlib import Path

from common import configure_stdio, translate_error_text


def load_error_text(args: argparse.Namespace) -> str:
    if args.input_file is not None:
        path = args.input_file.resolve()
        if not path.exists():
            raise FileNotFoundError(f"Error input file does not exist: {path}")
        return path.read_text(encoding="utf-8")

    if args.error_text is not None:
        return args.error_text

    raise ValueError("Provide --error-text or --input-file.")


def build_payload(args: argparse.Namespace) -> dict:
    error_text = load_error_text(args)
    translation = translate_error_text(error_text, include_empty_fallback=args.include_empty_fallback)
    if translation is None:
        raise ValueError("No error text to translate after sanitization.")

    payload = {
        "status": translation["status"],
        "translation": translation,
    }
    return payload


def format_text(payload: dict) -> str:
    translation = payload["translation"]
    lines = [
        "Forge Error Translation",
        f"- Status: {payload['status']}",
        f"- Category: {translation['category']}",
        f"- Meaning: {translation['human_message']}",
        f"- Suggested action: {translation['suggested_action']}",
    ]
    if translation["error_excerpt"]:
        lines.append(f"- Error excerpt: {translation['error_excerpt']}")
    else:
        lines.append("- Error excerpt: (none)")
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Translate a raw technical error into a host-neutral human summary.")
    parser.add_argument("--error-text", help="Raw error text to translate")
    parser.add_argument("--input-file", type=Path, help="Read raw error text from a file")
    parser.add_argument(
        "--include-empty-fallback",
        action="store_true",
        help="Return a generic translation even when the sanitized input is empty",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    try:
        payload = build_payload(args)
    except (FileNotFoundError, ValueError) as exc:
        if args.format == "json":
            print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2, ensure_ascii=False))
        else:
            print("\n".join(["Forge Error Translation", "- Status: FAIL", f"- Error: {exc}"]))
        return 1

    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(format_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
