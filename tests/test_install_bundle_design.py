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


LIVE_SMOKE_ENV = "FORGE_BROWSE_RUN_PLAYWRIGHT_SMOKE"


class DesignInstallTests(unittest.TestCase):
    def test_install_bundle_requires_explicit_target_for_forge_design(self) -> None:
        build_release.build_all()
        with self.assertRaises(ValueError):
            install_bundle.install_bundle("forge-design", dry_run=True)

    def test_installed_design_bundle_generates_board_from_persisted_brief(self) -> None:
        build_release.build_all()
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target = temp_root / "runtime" / "forge-design"
            install_bundle.install_bundle(
                "forge-design",
                target=str(target),
                backup_dir=str(temp_root / "backups"),
            )

            brief_dir = temp_root / "ui-briefs" / "demo" / "visualize"
            (brief_dir / "pages").mkdir(parents=True, exist_ok=True)
            (brief_dir / "MASTER.md").write_text("# Master\n\nDesign notes.\n", encoding="utf-8")
            (brief_dir / "MASTER.json").write_text(
                '{"project_name":"Demo Kiosk","mode":"visualize","stack":"react-vite","platform":"tablet"}',
                encoding="utf-8",
            )
            (brief_dir / "pages" / "checkout.md").write_text("# Checkout Override\n\nSpecific notes.\n", encoding="utf-8")
            evidence = temp_root / "evidence"
            evidence.mkdir(parents=True, exist_ok=True)
            (evidence / "mockup.png").write_bytes(b"fake-png")

            result = subprocess.run(
                [
                    sys.executable,
                    str(target / "scripts" / "forge_design.py"),
                    "board",
                    "--brief-dir",
                    str(brief_dir),
                    "--screen",
                    "checkout",
                    "--evidence-dir",
                    str(evidence),
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            payload = json.loads(result.stdout)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(payload["status"], "PASS")
            self.assertTrue(Path(payload["output_path"]).exists())
            self.assertEqual(payload["asset_count"], 1)

    def test_installed_design_packet_can_be_captured_by_installed_browse_bundle(self) -> None:
        if os.environ.get(LIVE_SMOKE_ENV, "").strip().lower() not in {"1", "true", "yes", "on"}:
            self.skipTest("Set FORGE_BROWSE_RUN_PLAYWRIGHT_SMOKE=1 to run installed design+browse smoke.")
        build_release.build_all()
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            design_target = temp_root / "runtime" / "forge-design"
            browse_target = temp_root / "runtime" / "forge-browse"
            install_bundle.install_bundle("forge-design", target=str(design_target), backup_dir=str(temp_root / "backups"))
            install_bundle.install_bundle("forge-browse", target=str(browse_target), backup_dir=str(temp_root / "backups"))

            brief_dir = temp_root / "ui-briefs" / "demo" / "visualize"
            (brief_dir / "pages").mkdir(parents=True, exist_ok=True)
            (brief_dir / "MASTER.json").write_text(
                json.dumps(
                    {
                        "project_name": "Demo Kiosk",
                        "mode": "visualize",
                        "title": "Installed Review Packet",
                        "screen": "checkout",
                        "summary": "Installed packet smoke",
                        "objective": "Verify installed forge-design and forge-browse work together.",
                        "stack": "react-vite",
                        "platform": "tablet",
                        "sections": ["screen map"],
                        "deliverables": ["review packet"],
                        "stack_focus": ["first fold"],
                        "stack_watchouts": ["avoid hover-only flows"],
                        "platform_notes": ["touch-first layout"],
                        "anti_patterns": ["flat hierarchy"],
                        "notes": ["Installed smoke only."],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (brief_dir / "pages" / "checkout.md").write_text("# Checkout Override\n\n- Primary CTA stays visible.\n", encoding="utf-8")
            packet_path = temp_root / "review-packet.html"
            capture_path = temp_root / "review-packet.png"

            render_result = subprocess.run(
                [
                    sys.executable,
                    str(design_target / "scripts" / "forge_design.py"),
                    "render-brief",
                    str(brief_dir),
                    "--screen",
                    "checkout",
                    "--output",
                    str(packet_path),
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(render_result.returncode, 0, render_result.stderr)
            render_payload = json.loads(render_result.stdout)

            create_result = subprocess.run(
                [
                    sys.executable,
                    str(browse_target / "scripts" / "forge_browse.py"),
                    "session-create",
                    "--label",
                    "installed-design-review",
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(create_result.returncode, 0, create_result.stderr)
            session_payload = json.loads(create_result.stdout)
            session_id = session_payload["session"]["id"]

            snapshot_result = subprocess.run(
                [
                    sys.executable,
                    str(browse_target / "scripts" / "forge_browse.py"),
                    "snapshot",
                    "--session",
                    session_id,
                    "--url",
                    packet_path.resolve().as_uri(),
                    "--output",
                    str(capture_path),
                    "--browser",
                    "chromium",
                    "--timeout-ms",
                    "30000",
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(snapshot_result.returncode, 0, snapshot_result.stderr)
            snapshot_payload = json.loads(snapshot_result.stdout)

            self.assertTrue(packet_path.exists())
            self.assertTrue(capture_path.exists())
            self.assertTrue((temp_root / "runtime" / "forge-design-state" / "state" / "renders.jsonl").exists())
            self.assertTrue((temp_root / "runtime" / "forge-browse-state" / "state" / "sessions.json").exists())
            self.assertEqual(render_payload["status"], "PASS")
            self.assertEqual(snapshot_payload["status"], "PASS")
            self.assertEqual(snapshot_payload["runtime"]["status"], "PASS")
            self.assertEqual(session_payload["state"]["root"], str((temp_root / "runtime" / "forge-browse-state").resolve()))


if __name__ == "__main__":
    unittest.main()
