from __future__ import annotations

import unittest
from argparse import Namespace

from support import load_json_fixture, workspace_fixture

import check_workspace_router  # noqa: E402


class RouterCheckSmokeMatrixTests(unittest.TestCase):
    def test_router_check_cases(self) -> None:
        for case in load_json_fixture("router_check_cases.json"):
            with self.subTest(case=case["name"]):
                workspace = workspace_fixture(case["workspace_fixture"])
                report = check_workspace_router.check_workspace(
                    Namespace(workspace=workspace, agents=None, router_map=None)
                )
                codes = [item["code"] for item in report["findings"]]
                warn_count = report["counts"]["warn"]
                normalized_router_map = report["router_map"].replace("\\", "/")

                self.assertEqual(report["status"], case["expected_status"])
                self.assertTrue(normalized_router_map.endswith(case["expected_router_suffix"]))
                for code in case.get("expected_codes", []):
                    self.assertIn(code, codes)
                self.assertEqual(warn_count, case["expected_warn_count"])


if __name__ == "__main__":
    unittest.main()
