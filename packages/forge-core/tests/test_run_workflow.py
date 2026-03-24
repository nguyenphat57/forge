from __future__ import annotations

import json
import unittest

from support import FIXTURES_DIR, run_python_script, workspace_fixture


class RunWorkflowTests(unittest.TestCase):
    def test_build_success_routes_to_test(self) -> None:
        helper = FIXTURES_DIR / "run_helpers" / "build_fixture.py"
        result = run_python_script(
            "run_with_guidance.py",
            "--workspace",
            str(workspace_fixture("run_workspace")),
            "--timeout-ms",
            "1000",
            "--format",
            "json",
            "--",
            "python",
            str(helper),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["state"], "completed")
        self.assertEqual(report["command_kind"], "build")
        self.assertEqual(report["suggested_workflow"], "test")

    def test_ready_server_timeout_is_treated_as_running(self) -> None:
        helper = FIXTURES_DIR / "run_helpers" / "serve_fixture.py"
        result = run_python_script(
            "run_with_guidance.py",
            "--workspace",
            str(workspace_fixture("run_workspace")),
            "--timeout-ms",
            "150",
            "--format",
            "json",
            "--",
            "python",
            str(helper),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["state"], "running")
        self.assertEqual(report["suggested_workflow"], "test")
        self.assertTrue(report["readiness_detected"])

    def test_failed_command_routes_to_debug(self) -> None:
        helper = FIXTURES_DIR / "run_helpers" / "fail_fixture.py"
        result = run_python_script(
            "run_with_guidance.py",
            "--workspace",
            str(workspace_fixture("run_workspace")),
            "--timeout-ms",
            "1000",
            "--format",
            "json",
            "--",
            "python",
            str(helper),
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)

        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["state"], "failed")
        self.assertEqual(report["suggested_workflow"], "debug")
        self.assertIsNotNone(report["error_translation"])
        self.assertEqual(report["error_translation"]["category"], "module")

    def test_deploy_success_routes_to_deploy(self) -> None:
        helper = FIXTURES_DIR / "run_helpers" / "deploy_fixture.py"
        result = run_python_script(
            "run_with_guidance.py",
            "--workspace",
            str(workspace_fixture("run_workspace")),
            "--timeout-ms",
            "1000",
            "--format",
            "json",
            "--",
            "python",
            str(helper),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["state"], "completed")
        self.assertEqual(report["command_kind"], "deploy")
        self.assertEqual(report["suggested_workflow"], "deploy")


if __name__ == "__main__":
    unittest.main()
