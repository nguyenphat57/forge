from __future__ import annotations

import json
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
                backup_dir=str(temp_root / "backups"),
                dry_run=True,
                activate_codex=True,
                codex_home=str(codex_home),
            )

            self.assertTrue(report["codex_host_activation"]["enabled"])
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
                backup_dir=str(temp_root / "backups"),
                activate_codex=True,
                codex_home=str(codex_home),
            )

            self.assertTrue((target / "SKILL.md").exists())
            self.assertFalse((target / "old.txt").exists())
            self.assertFalse(legacy_runtime.exists())
            self.assertFalse(legacy_skill.exists())

            agents_text = agents_path.read_text(encoding="utf-8")
            self.assertIn("Use `forge-codex` as the only global orchestrator for Codex.", agents_text)
            self.assertIn(str(target.resolve()), agents_text)
            self.assertNotIn("{{FORGE_CODEX_SKILL}}", agents_text)

            host_backup_path = Path(report["codex_host_activation"]["host_backup_path"])
            self.assertTrue(host_backup_path.exists())
            self.assertTrue((host_backup_path / "AGENTS.md").exists())
            self.assertTrue((host_backup_path / "awf-codex" / "workflows" / "plan.md").exists())
            self.assertTrue((host_backup_path / "skills" / "awf-session-restore" / "SKILL.md").exists())

            manifest = json.loads((target / "INSTALL-MANIFEST.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["codex_host_activation"]["enabled"])
            self.assertNotIn("awf-codex", json.dumps(manifest, ensure_ascii=False))

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
                    backup_dir=str(temp_root / "backups"),
                    dry_run=True,
                    activate_codex=True,
                    codex_home=str(codex_home),
                )


if __name__ == "__main__":
    unittest.main()
