from __future__ import annotations

import json
import unittest

from support import copied_workspace_fixture, run_python_script, temporary_workspace


class WorkspaceCanaryTests(unittest.TestCase):
    def test_workspace_canary_passes_for_agents_entrypoint_workspace(self) -> None:
        with copied_workspace_fixture("local_python_router", target_name="python-router") as workspace:
            (workspace / "pyproject.toml").write_text("[project]\nname='fixture'\n", encoding="utf-8")
            (workspace / "tests").mkdir()

            result = run_python_script(
                "run_workspace_canary.py",
                str(workspace),
                "--format",
                "json",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(any(item["name"] == "local-companion" for item in payload["scenarios"]))
        self.assertTrue(any(item["name"] == "review" for item in payload["scenarios"]))

    def test_workspace_canary_passes_without_agents_by_running_core_pack_only(self) -> None:
        with temporary_workspace("plain-python") as workspace:
            (workspace / "pyproject.toml").write_text("[project]\nname='fixture'\n", encoding="utf-8")
            (workspace / "tests").mkdir()

            result = run_python_script(
                "run_workspace_canary.py",
                str(workspace),
                "--format",
                "json",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "pass")
        self.assertIsNone(payload["router_check"])
        build_scenario = next(item for item in payload["scenarios"] if item["name"] == "build")
        self.assertNotIn("auth", build_scenario["prompt"].lower())


if __name__ == "__main__":
    unittest.main()
