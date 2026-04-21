from __future__ import annotations

import copy
import json
import os
import shutil
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def resolve_core_root() -> Path:
    if (ROOT_DIR / "scripts").exists() and (ROOT_DIR / "data").exists():
        return ROOT_DIR
    return ROOT_DIR.parents[1] / "forge-core"


CORE_ROOT_DIR = resolve_core_root()
CORE_SCRIPTS_DIR = CORE_ROOT_DIR / "scripts"
DEFAULT_TEST_FORGE_HOME = (CORE_ROOT_DIR / "tests" / "fixtures" / "forge-homes" / "empty").resolve()


def merge_overlay(base: object, overlay: object) -> object:
    if isinstance(base, dict) and isinstance(overlay, dict):
        merged = {key: copy.deepcopy(value) for key, value in base.items()}
        for key, value in overlay.items():
            merged[key] = merge_overlay(merged[key], value) if key in merged else copy.deepcopy(value)
        return merged
    if isinstance(base, list) and isinstance(overlay, list):
        merged = [copy.deepcopy(item) for item in base]
        seen = {json.dumps(item, sort_keys=True, ensure_ascii=False) for item in merged}
        for item in overlay:
            marker = json.dumps(item, sort_keys=True, ensure_ascii=False)
            if marker not in seen:
                seen.add(marker)
                merged.append(copy.deepcopy(item))
        return merged
    return copy.deepcopy(overlay)


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def stage_bundle_root() -> Path:
    stage_root = Path(tempfile.mkdtemp(prefix="forge-antigravity-bundle-"))
    stage_data_dir = stage_root / "data"
    shutil.copytree(CORE_ROOT_DIR / "data", stage_data_dir, dirs_exist_ok=True)
    write_json(
        stage_data_dir / "orchestrator-registry.json",
        merge_overlay(
            load_json(CORE_ROOT_DIR / "data" / "orchestrator-registry.json"),
            load_json(ROOT_DIR / "data" / "orchestrator-registry.json"),
        ),
    )
    for filename in ("output-contracts.json", "routing-locales.json"):
        source = ROOT_DIR / "data" / filename
        if source.exists():
            shutil.copy2(source, stage_data_dir / filename)
    locale_dir = ROOT_DIR / "data" / "routing-locales"
    if locale_dir.exists():
        shutil.copytree(locale_dir, stage_data_dir / "routing-locales", dirs_exist_ok=True)
    return stage_root


if "FORGE_BUNDLE_ROOT" not in os.environ:
    os.environ["FORGE_BUNDLE_ROOT"] = str(stage_bundle_root())

if str(CORE_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_SCRIPTS_DIR))

for module_name in ("common", "preferences", "preferences_contract", "preferences_paths", "route_preview"):
    sys.modules.pop(module_name, None)

import common  # noqa: E402
import route_preview  # noqa: E402


def build_route_args(prompt: str, *, repo_signals: list[str] | None = None, changed_files: int | None = None) -> Namespace:
    return Namespace(
        prompt=prompt,
        repo_signal=repo_signals or [],
        workspace_router=None,
        workspace=None,
        changed_files=changed_files,
        has_harness="auto",
        delegation_preference=None,
        forge_home=DEFAULT_TEST_FORGE_HOME,
        format="json",
        persist=False,
        output_dir=None,
    )


def load_output_contract_profiles() -> dict | None:
    if not common.OUTPUT_CONTRACTS_PATH.exists():
        return None
    payload = json.loads(common.OUTPUT_CONTRACTS_PATH.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def expected_output_contract(extra: object) -> dict[str, object]:
    if not isinstance(extra, dict):
        return {}
    contract: dict[str, object] = {}
    profiles = load_output_contract_profiles()
    language = extra.get("language")
    if isinstance(language, str) and language.strip():
        normalized_language = common.normalize_choice_token(language)
        contract["language"] = normalized_language
        languages = profiles.get("languages") if isinstance(profiles, dict) else None
        profile = languages.get(normalized_language) if isinstance(languages, dict) else None
        if isinstance(profile, dict):
            profile_contract = profile.get("contract")
            if isinstance(profile_contract, dict):
                contract.update(copy.deepcopy(profile_contract))
            default_orthography = profile.get("default_orthography")
            if isinstance(default_orthography, str) and "orthography" not in contract:
                normalized = common.normalize_choice_token(default_orthography)
                contract["orthography"] = normalized
                orthographies = profiles.get("orthographies") if isinstance(profiles, dict) else None
                orthography_profile = orthographies.get(normalized) if isinstance(orthographies, dict) else None
                if isinstance(orthography_profile, dict):
                    contract.update(copy.deepcopy(orthography_profile))
    return contract


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

    # --- Flat build routing ---

    def test_vietnamese_high_risk_keywords_no_longer_activate_spec_review(self) -> None:
        # Flat model: auth/security keywords keep BUILD routing but no longer add a separate spec-review stage
        report = route_preview.build_report(
            build_route_args("Xây dựng module xác thực và bảo mật cho hệ thống thanh toán")
        )

        self.assertEqual(report["detected"]["intent"], "BUILD")
        self.assertIn("build", report["detected"]["forge_skills"])
        self.assertNotIn("spec-review", report["detected"]["forge_skills"])

    def test_vietnamese_migration_keywords_no_longer_activate_spec_review(self) -> None:
        # Flat model: migration keywords keep BUILD routing but no longer add a separate spec-review stage
        report = route_preview.build_report(
            build_route_args("Tạo di trú database để thêm bảng mới cho module mới")
        )

        self.assertEqual(report["detected"]["intent"], "BUILD")
        self.assertIn("build", report["detected"]["forge_skills"])
        self.assertNotIn("spec-review", report["detected"]["forge_skills"])

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

    def test_parallel_safe_prompt_stays_sequential_on_antigravity(self) -> None:
        report = route_preview.build_report(
            build_route_args("Implement many screens and many endpoints in parallel", changed_files=12)
        )

        self.assertEqual(report["detected"]["execution_mode"], "parallel-safe")
        self.assertEqual(report["detected"]["host_capability_tier"], "controller-baseline")
        self.assertEqual(report["detected"]["delegation_strategy"], "sequential-lanes")
        self.assertEqual(report["detected"]["host_skills"], [])


if __name__ == "__main__":
    unittest.main()
