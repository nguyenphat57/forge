from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_release
import install_bundle


FORGE_SIBLING_SKILLS = [
    "forge-brainstorming",
    "forge-writing-plans",
    "forge-executing-plans",
    "forge-test-driven-development",
    "forge-using-git-worktrees",
    "forge-dispatching-parallel-agents",
    "forge-subagent-driven-development",
    "forge-systematic-debugging",
    "forge-requesting-code-review",
    "forge-receiving-code-review",
    "forge-verification-before-completion",
    "forge-finishing-a-development-branch",
    "forge-writing-skills",
    "forge-session-management",
]

EXPECTED_SIBLING_SKILL_REFERENCES = {
    "forge-brainstorming": [
        "references/design/architectural-lens.md",
        "references/design/visual-companion-guidance.md",
    ],
    "forge-subagent-driven-development": [
        "references/subagent-execution.md",
        "references/subagent-prompts/final-reviewer-prompt.md",
        "references/subagent-prompts/implementer-prompt.md",
        "references/subagent-prompts/quality-reviewer-prompt.md",
        "references/subagent-prompts/spec-reviewer-prompt.md",
    ],
    "forge-systematic-debugging": [
        "references/debugging/condition-based-waiting.md",
        "references/debugging/defense-in-depth.md",
        "references/debugging/root-cause-tracing.md",
    ],
}


class RetiredBundleMatrixTests(unittest.TestCase):
    def test_build_release_only_keeps_kernel_bundles(self) -> None:
        build_release.build_all(force=True)

        self.assertTrue((ROOT_DIR / "dist" / "forge-core").exists())
        self.assertTrue((ROOT_DIR / "dist" / "forge-codex").exists())
        self.assertTrue((ROOT_DIR / "dist" / "forge-antigravity").exists())
        for bundle_name in ("forge-core", "forge-codex", "forge-antigravity"):
            with self.subTest(bundle=bundle_name):
                self.assertFalse((ROOT_DIR / "dist" / bundle_name / "skills").exists())
                self.assertFalse((ROOT_DIR / "dist" / bundle_name / "references").exists())
        for skill_name in FORGE_SIBLING_SKILLS:
            with self.subTest(skill=skill_name):
                self.assertTrue((ROOT_DIR / "dist" / skill_name / "SKILL.md").exists())
                self.assertFalse((ROOT_DIR / "dist" / skill_name / "scripts").exists())
                self.assertFalse((ROOT_DIR / "dist" / skill_name / "data").exists())
        for skill_name, relative_paths in EXPECTED_SIBLING_SKILL_REFERENCES.items():
            for relative_path in relative_paths:
                with self.subTest(skill=skill_name, path=relative_path):
                    self.assertTrue((ROOT_DIR / "dist" / skill_name / relative_path).exists())
        self.assertFalse((ROOT_DIR / "dist" / "forge-browse").exists())
        self.assertFalse((ROOT_DIR / "dist" / "forge-design").exists())

    def test_install_cli_choices_match_kernel_only_bundle_set(self) -> None:
        self.assertEqual(
            install_bundle.bundle_names(),
            ["forge-core", "forge-antigravity", "forge-codex"],
        )

    def test_package_matrix_serializes_three_bundles(self) -> None:
        package_matrix = json.loads((ROOT_DIR / "docs" / "release" / "package-matrix.json").read_text(encoding="utf-8"))
        self.assertEqual([bundle["name"] for bundle in package_matrix["bundles"]], ["forge-core", "forge-antigravity", "forge-codex"])

    def test_package_matrix_declares_sibling_skill_pack(self) -> None:
        package_matrix = json.loads((ROOT_DIR / "docs" / "release" / "package-matrix.json").read_text(encoding="utf-8"))

        self.assertEqual(package_matrix["skill_pack"]["source"], "packages/forge-skills")
        self.assertEqual(package_matrix["skill_pack"]["skills"], FORGE_SIBLING_SKILLS)

    def test_package_matrix_has_no_root_reference_required_paths(self) -> None:
        package_matrix = json.loads((ROOT_DIR / "docs" / "release" / "package-matrix.json").read_text(encoding="utf-8"))

        for bundle in package_matrix["bundles"]:
            for path in bundle["required_bundle_paths"]:
                with self.subTest(bundle=bundle["name"], path=path):
                    self.assertFalse(path.startswith("references/"))


if __name__ == "__main__":
    unittest.main()
