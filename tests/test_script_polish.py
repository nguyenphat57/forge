from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def read_repo_text(relative_path: str) -> str:
    return (ROOT_DIR / relative_path).read_text(encoding="utf-8")


class ScriptPolishTests(unittest.TestCase):
    def test_dead_script_helpers_and_imports_are_removed(self) -> None:
        forbidden_by_file = {
            "scripts/generate_overlay_skills.py": [
                "adapter_skill_specs, ensure_generated_overlay_skills",
            ],
            "scripts/operator_surface_support.py": [
                "def operator_surface(",
                "def _first_host_value(",
            ],
            "scripts/install_bundle_report.py": [
                "def _version_parts(",
                "def _version_in_range(",
            ],
            "packages/forge-skills/bump-release/references/scripts/prepare_bump.py": [
                "_forge_core_command",
                "from common import",
                "from prepare_bump_git import",
                "from prepare_bump_semver import",
                "EXPLICIT_BUMP_TOKENS",
            ],
            "packages/forge-skills/session-management/commands/session_context_reports.py": [
                "git_worktree_clean,",
            ],
            "packages/forge-skills/customize/shared/preferences_store.py": [
                "def _write_scope_file(",
            ],
        }

        for relative_path, forbidden_items in forbidden_by_file.items():
            text = read_repo_text(relative_path)
            for forbidden in forbidden_items:
                with self.subTest(path=relative_path, forbidden=forbidden):
                    self.assertNotIn(forbidden, text)

    def test_host_artifact_specs_alias_is_removed(self) -> None:
        self.assertFalse((ROOT_DIR / "scripts" / "host_artifact_specs.py").exists())
        self.assertIn(
            "from host_artifact_manifest import generated_host_artifact_specs",
            read_repo_text("scripts/host_artifacts_support.py"),
        )
        self.assertIn(
            "from host_artifact_manifest import generated_host_artifact_specs",
            read_repo_text("tests/test_host_artifact_generation.py"),
        )
        self.assertNotIn(
            "host_artifact_specs.py",
            read_repo_text("scripts/build_release.py"),
        )

    def test_repo_operator_script_is_retired(self) -> None:
        self.assertFalse((ROOT_DIR / "scripts" / "repo_operator.py").exists())


if __name__ == "__main__":
    unittest.main()
