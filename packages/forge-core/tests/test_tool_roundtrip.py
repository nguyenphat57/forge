from __future__ import annotations

import json
import unittest
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory

from support import ROOT_DIR, run_python_script

import common  # noqa: E402
import track_chain_status  # noqa: E402
import track_execution_progress  # noqa: E402
import track_ui_progress  # noqa: E402


class ToolRoundTripTests(unittest.TestCase):
    def test_backend_brief_round_trip_passes_checker(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            generate = run_python_script(
                "generate_backend_brief.py",
                "Add bulk order cancellation endpoint",
                "--pattern",
                "sync-api",
                "--runtime",
                "python-service",
                "--surface",
                "cancel-orders",
                "--persist",
                "--project-name",
                "Example Project",
                "--output-dir",
                str(output_dir),
                "--format",
                "json",
            )
            self.assertEqual(generate.returncode, 0, generate.stderr)

            artifact_dir = output_dir / ".forge-artifacts" / "backend-briefs" / common.slugify("Example Project")
            self.assertTrue((artifact_dir / "MASTER.md").exists())

            check = run_python_script(
                "check_backend_brief.py",
                str(artifact_dir),
                "--surface",
                "cancel-orders",
                "--format",
                "json",
            )
            self.assertEqual(check.returncode, 0, check.stderr)
            report = json.loads(check.stdout)
            self.assertEqual(report["status"], "PASS")

    def test_ui_brief_round_trip_passes_checker_for_frontend_and_visualize(self) -> None:
        modes = [
            ("frontend", "Refresh checkout for tablet POS", "react-vite", "checkout"),
            ("visualize", "Explore calmer kitchen dashboard direction", "mobile-webview", "kitchen-dashboard"),
        ]
        for mode, summary, stack, screen in modes:
            with self.subTest(mode=mode):
                with TemporaryDirectory() as temp_dir:
                    output_dir = Path(temp_dir)
                    generate = run_python_script(
                        "generate_ui_brief.py",
                        summary,
                        "--mode",
                        mode,
                        "--stack",
                        stack,
                        "--platform",
                        "tablet",
                        "--screen",
                        screen,
                        "--persist",
                        "--project-name",
                        "Example Project",
                        "--output-dir",
                        str(output_dir),
                        "--format",
                        "json",
                    )
                    self.assertEqual(generate.returncode, 0, generate.stderr)

                    artifact_dir = output_dir / ".forge-artifacts" / "ui-briefs" / common.slugify("Example Project") / mode
                    self.assertTrue((artifact_dir / "MASTER.md").exists())

                    check = run_python_script(
                        "check_ui_brief.py",
                        str(artifact_dir),
                        "--mode",
                        mode,
                        "--screen",
                        screen,
                        "--format",
                        "json",
                    )
                    self.assertEqual(check.returncode, 0, check.stderr)
                    report = json.loads(check.stdout)
                    self.assertEqual(report["status"], "PASS")

    def test_capture_continuity_writes_scoped_entry(self) -> None:
        with TemporaryDirectory() as temp_dir:
            brain_dir = Path(temp_dir) / ".brain"
            result = run_python_script(
                "capture_continuity.py",
                "Compatibility window must stay one release",
                "--kind",
                "decision",
                "--scope",
                "orders-api",
                "--evidence",
                "docs/DESIGN.md",
                "--brain-dir",
                str(brain_dir),
                "--format",
                "json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            entries = json.loads((brain_dir / "decisions.json").read_text(encoding="utf-8"))

        self.assertEqual(report["entry"]["scope"], "orders-api")
        self.assertEqual(entries[0]["summary"], "Compatibility window must stay one release")

    def test_execution_progress_requires_proof_for_ready_states(self) -> None:
        with self.assertRaises(ValueError):
            track_execution_progress.build_report(
                Namespace(
                    task="Offline reconciliation",
                    mode="checkpoint-batch",
                    stage="integration",
                    status="completed",
                    completion_state="ready-for-review",
                    project_name="workspace",
                    lane="implementer",
                    model_tier="capable",
                    proof=[],
                    done=[],
                    next_step=[],
                    blocker=[],
                    risk=[],
                )
            )

    def test_chain_status_rejects_overflowing_review_iteration(self) -> None:
        with self.assertRaises(ValueError):
            track_chain_status.build_report(
                Namespace(
                    chain="Checkout rewrite",
                    project_name="workspace",
                    status="active",
                    current_stage="spec-review",
                    completed_stage=[],
                    next_stage=[],
                    active_skill=[],
                    active_lane=[],
                    lane_model=[],
                    blocker=[],
                    risk=[],
                    gate_decision=None,
                    review_iteration=4,
                    max_review_iterations=3,
                )
            )

    def test_ui_progress_persists_remaining_stages(self) -> None:
        with TemporaryDirectory() as temp_dir:
            payload = track_ui_progress.build_payload(
                Namespace(
                    mode="frontend",
                    task="Checkout tablet refresh",
                    stage="implementation",
                    status="active",
                    note=["Waiting on responsive review"],
                )
            )
            json_path, md_path = track_ui_progress.persist_payload(payload, temp_dir)

            persisted = json.loads(json_path.read_text(encoding="utf-8"))
            markdown = md_path.read_text(encoding="utf-8")

        self.assertEqual(persisted["remaining_stages"], ["responsive-a11y-review", "handover"])
        self.assertIn("Waiting on responsive review", markdown)


if __name__ == "__main__":
    unittest.main()
