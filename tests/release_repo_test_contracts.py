from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from release_repo_test_support import ROOT_DIR, ReleaseRepoTestSupport, build_release

EXPECTED_SIBLING_SKILL_REFERENCES = {
    "forge-init": [
        "references/project-docs-blueprint.md",
    ],
    "forge-brainstorming": [
        "references/design/architectural-lens.md",
        "references/design/visual-companion-guidance.md",
    ],
    "forge-subagent-driven-development": [
        "references/subagent-execution.md",
        "references/subagent-prompts/final-reviewer-prompt.md",
        "references/subagent-prompts/implementer-prompt.md",
        "references/subagent-prompts/quality-reviewer-prompt.md",
        "references/subagent-prompts/spec-reviewer-prompt.md",
    ],
    "forge-systematic-debugging": [
        "references/debugging/condition-based-waiting.md",
        "references/debugging/defense-in-depth.md",
        "references/debugging/root-cause-tracing.md",
    ],
    "forge-customize": [
        "references/forge-preferences.md",
        "references/forge-paths.md",
    ],
    "forge-bump-release": [
        "references/bump-release.md",
        "references/scripts/prepare_bump.py",
        "references/scripts/prepare_bump_git.py",
        "references/scripts/prepare_bump_report.py",
        "references/scripts/prepare_bump_semver.py",
    ],
    "forge-deploy": [
        "references/deploy-contract.md",
        "references/deploy-checks.md",
        "references/rollback-guidance.md",
    ],
}


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
        architecture_layers = (ROOT_DIR / "docs" / "architecture" / "architecture-layers.md").read_text(encoding="utf-8")
        monorepo = (ROOT_DIR / "docs" / "architecture" / "monorepo.md").read_text(encoding="utf-8")
        release_process = (ROOT_DIR / "docs" / "release" / "release-process.md").read_text(encoding="utf-8")

        self.assertIn("forge-claude", boundary)
        self.assertIn("forge-core", boundary)
        self.assertIn("packages/forge-core/shared/", architecture_layers)
        self.assertIn("packages/forge-core/commands/", architecture_layers)
        self.assertNotIn("packages/forge-core/engine/", architecture_layers)
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
            ROOT_DIR / "docs" / "current" / "kernel-tooling.md",
            ROOT_DIR / "docs" / "current" / "target-state.md",
            ROOT_DIR / "docs" / "architecture" / "architecture-layers.md",
            ROOT_DIR / "docs" / "release" / "install.md",
            ROOT_DIR / "docs" / "release" / "release-process.md",
            ROOT_DIR / "packages" / "forge-skills" / "brainstorming" / "references" / "backend-briefs.md",
            ROOT_DIR / "packages" / "forge-skills" / "brainstorming" / "references" / "ui-briefs.md",
        ]

        for needle in (
            "resolve_runtime_tool.py",
            "invoke_runtime_tool.py",
            "forge-browse",
            "forge-design",
            "archive/packages/",
            "engine/forge_core_runtime",
            "packages/forge-core/engine/",
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
        self.assertIn("shared/common.py", manifest["packaging"]["required_bundle_paths"])
        self.assertIn("commands/capture_continuity.py", manifest["packaging"]["required_bundle_paths"])
        self.assertNotIn("commands/initialize_workspace.py", manifest["packaging"]["required_bundle_paths"])
        self.assertNotIn("commands/_forge_skill_command.py", manifest["packaging"]["required_bundle_paths"])
        self.assertNotIn("commands/write_preferences.py", manifest["packaging"]["required_bundle_paths"])
        self.assertNotIn("commands/resolve_preferences.py", manifest["packaging"]["required_bundle_paths"])
        self.assertNotIn("data/preferences-schema.json", manifest["packaging"]["required_bundle_paths"])
        self.assertNotIn("shared/compat.py", manifest["packaging"]["required_bundle_paths"])
        self.assertFalse(
            any(path.startswith("engine/") for path in manifest["packaging"]["required_bundle_paths"])
        )
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
        metadata = {
            "version": build_release.read_version(),
            "git_revision": build_release.resolve_git_revision(),
            "git_tree": provenance,
        }
        build_release.build_core_bundle(metadata, force=True)

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

    def test_build_release_includes_codex_generated_artifacts_without_workflows(self) -> None:
        build_release.build_all()
        manifest = json.loads((ROOT_DIR / "dist" / "forge-codex" / "BUILD-MANIFEST.json").read_text(encoding="utf-8"))
        agents_text = (ROOT_DIR / "dist" / "forge-codex" / "AGENTS.global.md").read_text(encoding="utf-8")
        gemini_text = (ROOT_DIR / "dist" / "forge-antigravity" / "GEMINI.global.md").read_text(encoding="utf-8")

        outputs = {item["bundle_output"] for item in manifest["generated_artifacts"]["artifacts"]}
        required = set(manifest["packaging"]["required_bundle_paths"])

        self.assertNotIn("workflows/operator/session.md", required)
        self.assertNotIn("workflows/operator/help.md", required)
        self.assertNotIn("workflows/operator/next.md", required)
        self.assertNotIn("workflows/operator/run.md", required)
        self.assertNotIn("workflows/operator/bump.md", required)
        self.assertFalse(any(path.startswith("workflows/") for path in required))
        self.assertNotIn("workflows/operator/session.md", outputs)
        self.assertNotIn("workflows/operator/help.md", outputs)
        self.assertNotIn("workflows/operator/next.md", outputs)
        self.assertNotIn("workflows/operator/run.md", outputs)
        self.assertNotIn("workflows/operator/bump.md", outputs)
        self.assertFalse(any(path.startswith("workflows/") for path in outputs))
        self.assertNotIn("Compatibility aliases:", agents_text)
        self.assertNotIn("Operator aliases:", agents_text)
        self.assertNotIn("/delegate", agents_text)
        self.assertNotIn("/customize", agents_text)
        self.assertNotIn("/init", agents_text)
        self.assertNotIn("Compatibility aliases:", gemini_text)
        self.assertNotIn("Primary operator aliases:", gemini_text)
        self.assertNotIn("/customize", gemini_text)
        self.assertNotIn("/init", gemini_text)

    def test_release_bundles_do_not_materialize_init_runtime_outside_owner_skill(self) -> None:
        build_release.build_all()

        for bundle_name in ("forge-core", "forge-codex", "forge-antigravity"):
            with self.subTest(bundle=bundle_name):
                self.assertFalse((ROOT_DIR / "dist" / bundle_name / "commands" / "initialize_workspace.py").exists())
                self.assertFalse((ROOT_DIR / "dist" / bundle_name / "commands" / "_forge_skill_command.py").exists())
        self.assertTrue(
            (ROOT_DIR / "dist" / "forge-init" / "commands" / "initialize_workspace.py").exists()
        )
        self.assertTrue(
            (ROOT_DIR / "dist" / "forge-init" / "commands" / "_forge_skill_command.py").exists()
        )

    def test_release_bundles_do_not_materialize_customize_runtime_outside_owner_skill(self) -> None:
        build_release.build_all()

        for bundle_name in ("forge-core", "forge-codex", "forge-antigravity"):
            with self.subTest(bundle=bundle_name):
                self.assertFalse((ROOT_DIR / "dist" / bundle_name / "commands" / "resolve_preferences.py").exists())
                self.assertFalse((ROOT_DIR / "dist" / bundle_name / "commands" / "write_preferences.py").exists())
                self.assertFalse((ROOT_DIR / "dist" / bundle_name / "commands" / "_forge_customize_command.py").exists())
                self.assertFalse((ROOT_DIR / "dist" / bundle_name / "data" / "preferences-schema.json").exists())
                self.assertFalse((ROOT_DIR / "dist" / bundle_name / "shared" / "compat.py").exists())
                self.assertFalse((ROOT_DIR / "dist" / bundle_name / "shared" / "preferences.py").exists())

        self.assertTrue((ROOT_DIR / "dist" / "forge-customize" / "commands" / "resolve_preferences.py").exists())
        self.assertTrue((ROOT_DIR / "dist" / "forge-customize" / "commands" / "write_preferences.py").exists())
        self.assertTrue((ROOT_DIR / "dist" / "forge-customize" / "commands" / "_forge_customize_command.py").exists())
        self.assertTrue((ROOT_DIR / "dist" / "forge-customize" / "data" / "preferences-schema.json").exists())
        self.assertTrue((ROOT_DIR / "dist" / "forge-customize" / "shared" / "compat.py").exists())
        self.assertTrue((ROOT_DIR / "dist" / "forge-customize" / "shared" / "preferences.py").exists())

    def test_core_workflow_tree_is_retired(self) -> None:
        build_release.build_all()

        for base in (
            ROOT_DIR / "packages" / "forge-core",
            ROOT_DIR / "dist" / "forge-core",
        ):
            with self.subTest(base=base):
                self.assertFalse((base / "workflows").exists())

    def test_build_release_keeps_core_bundle_english_only(self) -> None:
        build_release.build_all()
        dist_root = ROOT_DIR / "dist" / "forge-core"

        self.assertFalse((dist_root / "data" / "routing-locales.json").exists())
        self.assertFalse((dist_root / "data" / "routing-locales").exists())
        self.assertFalse((dist_root / "data" / "output-contracts.json").exists())

    def test_uninstalled_dist_bundles_do_not_ship_customize_runtime_commands(self) -> None:
        build_release.build_all()

        for bundle_name in ("forge-core", "forge-codex", "forge-antigravity"):
            with self.subTest(bundle=bundle_name):
                self.assertFalse((ROOT_DIR / "dist" / bundle_name / "commands" / "write_preferences.py").exists())
                self.assertFalse((ROOT_DIR / "dist" / bundle_name / "commands" / "resolve_preferences.py").exists())

    def test_split_skill_target_tokens_are_visible(self) -> None:
        target_state = (ROOT_DIR / "docs" / "current" / "target-state.md").read_text(encoding="utf-8")
        architecture_layers = (ROOT_DIR / "docs" / "architecture" / "architecture-layers.md").read_text(encoding="utf-8")
        skill = (ROOT_DIR / "packages" / "forge-core" / "SKILL.md").read_text(encoding="utf-8")

        for token in (
            "split-skill",
            "skill-first",
            "Host-discoverable Forge sibling skills",
            "line-budget reductions",
        ):
            with self.subTest(token=token):
                self.assertIn(token, target_state)

        for token, text in (
            ("packages/forge-skills/", architecture_layers),
            ("Sibling Skill Pack", architecture_layers),
        ):
            with self.subTest(reference_token=token):
                self.assertIn(token, text)

        for token in ("Forge sibling skills", "1% chance", "Proof before claims"):
            with self.subTest(skill_token=token):
                self.assertIn(token, skill)

    def test_current_split_skill_operating_contract_tokens_are_visible(self) -> None:
        target_state = (ROOT_DIR / "docs" / "current" / "target-state.md").read_text(encoding="utf-8")
        operator_surface = (ROOT_DIR / "docs" / "current" / "operator-surface.md").read_text(encoding="utf-8")

        for token in (
            "## Current Contract Closure",
            "bootstrap-driven sibling skill activation",
            "process skills before implementation skills",
            "Escalate into an explicit roadmap or product decision only if",
        ):
            with self.subTest(target_token=token):
                self.assertIn(token, target_state)

        for token in (
            "Forge sibling skills",
            "Source Repo",
            "forge-bump-release",
            "forge-deploy",
        ):
            with self.subTest(reference_token=token):
                self.assertIn(token, operator_surface)

    def test_surface_slim_split_skill_tokens_are_visible(self) -> None:
        target_state = (ROOT_DIR / "docs" / "current" / "target-state.md").read_text(encoding="utf-8")
        install_activation = (ROOT_DIR / "docs" / "current" / "install-and-activation.md").read_text(encoding="utf-8")

        for token in (
            "docs/current/",
            "packages/forge-skills/*/SKILL.md",
            "generated host artifacts bootstrap-only",
            "There is no active roadmap tranche now.",
        ):
            with self.subTest(target_token=token):
                self.assertIn(token, target_state)

        for token in (
            "docs/current/",
            "packages/forge-skills/",
            "Generated host artifacts remain bootstrap-only",
        ):
            with self.subTest(reference_token=token):
                self.assertIn(token, install_activation)

    def test_readme_start_here_onboarding_tokens_remain_visible(self) -> None:
        readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("Evidence-first execution kernel", readme)
        self.assertIn("Current stable release", readme)
        self.assertIn("Start Here (Solo Operator)", readme)
        self.assertIn("verify_repo.py --profile fast", readme)
        self.assertIn("bounded slice", readme)

    def test_bump_release_contract_is_owned_by_sibling_skill(self) -> None:
        bump_skill = ROOT_DIR / "packages" / "forge-skills" / "bump-release" / "SKILL.md"
        bump_reference = ROOT_DIR / "packages" / "forge-skills" / "bump-release" / "references" / "bump-release.md"
        bump_script = ROOT_DIR / "packages" / "forge-skills" / "bump-release" / "references" / "scripts" / "prepare_bump.py"
        core_skill = ROOT_DIR / "packages" / "forge-core" / "SKILL.md"
        antigravity_skill = ROOT_DIR / "packages" / "forge-antigravity" / "overlay" / "SKILL.md"
        codex_skill = ROOT_DIR / "packages" / "forge-codex" / "overlay" / "SKILL.md"

        self.assertTrue(bump_skill.exists())
        self.assertTrue(bump_reference.exists())
        self.assertTrue(bump_script.exists())
        self.assertIn(
            "Current version is stated and target version is either explicit or justified by inference",
            bump_skill.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "python references/scripts/prepare_bump.py --workspace <workspace>",
            bump_reference.read_text(encoding="utf-8"),
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
        self.assertFalse((ROOT_DIR / "packages" / "forge-core" / "workflows" / "operator" / "bump.md").exists())
        self.assertFalse((ROOT_DIR / "packages" / "forge-antigravity" / "overlay" / "workflows" / "operator" / "bump.md").exists())
        self.assertFalse((ROOT_DIR / "packages" / "forge-codex" / "overlay" / "workflows" / "operator" / "bump.md").exists())

    def test_deploy_contract_is_owned_by_sibling_skill(self) -> None:
        deploy_skill = ROOT_DIR / "packages" / "forge-skills" / "deploy" / "SKILL.md"
        deploy_contract = ROOT_DIR / "packages" / "forge-skills" / "deploy" / "references" / "deploy-contract.md"
        deploy_checks = ROOT_DIR / "packages" / "forge-skills" / "deploy" / "references" / "deploy-checks.md"
        rollback_guidance = ROOT_DIR / "packages" / "forge-skills" / "deploy" / "references" / "rollback-guidance.md"
        core_skill = ROOT_DIR / "packages" / "forge-core" / "SKILL.md"

        self.assertTrue(deploy_skill.exists())
        self.assertTrue(deploy_contract.exists())
        self.assertTrue(deploy_checks.exists())
        self.assertTrue(rollback_guidance.exists())
        self.assertIn(
            "pre-deploy readiness",
            deploy_skill.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "explicit confirmation",
            deploy_contract.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "rollback path",
            rollback_guidance.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Proof before claims is non-negotiable",
            core_skill.read_text(encoding="utf-8"),
        )
        self.assertFalse((ROOT_DIR / "packages" / "forge-core" / "workflows" / "operator" / "deploy.md").exists())
        self.assertFalse((ROOT_DIR / "packages" / "forge-antigravity" / "overlay" / "workflows" / "operator" / "deploy.md").exists())
        self.assertFalse((ROOT_DIR / "packages" / "forge-codex" / "overlay" / "workflows" / "operator" / "deploy.md").exists())

    def test_sibling_skill_build_manifests_declare_self_contained_reference_files(self) -> None:
        build_release.build_all()

        for skill_name, relative_paths in EXPECTED_SIBLING_SKILL_REFERENCES.items():
            manifest_path = ROOT_DIR / "dist" / skill_name / "BUILD-MANIFEST.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            required = set(manifest["packaging"]["required_bundle_paths"])
            with self.subTest(skill=skill_name):
                self.assertEqual(manifest["packaging"]["default_target_strategy"], "sibling-skill")
                for relative_path in relative_paths:
                    self.assertIn(relative_path, required)

    def test_dist_sibling_skill_bundles_keep_their_local_reference_files(self) -> None:
        build_release.build_all()

        for skill_name, relative_paths in EXPECTED_SIBLING_SKILL_REFERENCES.items():
            bundle_root = ROOT_DIR / "dist" / skill_name
            for relative_path in relative_paths:
                with self.subTest(skill=skill_name, path=relative_path):
                    self.assertTrue((bundle_root / relative_path).exists())
