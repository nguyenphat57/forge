from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import run_python_script, workspace_fixture


class WorkspaceCanaryTests(unittest.TestCase):
    def test_workspace_canary_passes_for_agents_entrypoint_workspace(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "python-router"
            shutil.copytree(workspace_fixture("local_python_router"), workspace)
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
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "plain-python"
            workspace.mkdir()
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


if __name__ == "__main__":
    unittest.main()
