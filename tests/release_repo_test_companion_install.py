from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from release_repo_test_support import ReleaseRepoTestSupport, install_bundle


class ReleaseRepoCompanionInstallTests(ReleaseRepoTestSupport):
    def test_install_companion_bundle_inspect_reports_compatibility_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target = temp_root / "companions" / "forge-nextjs-typescript-postgres"

            report = install_bundle.install_bundle(
                "forge-nextjs-typescript-postgres",
                target=str(target),
                intent="inspect",
                dry_run=True,
            )

            self.assertEqual(report["mode"], "inspect")
            self.assertTrue(report["dry_run"])
            self.assertIn("compatibility", report)
            self.assertEqual(report["compatibility"]["status"], "PASS")
            self.assertTrue(report["compatibility"]["compatible"])
            self.assertIn("is compatible", report["compatibility"]["message"])
            self.assertFalse((target / "INSTALL-MANIFEST.json").exists())

    def test_install_companion_bundle_upgrade_reports_transition(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target = temp_root / "companions" / "forge-nextjs-typescript-postgres"

            install_bundle.install_bundle(
                "forge-nextjs-typescript-postgres",
                target=str(target),
                backup_dir=str(temp_root / "backups"),
            )
            report = install_bundle.install_bundle(
                "forge-nextjs-typescript-postgres",
                target=str(target),
                backup_dir=str(temp_root / "backups"),
                intent="upgrade",
            )

            self.assertEqual(report["mode"], "upgrade")
            self.assertEqual(report["transition"]["status"], "upgrade")
            self.assertIn("Upgrade requested", report["transition"]["message"])

    def test_install_companion_bundle_reports_stale_registry_replacement(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            codex_home = temp_root / "codex-home"
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
                                "target": str((temp_root / "old-target").resolve()),
                                "version": "0.0.1",
                                "registered_at": "2026-03-28T00:00:00+00:00",
                            }
                        },
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            target = temp_root / "companions" / "forge-nextjs-typescript-postgres"
            report = install_bundle.install_bundle(
                "forge-nextjs-typescript-postgres",
                target=str(target),
                codex_home=str(codex_home),
                register_codex_companion=True,
                backup_dir=str(temp_root / "backups"),
            )

            self.assertEqual(report["codex_companion_registration"]["status"], "replaced-stale-path")
            self.assertIn("stale registry target", report["codex_companion_registration"]["message"])
