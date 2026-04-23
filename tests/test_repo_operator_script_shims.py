from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

from release_repo_test_support import ROOT_DIR


class RepoOperatorScriptShimTests(unittest.TestCase):
    def test_repo_operator_surface_is_retired(self) -> None:
        removed_proxies = [
            "capture_continuity.py",
            "initialize_workspace.py",
            "prepare_bump.py",
            "repo_operator.py",
            "resolve_help_next.py",
            "resolve_preferences.py",
            "resolve_rollback.py",
            "run_with_guidance.py",
            "session_context.py",
            "write_preferences.py",
            "_forge_core_script_proxy.py",
        ]
        for name in removed_proxies:
            with self.subTest(script=name):
                self.assertFalse((ROOT_DIR / "scripts" / name).exists())

    def test_workspace_agents_points_codex_to_forge_skills(self) -> None:
        agents = (ROOT_DIR / "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("Use `forge-session-management` for `resume`, `continue`, and recap-style context restore", agents)
        self.assertIn("Use `forge-session-management` for `save context`", agents)
        self.assertIn("Use `forge-session-management` for `handover`", agents)
        self.assertIn("forge-bump-release", agents)
        self.assertIn("Use natural language plus Forge skills for guidance, next-step selection, and command execution", agents)
        self.assertNotIn("python scripts/repo_operator.py bump", agents)
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


if __name__ == "__main__":
    unittest.main()
