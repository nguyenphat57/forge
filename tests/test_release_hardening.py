from __future__ import annotations

import json
import os
import re
import shutil
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


class ReleaseHardeningTests(unittest.TestCase):
    def _run_build_release(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "build_release.py"), "--format", "json"],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_public_repo_docs_exist(self) -> None:
        required_paths = [
            ROOT_DIR / "LICENSE",
            ROOT_DIR / "CONTRIBUTING.md",
            ROOT_DIR / "SECURITY.md",
            ROOT_DIR / "CODE_OF_CONDUCT.md",
            ROOT_DIR / "docs" / "release" / "public-readiness.md",
            ROOT_DIR / "docs" / "release" / "github-public-switch-checklist.md",
        ]
        for path in required_paths:
            with self.subTest(path=path):
                self.assertTrue(path.exists(), f"Missing public repo doc: {path}")

    def test_public_docs_do_not_embed_repo_absolute_path(self) -> None:
        repo_root_text = str(ROOT_DIR)
        docs_to_check = [ROOT_DIR / "README.md"]
        docs_to_check.extend(sorted((ROOT_DIR / "docs").rglob("*.md")))
        docs_to_check.extend(sorted((ROOT_DIR / "packages").glob("*/README.md")))
        for path in docs_to_check:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn(repo_root_text, text)

    def test_release_facing_docs_do_not_require_host_soak(self) -> None:
        banned_phrases = [
            "soak time on a real Codex host",
            "host-specific smoke or canary checks before broad promotion",
        ]
        docs_to_check = [
            ROOT_DIR / "README.md",
            ROOT_DIR / "docs" / "release" / "public-readiness.md",
            ROOT_DIR / "docs" / "release" / "release-process.md",
        ]
        for path in docs_to_check:
            text = path.read_text(encoding="utf-8")
            for phrase in banned_phrases:
                with self.subTest(path=path, phrase=phrase):
                    self.assertNotIn(phrase, text)

    def test_release_facing_docs_match_current_stable_version(self) -> None:
        version = (ROOT_DIR / "VERSION").read_text(encoding="utf-8").strip()
        readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
        public_readiness = (ROOT_DIR / "docs" / "release" / "public-readiness.md").read_text(encoding="utf-8")
        release_process = (ROOT_DIR / "docs" / "release" / "release-process.md").read_text(encoding="utf-8")
        changelog = (ROOT_DIR / "CHANGELOG.md").read_text(encoding="utf-8")

        self.assertIn(f"Current stable release: `{version}`", readme)
        self.assertRegex(
            public_readiness,
            rf"Status:\s*`{re.escape(version)}` is the current stable release",
        )
        self.assertIn(f"release-facing docs now align on `{version}`", public_readiness)
        self.assertRegex(
            release_process,
            rf"Forge `{re.escape(version)}` is the current stable release",
        )

        first_release_heading = next(
            line for line in changelog.splitlines() if line.startswith("## ")
        )
        self.assertRegex(first_release_heading, r"^## \d+\.\d+\.\d+ \(stable\) - .+$")
        self.assertTrue(
            first_release_heading.startswith(f"## {version} (stable) - "),
            f"Top changelog release does not match VERSION: {first_release_heading}",
        )

    def test_plan_inventory_reflects_current_roadmap_and_archive_boundary(self) -> None:
        closure_path = ROOT_DIR / "docs" / "plans" / "2026-04-02-forge-1.15.x-maintenance-closure.md"
        roadmap_path = ROOT_DIR / "docs" / "plans" / "forge_refactor_V3.md"
        archive_index = ROOT_DIR / "docs" / "archive" / "INDEX.md"
        closure_text = closure_path.read_text(encoding="utf-8")
        roadmap_text = roadmap_path.read_text(encoding="utf-8")
        archive_text = archive_index.read_text(encoding="utf-8")

        self.assertIn("Status: historical maintenance closure", closure_text)
        self.assertIn("Status: current roadmap", roadmap_text)
        self.assertIn("Historical roadmap and spec material moved here", archive_text)
        self.assertIn("All roadmap files under `docs/plans/` should now be one of:", closure_text)
        self.assertIn("current roadmap", closure_text)
        self.assertTrue((ROOT_DIR / "docs" / "current" / "architecture.md").exists())
        self.assertTrue((ROOT_DIR / "docs" / "current" / "operator-surface.md").exists())
        self.assertTrue((ROOT_DIR / "docs" / "current" / "install-and-activation.md").exists())

        allowed_status_patterns = (
            re.compile(r"^\*\*Status:\*\* historical"),
            re.compile(r"^Status: historical"),
            re.compile(r"^Status: implemented"),
            re.compile(r"^Status: historical maintenance closure"),
            re.compile(r"^Status: current roadmap$"),
        )

        for path in sorted((ROOT_DIR / "docs" / "plans").glob("*.md")):
            text = path.read_text(encoding="utf-8")
            status_line = next(
                (line.strip() for line in text.splitlines() if line.startswith("Status:") or line.startswith("**Status:**")),
                None,
            )
            self.assertIsNotNone(status_line, f"Missing status line in plan doc: {path}")
            with self.subTest(path=path, status=status_line):
                self.assertTrue(
                    any(pattern.match(status_line) for pattern in allowed_status_patterns),
                    f"Plan doc status is not maintenance-safe: {path} -> {status_line}",
                )

    def test_brain_decisions_keep_only_one_current_stable_line(self) -> None:
        decisions = json.loads((ROOT_DIR / ".brain" / "decisions.json").read_text(encoding="utf-8"))
        version = (ROOT_DIR / "VERSION").read_text(encoding="utf-8").strip()
        major, minor, *_ = version.split(".")
        expected_scope = f"forge-{major}-{minor}-stable-status"
        stable_decisions = [item for item in decisions if item.get("scope", "").endswith("-stable-status")]

        current_line_decisions = [
            item for item in stable_decisions if "current stable Forge release" in item.get("summary", "")
        ]
        self.assertEqual(len(current_line_decisions), 1)
        self.assertEqual(current_line_decisions[0]["scope"], expected_scope)
        self.assertEqual(current_line_decisions[0]["status"], "resolved")

        for item in stable_decisions:
            if item["scope"] != expected_scope:
                with self.subTest(scope=item["scope"]):
                    self.assertEqual(item["status"], "superseded")
                    self.assertNotIn("current stable Forge release", item["summary"])

        closure = next(
            item for item in decisions if item.get("scope") == "forge-1-15-maintenance-closure"
        )
        self.assertEqual(closure["status"], "resolved")
        self.assertIn("docs/plans/2026-04-02-forge-1.15.x-maintenance-closure.md", closure["evidence"])
        self.assertIn("packages/forge-core/references/target-state.md", closure["evidence"])

    def test_changelog_is_english_first_public_text(self) -> None:
        changelog = (ROOT_DIR / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertTrue(changelog.isascii(), "CHANGELOG.md should stay ASCII and English-first for public release surfaces.")

    def test_security_policy_includes_direct_contact_path(self) -> None:
        security = (ROOT_DIR / "SECURITY.md").read_text(encoding="utf-8")
        self.assertIn("@nguyenphat57", security)
        self.assertIn("https://github.com/nguyenphat57", security)

    def test_verify_workflow_uses_cross_platform_matrix(self) -> None:
        workflow = (ROOT_DIR / ".github" / "workflows" / "verify.yml").read_text(encoding="utf-8")
        self.assertIn("strategy:", workflow)
        self.assertIn("matrix:", workflow)
        self.assertIn("windows-latest", workflow)
        self.assertIn("ubuntu-latest", workflow)
        self.assertIn("macos-latest", workflow)
        self.assertIn("python-version: ${{ matrix.python-version }}", workflow)

    def test_build_release_excludes_cached_python_artifacts(self) -> None:
        self._run_build_release()
        for bundle_name in ("forge-antigravity", "forge-codex", "forge-core"):
            with self.subTest(bundle=bundle_name):
                dist_root = ROOT_DIR / "dist" / bundle_name
                self.assertFalse(any(dist_root.rglob("__pycache__")))
                self.assertFalse(any(dist_root.rglob("*.pyc")))

    def test_install_bundle_rejects_repo_local_targets(self) -> None:
        self._run_build_release()
        targets = [
            ROOT_DIR / ".tmp" / "repo-target",
            ROOT_DIR / "dist" / "repo-target",
            ROOT_DIR / "packages" / "repo-target",
        ]
        for target in targets:
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    install_bundle.install_bundle(
                        "forge-codex",
                        target=str(target),
                        dry_run=True,
                    )

    def test_repeated_build_release_remains_stable_after_dist_execution(self) -> None:
        self._run_build_release()
        for bundle_name in ("forge-antigravity", "forge-codex", "forge-core"):
            with self.subTest(bundle=bundle_name):
                with TemporaryDirectory() as temp_dir:
                    temp_root = Path(temp_dir)
                    source_bundle = ROOT_DIR / "dist" / bundle_name
                    verify_root = temp_root / bundle_name
                    shutil.copytree(source_bundle, verify_root)

                    verify_script = verify_root / "scripts" / "verify_bundle.py"
                    poisoned_env = os.environ.copy()
                    poisoned_env["FORGE_HOME"] = str(verify_root)
                    poisoned_env["FORGE_BUNDLE_ROOT"] = str(ROOT_DIR)
                    result = subprocess.run(
                        [sys.executable, str(verify_script), "--format", "json"],
                        cwd=str(ROOT_DIR),
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        check=False,
                        env=poisoned_env,
                    )
                    self.assertEqual(
                        result.returncode,
                        0,
                        f"{bundle_name} verify failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
                    )
                    payload = json.loads(result.stdout)
                    self.assertEqual(payload["status"], "PASS")

        self._run_build_release()
        self.assertTrue((ROOT_DIR / "dist" / "forge-antigravity" / "BUILD-MANIFEST.json").exists())
        self.assertTrue((ROOT_DIR / "dist" / "forge-codex" / "BUILD-MANIFEST.json").exists())
        self.assertTrue((ROOT_DIR / "dist" / "forge-core" / "BUILD-MANIFEST.json").exists())
        self.assertFalse((ROOT_DIR / "dist" / "forge-browse" / "BUILD-MANIFEST.json").exists())
        self.assertFalse((ROOT_DIR / "dist" / "forge-design" / "BUILD-MANIFEST.json").exists())

    def test_verify_repo_pipeline_includes_secret_scan(self) -> None:
        verify_repo = (ROOT_DIR / "scripts" / "verify_repo.py").read_text(encoding="utf-8")
        self.assertIn("repo.secret_scan", verify_repo)
        self.assertIn("repo.generated_host_artifacts", verify_repo)
        self.assertIn("repo.generated_overlay_skills", verify_repo)
        self.assertIn("install_dry_run.forge-core", verify_repo)
        self.assertNotIn("install_dry_run.forge-browse", verify_repo)
        self.assertNotIn("install_dry_run.forge-design", verify_repo)
        self.assertTrue((ROOT_DIR / "scripts" / "scan_repo_secrets.py").exists())
        self.assertTrue((ROOT_DIR / "scripts" / "generate_host_artifacts.py").exists())
        self.assertTrue((ROOT_DIR / "scripts" / "generate_overlay_skills.py").exists())

    def test_build_release_requires_fresh_generated_host_artifacts(self) -> None:
        build_script = (ROOT_DIR / "scripts" / "build_release.py").read_text(encoding="utf-8")
        self.assertIn("ensure_generated_host_artifacts(check=True)", build_script)
        self.assertIn("ensure_generated_overlay_skills(check=True)", build_script)

    def test_install_bundle_rejects_custom_source_with_drifted_fingerprint(self) -> None:
        self._run_build_release()
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            source = temp_root / "forge-codex"
            shutil.copytree(ROOT_DIR / "dist" / "forge-codex", source)
            (source / "SKILL.md").write_text("drifted bundle\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                install_bundle.install_bundle(
                    "forge-codex",
                    source=str(source),
                    target=str(temp_root / "runtime" / "forge-codex"),
                    dry_run=True,
                )


if __name__ == "__main__":
    unittest.main()
