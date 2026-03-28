from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from host_artifacts_support import ensure_generated_host_artifacts, format_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or verify host global artifact templates from canonical source.")
    parser.add_argument("--apply", action="store_true", help="Write generated artifacts to their target overlay paths")
    parser.add_argument("--write", action="store_true", help="Alias for --apply")
    parser.add_argument("--check", action="store_true", help="Fail when generated artifacts do not match the current files")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    apply_mode = args.apply or args.write
    report = ensure_generated_host_artifacts(check=not apply_mode)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_report(report))
    if args.check and report["stale_outputs"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
