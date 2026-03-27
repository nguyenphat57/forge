from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

SUPPORT_SPEC = importlib.util.spec_from_file_location(
    "forge_codex_overlay_support",
    SCRIPTS_DIR / "support.py",
)
if SUPPORT_SPEC is None or SUPPORT_SPEC.loader is None:
    raise RuntimeError("Unable to load forge-codex overlay support module.")
SUPPORT_MODULE = importlib.util.module_from_spec(SUPPORT_SPEC)
SUPPORT_SPEC.loader.exec_module(SUPPORT_MODULE)

build_route_args = SUPPORT_MODULE.build_route_args
expected_output_contract = SUPPORT_MODULE.expected_output_contract

import common  # noqa: E402
import response_contract  # noqa: E402
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

    def test_vietnamese_direction_question_inserts_brainstorm(self) -> None:
        report = route_preview.build_report(
            build_route_args("Nên chọn hướng web hay native cho luồng thanh toán mới?")
        )

        self.assertEqual(report["detected"]["intent"], "BUILD")
        self.assertEqual(report["detected"]["forge_skills"][0], "brainstorm")
        self.assertIn("vi", report["detected"]["routing_locales"])

    def test_vietnamese_direction_question_without_explicit_locale_keyword_still_inserts_brainstorm(self) -> None:
        report = route_preview.build_report(
            build_route_args("Web hay native là phương án nào cho luồng thanh toán mới?")
        )

        self.assertEqual(report["detected"]["intent"], "BUILD")
        self.assertEqual(report["detected"]["forge_skills"][0], "brainstorm")
        self.assertIn("vi", report["detected"]["routing_locales"])

    def test_vietnamese_backward_compatibility_prompt_triggers_spec_review(self) -> None:
        report = route_preview.build_report(
            build_route_args(
                "Thêm endpoint mới cho client hiện tại, cần giữ tương thích ngược",
                repo_signals=["api/"],
            )
        )

        self.assertEqual(report["detected"]["intent"], "BUILD")
        self.assertIn("spec-review", report["detected"]["forge_skills"])
        self.assertIn("vi", report["detected"]["routing_locales"])

    def test_vietnamese_keep_legacy_api_phrase_triggers_spec_review(self) -> None:
        report = route_preview.build_report(
            build_route_args(
                "Thêm endpoint mới nhưng vẫn giữ API cũ cho client hiện tại",
                repo_signals=["api/"],
            )
        )

        self.assertEqual(report["detected"]["intent"], "BUILD")
        self.assertIn("spec-review", report["detected"]["forge_skills"])
        self.assertIn("vi", report["detected"]["routing_locales"])

    def test_bundle_language_profiles_expand_vietnamese_output_contract(self) -> None:
        contract = common.resolve_output_contract({"language": "vi"})

        self.assertEqual(contract, expected_output_contract({"language": "vi"}))
        self.assertEqual(contract["language"], "vi")
        self.assertEqual(contract["orthography"], "vietnamese-diacritics")
        self.assertEqual(contract["accent_policy"], "required")
        self.assertEqual(contract["encoding"], "utf-8")

    def test_vietnamese_response_contract_rejects_accent_stripped_output(self) -> None:
        contract = common.resolve_output_contract({"language": "vi"})
        report = response_contract.validate_response_contract(
            "Em da xac minh: pytest -q pass. Dung vi da co evidence. Da sua: bo sung validator.",
            output_contract=contract,
            require_evidence_response=True,
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("accent-stripped Vietnamese" in finding for finding in report["findings"]))


if __name__ == "__main__":
    unittest.main()
