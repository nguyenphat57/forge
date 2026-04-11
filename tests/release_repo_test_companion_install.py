from __future__ import annotations

from release_repo_test_support import ReleaseRepoTestSupport, install_bundle


class ReleaseRepoRetiredBundleInstallTests(ReleaseRepoTestSupport):
    def test_retired_example_bundle_is_absent_from_install_cli_choices(self) -> None:
        self.assertNotIn("forge-nextjs-typescript-postgres", install_bundle.bundle_names())

    def test_retired_runtime_bundles_are_absent_from_install_cli_choices(self) -> None:
        bundle_names = install_bundle.bundle_names()
        self.assertNotIn("forge-browse", bundle_names)
        self.assertNotIn("forge-design", bundle_names)


if __name__ == "__main__":
    import unittest

    unittest.main()
