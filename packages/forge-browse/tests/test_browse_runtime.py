from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import browse_support  # noqa: E402
import browse_runtime  # noqa: E402
from support import serve_directory  # noqa: E402


class BrowseRuntimeTests(unittest.TestCase):
    def test_open_url_persists_session_and_snapshot(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            site_root = temp_root / "site"
            site_root.mkdir(parents=True, exist_ok=True)
            (site_root / "index.html").write_text(
                "<html><head><title>Forge Browse</title></head><body><main>Hello Browse Runtime</main></body></html>",
                encoding="utf-8",
            )
            with serve_directory(site_root) as base_url:
                report = browse_runtime.open_url(
                    state_root=str(temp_root / "state"),
                    session_id="smoke",
                    url=f"{base_url}/index.html",
                )
                snapshot = browse_runtime.snapshot_tab(state_root=str(temp_root / "state"), session_id="smoke")

            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["active_tab_id"], "1")
            self.assertEqual(report["tab"]["title"], "Forge Browse")
            self.assertTrue(Path(report["tab"]["snapshot_path"]).exists())
            self.assertIn("Hello Browse Runtime", snapshot["tab"]["text_excerpt"])
            sessions = json.loads((temp_root / "state" / "state" / "sessions.json").read_text(encoding="utf-8"))
            self.assertEqual(sessions["sessions"][0]["id"], "smoke")
            self.assertEqual(sessions["sessions"][0]["active_tab_id"], "1")
            self.assertEqual(sessions["sessions"][0]["driver"], "html-fetch")

    def test_assert_text_contains_reports_failures(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            site_root = temp_root / "site"
            site_root.mkdir(parents=True, exist_ok=True)
            (site_root / "index.html").write_text(
                "<html><body><article>Stable browse evidence</article></body></html>",
                encoding="utf-8",
            )
            with serve_directory(site_root) as base_url:
                browse_runtime.open_url(
                    state_root=str(temp_root / "state"),
                    session_id="assertions",
                    url=f"{base_url}/index.html",
                )
            passing = browse_runtime.assert_text_contains(
                state_root=str(temp_root / "state"),
                session_id="assertions",
                expected_text="Stable browse evidence",
            )
            failing = browse_runtime.assert_text_contains(
                state_root=str(temp_root / "state"),
                session_id="assertions",
                expected_text="Missing text",
            )

            self.assertEqual(passing["status"], "PASS")
            self.assertTrue(passing["matched"])
            self.assertEqual(failing["status"], "FAIL")
            self.assertFalse(failing["matched"])

    def test_open_url_updates_session_created_by_shared_state_helpers(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            state_root = temp_root / "state"
            paths = browse_support.ensure_state_layout(browse_support.resolve_state_paths(str(state_root)))
            session = browse_support.create_session(
                paths,
                label="shared",
                browser="chromium",
                lang="vi-VN",
                device=None,
            )
            site_root = temp_root / "site"
            site_root.mkdir(parents=True, exist_ok=True)
            (site_root / "index.html").write_text(
                "<html><body><section>Shared browse state</section></body></html>",
                encoding="utf-8",
            )
            with serve_directory(site_root) as base_url:
                report = browse_runtime.open_url(
                    state_root=str(state_root),
                    session_id=session["id"],
                    url=f"{base_url}/index.html",
                )
            updated = browse_support.get_session(paths, session["id"])

            self.assertEqual(report["status"], "PASS")
            self.assertEqual(updated["active_tab_id"], "1")
            self.assertEqual(updated["last_url"], f"{base_url}/index.html")
            self.assertEqual(updated["tabs"][0]["driver"], "html-fetch")


if __name__ == "__main__":
    unittest.main()
