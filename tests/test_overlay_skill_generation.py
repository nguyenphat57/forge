from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import skill_bundle_composer  # noqa: E402


class OverlaySkillGenerationTests(unittest.TestCase):
    def _raw_line_count(self, path: Path) -> int:
        text = path.read_text(encoding="utf-8")
        return text.count("\n") + (0 if text.endswith("\n") else 1)

    def test_generated_overlay_skills_are_fresh(self) -> None:
        report = skill_bundle_composer.ensure_generated_overlay_skills(check=True)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["stale_outputs"], [])
        self.assertEqual(len(report["artifacts"]), 2)

    def test_generated_overlay_skills_match_composer_output(self) -> None:
        for spec in skill_bundle_composer.adapter_skill_specs():
            bundle = str(spec["bundle"])
            output_path = Path(spec["output_path"])
            with self.subTest(bundle=bundle):
                self.assertTrue(output_path.exists())
                self.assertEqual(
                    output_path.read_text(encoding="utf-8"),
                    skill_bundle_composer.compose_adapter_skill(bundle),
                )

    def test_adapter_delta_files_do_not_duplicate_shared_core_sections(self) -> None:
        for spec in skill_bundle_composer.adapter_skill_specs():
            delta_path = Path(spec["delta_path"])
            delta_text = delta_path.read_text(encoding="utf-8")
            with self.subTest(delta=delta_path.name):
                for heading in skill_bundle_composer.SHARED_SECTION_HEADINGS:
                    self.assertNotIn(f"## {heading}", delta_text)

    def test_thin_skill_line_budgets_remain_calibrated(self) -> None:
        budgets = {
            ROOT_DIR / "packages" / "forge-core" / "SKILL.md": 100,
            ROOT_DIR / "packages" / "forge-codex" / "overlay" / "SKILL.delta.md": 50,
            ROOT_DIR / "packages" / "forge-codex" / "overlay" / "SKILL.md": 110,
            ROOT_DIR / "packages" / "forge-antigravity" / "overlay" / "SKILL.delta.md": 60,
            ROOT_DIR / "packages" / "forge-antigravity" / "overlay" / "SKILL.md": 120,
        }
        for path, budget in budgets.items():
            with self.subTest(path=path.relative_to(ROOT_DIR).as_posix()):
                self.assertLessEqual(self._raw_line_count(path), budget)
