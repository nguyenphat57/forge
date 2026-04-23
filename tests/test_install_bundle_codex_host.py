from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_release  # noqa: E402
import install_bundle  # noqa: E402


def assert_is_relative_to(test_case: unittest.TestCase, path: str | Path, parent: Path) -> None:
    test_case.assertTrue(Path(path).resolve().is_relative_to(parent.resolve()))


def assert_is_not_relative_to(test_case: unittest.TestCase, path: str | Path, parent: Path) -> None:
    test_case.assertFalse(Path(path).resolve().is_relative_to(parent.resolve()))


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
        "tools/visual-companion/scripts/frame-template.html",
        "tools/visual-companion/scripts/helper.js",
        "tools/visual-companion/scripts/server.cjs",
        "tools/visual-companion/scripts/start-server.ps1",
        "tools/visual-companion/scripts/start-server.sh",
        "tools/visual-companion/scripts/stop-server.ps1",
        "tools/visual-companion/scripts/stop-server.sh",
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


class CodexHostInstallTests(unittest.TestCase):
    def seed_codex_home(self, codex_home: Path, target: Path) -> tuple[Path, Path, Path]:
        target.mkdir(parents=True, exist_ok=True)
        (target / "old.txt").write_text("old", encoding="utf-8")

        agents_path = codex_home / "AGENTS.md"
        agents_path.parent.mkdir(parents=True, exist_ok=True)
        agents_path.write_text("legacy global orchestrator", encoding="utf-8")

        legacy_runtime = codex_home / "awf-codex"
        (legacy_runtime / "workflows").mkdir(parents=True, exist_ok=True)
        (legacy_runtime / "workflows" / "plan.md").write_text("legacy", encoding="utf-8")

        legacy_skill = codex_home / "skills" / "awf-session-restore"
        legacy_skill.mkdir(parents=True, exist_ok=True)
        (legacy_skill / "SKILL.md").write_text("legacy skill", encoding="utf-8")
        return agents_path, legacy_runtime, legacy_skill

    def test_activate_codex_dry_run_reports_without_mutation(self) -> None:
        build_release.build_all()
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            codex_home = temp_root / "codex-home"
            target = codex_home / "skills" / "forge-codex"
            agents_path, legacy_runtime, legacy_skill = self.seed_codex_home(codex_home, target)

            report = install_bundle.install_bundle(
                "forge-codex",
                target=str(target),
                dry_run=True,
                activate_codex=True,
                codex_home=str(codex_home),
            )

            self.assertTrue(report["codex_host_activation"]["enabled"])
            self.assertEqual(
                [item["name"] for item in report["sibling_skills"]["skills"]],
                FORGE_SIBLING_SKILLS,
            )
            self.assertEqual(agents_path.read_text(encoding="utf-8"), "legacy global orchestrator")
            self.assertTrue((target / "old.txt").exists())
            self.assertTrue(legacy_runtime.exists())
            self.assertTrue(legacy_skill.exists())

    def test_activate_codex_rewrites_agents_and_removes_legacy_artifacts(self) -> None:
        build_release.build_all()
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            codex_home = temp_root / "codex-home"
            target = codex_home / "skills" / "forge-codex"
            agents_path, legacy_runtime, legacy_skill = self.seed_codex_home(codex_home, target)

            report = install_bundle.install_bundle(
                "forge-codex",
                target=str(target),
                activate_codex=True,
                codex_home=str(codex_home),
            )

            self.assertTrue((target / "SKILL.md").exists())
            self.assertTrue((target / "commands").is_dir())
            self.assertTrue((target / "shared").is_dir())
            self.assertFalse((target / "engine").exists())
            self.assertFalse((target / "skills").exists())
            for skill_name in FORGE_SIBLING_SKILLS:
                with self.subTest(skill=skill_name):
                    self.assertTrue((codex_home / "skills" / skill_name / "SKILL.md").exists())
                    self.assertFalse((codex_home / "skills" / skill_name / "scripts").exists())
                    self.assertFalse((codex_home / "skills" / skill_name / "data").exists())
            for skill_name, relative_paths in EXPECTED_SIBLING_SKILL_REFERENCES.items():
                for relative_path in relative_paths:
                    with self.subTest(skill=skill_name, path=relative_path):
                        self.assertTrue((codex_home / "skills" / skill_name / relative_path).exists())
            self.assertFalse((target / "old.txt").exists())
            self.assertFalse(legacy_runtime.exists())
            self.assertFalse(legacy_skill.exists())

            agents_text = agents_path.read_text(encoding="utf-8")
            expected_state_root = str((codex_home / "forge-codex").resolve())
            expected_preferences = str((codex_home / "forge-codex" / "state" / "preferences.json").resolve())
            expected_skill = str((target / "SKILL.md").resolve())
            self.assertIn("Use `forge-codex` as the only global orchestrator for Codex.", agents_text)
            self.assertIn(expected_skill, agents_text)
            self.assertIn(expected_state_root, agents_text)
            self.assertIn(expected_preferences, agents_text)
            self.assertIn(f"python {target.resolve() / 'commands' / 'resolve_preferences.py'}", agents_text)
            self.assertNotIn("{{FORGE_CODEX_SKILL}}", agents_text)
            self.assertNotRegex(agents_text, re.compile(r"\{\{[A-Z0-9_]+\}\}"))

            host_backup_path = Path(report["codex_host_activation"]["host_backup_path"])
            self.assertTrue(host_backup_path.exists())
            self.assertTrue((host_backup_path / "AGENTS.md").exists())
            self.assertTrue((host_backup_path / "awf-codex" / "workflows" / "plan.md").exists())
            self.assertTrue((host_backup_path / "skills" / "awf-session-restore" / "SKILL.md").exists())
            assert_is_relative_to(self, host_backup_path, codex_home / "forge-codex" / "rollbacks" / "install")
            assert_is_not_relative_to(self, host_backup_path, ROOT_DIR)

            manifest = json.loads((target / "INSTALL-MANIFEST.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["codex_host_activation"]["enabled"])
            self.assertEqual(manifest["state"]["scope"], "adapter-global")
            self.assertEqual(manifest["state"]["root"], str((codex_home / "forge-codex").resolve()))
            self.assertEqual(
                manifest["state"]["preferences_path"],
                str((codex_home / "forge-codex" / "state" / "preferences.json").resolve()),
            )
            self.assertTrue(manifest["bundle_fingerprint"]["host_mutation_expected"])
            self.assertTrue(manifest["bundle_fingerprint"]["matches_source"])
            self.assertEqual(len(manifest["bundle_fingerprint"]["installed"]["sha256"]), 64)
            self.assertEqual(
                manifest["bundle_fingerprint"]["source"]["sha256"],
                report["source_build_manifest"]["bundle_fingerprint"]["sha256"],
            )
            self.assertEqual(report["source_build_manifest"]["state"]["dev_root"]["env_var"], "CODEX_HOME")
            self.assertEqual(report["source_build_manifest"]["state"]["dev_root"]["path_relative"], "forge-codex")
            self.assertEqual(
                report["source_build_manifest"]["generated_artifacts"]["artifacts"][0]["name"],
                "forge-codex-global-agents",
            )
            self.assertTrue((codex_home / "forge-codex").is_dir())
            self.assertTrue((codex_home / "forge-codex" / "state").is_dir())
            self.assertNotIn("awf-codex", json.dumps(manifest, ensure_ascii=False))

    def test_installed_codex_bundle_uses_codex_host_state_by_default(self) -> None:
        build_release.build_all()
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            codex_home = temp_root / "codex-home"
            target = codex_home / "skills" / "forge-codex"
            self.seed_codex_home(codex_home, target)

            install_bundle.install_bundle(
                "forge-codex",
                target=str(target),
                activate_codex=True,
                codex_home=str(codex_home),
            )

            self.assertTrue((target / "shared").is_dir())
            self.assertFalse((target / "engine").exists())

            workspace = temp_root / "workspace"
            workspace.mkdir(parents=True, exist_ok=True)
            expected_state_root = (codex_home / "forge-codex").resolve()
            expected_preferences = (expected_state_root / "state" / "preferences.json").resolve()
            env = os.environ.copy()
            env.pop("FORGE_HOME", None)

            write_result = subprocess.run(
                [
                    sys.executable,
                    str(target / "commands" / "write_preferences.py"),
                    "--workspace",
                    str(workspace),
                    "--technical-level",
                    "technical",
                    "--apply",
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
                env=env,
            )
            self.assertEqual(write_result.returncode, 0, write_result.stderr)
            write_report = json.loads(write_result.stdout)

            self.assertEqual(write_report["state_root"], str(expected_state_root))
            self.assertEqual(write_report["targets"], [str(expected_preferences)])
            self.assertTrue(expected_preferences.exists())

            resolve_result = subprocess.run(
                [
                    sys.executable,
                    str(target / "commands" / "resolve_preferences.py"),
                    "--workspace",
                    str(workspace),
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
                env=env,
            )
            self.assertEqual(resolve_result.returncode, 0, resolve_result.stderr)
            resolve_report = json.loads(resolve_result.stdout)

            self.assertEqual(resolve_report["source"]["type"], "global")
            self.assertEqual(resolve_report["source"]["path"], str(expected_preferences))
            self.assertEqual(resolve_report["preferences"]["technical_level"], "technical")

    def test_activate_codex_requires_canonical_target(self) -> None:
        build_release.build_all()
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            codex_home = temp_root / "codex-home"
            wrong_target = temp_root / "sandbox" / "forge-codex"

            with self.assertRaises(ValueError):
                install_bundle.install_bundle(
                    "forge-codex",
                    target=str(wrong_target),
                    dry_run=True,
                    activate_codex=True,
                    codex_home=str(codex_home),
                )


if __name__ == "__main__":
    unittest.main()
