from __future__ import annotations

import json
import unittest

from support import FIXTURES_DIR, run_python_script
from common import sanitize_error_text, translate_error_text


class ErrorTranslationTests(unittest.TestCase):
    def test_translate_error_matches_known_pattern(self) -> None:
        translation = translate_error_text("Module not found: payments.service")

        self.assertIsNotNone(translation)
        self.assertEqual(translation["status"], "PASS")
        self.assertEqual(translation["category"], "module")
        self.assertIn("missing", translation["human_message"].lower())

    def test_sanitize_error_redacts_sensitive_bits(self) -> None:
        sanitized = sanitize_error_text(
            "Bearer abc123 cannot find module at C:\\Users\\Admin\\secret\\app.py password=hunter2"
        )

        self.assertNotIn("abc123", sanitized)
        self.assertNotIn("hunter2", sanitized)
        self.assertNotIn("C:\\Users\\Admin\\secret\\app.py", sanitized)
        self.assertIn("<redacted>", sanitized)
        self.assertIn("<path>", sanitized)

    def test_translate_error_script_cases(self) -> None:
        cases = json.loads((FIXTURES_DIR / "error_translation_cases.json").read_text(encoding="utf-8"))
        for case in cases:
            with self.subTest(case=case["name"]):
                result = run_python_script(
                    "translate_error.py",
                    "--error-text",
                    case["error_text"],
                    "--format",
                    "json",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                translation = payload["translation"]

                self.assertEqual(payload["status"], case["expected_status"])
                self.assertEqual(translation["category"], case["expected_category"])
                self.assertIn(case["expected_message_contains"], translation["human_message"].lower())
                self.assertIn(case["expected_action_contains"], translation["suggested_action"].lower())


if __name__ == "__main__":
    unittest.main()
