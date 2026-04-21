from __future__ import annotations

import unittest

from support import build_route_args

import route_preview  # noqa: E402


class SuperpowersRoutePreviewTests(unittest.TestCase):
    def test_small_behavioral_build_routes_through_brainstorm_then_plan(self) -> None:
        report = route_preview.build_report(build_route_args("Add a small checkout endpoint", changed_files=2))
        detected = report["detected"]

        self.assertEqual(detected["forge_skills"][:3], ["brainstorm", "plan", "build"])
        self.assertEqual(detected["required_stage_chain"][:3], ["brainstorm", "plan", "build"])

    def test_visualize_intent_uses_optional_visualize_lens_not_required_stage(self) -> None:
        report = route_preview.build_report(
            build_route_args("Sketch a new checkout screen for tablet with fast touch interactions")
        )
        detected = report["detected"]

        self.assertEqual(detected["forge_skills"], ["brainstorm", "plan"])
        self.assertEqual(detected["required_stage_chain"], ["brainstorm", "plan"])
        self.assertEqual(detected["optional_design_lenses"], ["visualize"])

    def test_large_build_uses_architect_as_optional_lens_not_required_stage(self) -> None:
        report = route_preview.build_report(
            build_route_args(
                "Add a new checkout flow with payment and auth",
                repo_signals=["package.json", "api/"],
            )
        )
        detected = report["detected"]

        self.assertEqual(detected["required_stage_chain"][:3], ["brainstorm", "plan", "build"])
        self.assertNotIn("architect", detected["forge_skills"])
        self.assertIn("architect", detected["optional_design_lenses"])


if __name__ == "__main__":
    unittest.main()
