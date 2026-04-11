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
                        workspace=workspace_fixture(case["workspace_fixture"]) if case.get("workspace_fixture") and not case.get("workspace_router") else None,
                        changed_files=case.get("changed_files"),
                        has_harness=case.get("has_harness", "auto"),
                        delegation_preference=case.get("delegation_preference"),
                    )
                )
                detected = report["detected"]
                host_supports_subagents = detected.get("host_supports_subagents", False)

                self.assertEqual(detected["intent"], case["expected_intent"])
                self.assertEqual(detected["complexity"], case["expected_complexity"])
                self.assertEqual(detected["verification_profile"], case.get("expected_verification_profile"))
                if "expected_session_mode" in case:
                    self.assertEqual(detected["session_mode"], case["expected_session_mode"])
                if "expected_profile" in case:
                    self.assertEqual(detected["profile"], case["expected_profile"])

                if "expected_skills" in case:
                    self.assertEqual(detected["forge_skills"], case["expected_skills"])
                if "expected_skill_prefix" in case:
                    expected_prefix = case["expected_skill_prefix"]
                    self.assertEqual(detected["forge_skills"][: len(expected_prefix)], expected_prefix)
                if "expected_required_stage_chain" in case:
                    self.assertEqual(detected["required_stage_chain"], case["expected_required_stage_chain"])
                if "expected_required_stage_prefix" in case:
                    expected_prefix = case["expected_required_stage_prefix"]
                    self.assertEqual(detected["required_stage_chain"][: len(expected_prefix)], expected_prefix)
                if "expected_local_companions" in case:
                    self.assertEqual(detected["local_companions"], case["expected_local_companions"])
                if "expected_quality_profile" in case:
                    self.assertEqual(detected["quality_profile"], case["expected_quality_profile"])
                if "expected_execution_pipeline" in case:
                    self.assertEqual(detected["execution_pipeline"], case["expected_execution_pipeline"])
                if "expected_resolved_delegation_preference" in case:
                    self.assertEqual(
                        detected["resolved_delegation_preference"],
                        case["expected_resolved_delegation_preference"],
                    )
                if "expected_effective_delegation_mode" in case:
                    self.assertEqual(
                        detected["effective_delegation_mode"],
                        case["expected_effective_delegation_mode"],
                    )
                if "expected_delegation_strategy" in case:
                    expected_strategy = case["expected_delegation_strategy_when_subagents"] if host_supports_subagents and "expected_delegation_strategy_when_subagents" in case else case["expected_delegation_strategy"]
                    self.assertEqual(detected["delegation_strategy"], expected_strategy)
                if "expected_host_skills" in case:
                    self.assertEqual(detected["host_skills"], case["expected_host_skills"])
                if "expected_host_skills_when_subagents" in case and host_supports_subagents:
                    self.assertEqual(detected["host_skills"], case["expected_host_skills_when_subagents"])
                if "expected_process_precheck_required" in case:
                    self.assertEqual(detected["process_precheck_required"], case["expected_process_precheck_required"])
                if "expected_baseline_proof_required" in case:
                    self.assertEqual(detected["baseline_proof_required"], case["expected_baseline_proof_required"])
                if "expected_verify_change_required" in case:
                    self.assertEqual(detected["verify_change_required"], case["expected_verify_change_required"])
                if "expected_review_artifact_required" in case:
                    self.assertEqual(detected["review_artifact_required"], case["expected_review_artifact_required"])
                if "expected_durable_process_artifacts_required" in case:
                    self.assertEqual(
                        detected["durable_process_artifacts_required"],
                        case["expected_durable_process_artifacts_required"],
                    )
                if "expected_isolation_recommendation" in case:
                    self.assertEqual(detected["isolation_recommendation"], case["expected_isolation_recommendation"])


if __name__ == "__main__":
    unittest.main()
