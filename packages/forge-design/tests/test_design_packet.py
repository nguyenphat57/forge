from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT_DIR = Path(__file__).resolve().parents[1]
CLI_PATH = ROOT_DIR / "scripts" / "forge_design.py"


def _write_brief(root: Path) -> Path:
    brief_dir = root / "visualize"
    pages_dir = brief_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    (brief_dir / "MASTER.json").write_text(
        json.dumps(
            {
                "mode": "visualize",
                "title": "Visual Brief",
                "project_name": "Kitchen Console",
                "screen": "dashboard",
                "summary": "Explore a calmer dashboard direction for kitchen mode.",
                "stack": "mobile-webview",
                "platform": "tablet",
                "objective": "Clarify the interaction model before UI implementation.",
                "sections": ["screen map", "component/state matrix"],
                "deliverables": ["design review packet"],
                "stack_focus": ["touch-first hierarchy"],
                "stack_watchouts": ["do not rely on hover"],
                "platform_notes": ["thumb reach matters"],
                "anti_patterns": ["crowded first fold"],
                "notes": ["Keep alerts visible."],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (pages_dir / "dashboard.md").write_text("# Page Override: dashboard\n\n## Scope Override\nDashboard shifts KPIs lower.\n", encoding="utf-8")
    return brief_dir


class DesignPacketTests(unittest.TestCase):
    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI_PATH), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def test_render_brief_writes_packet_into_state_root_by_default(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            brief_dir = _write_brief(temp_root / "briefs")
            state_root = temp_root / "design-state"

            result = self._run("render-brief", str(brief_dir), "--screen", "dashboard", "--state-root", str(state_root), "--format", "json")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)

            packet_path = Path(payload["output_path"])
            self.assertTrue(packet_path.exists())
            self.assertTrue(str(packet_path).startswith(str((state_root / "packets").resolve())))
            self.assertIn("dashboard.md", payload["page_override"])
            self.assertTrue((state_root / "state" / "renders.jsonl").exists())
            html_text = packet_path.read_text(encoding="utf-8")
            self.assertIn("Kitchen Console", html_text)
            self.assertIn("Dashboard shifts KPIs lower.", html_text)

    def test_render_brief_accepts_master_json_and_explicit_output(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            brief_dir = _write_brief(temp_root / "briefs")
            output_path = temp_root / "packet.html"

            result = self._run("render-brief", str(brief_dir / "MASTER.json"), "--output", str(output_path), "--format", "json")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)

            self.assertEqual(payload["output_path"], str(output_path.resolve()))
            self.assertTrue(output_path.exists())
            self.assertIn("Visual Brief", output_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
