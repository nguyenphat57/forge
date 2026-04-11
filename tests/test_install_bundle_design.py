from __future__ import annotations

import json
import unittest
from pathlib import Path

import build_release
import install_bundle


ROOT_DIR = Path(__file__).resolve().parents[1]


class RetiredBundleMatrixTests(unittest.TestCase):
    def test_build_release_only_keeps_kernel_bundles(self) -> None:
        build_release.build_all(force=True)

        self.assertTrue((ROOT_DIR / "dist" / "forge-core").exists())
        self.assertTrue((ROOT_DIR / "dist" / "forge-codex").exists())
        self.assertTrue((ROOT_DIR / "dist" / "forge-antigravity").exists())
        self.assertFalse((ROOT_DIR / "dist" / "forge-browse").exists())
        self.assertFalse((ROOT_DIR / "dist" / "forge-design").exists())

    def test_install_cli_choices_match_kernel_only_bundle_set(self) -> None:
        self.assertEqual(
            install_bundle.bundle_names(),
            ["forge-core", "forge-antigravity", "forge-codex"],
        )

    def test_package_matrix_serializes_three_bundles(self) -> None:
        package_matrix = json.loads((ROOT_DIR / "docs" / "release" / "package-matrix.json").read_text(encoding="utf-8"))
        self.assertEqual([bundle["name"] for bundle in package_matrix["bundles"]], ["forge-core", "forge-antigravity", "forge-codex"])


if __name__ == "__main__":
    unittest.main()
