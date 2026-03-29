from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import run_python_script


def _write_workspace_canary(workspace: Path, status: str, summary: str) -> None:
    canary_dir = workspace / ".forge-artifacts" / "workspace-canaries" / workspace.name
    canary_dir.mkdir(parents=True, exist_ok=True)
    payload = {"workspace": str(workspace), "workspace_name": workspace.name, "status": status, "summary": summary}
    (canary_dir / "latest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_canary_run(path: Path, workspace_name: str, status: str, observed_at: str) -> None:
    workspace_dir = path / workspace_name
    workspace_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "workspace": workspace_name,
        "status": status,
        "observed_at": observed_at,
        "summary": f"{workspace_name} {status}",
    }
    (workspace_dir / f"{observed_at[:10]}-{workspace_name}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_review_pack(workspace: Path, status: str, summary: str) -> None:
    review_dir = workspace / ".forge-artifacts" / "review-packs"
    review_dir.mkdir(parents=True, exist_ok=True)
    payload = {"workspace": str(workspace), "status": status, "summary": summary}
    (review_dir / "latest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _record_gate_prerequisites(workspace: Path, project_name: str, scope: str = "Release slice") -> None:
    execution = run_python_script(
        "track_execution_progress.py",
        scope,
        "--mode",
        "checkpoint-batch",
        "--stage",
        "release-checks",
        "--status",
        "completed",
        "--completion-state",
        "ready-for-merge",
        "--project-name",
        project_name,
        "--harness-available",
        "no",
        "--proof",
        "release verification packet",
        "--persist",
        "--output-dir",
        str(workspace),
        "--format",
        "json",
        cwd=workspace,
    )
    if execution.returncode != 0:
        raise AssertionError(execution.stderr or execution.stdout)

    review = run_python_script(
        "record_review_state.py",
        "--workspace",
        str(workspace),
        "--project-name",
        project_name,
        "--scope",
        scope,
        "--disposition",
        "ready-for-merge",
        "--branch-state",
        "clean baseline confirmed",
        "--evidence",
        "release verification packet",
        "--no-finding-rationale",
        "Fresh review found no blocking issues.",
        "--persist",
        "--output-dir",
        str(workspace),
        "--format",
        "json",
    )
    if review.returncode != 0:
        raise AssertionError(review.stderr or review.stdout)


class ReleaseReadinessTests(unittest.TestCase):
    def test_release_readiness_passes_for_clean_standard_slice(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "checkout-web"
            workspace.mkdir(parents=True, exist_ok=True)
            _record_gate_prerequisites(workspace, "checkout-web")

            gate = run_python_script(
                "record_quality_gate.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "checkout-web",
                "--profile",
                "standard",
                "--target-claim",
                "deploy",
                "--decision",
                "go",
                "--evidence",
                "lint",
                "--response",
                "Current release evidence is fresh.",
                "--why",
                "Lint, tests, and build are current.",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(gate.returncode, 0, gate.stderr)

            docs = run_python_script(
                "release_doc_sync.py",
                "--workspace",
                str(workspace),
                "--changed-path",
                "app/page.tsx",
                "--changed-path",
                "README.md",
                "--persist",
                "--format",
                "json",
            )
            self.assertEqual(docs.returncode, 0, docs.stderr)

            _write_workspace_canary(workspace, "pass", "Workspace canary clean.")
            _write_review_pack(workspace, "PASS", "Review pack clean.")
            canary_root = workspace / ".forge-artifacts" / "canary-runs"
            _write_canary_run(canary_root, "checkout-web", "pass", "2026-03-28T10:00:00")
            _write_canary_run(canary_root, "admin-console", "pass", "2026-03-28T11:00:00")

            result = run_python_script(
                "release_readiness.py",
                "--workspace",
                str(workspace),
                "--profile",
                "standard",
                "--persist",
                "--format",
                "json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "PASS")
            self.assertTrue((workspace / ".forge-artifacts" / "release-readiness" / "latest.json").exists())

    def test_release_readiness_fails_for_production_when_docs_sync_warns(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "checkout-web"
            workspace.mkdir(parents=True, exist_ok=True)
            _record_gate_prerequisites(workspace, "checkout-web")

            gate = run_python_script(
                "record_quality_gate.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "checkout-web",
                "--profile",
                "release-critical",
                "--target-claim",
                "deploy",
                "--decision",
                "go",
                "--evidence",
                "build",
                "--response",
                "Release evidence is fresh.",
                "--why",
                "Gate is green for deploy.",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(gate.returncode, 0, gate.stderr)

            docs = run_python_script(
                "release_doc_sync.py",
                "--workspace",
                str(workspace),
                "--changed-path",
                "prisma/schema.prisma",
                "--persist",
                "--format",
                "json",
            )
            self.assertEqual(docs.returncode, 1, docs.stderr)

            _write_workspace_canary(workspace, "pass", "Workspace canary clean.")
            _write_review_pack(workspace, "WARN", "Review pack found auth follow-up.")
            canary_root = workspace / ".forge-artifacts" / "canary-runs"
            for workspace_name, day in (("checkout-web", "2026-03-27"), ("admin-console", "2026-03-27"), ("ops-console", "2026-03-27"), ("checkout-web", "2026-03-28"), ("admin-console", "2026-03-28"), ("ops-console", "2026-03-28")):
                _write_canary_run(canary_root, workspace_name, "pass", f"{day}T10:00:00")

            result = run_python_script(
                "release_readiness.py",
                "--workspace",
                str(workspace),
                "--profile",
                "production",
                "--format",
                "json",
            )

            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "FAIL")
            self.assertTrue(any(item["id"] == "release-doc-sync" and item["status"] == "FAIL" for item in report["checks"]))

    def test_release_readiness_auto_uses_auth_profile_and_requires_review_pack(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "auth-web"
            workspace.mkdir(parents=True, exist_ok=True)
            (workspace / "package.json").write_text(
                json.dumps(
                    {
                        "name": "auth-web",
                        "dependencies": {"next": "15.0.0", "@prisma/client": "6.0.0", "bcryptjs": "2.4.3"},
                        "devDependencies": {"typescript": "5.0.0", "prisma": "6.0.0"},
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            (workspace / "tsconfig.json").write_text("{}", encoding="utf-8")
            (workspace / "app" / "(auth)" / "login").mkdir(parents=True)
            (workspace / "app" / "(auth)" / "login" / "page.tsx").write_text("export default function Page() { return null; }\n", encoding="utf-8")
            (workspace / "lib" / "auth").mkdir(parents=True)
            (workspace / "lib" / "auth" / "password.ts").write_text("export const hash = async () => '';\n", encoding="utf-8")
            (workspace / "prisma").mkdir()
            (workspace / "prisma" / "schema.prisma").write_text("generator client { provider = \"prisma-client-js\" }\n", encoding="utf-8")
            _record_gate_prerequisites(workspace, "auth-web")

            gate = run_python_script(
                "record_quality_gate.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "auth-web",
                "--profile",
                "standard",
                "--target-claim",
                "deploy",
                "--decision",
                "go",
                "--evidence",
                "test",
                "--response",
                "Gate is green.",
                "--why",
                "Checks passed.",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(gate.returncode, 0, gate.stderr)
            _write_workspace_canary(workspace, "pass", "Workspace canary clean.")

            result = run_python_script("release_readiness.py", "--workspace", str(workspace), "--profile", "auto", "--format", "json")

            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["effective_profile"], "auth")
            self.assertIn("review-pack", report["missing_evidence"])

    def test_release_readiness_auto_uses_billing_profile_from_generic_repo_markers(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "billing-worker"
            workspace.mkdir(parents=True, exist_ok=True)
            (workspace / "package.json").write_text(
                json.dumps(
                    {
                        "name": "billing-worker",
                        "dependencies": {"stripe": "17.0.0"},
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            (workspace / "src" / "billing").mkdir(parents=True)
            (workspace / "src" / "billing" / "stripe.ts").write_text("export const stripe = {};\n", encoding="utf-8")
            _record_gate_prerequisites(workspace, "billing-worker")

            gate = run_python_script(
                "record_quality_gate.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "billing-worker",
                "--profile",
                "standard",
                "--target-claim",
                "deploy",
                "--decision",
                "go",
                "--evidence",
                "test",
                "--response",
                "Gate is green.",
                "--why",
                "Checks passed.",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(gate.returncode, 0, gate.stderr)

            docs = run_python_script(
                "release_doc_sync.py",
                "--workspace",
                str(workspace),
                "--changed-path",
                "src/billing/stripe.ts",
                "--changed-path",
                "docs/release/notes.md",
                "--changed-path",
                "docs/architecture/billing.md",
                "--changed-path",
                "docs/plans/billing.md",
                "--format",
                "json",
            )
            self.assertEqual(docs.returncode, 0, docs.stderr)
            _write_workspace_canary(workspace, "pass", "Workspace canary clean.")
            canary_root = workspace / ".forge-artifacts" / "canary-runs"
            for workspace_name, day in (("billing-worker", "2026-03-27"), ("ops-console", "2026-03-27"), ("checkout-web", "2026-03-28"), ("billing-worker", "2026-03-28"), ("ops-console", "2026-03-28"), ("checkout-web", "2026-03-27")):
                _write_canary_run(canary_root, workspace_name, "pass", f"{day}T10:00:00")

            result = run_python_script("release_readiness.py", "--workspace", str(workspace), "--profile", "auto", "--format", "json")

            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["effective_profile"], "billing")
            self.assertIn("review-pack", report["missing_evidence"])


if __name__ == "__main__":
    unittest.main()
