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


class RuntimeToolRegistrationTests(unittest.TestCase):
    def _run_script(self, script_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script_path), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def _write_visual_brief(self, root: Path) -> Path:
        brief_dir = root / "ui-briefs" / "demo" / "visualize"
        (brief_dir / "pages").mkdir(parents=True, exist_ok=True)
        (brief_dir / "MASTER.json").write_text(
            json.dumps(
                {
                    "project_name": "Runtime Tool Host Smoke",
                    "mode": "visualize",
                    "title": "Wrapper Review Packet",
                    "screen": "checkout",
                    "summary": "Exercise host runtime-tool wrappers end to end.",
                    "objective": "Ensure host wrappers can render and capture review artifacts.",
                    "stack": "react-vite",
                    "platform": "tablet",
                    "sections": ["screen map"],
                    "deliverables": ["review packet", "browse capture"],
                    "stack_focus": ["first fold"],
                    "stack_watchouts": ["avoid hover-only flows"],
                    "platform_notes": ["touch-first layout"],
                    "anti_patterns": ["flat hierarchy"],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (brief_dir / "pages" / "checkout.md").write_text("# Checkout Override\n\n- Primary CTA stays visible.\n", encoding="utf-8")
        return brief_dir

    def test_installed_host_bundles_resolve_registered_runtime_tools(self) -> None:
        build_release.build_all()
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            browse_target = temp_root / "runtime-tools" / "forge-browse"
            codex_home = temp_root / "codex-home"
            gemini_home = temp_root / "gemini-home"

            install_bundle.install_bundle(
                "forge-browse",
                target=str(browse_target),
                backup_dir=str(temp_root / "backups"),
                register_codex_runtime=True,
                codex_home=str(codex_home),
                register_gemini_runtime=True,
                gemini_home=str(gemini_home),
            )
            install_bundle.install_bundle(
                "forge-codex",
                backup_dir=str(temp_root / "backups"),
                codex_home=str(codex_home),
            )
            install_bundle.install_bundle(
                "forge-antigravity",
                backup_dir=str(temp_root / "backups"),
                gemini_home=str(gemini_home),
            )

            codex_bundle = codex_home / "skills" / "forge-codex"
            gemini_bundle = gemini_home / "antigravity" / "skills" / "forge-antigravity"
            codex_registry = codex_home / "forge-codex" / "state" / "runtime-tools.json"
            gemini_registry = gemini_home / "forge-antigravity" / "state" / "runtime-tools.json"

            self.assertTrue(codex_registry.exists())
            self.assertTrue(gemini_registry.exists())
            self.assertEqual(json.loads(codex_registry.read_text(encoding="utf-8"))["tools"]["forge-browse"]["target"], str(browse_target.resolve()))
            self.assertEqual(json.loads(gemini_registry.read_text(encoding="utf-8"))["tools"]["forge-browse"]["target"], str(browse_target.resolve()))

            codex_resolve = self._run_script(codex_bundle / "scripts" / "resolve_runtime_tool.py", "forge-browse", "--format", "json")
            gemini_resolve = self._run_script(gemini_bundle / "scripts" / "resolve_runtime_tool.py", "forge-browse", "--format", "json")
            self.assertEqual(codex_resolve.returncode, 0, codex_resolve.stderr)
            self.assertEqual(gemini_resolve.returncode, 0, gemini_resolve.stderr)
            self.assertEqual(json.loads(codex_resolve.stdout)["target"], str(browse_target.resolve()))
            self.assertEqual(json.loads(gemini_resolve.stdout)["target"], str(browse_target.resolve()))

            codex_invoke = self._run_script(
                codex_bundle / "scripts" / "invoke_runtime_tool.py",
                "forge-browse",
                "session-create",
                "--label",
                "codex-smoke",
                "--format",
                "json",
            )
            gemini_invoke = self._run_script(
                gemini_bundle / "scripts" / "invoke_runtime_tool.py",
                "forge-browse",
                "session-create",
                "--label",
                "gemini-smoke",
                "--format",
                "json",
            )
            self.assertEqual(codex_invoke.returncode, 0, codex_invoke.stderr)
            self.assertEqual(gemini_invoke.returncode, 0, gemini_invoke.stderr)
            self.assertTrue(json.loads(codex_invoke.stdout)["state"]["root"].endswith("forge-browse-state"))
            self.assertTrue(json.loads(gemini_invoke.stdout)["state"]["root"].endswith("forge-browse-state"))

    def test_installed_host_wrappers_can_render_and_capture_with_registered_runtime_tools(self) -> None:
        if os.environ.get(LIVE_SMOKE_ENV, "").strip().lower() not in {"1", "true", "yes", "on"}:
            self.skipTest("Set FORGE_BROWSE_RUN_PLAYWRIGHT_SMOKE=1 to run host wrapper design+browse smoke.")
        build_release.build_all()
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            browse_target = temp_root / "runtime-tools" / "forge-browse"
            design_target = temp_root / "runtime-tools" / "forge-design"
            codex_home = temp_root / "codex-home"
            gemini_home = temp_root / "gemini-home"

            install_bundle.install_bundle(
                "forge-browse",
                target=str(browse_target),
                backup_dir=str(temp_root / "backups"),
                register_codex_runtime=True,
                codex_home=str(codex_home),
                register_gemini_runtime=True,
                gemini_home=str(gemini_home),
            )
            install_bundle.install_bundle(
                "forge-design",
                target=str(design_target),
                backup_dir=str(temp_root / "backups"),
                register_codex_runtime=True,
                codex_home=str(codex_home),
                register_gemini_runtime=True,
                gemini_home=str(gemini_home),
            )
            install_bundle.install_bundle("forge-codex", backup_dir=str(temp_root / "backups"), codex_home=str(codex_home))
            install_bundle.install_bundle("forge-antigravity", backup_dir=str(temp_root / "backups"), gemini_home=str(gemini_home))

            host_cases = (
                ("codex", codex_home / "skills" / "forge-codex"),
                ("gemini", gemini_home / "antigravity" / "skills" / "forge-antigravity"),
            )
            for host_name, host_bundle in host_cases:
                with self.subTest(host=host_name):
                    host_root = temp_root / host_name
                    brief_dir = self._write_visual_brief(host_root)
                    packet_path = host_root / "review-packet.html"
                    capture_path = host_root / "review-packet.png"

                    render_result = self._run_script(
                        host_bundle / "scripts" / "invoke_runtime_tool.py",
                        "forge-design",
                        "render-brief",
                        str(brief_dir),
                        "--screen",
                        "checkout",
                        "--output",
                        str(packet_path),
                        "--format",
                        "json",
                    )
                    self.assertEqual(render_result.returncode, 0, render_result.stderr)
                    render_payload = json.loads(render_result.stdout)

                    create_result = self._run_script(
                        host_bundle / "scripts" / "invoke_runtime_tool.py",
                        "forge-browse",
                        "session-create",
                        "--label",
                        f"{host_name}-wrapper-smoke",
                        "--browser",
                        "chromium",
                        "--format",
                        "json",
                    )
                    self.assertEqual(create_result.returncode, 0, create_result.stderr)
                    session_payload = json.loads(create_result.stdout)
                    session_id = session_payload["session"]["id"]

                    snapshot_result = self._run_script(
                        host_bundle / "scripts" / "invoke_runtime_tool.py",
                        "forge-browse",
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
                    )
                    self.assertEqual(snapshot_result.returncode, 0, snapshot_result.stderr)
                    snapshot_payload = json.loads(snapshot_result.stdout)

                    self.assertEqual(render_payload["status"], "PASS")
                    self.assertEqual(snapshot_payload["status"], "PASS")
                    self.assertEqual(snapshot_payload["runtime"]["status"], "PASS")
                    self.assertTrue(packet_path.exists())
                    self.assertTrue(capture_path.exists())


if __name__ == "__main__":
    unittest.main()
