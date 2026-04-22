from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from release_repo_test_support import ROOT_DIR, ReleaseRepoTestSupport, build_release


class ReleaseRepoContractTests(ReleaseRepoTestSupport):
    def init_git_repo(self, root: Path) -> None:
        subprocess.run(["git", "init"], cwd=root, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, capture_output=True, check=True)

    def commit_readme(self, root: Path) -> None:
        readme = root / "README.md"
        readme.write_text("safe text only\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "add readme"], cwd=root, capture_output=True, check=True)

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
        self.assertIn("git_tree", release_process)
        self.assertIn("modified_files", release_process)
        self.assertIn("untracked_files", release_process)

    def test_runtime_era_packages_are_archived_out_of_current_package_root(self) -> None:
        self.assertFalse((ROOT_DIR / "packages" / "forge-browse").exists())
        self.assertFalse((ROOT_DIR / "packages" / "forge-design").exists())
        self.assertFalse((ROOT_DIR / "archive" / "packages" / "forge-browse").exists())
        self.assertFalse((ROOT_DIR / "archive" / "packages" / "forge-design").exists())

    def test_current_docs_do_not_reference_retired_runtime_tool_commands(self) -> None:
        current_paths = [
            ROOT_DIR / "README.md",
            ROOT_DIR / "docs" / "architecture" / "monorepo.md",
            ROOT_DIR / "docs" / "current" / "architecture.md",
            ROOT_DIR / "docs" / "current" / "install-and-activation.md",
            ROOT_DIR / "docs" / "current" / "operator-surface.md",
            ROOT_DIR / "docs" / "release" / "install.md",
            ROOT_DIR / "docs" / "release" / "release-process.md",
            ROOT_DIR / "packages" / "forge-core" / "references" / "backend-briefs.md",
            ROOT_DIR / "packages" / "forge-core" / "references" / "reference-map.md",
            ROOT_DIR / "packages" / "forge-core" / "references" / "tooling.md",
            ROOT_DIR / "packages" / "forge-core" / "references" / "ui-briefs.md",
        ]

        for needle in (
            "resolve_runtime_tool.py",
            "invoke_runtime_tool.py",
            "forge-browse",
            "forge-design",
            "archive/packages/",
        ):
            for path in current_paths:
                with self.subTest(path=path.name, needle=needle):
                    self.assertNotIn(needle, path.read_text(encoding="utf-8"))

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

    def test_git_tree_provenance_distinguishes_clean_modified_and_untracked_states(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.init_git_repo(root)
            self.commit_readme(root)

            clean = build_release.resolve_git_tree_provenance(root)
            self.assertTrue(clean["available"])
            self.assertEqual(clean["state"], "clean")
            self.assertEqual(clean["modified_files"], [])
            self.assertEqual(clean["untracked_files"], [])

            (root / "README.md").write_text("updated text\n", encoding="utf-8")
            modified = build_release.resolve_git_tree_provenance(root)
            self.assertTrue(modified["available"])
            self.assertEqual(modified["state"], "modified")
            self.assertIn("README.md", modified["modified_files"])
            self.assertEqual(modified["untracked_files"], [])

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.init_git_repo(root)
            self.commit_readme(root)

            (root / "leak.env").write_text("untracked text\n", encoding="utf-8")
            untracked = build_release.resolve_git_tree_provenance(root)
            self.assertTrue(untracked["available"])
            self.assertEqual(untracked["state"], "untracked")
            self.assertEqual(untracked["modified_files"], [])
            self.assertIn("leak.env", untracked["untracked_files"])

    def test_build_release_manifest_carries_git_tree_provenance(self) -> None:
        provenance = {
            "available": True,
            "state": "untracked",
            "modified_files": ["README.md"],
            "untracked_files": ["leak.env"],
        }

        with patch.object(build_release, "resolve_git_tree_provenance", return_value=provenance):
            build_release.build_all()

        manifest = json.loads((ROOT_DIR / "dist" / "forge-core" / "BUILD-MANIFEST.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["git_tree"], provenance)
        self.assertEqual(manifest["git_tree"]["state"], "untracked")
        self.assertEqual(manifest["git_tree"]["modified_files"], ["README.md"])
        self.assertEqual(manifest["git_tree"]["untracked_files"], ["leak.env"])
        self.assertIn("git_revision", manifest)

    def test_build_release_excludes_retired_bundle_outputs(self) -> None:
        build_release.build_all()
        for bundle_name in ("forge-browse", "forge-design", "forge-nextjs-typescript-postgres"):
            with self.subTest(bundle=bundle_name):
                self.assertFalse((ROOT_DIR / "dist" / bundle_name).exists())

    def test_build_release_skips_source_only_example_bundle(self) -> None:
        stale_dist = ROOT_DIR / "dist" / "forge-nextjs-typescript-postgres"
        stale_dist.mkdir(parents=True, exist_ok=True)
        (stale_dist / "stale.txt").write_text("stale", encoding="utf-8")
        build_release.build_all()

        self.assertFalse(stale_dist.exists())

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
                    self.assertEqual(
                        payload["targets"],
                        [str((expected_state_root / "state" / "preferences.json").resolve())],
                    )
                    self.assertFalse((home / ".forge").exists())

    def test_split_skill_target_tokens_are_visible(self) -> None:
        target_state = (ROOT_DIR / "packages" / "forge-core" / "references" / "target-state.md").read_text(encoding="utf-8")
        reference_map = (ROOT_DIR / "packages" / "forge-core" / "references" / "reference-map.md").read_text(encoding="utf-8")
        skill = (ROOT_DIR / "packages" / "forge-core" / "SKILL.md").read_text(encoding="utf-8")

        for token in (
            "split-skill",
            "skill-first",
            "Host-discoverable Forge sibling skills",
            "line-budget reductions",
        ):
            with self.subTest(token=token):
                self.assertIn(token, target_state)

        for token in ("packages/forge-core/skills/", "architecture-layers.md", "help-next.md"):
            with self.subTest(reference_token=token):
                self.assertIn(token, reference_map)

        for token in ("Forge sibling skills", "1% chance", "Proof before claims"):
            with self.subTest(skill_token=token):
                self.assertIn(token, skill)

    def test_current_split_skill_operating_contract_tokens_are_visible(self) -> None:
        target_state = (ROOT_DIR / "packages" / "forge-core" / "references" / "target-state.md").read_text(encoding="utf-8")
        reference_map = (ROOT_DIR / "packages" / "forge-core" / "references" / "reference-map.md").read_text(encoding="utf-8")

        for token in (
            "## Current Contract Closure",
            "bootstrap-driven sibling skill activation",
            "process skills before implementation skills",
            "Escalate into an explicit roadmap or product decision only if",
        ):
            with self.subTest(target_token=token):
                self.assertIn(token, target_state)

        for token in (
            "current split-skill",
            "When verifying current contract alignment",
            "Do not teach `workflows/` files as the primary activation surface.",
        ):
            with self.subTest(reference_token=token):
                self.assertIn(token, reference_map)

    def test_surface_slim_split_skill_tokens_are_visible(self) -> None:
        target_state = (ROOT_DIR / "packages" / "forge-core" / "references" / "target-state.md").read_text(encoding="utf-8")
        reference_map = (ROOT_DIR / "packages" / "forge-core" / "references" / "reference-map.md").read_text(encoding="utf-8")

        for token in (
            "docs/current/",
            "packages/forge-core/skills/*/SKILL.md",
            "generated host artifacts bootstrap-only",
            "There is no active roadmap tranche now.",
        ):
            with self.subTest(target_token=token):
                self.assertIn(token, target_state)

        for token in (
            "docs/current/operator-surface.md",
            "docs/current/install-and-activation.md",
            "docs/archive/INDEX.md",
        ):
            with self.subTest(reference_token=token):
                self.assertIn(token, reference_map)

    def test_readme_start_here_onboarding_tokens_remain_visible(self) -> None:
        readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("Evidence-first execution kernel", readme)
        self.assertIn("Current stable release", readme)
        self.assertIn("Start Here (Solo Operator)", readme)
        self.assertIn("verify_repo.py --profile fast", readme)
        self.assertIn("bounded slice", readme)

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
            "Proof before claims is non-negotiable",
            core_skill.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Proof before claims is non-negotiable",
            antigravity_skill.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Proof before claims is non-negotiable",
            codex_skill.read_text(encoding="utf-8"),
        )
        self.assert_bump_wrapper_matches_release_contract(antigravity_bump, label="forge-antigravity")
        self.assert_bump_wrapper_matches_release_contract(codex_bump, label="forge-codex")
