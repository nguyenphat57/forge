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
            secret_file.write_text("OPENAI_API_KEY=sk-AAAAAAAAAAAAAAAAAAAAAA\n", encoding="utf-8")

            result = self.run_scan(root)
            self.assertEqual(result.returncode, 1, result.stdout)
            payload = json.loads(result.stdout)

            self.assertEqual(payload["status"], "FAIL")
            self.assertEqual(len(payload["findings"]), 1)
            self.assertEqual(payload["findings"][0]["type"], "openai-key")
            self.assertEqual(payload["findings"][0]["line"], 1)
            self.assertEqual(Path(payload["findings"][0]["path"]), secret_file.resolve())


if __name__ == "__main__":
    unittest.main()
