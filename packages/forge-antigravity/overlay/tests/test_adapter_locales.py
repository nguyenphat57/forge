from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from support import build_route_args, expected_output_contract  # noqa: E402

import common  # noqa: E402
import route_preview  # noqa: E402


class AdapterLocaleTests(unittest.TestCase):
    def test_vietnamese_build_prompt_routes_with_bundle_locale_pack(self) -> None:
        report = route_preview.build_report(build_route_args("Thêm endpoint thanh toán mới"))

        self.assertEqual(report["detected"]["intent"], "BUILD")
        self.assertIn("build", report["detected"]["forge_skills"])
        self.assertIn("vi", report["detected"]["routing_locales"])

    def test_vietnamese_session_prompt_routes_with_bundle_locale_pack(self) -> None:
        report = route_preview.build_report(build_route_args("Tiếp tục task đang dở"))

        self.assertEqual(report["detected"]["intent"], "SESSION")
        self.assertIn("vi", report["detected"]["routing_locales"])

    def test_bundle_language_profiles_expand_vietnamese_output_contract(self) -> None:
        contract = common.resolve_output_contract({"language": "vi"})

        self.assertEqual(contract, expected_output_contract({"language": "vi"}))
        self.assertEqual(contract["language"], "vi")
        self.assertEqual(contract["orthography"], "vietnamese-diacritics")
        self.assertEqual(contract["accent_policy"], "required")
        self.assertEqual(contract["encoding"], "utf-8")


if __name__ == "__main__":
    unittest.main()
