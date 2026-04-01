from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
IGNORED_DIRS = {".git", ".install-backups", ".pytest_cache", "__pycache__", "dist"}
IGNORED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".pdf",
    ".zip",
    ".gz",
    ".whl",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".pyc",
}
SECRET_PATTERNS = [
    ("private-key", "-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
    ("openai-key", r"\bsk-[A-Za-z0-9]{20,}\b"),
    ("github-token", r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    ("aws-access-key", r"\bAKIA[0-9A-Z]{16}\b"),
    ("google-api-key", r"\bAIza[0-9A-Za-z_-]{35}\b"),
    ("slack-token", r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b"),
]
COMPILED_SECRET_PATTERNS = [(name, re.compile(pattern)) for name, pattern in SECRET_PATTERNS]


def tracked_files(root: Path) -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=str(root),
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return sorted(path for path in root.rglob("*") if path.is_file())
    entries = [item for item in completed.stdout.decode("utf-8", errors="ignore").split("\0") if item]
    return [root / entry for entry in entries]


def should_scan(path: Path) -> bool:
    if any(part in IGNORED_DIRS for part in path.parts):
        return False
    return path.suffix.lower() not in IGNORED_EXTENSIONS


def find_matches(path: Path) -> list[dict[str, object]]:
    if not should_scan(path):
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    findings: list[dict[str, object]] = []
    for name, regex in COMPILED_SECRET_PATTERNS:
        for match in regex.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(
                {
                    "type": name,
                    "path": str(path),
                    "line": line,
                }
            )
    return findings


def scan_repo(root: Path) -> dict[str, object]:
    findings: list[dict[str, object]] = []
    for path in tracked_files(root):
        findings.extend(find_matches(path.resolve()))
    findings.sort(key=lambda item: (item["path"], item["line"], item["type"]))
    return {
        "status": "FAIL" if findings else "PASS",
        "root": str(root.resolve()),
        "findings": findings,
    }


def format_text(report: dict[str, object]) -> str:
    lines = ["Forge Secret Scan", f"- Status: {report['status']}", f"- Root: {report['root']}"]
    findings = report["findings"]
    if findings:
        lines.append("- Findings:")
        for item in findings:
            lines.append(f"  - [{item['type']}] {item['path']}:{item['line']}")
    else:
        lines.append("- Findings: none")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a high-signal secret scan over the Forge repo.")
    parser.add_argument("--root", type=Path, default=ROOT_DIR, help="Repo root to scan")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    report = scan_repo(args.root.resolve())
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
