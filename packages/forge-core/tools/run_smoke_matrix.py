from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

os.environ.pop("FORGE_HOME", None)
os.environ.pop("FORGE_BUNDLE_ROOT", None)
for key in tuple(os.environ):
    if key.startswith("PYTEST_"):
        os.environ.pop(key, None)

ROOT_DIR = Path(__file__).resolve().parents[1]
SHARED_DIR = ROOT_DIR / "shared"
CUSTOMIZE_SHARED_DIR = ROOT_DIR.parent / "forge-skills" / "customize" / "shared"
for import_dir in (CUSTOMIZE_SHARED_DIR, SHARED_DIR):
    if import_dir.is_dir() and str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))

from common import configure_stdio
from smoke_matrix_runtime import format_text, summarize
from smoke_matrix_suites import SUITE_RUNNERS


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Run Forge smoke matrices for current operator flows and router checks.")
    parser.add_argument(
        "--suite",
        choices=[*SUITE_RUNNERS.keys(), "all"],
        default="all",
        help="Smoke suite to run",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    selected_suites = SUITE_RUNNERS.keys() if args.suite == "all" else [args.suite]
    results: list[dict] = []
    for suite_name in selected_suites:
        results.extend(SUITE_RUNNERS[suite_name]())

    summary = summarize(results)
    payload = {"summary": summary, "results": results}
    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(format_text(summary, results))

    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
