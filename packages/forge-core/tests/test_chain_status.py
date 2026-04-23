from __future__ import annotations

import json
import unittest
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory

from support import run_python_script

import track_chain_status  # noqa: E402


class ChainStatusTests(unittest.TestCase):
    def test_chain_status_includes_packet_graph_fields(self) -> None:
        report = track_chain_status.build_report(
            Namespace(
                chain="Checkout graph",
                project_name="workspace",
                status="active",
                current_stage="build",
                profile=None,
                intent=None,
                required_stage=[],
                completed_stage=["plan"],
                next_stage=["review"],
                active_skill=["build"],
                active_lane=["implementer"],
                lane_model=["implementer=capable"],
                active_packet=["packet-checkout-ui"],
                blocked_packet=[],
                review_ready_packet=["packet-checkout-ui"],
                merge_ready_packet=[],
                next_merge_point="merge-ui-and-api",
                merge_target="main",
                merge_strategy="squash",
                overlap_risk_status="low",
                review_readiness="ready",
                merge_readiness="pending",
                completion_gate="review-ready",
                browser_qa_pending=[],
                write_scope_overlap=[],
                sequential_reason=[],
                blocker=[],
                risk=[],
                gate_decision=None,
                review_iteration=1,
                max_review_iterations=3,
            )
        )

        self.assertEqual(report["merge_target"], "main")
        self.assertEqual(report["merge_strategy"], "squash")
        self.assertEqual(report["overlap_risk_status"], "low")
        self.assertEqual(report["review_readiness"], "ready")
        self.assertEqual(report["merge_readiness"], "pending")
        self.assertEqual(report["completion_gate"], "review-ready")

    def test_chain_status_rejects_merge_ready_without_review_ready(self) -> None:
        with self.assertRaises(ValueError):
            track_chain_status.build_report(
                Namespace(
                    chain="Checkout graph",
                    project_name="workspace",
                    status="active",
                    current_stage="build",
                    profile=None,
                    intent=None,
                    required_stage=[],
                    completed_stage=[],
                    next_stage=[],
                    active_skill=[],
                    active_lane=[],
                    lane_model=[],
                    active_packet=[],
                    blocked_packet=[],
                    review_ready_packet=[],
                    merge_ready_packet=[],
                    next_merge_point=None,
                    merge_target="main",
                    merge_strategy="merge-commit",
                    overlap_risk_status="none",
                    review_readiness="pending",
                    merge_readiness="ready",
                    completion_gate="merge-ready",
                    browser_qa_pending=[],
                    write_scope_overlap=[],
                    sequential_reason=[],
                    blocker=[],
                    risk=[],
                    gate_decision=None,
                    review_iteration=0,
                    max_review_iterations=0,
                )
            )

    def test_next_surfaces_chain_merge_target_when_ready(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Chain\n", encoding="utf-8")
            (workspace / "package.json").write_text('{"name":"chain"}\n', encoding="utf-8")

            result = run_python_script(
                "track_chain_status.py",
                "Checkout graph",
                "--project-name",
                "Example Project",
                "--current-stage",
                "build",
                "--active-packet",
                "packet-ui",
                "--review-ready-packet",
                "packet-ui",
                "--merge-ready-packet",
                "packet-ui",
                "--merge-target",
                "main",
                "--merge-strategy",
                "squash",
                "--review-readiness",
                "ready",
                "--merge-readiness",
                "ready",
                "--completion-gate",
                "merge-ready",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            next_report = run_python_script(
                "session_context.py",
                "resume",
                "--workspace",
                str(workspace),
                "--format",
                "json",
            )

        self.assertEqual(next_report.returncode, 0, next_report.stderr)
        payload = json.loads(next_report.stdout)
        self.assertEqual(payload["current_stage"], "session-active")
        self.assertTrue(payload["important_files_or_artifacts"])
        self.assertIn("merge target", payload["best_next_step"].lower())


if __name__ == "__main__":
    unittest.main()
