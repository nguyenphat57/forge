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
    def _run_repo_operator(self, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        return subprocess.run(
            [sys.executable, str(ROOT_DIR / "scripts" / "repo_operator.py"), *args],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            env=merged_env,
        )

    def test_repo_operator_is_the_only_documented_repo_root_operator_entrypoint(self) -> None:
        self.assertTrue((ROOT_DIR / "scripts" / "repo_operator.py").exists())
        removed_proxies = [
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
        for name in removed_proxies:
            with self.subTest(script=name):
                self.assertFalse((ROOT_DIR / "scripts" / name).exists())

    def test_workspace_agents_points_codex_to_repo_operator(self) -> None:
        agents = (ROOT_DIR / "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("use `scripts/repo_operator.py` as the canonical operator entrypoint", agents)
        self.assertIn("python scripts/repo_operator.py resume", agents)
        self.assertIn("python scripts/repo_operator.py save --workspace C:\\Users\\Admin\\.gemini\\forge --format json", agents)
        self.assertIn("python scripts/repo_operator.py handover --workspace C:\\Users\\Admin\\.gemini\\forge --format json", agents)
        self.assertIn("python scripts/repo_operator.py help --workspace C:\\Users\\Admin\\.gemini\\forge --format json", agents)
        self.assertIn("python scripts/repo_operator.py next --workspace C:\\Users\\Admin\\.gemini\\forge --format json", agents)
        self.assertIn("python scripts/repo_operator.py run --workspace C:\\Users\\Admin\\.gemini\\forge", agents)
        self.assertIn("python scripts/repo_operator.py bump --workspace C:\\Users\\Admin\\.gemini\\forge", agents)
        self.assertIn("python scripts/repo_operator.py rollback --scope <scope> --format json", agents)
        self.assertIn("python scripts/repo_operator.py customize --workspace C:\\Users\\Admin\\.gemini\\forge --format json", agents)
        self.assertIn("python scripts/repo_operator.py init --workspace C:\\Users\\Admin\\.gemini\\forge --format json", agents)
        self.assertIn("may auto-seed canonical `workflow-state`", agents)
        self.assertNotIn("python scripts/repo_operator.py bootstrap", agents)
        self.assertNotIn("python scripts/session_context.py", agents)
        self.assertNotIn("python scripts/resolve_help_next.py", agents)
        self.assertNotIn("python scripts/run_with_guidance.py", agents)

    def test_repo_operator_restores_context(self) -> None:
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

            saved = self._run_repo_operator(
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

            resumed = self._run_repo_operator(
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
        self.assertEqual(report["current_stage"], "unscoped")
        self.assertEqual(report["current_focus"], "No active work slice detected from repo state.")
        self.assertEqual(report["pending_work"], ["Run browser QA on checkout"])
        self.assertIn("Verification: pytest tests/test_checkout.py", report["relevant_continuity"])

    def test_repo_operator_rejects_unknown_action(self) -> None:
        result = self._run_repo_operator("unknown-action")

        self.assertEqual(result.returncode, 2)
        self.assertIn("Unsupported action: unknown-action", result.stderr)
        self.assertIn("Usage:", result.stderr)

    def test_repo_operator_rejects_demoted_capture_continuity_action(self) -> None:
        result = self._run_repo_operator("capture-continuity")

        self.assertEqual(result.returncode, 2)
        self.assertIn("Unsupported action: capture-continuity", result.stderr)
        self.assertIn("Usage:", result.stderr)

    def test_repo_operator_rejects_retired_bootstrap_action(self) -> None:
        result = self._run_repo_operator("bootstrap")

        self.assertEqual(result.returncode, 2)
        self.assertIn("Unsupported action: bootstrap", result.stderr)
        self.assertIn("Usage:", result.stderr)


if __name__ == "__main__":
    unittest.main()
