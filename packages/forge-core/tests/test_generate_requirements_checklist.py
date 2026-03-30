from __future__ import annotations

import json
import unittest

from support import run_python_script


class GenerateRequirementsChecklistTests(unittest.TestCase):
    def test_checklist_warns_on_ambiguous_requirement(self) -> None:
        result = run_python_script(
            "generate_requirements_checklist.py",
            "--requirement",
            "The checkout flow should be fast and easy for everyone.",
            "--format",
            "json",
        )

        self.assertEqual(result.returncode, 1)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "WARN")
        self.assertEqual(report["requirements"][0]["checks"]["ambiguity"], "WARN")

    def test_checklist_passes_for_measurable_and_testable_requirement(self) -> None:
        result = run_python_script(
            "generate_requirements_checklist.py",
            "--requirement",
            "When checkout fails, retry within 30 seconds and verify with pytest.",
            "--format",
            "json",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["requirements"][0]["checks"]["measurability"], "PASS")
        self.assertEqual(report["requirements"][0]["checks"]["testability"], "PASS")


if __name__ == "__main__":
    unittest.main()
