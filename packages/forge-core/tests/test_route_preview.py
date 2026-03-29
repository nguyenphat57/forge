from __future__ import annotations

import copy
import sys
import unittest
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


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
        changed_files: int | None = None,
        has_harness: str = "auto",
    ) -> Namespace:
        return Namespace(
            prompt=prompt,
            repo_signal=repo_signals or [],
            workspace_router=workspace_router,
            changed_files=changed_files,
            has_harness=has_harness,
            format="json",
            persist=False,
            output_dir=None,
        )

    def test_review_prompt_routes_to_review_intent(self) -> None:
        report = route_preview.build_report(self.build_args("Review code before merge"))

        self.assertEqual(report["detected"]["intent"], "REVIEW")
        self.assertEqual(report["detected"]["forge_skills"], ["review", "secure"])

    def test_build_prompt_routes_to_build_intent(self) -> None:
        report = route_preview.build_report(self.build_args("Add a new checkout endpoint"))

        self.assertEqual(report["detected"]["intent"], "BUILD")
        self.assertIn("build", report["detected"]["forge_skills"])

    def test_medium_build_requires_change_artifacts(self) -> None:
        report = route_preview.build_report(
            self.build_args(
                "Implement a new checkout feature",
                changed_files=3,
            )
        )

        self.assertEqual(report["detected"]["complexity"], "medium")
        self.assertTrue(report["detected"]["change_artifacts_required"])

    def test_session_prompt_skips_edit_verification_profile(self) -> None:
        report = route_preview.build_report(self.build_args("Continue the task in progress"))
        active_routing_locales = common.routing_locale_names()
        expected_routing_locales = ", ".join(active_routing_locales) if active_routing_locales else "(none)"

        self.assertEqual(report["detected"]["intent"], "SESSION")
        self.assertEqual(report["detected"]["routing_locales"], active_routing_locales)
        self.assertIsNone(report["detected"]["verification_profile"])
        self.assertIsNone(report["verification"])
        self.assertIn("Verification profile: (n/a)", route_preview.format_text(report))
        self.assertIn(f"Routing locales: {expected_routing_locales}", route_preview.format_text(report))

    def test_mixed_english_review_prompt_routes_to_review_intent(self) -> None:
        report = route_preview.build_report(self.build_args("Review the checkout flow before merge"))

        self.assertEqual(report["detected"]["intent"], "REVIEW")
        self.assertEqual(report["detected"]["forge_skills"], ["review", "secure"])

    def test_direction_question_inserts_brainstorm_without_explicit_keyword(self) -> None:
        report = route_preview.build_report(
            self.build_args("Should we use web or native for the new checkout flow?")
        )

        self.assertEqual(report["detected"]["intent"], "BUILD")
        self.assertEqual(report["detected"]["forge_skills"][0], "brainstorm")

    def test_backward_compatibility_boundary_inserts_spec_review(self) -> None:
        report = route_preview.build_report(
            self.build_args(
                "Add a new endpoint for existing clients and keep backward compatibility",
                repo_signals=["api/"],
            )
        )

        self.assertEqual(report["detected"]["intent"], "BUILD")
        self.assertIn("spec-review", report["detected"]["forge_skills"])

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
                )
            )

        self.assertEqual(report["detected"]["execution_mode"], "parallel-safe")
        self.assertEqual(report["detected"]["delegation_strategy"], "parallel-split")
        self.assertEqual(report["detected"]["host_skills"], ["dispatch-subagents"])
        self.assertEqual(report["delegation_plan"]["activation_skill"], "dispatch-subagents")
        self.assertEqual(report["delegation_plan"]["dispatch_mode"], "parallel-workers")
        self.assertEqual(
            report["delegation_plan"]["packet_template"]["required_fields"],
            [
                "goal",
                "current_slice_or_review_question",
                "owned_files_or_write_scope",
                "files_to_avoid",
                "allowed_reads_or_supporting_artifacts",
                "proof_before_progress",
                "verification_to_rerun",
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
                }
            ],
        )

    def test_review_lane_host_gets_packetized_independent_reviewer_plan(self) -> None:
        registry = copy.deepcopy(route_preview.load_registry())
        registry["host_capabilities"] = {
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
        )

        self.assertEqual(strategy, "independent-reviewer")
        self.assertEqual(host_skills, ["dispatch-subagents"])
        self.assertEqual(plan["dispatch_mode"], "independent-reviewers")
        self.assertEqual(
            plan["packet_blueprints"],
            [
                {
                    "lane": "implementer",
                    "packet_type": "implementer-pass",
                    "runtime_role": "worker",
                    "read_only": False,
                    "scope_rule": "Owns the implementation slice with explicit file scope.",
                },
                {
                    "lane": "quality-reviewer",
                    "packet_type": "reviewer-pass",
                    "runtime_role": "default",
                    "read_only": True,
                    "scope_rule": "Read-only findings pass over implementer evidence and changed files.",
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
