from __future__ import annotations

import json
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


class RuntimeToolRegistrationTests(unittest.TestCase):
    def _run_script(self, script_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script_path), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

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


if __name__ == "__main__":
    unittest.main()
