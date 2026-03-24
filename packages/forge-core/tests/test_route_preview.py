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

    def test_session_prompt_skips_edit_verification_profile(self) -> None:
        report = route_preview.build_report(self.build_args("Tiếp tục task đang dở"))

        self.assertEqual(report["detected"]["intent"], "SESSION")
        self.assertIsNone(report["detected"]["verification_profile"])
        self.assertIsNone(report["verification"])
        self.assertIn("Verification profile: (n/a)", route_preview.format_text(report))

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


if __name__ == "__main__":
    unittest.main()
