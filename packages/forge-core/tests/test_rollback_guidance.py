from __future__ import annotations

import json
import unittest

from support import FIXTURES_DIR, run_python_script


class RollbackGuidanceTests(unittest.TestCase):
    def test_rollback_cases(self) -> None:
        cases = json.loads((FIXTURES_DIR / "rollback_cases.json").read_text(encoding="utf-8"))
        for case in cases:
            with self.subTest(case=case["name"]):
                command = [
                    "resolve_rollback.py",
                    "--scope",
                    case["scope"],
                    "--customer-impact",
                    case["customer_impact"],
                    "--data-risk",
                    case["data_risk"],
                    "--format",
                    "json",
                ]
                if case["has_rollback_artifact"]:
                    command.append("--has-rollback-artifact")

                result = run_python_script(*command)
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(result.stdout)

                self.assertEqual(report["status"], case["expected_status"])
                self.assertEqual(report["recommended_strategy"], case["expected_strategy"])
                self.assertEqual(report["suggested_workflow"], case["expected_workflow"])

                for expected in case.get("expected_warning_contains", []):
                    self.assertTrue(any(expected in warning for warning in report["warnings"]))


if __name__ == "__main__":
    unittest.main()
