from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import response_contract  # noqa: E402
import text_utils  # noqa: E402


VIETNAMESE_OUTPUT_CONTRACT = {
    "language": "vi",
    "user_facing_language": "vietnamese",
    "orthography": "vietnamese-diacritics",
    "accent_policy": "required",
    "encoding": "utf-8",
}

HONORIFIC_OUTPUT_CONTRACT = {
    **VIETNAMESE_OUTPUT_CONTRACT,
    "tone_detail": "Gọi Sếp, xưng Em",
}


class ResponseContractTests(unittest.TestCase):
    def test_normalize_text_folds_vietnamese_d_with_stroke(self) -> None:
        self.assertEqual(text_utils.normalize_text("Đánh giá hướng"), "danh gia huong")

    def test_validator_accepts_verified_response(self) -> None:
        report = response_contract.validate_response_contract(
            "I verified: pytest -q passed. Correct because the change only adds contract validation. Fixed: added the response validator.",
            require_evidence_response=True,
        )

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["checks"]["evidence_response"]["mode"], "verified")

    def test_validator_rejects_banned_phrase(self) -> None:
        report = response_contract.validate_response_contract(
            "Good catch! Fixed.",
            require_evidence_response=True,
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("Banned phrase detected" in finding for finding in report["findings"]))

    def test_validator_rejects_mojibake_for_vietnamese_contract(self) -> None:
        report = response_contract.validate_response_contract(
            "KhÃ´ng reproduce duoc nen chac on.",
            output_contract=VIETNAMESE_OUTPUT_CONTRACT,
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("mojibake" in finding.lower() for finding in report["findings"]))

    def test_validator_accepts_vietnamese_verified_response(self) -> None:
        report = response_contract.validate_response_contract(
            "Đã xác minh: `pytest -q` pass. Đúng vì validator mới chỉ siết guardrail output. Đã sửa: bổ sung kiểm tra hợp đồng phản hồi.",
            output_contract=VIETNAMESE_OUTPUT_CONTRACT,
            require_evidence_response=True,
        )

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["checks"]["evidence_response"]["mode"], "verified")

    def test_clarification_requires_exactly_one_question(self) -> None:
        report = response_contract.validate_response_contract(
            "Cần làm rõ: Anh muốn ưu tiên validator trước? Hay ưu tiên routing trước?",
            output_contract=VIETNAMESE_OUTPUT_CONTRACT,
            require_evidence_response=True,
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("exactly one question" in finding for finding in report["findings"]))

    def test_validator_rejects_wrong_honorific_for_tone_detail(self) -> None:
        report = response_contract.validate_response_contract(
            "Em đã xác minh: pytest -q pass. Đúng vì validator đã chạy. Đã sửa: anh sẽ cập nhật lại luồng trả lời.",
            output_contract=HONORIFIC_OUTPUT_CONTRACT,
            require_evidence_response=True,
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("Sếp" in finding or "xưng 'Em'" in finding for finding in report["findings"]))

    def test_validator_accepts_expected_honorific_for_tone_detail(self) -> None:
        report = response_contract.validate_response_contract(
            "Em đã xác minh: pytest -q pass. Đúng vì validator đã chạy. Em đã sửa: từ giờ Em sẽ gọi Sếp đúng theo thiết lập.",
            output_contract=HONORIFIC_OUTPUT_CONTRACT,
            require_evidence_response=True,
        )

        self.assertEqual(report["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
