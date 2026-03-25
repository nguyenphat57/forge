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
    def install_antigravity_bundle(self, temp_root: Path) -> tuple[dict, Path]:
        target = temp_root / "antigravity-home" / "skills" / "forge-antigravity"
        report = install_bundle.install_bundle(
            "forge-antigravity",
            target=str(target),
            backup_dir=str(temp_root / "backups"),
        )
        return report, target

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
                },
            )
            self.assertEqual(payload["warnings"], [])

    def test_installed_antigravity_bundle_writes_back_to_native_schema(self) -> None:
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

            written = json.loads(preferences_path.read_text(encoding="utf-8"))
            self.assertEqual(written["communication"]["personality"], "smart_assistant")
            self.assertEqual(written["technical"]["detail_level"], "detailed")
            self.assertEqual(written["technical"]["autonomy"], "ask_often")
            self.assertEqual(written["technical"]["technical_level"], "learning")
            self.assertEqual(written["working_style"]["pace"], "fast")
            self.assertEqual(written["working_style"]["feedback"], "gentle")
            self.assertEqual(written["custom_rules"], NATIVE_ANTIGRAVITY_PREFERENCES["custom_rules"])


if __name__ == "__main__":
    unittest.main()
