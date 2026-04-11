from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import copied_workspace_fixture, reference_companion_environment, run_python_script


class MapCodebaseTests(unittest.TestCase):
    def test_map_codebase_detects_next_workspace_and_persists_artifacts(self) -> None:
        with copied_workspace_fixture("map_codebase_next_workspace") as workspace:
            result = run_python_script("map_codebase.py", "--workspace", str(workspace), "--format", "json")

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "PASS")
            self.assertIn("nextjs", report["stack"]["frameworks"])
            self.assertTrue(report["brownfield"]["core_only_ready"])
            self.assertTrue(any("`help` or `next`" in item for item in report["brownfield"]["next_actions"]))
            self.assertTrue((workspace / ".forge-artifacts" / "codebase" / "summary.md").exists())

    def test_map_codebase_supports_focus_mode_for_python_workspace(self) -> None:
        with copied_workspace_fixture("map_codebase_python_workspace") as workspace:
            result = run_python_script("map_codebase.py", "--workspace", str(workspace), "--focus", "api", "--format", "json")

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["project_name"], "billing-api")
            self.assertIn("fastapi", report["stack"]["frameworks"])
            self.assertTrue((workspace / ".forge-artifacts" / "codebase" / "focus" / "api.md").exists())

    def test_map_codebase_applies_nextjs_companion_enrichment(self) -> None:
        with copied_workspace_fixture("nextjs_postgres_workspace") as workspace, reference_companion_environment() as (_, companion_env):
            result = run_python_script("map_codebase.py", "--workspace", str(workspace), "--format", "json", env=companion_env)

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["companions"][0]["id"], "nextjs-typescript-postgres")
            self.assertIn("prisma", report["stack"]["database_adapters"])
            self.assertIn("nextjs-app-router", report["stack"]["frameworks"])
            self.assertEqual(report["companion_operator"][0]["profile"], "nextjs-prisma-app-router")
            self.assertEqual(report["companion_operator"][0]["verification_pack"], "nextjs-production-ready")

    def test_map_codebase_detects_repo_root_operator_entrypoints_from_agents(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "forge-source"
            scripts_dir = workspace / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            (workspace / "AGENTS.md").write_text(
                "\n".join(
                    [
                        "# Workspace Entry",
                        "- Use `python scripts/repo_operator.py resume --workspace <workspace> --format json`.",
                        "- Use `python scripts/repo_operator.py help --workspace <workspace> --format json`.",
                        "- Use `python scripts/repo_operator.py run --workspace <workspace> --timeout-ms 20000 -- <command>`.",
                    ]
                ),
                encoding="utf-8",
            )
            (scripts_dir / "repo_operator.py").write_text("print('shim')\n", encoding="utf-8")

            result = run_python_script("map_codebase.py", "--workspace", str(workspace), "--format", "json")

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertIn("scripts/repo_operator.py", report["brownfield"]["entrypoints"])
            self.assertNotIn("No obvious entrypoint detected from common markers.", report["brownfield"]["risks"])
            summary = (workspace / ".forge-artifacts" / "codebase" / "summary.md").read_text(encoding="utf-8")
            risks = (workspace / ".forge-artifacts" / "codebase" / "risks.md").read_text(encoding="utf-8")
            self.assertIn("scripts/repo_operator.py", summary)
            self.assertNotIn("No obvious entrypoint detected from common markers.", risks)


if __name__ == "__main__":
    unittest.main()
