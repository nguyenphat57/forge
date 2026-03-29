from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import urlparse


def _domain_matches(host: str, cookie_domain: str) -> bool:
    normalized = cookie_domain.lstrip(".").lower()
    if not normalized:
        return False
    return host == normalized or host.endswith(f".{normalized}")


def _path_matches(request_path: str, cookie_path: str | None) -> bool:
    normalized = cookie_path or "/"
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    return request_path.startswith(normalized)


def load_cookie_header(storage_state_path: str | Path, url: str) -> str | None:
    path = Path(storage_state_path)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    cookies = payload.get("cookies")
    if not isinstance(cookies, list):
        return None
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    request_path = parsed.path or "/"
    is_https = parsed.scheme.lower() == "https"
    now = time.time()
    pairs: list[str] = []
    for item in cookies:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        value = item.get("value")
        domain = item.get("domain")
        if not all(isinstance(part, str) and part for part in (name, value, domain)):
            continue
        expires = item.get("expires")
        if isinstance(expires, (int, float)) and expires > 0 and expires < now:
            continue
        if bool(item.get("secure")) and not is_https:
            continue
        if not _domain_matches(host, domain):
            continue
        if not _path_matches(request_path, item.get("path")):
            continue
        pairs.append(f"{name}={value}")
    return "; ".join(pairs) if pairs else None
