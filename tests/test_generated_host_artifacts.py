from __future__ import annotations

from release_repo_test_support import ReleaseRepoTestSupport
import host_artifact_manifest  # noqa: E402
import host_artifacts_support  # noqa: E402


class GeneratedHostArtifactTests(ReleaseRepoTestSupport):
    def test_repo_generated_host_artifacts_are_fresh(self) -> None:
        report = host_artifacts_support.ensure_generated_host_artifacts(check=True)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["stale_outputs"], [])
        self.assertGreaterEqual(len(report["artifacts"]), 9)
        names = {artifact["name"] for artifact in report["artifacts"]}
        self.assertIn("source-repo-operator-surface", names)
        for artifact in report["artifacts"]:
            with self.subTest(artifact=artifact["name"]):
                self.assertTrue(artifact["output_exists"])
                self.assertFalse(artifact["stale"])
                self.assertEqual(len(artifact["source_sha256"]), 64)
                self.assertEqual(len(artifact["output_sha256"]), 64)

    def test_manifest_entries_resolve_to_valid_outputs(self) -> None:
        specs = host_artifact_manifest.generated_host_artifact_specs()
        self.assertGreaterEqual(len(specs), 9)
        for spec in specs:
            with self.subTest(name=spec["name"]):
                self.assertTrue(spec["source_path"].exists())
                if spec["target_kind"] == "bundle-overlay":
                    self.assertTrue(spec["output"].startswith(f"packages/{spec['bundle']}/overlay/"))
                else:
                    self.assertEqual(spec["bundle"], "source-repo")
                    self.assertEqual(spec["output"], "docs/current/operator-surface.md")


if __name__ == "__main__":
    import unittest

    unittest.main()
