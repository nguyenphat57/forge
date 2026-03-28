from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import design_board  # noqa: E402


class DesignBoardTests(unittest.TestCase):
    def test_build_design_board_writes_html_and_copies_assets(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            brief_dir = temp_root / "ui-briefs" / "demo" / "visualize"
            (brief_dir / "pages").mkdir(parents=True, exist_ok=True)
            (brief_dir / "MASTER.md").write_text("# Master\n\nVisual direction here.\n", encoding="utf-8")
            (brief_dir / "MASTER.json").write_text(
                '{"project_name":"Demo POS","mode":"visualize","stack":"react-vite","platform":"tablet"}',
                encoding="utf-8",
            )
            (brief_dir / "pages" / "checkout.md").write_text("# Checkout Override\n\nOverride details.\n", encoding="utf-8")
            evidence = temp_root / "evidence"
            evidence.mkdir(parents=True, exist_ok=True)
            (evidence / "screen.png").write_bytes(b"fake-png")

            report = design_board.build_design_board(
                brief_dir=str(brief_dir),
                screen="checkout",
                evidence_dir=str(evidence),
            )

            html_path = Path(report["output_path"])
            html_text = html_path.read_text(encoding="utf-8")
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["asset_count"], 1)
            self.assertTrue(html_path.exists())
            self.assertIn("Demo POS Design Board", html_text)
            self.assertIn("Checkout Override", html_text)
            self.assertIn("screen.png", html_text)
            self.assertTrue((html_path.parent / f"{html_path.stem}-assets").is_dir())


if __name__ == "__main__":
    unittest.main()
