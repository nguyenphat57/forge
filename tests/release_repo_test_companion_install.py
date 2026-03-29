from __future__ import annotations

from release_repo_test_support import ReleaseRepoTestSupport, install_bundle


class ReleaseRepoCompanionInstallTests(ReleaseRepoTestSupport):
    def test_source_only_example_companion_is_absent_from_install_cli_choices(self) -> None:
        self.assertNotIn("forge-nextjs-typescript-postgres", install_bundle.bundle_names())
