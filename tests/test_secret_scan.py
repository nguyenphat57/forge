from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT_DIR = Path(__file__).resolve().parents[1]
SCAN_SCRIPT = ROOT_DIR / "scripts" / "scan_repo_secrets.py"


class SecretScanTests(unittest.TestCase):
    def run_scan(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCAN_SCRIPT), "--root", str(root), "--format", "json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def init_git_repo(self, root: Path) -> None:
        subprocess.run(["git", "init"], cwd=root, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, capture_output=True, check=True)

    def test_scan_passes_clean_workspace(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "README.md").write_text("safe text only\n", encoding="utf-8")

            result = self.run_scan(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)

            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["findings"], [])

    def test_scan_detects_high_signal_secret_patterns(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            secret_file = root / "config.env"
            secret_value = "sk-" + ("A" * 22)
            secret_file.write_text(f"OPENAI_API_KEY={secret_value}\n", encoding="utf-8")

            result = self.run_scan(root)
            self.assertEqual(result.returncode, 1, result.stdout)
            payload = json.loads(result.stdout)

            self.assertEqual(payload["status"], "FAIL")
            self.assertEqual(len(payload["findings"]), 1)
            self.assertEqual(payload["findings"][0]["type"], "openai-key")
            self.assertEqual(payload["findings"][0]["line"], 1)
            self.assertEqual(Path(payload["findings"][0]["path"]), secret_file.resolve())

    def test_scan_detects_untracked_secrets_in_git_repos(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.init_git_repo(root)

            readme = root / "README.md"
            readme.write_text("safe text only\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=root, capture_output=True, check=True)
            subprocess.run(["git", "commit", "-m", "add readme"], cwd=root, capture_output=True, check=True)

            leak_file = root / "leak.env"
            leak_value = "sk-" + ("A" * 22)
            leak_file.write_text(f"OPENAI_API_KEY={leak_value}\n", encoding="utf-8")

            result = self.run_scan(root)
            self.assertEqual(result.returncode, 1, result.stdout)
            payload = json.loads(result.stdout)

            self.assertEqual(payload["status"], "FAIL")
            self.assertEqual(len(payload["findings"]), 1)
            finding = payload["findings"][0]
            self.assertEqual(finding["type"], "openai-key")
            self.assertEqual(finding["line"], 1)
            self.assertEqual(Path(finding["path"]), leak_file.resolve())


if __name__ == "__main__":
    unittest.main()
