from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class DesignContractTests(unittest.TestCase):
    def test_runtime_manifest_declares_runtime_tool_state(self) -> None:
        manifest = json.loads((ROOT_DIR / "runtime.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["kind"], "runtime-tool")
        self.assertEqual(manifest["host"], "runtime")
        self.assertEqual(manifest["state"]["scope"], "runtime-tool-global")
        self.assertEqual(manifest["state"]["renders_relative_path"], "state/renders.jsonl")
        self.assertEqual(manifest["state"]["packets_relative_dir"], "packets")

    def test_readme_and_verify_bundle_document_browse_capture_smoke(self) -> None:
        readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
        verify_bundle = (ROOT_DIR / "scripts" / "verify_bundle.py").read_text(encoding="utf-8")

        self.assertIn("forge-browse", readme)
        self.assertIn("support an env-gated live smoke", readme)
        self.assertIn("FORGE_DESIGN_RUN_BROWSE_SMOKE", verify_bundle)
        self.assertIn("FORGE_BROWSE_RUN_PLAYWRIGHT_SMOKE", verify_bundle)
        self.assertIn("design_browse_live_smoke.py", verify_bundle)


if __name__ == "__main__":
    unittest.main()
