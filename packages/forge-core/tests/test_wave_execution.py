from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import SCRIPTS_DIR, run_python_script


def load_wave_execution_module():
    module_path = SCRIPTS_DIR / "wave_execution.py"
    if not module_path.exists():
        raise AssertionError(f"Missing wave execution module: {module_path}")
    spec = importlib.util.spec_from_file_location("wave_execution", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load wave execution module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules.pop("wave_execution", None)
    spec.loader.exec_module(module)
    return module


def verification_command(packet_id: str) -> str:
    return f"python -m pytest tests/test_{packet_id.replace('-', '_')}.py -q"


def packet(
    packet_id: str,
    *,
    depends_on: list[str] | None = None,
    scope: list[str] | None = None,
    gate: str = "incomplete",
    overlap_risk_status: str = "none",
    write_scope_conflicts: list[str] | None = None,
) -> dict:
    return {
        "packet_id": packet_id,
        "goal": packet_id,
        "depends_on_packets": list(depends_on or []),
        "owned_files_or_write_scope": list(scope or [packet_id]),
        "write_scope_conflicts": list(write_scope_conflicts or []),
        "overlap_risk_status": overlap_risk_status,
        "merge_target": "main",
        "merge_strategy": "squash",
        "completion_gate": gate,
        "verification_to_rerun": [verification_command(packet_id)],
    }


def progress(
    packet_id: str,
    *,
    status: str = "completed",
    completion_state: str = "ready-for-review",
    completion_gate: str | None = None,
    overlap_risk_status: str = "none",
    write_scope_conflicts: list[str] | None = None,
) -> dict:
    return {
        "packet_id": packet_id,
        "status": status,
        "completion_state": completion_state,
        "completion_gate": completion_gate
        or (
            "merge-ready"
            if completion_state == "ready-for-merge"
            else "review-ready"
            if completion_state == "ready-for-review"
            else "blocked"
            if completion_state == "blocked-by-residual-risk"
            else "incomplete"
        ),
        "overlap_risk_status": overlap_risk_status,
        "write_scope_conflicts": list(write_scope_conflicts or []),
    }


def run_report(command_display: str, *, status: str = "PASS", state: str = "completed", artifact_mtime: float = 2.0) -> dict:
    return {
        "status": status,
        "state": state,
        "command_display": command_display,
        "_artifact_mtime": artifact_mtime,
    }


class WaveExecutionUnitTests(unittest.TestCase):
    def test_plan_builds_independent_first_wave_before_integration_wave(self) -> None:
        wave_execution = load_wave_execution_module()

        plan = wave_execution.plan_wave_execution(
            [packet("ui-slice", scope=["src/ui"]), packet("api-slice", scope=["src/api"]), packet("integration-slice", depends_on=["ui-slice", "api-slice"], scope=["src/integration"])],
            project="Example Project",
        )

        self.assertEqual(len(plan["waves"]), 2)
        self.assertEqual(set(plan["waves"][0]["packet_ids"]), {"ui-slice", "api-slice"})
        self.assertEqual(plan["waves"][1]["packet_ids"], ["integration-slice"])
        self.assertEqual(plan["ready_packets"], ["api-slice", "ui-slice"])
        self.assertEqual(plan["current_wave"], 0)
        self.assertEqual(plan["next_ready_wave"]["wave_index"], 0)
        self.assertEqual(plan["blocked_packets"], [])

    def test_plan_rejects_cycle(self) -> None:
        wave_execution = load_wave_execution_module()

        with self.assertRaisesRegex(ValueError, "cycle"):
            wave_execution.plan_wave_execution(
                [packet("ui-slice", depends_on=["api-slice"]), packet("api-slice", depends_on=["ui-slice"])],
                project="Example Project",
            )

    def test_plan_rejects_missing_dependency(self) -> None:
        wave_execution = load_wave_execution_module()

        with self.assertRaisesRegex(ValueError, "missing dependency"):
            wave_execution.plan_wave_execution(
                [packet("ui-slice", depends_on=["api-slice"])],
                project="Example Project",
            )

    def test_plan_separates_overlapping_write_scope_into_different_waves(self) -> None:
        wave_execution = load_wave_execution_module()

        plan = wave_execution.plan_wave_execution(
            [packet("ui-a", scope=["src/ui"]), packet("ui-b", scope=["src/ui"]), packet("api-slice", scope=["src/api"])],
            project="Example Project",
        )

        self.assertEqual(len(plan["waves"]), 2)
        self.assertTrue(all({"ui-a", "ui-b"} != set(wave["packet_ids"]) for wave in plan["waves"]))
        self.assertEqual(sorted(plan["packets"]), ["api-slice", "ui-a", "ui-b"])

    def test_advance_waits_for_full_current_wave_before_unlocking_next_wave(self) -> None:
        wave_execution = load_wave_execution_module()
        plan = wave_execution.plan_wave_execution(
            [packet("ui-slice", scope=["src/ui"]), packet("api-slice", scope=["src/api"]), packet("integration-slice", depends_on=["ui-slice", "api-slice"], scope=["src/integration"])],
            project="Example Project",
        )

        partially_advanced = wave_execution.advance_wave_execution(
            plan,
            {
                "ui-slice": {**progress("ui-slice", status="active", completion_state="in-progress"), "_artifact_mtime": 1.0},
                "api-slice": {**progress("api-slice"), "_artifact_mtime": 1.0},
            },
        )

        self.assertEqual(partially_advanced["running_packets"], ["ui-slice"])
        self.assertEqual(partially_advanced["completed_packets"], ["api-slice"])
        self.assertIsNone(partially_advanced["next_ready_wave"])
        self.assertEqual(partially_advanced["ready_packets"], [])

        fully_advanced = wave_execution.advance_wave_execution(
            plan,
            {
                "ui-slice": {**progress("ui-slice"), "_artifact_mtime": 1.0},
                "api-slice": {**progress("api-slice"), "_artifact_mtime": 1.0},
            },
        )

        self.assertEqual(fully_advanced["current_wave"], 0)
        self.assertEqual(fully_advanced["ready_packets"], [])
        self.assertEqual(fully_advanced["shared_verification_status"], "pending")
        self.assertEqual(
            fully_advanced["shared_verification_pending"],
            [
                verification_command("api-slice"),
                verification_command("ui-slice"),
            ],
        )
        self.assertIsNone(fully_advanced["next_ready_wave"])

        unlocked = wave_execution.advance_wave_execution(
            plan,
            {
                "ui-slice": {**progress("ui-slice"), "_artifact_mtime": 1.0},
                "api-slice": {**progress("api-slice"), "_artifact_mtime": 1.0},
            },
            {
                verification_command("api-slice"): run_report(
                    verification_command("api-slice"),
                    artifact_mtime=2.0,
                ),
                verification_command("ui-slice"): run_report(
                    verification_command("ui-slice"),
                    artifact_mtime=2.0,
                ),
            },
        )

        self.assertEqual(unlocked["current_wave"], 1)
        self.assertEqual(unlocked["ready_packets"], ["integration-slice"])
        self.assertEqual(unlocked["next_ready_wave"]["packet_ids"], ["integration-slice"])

    def test_advance_marks_blocked_packet_and_keeps_downstream_locked(self) -> None:
        wave_execution = load_wave_execution_module()
        plan = wave_execution.plan_wave_execution(
            [packet("ui-slice", scope=["src/ui"]), packet("api-slice", scope=["src/api"]), packet("integration-slice", depends_on=["ui-slice", "api-slice"], scope=["src/integration"])],
            project="Example Project",
        )

        advanced = wave_execution.advance_wave_execution(
            plan,
            {
                "ui-slice": {**progress("ui-slice", status="blocked", completion_state="blocked-by-residual-risk"), "_artifact_mtime": 1.0},
                "api-slice": {**progress("api-slice"), "_artifact_mtime": 1.0},
            },
        )

        self.assertEqual(advanced["blocked_packets"], ["ui-slice"])
        self.assertIn("integration-slice", advanced["packet_statuses"])
        self.assertEqual(advanced["packet_statuses"]["integration-slice"]["status"], "pending")
        self.assertIsNone(advanced["next_ready_wave"])


class WaveExecutionScriptTests(unittest.TestCase):
    def _write_workspace(self, workspace: Path) -> None:
        (workspace / "README.md").write_text("# Wave Workspace\n", encoding="utf-8")
        (workspace / "package.json").write_text('{"name":"wave-workspace"}\n', encoding="utf-8")
        tests_dir = workspace / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        for packet_id in ("ui-slice", "api-slice", "integration-slice"):
            (tests_dir / f"test_{packet_id.replace('-', '_')}.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

    def _write_packet_file(self, workspace: Path) -> Path:
        packet_file = workspace / "wave-packets.json"
        packet_file.write_text(
            json.dumps(
                {
                    "packets": [
                        packet("ui-slice", scope=["src/ui"]),
                        packet("api-slice", scope=["src/api"]),
                        packet("integration-slice", depends_on=["ui-slice", "api-slice"], scope=["src/integration"]),
                    ]
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        return packet_file

    def test_plan_persists_wave_plan_and_next_prefers_spawn_current_wave(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            self._write_workspace(workspace)
            packet_file = self._write_packet_file(workspace)

            result = run_python_script(
                "run_wave_execution.py",
                "plan",
                "--workspace",
                str(workspace),
                "--project-name",
                "Wave Workspace",
                "--packet-file",
                str(packet_file),
                "--format",
                "json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["ready_packets"], ["api-slice", "ui-slice"])

            next_report = run_python_script(
                "resolve_help_next.py",
                "--workspace",
                str(workspace),
                "--mode",
                "next",
                "--format",
                "json",
            )

        self.assertEqual(next_report.returncode, 0, next_report.stderr)
        help_payload = json.loads(next_report.stdout)
        self.assertIn("spawn current wave", help_payload["recommended_action"].casefold())
        self.assertIn("api-slice", help_payload["recommended_action"])

    def test_advance_reads_latest_execution_progress_and_unlocks_next_wave(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            self._write_workspace(workspace)
            packet_file = self._write_packet_file(workspace)

            result = run_python_script(
                "run_wave_execution.py",
                "plan",
                "--workspace",
                str(workspace),
                "--project-name",
                "Wave Workspace",
                "--packet-file",
                str(packet_file),
                "--format",
                "json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            for packet_id in ("ui-slice", "api-slice"):
                progress_result = run_python_script(
                    "track_execution_progress.py",
                    packet_id,
                    "--mode",
                    "parallel-safe",
                    "--stage",
                    "integration",
                    "--status",
                    "completed",
                    "--completion-state",
                    "ready-for-review",
                    "--project-name",
                    "Wave Workspace",
                    "--packet-id",
                    packet_id,
                    "--owned-scope",
                    f"src/{packet_id}",
                    "--proof",
                    verification_command(packet_id),
                    "--verify-again",
                    verification_command(packet_id),
                    "--harness-available",
                    "no",
                    "--persist",
                    "--output-dir",
                    str(workspace),
                    "--format",
                    "json",
                )
                self.assertEqual(progress_result.returncode, 0, progress_result.stderr)

            advance_result = run_python_script(
                "run_wave_execution.py",
                "advance",
                "--workspace",
                str(workspace),
                "--project-name",
                "Wave Workspace",
                "--format",
                "json",
            )
            self.assertEqual(advance_result.returncode, 0, advance_result.stderr)
            gated_payload = json.loads(advance_result.stdout)
            self.assertEqual(gated_payload["current_wave"], 0)
            self.assertEqual(gated_payload["shared_verification_status"], "pending")

            next_report = run_python_script(
                "resolve_help_next.py",
                "--workspace",
                str(workspace),
                "--mode",
                "next",
                "--format",
                "json",
            )
            self.assertEqual(next_report.returncode, 0, next_report.stderr)
            next_payload = json.loads(next_report.stdout)
            self.assertIn("shared verification", next_payload["recommended_action"].casefold())

            for packet_id in ("api-slice", "ui-slice"):
                verification_result = run_python_script(
                    "run_with_guidance.py",
                    "--workspace",
                    str(workspace),
                    "--project-name",
                    "Wave Workspace",
                    "--persist",
                    "--output-dir",
                    str(workspace),
                    "--format",
                    "json",
                    "--",
                    "python",
                    "-m",
                    "pytest",
                    f"tests/test_{packet_id.replace('-', '_')}.py",
                    "-q",
                )
                self.assertEqual(verification_result.returncode, 0, verification_result.stderr)

            advance_result = run_python_script(
                "run_wave_execution.py",
                "advance",
                "--workspace",
                str(workspace),
                "--project-name",
                "Wave Workspace",
                "--format",
                "json",
            )

        self.assertEqual(advance_result.returncode, 0, advance_result.stderr)
        payload = json.loads(advance_result.stdout)
        self.assertEqual(payload["current_wave"], 1)
        self.assertEqual(payload["ready_packets"], ["integration-slice"])
        self.assertEqual(set(payload["completed_packets"]), {"api-slice", "ui-slice"})

    def test_status_reflects_blocked_packet_and_next_keeps_focus_on_resolution(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            self._write_workspace(workspace)
            packet_file = self._write_packet_file(workspace)

            result = run_python_script(
                "run_wave_execution.py",
                "plan",
                "--workspace",
                str(workspace),
                "--project-name",
                "Wave Workspace",
                "--packet-file",
                str(packet_file),
                "--format",
                "json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            blocked = run_python_script(
                "track_execution_progress.py",
                "ui-slice",
                "--mode",
                "parallel-safe",
                "--stage",
                "integration",
                "--status",
                "blocked",
                "--completion-state",
                "blocked-by-residual-risk",
                "--project-name",
                "Wave Workspace",
                "--packet-id",
                "ui-slice",
                "--owned-scope",
                "src/ui",
                "--blocker",
                "UI slice is blocked by a regression",
                "--risk",
                "UI slice needs follow-up",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(blocked.returncode, 0, blocked.stderr)

            advance_result = run_python_script(
                "run_wave_execution.py",
                "advance",
                "--workspace",
                str(workspace),
                "--project-name",
                "Wave Workspace",
                "--format",
                "json",
            )
            self.assertEqual(advance_result.returncode, 0, advance_result.stderr)

            status_result = run_python_script(
                "run_wave_execution.py",
                "status",
                "--workspace",
                str(workspace),
                "--project-name",
                "Wave Workspace",
                "--format",
                "json",
            )
            next_report = run_python_script(
                "resolve_help_next.py",
                "--workspace",
                str(workspace),
                "--mode",
                "next",
                "--format",
                "json",
            )

        self.assertEqual(status_result.returncode, 0, status_result.stderr)
        status_payload = json.loads(status_result.stdout)
        self.assertEqual(status_payload["blocked_packets"], ["ui-slice"])
        self.assertIsNone(status_payload["next_ready_wave"])

        self.assertEqual(next_report.returncode, 0, next_report.stderr)
        help_payload = json.loads(next_report.stdout)
        self.assertIn("resolve blocked packet", help_payload["recommended_action"].casefold())
        self.assertIn("ui-slice", help_payload["recommended_action"])


if __name__ == "__main__":
    unittest.main()
