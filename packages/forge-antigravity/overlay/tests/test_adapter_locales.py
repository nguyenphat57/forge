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

    # --- Brainstorm gate ---

    def test_brainstorm_gate_fires_on_vietnamese_ambiguity_keywords(self) -> None:
        # "ý tưởng" (idea) + "nên chọn" (should choose) → ambiguity → brainstorm gate
        report = route_preview.build_report(
            build_route_args("Có mấy ý tưởng cho tính năng thanh toán, nên chọn hướng nào?")
        )

        self.assertEqual(report["detected"]["intent"], "BUILD")
        self.assertIn("brainstorm", report["detected"]["forge_skills"])
        # brainstorm should appear before plan
        skills = report["detected"]["forge_skills"]
        self.assertLess(skills.index("brainstorm"), skills.index("plan"))

    def test_brainstorm_gate_fires_on_non_diacritics_vietnamese(self) -> None:
        # Non-diacritics variant: "y tuong", "nen chon"
        report = route_preview.build_report(
            build_route_args("Co may y tuong cho tinh nang moi, nen chon huong nao?")
        )

        self.assertEqual(report["detected"]["intent"], "BUILD")
        self.assertIn("brainstorm", report["detected"]["forge_skills"])

    # --- Spec-review gate ---

    def test_spec_review_gate_fires_on_vietnamese_high_risk_keywords(self) -> None:
        # "bảo mật" (security) + "xác thực" (auth) → high-risk → spec-review gate
        report = route_preview.build_report(
            build_route_args("Xây dựng module xác thực và bảo mật cho hệ thống thanh toán")
        )

        self.assertEqual(report["detected"]["intent"], "BUILD")
        self.assertIn("spec-review", report["detected"]["forge_skills"])

    def test_spec_review_gate_fires_on_vietnamese_migration_keywords(self) -> None:
        # "di trú" (migration) → spec-review gate
        report = route_preview.build_report(
            build_route_args("Tạo di trú database để thêm bảng mới cho module mới")
        )

        self.assertEqual(report["detected"]["intent"], "BUILD")
        self.assertIn("spec-review", report["detected"]["forge_skills"])

    # --- Complexity detection ---

    def test_vietnamese_large_complexity_keywords(self) -> None:
        # "thanh toán" (payment) + "kiến trúc" (architecture) → large
        report = route_preview.build_report(
            build_route_args("Thiết kế lại kiến trúc thanh toán")
        )

        self.assertEqual(report["detected"]["complexity"], "large")

    def test_vietnamese_small_complexity_keywords(self) -> None:
        # "sửa css" (fix css) → small
        report = route_preview.build_report(
            build_route_args("Sửa css cho nút đăng nhập")
        )

        self.assertEqual(report["detected"]["complexity"], "small")

    # --- Change type hints ---

    def test_vietnamese_non_behavioral_change_type(self) -> None:
        # "tài liệu" (docs) + "cấu hình" (config) → non_behavioral
        report = route_preview.build_report(
            build_route_args("Cập nhật tài liệu và cấu hình cho project")
        )

        self.assertEqual(report["detected"]["verification_profile"], "non_behavioral")

    def test_vietnamese_behavioral_change_type(self) -> None:
        # "lỗi" (bug) + "tính năng" (feature) → behavioral
        report = route_preview.build_report(
            build_route_args("Sửa lỗi tính năng đăng nhập bị crash")
        )

        self.assertIn(
            report["detected"]["verification_profile"],
            ("behavioral_with_harness", "behavioral_reproduction_first"),
        )

    # --- Host capabilities ---

    def test_host_capabilities_reflects_antigravity_subagent_support(self) -> None:
        import skill_routing  # noqa: E402

        registry = skill_routing.load_registry()
        host = registry["host_capabilities"]

        self.assertEqual(host["active_tier"], "controller-baseline")
        self.assertFalse(host["supports_subagents"])
        self.assertFalse(host["supports_parallel_subagents"])
        self.assertIsNone(host["subagent_dispatch_skill"])


if __name__ == "__main__":
    unittest.main()
