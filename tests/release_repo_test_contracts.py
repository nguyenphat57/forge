from __future__ import annotations

import json
import os
import shutil
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
        self.assertTrue((ROOT_DIR / "docs" / "release" / "package-matrix.json").exists())
        self.assertTrue((ROOT_DIR / "docs" / "release" / "release-process.md").exists())

    def test_architecture_docs_enforce_core_purity(self) -> None:
        boundary = (ROOT_DIR / "docs" / "architecture" / "adapter-boundary.md").read_text(encoding="utf-8")
        monorepo = (ROOT_DIR / "docs" / "architecture" / "monorepo.md").read_text(encoding="utf-8")
        release_process = (ROOT_DIR / "docs" / "release" / "release-process.md").read_text(encoding="utf-8")

        self.assertIn("forge-claude", boundary)
        self.assertIn("forge-core", boundary)
        self.assertIn("adapter-boundary.md", monorepo)
        self.assertIn("architecture-layers.md", monorepo)
        self.assertIn("generated artifacts", monorepo)
        self.assertIn("workflow state", monorepo)
        self.assertIn("runtime tools", monorepo)
        self.assertIn("forge-claude", release_process)
        self.assertIn("core purity", release_process.lower())
        self.assertIn("package-matrix.json", release_process)

    def test_build_release_manifest_carries_version(self) -> None:
        build_release.build_all()
        manifest = json.loads((ROOT_DIR / "dist" / "forge-core" / "BUILD-MANIFEST.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["version"], build_release.read_version())
        self.assertEqual(manifest["package"], "forge-core")
        self.assertIn("git_revision", manifest)
        self.assertEqual(manifest["packaging"]["matrix_path"], "docs/release/package-matrix.json")
        self.assertEqual(manifest["packaging"]["default_target_strategy"], "explicit")
        self.assertIn("scripts/write_preferences.py", manifest["packaging"]["required_bundle_paths"])
        self.assertEqual(manifest["bundle_fingerprint"]["mode"], "path-content-sha256-v1")
        self.assertGreater(manifest["bundle_fingerprint"]["file_count"], 0)
        self.assertEqual(len(manifest["bundle_fingerprint"]["sha256"]), 64)
        self.assertEqual(manifest["generated_artifacts"]["manifest_path"], "docs/architecture/host-artifacts-manifest.json")
        self.assertEqual(manifest["generated_artifacts"]["artifacts"], [])

    def test_build_release_includes_runtime_tool_bundle(self) -> None:
        build_release.build_all()
        manifest = json.loads((ROOT_DIR / "dist" / "forge-browse" / "BUILD-MANIFEST.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["version"], build_release.read_version())
        self.assertEqual(manifest["package"], "forge-browse")
        self.assertEqual(manifest["host"], "runtime")
        self.assertEqual(manifest["packaging"]["default_target_strategy"], "explicit")
        self.assertIn("scripts/forge_browse.py", manifest["packaging"]["required_bundle_paths"])
        self.assertIn("scripts/browse_packets.py", manifest["packaging"]["required_bundle_paths"])
        self.assertIn("scripts/browse_runtime.py", manifest["packaging"]["required_bundle_paths"])
        self.assertEqual(manifest["generated_artifacts"]["artifacts"], [])
        self.assertTrue((ROOT_DIR / "dist" / "forge-browse" / "runtime.json").exists())

    def test_build_release_includes_design_runtime_bundle(self) -> None:
        build_release.build_all()
        manifest = json.loads((ROOT_DIR / "dist" / "forge-design" / "BUILD-MANIFEST.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["version"], build_release.read_version())
        self.assertEqual(manifest["package"], "forge-design")
        self.assertEqual(manifest["host"], "runtime")
        self.assertEqual(manifest["packaging"]["default_target_strategy"], "explicit")
        self.assertIn("scripts/forge_design.py", manifest["packaging"]["required_bundle_paths"])
        self.assertIn("scripts/design_browse_live_smoke.py", manifest["packaging"]["required_bundle_paths"])
        self.assertIn("scripts/design_packet.py", manifest["packaging"]["required_bundle_paths"])
        self.assertTrue((ROOT_DIR / "dist" / "forge-design" / "runtime.json").exists())

    def test_build_release_includes_nextjs_companion_bundle(self) -> None:
        build_release.build_all()
        manifest = json.loads((ROOT_DIR / "dist" / "forge-nextjs-typescript-postgres" / "BUILD-MANIFEST.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["version"], build_release.read_version())
        self.assertEqual(manifest["package"], "forge-nextjs-typescript-postgres")
        self.assertEqual(manifest["host"], "companion")
        self.assertEqual(manifest["packaging"]["default_target_strategy"], "explicit")
        self.assertIn("companion.json", manifest["packaging"]["required_bundle_paths"])
        self.assertIn("scripts/scaffold_preset.py", manifest["packaging"]["required_bundle_paths"])
        self.assertIn("templates/auth-saas/package.json", manifest["packaging"]["required_bundle_paths"])
        self.assertIn("templates/billing-saas/package.json", manifest["packaging"]["required_bundle_paths"])
        self.assertTrue((ROOT_DIR / "dist" / "forge-nextjs-typescript-postgres" / "companion.json").exists())

    def test_build_release_includes_codex_generated_wrapper_artifacts(self) -> None:
        build_release.build_all()
        manifest = json.loads((ROOT_DIR / "dist" / "forge-codex" / "BUILD-MANIFEST.json").read_text(encoding="utf-8"))

        outputs = {item["bundle_output"] for item in manifest["generated_artifacts"]["artifacts"]}
        required = set(manifest["packaging"]["required_bundle_paths"])

        self.assertIn("workflows/execution/session.md", required)
        self.assertIn("workflows/operator/help.md", required)
        self.assertIn("workflows/operator/next.md", required)
        self.assertIn("workflows/operator/run.md", required)
        self.assertIn("workflows/operator/customize.md", required)
        self.assertIn("workflows/operator/init.md", required)
        self.assertIn("workflows/execution/session.md", outputs)
        self.assertIn("workflows/operator/help.md", outputs)
        self.assertIn("workflows/operator/next.md", outputs)
        self.assertIn("workflows/operator/run.md", outputs)

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

    def test_uninstalled_dist_runtime_tool_uses_bundle_state_root(self) -> None:
        build_release.build_all()
        script_path = ROOT_DIR / "dist" / "forge-browse" / "scripts" / "forge_browse.py"
        expected_state_root = (ROOT_DIR / "dist" / "forge-browse-state").resolve()
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "session-create",
                    "--label",
                    "smoke",
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)

            self.assertEqual(payload["state"]["root"], str(expected_state_root))
            self.assertEqual(payload["state"]["sessions_path"], str((expected_state_root / "state" / "sessions.json").resolve()))
            self.assertTrue(payload["session"]["artifacts_dir"].startswith(str(expected_state_root)))
        finally:
            shutil.rmtree(expected_state_root, ignore_errors=True)

    def test_uninstalled_dist_host_bundle_reads_runtime_registry_path_from_manifest(self) -> None:
        build_release.build_all()
        script_path = ROOT_DIR / "dist" / "forge-codex" / "scripts" / "resolve_runtime_tool.py"

        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "forge-browse",
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)

        self.assertEqual(
            payload["registry_path"],
            str((ROOT_DIR / "dist" / "forge-codex" / "state" / "runtime-tools.json").resolve()),
        )
        self.assertEqual(payload["resolution_source"], "bundle-neighbor")

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
