from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import playwright_cli  # noqa: E402


class PlaywrightCliTests(unittest.TestCase):
    @patch("playwright_cli.shutil.which")
    def test_resolve_playwright_command_prefers_npx_cmd_on_windows(self, mock_which) -> None:
        mock_which.side_effect = lambda name: {
            "npx.cmd": r"C:\Program Files\nodejs\npx.cmd",
            "npx": r"C:\Program Files\nodejs\npx",
        }.get(name)

        command = playwright_cli.resolve_playwright_command()

        self.assertEqual(command, [r"C:\Program Files\nodejs\npx.cmd", "playwright"])

    @patch("playwright_cli.subprocess.run")
    def test_doctor_reports_versions(self, mock_run) -> None:
        mock_run.side_effect = [
            subprocess.CompletedProcess(["node", "-v"], 0, stdout="v24.13.0\n", stderr=""),
            subprocess.CompletedProcess(["npx", "playwright", "--version"], 0, stdout="Version 1.58.2\n", stderr=""),
        ]

        payload = playwright_cli.doctor(timeout_ms=5000)

        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["checks"]["node"]["stdout"], "v24.13.0")
        self.assertEqual(payload["checks"]["playwright_cli"]["stdout"], "Version 1.58.2")

    @patch("playwright_cli.subprocess.run")
    def test_screenshot_uses_session_storage_paths(self, mock_run) -> None:
        mock_run.return_value = subprocess.CompletedProcess(["npx"], 0, stdout="", stderr="")
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            session = {
                "user_data_dir": str((temp_root / "user-data").resolve()),
                "storage_state_path": str((temp_root / "storage-state.json").resolve()),
            }
            Path(session["user_data_dir"]).mkdir(parents=True, exist_ok=True)
            Path(session["storage_state_path"]).write_text("{}", encoding="utf-8")

            output = temp_root / "artifact.png"
            har = temp_root / "artifact.har"
            payload = playwright_cli.screenshot(
                session=session,
                url="https://example.com",
                output_path=output,
                browser="chromium",
                lang="vi-VN",
                device=None,
                full_page=True,
                wait_for_selector="#app",
                wait_for_timeout=250,
                save_har_path=har,
                timeout_ms=9000,
            )

            command = mock_run.call_args.kwargs["args"] if "args" in mock_run.call_args.kwargs else mock_run.call_args.args[0]
            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(command[1], "playwright")
            self.assertIn("--load-storage", command)
            self.assertIn("--save-storage", command)
            self.assertNotIn("--user-data-dir", command)
            self.assertIn("--full-page", command)
            self.assertIn("--save-har", command)
            self.assertEqual(payload["output_path"], str(output))

    @patch("playwright_cli.subprocess.run")
    def test_open_browser_keeps_user_data_dir_for_interactive_session(self, mock_run) -> None:
        mock_run.return_value = subprocess.CompletedProcess(["npx"], 0, stdout="", stderr="")
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            session = {
                "user_data_dir": str((temp_root / "user-data").resolve()),
                "storage_state_path": str((temp_root / "storage-state.json").resolve()),
            }
            Path(session["user_data_dir"]).mkdir(parents=True, exist_ok=True)
            Path(session["storage_state_path"]).write_text("{}", encoding="utf-8")

            payload = playwright_cli.open_browser(
                session=session,
                url="https://example.com",
                browser="chromium",
                lang=None,
                device=None,
                timeout_ms=9000,
            )

            command = mock_run.call_args.kwargs["args"] if "args" in mock_run.call_args.kwargs else mock_run.call_args.args[0]
            self.assertEqual(payload["status"], "PASS")
            self.assertIn("--user-data-dir", command)
            self.assertIn("--load-storage", command)
            self.assertIn("--save-storage", command)


if __name__ == "__main__":
    unittest.main()
