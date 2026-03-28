from __future__ import annotations

import hashlib
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

from browse_support import append_event, ensure_session, ensure_state_layout, get_session, resolve_state_paths, update_session


USER_AGENT = "forge-browse/1.0"


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)


def _extract_title(html: str) -> str | None:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return " ".join(match.group(1).split()) or None


def _extract_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return " ".join(parser.parts)


def _fetch_html(url: str, *, timeout_seconds: float) -> tuple[str, int]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        status = getattr(response, "status", response.getcode())
        charset = response.headers.get_content_charset() or "utf-8"
        html = response.read().decode(charset, errors="replace")
        return html, int(status)


def _resolve_runtime_paths(state_root: str | None) -> dict[str, str]:
    return ensure_state_layout(resolve_state_paths(state_root))


def _ensure_runtime_session(paths: dict[str, str], session_id: str) -> dict:
    return ensure_session(
        paths,
        session_id,
        label=session_id,
        browser="chromium",
        lang=None,
        device=None,
    )


def open_url(
    *,
    state_root: str | None,
    session_id: str,
    url: str,
    timeout_seconds: float = 10.0,
) -> dict:
    paths = _resolve_runtime_paths(state_root)
    session = _ensure_runtime_session(paths, session_id)
    tab_id = str(len(session.get("tabs") or []) + 1)
    html, status = _fetch_html(url, timeout_seconds=timeout_seconds)
    snapshot_path = Path(session["artifacts_dir"]) / f"tab-{tab_id}.html"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(html, encoding="utf-8")
    text_excerpt = _extract_text(html)[:400]
    tab = {
        "tab_id": tab_id,
        "url": url,
        "status": status,
        "title": _extract_title(html),
        "snapshot_path": str(snapshot_path.resolve()),
        "html_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
        "text_excerpt": text_excerpt,
        "driver": "html-fetch",
    }
    session = update_session(
        paths,
        session_id,
        driver="html-fetch",
        tabs=[*(session.get("tabs") or []), tab],
        active_tab_id=tab_id,
        last_url=url,
        last_artifact=str(snapshot_path.resolve()),
    )
    append_event(
        paths,
        {
            "event": "open",
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


def snapshot_tab(*, state_root: str | None, session_id: str, tab_id: str | None = None) -> dict:
    paths = _resolve_runtime_paths(state_root)
    session = get_session(paths, session_id)
    active_tab_id = tab_id or session.get("active_tab_id")
    for tab in session.get("tabs") or []:
        if tab.get("tab_id") == active_tab_id:
            return {
                "status": "PASS",
                "state_root": paths["root"],
                "session_id": session_id,
                "active_tab_id": active_tab_id,
                "tab": tab,
            }
    raise ValueError(f"Unknown tab for session {session_id}: {active_tab_id}")


def assert_text_contains(
    *,
    state_root: str | None,
    session_id: str,
    expected_text: str,
    tab_id: str | None = None,
) -> dict:
    snapshot = snapshot_tab(state_root=state_root, session_id=session_id, tab_id=tab_id)
    snapshot_path = Path(snapshot["tab"]["snapshot_path"])
    html = snapshot_path.read_text(encoding="utf-8")
    text = _extract_text(html)
    passed = expected_text in text or expected_text in html
    return {
        "status": "PASS" if passed else "FAIL",
        "state_root": snapshot["state_root"],
        "session_id": session_id,
        "active_tab_id": snapshot["active_tab_id"],
        "expected_text": expected_text,
        "matched": passed,
        "tab": snapshot["tab"],
    }
