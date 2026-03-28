from __future__ import annotations

import json
import socket
import subprocess
import sys
import threading
import time
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
import urllib.error
import urllib.request


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_release  # noqa: E402
import install_bundle  # noqa: E402


class BrowseInstallTests(unittest.TestCase):
    def _serve_directory(self, root: Path) -> tuple[ThreadingHTTPServer, threading.Thread, str]:
        handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, directory=str(root), **kwargs)
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        return server, thread, f"http://{host}:{port}"

    def _run_script(self, script_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script_path), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def _free_port(self) -> int:
        with socket.socket() as handle:
            handle.bind(("127.0.0.1", 0))
            return int(handle.getsockname()[1])

    def _json_request(self, url: str, *, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read().decode("utf-8"))

    def _wait_for_server(self, origin: str) -> None:
        for _ in range(40):
            try:
                status, _ = self._json_request(f"{origin}/health")
                if status == 200:
                    return
            except OSError:
                time.sleep(0.1)
                continue
            time.sleep(0.1)
        raise AssertionError(f"forge-browse server did not become ready: {origin}")

    def test_install_bundle_requires_explicit_target_for_forge_browse(self) -> None:
        build_release.build_all()
        with self.assertRaises(ValueError):
            install_bundle.install_bundle("forge-browse", dry_run=True)

    def test_installed_browse_bundle_opens_and_asserts_against_snapshot(self) -> None:
        build_release.build_all()
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target = temp_root / "runtime" / "forge-browse"
            report = install_bundle.install_bundle(
                "forge-browse",
                target=str(target),
                backup_dir=str(temp_root / "backups"),
            )

            site_root = temp_root / "site"
            site_root.mkdir(parents=True, exist_ok=True)
            (site_root / "index.html").write_text(
                "<html><head><title>Installed Browse</title></head><body><main>Installed browse smoke</main></body></html>",
                encoding="utf-8",
            )
            server, thread, base_url = self._serve_directory(site_root)
            port = self._free_port()
            browse_process = subprocess.Popen(
                [sys.executable, str(target / "scripts" / "browse_server.py"), "--port", str(port)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            try:
                origin = f"http://127.0.0.1:{port}"
                self._wait_for_server(origin)
                open_status, open_payload = self._json_request(
                    f"{origin}/open",
                    method="POST",
                    payload={"session": "installed", "url": f"{base_url}/index.html"},
                )
                snapshot_status, snapshot_payload = self._json_request(f"{origin}/snapshot?session=installed")
                assert_status, assert_payload = self._json_request(
                    f"{origin}/assert-text",
                    method="POST",
                    payload={"session": "installed", "text": "Installed browse smoke"},
                )
            finally:
                browse_process.terminate()
                browse_process.wait(timeout=5)
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()

            manifest = json.loads((target / "INSTALL-MANIFEST.json").read_text(encoding="utf-8"))

            self.assertEqual(report["source_build_manifest"]["host"], "runtime")
            self.assertEqual(manifest["bundle"], "forge-browse")
            self.assertEqual(manifest["state"]["scope"], "runtime-tool-global")
            self.assertTrue(manifest["bundle_fingerprint"]["matches_source"])
            self.assertEqual(open_status, 200)
            self.assertEqual(snapshot_status, 200)
            self.assertEqual(assert_status, 200)
            self.assertEqual(open_payload["tab"]["title"], "Installed Browse")
            self.assertIn("Installed browse smoke", snapshot_payload["tab"]["text_excerpt"])
            self.assertTrue(assert_payload["matched"])
            self.assertTrue((temp_root / "runtime" / "forge-browse-state" / "state" / "sessions.json").exists())


if __name__ == "__main__":
    unittest.main()
