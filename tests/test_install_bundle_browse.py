from __future__ import annotations

import unittest

import install_bundle


class RetiredBundleInstallTests(unittest.TestCase):
    def test_retired_bundle_names_are_not_in_install_cli_choices(self) -> None:
        bundle_names = install_bundle.bundle_names()

        self.assertNotIn("forge-browse", bundle_names)
        self.assertNotIn("forge-design", bundle_names)

    def test_install_bundle_rejects_retired_bundle_names(self) -> None:
        for bundle_name in ("forge-browse", "forge-design"):
            with self.subTest(bundle=bundle_name):
                with self.assertRaises(KeyError):
                    install_bundle.install_bundle(bundle_name, dry_run=True)


if __name__ == "__main__":
    unittest.main()
