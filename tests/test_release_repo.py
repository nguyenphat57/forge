from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_release  # noqa: E402
import install_bundle  # noqa: E402


class ReleaseRepoTests(unittest.TestCase):
    def assert_bump_wrapper_matches_release_contract(self, path: Path, *, label: str) -> None:
        text = path.read_text(encoding="utf-8")
        self.assertIn("Current version is stated and target version is either explicit or justified by inference", text, label)
        self.assertIn("python scripts/prepare_bump.py --workspace <workspace>", text, label)
        self.assertIn("bump source: explicit or inferred", text, label)
        self.assertIn("explicit or inferred semver", text, label)

    def assert_session_restores_preferences(self, path: Path, *, label: str) -> None:
        text = path.read_text(encoding="utf-8")
        self.assertIn("adapter-global", text, label)
        self.assertIn("state/preferences.json", text, label)
        self.assertIn("state/extra_preferences.json", text, label)
        self.assertIn("resolve_preferences.py", text, label)
        self.assertIn("Response Personalization", text, label)

    def assert_codex_global_agents_bootstraps_preferences(self, path: Path, *, label: str) -> None:
        text = path.read_text(encoding="utf-8")
        self.assertIn("Thread Bootstrap", text, label)
        self.assertIn("On every new thread, restore Forge response personalization", text, label)
        self.assertIn("state/preferences.json", text, label)
        self.assertIn("state/extra_preferences.json", text, label)
        self.assertIn("resolve_preferences.py", text, label)

    def assert_antigravity_skill_bootstraps_preferences(self, path: Path, *, label: str) -> None:
        text = path.read_text(encoding="utf-8")
        self.assertIn("At the start of each new thread, resolve preferences", text, label)
        self.assertIn("state/preferences.json", text, label)
        self.assertIn("state/extra_preferences.json", text, label)
        self.assertIn("resolve_preferences.py", text, label)

    def assert_antigravity_agent_prompt_bootstraps_preferences(self, path: Path, *, label: str) -> None:
        text = path.read_text(encoding="utf-8")
        self.assertIn("restore preferences from Antigravity-global state at thread start", text, label)
        self.assertIn("default to Vietnamese with full diacritics unless resolved preferences say otherwise", text, label)

    def assert_antigravity_global_gemini_bootstraps_preferences(self, path: Path, *, label: str) -> None:
        text = path.read_text(encoding="utf-8")
        self.assertIn("Preferences resolver", text, label)
        self.assertIn("state/preferences.json", text, label)
        self.assertIn("state/extra_preferences.json", text, label)
        self.assertIn("read the two preference files directly", text, label)
        self.assertIn("resolve_preferences.py", text, label)

    def assert_routing_locale_config(self, path: Path, *, label: str) -> None:
        config = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("enabled_locales", config, label)
        self.assertIn("vi", config["enabled_locales"], label)

    def assert_output_contract_profiles(self, path: Path, *, label: str) -> None:
        payload = json.loads(path.read_text(encoding="utf-8"))
        vi = payload.get("languages", {}).get("vi", {})
        self.assertEqual(vi.get("default_orthography"), "vietnamese-diacritics", label)
        self.assertEqual(vi.get("contract", {}).get("accent_policy"), "required", label)
        self.assertEqual(
            payload.get("orthographies", {}).get("vietnamese-diacritics", {}).get("encoding"),
            "utf-8",
            label,
        )

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

    def test_install_bundle_dry_run_keeps_target_untouched(self) -> None:
        build_release.build_all()
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target = temp_root / "runtime" / "forge-codex"
            target.mkdir(parents=True, exist_ok=True)
            (target / "marker.txt").write_text("keep", encoding="utf-8")

            report = install_bundle.install_bundle(
                "forge-codex",
                target=str(target),
                backup_dir=str(temp_root / "backups"),
                dry_run=True,
            )

            self.assertTrue((target / "marker.txt").exists())
            self.assertEqual(report["bundle"], "forge-codex")
            self.assertIsNotNone(report["backup_path"])
            self.assertFalse(Path(report["backup_path"]).exists())

    def test_install_bundle_replaces_target_and_writes_manifest(self) -> None:
        build_release.build_all()
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target = temp_root / "runtime" / "forge-antigravity"
            target.mkdir(parents=True, exist_ok=True)
            (target / "old.txt").write_text("old", encoding="utf-8")

            report = install_bundle.install_bundle(
                "forge-antigravity",
                target=str(target),
                backup_dir=str(temp_root / "backups"),
            )

            self.assertTrue((target / "SKILL.md").exists())
            self.assertFalse((target / "old.txt").exists())
            self.assertIsNotNone(report["backup_path"])
            self.assertTrue(Path(report["backup_path"]).exists())

            manifest = json.loads((target / "INSTALL-MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["bundle"], "forge-antigravity")
            self.assertEqual(manifest["version"], build_release.read_version())
            self.assertEqual(manifest["state"]["scope"], "adapter-global")
            self.assertEqual(
                manifest["state"]["root"],
                str((temp_root / "runtime" / "forge-antigravity-state").resolve()),
            )
            self.assertEqual(
                manifest["state"]["preferences_path"],
                str((temp_root / "runtime" / "forge-antigravity-state" / "state" / "preferences.json").resolve()),
            )
            self.assertTrue((temp_root / "runtime" / "forge-antigravity-state").is_dir())
            self.assertTrue((temp_root / "runtime" / "forge-antigravity-state" / "state").is_dir())

    def test_install_bundle_succeeds_when_target_root_is_locked_as_cwd(self) -> None:
        build_release.build_all()
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target = temp_root / "runtime" / "forge-antigravity"
            target.mkdir(parents=True, exist_ok=True)
            (target / "old.txt").write_text("old", encoding="utf-8")

            locker = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    "import os, sys, time; os.chdir(sys.argv[1]); time.sleep(10)",
                    str(target),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            try:
                report = install_bundle.install_bundle(
                    "forge-antigravity",
                    target=str(target),
                    backup_dir=str(temp_root / "backups"),
                )
            finally:
                locker.terminate()
                locker.wait(timeout=5)

            self.assertEqual(report["bundle"], "forge-antigravity")
            self.assertTrue((target / "SKILL.md").exists())
            self.assertFalse((target / "old.txt").exists())

    def test_antigravity_wave_b_overlay_files_exist(self) -> None:
        overlay_root = ROOT_DIR / "packages" / "forge-antigravity" / "overlay"
        expected_files = [
            overlay_root / "GEMINI.global.md",
            overlay_root / "workflows" / "operator" / "customize.md",
            overlay_root / "workflows" / "operator" / "init.md",
            overlay_root / "workflows" / "operator" / "recap.md",
            overlay_root / "workflows" / "operator" / "save-brain.md",
            overlay_root / "workflows" / "operator" / "handover.md",
            overlay_root / "references" / "antigravity-operator-surface.md",
            overlay_root / "data" / "preferences-compat.json",
            overlay_root / "data" / "routing-locales.json",
            overlay_root / "data" / "routing-locales" / "vi.json",
            overlay_root / "data" / "output-contracts.json",
        ]
        for path in expected_files:
            with self.subTest(path=path):
                self.assertTrue(path.exists())

        skill = (overlay_root / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("/customize", skill)
        self.assertIn("/init", skill)
        self.assertIn("/save-brain", skill)
        self.assert_antigravity_skill_bootstraps_preferences(
            overlay_root / "SKILL.md",
            label="forge-antigravity overlay skill",
        )
        self.assert_antigravity_agent_prompt_bootstraps_preferences(
            overlay_root / "agents" / "openai.yaml",
            label="forge-antigravity overlay agent prompt",
        )
        self.assert_antigravity_global_gemini_bootstraps_preferences(
            overlay_root / "GEMINI.global.md",
            label="forge-antigravity overlay gemini",
        )

    def test_build_release_preserves_antigravity_wave_b_overlay(self) -> None:
        build_release.build_all()
        dist_root = ROOT_DIR / "dist" / "forge-antigravity"
        self.assertTrue((dist_root / "GEMINI.global.md").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "customize.md").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "init.md").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "recap.md").exists())
        self.assertTrue((dist_root / "references" / "antigravity-operator-surface.md").exists())
        self.assertTrue((dist_root / "data" / "preferences-compat.json").exists())
        self.assertTrue((dist_root / "data" / "routing-locales.json").exists())
        self.assertTrue((dist_root / "data" / "routing-locales" / "vi.json").exists())
        self.assertTrue((dist_root / "data" / "output-contracts.json").exists())
        self.assert_antigravity_skill_bootstraps_preferences(
            dist_root / "SKILL.md",
            label="dist forge-antigravity skill",
        )
        self.assert_antigravity_agent_prompt_bootstraps_preferences(
            dist_root / "agents" / "openai.yaml",
            label="dist forge-antigravity agent prompt",
        )
        self.assert_antigravity_global_gemini_bootstraps_preferences(
            dist_root / "GEMINI.global.md",
            label="dist forge-antigravity gemini",
        )
        self.assert_routing_locale_config(dist_root / "data" / "routing-locales.json", label="dist forge-antigravity")
        self.assert_output_contract_profiles(dist_root / "data" / "output-contracts.json", label="dist forge-antigravity")
        self.assert_session_restores_preferences(
            dist_root / "workflows" / "execution" / "session.md",
            label="dist forge-antigravity session",
        )

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

    def test_codex_wave_c_overlay_files_exist(self) -> None:
        overlay_root = ROOT_DIR / "packages" / "forge-codex" / "overlay"
        expected_files = [
            overlay_root / "AGENTS.global.md",
            overlay_root / "data" / "orchestrator-registry.json",
            overlay_root / "data" / "routing-locales.json",
            overlay_root / "data" / "routing-locales" / "vi.json",
            overlay_root / "data" / "output-contracts.json",
            overlay_root / "workflows" / "execution" / "dispatch-subagents.md",
            overlay_root / "workflows" / "execution" / "session.md",
            overlay_root / "workflows" / "operator" / "help.md",
            overlay_root / "workflows" / "operator" / "next.md",
            overlay_root / "workflows" / "operator" / "run.md",
            overlay_root / "workflows" / "operator" / "bump.md",
            overlay_root / "workflows" / "operator" / "rollback.md",
            overlay_root / "workflows" / "operator" / "customize.md",
            overlay_root / "workflows" / "operator" / "init.md",
            overlay_root / "references" / "codex-operator-surface.md",
        ]
        for path in expected_files:
            with self.subTest(path=path):
                self.assertTrue(path.exists())

        skill = (overlay_root / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("natural-language first", skill)
        self.assertIn("dispatch-subagents", skill)
        self.assertIn("workflows/operator/customize.md", skill)
        self.assertIn("workflows/operator/init.md", skill)
        self.assertIn("AGENTS.global.md", skill)
        self.assertIn("At the start of each new thread, resolve preferences", skill)
        self.assertNotIn("save-brain", skill)
        self.assert_codex_global_agents_bootstraps_preferences(
            overlay_root / "AGENTS.global.md",
            label="forge-codex overlay agents",
        )
        self.assertNotIn("/save-brain", (overlay_root / "workflows" / "execution" / "session.md").read_text(encoding="utf-8"))
        self.assert_session_restores_preferences(
            overlay_root / "workflows" / "execution" / "session.md",
            label="forge-codex overlay session",
        )

    def test_build_release_preserves_codex_wave_c_overlay(self) -> None:
        build_release.build_all()
        dist_root = ROOT_DIR / "dist" / "forge-codex"
        self.assertTrue((dist_root / "AGENTS.global.md").exists())
        self.assertTrue((dist_root / "data" / "orchestrator-registry.json").exists())
        self.assertTrue((dist_root / "data" / "routing-locales.json").exists())
        self.assertTrue((dist_root / "data" / "routing-locales" / "vi.json").exists())
        self.assertTrue((dist_root / "data" / "output-contracts.json").exists())
        self.assertTrue((dist_root / "workflows" / "execution" / "dispatch-subagents.md").exists())
        self.assertTrue((dist_root / "workflows" / "execution" / "session.md").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "customize.md").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "init.md").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "help.md").exists())
        self.assertTrue((dist_root / "references" / "codex-operator-surface.md").exists())
        self.assert_routing_locale_config(dist_root / "data" / "routing-locales.json", label="dist forge-codex")
        self.assert_output_contract_profiles(dist_root / "data" / "output-contracts.json", label="dist forge-codex")
        self.assert_codex_global_agents_bootstraps_preferences(
            dist_root / "AGENTS.global.md",
            label="dist forge-codex agents",
        )
        self.assert_session_restores_preferences(
            dist_root / "workflows" / "execution" / "session.md",
            label="dist forge-codex session",
        )

        registry = json.loads((dist_root / "data" / "orchestrator-registry.json").read_text(encoding="utf-8"))
        self.assertEqual(registry["intents"]["SESSION"]["shortcuts"], [])
        self.assertTrue(registry["host_capabilities"]["supports_subagents"])
        self.assertEqual(registry["host_capabilities"]["subagent_dispatch_skill"], "dispatch-subagents")
        dist_skill = (dist_root / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("At the start of each new thread, resolve preferences", dist_skill)
        self.assertNotIn("save-brain", dist_skill)
        self.assertNotIn("/save-brain", (dist_root / "workflows" / "execution" / "session.md").read_text(encoding="utf-8"))

        antigravity_dist_root = ROOT_DIR / "dist" / "forge-antigravity"
        self.assert_bump_wrapper_matches_release_contract(
            antigravity_dist_root / "workflows" / "operator" / "bump.md",
            label="dist forge-antigravity",
        )
        self.assert_bump_wrapper_matches_release_contract(
            dist_root / "workflows" / "operator" / "bump.md",
            label="dist forge-codex",
        )
        self.assertIn(
            "VERSION BUMPS MUST BE USER-REQUESTED, JUSTIFIED, AND MUST SURFACE RELEASE VERIFICATION",
            (antigravity_dist_root / "SKILL.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "VERSION BUMPS MUST BE USER-REQUESTED, JUSTIFIED, AND MUST SURFACE RELEASE VERIFICATION",
            (dist_root / "SKILL.md").read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
