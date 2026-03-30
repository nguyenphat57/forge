from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from design_state import ensure_state_layout, resolve_state_paths  # noqa: E402


class DesignStateTests(unittest.TestCase):
    def test_ensure_state_layout_materializes_empty_renders_log(self) -> None:
        with TemporaryDirectory() as temp_dir:
            state_root = Path(temp_dir) / "forge-design-state"

            paths = ensure_state_layout(resolve_state_paths(str(state_root)))
            renders_path = state_root / "state" / "renders.jsonl"

            self.assertEqual(Path(paths["renders_path"]).resolve(), renders_path.resolve())
            self.assertTrue(renders_path.exists())
            self.assertEqual(renders_path.read_text(encoding="utf-8"), "")
            self.assertTrue((state_root / "packets").exists())


if __name__ == "__main__":
    unittest.main()
