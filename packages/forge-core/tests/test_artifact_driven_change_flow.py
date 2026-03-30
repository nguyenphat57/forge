from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import run_python_script


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True, encoding="utf-8")
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    (path / "README.md").write_text("# Demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True, capture_output=True, text=True, encoding="utf-8")
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True, text=True, encoding="utf-8")


class ArtifactDrivenChangeFlowTests(unittest.TestCase):
    def test_medium_change_flow_round_trip_reaches_ready_for_review_gate(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "repo"
            workspace.mkdir(parents=True, exist_ok=True)
            _init_repo(workspace)

            start = run_python_script(
                "change_artifacts.py",
                "start",
                "Add checkout retry",
                "--workspace",
                str(workspace),
                "--slug",
                "checkout-retry",
                "--task",
                "Wire retry guard into checkout flow.",
                "--verification",
                "pytest tests/test_checkout.py -k retry",
                "--format",
                "json",
            )
            self.assertEqual(start.returncode, 0, start.stderr)
            start_report = json.loads(start.stdout)
            packet_path = Path(start_report["paths"]["implementation_packet"])
            spec_path = Path(start_report["paths"]["spec"])

            checklist = run_python_script(
                "generate_requirements_checklist.py",
                "--requirement",
                "Checkout retry must recover failed payments within 3 attempts and verify with a repeatable checkout scenario.",
                "--format",
                "json",
            )
            self.assertEqual(checklist.returncode, 0, checklist.stderr)
            self.assertEqual(json.loads(checklist.stdout)["status"], "PASS")

            packet_check = run_python_script(
                "check_spec_packet.py",
                "--source",
                str(packet_path),
                "--source",
                str(spec_path),
                "--format",
                "json",
            )
            self.assertEqual(packet_check.returncode, 0, packet_check.stderr)
            self.assertEqual(json.loads(packet_check.stdout)["status"], "PASS")

            worktree = run_python_script(
                "prepare_worktree.py",
                "--workspace",
                str(workspace),
                "--name",
                "checkout-retry",
                "--baseline-command",
                "python -c \"print('baseline ok')\"",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(worktree.returncode, 0, worktree.stderr)
            worktree_report = json.loads(worktree.stdout)
            self.assertEqual(worktree_report["status"], "PASS")
            self.assertTrue(Path(worktree_report["artifacts"]["json"]).exists())

            status = run_python_script(
                "change_artifacts.py",
                "status",
                "--workspace",
                str(workspace),
                "--slug",
                "checkout-retry",
                "--state",
                "ready-for-review",
                "--note",
                "First retry slice is implemented.",
                "--verified",
                "pytest tests/test_checkout.py -k retry",
                "--format",
                "json",
            )
            self.assertEqual(status.returncode, 0, status.stderr)

            verify = run_python_script(
                "verify_change.py",
                "--workspace",
                str(workspace),
                "--slug",
                "checkout-retry",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(verify.returncode, 0, verify.stderr)
            verify_report = json.loads(verify.stdout)
            self.assertEqual(verify_report["status"], "PASS")
            self.assertTrue(Path(verify_report["artifacts"]["json"]).exists())

            gate = run_python_script(
                "record_quality_gate.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "Checkout Retry",
                "--profile",
                "standard",
                "--target-claim",
                "ready-for-review",
                "--decision",
                "go",
                "--evidence",
                "pytest tests/test_checkout.py -k retry",
                "--response",
                "I verified: checkout retry proof passed.",
                "--why",
                "The first slice is bounded and the change packet is aligned.",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(gate.returncode, 0, gate.stderr)
            gate_report = json.loads(gate.stdout)
            self.assertEqual(gate_report["status"], "PASS")
            self.assertTrue(Path(gate_report["artifacts"]["json"]).exists())
            process_kinds = {item["kind"] for item in gate_report["process_artifacts"]}
            self.assertIn("change-state", process_kinds)
            self.assertIn("verify-change", process_kinds)


if __name__ == "__main__":
    unittest.main()
