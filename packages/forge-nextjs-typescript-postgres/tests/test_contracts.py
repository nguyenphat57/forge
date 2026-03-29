from __future__ import annotations

import json
import unittest
from pathlib import Path

from support import ROOT_DIR


class CompanionContractTests(unittest.TestCase):
    def test_companion_manifest_and_capabilities_exist(self) -> None:
        manifest = json.loads((ROOT_DIR / "companion.json").read_text(encoding="utf-8"))
        capabilities = json.loads((ROOT_DIR / "data" / "companion-capabilities.json").read_text(encoding="utf-8"))
        repo_version = (ROOT_DIR.parents[1] / "VERSION").read_text(encoding="utf-8").strip()

        self.assertEqual(manifest["name"], "forge-nextjs-typescript-postgres")
        self.assertEqual(manifest["kind"], "companion")
        self.assertEqual(capabilities["id"], "nextjs-typescript-postgres")
        self.assertEqual(capabilities["version"], repo_version)
        self.assertEqual(capabilities["compatibility"]["forge_core_min"], repo_version)
        self.assertEqual(capabilities["compatibility"]["forge_core_max"], "1.x")
        self.assertTrue((ROOT_DIR / capabilities["init_presets"][0]["template_dir"]).exists())
        self.assertEqual(
            {item["id"] for item in capabilities["init_presets"]},
            {"minimal-saas", "auth-saas", "billing-saas", "deploy-observability"},
        )

    def test_template_catalog_points_to_real_paths(self) -> None:
        capabilities = json.loads((ROOT_DIR / "data" / "companion-capabilities.json").read_text(encoding="utf-8"))
        for item in capabilities["template_catalog"] + capabilities["example_catalog"]:
            with self.subTest(item=item["id"]):
                self.assertTrue((ROOT_DIR / item["path"]).exists(), Path(item["path"]))


if __name__ == "__main__":
    unittest.main()
