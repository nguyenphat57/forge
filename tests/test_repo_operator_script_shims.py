from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

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

    def test_repo_operator_proxy_dispatches_to_owner_commands(self) -> None:
        proxy = (ROOT_DIR / "scripts" / "_forge_core_script_proxy.py").read_text(encoding="utf-8")

        self.assertIn('"commands"', proxy)
        self.assertNotIn("forge_core_runtime", proxy)
        self.assertNotIn("packages\" / \"forge-core\" / \"scripts", proxy)

    def test_workspace_agents_points_codex_to_repo_operator(self) -> None:
        agents = (ROOT_DIR / "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("use `scripts/repo_operator.py` as the canonical operator entrypoint", agents)
        self.assertIn("Use `forge-session-management` for `resume`, `continue`, and recap-style context restore", agents)
        self.assertIn("Use `forge-session-management` for `save context`", agents)
        self.assertIn("Use `forge-session-management` for `handover`", agents)
        self.assertIn("python scripts/repo_operator.py bump --workspace C:\\Users\\Admin\\.gemini\\forge", agents)
        self.assertIn("Use natural language plus Forge skills for guidance, next-step selection, and command execution", agents)
        self.assertNotIn("python scripts/repo_operator.py customize", agents)
        self.assertNotIn("python scripts/repo_operator.py help", agents)
        self.assertNotIn("python scripts/repo_operator.py next", agents)
        self.assertNotIn("python scripts/repo_operator.py run", agents)
        self.assertIn("forge-init", agents)
        self.assertIn("forge-customize", agents)
        self.assertIn("forge-verification-before-completion", agents)
        self.assertNotIn("python scripts/repo_operator.py bootstrap", agents)
        self.assertNotIn("python scripts/repo_operator.py rollback", agents)
        self.assertNotIn("python scripts/repo_operator.py init", agents)
        self.assertNotIn("python scripts/session_context.py", agents)
        self.assertNotIn("python scripts/resolve_help_next.py", agents)
        self.assertNotIn("python scripts/run_with_guidance.py", agents)

    def test_repo_operator_rejects_retired_session_actions_with_owner_guidance(self) -> None:
        for action in ("resume", "save", "handover"):
            with self.subTest(action=action):
                result = self._run_repo_operator(action)
                self.assertEqual(result.returncode, 2)
                self.assertIn(f"Unsupported action: {action}", result.stderr)
                self.assertIn("forge-session-management", result.stderr)

    def test_repo_operator_rejects_retired_help_next_run_actions_with_guidance(self) -> None:
        for action in ("help", "next", "run"):
            with self.subTest(action=action):
                result = self._run_repo_operator(action)
                self.assertEqual(result.returncode, 2)
                self.assertIn(f"Unsupported action: {action}", result.stderr)
                self.assertIn("natural language", result.stderr)
                self.assertIn("Forge skills", result.stderr)
                self.assertIn("host-native command execution", result.stderr)

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

    def test_repo_operator_rejects_removed_rollback_action(self) -> None:
        result = self._run_repo_operator("rollback")

        self.assertEqual(result.returncode, 2)
        self.assertIn("Unsupported action: rollback", result.stderr)
        self.assertIn("Usage:", result.stderr)

    def test_repo_operator_rejects_removed_customize_action(self) -> None:
        result = self._run_repo_operator("customize")

        self.assertEqual(result.returncode, 2)
        self.assertIn("Unsupported action: customize", result.stderr)
        self.assertIn("Usage:", result.stderr)


if __name__ == "__main__":
    unittest.main()
