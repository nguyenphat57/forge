from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from companion_test_support import TEMPLATES_DIR, run_python_script


class CompanionEnricherTests(unittest.TestCase):
    def test_enrich_doctor_reports_nextjs_and_postgres_checks(self) -> None:
        workspace = TEMPLATES_DIR / "minimal-saas"
        result = run_python_script("enrich_doctor.py", "--workspace", str(workspace), "--format", "json")

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        statuses = {item["id"]: item["status"] for item in report["checks"]}
        self.assertEqual(statuses["nextjs-package"], "PASS")
        self.assertEqual(statuses["postgres-adapter"], "PASS")

    def test_enrich_map_reports_app_router_and_prisma_markers(self) -> None:
        workspace = TEMPLATES_DIR / "minimal-saas"
        result = run_python_script("enrich_map_codebase.py", "--workspace", str(workspace), "--format", "json")

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertIn("nextjs-app-router", report["enrichments"]["stack"]["frameworks"])
        self.assertIn("prisma/schema.prisma", report["enrichments"]["structure"]["entrypoints"])

    def test_enrich_doctor_reports_auth_and_billing_env_checks(self) -> None:
        workspace = TEMPLATES_DIR / "billing-saas"
        result = run_python_script("enrich_doctor.py", "--workspace", str(workspace), "--format", "json")

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        statuses = {item["id"]: item["status"] for item in report["checks"]}
        self.assertEqual(statuses["auth-secret"], "PASS")
        self.assertEqual(statuses["stripe-env"], "PASS")

    def test_enrich_map_reports_auth_and_billing_markers(self) -> None:
        workspace = TEMPLATES_DIR / "billing-saas"
        result = run_python_script("enrich_map_codebase.py", "--workspace", str(workspace), "--format", "json")

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertIn("billing", report["enrichments"]["stack"]["product_features"])
        self.assertIn("auth", report["enrichments"]["stack"]["product_features"])
        self.assertIn("auth", report["enrichments"]["structure"]["integrations"])
        self.assertIn("stripe", report["enrichments"]["structure"]["integrations"])

    def test_enrich_doctor_reports_observability_env_checks(self) -> None:
        workspace = TEMPLATES_DIR / "deploy-observability"
        result = run_python_script("enrich_doctor.py", "--workspace", str(workspace), "--format", "json")

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        statuses = {item["id"]: item["status"] for item in report["checks"]}
        self.assertEqual(statuses["observability-env"], "PASS")

    def test_enrich_map_reports_observability_markers(self) -> None:
        workspace = TEMPLATES_DIR / "deploy-observability"
        result = run_python_script("enrich_map_codebase.py", "--workspace", str(workspace), "--format", "json")

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertIn("observability", report["enrichments"]["stack"]["product_features"])
        self.assertIn("sentry", report["enrichments"]["structure"]["integrations"])
        self.assertIn("opentelemetry", report["enrichments"]["structure"]["integrations"])


if __name__ == "__main__":
    unittest.main()
