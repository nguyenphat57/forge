from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import run_python_script


class ReviewPackTests(unittest.TestCase):
    def test_review_pack_flags_auth_and_billing_env_gaps(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "package.json").write_text(
                json.dumps(
                    {
                        "name": "billing-app",
                        "dependencies": {
                            "next": "15.0.0",
                            "@prisma/client": "6.0.0",
                            "bcryptjs": "2.4.3",
                            "stripe": "17.0.0",
                        },
                        "devDependencies": {"typescript": "5.0.0", "prisma": "6.0.0"},
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            (workspace / "tsconfig.json").write_text("{}", encoding="utf-8")
            (workspace / "prisma").mkdir()
            (workspace / "prisma" / "schema.prisma").write_text("generator client { provider = \"prisma-client-js\" }\n", encoding="utf-8")
            (workspace / "app" / "(auth)" / "login").mkdir(parents=True)
            (workspace / "app" / "(auth)" / "login" / "page.tsx").write_text("export default function Page() { return null; }\n", encoding="utf-8")
            (workspace / "app" / "api" / "webhooks" / "stripe").mkdir(parents=True)
            (workspace / "app" / "api" / "webhooks" / "stripe" / "route.ts").write_text("export async function POST() { return Response.json({ ok: true }); }\n", encoding="utf-8")
            (workspace / ".env.example").write_text("DATABASE_URL=\n", encoding="utf-8")

            result = run_python_script("review_pack.py", "--workspace", str(workspace), "--format", "json")

            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "WARN")
            self.assertIn("auth", report["features"])
            self.assertIn("billing", report["features"])
            self.assertTrue(any("AUTH_SECRET" in item for item in report["findings"]))
            self.assertTrue(any("STRIPE_SECRET_KEY" in item for item in report["findings"]))
            self.assertTrue(any("base URL" in item for item in report["findings"]))
            self.assertTrue(any("publishable key" in item for item in report["findings"]))

    def test_review_pack_adversarial_profile_adds_attack_checks(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "package.json").write_text(json.dumps({"dependencies": {"next": "15.0.0"}}, indent=2), encoding="utf-8")
            (workspace / "tsconfig.json").write_text("{}", encoding="utf-8")

            result = run_python_script(
                "review_pack.py",
                "--workspace",
                str(workspace),
                "--profile",
                "adversarial",
                "--format",
                "json",
            )

            self.assertIn(result.returncode, {0, 1}, result.stderr)
            report = json.loads(result.stdout)
            self.assertGreater(len(report["adversarial_checks"]), 0)

    def test_review_pack_flags_missing_webhook_route_for_billing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "package.json").write_text(
                json.dumps(
                    {
                        "dependencies": {"next": "15.0.0", "stripe": "17.0.0"},
                        "devDependencies": {"typescript": "5.0.0"},
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            (workspace / "tsconfig.json").write_text("{}", encoding="utf-8")
            (workspace / ".env.example").write_text("STRIPE_SECRET_KEY=\nSTRIPE_WEBHOOK_SECRET=\n", encoding="utf-8")
            (workspace / "lib" / "billing").mkdir(parents=True)
            (workspace / "lib" / "billing" / "stripe.ts").write_text("export const stripe = {};\n", encoding="utf-8")

            result = run_python_script("review_pack.py", "--workspace", str(workspace), "--format", "json")

            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(result.stdout)
            self.assertTrue(any("webhook route" in item for item in report["findings"]))

    def test_review_pack_detects_billing_markers_without_companion_match(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "package.json").write_text(
                json.dumps(
                    {
                        "name": "generic-billing-service",
                        "dependencies": {"stripe": "17.0.0"},
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            (workspace / "src" / "billing").mkdir(parents=True)
            (workspace / "src" / "billing" / "stripe.ts").write_text("export const stripe = {};\n", encoding="utf-8")
            (workspace / ".env.example").write_text("DATABASE_URL=\n", encoding="utf-8")

            result = run_python_script("review_pack.py", "--workspace", str(workspace), "--format", "json")

            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(result.stdout)
            self.assertIn("billing", report["features"])
            self.assertTrue(any("STRIPE_SECRET_KEY" in item for item in report["findings"]))


if __name__ == "__main__":
    unittest.main()
