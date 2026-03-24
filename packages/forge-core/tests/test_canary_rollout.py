from __future__ import annotations

import json
import unittest
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory

from support import run_python_script

import evaluate_canary_readiness  # noqa: E402
import record_canary_result  # noqa: E402


class CanaryRolloutTests(unittest.TestCase):
    def test_record_canary_result_persists_workspace_artifact(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            report = record_canary_result.build_report(
                Namespace(
                    workspace="lamdi-pos",
                    summary="Stable route behavior across core prompts",
                    status="pass",
                    host="antigravity",
                    scenario=["review", "build", "session"],
                    signal=["No misroute seen"],
                    blocker=[],
                    follow_up=["Continue soak for another day"],
                )
            )
            json_path, md_path = record_canary_result.persist_report(report, str(output_dir))
            persisted = json.loads(json_path.read_text(encoding="utf-8"))
            markdown_exists = md_path.exists()

        self.assertEqual(persisted["workspace"], "lamdi-pos")
        self.assertTrue(markdown_exists)

    def test_controlled_rollout_readiness_passes_for_two_clean_workspaces(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            for workspace in ("lamdi-pos", "kitchen-display"):
                result = run_python_script(
                    "record_canary_result.py",
                    "Core prompts stable",
                    "--workspace",
                    workspace,
                    "--status",
                    "pass",
                    "--scenario",
                    "route-preview",
                    "--persist",
                    "--output-dir",
                    str(output_dir),
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            report = evaluate_canary_readiness.evaluate_runs(
                evaluate_canary_readiness.load_runs(output_dir / ".forge-artifacts" / "canary-runs"),
                "controlled-rollout",
            )

        self.assertEqual(report["status"], "PASS")

    def test_broad_readiness_fails_when_warn_workspace_exists(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            for workspace, status in (
                ("lamdi-pos", "pass"),
                ("kitchen-display", "pass"),
                ("ops-console", "warn"),
            ):
                for index in range(2):
                    result = run_python_script(
                        "record_canary_result.py",
                        f"Run {index + 1}",
                        "--workspace",
                        workspace,
                        "--status",
                        status if index == 1 else "pass",
                        "--scenario",
                        "route-preview",
                        "--persist",
                        "--output-dir",
                        str(output_dir),
                    )
                    self.assertIn(result.returncode, {0, 1}, result.stderr)

            report = evaluate_canary_readiness.evaluate_runs(
                evaluate_canary_readiness.load_runs(output_dir / ".forge-artifacts" / "canary-runs"),
                "broad",
            )

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("Warn workspaces exceed limit" in item for item in report["failures"]))

    def test_broad_readiness_requires_multiple_observation_days(self) -> None:
        runs = []
        for workspace in ("lamdi-pos", "kitchen-display", "ops-console"):
            for index in range(2):
                runs.append(
                    {
                        "workspace": workspace,
                        "status": "pass",
                        "observed_at": f"2026-03-23T0{index}:00:00",
                        "summary": f"{workspace} run {index + 1}",
                        "_path": f"{workspace}-{index + 1}.json",
                    }
                )

        report = evaluate_canary_readiness.evaluate_runs(runs, "broad")

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("observation day" in item for item in report["failures"]))


if __name__ == "__main__":
    unittest.main()
