from __future__ import annotations

import json
import os
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


NATIVE_ANTIGRAVITY_PREFERENCES = {
    "version": "1.0",
    "created_at": "2026-03-09T11:25:43+07:00",
    "scope": "project",
    "communication": {
        "tone": "custom",
        "tone_detail": "Goi Sep, xung Em",
        "personality": "smart_assistant",
        "language": "vi",
    },
    "technical": {
        "detail_level": "detailed",
        "autonomy": "ask_often",
        "output_quality": "production_ready",
        "technical_level": "learning",
    },
    "working_style": {
        "pace": "steady",
        "feedback": "direct",
    },
    "custom_rules": [
        "Moi file khong duoc vuot qua 300 dong",
        "Luon dung PowerShell thay vi Command Prompt",
    ],
}


class AntigravityHostInstallTests(unittest.TestCase):
    def seed_gemini_home(self, gemini_home: Path) -> Path:
        gemini_md_path = gemini_home / "GEMINI.md"
        gemini_md_path.parent.mkdir(parents=True, exist_ok=True)
        gemini_md_path.write_text("legacy global orchestrator", encoding="utf-8")
        return gemini_md_path

    def install_antigravity_bundle(self, temp_root: Path) -> tuple[dict, Path]:
        target = temp_root / "antigravity-home" / "skills" / "forge-antigravity"
        report = install_bundle.install_bundle(
            "forge-antigravity",
            target=str(target),
            backup_dir=str(temp_root / "backups"),
        )
        return report, target

    def test_activate_gemini_rewrites_global_gemini_md(self) -> None:
        build_release.build_all()
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            gemini_home = temp_root / "gemini-home"
            target = gemini_home / "antigravity" / "skills" / "forge-antigravity"
            gemini_md_path = self.seed_gemini_home(gemini_home)

            report = install_bundle.install_bundle(
                "forge-antigravity",
                target=str(target),
                backup_dir=str(temp_root / "backups"),
                activate_gemini=True,
                gemini_home=str(gemini_home),
            )

            rendered = gemini_md_path.read_text(encoding="utf-8")
            expected_state_root = str((gemini_home / "antigravity" / "forge-antigravity").resolve())
            expected_preferences = str((gemini_home / "antigravity" / "forge-antigravity" / "state" / "preferences.json").resolve())
            expected_skill = str((target / "SKILL.md").resolve())

            self.assertIn("Use `forge-antigravity` as the global orchestrator for Gemini workspaces.", rendered)
            self.assertIn(expected_skill, rendered)
            self.assertIn(expected_state_root, rendered)
            self.assertIn(expected_preferences, rendered)
            self.assertIn(f"python {target.resolve() / 'scripts' / 'resolve_preferences.py'}", rendered)

            host_backup_path = Path(report["gemini_host_activation"]["host_backup_path"])
            self.assertTrue(host_backup_path.exists())
            self.assertTrue((host_backup_path / "GEMINI.md").exists())

            manifest = json.loads((target / "INSTALL-MANIFEST.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["gemini_host_activation"]["enabled"])
            self.assertEqual(manifest["gemini_host_activation"]["gemini_md_path"], str(gemini_md_path.resolve()))
            self.assertEqual(manifest["state"]["root"], expected_state_root)
            self.assertEqual(manifest["state"]["preferences_path"], expected_preferences)
            self.assertTrue(manifest["bundle_fingerprint"]["host_mutation_expected"])
            self.assertTrue(manifest["bundle_fingerprint"]["matches_source"])
            self.assertEqual(len(manifest["bundle_fingerprint"]["installed"]["sha256"]), 64)

    def run_installed_script(self, script_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.pop("FORGE_HOME", None)
        return subprocess.run(
            [sys.executable, str(script_path), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            env=env,
        )

    def test_installed_antigravity_bundle_defaults_to_vietnamese_output_contract(self) -> None:
        build_release.build_all()
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            _, target = self.install_antigravity_bundle(temp_root)

            result = self.run_installed_script(target / "scripts" / "resolve_preferences.py", "--format", "json")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)

            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["source"]["type"], "defaults")
            self.assertEqual(
                payload["preferences"],
                {
                    "technical_level": "basic",
                    "detail_level": "balanced",
                    "autonomy_level": "balanced",
                    "pace": "balanced",
                    "feedback_style": "balanced",
                    "personality": "default",
                    "language": "vi",
                    "orthography": "vietnamese_diacritics",
                    "delegation_preference": "auto",
                },
            )
            self.assertEqual(payload["output_contract"]["language"], "vi")
            self.assertEqual(payload["output_contract"]["orthography"], "vietnamese-diacritics")
            self.assertEqual(payload["output_contract"]["accent_policy"], "required")
            self.assertEqual(payload["output_contract"]["encoding"], "utf-8")

    def test_installed_antigravity_bundle_reads_native_preferences_schema(self) -> None:
        build_release.build_all()
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            report, target = self.install_antigravity_bundle(temp_root)
            preferences_path = Path(report["state"]["preferences_path"])
            preferences_path.parent.mkdir(parents=True, exist_ok=True)
            preferences_path.write_text(
                json.dumps(NATIVE_ANTIGRAVITY_PREFERENCES, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            result = self.run_installed_script(target / "scripts" / "resolve_preferences.py", "--format", "json")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)

            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["source"]["type"], "global")
            self.assertEqual(payload["source"]["path"], str(preferences_path))
            self.assertEqual(
                payload["preferences"],
                {
                    "technical_level": "basic",
                    "detail_level": "detailed",
                    "autonomy_level": "guided",
                    "pace": "steady",
                    "feedback_style": "direct",
                    "personality": "default",
                    "delegation_preference": "auto",
                    "language": "vi",
                    "orthography": "vietnamese_diacritics",
                    "tone_detail": "Goi Sep, xung Em",
                    "output_quality": "production_ready",
                    "custom_rules": [
                        "Moi file khong duoc vuot qua 300 dong",
                        "Luon dung PowerShell thay vi Command Prompt",
                    ],
                },
            )
            self.assertEqual(payload["warnings"], [])

    def test_installed_antigravity_bundle_migrates_legacy_state_to_split_files(self) -> None:
        build_release.build_all()
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            report, target = self.install_antigravity_bundle(temp_root)
            preferences_path = Path(report["state"]["preferences_path"])
            preferences_path.parent.mkdir(parents=True, exist_ok=True)
            preferences_path.write_text(
                json.dumps(NATIVE_ANTIGRAVITY_PREFERENCES, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            result = self.run_installed_script(
                target / "scripts" / "write_preferences.py",
                "--pace",
                "fast",
                "--feedback-style",
                "gentle",
                "--apply",
                "--format",
                "json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)

            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["preferences"]["detail_level"], "detailed")
            self.assertEqual(payload["preferences"]["autonomy_level"], "guided")
            self.assertEqual(payload["preferences"]["pace"], "fast")
            self.assertEqual(payload["preferences"]["feedback_style"], "gentle")
            self.assertEqual(payload["preferences"]["personality"], "default")
            self.assertTrue(payload["migrated_legacy_global_preferences"])

            written = json.loads(preferences_path.read_text(encoding="utf-8"))
            self.assertEqual(
                written,
                {
                    "technical_level": "basic",
                    "detail_level": "detailed",
                    "autonomy_level": "guided",
                    "pace": "fast",
                    "feedback_style": "gentle",
                    "personality": "default",
                    "language": "vi",
                    "tone_detail": "Goi Sep, xung Em",
                    "output_quality": "production_ready",
                    "custom_rules": NATIVE_ANTIGRAVITY_PREFERENCES["custom_rules"],
                },
            )
            self.assertTrue((preferences_path.parent / "preferences.json.legacy.bak").exists())
            self.assertFalse(preferences_path.with_name("extra_preferences.json").exists())


if __name__ == "__main__":
    unittest.main()
