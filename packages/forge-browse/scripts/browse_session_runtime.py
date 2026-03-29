from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path

import browse_runtime
from browse_storage_state import load_cookie_header
from browse_support import append_event, ensure_session, ensure_state_layout, resolve_state_paths, update_session


def _fetch_html(url: str, *, timeout_seconds: float, cookie_header: str) -> tuple[str, int]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": browse_runtime.USER_AGENT,
            "Cookie": cookie_header,
        },
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        status = getattr(response, "status", response.getcode())
        charset = response.headers.get_content_charset() or "utf-8"
        html = response.read().decode(charset, errors="replace")
        return html, int(status)


def open_authenticated_url(
    *,
    state_root: str | None,
    session_id: str,
    url: str,
    storage_state_path: str,
    timeout_seconds: float = 10.0,
) -> dict[str, object]:
    cookie_header = load_cookie_header(storage_state_path, url)
    if not cookie_header:
        return {
            "status": "FAIL",
            "state_root": str(Path(state_root).resolve()) if state_root else None,
            "session_id": session_id,
            "error": "No matching cookies were found in storage_state for the target URL.",
        }
    paths = ensure_state_layout(resolve_state_paths(state_root))
    session = ensure_session(paths, session_id, label=session_id, browser="chromium", lang=None, device=None)
    tab_id = str(len(session.get("tabs") or []) + 1)
    html, status = _fetch_html(url, timeout_seconds=timeout_seconds, cookie_header=cookie_header)
    snapshot_path = Path(session["artifacts_dir"]) / f"tab-{tab_id}.html"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(html, encoding="utf-8")
    text_excerpt = browse_runtime._extract_text(html)[:400]
    tab = {
        "tab_id": tab_id,
        "url": url,
        "status": status,
        "title": browse_runtime._extract_title(html),
        "snapshot_path": str(snapshot_path.resolve()),
        "html_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
        "text_excerpt": text_excerpt,
        "driver": "session-html-fetch",
        "cookie_header_applied": True,
    }
    session = update_session(
        paths,
        session_id,
        driver="session-html-fetch",
        tabs=[*(session.get("tabs") or []), tab],
        active_tab_id=tab_id,
        last_url=url,
        last_artifact=str(snapshot_path.resolve()),
    )
    append_event(
        paths,
        {
            "event": "open-auth",
            "session_id": session_id,
            "tab_id": tab_id,
            "url": url,
            "artifact": str(snapshot_path.resolve()),
        },
    )
    return {
        "status": "PASS",
        "state_root": paths["root"],
        "session_id": session_id,
        "active_tab_id": session["active_tab_id"],
        "tab": tab,
    }
