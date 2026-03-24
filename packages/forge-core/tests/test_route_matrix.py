from __future__ import annotations

import unittest

from support import build_route_args, load_json_fixture, workspace_fixture

import route_preview  # noqa: E402


class RoutePreviewSmokeMatrixTests(unittest.TestCase):
    def test_route_preview_cases(self) -> None:
        for case in load_json_fixture("route_preview_cases.json"):
            with self.subTest(case=case["name"]):
                workspace_router = None
                if case.get("workspace_fixture") and case.get("workspace_router"):
                    workspace_router = workspace_fixture(case["workspace_fixture"]) / case["workspace_router"]

                report = route_preview.build_report(
                    build_route_args(
                        case["prompt"],
                        repo_signals=case.get("repo_signals"),
                        workspace_router=workspace_router,
                        changed_files=case.get("changed_files"),
                        has_harness=case.get("has_harness", "auto"),
                    )
                )
                detected = report["detected"]
                host_supports_subagents = detected.get("host_supports_subagents", False)

                self.assertEqual(detected["intent"], case["expected_intent"])
                self.assertEqual(detected["complexity"], case["expected_complexity"])
                self.assertEqual(detected["verification_profile"], case.get("expected_verification_profile"))

                if "expected_skills" in case:
                    self.assertEqual(detected["forge_skills"], case["expected_skills"])
                if "expected_skill_prefix" in case:
                    expected_prefix = case["expected_skill_prefix"]
                    self.assertEqual(detected["forge_skills"][: len(expected_prefix)], expected_prefix)
                if "expected_domain_skills" in case:
                    self.assertEqual(detected["domain_skills"], case["expected_domain_skills"])
                if "expected_local_companions" in case:
                    self.assertEqual(detected["local_companions"], case["expected_local_companions"])
                if "expected_quality_profile" in case:
                    self.assertEqual(detected["quality_profile"], case["expected_quality_profile"])
                if "expected_execution_pipeline" in case:
                    self.assertEqual(detected["execution_pipeline"], case["expected_execution_pipeline"])
                if "expected_delegation_strategy" in case:
                    expected_strategy = case["expected_delegation_strategy_when_subagents"] if host_supports_subagents and "expected_delegation_strategy_when_subagents" in case else case["expected_delegation_strategy"]
                    self.assertEqual(detected["delegation_strategy"], expected_strategy)
                if "expected_host_skills" in case:
                    self.assertEqual(detected["host_skills"], case["expected_host_skills"])
                if "expected_host_skills_when_subagents" in case and host_supports_subagents:
                    self.assertEqual(detected["host_skills"], case["expected_host_skills_when_subagents"])


if __name__ == "__main__":
    unittest.main()
