from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from release_repo_test_support import ReleaseRepoTestSupport, build_release, install_bundle


class ReleaseRepoInstallTests(ReleaseRepoTestSupport):
    def test_install_bundle_dry_run_keeps_target_untouched(self) -> None:
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
            self.assertEqual(report["source_build_manifest"]["state"]["dev_root"]["env_var"], "GEMINI_HOME")
            self.assertEqual(report["source_build_manifest"]["state"]["dev_root"]["path_relative"], "forge-antigravity")
            self.assertEqual(
                report["source_build_manifest"]["generated_artifacts"]["artifacts"][0]["name"],
                "forge-antigravity-global-gemini",
            )
            self.assertEqual(
                manifest["source_build_manifest"]["generated_artifacts"]["artifacts"][0]["bundle_output"],
                "GEMINI.global.md",
            )
            self.assertEqual(
                len(manifest["source_build_manifest"]["generated_artifacts"]["artifacts"][0]["output_sha256"]),
                64,
            )
            self.assertTrue(manifest["bundle_fingerprint"]["matches_source"])
            self.assertFalse(manifest["bundle_fingerprint"]["host_mutation_expected"])
            self.assertEqual(
                manifest["bundle_fingerprint"]["source"]["sha256"],
                report["source_build_manifest"]["bundle_fingerprint"]["sha256"],
            )
            self.assertEqual(
                manifest["bundle_fingerprint"]["installed"]["sha256"],
                report["source_build_manifest"]["bundle_fingerprint"]["sha256"],
            )
            self.assertTrue((temp_root / "runtime" / "forge-antigravity-state").is_dir())
            self.assertTrue((temp_root / "runtime" / "forge-antigravity-state" / "state").is_dir())

    def test_install_bundle_succeeds_when_target_root_is_locked_as_cwd(self) -> None:
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

    def test_install_runtime_tool_writes_runtime_state_layout(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target = temp_root / "runtime" / "forge-browse"

            report = install_bundle.install_bundle(
                "forge-browse",
                target=str(target),
                backup_dir=str(temp_root / "backups"),
            )

            manifest = json.loads((target / "INSTALL-MANIFEST.json").read_text(encoding="utf-8"))
            expected_root = str((temp_root / "runtime" / "forge-browse-state").resolve())
            self.assertEqual(manifest["bundle"], "forge-browse")
            self.assertEqual(manifest["state"]["scope"], "runtime-tool-global")
            self.assertEqual(manifest["state"]["root"], expected_root)
            self.assertEqual(manifest["state"]["sessions_path"], str((Path(expected_root) / "state" / "sessions.json").resolve()))
            self.assertEqual(manifest["state"]["events_path"], str((Path(expected_root) / "state" / "events.jsonl").resolve()))
            self.assertEqual(manifest["state"]["artifacts_dir"], str((Path(expected_root) / "artifacts").resolve()))
            self.assertTrue(Path(manifest["state"]["artifacts_dir"]).is_dir())
            self.assertEqual(report["source_build_manifest"]["host"], "runtime")

            result = subprocess.run(
                [
                    sys.executable,
                    str(target / "scripts" / "forge_browse.py"),
                    "session-create",
                    "--label",
                    "installed",
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

            self.assertEqual(payload["state"]["root"], expected_root)
            self.assertTrue(Path(payload["state"]["sessions_path"]).exists())

    def test_install_companion_bundle_writes_manifest_without_state_root(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target = temp_root / "companions" / "forge-nextjs-typescript-postgres"

            report = install_bundle.install_bundle(
                "forge-nextjs-typescript-postgres",
                target=str(target),
                backup_dir=str(temp_root / "backups"),
            )

            manifest = json.loads((target / "INSTALL-MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["bundle"], "forge-nextjs-typescript-postgres")
            self.assertEqual(manifest["host"], "companion")
            self.assertEqual(manifest["mode"], "install")
            self.assertIn("compatibility", manifest)
            self.assertEqual(manifest["compatibility"]["status"], "PASS")
            self.assertTrue(manifest["compatibility"]["compatible"])
            self.assertIn("is compatible", manifest["compatibility"]["message"])
            self.assertIn("transition", manifest)
            self.assertEqual(manifest["transition"]["status"], "new-install")
            self.assertTrue((target / "companion.json").exists())
            self.assertEqual(report["state"]["root"], str((temp_root / "companions" / "forge-nextjs-typescript-postgres-state").resolve()))

    def test_installed_codex_bundle_can_discover_registered_companion(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            codex_home = temp_root / "codex-home"
            codex_target = codex_home / "skills" / "forge-codex"
            companion_target = temp_root / "companions" / "forge-nextjs-typescript-postgres"
            workspace = temp_root / "workspace"
            workspace.mkdir(parents=True, exist_ok=True)
            (workspace / "package.json").write_text(
                json.dumps(
                    {
                        "name": "demo-app",
                        "dependencies": {
                            "next": "15.0.0",
                            "@prisma/client": "6.0.0",
                        },
                        "devDependencies": {"typescript": "5.0.0", "prisma": "6.0.0"},
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            (workspace / "tsconfig.json").write_text("{}", encoding="utf-8")
            (workspace / "next.config.ts").write_text("export default {};\n", encoding="utf-8")
            (workspace / "app").mkdir()
            (workspace / "app" / "layout.tsx").write_text("export default function Layout() { return null; }\n", encoding="utf-8")
            (workspace / "prisma").mkdir()
            (workspace / "prisma" / "schema.prisma").write_text("generator client { provider = \"prisma-client-js\" }\n", encoding="utf-8")

            install_bundle.install_bundle(
                "forge-codex",
                target=str(codex_target),
                codex_home=str(codex_home),
                backup_dir=str(temp_root / "backups"),
            )
            companion_report = install_bundle.install_bundle(
                "forge-nextjs-typescript-postgres",
                target=str(companion_target),
                codex_home=str(codex_home),
                register_codex_companion=True,
                backup_dir=str(temp_root / "backups"),
            )

            registry_path = codex_home / "forge-codex" / "state" / "companions.json"
            self.assertTrue(registry_path.exists())
            self.assertEqual(
                companion_report["codex_companion_registration"]["registry_path"],
                str(registry_path.resolve()),
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(codex_target / "scripts" / "doctor.py"),
                    "--workspace",
                    str(workspace),
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

            self.assertEqual(report["companions"][0]["id"], "nextjs-typescript-postgres")
            self.assertTrue(report["companions"][0]["registered"])
            self.assertEqual(report["companions"][0]["registered_target"], str(companion_target.resolve()))
            self.assertEqual(report["companions"][0]["local_root"], str(companion_target.resolve()))
