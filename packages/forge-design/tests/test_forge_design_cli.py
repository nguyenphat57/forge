from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT_DIR = Path(__file__).resolve().parents[1]


class ForgeDesignCliTests(unittest.TestCase):
    def test_board_command_emits_json_report(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            brief_dir = temp_root / "ui-briefs" / "demo" / "frontend"
            brief_dir.mkdir(parents=True, exist_ok=True)
            (brief_dir / "MASTER.md").write_text("# Master\n\nFrontend brief.\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT_DIR / "scripts" / "forge_design.py"),
                    "board",
                    "--brief-dir",
                    str(brief_dir),
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


if __name__ == "__main__":
    unittest.main()
