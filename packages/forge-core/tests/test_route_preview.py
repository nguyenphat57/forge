from __future__ import annotations

import copy
import json
import os
import sys
import unittest
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from support import reference_companion_environment


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import common  # noqa: E402
import route_preview  # noqa: E402


class RoutePreviewTests(unittest.TestCase):
    def build_args(
        self,
        prompt: str,
        *,
        repo_signals: list[str] | None = None,
        workspace_router: Path | None = None,
        workspace: Path | None = None,
        changed_files: int | None = None,
        has_harness: str = "auto",
        delegation_preference: str | None = None,
        forge_home: Path | None = None,
    ) -> Namespace:
        if forge_home is None:
            forge_home = ROOT_DIR / "tests" / "fixtures" / "forge-homes" / "empty"
        return Namespace(
            prompt=prompt,
            repo_signal=repo_signals or [],
            workspace_router=workspace_router,
            workspace=workspace,
            changed_files=changed_files,
            has_harness=has_harness,
            delegation_preference=delegation_preference,
            forge_home=forge_home,
            format="json",
            persist=False,
            output_dir=None,
        )

    def test_review_prompt_routes_to_review_intent(self) -> None:
        report = route_preview.build_report(self.build_args("Review code before merge"))

        self.assertEqual(report["detected"]["intent"], "REVIEW")
        self.assertEqual(report["detected"]["profile"], "solo-internal")
        self.assertEqual(report["detected"]["forge_skills"], ["review", "secure"])
        self.assertEqual(report["detected"]["required_stage_chain"], ["review"])

    def test_build_prompt_routes_to_build_intent(self) -> None:
        report = route_preview.build_report(self.build_args("Add a new checkout endpoint"))

        self.assertEqual(report["detected"]["intent"], "BUILD")
        self.assertIn("build", report["detected"]["forge_skills"])
        self.assertIn(
            {
                "skill": "build",
                "reason_code": "default_chain",
                "reason": "selected by the default chain for this intent and complexity.",
            },
            report["detected"]["skill_selection_rationale"],
        )

    def test_medium_build_requires_change_artifacts(self) -> None:
        report = route_preview.build_report(
            self.build_args(
                "Implement a new checkout feature",
                changed_files=3,
            )
        )

        self.assertEqual(report["detected"]["complexity"], "medium")
        self.assertEqual(report["detected"]["profile"], "solo-internal")
        self.assertEqual(
            report["detected"]["required_stage_chain"],
            ["plan", "spec-review", "build", "test", "self-review", "secure", "quality-gate"],
        )
        self.assertEqual(report["detected"]["execution_pipeline"], "implementer-spec-quality")
        self.assertFalse(report["detected"]["change_artifacts_required"])
        self.assertTrue(report["detected"]["durable_process_artifacts_required"])
        self.assertTrue(report["detected"]["process_precheck_required"])
        self.assertTrue(report["detected"]["baseline_proof_required"])
        self.assertFalse(report["detected"]["verify_change_required"])
        self.assertTrue(report["detected"]["review_artifact_required"])
        self.assertEqual(report["detected"]["isolation_recommendation"], "worktree")
        self.assertIsNotNone(report["detected"]["baseline_verification"])
        self.assertEqual(report["detected"]["worktree_bootstrap"]["helper"], "prepare_worktree.py")
        self.assertEqual(
            report["detected"]["review_sequence"],
            [
                {"sequence_index": 1, "lane": "implementer", "review_kind": None, "depends_on": []},
                {"sequence_index": 2, "lane": "spec-reviewer", "review_kind": "spec-compliance", "depends_on": ["implementer"]},
                {"sequence_index": 3, "lane": "quality-reviewer", "review_kind": "quality-pass", "depends_on": ["spec-reviewer"]},
            ],
        )

    def test_small_non_behavioral_build_routes_through_plan_before_build(self) -> None:
        report = route_preview.build_report(self.build_args("Update checkout docs", changed_files=2))

        self.assertEqual(report["detected"]["intent"], "BUILD")
        self.assertEqual(report["detected"]["complexity"], "small")
        self.assertEqual(report["detected"]["forge_skills"], ["plan", "build", "test"])
        self.assertEqual(report["detected"]["required_stage_chain"], ["plan", "build", "test"])
        self.assertFalse(report["detected"]["durable_process_artifacts_required"])
        self.assertFalse(report["detected"]["process_precheck_required"])
        self.assertFalse(report["detected"]["baseline_proof_required"])
        self.assertFalse(report["detected"]["verify_change_required"])
        self.assertFalse(report["detected"]["review_artifact_required"])
        self.assertEqual(report["detected"]["isolation_recommendation"], "same-tree")
        self.assertIsNone(report["detected"]["baseline_verification"])
        self.assertIsNone(report["detected"]["worktree_bootstrap"])

    def test_small_visualize_routes_through_plan_before_visualize(self) -> None:
        report = route_preview.build_report(self.build_args("Sketch a small checkout layout tweak", changed_files=1))

        self.assertEqual(report["detected"]["intent"], "VISUALIZE")
        self.assertEqual(report["detected"]["complexity"], "small")
        self.assertEqual(report["detected"]["forge_skills"], ["plan", "visualize"])
        self.assertEqual(report["detected"]["required_stage_chain"], ["plan", "visualize"])
        self.assertFalse(report["detected"]["durable_process_artifacts_required"])
        self.assertTrue(report["detected"]["process_precheck_required"])
        self.assertFalse(report["detected"]["baseline_proof_required"])
        self.assertFalse(report["detected"]["verify_change_required"])
        self.assertFalse(report["detected"]["review_artifact_required"])
        self.assertIsNone(report["detected"]["isolation_recommendation"])
        self.assertIsNone(report["detected"]["baseline_verification"])
        self.assertIsNone(report["detected"]["worktree_bootstrap"])

    def test_small_behavioral_build_requires_process_precheck(self) -> None:
        report = route_preview.build_report(self.build_args("Add a small checkout endpoint", changed_files=2))

        self.assertEqual(report["detected"]["intent"], "BUILD")
        self.assertEqual(report["detected"]["complexity"], "small")
        self.assertTrue(report["detected"]["process_precheck_required"])
        self.assertFalse(report["detected"]["baseline_proof_required"])
        self.assertFalse(report["detected"]["verify_change_required"])
        self.assertFalse(report["detected"]["durable_process_artifacts_required"])

    def test_session_prompt_skips_edit_verification_profile(self) -> None:
        report = route_preview.build_report(self.build_args("Continue the task in progress"))
        active_routing_locales = common.routing_locale_names()
        expected_routing_locales = ", ".join(active_routing_locales) if active_routing_locales else "(none)"

        self.assertEqual(report["detected"]["intent"], "SESSION")
        self.assertEqual(report["detected"]["session_mode"], "restore")
        self.assertEqual(report["detected"]["routing_locales"], active_routing_locales)
        self.assertIsNone(report["detected"]["verification_profile"])
        self.assertIsNone(report["verification"])
        self.assertIn("Verification profile: (n/a)", route_preview.format_text(report))
        self.assertIn(f"Routing locales: {expected_routing_locales}", route_preview.format_text(report))
        self.assertIn("Session mode: restore", route_preview.format_text(report))

    def test_save_context_prompt_detects_save_session_mode(self) -> None:
        report = route_preview.build_report(
            self.build_args("Save context for this task before I close the window")
        )

        self.assertEqual(report["detected"]["intent"], "SESSION")
        self.assertEqual(report["detected"]["session_mode"], "save")

    def test_mixed_english_review_prompt_routes_to_review_intent(self) -> None:
        report = route_preview.build_report(self.build_args("Review the checkout flow before merge"))

        self.assertEqual(report["detected"]["intent"], "REVIEW")
        self.assertEqual(report["detected"]["forge_skills"], ["review", "secure"])
        self.assertEqual(report["detected"]["required_stage_chain"], ["review"])

    def test_direction_question_inserts_brainstorm_without_explicit_keyword(self) -> None:
        report = route_preview.build_report(
            self.build_args("Should we use web or native for the new checkout flow?")
        )

        self.assertEqual(report["detected"]["intent"], "BUILD")
        self.assertEqual(report["detected"]["forge_skills"][0], "brainstorm")
        self.assertEqual(report["detected"]["skill_selection_rationale"][0]["skill"], "brainstorm")
        self.assertEqual(report["detected"]["skill_selection_rationale"][0]["reason_code"], "default_chain")

    def test_backward_compatibility_boundary_inserts_spec_review(self) -> None:
        report = route_preview.build_report(
            self.build_args(
                "Add a new endpoint for existing clients and keep backward compatibility",
                repo_signals=["api/"],
            )
        )

        self.assertEqual(report["detected"]["intent"], "BUILD")
        self.assertIn("spec-review", report["detected"]["forge_skills"])

    def test_public_release_resolves_solo_public_profile(self) -> None:
        report = route_preview.build_report(
            self.build_args("Deploy the app to external users with a public launch")
        )

        self.assertEqual(report["detected"]["intent"], "DEPLOY")
        self.assertEqual(report["detected"]["profile"], "solo-public")
        self.assertEqual(
            report["detected"]["required_stage_chain"],
            ["review-pack", "self-review", "secure", "quality-gate", "release-doc-sync", "release-readiness", "deploy", "adoption-check"],
        )
        self.assertEqual(
            report["detected"]["forge_skills"],
            ["review-pack", "review", "secure", "quality-gate", "release-doc-sync", "release-readiness", "deploy", "adoption-check"],
        )

    def test_public_release_without_broad_rollout_marker_skips_release_readiness(self) -> None:
        report = route_preview.build_report(
            self.build_args("Deploy the app to external users from staging")
        )

        self.assertEqual(report["detected"]["intent"], "DEPLOY")
        self.assertEqual(report["detected"]["profile"], "solo-public")
        self.assertEqual(
            report["detected"]["required_stage_chain"],
            ["review-pack", "self-review", "secure", "quality-gate", "release-doc-sync", "deploy", "adoption-check"],
        )
        self.assertNotIn("release-readiness", report["detected"]["forge_skills"])

    def test_runtime_signal_can_select_local_companion(self) -> None:
        with TemporaryDirectory() as temp_dir:
            router_path = Path(temp_dir) / "workspace-router.md"
            router_path.write_text(
                "\n".join(
                    [
                        "## Scope Policy",
                        "Global orchestrator is `forge-runtime`.",
                        "## Local Skill Inventory",
                        "- `python-fastapi`",
                        "## Routing Map",
                        "Use `python-fastapi` for Python API work.",
                    ]
                ),
                encoding="utf-8",
            )

            report = route_preview.build_report(
                self.build_args(
                    "Implement endpoint",
                    repo_signals=["pyproject.toml"],
                    workspace_router=router_path,
                )
            )

        self.assertIn("python-fastapi", report["detected"]["local_companions"])

    def test_review_prompt_can_pull_explicit_local_companion(self) -> None:
        with TemporaryDirectory() as temp_dir:
            router_path = Path(temp_dir) / "workspace-router.md"
            router_path.write_text(
                "\n".join(
                    [
                        "## Scope Policy",
                        "Global orchestrator is `forge-runtime`.",
                        "## Local Skill Inventory",
                        "- `capacitor-android`",
                        "## Routing Map",
                        "Use `capacitor-android` for Android shell work.",
                    ]
                ),
                encoding="utf-8",
            )

            report = route_preview.build_report(
                self.build_args(
                    "Review Android flow before merge",
                    repo_signals=["package.json", "capacitor.config.ts", "android"],
                    workspace_router=router_path,
                )
            )

        self.assertEqual(report["detected"]["intent"], "REVIEW")
        self.assertIn("capacitor-android", report["detected"]["local_companions"])

    def test_route_preview_detects_first_party_nextjs_companion(self) -> None:
        with reference_companion_environment() as (_, env):
            with patch.dict(os.environ, env):
                report = route_preview.build_report(
                    self.build_args(
                        "Add a new Next.js checkout page with Prisma-backed persistence",
                        repo_signals=["package.json", "tsconfig.json", "next.config.ts", "prisma/schema.prisma"],
                    )
                )

            self.assertIn("nextjs-typescript-postgres", report["detected"]["first_party_companions"])
            self.assertIn("nextjs-typescript-postgres", report["activation_line"])

    def test_parallel_safe_host_can_activate_subagent_dispatch_skill(self) -> None:
        registry = copy.deepcopy(route_preview.load_registry())
        registry["host_capabilities"] = {
            "active_tier": "parallel-workers",
            "supports_subagents": True,
            "supports_parallel_subagents": True,
            "subagent_dispatch_skill": "dispatch-subagents",
            "delegation_contract": [
                "Fresh packet per delegated slice.",
                "Explicit ownership and write scope.",
                "Return changed files, verification, and residual risk.",
            ],
        }

        with patch.object(route_preview, "load_registry", return_value=registry):
            report = route_preview.build_report(
                self.build_args(
                    "Implement many screens and many endpoints in parallel",
                    changed_files=12,
                    delegation_preference="auto",
                )
            )

        self.assertEqual(report["detected"]["execution_mode"], "parallel-safe")
        self.assertEqual(report["detected"]["delegation_strategy"], "parallel-split")
        self.assertEqual(report["detected"]["host_capability_tier"], "parallel-workers")
        self.assertEqual(report["detected"]["resolved_delegation_preference"], "auto")
        self.assertEqual(report["detected"]["effective_delegation_mode"], "parallel-workers")
        self.assertEqual(report["detected"]["host_dispatch_mode"], "parallel-workers")
        self.assertEqual(report["detected"]["host_skills"], ["dispatch-subagents"])
        self.assertEqual(report["detected"]["browser_qa_classification"], "optional-accelerator")
        self.assertEqual(report["detected"]["browser_qa_scope"], ["multi-surface frontend or workflow slice"])
        self.assertEqual(report["delegation_plan"]["activation_skill"], "dispatch-subagents")
        self.assertEqual(report["delegation_plan"]["dispatch_mode"], "parallel-workers")
        self.assertEqual(report["delegation_plan"]["host_capability_tier"], "parallel-workers")
        self.assertEqual(report["delegation_plan"]["resolved_delegation_preference"], "auto")
        self.assertEqual(report["delegation_plan"]["effective_delegation_mode"], "parallel-workers")
        self.assertEqual(
            report["delegation_plan"]["packet_template"]["required_fields"],
            [
                "packet_id",
                "packet_mode",
                "parent_packet",
                "source_of_truth",
                "goal",
                "current_slice_or_review_question",
                "exact_files_or_paths_in_scope",
                "owned_files_or_write_scope",
                "depends_on_packets",
                "unblocks_packets",
                "merge_target",
                "merge_strategy",
                "overlap_risk_status",
                "write_scope_conflicts",
                "review_readiness",
                "merge_readiness",
                "completion_gate",
                "baseline_or_clean_start_proof",
                "red_proof",
                "out_of_scope_for_this_slice",
                "reopen_conditions",
                "files_to_avoid",
                "allowed_reads_or_supporting_artifacts",
                "proof_before_progress",
                "verification_to_rerun",
                "browser_qa_classification",
                "browser_qa_scope",
                "browser_qa_status",
                "blockers",
                "residual_risk",
                "next_steps",
            ],
        )
        self.assertEqual(
            report["delegation_plan"]["packet_template"]["status_values"],
            ["DONE", "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED"],
        )
        self.assertEqual(
            report["delegation_plan"]["packet_blueprints"],
            [
                {
                    "lane": "implementer",
                    "packet_type": "slice-worker",
                    "runtime_role": "worker",
                    "read_only": False,
                    "scope_rule": "One packet per independent slice with non-overlapping write ownership.",
                    "review_kind": None,
                    "sequence_index": 1,
                    "depends_on": [],
                }
            ],
        )

    def test_frontend_build_gets_browser_qa_eligibility_without_forcing_required_status(self) -> None:
        report = route_preview.build_report(
            self.build_args(
                "Implement checkout page flow with form validation and responsive states",
                repo_signals=["package.json", "src/", ".tsx"],
                changed_files=4,
            )
        )

        self.assertEqual(report["detected"]["intent"], "BUILD")
        self.assertEqual(report["detected"]["browser_qa_classification"], "optional-accelerator")
        self.assertIn("ui or workflow verification", report["detected"]["browser_qa_scope"])
        self.assertNotIn("domain_skills", report["detected"])
        self.assertNotIn("frontend", report["activation_line"])
        self.assertNotIn("Domain skills:", route_preview.format_text(report))

    def test_explicit_browser_flow_can_mark_packet_as_browser_required(self) -> None:
        report = route_preview.build_report(
            self.build_args(
                "Debug the multi-step checkout flow in browser with screenshot evidence",
                repo_signals=["package.json", "src/", ".tsx"],
                changed_files=5,
            )
        )

        self.assertEqual(report["detected"]["intent"], "DEBUG")
        self.assertEqual(report["detected"]["browser_qa_classification"], "required-for-this-packet")
        self.assertIn("explicit browser reproduction", report["detected"]["browser_qa_scope"])

    def test_backend_risk_prompt_keeps_spec_review_without_backend_skill_surface(self) -> None:
        report = route_preview.build_report(
            self.build_args(
                "Add a new checkout flow with payment and auth",
                repo_signals=["package.json", "api/"],
            )
        )

        self.assertEqual(report["detected"]["intent"], "BUILD")
        self.assertIn("spec-review", report["detected"]["forge_skills"])
        self.assertNotIn("domain_skills", report["detected"])
        self.assertNotIn("backend", report["activation_line"])
        self.assertNotIn("Domain skills:", route_preview.format_text(report))

    def test_review_lane_host_gets_packetized_independent_reviewer_plan(self) -> None:
        registry = copy.deepcopy(route_preview.load_registry())
        registry["host_capabilities"] = {
            "active_tier": "review-lane-subagents",
            "supports_subagents": True,
            "supports_parallel_subagents": False,
            "subagent_dispatch_skill": "dispatch-subagents",
            "delegation_contract": [
                "Fresh packet per delegated slice.",
                "Explicit ownership and write scope.",
                "Return changed files, verification, and residual risk.",
            ],
        }

        strategy, plan, host_skills = route_preview.choose_delegation_plan(
            "DEBUG",
            "single-threaded",
            "implementer-quality",
            registry,
            "review-lanes",
        )

        self.assertEqual(strategy, "independent-reviewer")
        self.assertEqual(host_skills, ["dispatch-subagents"])
        self.assertEqual(plan["dispatch_mode"], "independent-reviewers")
        self.assertEqual(plan["host_capability_tier"], "review-lane-subagents")
        self.assertEqual(plan["resolved_delegation_preference"], "review-lanes")
        self.assertEqual(plan["effective_delegation_mode"], "review-lane-subagents")
        self.assertEqual(
            plan["packet_blueprints"],
            [
                {
                    "lane": "implementer",
                    "packet_type": "implementer-pass",
                    "runtime_role": "worker",
                    "read_only": False,
                    "scope_rule": "Owns the implementation slice with explicit file scope.",
                    "review_kind": None,
                    "sequence_index": 1,
                    "depends_on": [],
                },
                {
                    "lane": "quality-reviewer",
                    "packet_type": "reviewer-pass",
                    "runtime_role": "default",
                    "read_only": True,
                    "scope_rule": "Read-only findings pass over implementer evidence and changed files.",
                    "review_kind": "quality-pass",
                    "sequence_index": 2,
                    "depends_on": ["implementer"],
                },
            ],
        )

    def test_parallel_worker_host_can_be_reduced_to_review_lanes_by_preference(self) -> None:
        registry = copy.deepcopy(route_preview.load_registry())
        registry["host_capabilities"] = {
            "active_tier": "parallel-workers",
            "supports_subagents": True,
            "supports_parallel_subagents": True,
            "subagent_dispatch_skill": "dispatch-subagents",
            "tiers": route_preview.load_registry()["host_capabilities"]["tiers"],
        }

        strategy, plan, host_skills = route_preview.choose_delegation_plan(
            "BUILD",
            "parallel-safe",
            "implementer-spec-quality",
            registry,
            "review-lanes",
        )

        self.assertEqual(strategy, "independent-reviewer")
        self.assertEqual(host_skills, ["dispatch-subagents"])
        self.assertEqual(plan["resolved_delegation_preference"], "review-lanes")
        self.assertEqual(plan["effective_delegation_mode"], "review-lane-subagents")

    def test_preference_off_disables_subagent_strategy_on_capable_host(self) -> None:
        registry = copy.deepcopy(route_preview.load_registry())
        registry["host_capabilities"] = {
            "active_tier": "parallel-workers",
            "supports_subagents": True,
            "supports_parallel_subagents": True,
            "subagent_dispatch_skill": "dispatch-subagents",
            "tiers": route_preview.load_registry()["host_capabilities"]["tiers"],
        }

        with patch.object(route_preview, "load_registry", return_value=registry):
            report = route_preview.build_report(
                self.build_args(
                    "Implement many screens and many endpoints in parallel",
                    changed_files=12,
                    delegation_preference="off",
                )
            )

        self.assertEqual(report["detected"]["host_capability_tier"], "parallel-workers")
        self.assertEqual(report["detected"]["resolved_delegation_preference"], "off")
        self.assertEqual(report["detected"]["effective_delegation_mode"], "controller-baseline")
        self.assertEqual(report["detected"]["delegation_strategy"], "sequential-lanes")
        self.assertEqual(report["detected"]["host_skills"], [])
        self.assertEqual(report["detected"]["isolation_recommendation"], "worktree")

    def test_resolve_preferences_payload_drives_default_delegation_preference(self) -> None:
        with TemporaryDirectory() as temp_dir:
            forge_home = Path(temp_dir) / "forge-home"
            preferences_path = common.resolve_global_preferences_path(forge_home)
            extra_path = common.resolve_global_extra_preferences_path(forge_home)
            preferences_path.parent.mkdir(parents=True, exist_ok=True)
            preferences_path.write_text(
                json.dumps(
                    {
                        "technical_level": "technical",
                        "detail_level": "concise",
                        "autonomy_level": "autonomous",
                        "pace": "fast",
                        "feedback_style": "direct",
                        "personality": "strict-coach",
                    },
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            extra_path.write_text(
                json.dumps(
                    {
                        "custom_rules": [
                            "Delegated: Spawn subagents để tăng tiến độ khi cần",
                        ],
                    },
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            report = route_preview.build_report(
                self.build_args(
                    "Implement many screens and many endpoints in parallel",
                    changed_files=12,
                    forge_home=forge_home,
                )
            )

        self.assertEqual(report["detected"]["resolved_delegation_preference"], "auto")


if __name__ == "__main__":
    unittest.main()
