from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import browse_support  # noqa: E402


class BrowseStateTests(unittest.TestCase):
    def test_create_and_close_session_persists_store(self) -> None:
        with TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {browse_support.STATE_ROOT_ENV: temp_dir}, clear=False):
                paths = browse_support.ensure_state_layout(browse_support.resolve_state_paths())
                session = browse_support.create_session(
                    paths,
                    label="smoke",
                    browser="chromium",
                    lang="vi-VN",
                    device=None,
                )

                self.assertEqual(paths["root"], str(Path(temp_dir).resolve()))
                self.assertEqual(session["status"], "active")
                self.assertTrue(Path(session["artifacts_dir"]).is_dir())
                self.assertEqual(len(browse_support.list_sessions(paths)), 1)

                closed = browse_support.close_session(paths, session["id"])
                self.assertEqual(closed["status"], "closed")
                events = Path(paths["events_path"]).read_text(encoding="utf-8").splitlines()
                self.assertEqual(len(events), 2)

    def test_default_artifact_path_stays_inside_session_artifacts_dir(self) -> None:
        with TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {browse_support.STATE_ROOT_ENV: temp_dir}, clear=False):
                paths = browse_support.ensure_state_layout(browse_support.resolve_state_paths())
                session = browse_support.create_session(paths, label="proof", browser="chromium", lang=None, device=None)
                output = browse_support.default_artifact_path(paths, session["id"], "png")

                self.assertTrue(str(output).startswith(str(Path(session["artifacts_dir"]).resolve())))
                self.assertEqual(output.suffix, ".png")


if __name__ == "__main__":
    unittest.main()
