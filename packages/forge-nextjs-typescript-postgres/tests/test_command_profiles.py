from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from companion_test_support import TEMPLATES_DIR, run_python_script


class CompanionCommandTests(unittest.TestCase):
    def test_resolve_commands_uses_nextjs_prisma_profile(self) -> None:
        workspace = TEMPLATES_DIR / "minimal-saas"
        result = run_python_script("resolve_commands.py", "--workspace", str(workspace), "--format", "json")

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["profile"], "nextjs-prisma-app-router")
        self.assertEqual(report["package_manager"], "npm")
        self.assertEqual(report["commands"]["build"], "npm run build")
        self.assertEqual(report["verification_pack"]["id"], "nextjs-production-ready")

    def test_resolve_commands_uses_auth_profile(self) -> None:
        workspace = TEMPLATES_DIR / "auth-saas"
        result = run_python_script("resolve_commands.py", "--workspace", str(workspace), "--format", "json")

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["profile"], "nextjs-auth-prisma-app-router")
        self.assertEqual(report["commands"]["test_auth"], "npm run test:auth")
        self.assertEqual(report["verification_pack"]["id"], "nextjs-auth-ready")

    def test_resolve_commands_uses_billing_profile(self) -> None:
        workspace = TEMPLATES_DIR / "billing-saas"
        result = run_python_script("resolve_commands.py", "--workspace", str(workspace), "--format", "json")

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["profile"], "nextjs-billing-prisma-app-router")
        self.assertEqual(report["commands"]["test_billing"], "npm run test:billing")
        self.assertEqual(report["verification_pack"]["id"], "nextjs-billing-ready")

    def test_resolve_commands_uses_observability_profile(self) -> None:
        workspace = TEMPLATES_DIR / "deploy-observability"
        result = run_python_script("resolve_commands.py", "--workspace", str(workspace), "--format", "json")

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["profile"], "nextjs-observability-prisma-app-router")
        self.assertEqual(report["commands"]["test_observability"], "npm run test:observability")
        self.assertEqual(report["verification_pack"]["id"], "nextjs-observability-ready")


if __name__ == "__main__":
    unittest.main()
