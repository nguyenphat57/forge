from __future__ import annotations

import json
import sys
import unittest
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
import threading


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"
TESTS_DIR = Path(__file__).resolve().parent

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import browse_packets  # noqa: E402
import browse_support  # noqa: E402
from browse_test_support import serve_directory  # noqa: E402


class BrowsePacketTests(unittest.TestCase):
    @contextmanager
    def _serve_auth_site(self) -> str:
        session_cookie = "forge-session=ok"

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                cookie = self.headers.get("Cookie", "")
                body = "<html><body><main>Sign in required</main></body></html>"
                if self.path == "/login":
                    body = "<html><body><main>Sign in</main></body></html>"
                elif self.path == "/app" and session_cookie in cookie:
                    body = "<html><body><main>Welcome back</main></body></html>"
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(body.encode("utf-8"))

            def log_message(self, format: str, *args: object) -> None:  # noqa: A003
                return None

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            yield f"http://{host}:{port}"
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

    def test_create_list_and_run_html_smoke_packet(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            paths = browse_support.ensure_state_layout(browse_support.resolve_state_paths(str(temp_root / "state")))
            session = browse_support.create_session(paths, label="qa", browser="chromium", lang=None, device=None)
            site_root = temp_root / "site"
            site_root.mkdir(parents=True, exist_ok=True)
            (site_root / "index.html").write_text("<html><body><main>Checkout Ready</main></body></html>", encoding="utf-8")

            with serve_directory(site_root) as base_url:
                created = browse_packets.create_packet(
                    paths=paths,
                    session_id=session["id"],
                    name="checkout-smoke",
                    url=f"{base_url}/index.html",
                    mode="html-smoke",
                    expected_text=["Checkout Ready"],
                    note=["Smoke main flow"],
                    wait_for_selector=None,
                    wait_for_timeout=None,
                    full_page=False,
                )
                listed = browse_packets.list_packets(paths=paths, session_id=session["id"])
                report = browse_packets.run_packet(paths=paths, session_id=session["id"], name="checkout-smoke")

            self.assertEqual(created["status"], "PASS")
            self.assertEqual(len(listed), 1)
            self.assertEqual(listed[0]["slug"], "checkout-smoke")
            self.assertEqual(report["status"], "PASS")
            self.assertTrue(report["assertions"][0]["matched"])
            self.assertTrue(Path(report["artifact_path"]).exists())
            self.assertTrue(Path(report["report_path"]).exists())

    def test_run_authenticated_packet_includes_preflight_and_passes_with_storage_state(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            paths = browse_support.ensure_state_layout(browse_support.resolve_state_paths(str(temp_root / "state")))
            session = browse_support.create_session(paths, label="qa", browser="chromium", lang=None, device=None)
            with self._serve_auth_site() as base_url:
                Path(session["storage_state_path"]).write_text(
                    json.dumps(
                        {
                            "cookies": [
                                {
                                    "name": "forge-session",
                                    "value": "ok",
                                    "domain": "127.0.0.1",
                                    "path": "/",
                                    "httpOnly": True,
                                    "secure": False,
                                    "sameSite": "Lax",
                                }
                            ],
                            "origins": [],
                        }
                    ),
                    encoding="utf-8",
                )
                created = browse_packets.create_authenticated_packet(
                    paths=paths,
                    session_id=session["id"],
                    name="auth-check",
                    url=f"{base_url}/app",
                    login_url=f"{base_url}/login",
                    expected_text=["Welcome back"],
                    note=["Authenticated smoke"],
                    wait_for_selector=None,
                    wait_for_timeout=None,
                    full_page=False,
                )
                report = browse_packets.run_packet(paths=paths, session_id=session["id"], name="auth-check")

            self.assertEqual(created["packet"]["auth"]["required"], True)
            self.assertEqual(created["packet"]["auth"]["login_url"], f"{base_url}/login")
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["preflight"][0]["id"], "auth-request")
            self.assertTrue(any(item["id"] == "storage-state" and item["status"] == "PASS" for item in report["preflight"]))
            self.assertTrue(report["assertions"][0]["matched"])
            self.assertEqual(report["runtime"]["tab"]["driver"], "session-html-fetch")

    def test_authenticated_packet_fails_when_storage_state_is_missing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            paths = browse_support.ensure_state_layout(browse_support.resolve_state_paths(str(temp_root / "state")))
            session = browse_support.create_session(paths, label="qa", browser="chromium", lang=None, device=None)
            site_root = temp_root / "site"
            site_root.mkdir(parents=True, exist_ok=True)
            (site_root / "index.html").write_text("<html><body><main>Private Area</main></body></html>", encoding="utf-8")

            with serve_directory(site_root) as base_url:
                browse_packets.create_authenticated_packet(
                    paths=paths,
                    session_id=session["id"],
                    name="missing-storage-state",
                    url=f"{base_url}/index.html",
                    login_url=f"{base_url}/index.html",
                    expected_text=["Private Area"],
                    note=[],
                    wait_for_selector=None,
                    wait_for_timeout=None,
                    full_page=False,
                )
                report = browse_packets.run_packet(paths=paths, session_id=session["id"], name="missing-storage-state")

            self.assertEqual(report["status"], "FAIL")
            self.assertTrue(any(item["id"] == "storage-state" and item["status"] == "FAIL" for item in report["preflight"]))
            self.assertIsNone(report["runtime"])
            self.assertIsNone(report["artifact_path"])

    def test_run_html_smoke_packet_reports_missing_text(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            paths = browse_support.ensure_state_layout(browse_support.resolve_state_paths(str(temp_root / "state")))
            session = browse_support.create_session(paths, label="qa", browser="chromium", lang=None, device=None)
            site_root = temp_root / "site"
            site_root.mkdir(parents=True, exist_ok=True)
            (site_root / "index.html").write_text("<html><body><main>Stable Flow</main></body></html>", encoding="utf-8")

            with serve_directory(site_root) as base_url:
                browse_packets.create_packet(
                    paths=paths,
                    session_id=session["id"],
                    name="missing-copy",
                    url=f"{base_url}/index.html",
                    mode="html-smoke",
                    expected_text=["Missing Text"],
                    note=[],
                    wait_for_selector=None,
                    wait_for_timeout=None,
                    full_page=False,
                )
                report = browse_packets.run_packet(paths=paths, session_id=session["id"], name="missing-copy")

            self.assertEqual(report["status"], "FAIL")
            self.assertFalse(report["assertions"][0]["matched"])

    def test_authenticated_packet_fails_when_storage_state_has_no_matching_cookie(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            paths = browse_support.ensure_state_layout(browse_support.resolve_state_paths(str(temp_root / "state")))
            session = browse_support.create_session(paths, label="qa", browser="chromium", lang=None, device=None)
            Path(session["storage_state_path"]).write_text(json.dumps({"cookies": [], "origins": []}), encoding="utf-8")

            with self._serve_auth_site() as base_url:
                browse_packets.create_authenticated_packet(
                    paths=paths,
                    session_id=session["id"],
                    name="no-cookie-match",
                    url=f"{base_url}/app",
                    login_url=f"{base_url}/login",
                    expected_text=["Welcome back"],
                    note=[],
                    wait_for_selector=None,
                    wait_for_timeout=None,
                    full_page=False,
                )
                report = browse_packets.run_packet(paths=paths, session_id=session["id"], name="no-cookie-match")

            self.assertEqual(report["status"], "FAIL")
            self.assertEqual(report["runtime"]["status"], "FAIL")
            self.assertIn("No matching cookies", report["runtime"]["error"])


if __name__ == "__main__":
    unittest.main()
