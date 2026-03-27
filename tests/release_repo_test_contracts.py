from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from release_repo_test_support import ROOT_DIR, ReleaseRepoTestSupport, build_release


class ReleaseRepoContractTests(ReleaseRepoTestSupport):
    def test_release_docs_and_version_exist(self) -> None:
        version = (ROOT_DIR / "VERSION").read_text(encoding="utf-8").strip()

        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        self.assertTrue((ROOT_DIR / "CHANGELOG.md").exists())
        self.assertTrue((ROOT_DIR / "docs" / "architecture" / "adapter-boundary.md").exists())
        self.assertTrue((ROOT_DIR / "docs" / "release" / "install.md").exists())
        self.assertTrue((ROOT_DIR / "docs" / "release" / "release-process.md").exists())

    def test_architecture_docs_enforce_core_purity(self) -> None:
        boundary = (ROOT_DIR / "docs" / "architecture" / "adapter-boundary.md").read_text(encoding="utf-8")
        monorepo = (ROOT_DIR / "docs" / "architecture" / "monorepo.md").read_text(encoding="utf-8")
        release_process = (ROOT_DIR / "docs" / "release" / "release-process.md").read_text(encoding="utf-8")

        self.assertIn("forge-claude", boundary)
        self.assertIn("forge-core", boundary)
        self.assertIn("adapter-boundary.md", monorepo)
        self.assertIn("forge-claude", release_process)
        self.assertIn("core purity", release_process.lower())

    def test_build_release_manifest_carries_version(self) -> None:
        build_release.build_all()
        manifest = json.loads((ROOT_DIR / "dist" / "forge-core" / "BUILD-MANIFEST.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["version"], build_release.read_version())
        self.assertEqual(manifest["package"], "forge-core")
        self.assertIn("git_revision", manifest)

    def test_build_release_keeps_core_bundle_english_only(self) -> None:
        build_release.build_all()
        dist_root = ROOT_DIR / "dist" / "forge-core"

        self.assertFalse((dist_root / "data" / "routing-locales.json").exists())
        self.assertFalse((dist_root / "data" / "routing-locales").exists())
        self.assertFalse((dist_root / "data" / "output-contracts.json").exists())

    def test_uninstalled_dist_bundles_use_bundle_native_state_roots(self) -> None:
        build_release.build_all()
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            home = temp_root / "home"
            home.mkdir(parents=True, exist_ok=True)
            cases = [
                (
                    "forge-core",
                    ROOT_DIR / "dist" / "forge-core" / "scripts" / "write_preferences.py",
                    (ROOT_DIR / "dist" / "forge-core-state").resolve(),
                ),
                (
                    "forge-codex",
                    ROOT_DIR / "dist" / "forge-codex" / "scripts" / "write_preferences.py",
                    (home / ".codex" / "forge-codex").resolve(),
                ),
                (
                    "forge-antigravity",
                    ROOT_DIR / "dist" / "forge-antigravity" / "scripts" / "write_preferences.py",
                    (home / ".gemini" / "antigravity" / "forge-antigravity").resolve(),
                ),
            ]

            for bundle_name, script_path, expected_state_root in cases:
                with self.subTest(bundle=bundle_name):
                    env = os.environ.copy()
                    env.pop("FORGE_HOME", None)
                    env.pop("CODEX_HOME", None)
                    env.pop("GEMINI_HOME", None)
                    env["USERPROFILE"] = str(home)
                    env["HOME"] = str(home)

                    result = subprocess.run(
                        [
                            sys.executable,
                            str(script_path),
                            "--technical-level",
                            "technical",
                            "--format",
                            "json",
                        ],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        check=False,
                        env=env,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    payload = json.loads(result.stdout)

                    self.assertEqual(payload["state_root"], str(expected_state_root))
                    self.assertEqual(payload["path"], str((expected_state_root / "state" / "preferences.json").resolve()))
                    self.assertFalse((home / ".forge").exists())

    def test_adapter_bump_contracts_stay_aligned_with_core(self) -> None:
        core_bump = ROOT_DIR / "packages" / "forge-core" / "workflows" / "operator" / "bump.md"
        core_skill = ROOT_DIR / "packages" / "forge-core" / "SKILL.md"
        antigravity_bump = ROOT_DIR / "packages" / "forge-antigravity" / "overlay" / "workflows" / "operator" / "bump.md"
        antigravity_skill = ROOT_DIR / "packages" / "forge-antigravity" / "overlay" / "SKILL.md"
        codex_bump = ROOT_DIR / "packages" / "forge-codex" / "overlay" / "workflows" / "operator" / "bump.md"
        codex_skill = ROOT_DIR / "packages" / "forge-codex" / "overlay" / "SKILL.md"

        self.assertIn(
            "Current version is stated and target version is either explicit or justified by inference",
            core_bump.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "VERSION BUMPS MUST BE USER-REQUESTED, JUSTIFIED, AND MUST SURFACE RELEASE VERIFICATION",
            core_skill.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "VERSION BUMPS MUST BE USER-REQUESTED, JUSTIFIED, AND MUST SURFACE RELEASE VERIFICATION",
            antigravity_skill.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "VERSION BUMPS MUST BE USER-REQUESTED, JUSTIFIED, AND MUST SURFACE RELEASE VERIFICATION",
            codex_skill.read_text(encoding="utf-8"),
        )
        self.assert_bump_wrapper_matches_release_contract(antigravity_bump, label="forge-antigravity")
        self.assert_bump_wrapper_matches_release_contract(codex_bump, label="forge-codex")
