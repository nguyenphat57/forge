from __future__ import annotations

import json
import unittest
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory

from support import run_python_script

import track_execution_progress  # noqa: E402


class FastLaneLifecycleTests(unittest.TestCase):
    def test_fast_lane_contract_rejects_missing_required_fields(self) -> None:
        with self.assertRaises(ValueError):
            track_execution_progress.build_report(
                Namespace(
                    task="Copy tweak",
                    mode="single-track",
                    stage="implementation",
                    status="active",
                    completion_state="in-progress",
                    packet_mode="fast-lane",
                    project_name="workspace",
                    lane="implementer",
                    model_tier="standard",
                    source=[],
                    scope_path=[],
                    owned_scope=[],
                    depends_on_packet=[],
                    unblock_packet=[],
                    baseline=[],
                    out_of_scope=[],
                    reopen_if=[],
                    harness_available="no",
                    red=[],
                    proof=[],
                    verify_again=[],
                    browser_qa_classification="not-needed",
                    browser_qa_scope=[],
                    browser_qa_status="not-needed",
                    done=[],
                    next_step=[],
                    blocker=[],
                    risk=[],
                )
            )

    def test_fast_lane_persists_and_help_next_surfaces_fast_lane_focus(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Fast Lane\n", encoding="utf-8")
            (workspace / "package.json").write_text('{"name":"fast-lane"}\n', encoding="utf-8")

            progress = run_python_script(
                "track_execution_progress.py",
                "Copy tweak",
                "--mode",
                "single-track",
                "--packet-mode",
                "fast-lane",
                "--stage",
                "implementation",
                "--status",
                "active",
                "--completion-state",
                "in-progress",
                "--packet-id",
                "packet-copy",
                "--goal",
                "Update one checkout copy path safely",
                "--scope-path",
                "src/copy.ts",
                "--owned-scope",
                "src/copy.ts",
                "--baseline",
                "git status --short",
                "--proof",
                "Rendered checkout copy preview",
                "--verify-again",
                "python -m pytest tests/test_copy.py -q",
                "--risk",
                "None beyond localized copy regression",
                "--next",
                "Apply approved copy text",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(progress.returncode, 0, progress.stderr)

            result = run_python_script(
                "resolve_help_next.py",
                "--workspace",
                str(workspace),
                "--mode",
                "next",
                "--format",
                "json",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["current_stage"], "session-active")
        self.assertEqual(report["signals"]["workflow_summary"]["packet_mode"], "fast-lane")
        self.assertEqual(report["current_focus"], "Fast-lane packet: Copy tweak [packet-copy]")
        self.assertIn("Continue fast-lane packet", report["recommended_action"])
        self.assertIn("Escalate to standard packet mode", " ".join(report["alternatives"]))

    def test_fast_lane_rejects_packet_graph_dependencies(self) -> None:
        with self.assertRaises(ValueError):
            track_execution_progress.build_report(
                Namespace(
                    task="Copy tweak",
                    mode="single-track",
                    stage="implementation",
                    status="active",
                    completion_state="in-progress",
                    packet_mode="fast-lane",
                    project_name="workspace",
                    lane="implementer",
                    model_tier="standard",
                    source=[],
                    scope_path=["src/copy.ts"],
                    owned_scope=["src/copy.ts"],
                    depends_on_packet=["packet-auth"],
                    unblock_packet=[],
                    baseline=["git status --short"],
                    out_of_scope=[],
                    reopen_if=[],
                    harness_available="no",
                    red=[],
                    proof=["rendered preview"],
                    verify_again=["python -m pytest tests/test_copy.py -q"],
                    browser_qa_classification="not-needed",
                    browser_qa_scope=[],
                    browser_qa_status="not-needed",
                    done=[],
                    next_step=["apply copy"],
                    blocker=[],
                    risk=["none"],
                )
            )


if __name__ == "__main__":
    unittest.main()
