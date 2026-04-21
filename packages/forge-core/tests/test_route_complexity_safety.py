from __future__ import annotations

import unittest

from support import build_route_args

import route_preview  # noqa: E402


class RouteComplexitySafetyTests(unittest.TestCase):
    def test_small_file_count_with_blast_radius_escalates_to_medium(self) -> None:
        report = route_preview.build_report(
            build_route_args(
                "Add a small public API helper",
                repo_signals=["packages/core/api.py"],
                changed_files=1,
            )
        )
        detected = report["detected"]

        self.assertEqual(detected["intent"], "BUILD")
        self.assertEqual(detected["complexity"], "medium")
        self.assertEqual(detected["complexity_audit"]["initial_complexity"], "small")
        self.assertTrue(detected["complexity_audit"]["escalated"])
        self.assertIn(
            "blast-radius: public or shared interface",
            detected["complexity_audit"]["reasons"],
        )
        self.assertTrue(detected["baseline_proof_required"])
        self.assertTrue(detected["review_artifact_required"])
        self.assertEqual(detected["packet_mode"], "standard")

    def test_accumulated_small_tasks_force_holistic_review(self) -> None:
        report = route_preview.build_report(
            build_route_args(
                "Update checkout docs",
                changed_files=1,
                recent_small_tasks=5,
            )
        )
        detected = report["detected"]

        self.assertEqual(detected["complexity"], "medium")
        self.assertEqual(detected["complexity_audit"]["initial_complexity"], "small")
        self.assertTrue(detected["complexity_audit"]["escalated"])
        self.assertIn(
            "accumulation: recent small-task threshold reached",
            detected["complexity_audit"]["reasons"],
        )
        self.assertTrue(detected["review_artifact_required"])

    def test_changed_files_since_review_threshold_forces_holistic_review(self) -> None:
        report = route_preview.build_report(
            build_route_args(
                "Update checkout docs",
                changed_files=1,
                changed_files_since_review=10,
            )
        )
        detected = report["detected"]

        self.assertEqual(detected["complexity"], "medium")
        self.assertIn(
            "accumulation: changed-files-since-review threshold reached",
            detected["complexity_audit"]["reasons"],
        )
        self.assertTrue(detected["review_artifact_required"])

    def test_critical_runtime_surface_escalates_to_large(self) -> None:
        report = route_preview.build_report(
            build_route_args(
                "Make a small auth permission fix",
                repo_signals=["packages/core/auth.py"],
                changed_files=1,
            )
        )
        detected = report["detected"]

        self.assertEqual(detected["complexity"], "large")
        self.assertIn(
            "blast-radius: critical runtime surface",
            detected["complexity_audit"]["reasons"],
        )
        self.assertTrue(detected["review_artifact_required"])

    def test_release_keyword_alone_does_not_escalate_deploy_to_large(self) -> None:
        report = route_preview.build_report(build_route_args("Deploy the app to production"))
        detected = report["detected"]

        self.assertEqual(detected["intent"], "DEPLOY")
        self.assertEqual(detected["complexity"], "medium")
        self.assertFalse(detected["complexity_audit"]["escalated"])

    def test_text_formatter_handles_legacy_reports_without_audit(self) -> None:
        report = route_preview.build_report(build_route_args("Update checkout docs", changed_files=1))
        report["detected"].pop("complexity_audit")

        text = route_preview.format_text(report)

        self.assertIn("Complexity authority: heuristic", text)


if __name__ == "__main__":
    unittest.main()
