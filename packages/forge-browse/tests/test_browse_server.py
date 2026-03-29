from __future__ import annotations

import json
import sys
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"
TESTS_DIR = Path(__file__).resolve().parent

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import browse_server  # noqa: E402
from browse_test_support import serve_directory  # noqa: E402


def _json_request(url: str, *, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:  # type: ignore[attr-defined]
        return error.code, json.loads(error.read().decode("utf-8"))


class BrowseServerTests(unittest.TestCase):
    def test_server_exposes_health_open_snapshot_and_assert(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            site_root = temp_root / "site"
            site_root.mkdir(parents=True, exist_ok=True)
            (site_root / "index.html").write_text(
                "<html><head><title>Browse Server</title></head><body><div>Server smoke text</div></body></html>",
                encoding="utf-8",
            )
            with serve_directory(site_root) as base_url:
                server = browse_server.create_server(host="127.0.0.1", port=0, state_root=str(temp_root / "state"))
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    host, port = server.server_address
                    origin = f"http://{host}:{port}"
                    status, health = _json_request(f"{origin}/health")
                    self.assertEqual(status, 200)
                    self.assertEqual(health["driver"], "html-fetch")

                    status, opened = _json_request(
                        f"{origin}/open",
                        method="POST",
                        payload={"session": "server", "url": f"{base_url}/index.html"},
                    )
                    self.assertEqual(status, 200)
                    self.assertEqual(opened["tab"]["title"], "Browse Server")

                    status, snapshot = _json_request(f"{origin}/snapshot?session=server")
                    self.assertEqual(status, 200)
                    self.assertIn("Server smoke text", snapshot["tab"]["text_excerpt"])

                    status, assertion = _json_request(
                        f"{origin}/assert-text",
                        method="POST",
                        payload={"session": "server", "text": "Server smoke text"},
                    )
                    self.assertEqual(status, 200)
                    self.assertTrue(assertion["matched"])
                finally:
                    server.shutdown()
                    thread.join(timeout=5)
                    server.server_close()


if __name__ == "__main__":
    unittest.main()
