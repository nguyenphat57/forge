from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import run_python_script


class LaneDecisionTests(unittest.TestCase):
    def test_lane_score_prefers_high_overlap_and_low_cost(self) -> None:
        result = run_python_script(
            "lane_score.py",
            "--candidate",
            "electron-react-postgres",
            "--real-repo-demand",
            "4",
            "--core-overlap",
            "4",
            "--companion-feasibility",
            "4",
            "--shipping-leverage",
            "4",
            "--maintenance-cost",
            "2",
            "--format",
            "json",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertGreaterEqual(report["total"], 70)
        self.assertEqual(report["recommendation"], "strong")

    def test_lane_gate_blocks_when_lane_one_is_not_ready(self) -> None:
        with TemporaryDirectory() as temp_dir:
            score_path = Path(temp_dir) / "electron.json"
            score_path.write_text(json.dumps({"total": 78.0}, indent=2), encoding="utf-8")

            result = run_python_script(
                "lane_gate.py",
                "--candidate",
                "electron-react-postgres",
                "--score-path",
                str(score_path),
                "--real-repo-count",
                "0",
                "--format",
                "json",
            )

        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("real repo" in item for item in report["blockers"]))


if __name__ == "__main__":
    unittest.main()
