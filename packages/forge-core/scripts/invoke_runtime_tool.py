from __future__ import annotations

import argparse
import json
import subprocess
import sys

from runtime_tool_support import available_runtime_tool_names, resolve_runtime_tool


def main() -> int:
    parser = argparse.ArgumentParser(description="Invoke a registered Forge runtime tool through the current bundle.")
    parser.add_argument("bundle", choices=available_runtime_tool_names(), help="Runtime tool bundle name")
    parser.add_argument("--tool-target", help="Override runtime tool root path")
    parser.add_argument("tool_args", nargs=argparse.REMAINDER, help="Arguments forwarded to the runtime tool")
    args = parser.parse_args()

    tool_args = list(args.tool_args)
    if tool_args[:1] == ["--"]:
        tool_args = tool_args[1:]

    payload = resolve_runtime_tool(args.bundle, explicit_target=args.tool_target)
    if payload["status"] != "PASS":
        print(json.dumps(payload, indent=2, ensure_ascii=False), file=sys.stderr)
        return 1

    completed = subprocess.run([sys.executable, str(payload["script_path"]), *tool_args], check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
