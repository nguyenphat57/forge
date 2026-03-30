from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import reference_companion_environment, run_python_script


class DashboardTests(unittest.TestCase):
    def test_dashboard_reflects_active_review_ready_workspace(self) -> None:
        with TemporaryDirectory() as temp_dir, reference_companion_environment() as (_, companion_env):
            workspace = Path(temp_dir) / "workspace"
            workspace.mkdir(parents=True, exist_ok=True)
            (workspace / "README.md").write_text("# Demo\n", encoding="utf-8")
            (workspace / "package.json").write_text(
                json.dumps(
                    {
                        "name": "demo-app",
                        "dependencies": {"next": "15.0.0", "@prisma/client": "6.0.0"},
                        "devDependencies": {"typescript": "5.0.0", "prisma": "6.0.0"},
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            (workspace / "tsconfig.json").write_text("{}", encoding="utf-8")
            (workspace / "next.config.ts").write_text("export default {};\n", encoding="utf-8")
            (workspace / "prisma").mkdir()
            (workspace / "prisma" / "schema.prisma").write_text("generator client { provider = \"prisma-client-js\" }\n", encoding="utf-8")
            (workspace / ".brain").mkdir()
            (workspace / ".brain" / "session.json").write_text(
                json.dumps(
                    {
                        "working_on": {"feature": "Checkout", "task": "Close review slice", "status": "active", "files": []},
                        "pending_tasks": ["Re-run final review"],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            (workspace / ".brain" / "decisions.json").write_text(json.dumps([{"id": "d1"}]), encoding="utf-8")
            (workspace / ".brain" / "learnings.json").write_text(json.dumps([{"id": "l1"}]), encoding="utf-8")
            (workspace / "docs" / "plans").mkdir(parents=True)
            (workspace / "docs" / "plans" / "checkout.md").write_text("# Plan: Checkout\n", encoding="utf-8")
            (workspace / ".forge-artifacts" / "codebase").mkdir(parents=True)
            (workspace / ".forge-artifacts" / "codebase" / "summary.md").write_text("# Codebase Summary\n", encoding="utf-8")

            started = run_python_script(
                "change_artifacts.py",
                "start",
                "Checkout review slice",
                "--workspace",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(started.returncode, 0, started.stderr)

            gate = run_python_script(
                "record_quality_gate.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "demo",
                "--profile",
                "standard",
                "--target-claim",
                "ready-for-review",
                "--decision",
                "go",
                "--evidence",
                "pytest tests/test_checkout.py",
                "--response",
                "Fresh evidence is sufficient for review.",
                "--why",
                "Focused verification passed for the active slice.",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(gate.returncode, 0, gate.stderr)

            docs_sync = run_python_script(
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
            self.assertEqual(docs_sync.returncode, 0, docs_sync.stderr)

            result = run_python_script(
                "dashboard.py",
                "--workspace",
                str(workspace),
                "--persist",
                "--format",
                "json",
                env=companion_env,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["next_workflow"], "review")
            self.assertTrue(report["brownfield"]["mapped"])
            self.assertEqual(report["continuity"]["decisions"], 1)
            self.assertEqual(report["continuity"]["learnings"], 1)
            self.assertTrue(any(item["id"] == "nextjs-typescript-postgres" for item in report["companions"]))
            self.assertTrue(any(item["profile"] == "nextjs-prisma-app-router" for item in report["companions"]))
            self.assertTrue((workspace / ".forge-artifacts" / "dashboard" / "latest.json").exists())

    def test_dashboard_prefers_brownfield_entry_for_unscoped_repo(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            workspace.mkdir(parents=True, exist_ok=True)
            (workspace / "README.md").write_text("# Demo\n", encoding="utf-8")
            (workspace / "package.json").write_text('{"name":"demo-app"}\n', encoding="utf-8")

            result = run_python_script(
                "dashboard.py",
                "--workspace",
                str(workspace),
                "--format",
                "json",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["next_workflow"], "map-codebase")
        self.assertFalse(report["brownfield"]["mapped"])
        self.assertIn("Run `doctor` and `map-codebase`", report["recommended_action"])


if __name__ == "__main__":
    unittest.main()
