from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from release_repo_test_support import ROOT_DIR


class RepoOperatorScriptShimTests(unittest.TestCase):
    def _run_script(self, script_name: str, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        return subprocess.run(
            [sys.executable, str(ROOT_DIR / "scripts" / script_name), *args],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            env=merged_env,
        )

    def test_documented_codex_operator_wrappers_exist_at_repo_root(self) -> None:
        expected = [
            "capture_continuity.py",
            "initialize_workspace.py",
            "prepare_bump.py",
            "resolve_help_next.py",
            "resolve_preferences.py",
            "resolve_rollback.py",
            "run_with_guidance.py",
            "session_context.py",
            "write_preferences.py",
        ]
        for name in expected:
            with self.subTest(script=name):
                self.assertTrue((ROOT_DIR / "scripts" / name).exists())

    def test_workspace_agents_points_codex_to_repo_root_operator_wrappers(self) -> None:
        agents = (ROOT_DIR / "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("prefer repo-root operator wrappers under `scripts/`", agents)
        self.assertIn("python scripts/session_context.py resume", agents)
        self.assertIn("python scripts/session_context.py save --workspace C:\\Users\\Admin\\.gemini\\forge --format json", agents)
        self.assertIn("python scripts/session_context.py save --workspace C:\\Users\\Admin\\.gemini\\forge --write-handover --format json", agents)
        self.assertIn("python scripts/resolve_help_next.py --workspace C:\\Users\\Admin\\.gemini\\forge --mode help", agents)
        self.assertIn("python scripts/resolve_help_next.py --workspace C:\\Users\\Admin\\.gemini\\forge --mode next", agents)
        self.assertIn("python scripts/run_with_guidance.py --workspace C:\\Users\\Admin\\.gemini\\forge", agents)
        self.assertIn("python scripts/prepare_bump.py --workspace C:\\Users\\Admin\\.gemini\\forge", agents)
        self.assertIn("python scripts/resolve_rollback.py --workspace C:\\Users\\Admin\\.gemini\\forge", agents)
        self.assertIn("python scripts/resolve_preferences.py --workspace C:\\Users\\Admin\\.gemini\\forge --format json", agents)
        self.assertIn("python scripts/initialize_workspace.py --workspace C:\\Users\\Admin\\.gemini\\forge", agents)

    def test_root_session_context_wrapper_restores_context(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            forge_home = Path(temp_dir) / "forge-home"
            workspace.mkdir(parents=True, exist_ok=True)
            (workspace / "README.md").write_text("# Checkout Workspace\n", encoding="utf-8")
            env = {
                "FORGE_HOME": str(forge_home),
                "HOME": temp_dir,
                "USERPROFILE": temp_dir,
            }

            saved = self._run_script(
                "session_context.py",
                "save",
                "--workspace",
                str(workspace),
                "--task",
                "Finish checkout retry slice",
                "--pending",
                "Run browser QA on checkout",
                "--verification",
                "pytest tests/test_checkout.py",
                "--write-handover",
                "--format",
                "json",
                env=env,
            )
            self.assertEqual(saved.returncode, 0, saved.stderr)

            resumed = self._run_script(
                "session_context.py",
                "resume",
                "--workspace",
                str(workspace),
                "--format",
                "json",
                env=env,
            )
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            report = json.loads(resumed.stdout)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["mode"], "resume")
        self.assertEqual(report["current_stage"], "session-active")
        self.assertEqual(report["current_focus"], "Session task: Finish checkout retry slice")
        self.assertEqual(report["pending_work"], ["Run browser QA on checkout"])
        self.assertIn("Verification: pytest tests/test_checkout.py", report["relevant_continuity"])


if __name__ == "__main__":
    unittest.main()
