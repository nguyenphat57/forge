from __future__ import annotations

import argparse
import json

from runtime_tool_support import available_runtime_tool_names, resolve_runtime_tool


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve a registered Forge runtime tool for the current bundle.")
    parser.add_argument("bundle", choices=available_runtime_tool_names(), help="Runtime tool bundle name")
    parser.add_argument("--tool-target", help="Override runtime tool root path")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    payload = resolve_runtime_tool(args.bundle, explicit_target=args.tool_target)
    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(payload)
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
