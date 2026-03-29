from __future__ import annotations

import json
import unittest

from support import copied_workspace_fixture, run_python_script


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
        with copied_workspace_fixture("nextjs_postgres_workspace") as workspace:
            result = run_python_script("map_codebase.py", "--workspace", str(workspace), "--format", "json")

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["companions"][0]["id"], "nextjs-typescript-postgres")
            self.assertIn("prisma", report["stack"]["database_adapters"])
            self.assertIn("nextjs-app-router", report["stack"]["frameworks"])
            self.assertEqual(report["companion_operator"][0]["profile"], "nextjs-prisma-app-router")
            self.assertEqual(report["companion_operator"][0]["verification_pack"], "nextjs-production-ready")


if __name__ == "__main__":
    unittest.main()
