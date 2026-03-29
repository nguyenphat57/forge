from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from companion_test_support import run_python_script


class CompanionPresetTests(unittest.TestCase):
    def test_scaffold_minimal_preset_creates_expected_files(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "demo-app"
            result = run_python_script(
                "scaffold_preset.py",
                "--workspace",
                str(workspace),
                "--preset",
                "minimal-saas",
                "--project-name",
                "Demo App",
                "--apply",
                "--format",
                "json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["preset"], "minimal-saas")
            self.assertTrue((workspace / "package.json").exists())
            self.assertTrue((workspace / "prisma" / "schema.prisma").exists())
            package_json = (workspace / "package.json").read_text(encoding="utf-8")
            self.assertIn("\"name\": \"demo-app\"", package_json)

    def test_scaffold_auth_preset_creates_auth_surfaces(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "demo-app"
            result = run_python_script(
                "scaffold_preset.py",
                "--workspace",
                str(workspace),
                "--preset",
                "auth-saas",
                "--project-name",
                "Demo App",
                "--apply",
                "--format",
                "json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["preset"], "auth-saas")
            self.assertTrue((workspace / "app" / "(auth)" / "login" / "page.tsx").exists())
            self.assertTrue((workspace / "lib" / "auth" / "session.ts").exists())
            env_example = (workspace / ".env.example").read_text(encoding="utf-8")
            self.assertIn("AUTH_SECRET", env_example)

    def test_scaffold_billing_preset_creates_billing_surfaces(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "demo-app"
            result = run_python_script(
                "scaffold_preset.py",
                "--workspace",
                str(workspace),
                "--preset",
                "billing-saas",
                "--project-name",
                "Demo App",
                "--apply",
                "--format",
                "json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["preset"], "billing-saas")
            self.assertTrue((workspace / "app" / "(app)" / "billing" / "page.tsx").exists())
            self.assertTrue((workspace / "app" / "api" / "webhooks" / "stripe" / "route.ts").exists())
            env_example = (workspace / ".env.example").read_text(encoding="utf-8")
            self.assertIn("STRIPE_SECRET_KEY", env_example)

    def test_scaffold_observability_preset_creates_status_surfaces(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "demo-app"
            result = run_python_script(
                "scaffold_preset.py",
                "--workspace",
                str(workspace),
                "--preset",
                "deploy-observability",
                "--project-name",
                "Demo App",
                "--apply",
                "--format",
                "json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["preset"], "deploy-observability")
            self.assertTrue((workspace / "app" / "api" / "health" / "route.ts").exists())
            self.assertTrue((workspace / "app" / "(app)" / "status" / "page.tsx").exists())
            env_example = (workspace / ".env.example").read_text(encoding="utf-8")
            self.assertIn("SENTRY_DSN", env_example)


if __name__ == "__main__":
    unittest.main()
