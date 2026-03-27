from __future__ import annotations

import argparse
import json

from common import configure_stdio
from smoke_matrix_runtime import format_text, summarize
from smoke_matrix_suites import SUITE_RUNNERS


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Run Forge smoke matrices for route preview and router checks.")
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
