from __future__ import annotations

import argparse
import json
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from browse_paths import STATE_SCOPE, resolve_state_root
from browse_runtime import assert_text_contains, open_url, snapshot_tab


class BrowseRequestHandler(BaseHTTPRequestHandler):
    server_version = "forge-browse/1.0"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._write_json(
                200,
                {
                    "status": "PASS",
                    "state_root": str(self.server.state_root),
                    "state_scope": STATE_SCOPE,
                    "driver": "html-fetch",
                },
            )
            return
        if parsed.path == "/snapshot":
            query = parse_qs(parsed.query)
            payload = snapshot_tab(
                state_root=str(self.server.state_root),
                session_id=query.get("session", ["default"])[0],
                tab_id=query.get("tab", [None])[0],
            )
            self._write_json(200, payload)
            return
        self._write_json(404, {"status": "FAIL", "error": "unknown route"})

    def do_POST(self) -> None:  # noqa: N802
        payload = self._read_json()
        if self.path == "/open":
            report = open_url(
                state_root=str(self.server.state_root),
                session_id=str(payload.get("session") or "default"),
                url=str(payload["url"]),
                timeout_seconds=float(payload.get("timeout_seconds", 10.0)),
            )
            self._write_json(200, report)
            return
        if self.path == "/assert-text":
            report = assert_text_contains(
                state_root=str(self.server.state_root),
                session_id=str(payload.get("session") or "default"),
                expected_text=str(payload["text"]),
                tab_id=payload.get("tab"),
            )
            self._write_json(200 if report["matched"] else 409, report)
            return
        self._write_json(404, {"status": "FAIL", "error": "unknown route"})

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b"{}"
        payload = json.loads(body.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        return payload

    def _write_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def create_server(*, host: str, port: int, state_root: str | None) -> ThreadingHTTPServer:
    resolved_state_root = resolve_state_root(state_root)
    handler = partial(BrowseRequestHandler)
    server = ThreadingHTTPServer((host, port), handler)
    server.state_root = resolved_state_root  # type: ignore[attr-defined]
    return server


def main() -> int:
    parser = argparse.ArgumentParser(description="Start the forge-browse HTTP control plane.")
    parser.add_argument("--host", default="127.0.0.1", help="Listen host")
    parser.add_argument("--port", type=int, default=9045, help="Listen port")
    parser.add_argument("--state-root", help="Override persistent state root")
    args = parser.parse_args()

    server = create_server(host=args.host, port=args.port, state_root=args.state_root)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
