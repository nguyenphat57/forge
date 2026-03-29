from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class BrowseContractTests(unittest.TestCase):
    def test_readme_declares_canonical_cli_and_optional_server(self) -> None:
        readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")

        self.assertIn("`forge_browse.py` is the canonical operator entrypoint.", readme)
        self.assertIn("`browse_server.py` is an optional local HTTP control plane", readme)
        self.assertIn("reusable QA packets", readme)
        self.assertIn("login-aware QA packets", readme)
        self.assertIn("FORGE_BROWSE_RUN_PLAYWRIGHT_SMOKE", readme)

    def test_runtime_manifest_and_verify_script_share_live_smoke_contract(self) -> None:
        runtime_manifest = json.loads((ROOT_DIR / "runtime.json").read_text(encoding="utf-8"))
        verify_bundle = (ROOT_DIR / "scripts" / "verify_bundle.py").read_text(encoding="utf-8")

        self.assertEqual(runtime_manifest["kind"], "runtime-tool")
        self.assertEqual(runtime_manifest["host"], "runtime")
        self.assertIn("FORGE_BROWSE_RUN_PLAYWRIGHT_SMOKE", verify_bundle)
        self.assertIn("playwright_live_smoke.py", verify_bundle)


if __name__ == "__main__":
    unittest.main()
