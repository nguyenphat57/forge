from __future__ import annotations

import json
import subprocess
import sys
from unittest import mock
from pathlib import Path
from tempfile import TemporaryDirectory

from release_repo_test_support import ROOT_DIR, ReleaseRepoTestSupport, build_release, install_bundle
import install_bundle_paths  # noqa: E402


class ReleaseRepoInstallTests(ReleaseRepoTestSupport):
    def test_ensure_bundle_source_ready_rechecks_fingerprint_after_rebuild(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            dist_dir = temp_root / "dist"
            source = dist_dir / "forge-codex"
            source.mkdir(parents=True, exist_ok=True)
            canonical_source = temp_root / "canonical-dist" / "forge-codex"
            canonical_source.mkdir(parents=True, exist_ok=True)
            (canonical_source / "BUILD-MANIFEST.json").write_text(
                json.dumps(
                    {
                        "package": "forge-codex",
                        "bundle_fingerprint": {
                            "mode": "path-content-sha256-v1",
                            "sha256": "0" * 64,
                            "file_count": 99,
                        },
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            required_path = canonical_source / "required.txt"
            path_cls = type(source)
            original_resolve = path_cls.resolve

            def fake_rebuild() -> list[dict]:
                required_path.write_text("now present", encoding="utf-8")
                return []

            def fake_resolve(path: Path, *args, **kwargs) -> Path:
                if path == source:
                    return canonical_source
                if path == dist_dir / "forge-codex":
                    return canonical_source
                return original_resolve(path, *args, **kwargs)

            with mock.patch.object(install_bundle_paths, "DIST_DIR", dist_dir):
                with mock.patch.object(
                    install_bundle_paths,
                    "required_bundle_source_paths",
                    return_value=[required_path],
                ):
                    with mock.patch.object(path_cls, "resolve", autospec=True, side_effect=fake_resolve):
                        with mock.patch.object(build_release, "build_all", side_effect=fake_rebuild):
                            with self.assertRaisesRegex(ValueError, "fingerprint mismatch"):
                                install_bundle_paths.ensure_bundle_source_ready("forge-codex", source)

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

    def test_source_only_example_companion_is_not_installable_bundle(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target = temp_root / "companions" / "forge-nextjs-typescript-postgres"

            with self.assertRaises(FileNotFoundError):
                install_bundle.install_bundle(
                    "forge-nextjs-typescript-postgres",
                    target=str(target),
                    backup_dir=str(temp_root / "backups"),
                )

    def test_installed_codex_bundle_can_discover_registered_companion(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            codex_home = temp_root / "codex-home"
            codex_target = codex_home / "skills" / "forge-codex"
            companion_target = (ROOT_DIR / "packages" / "forge-nextjs-typescript-postgres").resolve()
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
            registry_path = codex_home / "forge-codex" / "state" / "companions.json"
            registry_path.parent.mkdir(parents=True, exist_ok=True)
            registry_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "companions": {
                            "forge-nextjs-typescript-postgres": {
                                "id": "nextjs-typescript-postgres",
                                "package": "forge-nextjs-typescript-postgres",
                                "target": str(companion_target),
                                "version": "0.1.0",
                                "registered_at": "2026-03-29T00:00:00+00:00",
                            }
                        },
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            self.assertTrue(registry_path.exists())

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
            self.assertEqual(report["companions"][0]["registered_target"], str(companion_target))
            self.assertEqual(report["companions"][0]["local_root"], str(companion_target))
